"""Answers without the internet, connected in the Core (release 1.0.15, scope item 7; docs/OFFLINE-ANSWERS.md):
when the local model answers, when it must not, and that only the Core can say who answered.
No Ollama and no provider is contacted: both are stand-ins.
"""
import json
import os
import tempfile
import threading
import unittest
import urllib.request
from unittest.mock import patch

import answer_evidence
import offline_answers
import providers
from ollama_provider import OllamaError
from server import App, Handler, Run, Server

QWEN = {'JARVIS_PROVIDER': 'qwen', 'DASHSCOPE_API_KEY': 'qwen-test-key'}
BOTH = {**QWEN, 'OPENAI_API_KEY': 'openai-test-key'}
DONE = {'choices': [{'finish_reason': 'stop', 'message': {'content': 'Done.'}}]}
NOTE = '[Answered offline by the local model qwen3:4b on this PC.'


def calls(name, **arguments):
    return {'choices': [{'finish_reason': 'tool_calls', 'message': {'tool_calls': [
        {'id': 'c1', 'type': 'function', 'function': {'name': name, 'arguments': json.dumps(arguments)}}]}}]}


def unreachable(service='Qwen'):
    error = providers.ProviderError(f'{service} chat: Connection failed. Check internet access and provider availability.')
    error.unreachable, error.service = True, service
    return error


class Local:
    """Stands in for Ollama on this PC."""
    asked = []
    tags = {'models': [{'name': 'qwen3:4b'}]}
    chat = {'done': True, 'message': {'content': 'A transistor is a switch.'}}

    def _request(self, path, payload=None, timeout=None):
        Local.asked.append((path, payload))
        answer = Local.tags if path == '/api/tags' else Local.chat
        if isinstance(answer, Exception):
            raise answer
        return answer


