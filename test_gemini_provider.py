import os
import threading
import unittest
from unittest.mock import patch
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


if __name__ == '__main__':
    unittest.main()
