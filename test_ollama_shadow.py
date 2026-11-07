import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from ollama_provider import OllamaError, OllamaProvider, SCHEMA, INTENTS, validate
from ollama_shadow import ShadowObserver
from server import App, Run
import actions


def prediction(intent='time_now', target='unspecified'):
    return {'intent': intent, 'target': target, 'action': 'classify', 'parameters': {}}


def response(content=None, **extra):
    return {'done': True, 'done_reason': 'stop', 'load_duration': 1000000,
            'message': {'content': json.dumps(prediction()) if content is None else content}, **extra}


class AdapterTests(unittest.TestCase):
    def test_online_and_missing(self):
        p = OllamaProvider()
        with patch.object(p, '_request', side_effect=[{'models': [{'name': p.model}]}, {'models': []}]):
            self.assertEqual(p.health_check()['status'], 'ONLINE')
            self.assertFalse(p.health['loaded_before_request'])
        with patch.object(p, '_request', return_value={'models': []}):
            self.assertEqual(p.health_check()['error'], 'model_missing')

    def test_offline_and_timeout(self):
        for code in ('offline', 'timeout'):
            p = OllamaProvider()
            with patch.object(p, '_request', side_effect=OllamaError(code)):
                self.assertEqual(p.health_check()['error'], code)
                self.assertIn('health_latency_ms', p.health)

    def test_success_and_payload(self):
        p = OllamaProvider()
        with patch.object(p, '_request', return_value=response()) as call:
            result = p.classify_intent('what time is it')
        self.assertEqual(result['prediction'], prediction())
        body = call.call_args.args[1]
        self.assertIs(body['think'], False)
        self.assertIs(body['stream'], False)
        self.assertEqual(body['format'], SCHEMA)
        self.assertEqual(body['options']['temperature'], 0)
        self.assertEqual(body['keep_alive'], 30)
        self.assertNotIn('tools', body)

    def test_rejects_bad_outputs(self):
        bad = ['{', '[]', 'null', '{"intent":"time_now","intent":"none"}',
               json.dumps({**prediction(), 'extra': 1}), json.dumps({**prediction(), 'intent': 'shell'}),
               json.dumps({**prediction(), 'parameters': {'command': 'anything'}}),
               json.dumps({**prediction(), 'target': 'calculator'}), json.dumps({**prediction(), 'intent': 5}),
               json.dumps({**prediction(), 'action': 'execute'})]
        p = OllamaProvider()
        for content in bad:
            with self.subTest(content=content), patch.object(p, '_request', return_value=response(content)), self.assertRaises(OllamaError):
                p.classify_intent('time')

    def test_no_thinking_tools_or_partial(self):
        p = OllamaProvider()
        for data in [response(done=False), response(done_reason='length'),
                     response(message={'thinking': 'private', 'content': '{}'}),
                     response(message={'tool_calls': [{}], 'content': '{}'})]:
            with patch.object(p, '_request', return_value=data), self.assertRaises(OllamaError):
                p.classify_intent('time')

    def test_canonical_names(self):
        names = {t['function']['name'] for t in actions.TOOLS}
        self.assertTrue(set(INTENTS)-{'none'} <= names)

    def test_cold_and_warm_budgets(self):
        p = OllamaProvider()
        for loaded, budget in ((False, 20), (True, 8)):
            p.health['loaded_before_request'] = loaded
            with patch.object(p, '_request', return_value=response()) as request:
                p.classify_intent('time')
            self.assertEqual(request.call_args.kwargs['timeout'], budget)

    def test_transport_fixed_loopback_and_no_redirect(self):
        p = OllamaProvider()
        conn = Mock()
        conn.getresponse.return_value.status = 302
        with patch('ollama_provider.http.client.HTTPConnection', return_value=conn) as factory, self.assertRaises(OllamaError):
            p._request('/api/tags')
        self.assertEqual(factory.call_args.args, ('127.0.0.1', 11434))
        conn.close.assert_called_once()
        self.assertEqual(conn.request.call_count, 1)

    def test_transport_errors_and_response_limit(self):
        for error in (TimeoutError(), ConnectionRefusedError()):
            conn = Mock(); conn.request.side_effect = error
            with patch('ollama_provider.http.client.HTTPConnection', return_value=conn), self.assertRaises(OllamaError):
                OllamaProvider()._request('/api/tags')
            conn.close.assert_called_once()
        conn = Mock(); conn.getresponse.return_value.status = 200
        conn.getresponse.return_value.read1.return_value = b'x'*4096
        with patch('ollama_provider.http.client.HTTPConnection', return_value=conn), self.assertRaisesRegex(OllamaError, 'response_too_large'):
            OllamaProvider()._request('/api/tags')


class ShadowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.env = patch.dict(os.environ, {'JARVIS_OLLAMA_SHADOW': '1'})
        self.env.start(); self.addCleanup(self.env.stop)
        self.p = OllamaProvider()
        self.p.health_check = Mock(return_value={'status': 'ONLINE', 'loaded_before_request': False})
        self.p.classify_intent = Mock(return_value={'prediction': prediction(), 'latency_ms': 1, 'load_duration_ms': 1})
        self.s = ShadowObserver(self.tmp.name, self.p)

    def finish(self):
        if self.s.worker:
            self.s.worker.join(3)
            self.assertFalse(self.s.worker.is_alive())

    def test_match_mismatch_and_no_text_in_log(self):
        for result, match in [(prediction(), True), (prediction('none'), False)]:
            self.s.next_allowed = 0
            self.p.classify_intent.return_value['prediction'] = result
            self.s.submit('id', 'what time is it', ('time_now', {})); self.finish()
            self.assertIs(self.s.last['match'], match)
        content = self.s.path.read_text()
        self.assertNotIn('what time is it', content)
        self.assertNotIn('thinking', content)
        self.assertEqual(len(content.splitlines()), 2)

    def test_schema_failure_and_error_redaction(self):
        self.p.classify_intent.return_value['prediction'] = {'intent': 'shell'}
        self.s.submit('id', 'time', ('time_now', {})); self.finish()
        self.assertFalse(self.s.last['schema_valid'])
        self.assertIsNone(self.s.last['match'])
        self.s.next_allowed = 0
        self.p.classify_intent.side_effect = RuntimeError('secret-token')
        self.s.submit('id', 'time', ('time_now', {})); self.finish()
        self.assertNotIn('secret-token', self.s.path.read_text())

    def test_offline_cooldown_no_retries(self):
        self.p.health_check.return_value = {'status': 'OFFLINE', 'error': 'offline'}
        self.s.submit('id', 'time', ('time_now', {})); self.finish()
        self.s.submit('id2', 'time', ('time_now', {}))
        self.p.health_check.assert_called_once()
        self.p.classify_intent.assert_not_called()
        self.assertEqual(self.s.skipped, 1)

    def test_private_freeform_and_unknown_commands_excluded(self):
        for text in ('note: password abc', 'search for a private token', 'time\nsecret', 'open powershell'):
            self.s.submit('id', text, ('time_now', {}))
        self.assertIsNone(self.s.worker)
        self.p.classify_intent.assert_not_called()

    def test_disabled_no_traffic(self):
        self.s.enabled = False
        self.s.submit('id', 'time', ('time_now', {}))
        self.p.health_check.assert_not_called()

    def test_slow_provider_never_blocks_core_or_queues(self):
        entered, release = threading.Event(), threading.Event()
        def slow(_):
            entered.set(); release.wait(3)
            return {'prediction': prediction(), 'latency_ms': 1, 'load_duration_ms': 1}
        self.p.classify_intent.side_effect = slow
        self.s.submit('id', 'time', ('time_now', {}))
        self.assertTrue(entered.wait(1))
        self.s.submit('id2', 'time', ('time_now', {}))
        self.assertEqual(self.s.skipped, 1)
        release.set(); self.finish()

    def test_log_failure_is_contained(self):
        self.s.path = Path(self.tmp.name)  # directory is not writable as a file
        self.s.submit('id', 'time', ('time_now', {})); self.finish()
        self.assertEqual(self.s.last['logging_error'], 'record_write_failed')
        self.assertFalse(self.s.gate.locked())

    def test_core_authoritative_tool_and_memory_unchanged(self):
        app = App(Path(self.tmp.name)/'core'); app.ollama_shadow = self.s
        self.p.classify_intent.return_value['prediction'] = prediction('open_app', 'paint')
        before = app.store.items('memory')
        with patch.object(app, 'tool', return_value={'time': '12:00'}) as tool, patch.object(app, 'describe', return_value='It is noon.'), patch('providers.chat') as cloud:
            run = Run('test'); app.work(run, 'what time is it', None); self.finish()
        tool.assert_called_once_with('time_now', {}, run=run)
        cloud.assert_not_called()
        self.assertEqual(app.store.items('memory'), before)
        self.assertEqual(app.store.history('test')[-1]['content'], 'It is noon.')

    def test_provider_failures_preserve_core_response_and_memory(self):
        for code in ('offline', 'timeout', 'invalid_schema', 'unknown_intent'):
            with self.subTest(code=code):
                app = App(Path(self.tmp.name)/code); app.ollama_shadow = self.s
                self.s.next_allowed = 0
                self.p.classify_intent.side_effect = OllamaError(code)
                before = app.store.items('memory')
                with patch.object(app, 'tool', return_value={}) as tool, patch.object(app, 'describe', return_value='Authoritative response'):
                    run = Run(code); app.work(run, 'time', None); self.finish()
                tool.assert_called_once_with('time_now', {}, run=run)
                self.assertTrue(any(e['event'] == 'run.completed' for e in run.events))
                self.assertEqual(app.store.history(code)[-1]['content'], 'Authoritative response')
                self.assertEqual(app.store.items('memory'), before)
                self.assertEqual(self.s.last['error'], code)
                self.assertIsNone(self.s.last['match'])

    def test_observer_crash_does_not_break_core(self):
        app = App(Path(self.tmp.name)/'core')
        with patch.object(app.ollama_shadow, 'submit', side_effect=RuntimeError('broken')), patch.object(app, 'tool', return_value={}), patch.object(app, 'describe', return_value='OK'):
            run = Run('test'); app.work(run, 'time', None)
        self.assertTrue(run.done)
        self.assertTrue(any(e['event'] == 'run.completed' for e in run.events))

    def test_cloud_request_still_uses_existing_provider(self):
        app = App(Path(self.tmp.name)/'core'); app.ollama_shadow = self.s
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'fixture', 'JARVIS_PROVIDER': 'openrouter'}), patch('providers.chat', return_value={'role': 'assistant', 'content': 'A test explanation.'}) as cloud:
            run = Run('test'); app.work(run, 'Explain the colour blue', None)
        cloud.assert_called_once()
        self.p.classify_intent.assert_not_called()
        self.assertTrue(any(e['event'] == 'run.completed' for e in run.events))


if __name__ == '__main__':
    unittest.main()
