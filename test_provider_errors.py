"""Provider refusals in our own words (fix list item 5): a billing, credit or quota limit is told
apart from a temporary rate limit, per provider, from documented error codes only. Offline: every
request is mocked and no key is real."""
import http.client
import io
import json
import os
import re
import threading
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

import providers

OPENAI = 'https://api.openai.com/v1/chat/completions'
QWEN = 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions'
GEMINI = 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions'
UPSTREAM = 'UPSTREAM-DETAIL-NOT-SHOWN'
RETRY_TRIGGERS = ('connection failed', 'timed out', 'stream failed')  # providers.py and server.py retry on these


def error_body(code=None, kind=None):
    error = {'message': UPSTREAM}
    if code is not None:
        error['code'] = code
    if kind is not None:
        error['type'] = kind
    return json.dumps({'error': error}).encode()


def refusal(url, status, body=b'{}', headers=None):
    return urllib.error.HTTPError(url, status, 'refused', headers or {}, io.BytesIO(body))


class ProviderErrorTests(unittest.TestCase):
    def setUp(self):
        self.messages = []

    def request_error(self, url, status, body=b'{}', headers=None):
        with patch('urllib.request.urlopen', side_effect=refusal(url, status, body, headers)) as call, \
                self.assertRaises(providers.ProviderError) as caught:
            providers.request(url, {'model': 'm'}, {'Authorization': 'Bearer test-only'})
        self.assertEqual(call.call_count, 1)
        self.messages.append(str(caught.exception))
        self.assertNotIn(UPSTREAM, str(caught.exception))
        self.assertNotIn('test-only', str(caught.exception))
        return caught.exception

    def chat_error(self, env, error):
        with patch.dict(os.environ, env, clear=True), patch('urllib.request.urlopen', side_effect=error) as call, \
                self.assertRaises(providers.ProviderError) as caught:
            providers.chat([{'role': 'user', 'content': 'hi'}], [], lambda *args: None, threading.Event())
        self.assertEqual(call.call_count, 1)  # one request, no automatic retry
        self.messages.append(str(caught.exception))
        self.assertNotIn(UPSTREAM, str(caught.exception))
        return caught.exception

    def test_openai_no_credits_says_so_and_sets_no_pause(self):
        env = {'JARVIS_PROVIDER': 'openai', 'OPENAI_API_KEY': 'test-only', 'OPENAI_MODEL': 'gpt-4o-mini'}
        exc = self.chat_error(env, refusal(OPENAI, 429, error_body('insufficient_quota', 'insufficient_quota'), {'retry-after': '20'}))
        for text in ('OpenAI chat:', 'no API credits', 'waiting will not help', 'HTTP 429, insufficient_quota', 'No keys were rotated'):
            self.assertIn(text, str(exc))
        for text in ('Groq', 'Rate limit reached', 'test-only'):
            self.assertNotIn(text, str(exc))
        self.assertEqual((exc.limit, exc.service, exc.retry_after), ('billing', 'OpenAI', 0))
        self.assertNotIn('gpt-4o-mini', providers._cooldowns)

    def test_openai_responses_path_no_credits(self):
        # The owner's OpenAI model may use the Responses API (gpt-6-*); same wording there.
        env = {'JARVIS_PROVIDER': 'openai', 'OPENAI_API_KEY': 'test-only', 'OPENAI_MODEL': 'gpt-6-test'}
        for code in ('insufficient_quota', 'credit_balance_exhausted'):
            with self.subTest(code=code):
                exc = self.chat_error(env, refusal('https://api.openai.com/v1/responses', 429, error_body(code)))
                self.assertIn('OpenAI chat:', str(exc))
                self.assertIn('no API credits', str(exc))
                self.assertEqual((exc.limit, exc.retry_after), ('billing', 0))

    def test_openai_documented_billing_codes(self):
        for code, words in (('credit_balance_exhausted', 'no API credits'), ('organization_spend_limit_exceeded', 'spend limit'),
                            ('project_spend_limit_exceeded', 'spend limit'), ('organization_usage_limit_exceeded', 'usage limit')):
            with self.subTest(code=code):
                exc = self.request_error(OPENAI, 429, error_body(code))
                self.assertIn(words, str(exc))
                self.assertIn(f'(HTTP 429, {code})', str(exc))
                self.assertEqual((exc.limit, exc.retry_after), ('billing', 0))
        exc = self.request_error(OPENAI, 429, error_body('some_new_code', 'insufficient_quota'))  # only the type is known
        self.assertIn('billing or quota limit', str(exc))
        self.assertIn('(HTTP 429, type insufficient_quota)', str(exc))
        self.assertNotIn('some_new_code', str(exc))

    def test_openai_rate_limit_is_temporary_and_keeps_the_30_second_pause(self):
        env = {'JARVIS_PROVIDER': 'openai', 'OPENAI_API_KEY': 'test-only', 'OPENAI_MODEL': 'gpt-4o-mini'}
        exc = self.chat_error(env, refusal(OPENAI, 429, error_body('rate_limit_exceeded', 'requests')))
        self.assertIn('Rate limit reached (temporary)', str(exc))
        self.assertEqual((exc.limit, exc.retry_after), ('rate', 30))
        exc = self.chat_error(env, refusal(OPENAI, 429, b'not json'))  # no code: say both, never claim credits
        self.assertIn('Rate limit or usage quota reached', str(exc))
        self.assertIn('check the OpenAI plan, usage limits and billing', str(exc))
        self.assertEqual((exc.limit, exc.retry_after), ('rate', 30))

    def test_qwen_insufficient_quota_is_a_short_throttle_not_credit(self):
        exc = self.request_error(QWEN, 429, error_body('insufficient_quota'))
        self.assertIn('Qwen chat: Rate limit reached (temporary)', str(exc))
        for text in ('credits', 'billing limit'):
            self.assertNotIn(text, str(exc))
        self.assertEqual(exc.limit, 'rate')
        for code in ('Throttling', 'Throttling.RateQuota', 'limit_requests', 'Throttling.AllocationQuota'):
            with self.subTest(code=code):
                self.assertEqual(self.request_error(QWEN, 429, error_body(code)).limit, 'rate')

    def test_qwen_billing_codes(self):
        for code in ('PrepaidBillOverdue', 'PostpaidBillOverdue', 'BudgetLimitExceeded', 'CommodityNotPurchased'):
            with self.subTest(code=code):
                exc = self.request_error(QWEN, 429, error_body(code))
                self.assertIn('Alibaba Cloud', str(exc))
                self.assertIn('waiting will not help', str(exc))
                self.assertIn(f'(HTTP 429, {code})', str(exc))
                self.assertEqual((exc.limit, exc.retry_after), ('billing', 0))
        exc = self.request_error(QWEN, 400, error_body('Arrearage'))  # unchanged wording
        self.assertIn('account balance is overdue or empty', str(exc))
        self.assertEqual(exc.limit, 'billing')

    def test_gemini_429_and_402(self):
        exc = self.chat_error({'JARVIS_PROVIDER': 'gemini', 'GEMINI_API_KEY': 'test-only'},
                              refusal(GEMINI, 429, b'[{"error":{"code":429,"status":"RESOURCE_EXHAUSTED","message":"UPSTREAM-DETAIL-NOT-SHOWN"}}]'))
        self.assertIn('Gemini chat: Rate limit reached (temporary)', str(exc))
        self.assertIn('midnight Pacific', str(exc))
        self.assertNotIn('credits', str(exc))
        self.assertEqual(exc.limit, 'rate')
        exc = self.request_error(GEMINI, 402)
        self.assertIn('Gemini Prepay credit', str(exc))
        self.assertNotIn('Fish', str(exc))
        self.assertEqual(exc.limit, 'billing')
        self.assertIn('Fish developer dashboard', str(self.request_error('https://api.fish.audio/v1/tts', 402)))

    def test_broken_bodies_only_lose_the_code(self):
        oversized = json.dumps({'error': {'code': 'insufficient_quota', 'padding': 'x' * 5000}}).encode()
        bodies = (b'[]', b'null', b'123', b'"x"', b'{"error":null}', b'{"error":[]}', b'{"error":{"code":429}}',
                  b'\xff\xfe\x00', b'[' * 4096, oversized, b'{"error":{"code":"insufficient_quota\\n"}}',
                  b'{"error":{"code":"<script>alert(1)</script>"}}')
        for body in bodies:
            with self.subTest(body=body[:40]):
                for url, status in ((OPENAI, 429), (QWEN, 429), (QWEN, 400)):
                    exc = self.request_error(url, status, body)
                    self.assertNotIn('<script>', str(exc))
                    self.assertNotEqual(exc.limit, 'billing')  # no documented code was readable

    def test_a_cut_off_body_still_gives_our_message(self):
        class CutOff(io.BytesIO):
            def read(self, *args):
                raise http.client.IncompleteRead(b'{"error":')
        error = urllib.error.HTTPError(OPENAI, 429, 'refused', {}, CutOff())
        with patch('urllib.request.urlopen', side_effect=error), self.assertRaises(providers.ProviderError) as caught:
            providers.request(OPENAI, {'model': 'm'})
        self.assertIn('(HTTP 429)', str(caught.exception))

    def test_tool_services_never_pause_voice(self):
        # 'search for x' calls SerpApi directly; its 429 (even with a long Retry-After) must not
        # pause voice commands the way an AI provider's rate limit does.
        exc = self.request_error('https://serpapi.com/search.json?q=x', 429, b'{}', {'retry-after': '3600'})
        self.assertEqual((exc.service, exc.retry_after), ('SerpApi', 0))
        exc = self.request_error('https://html.duckduckgo.com/html/?q=x', 429)
        self.assertIn('Rate limit reached. Wait before retrying', str(exc))
        self.assertNotIn('that service', str(exc))

    def test_rate_limit_names_the_provider_and_bounds_the_wait(self):
        self.addCleanup(lambda: [providers._cooldowns.pop(m, None) for m in ('m1', 'm2', 'm3')])
        error = providers.rate_limit('m1', {'retry-after': '5'}, 'OpenAI')
        self.messages.append(str(error))
        for text in ('OpenAI', 'about 5 seconds', 'HTTP 429'):
            self.assertIn(text, str(error))
        for text in ('Groq', 'Fish'):
            self.assertNotIn(text, str(error))
        self.assertIn('Groq', str(providers.rate_limit('m2', {})))  # the default stays Groq
        for value, seconds in (('0', 1), ('-5', 1), ('999999', 86400), ('nan', 60), ('inf', 60), ('Wed, 21 Oct 2026 07:28:00 GMT', 60)):
            with self.subTest(value=value):
                self.assertEqual(providers.rate_limit('m3', {'retry-after': value}).retry_after, seconds)
        self.assertEqual(providers.rate_limit('m3', None).retry_after, 60)

    def test_cooldown_message_names_the_active_provider(self):
        providers._cooldowns['gpt-4o-mini'] = providers.time.time() + 50
        self.addCleanup(providers._cooldowns.pop, 'gpt-4o-mini', None)
        env = {'JARVIS_PROVIDER': 'openai', 'OPENAI_API_KEY': 'test-only', 'OPENAI_MODEL': 'gpt-4o-mini'}
        with patch.dict(os.environ, env, clear=True), patch('urllib.request.urlopen') as call, \
                self.assertRaises(providers.ProviderError) as caught:
            providers.chat([], [], lambda *args: None, threading.Event())
        call.assert_not_called()
        self.messages.append(str(caught.exception))
        self.assertIn('OpenAI rate limit', str(caught.exception))
        self.assertIn('No request was sent', str(caught.exception))
        self.assertNotIn('Groq', str(caught.exception))
        self.assertGreater(caught.exception.retry_after, 0)

    def test_messages_never_trigger_automatic_retries_and_keep_the_wearable_classification(self):
        for name in ('test_openai_no_credits_says_so_and_sets_no_pause', 'test_openai_documented_billing_codes',
                     'test_openai_rate_limit_is_temporary_and_keeps_the_30_second_pause', 'test_qwen_billing_codes',
                     'test_qwen_insufficient_quota_is_a_short_throttle_not_credit', 'test_gemini_429_and_402',
                     'test_rate_limit_names_the_provider_and_bounds_the_wait', 'test_cooldown_message_names_the_active_provider'):
            getattr(self, name)()
        for message in self.messages:
            with self.subTest(message=message[:70]):
                self.assertFalse(any(t in message.lower() for t in RETRY_TRIGGERS))
                if '429' in message:  # two of the patterns wearables/real_core.py classifies with
                    self.assertEqual(re.search(r'HTTP\s+(\d{3})', message).group(1), '429')
                    self.assertRegex(message, re.compile(r'quota|rate limit|credits', re.I))

    def test_interface_names_the_provider_not_always_groq(self):
        app = (Path(__file__).resolve().parent / 'static' / 'app.js').read_text(encoding='utf-8')
        self.assertNotIn('Groq cooldown', app)
        self.assertNotIn('Groq is cooling down', app)
        self.assertIn('event.data.provider', app)


if __name__ == '__main__':
    unittest.main()
