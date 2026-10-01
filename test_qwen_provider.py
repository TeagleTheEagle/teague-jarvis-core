import os
import threading
import unittest
from unittest.mock import patch
import providers


class QwenTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'JARVIS_PROVIDER': 'qwen', 'DASHSCOPE_API_KEY': 'test-key'}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_tools_and_context_preserved_with_default_model_and_region(self):
        call = {'id': 'c1', 'type': 'function', 'function': {'name': 'lookup', 'arguments': '{}'}}
        messages = [{'role': 'system', 'content': 'Mr Teague, evidence required'}, {'role': 'assistant', 'content': 'Previous answer', '_response_output': []}]
        tools = [{'type': 'function', 'function': {'name': 'lookup', 'parameters': {'type': 'object'}}}]
        with patch.object(providers, 'request', return_value={'choices': [{'finish_reason': 'tool_calls', 'message': {'tool_calls': [call]}}]}) as request:
            result = providers.chat(messages, tools, lambda *args: None, threading.Event())
        self.assertEqual(result['tool_calls'], [call])
        url, body, headers = request.call_args.args[:3]
        self.assertEqual(url, 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions')
        self.assertEqual(body['model'], 'qwen3.8-max')
        self.assertEqual(body['tools'], tools)
        self.assertNotIn('_response_output', body['messages'][1])
        self.assertEqual(headers['Authorization'], 'Bearer test-key')

    def test_region_and_model_are_configurable(self):
        os.environ.update(DASHSCOPE_BASE_URL='https://example-workspace.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1/',
                          QWEN_MODEL='qwen3.8-flash')
        with patch.object(providers, 'request', return_value={'choices': [{'finish_reason': 'stop', 'message': {'content': 'Hi'}}]}) as request:
            providers.chat([], [], lambda *args: None, threading.Event())
        self.assertEqual(request.call_args.args[0], 'https://example-workspace.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1/chat/completions')
        self.assertEqual(request.call_args.args[1]['model'], 'qwen3.8-flash')

    def test_key_is_never_sent_outside_alibaba_cloud(self):
        for base in ('https://evil.example/v1', 'http://dashscope-intl.aliyuncs.com/compatible-mode/v1',
                     'https://aliyuncs.com.evil.example/v1'):
            os.environ['DASHSCOPE_BASE_URL'] = base
            with patch.object(providers, 'request') as request, self.assertRaises(providers.ProviderError):
                providers.chat([], [], lambda *args: None, threading.Event())
            request.assert_not_called()

    def test_missing_key_never_falls_back(self):
        os.environ.pop('DASHSCOPE_API_KEY')
        os.environ['OPENAI_API_KEY'] = 'another-key'
        with patch.object(providers, 'request') as request, self.assertRaises(providers.ProviderError):
            providers.chat([], [], lambda *args: None, threading.Event())
        request.assert_not_called()

    def test_vision_needs_an_authorised_vision_model(self):
        with patch.object(providers, 'request') as request, self.assertRaisesRegex(providers.ProviderError, 'QWEN_VISION_MODEL'):
            providers.chat([], [], lambda *args: None, threading.Event(), vision=True)
        request.assert_not_called()
        self.assertFalse(providers.capabilities()['vision'])
        os.environ['QWEN_VISION_MODEL'] = 'qwen-vl-max'
        self.assertTrue(providers.capabilities()['vision'])

    def test_incomplete_answers_not_emitted(self):
        for reason in ('length', 'content_filter', None):
            emitted = []
            with patch.object(providers, 'request', return_value={'choices': [{'finish_reason': reason, 'message': {'content': 'partial'}}]}), self.assertRaises(providers.ProviderError):
                providers.chat([], [], lambda *args: emitted.append(args), threading.Event())
            self.assertEqual(emitted, [])

    def test_capabilities_report_qwen_and_keep_voice(self):
        os.environ.update(FISH_API_KEY='voice-key', FISH_VOICE_ID='voice-id')
        caps = providers.capabilities()
        self.assertEqual(caps['brain'], 'Qwen configured')
        self.assertEqual(caps['model'], 'qwen3.8-max')
        self.assertEqual(caps['voice_provider'], 'fish')
        os.environ.pop('DASHSCOPE_API_KEY')
        self.assertEqual(providers.capabilities()['brain'], 'Qwen not configured')

    def test_health_check_uses_minimal_completion(self):
        with patch.object(providers, 'request', return_value={'choices': [{'message': {'content': 'OK'}}]}) as request:
            checks = providers.live_health()
        self.assertEqual(checks['Chat model access']['status'], 'reachable')
        url, body = request.call_args_list[0].args[:2]
        self.assertTrue(url.endswith('/chat/completions'))
        self.assertLessEqual(body['max_completion_tokens'], 8)
        self.assertFalse(body['enable_thinking'])


class QwenErrorTests(unittest.TestCase):
    def raise_http(self, status, body):
        import io, urllib.error
        error = urllib.error.HTTPError('https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions',
                                       status, 'error', {}, io.BytesIO(body))
        with patch('urllib.request.urlopen', side_effect=error), self.assertRaises(providers.ProviderError) as raised:
            providers.request('https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions', {'model': 'x'})
        return str(raised.exception)

    def test_overdue_account_is_explained_without_echoing_the_response(self):
        message = self.raise_http(400, b'{"error":{"code":"Arrearage","message":"UPSTREAM-DETAIL-NOT-SHOWN"}}')
        self.assertIn('Qwen chat', message)
        self.assertIn('balance is overdue or empty', message)
        self.assertNotIn('UPSTREAM-DETAIL-NOT-SHOWN', message)

    def test_other_errors_keep_the_generic_label(self):
        message = self.raise_http(400, b'{"error":{"code":"InvalidParameter","message":"x"}}')
        self.assertIn('Request rejected', message)
        self.assertIn('Request rejected', self.raise_http(400, b'not json'))


if __name__ == '__main__':
    unittest.main()