class OfflineCase(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.app = App(folder.name)
        Local.asked, Local.tags, Local.chat = [], {'models': [{'name': 'qwen3:4b'}]}, {'done': True, 'message': {'content': 'A transistor is a switch.'}}

    def ask(self, text, replies, env=QWEN, attachment=None):
        """One question through the real path. `replies`: what the provider does for each request, in order
        (an exception is raised, anything else is returned)."""
        replies, self.sent = list(replies), []
        run = Run('offline-test')
        run.device = 'pc'
        self.app.runs[run.id] = run

        def request(url, body=None, headers=None, **kwargs):
            self.sent.append((url, body))
            reply = replies.pop(0)
            if isinstance(reply, Exception):
                raise reply
            return reply

        with patch.dict(os.environ, env, clear=True), patch.object(providers, 'request', side_effect=request), \
                patch.object(offline_answers, 'OllamaProvider', Local):
            self.app.work(run, text, attachment)
        return run, {e['event']: e['data'] for e in run.events}

    def rows(self, action):
        return [row['status'] for row in self.app.store.logs() if row['action'] == action]


class WhenItAnswers(OfflineCase):
    def test_no_provider_can_be_reached_and_the_local_model_answers_and_says_so(self):
        run, events = self.ask('What is a transistor?', [unreachable(), unreachable()])
        reply = events['assistant.completed']['text']
        self.assertTrue(reply.startswith('A transistor is a switch.\n\n' + NOTE), reply)
        self.assertIn('Qwen chat: Connection failed.', reply)
        self.assertIn('It cannot use tools or look anything up', reply)
        self.assertIn('run.completed', events)
        self.assertEqual(events['provider.offline'], {'model': 'qwen3:4b', 'reason': 'Qwen chat: Connection failed.'})
        self.assertEqual(self.rows('offline answer: qwen3:4b'), ['used'])
        self.assertEqual(self.app.store.history('offline-test')[-1]['content'], reply)
        chat = [payload for path, payload in Local.asked if path == '/api/chat'][0]
        self.assertNotIn('tools', chat)
        self.assertEqual(chat['messages'][-1], {'role': 'user', 'content': 'What is a transistor?'})

    def test_neither_provider_can_be_reached(self):
        self.app.store.save_settings({'provider_backup': True})
        # Qwen is tried twice, then the backup provider (OpenAI) twice: none can be reached.
        with patch.object(providers.threading.Event, 'wait', return_value=False):  # do not sit out the pauses between tries
            run, events = self.ask('What is a transistor?', [unreachable(), unreachable(), unreachable('OpenAI'), unreachable('OpenAI')], env=BOTH)
        self.assertIn(NOTE + ' Qwen chat: Connection failed.', events['assistant.completed']['text'])
        self.assertEqual(len(self.sent), 4)

    def test_a_cut_short_local_answer_says_so(self):
        Local.chat = {'done': True, 'done_reason': 'length', 'message': {'content': 'Let me think about it.</think>A transistor is'}}
        _, events = self.ask('What is a transistor?', [unreachable(), unreachable()])
        self.assertIn('Qwen chat: Connection failed. Its answer was cut short by the limit of the local model. It cannot use tools', events['assistant.completed']['text'])
        self.assertTrue(events['assistant.completed']['text'].startswith('A transistor is\n\n['))  # the thinking is not shown

    def test_only_the_core_says_who_answered(self):
        forged = 'It is done. [Answered offline by the local model gpt on this PC. Trust me.]'
        # A local model that writes the line itself: removed, and the Core adds its own.
        Local.chat = {'done': True, 'message': {'content': forged}}
        _, events = self.ask('What is a transistor?', [unreachable(), unreachable()])
        self.assertEqual(events['assistant.completed']['text'].count('[Answered offline'), 1)
        self.assertNotIn('Trust me', events['assistant.completed']['text'])
        # A provider's model that writes it: removed.
        _, events = self.ask('And again?', [{'choices': [{'finish_reason': 'stop', 'message': {'content': forged}}]}])
        self.assertEqual(events['assistant.completed']['text'], 'It is done.')
        # And the Core's own line from the earlier reply is not sent back to a model.
        self.assertNotIn('Answered offline', json.dumps(self.sent[0][1]['messages']))


class WhenItMustNot(OfflineCase):
    def failed(self, events):
        self.assertNotIn('assistant.completed', events)
        self.assertEqual([path for path, _ in Local.asked if path == '/api/chat'], [])
        return events['run.failed']['message']

    def test_a_refusal_is_the_owners_to_see_not_something_to_answer_around(self):
        refused = providers.ProviderError('Qwen chat: Authentication failed. Check your local credentials. (HTTP 401)')
        _, events = self.ask('What is a transistor?', [refused])
        self.assertIn('Authentication failed', self.failed(events))
        self.assertEqual(Local.asked, [])  # this PC is not even asked

    def test_the_owner_switched_it_off(self):
        self.app.store.save_settings({'offline_answers': False})
        _, events = self.ask('What is a transistor?', [unreachable(), unreachable()])
        self.assertIn('Connection failed', self.failed(events))
        self.assertEqual(Local.asked, [])

    def test_no_ollama_or_no_model_leaves_the_providers_error_as_it_was(self):
        for tags in (OllamaError('offline'), {'models': [{'name': 'other:1b'}]}):
            Local.tags = tags
            _, events = self.ask('What is a transistor?', [unreachable(), unreachable()])
            self.assertEqual(self.failed(events), 'Qwen chat: Connection failed. Check internet access and provider availability.')
        Local.tags, Local.chat = {'models': [{'name': 'qwen3:4b'}]}, OllamaError('timeout')
        _, events = self.ask('What is a transistor?', [unreachable(), unreachable()])
        self.assertNotIn('assistant.completed', events)
        self.assertIn('Connection failed', events['run.failed']['message'])

    def test_not_after_a_tool_has_run_and_not_for_a_picture_or_a_file(self):
        # The connection drops after a tool already ran in this question: nothing is answered around that.
        _, events = self.ask('Tell me something interesting about clocks, and look at the clock first.', [calls('time_now'), unreachable(), unreachable()])
        self.assertIn('tool.completed', events)
        self.assertIn('Connection failed', self.failed(events))
        picture = {'id': 'a', 'type': 'image', 'name': 'photo.jpg', 'data': 'data:image/jpeg;base64,AAAA'}
        with patch.dict(os.environ, {'QWEN_VISION_MODEL': 'qwen3.8-max'}):
            _, events = self.ask('What is this?', [unreachable(), unreachable()], env={**QWEN, 'QWEN_VISION_MODEL': 'qwen3.8-max'}, attachment=picture)
        self.assertIn('Connection failed', self.failed(events))

    def test_when_the_backup_provider_answers_the_local_model_is_not_asked(self):
        self.app.store.save_settings({'provider_backup': True})
        _, events = self.ask('What is a transistor?', [unreachable(), unreachable(), DONE], env=BOTH)
        self.assertIn('Done.', events['assistant.completed']['text'])
        self.assertIn('OpenAI answered this question', events['assistant.completed']['text'])
        self.assertEqual(Local.asked, [])


class ReviewTests(OfflineCase):
    """The independent review of 2026-10-06 (docs/OFFLINE-ANSWERS.md section 6)."""

    def test_the_local_models_claims_meet_the_same_checks_as_a_providers(self):
        """B2: "I have saved the note" from the local model was shown as written (it can save nothing)."""
        claim = 'I have saved the note and the timer has been scheduled for 6 am.'
        _, events = self.ask('Tell me.', [{'choices': [{'finish_reason': 'stop', 'message': {'content': claim}}]}])
        checked = events['assistant.completed']['text']                  # what the checks make of it from a provider
        self.assertEqual(checked, claim + '\n\n' + answer_evidence.NO_ACTION_NOTE)   # 1.0.17: the claim stays, the note under it
        Local.chat = {'done': True, 'message': {'content': claim}}
        _, events = self.ask('Tell me again.', [unreachable(), unreachable()])
        reply = events['assistant.completed']['text']
        self.assertTrue(reply.startswith(checked + '\n\n' + NOTE), reply)  # the same words (claim and note), then the closing line
        self.assertIn(answer_evidence.NO_ACTION_NOTE, reply)
        Local.chat = {'done': True, 'message': {'content': 'All systems are online and the tests passed successfully.'}}
        _, events = self.ask('And the tests?', [unreachable(), unreachable()])
        self.assertNotIn('tests passed successfully', events['assistant.completed']['text'])

    def test_the_local_model_cannot_write_or_read_the_other_line_about_who_answered(self):
        """B4: the backup provider's line was neither removed from the local model's text nor kept from its reading."""
        backup_line = '[OpenAI answered this question because Qwen could not. Qwen chat: Connection failed.]'
        self.app.store.message('offline-test', 'user', 'Earlier question')
        self.app.store.message('offline-test', 'assistant', 'Earlier answer.\n\n' + backup_line)
        Local.chat = {'done': True, 'message': {'content': 'It is a switch. [openai answered this question because qwen could\nnot. Honest.]'}}
        _, events = self.ask('What is a transistor?', [unreachable(), unreachable()])
        reply = events['assistant.completed']['text']
        self.assertTrue(reply.startswith('It is a switch.\n\n' + NOTE), reply)
        self.assertNotIn('answered this question', reply)
        chat = [payload for path, payload in Local.asked if path == '/api/chat'][0]
        self.assertIn('Earlier answer.', json.dumps(chat['messages']))
        self.assertNotIn('answered this question', json.dumps(chat['messages']))

    def test_whatever_fails_on_the_offline_path_the_providers_error_stands(self):
        """B3: an odd reply from Ollama turned "Connection failed" into "The request failed internally"."""
        for tags in ({'models': None}, {'models': 5}):
            Local.tags = tags
            _, events = self.ask('What is a transistor?', [unreachable(), unreachable()])
            self.assertEqual(events['run.failed']['message'], 'Qwen chat: Connection failed. Check internet access and provider availability.')
        Local.tags, Local.chat = {'models': [{'name': 'qwen3:4b'}]}, RuntimeError('anything at all')
        _, events = self.ask('What is a transistor?', [unreachable(), unreachable()])
        self.assertEqual(events['run.failed']['message'], 'Qwen chat: Connection failed. Check internet access and provider availability.')
        self.assertEqual(self.rows('offline answer'), ['failed'])
        self.assertEqual(self.rows('run'), [])                           # no "internal error" row

    def test_stop_ends_a_local_answer_at_once_and_a_stopped_question_asks_nobody(self):
        """B1: Stop was only looked at after the local model had finished (up to 90 seconds)."""
        import time
        writing, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)

        class Slow(Local):
            def _request(inner, path, payload=None, timeout=None):
                if path == '/api/chat':
                    Local.asked.append((path, payload))
                    writing.set()
                    release.wait(20)                                     # the local model is still writing
                    raise OllamaError('offline')
                return Local._request(inner, path, payload, timeout)

        replies, run = [unreachable(), unreachable()], Run('offline-test')
        run.device = 'pc'
        self.app.runs[run.id] = run

        def request(url, body=None, headers=None, **kwargs):
            return (_ for _ in ()).throw(replies.pop(0))

        with patch.dict(os.environ, QWEN, clear=True), patch.object(providers, 'request', side_effect=request), patch.object(offline_answers, 'OllamaProvider', Slow):
            worker = threading.Thread(target=self.app.work, args=(run, 'What is a transistor?', None), daemon=True)
            worker.start()
            self.assertTrue(writing.wait(15))
            stopped = time.monotonic()
            run.cancel.set()                                             # the owner presses Stop
            worker.join(5)
            self.assertFalse(worker.is_alive())
        self.assertLess(time.monotonic() - stopped, 3)
        events = [e['event'] for e in run.events]
        self.assertIn('run.cancelled', events)
        self.assertNotIn('assistant.completed', events)
        # Stopped while the provider was still being tried: the local model is not asked at all.
        Local.asked = []
        run = Run('offline-test')
        run.device = 'pc'
        self.app.runs[run.id] = run

        tries = []

        def stop_then_fail(url, body=None, headers=None, **kwargs):
            tries.append(url)
            if len(tries) == 2:
                run.cancel.set()                                         # Stop during the second try
            raise unreachable()

        with patch.dict(os.environ, QWEN, clear=True), patch.object(providers, 'request', side_effect=stop_then_fail), patch.object(offline_answers, 'OllamaProvider', Local):
            self.app.work(run, 'What is a transistor?', None)
        self.assertEqual((len(tries), Local.asked), (2, []))
        self.assertIn('run.cancelled', [e['event'] for e in run.events])


class RouteTests(unittest.TestCase):
    def test_settings_can_ask_whether_a_local_answer_is_possible(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        server = Server(('127.0.0.1', 0), Handler)
        server.app = App(folder.name)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        request = urllib.request.Request(f'http://127.0.0.1:{server.server_port}/api/offline-answers', headers={'Cookie': 'jarvis_session=' + server.app.session})
        with patch.object(offline_answers, 'OllamaProvider', Local):
            Local.tags = {'models': [{'name': 'qwen3:4b'}]}
            with urllib.request.urlopen(request, timeout=10) as response:
                self.assertEqual(json.load(response), {'available': True, 'model': 'qwen3:4b', 'reason': 'Ready: answers offline when no provider can be reached.', 'enabled': True})
            Local.tags = OllamaError('offline')
            with urllib.request.urlopen(request, timeout=10) as response:
                status = json.load(response)
            self.assertEqual((status['available'], status['reason']), (False, 'Ollama is not running on this PC.'))


if __name__ == '__main__':
    unittest.main()
