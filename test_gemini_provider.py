import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import providers


class GeminiTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'JARVIS_PROVIDER': 'gemini', 'GEMINI_API_KEY': 'test-key'}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_tools_and_context_preserved(self):
        call = {'id': 'c1', 'type': 'function', 'function': {'name': 'lookup', 'arguments': '{}'}}
        messages = [{'role': 'system', 'content': 'Mr Teague, evidence required'}, {'role': 'assistant', 'content': 'Previous answer', '_response_output': []}]
        tools = [{'type': 'function', 'function': {'name': 'lookup', 'parameters': {'type': 'object'}}}]
        with patch.object(providers, 'request', return_value={'choices': [{'finish_reason': 'tool_calls', 'message': {'tool_calls': [call]}}]}) as request:
            result = providers.chat(messages, tools, lambda *args: None, threading.Event())
        self.assertEqual(result['tool_calls'], [call])
        body = request.call_args.args[1]
        self.assertEqual(body['tools'], tools)
        self.assertEqual(body['messages'][0], messages[0])
        self.assertNotIn('_response_output', body['messages'][1])
        self.assertIn('generativelanguage.googleapis.com', request.call_args.args[0])

    def test_missing_key_never_falls_back(self):
        os.environ.pop('GEMINI_API_KEY')
        os.environ['OPENAI_API_KEY'] = 'another-key'
        with patch.object(providers, 'request') as request, self.assertRaises(providers.ProviderError):
            providers.chat([], [], lambda *args: None, threading.Event())
        request.assert_not_called()

    def test_incomplete_and_blocked_answers_not_emitted(self):
        for reason in ('length', 'content_filter', None):
            emitted = []
            with patch.object(providers, 'request', return_value={'choices': [{'finish_reason': reason, 'message': {'content': 'partial'}}]}), self.assertRaises(providers.ProviderError):
                providers.chat([], [], lambda *args: emitted.append(args), threading.Event())
            self.assertEqual(emitted, [])

    def test_cancelled_request_not_sent(self):
        cancel = threading.Event()
        cancel.set()
        with patch.object(providers, 'request') as request:
            self.assertIsNone(providers.chat([], [], lambda *args: None, cancel))
        request.assert_not_called()

    def test_capabilities_keep_voice(self):
        os.environ.update(FISH_API_KEY='voice-key', FISH_VOICE_ID='voice-id')
        caps = providers.capabilities()
        self.assertEqual(caps['brain'], 'Gemini configured')
        self.assertEqual(caps['voice_provider'], 'fish')

    def sent_model(self):
        reply = {'choices': [{'finish_reason': 'stop', 'message': {'content': 'ok'}}]}
        with patch.object(providers, 'request', return_value=reply) as request:
            providers.chat([], [], lambda *args: None, threading.Event())
        return request.call_args.args[1]['model']

    def test_default_model_is_googles_current_stable_flash(self):
        # Fix list item 6: since 2026-09-18 Google serves gemini-2.5 only to projects that used it before.
        self.assertEqual(providers.GEMINI_DEFAULT_MODEL, 'gemini-3.8-flash')
        self.assertEqual(self.sent_model(), 'gemini-3.8-flash')
        self.assertEqual(providers.capabilities()['model'], 'gemini-3.8-flash')

    def test_a_model_line_in_the_key_file_wins_and_an_empty_one_does_not(self):
        os.environ['GEMINI_MODEL'] = 'gemini-3.5-flash-lite'
        self.assertEqual((self.sent_model(), providers.capabilities()['model']), ('gemini-3.5-flash-lite',) * 2)
        os.environ['GEMINI_MODEL'] = ''  # "GEMINI_MODEL=" with no value
        self.assertEqual((self.sent_model(), providers.capabilities()['model']), ('gemini-3.8-flash',) * 2)

    def test_health_check_asks_for_the_default_model(self):
        with patch.object(providers, 'request', return_value={'id': 'models/gemini-3.8-flash'}) as request:
            checks = providers.live_health()
        self.assertEqual(checks['Chat model access']['status'], 'reachable')
        self.assertTrue(request.call_args_list[0].args[0].endswith('/v1beta/openai/models/gemini-3.8-flash'))

    def test_tool_call_extra_fields_are_returned_unchanged(self):
        # Gemini 3 refuses (HTTP 400) a follow-up that drops a tool call's thought signature.
        call = {'id': 'c1', 'type': 'function', 'function': {'name': 'lookup', 'arguments': '{}'},
                'extra_content': {'google': {'thought_signature': 'opaque-signature'}}}
        reply = {'choices': [{'finish_reason': 'tool_calls', 'message': {'tool_calls': [call]}}]}
        with patch.object(providers, 'request', return_value=reply):
            result = providers.chat([], [], lambda *args: None, threading.Event())
        self.assertEqual(result['tool_calls'], [call])
        follow_up = [result, {'role': 'tool', 'tool_call_id': 'c1', 'content': '{}'}]
        with patch.object(providers, 'request', return_value={'choices': [{'finish_reason': 'stop', 'message': {'content': 'ok'}}]}) as request:
            providers.chat(follow_up, [], lambda *args: None, threading.Event())
        self.assertEqual(request.call_args.args[1]['messages'][0]['tool_calls'], [call])

    def test_setup_tool_saves_the_same_default(self):
        # configure_gemini.py needs tkinter, which the release's Python does not have: stub it.
        with tempfile.TemporaryDirectory() as folder, \
                patch.dict(sys.modules, {'tkinter': MagicMock(), 'tkinter.ttk': MagicMock()}):
            import configure_gemini
            (Path(folder) / '.env').write_text('OTHER_SETTING=kept\nGEMINI_MODEL=gemini-2.5-flash\n', encoding='utf-8')
            with patch.object(configure_gemini, 'ROOT', Path(folder)):
                configure_gemini.save_config('opaque-test-value')
            lines = (Path(folder) / '.env').read_text(encoding='utf-8').splitlines()
            sys.modules.pop('configure_gemini', None)
        self.assertIn('OTHER_SETTING=kept', lines)
        self.assertIn('GEMINI_MODEL=gemini-3.8-flash', lines)
        self.assertNotIn('GEMINI_MODEL=gemini-2.5-flash', lines)


if __name__ == '__main__':
    unittest.main()
