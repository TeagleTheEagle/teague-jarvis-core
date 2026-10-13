"""Provider refusals in our own words (fix list item 5): a billing or credit limit (HTTP 402) is told
apart from a temporary rate limit (HTTP 429), and the upstream body is never shown. OpenRouter is the only AI
provider since 2026-10-13. Offline: every request is mocked and no key is real."""
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

OPENROUTER = 'https://openrouter.ai/api/v1/chat/completions'
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

    def test_openrouter_no_credit_says_so_and_sets_no_pause(self):
        env = {'JARVIS_PROVIDER': 'openrouter', 'OPENROUTER_API_KEY': 'test-only'}
        exc = self.chat_error(env, refusal(OPENROUTER, 402, error_body()))
        self.assertIn('OpenRouter chat: OpenRouter has no credit for this request', str(exc))
        self.assertIn('(HTTP 402)', str(exc))
        self.assertEqual((exc.limit, exc.retry_after, exc.status), ('billing', 0, 402))  # waiting will not help

    def test_openrouter_rate_limit_is_temporary_and_keeps_the_30_second_pause(self):
        env = {'JARVIS_PROVIDER': 'openrouter', 'OPENROUTER_API_KEY': 'test-only'}
        exc = self.chat_error(env, refusal(OPENROUTER, 429, error_body('rate_limit_exceeded')))
        self.assertIn('Rate limit or usage quota reached', str(exc))
        self.assertIn('check the OpenRouter plan', str(exc))
        self.assertEqual((exc.limit, exc.retry_after, exc.status), ('rate', 30, 429))

    def test_a_request_that_is_too_large_says_waiting_will_not_help(self):
        # 2026-10-05: one JARVIS question was larger than a free plan's limit per minute (HTTP 413).
        exc = self.request_error(OPENROUTER, 413)
        for text in ('OpenRouter chat: The request is larger than', 'Waiting will not help', '(HTTP 413)'):
            self.assertIn(text, str(exc))
        self.assertEqual((exc.limit, exc.retry_after, exc.status), (None, 0, 413))

    def test_402_names_the_fish_dashboard_only_for_fish(self):
        exc = self.request_error(OPENROUTER, 402)
        self.assertIn('OpenRouter has no credit', str(exc))
        self.assertNotIn('Fish', str(exc))
        self.assertEqual(exc.limit, 'billing')
        exc = self.request_error('https://api.fish.audio/v1/tts', 402)
        self.assertIn('Fish Audio voice synthesis:', str(exc))
        self.assertIn('Fish developer dashboard', str(exc))

    def test_broken_bodies_only_lose_the_code(self):
        oversized = json.dumps({'error': {'code': 'insufficient_quota', 'padding': 'x' * 5000}}).encode()
        bodies = (b'[]', b'null', b'123', b'"x"', b'{"error":null}', b'{"error":[]}', b'{"error":{"code":429}}',
                  b'\xff\xfe\x00', b'[' * 4096, oversized, b'{"error":{"code":"insufficient_quota\\n"}}',
                  b'{"error":{"code":"<script>alert(1)</script>"}}')
        for body in bodies:
            with self.subTest(body=body[:40]):
                for url, status in ((OPENROUTER, 429), (OPENROUTER, 400), (OPENROUTER, 402)):
                    exc = self.request_error(url, status, body)
                    self.assertNotIn('<script>', str(exc))
                    self.assertNotIn('UPSTREAM', str(exc))  # nothing of the body is shown, whatever it holds

    def test_a_cut_off_body_still_gives_our_message(self):
        class CutOff(io.BytesIO):
            def read(self, *args):
                raise http.client.IncompleteRead(b'{"error":')
        error = urllib.error.HTTPError(OPENROUTER, 429, 'refused', {}, CutOff())
        with patch('urllib.request.urlopen', side_effect=error), self.assertRaises(providers.ProviderError) as caught:
            providers.request(OPENROUTER, {'model': 'm'})
        self.assertIn('(HTTP 429)', str(caught.exception))

    def test_tool_services_never_pause_voice(self):
        # 'search for x' calls SerpApi directly; its 429 (even with a long Retry-After) must not
        # pause voice commands the way an AI provider's rate limit does.
        exc = self.request_error('https://serpapi.com/search.json?q=x', 429, b'{}', {'retry-after': '3600'})
        self.assertEqual((exc.service, exc.retry_after), ('SerpApi', 0))
        exc = self.request_error('https://html.duckduckgo.com/html/?q=x', 429)
        self.assertIn('Rate limit reached. Wait before retrying', str(exc))
        self.assertNotIn('that service', str(exc))

    def test_messages_never_trigger_automatic_retries_and_keep_the_wearable_classification(self):
        for name in ('test_openrouter_no_credit_says_so_and_sets_no_pause',
                     'test_openrouter_rate_limit_is_temporary_and_keeps_the_30_second_pause',
                     'test_402_names_the_fish_dashboard_only_for_fish'):
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
