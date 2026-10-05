"""Speech through Qwen as well (release 1.0.15, scope item 5): speech recognition by the chosen AI provider
behind one setting; local Whisper stays the default and stands in when the cloud cannot.
"""
import base64
import http.client
import io
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

import providers
from server import App, Handler, Server
from store import Store

QWEN = {'JARVIS_PROVIDER': 'qwen', 'DASHSCOPE_API_KEY': 'qwen-test-key'}
OPENAI = {'JARVIS_PROVIDER': 'openai', 'OPENAI_API_KEY': 'openai-test-key'}
PCM = bytes(32000)  # one second of silence, 16 kHz mono 16-bit


class ProviderTests(unittest.TestCase):
    def test_the_chosen_provider_does_the_cloud_recognition_when_its_key_is_there(self):
        for env, name, label in ((QWEN, 'qwen', 'Qwen'), (OPENAI, 'openai', 'OpenAI')):
            with patch.dict(os.environ, env, clear=True):
                self.assertEqual(providers.cloud_speech(), name)
                capabilities = providers.capabilities()
                self.assertEqual((capabilities['transcription'], capabilities['transcription_provider']), (True, label))
        # The other provider's key does not count: recognition follows the provider the owner chose.
        for env in ({'JARVIS_PROVIDER': 'qwen', 'OPENAI_API_KEY': 'x'}, {'JARVIS_PROVIDER': 'openai', 'DASHSCOPE_API_KEY': 'x'}, {}):
            with patch.dict(os.environ, env, clear=True):
                self.assertIsNone(providers.cloud_speech())
                capabilities = providers.capabilities()
                self.assertEqual((capabilities['transcription'], capabilities['transcription_provider']), (False, None))

    def test_the_qwen_request_is_the_documented_one(self):
        answer = {'choices': [{'message': {'content': ' Set a timer for 5 minutes. ', 'annotations': [{'language': 'en'}]}}]}
        with patch.dict(os.environ, QWEN, clear=True), patch.object(providers, 'request', return_value=answer) as sent:
            self.assertEqual(providers.transcribe(b'RIFFdata', 'audio/wav'), {'text': 'Set a timer for 5 minutes.'})
        url, body, headers = sent.call_args.args
        self.assertEqual(url, 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions')
        self.assertEqual(headers, {'Authorization': 'Bearer qwen-test-key'})
        self.assertEqual(sent.call_args.kwargs['operation'], 'speech recognition')
        self.assertEqual(body, {'model': 'qwen3-asr-flash', 'stream': False, 'asr_options': {'enable_itn': True, 'language': 'en'},
                                'messages': [{'role': 'user', 'content': [{'type': 'input_audio', 'input_audio': {'data': 'data:audio/wav;base64,' + base64.b64encode(b'RIFFdata').decode()}}]}]})
        # The key file can name another model, and an empty language line lets Alibaba detect the language.
        with patch.dict(os.environ, {**QWEN, 'QWEN_ASR_MODEL': 'qwen3-asr-flash-2026-02-10', 'QWEN_ASR_LANGUAGE': ''}, clear=True), \
                patch.object(providers, 'request', return_value={'choices': [{'message': {'content': [{'text': 'hello'}, {'text': 'there'}]}}]}) as sent:
            self.assertEqual(providers.qwen_transcribe(b'x', 'audio/mpeg;codecs=mp3'), {'text': 'hello there'})
        body = sent.call_args.args[1]
        self.assertEqual((body['model'], body['asr_options']), ('qwen3-asr-flash-2026-02-10', {'enable_itn': True}))
        self.assertTrue(body['messages'][0]['content'][0]['input_audio']['data'].startswith('data:audio/mpeg;base64,'))

    def test_what_qwen_recognition_refuses_before_sending(self):
        with patch.dict(os.environ, QWEN, clear=True), patch.object(providers, 'request', side_effect=AssertionError('nothing is sent')):
            with self.assertRaisesRegex(ValueError, 'WAV or MP3'):
                providers.qwen_transcribe(b'x', 'audio/webm')
            with self.assertRaisesRegex(ValueError, 'too large'):
                providers.qwen_transcribe(bytes(8 * 1024 * 1024), 'audio/wav')
        with patch.dict(os.environ, {'JARVIS_PROVIDER': 'qwen'}, clear=True), patch.object(providers, 'request', side_effect=AssertionError('nothing is sent')):
            with self.assertRaisesRegex(providers.ProviderError, 'needs DASHSCOPE_API_KEY'):
                providers.transcribe(b'x', 'audio/wav')
        with patch.dict(os.environ, {'JARVIS_PROVIDER': 'groq', 'OPENAI_API_KEY': 'x'}, clear=True), patch('urllib.request.urlopen') as call:
            with self.assertRaisesRegex(providers.ProviderError, 'openai or qwen'):
                providers.transcribe(b'x', 'audio/wav')
            call.assert_not_called()

    def test_a_qwen_refusal_or_an_empty_answer_is_named_as_speech_recognition(self):
        refusal = urllib.error.HTTPError('https://dashscope-intl.aliyuncs.com/x', 403, 'Forbidden', {}, io.BytesIO(json.dumps({'error': {'code': 'AccessDenied.Unpurchased', 'message': 'no'}}).encode()))
        with patch.dict(os.environ, QWEN, clear=True), patch('urllib.request.urlopen', side_effect=refusal):
            with self.assertRaises(providers.ProviderError) as failed:
                providers.transcribe(b'x', 'audio/wav')
        self.assertTrue(str(failed.exception).startswith('Qwen speech recognition: '), str(failed.exception))
        # Anything else than text is an error, never "nothing was said" (review of this item).
        def content(value):
            return {'choices': [{'message': {'content': value}}]}
        for odd in ({}, {'choices': []}, {'choices': [{'message': {}}]}, content(None), content({'text': 'x'}), content(5),
                    content([{'text': None}]), content([{'text': 'a'}, 'b']), content([5])):
            with patch.dict(os.environ, QWEN, clear=True), patch.object(providers, 'request', return_value=odd):
                with self.assertRaisesRegex(providers.ProviderError, 'no text in the answer'):
                    providers.transcribe(b'x', 'audio/wav')
        with patch.dict(os.environ, QWEN, clear=True), patch.object(providers, 'request', return_value=content('')):
            self.assertEqual(providers.transcribe(b'x', 'audio/wav'), {'text': ''})  # silence: no words, no error

    def test_openai_recognition_is_unchanged(self):
        with patch.dict(os.environ, OPENAI, clear=True), patch.object(providers, 'request', return_value={'text': 'hello'}) as sent:
            self.assertEqual(providers.transcribe(b'audio', 'audio/webm'), {'text': 'hello'})
        self.assertEqual(sent.call_args.args[0], 'https://api.openai.com/v1/audio/transcriptions')
        self.assertEqual(sent.call_args.kwargs['timeout'], 60)
        for odd in ({}, [], {'text': None}, {'text': 5}):
            with patch.dict(os.environ, OPENAI, clear=True), patch.object(providers, 'request', return_value=odd):
                with self.assertRaisesRegex(providers.ProviderError, 'no text in the answer'):
                    providers.transcribe(b'audio', 'audio/webm')

    def test_with_a_time_limit_there_is_one_short_request_and_no_second_try(self):
        slow = providers.ProviderError('OpenAI transcription: Connection timed out. Try again shortly.')
        with patch.dict(os.environ, OPENAI, clear=True), patch.object(providers, 'request', side_effect=slow) as sent, patch('time.sleep') as wait:
            with self.assertRaises(providers.ProviderError):
                providers.transcribe(b'audio', 'audio/wav', timeout=8)
        self.assertEqual((sent.call_count, sent.call_args.kwargs['timeout']), (1, 8))
        wait.assert_not_called()
        with patch.dict(os.environ, QWEN, clear=True), patch.object(providers, 'request', return_value={'choices': [{'message': {'content': 'hi'}}]}) as sent:
            providers.transcribe(b'audio', 'audio/wav', timeout=8)
        self.assertEqual(sent.call_args.kwargs['timeout'], 8)

    def test_a_request_that_carries_a_key_is_never_sent_on_to_another_address(self):
        seen = []

        class Redirecting(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def answer(self):
                seen.append((self.path, self.headers.get('Authorization')))
                if self.path == '/first':
                    self.send_response(302)
                    self.send_header('Location', f'http://127.0.0.1:{self.server.server_port}/second')
                    self.send_header('Content-Length', '0')
                    self.end_headers()
                else:
                    body = b'{"ok": true}'
                    self.send_response(200)
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
            do_GET = do_POST = answer

        server = ThreadingHTTPServer(('127.0.0.1', 0), Redirecting)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            first = f'http://127.0.0.1:{server.server_port}/first'
            with self.assertRaises(providers.ProviderError):
                providers.request(first, {'recording': 'x'}, {'Authorization': 'Bearer secret'})
            self.assertEqual(seen, [('/first', 'Bearer secret')])  # the key went to the first address only
            del seen[:]
            self.assertEqual(providers.request(first), {'ok': True})  # without a key a redirect is followed as before
            self.assertEqual([path for path, _ in seen], ['/first', '/second'])
        finally:
            server.shutdown()
            thread.join()
            server.server_close()


class CoreTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.app = App(folder.name)
        self.body = {'data': base64.b64encode(PCM).decode()}
        self.local = patch.object(self.app.local_stt, 'transcribe', return_value={'text': 'local words', 'latency_ms': 5, 'local': True})

    def test_on_this_pc_by_default_and_nothing_is_sent(self):
        self.assertEqual(self.app.store.settings()['speech_recognition'], 'local')
        with patch.dict(os.environ, QWEN, clear=True), self.local as local, patch.object(providers, 'transcribe', side_effect=AssertionError('nothing is sent')):
            result = self.app.transcribe_speech(self.body)
        self.assertEqual((result['text'], result['engine']), ('local words', 'this PC'))
        local.assert_called_once_with(self.body)

    def test_the_cloud_when_the_owner_chose_it(self):
        self.app.store.save_settings({'speech_recognition': 'cloud'})
        with patch.dict(os.environ, QWEN, clear=True), self.local as local, patch.object(providers, 'transcribe', return_value={'text': ' cloud words '}) as cloud:
            result = self.app.transcribe_speech(self.body)
        self.assertEqual((result['text'], result['engine'], result['local'], result['audio_seconds']), ('cloud words', 'Qwen', False, 1.0))
        local.assert_not_called()
        recording, mime = cloud.call_args.args
        self.assertEqual(mime, 'audio/wav')
        self.assertEqual(cloud.call_args.kwargs, {'timeout': 8})  # a few seconds, then this PC does it
        with wave.open(io.BytesIO(recording), 'rb') as sound:  # the microphone's own samples, written as a WAV file
            self.assertEqual((sound.getnchannels(), sound.getsampwidth(), sound.getframerate(), sound.readframes(sound.getnframes())), (1, 2, 16000, PCM))
        with patch.dict(os.environ, OPENAI, clear=True), self.local, patch.object(providers, 'transcribe', return_value={'text': 'x'}):
            self.assertEqual(self.app.transcribe_speech(self.body)['engine'], 'OpenAI')

    def test_when_the_cloud_cannot_this_pc_does_it_and_says_why(self):
        self.app.store.save_settings({'speech_recognition': 'cloud'})
        failure = providers.ProviderError('Qwen speech recognition: Authentication failed. Check your local credentials. (HTTP 401)')
        with patch.dict(os.environ, QWEN, clear=True), self.local as local, patch.object(providers, 'transcribe', side_effect=failure):
            result = self.app.transcribe_speech(self.body)
        self.assertEqual((result['text'], result['engine']), ('local words', 'this PC'))
        self.assertIn('Authentication failed', result['cloud_error'])
        local.assert_called_once()
        # No key for the chosen provider: this PC, and no attempt.
        with patch.dict(os.environ, {'JARVIS_PROVIDER': 'qwen'}, clear=True), self.local, patch.object(providers, 'transcribe', side_effect=AssertionError('no attempt')):
            self.assertEqual(self.app.transcribe_speech(self.body)['engine'], 'this PC')

    def test_whatever_goes_wrong_in_the_cloud_the_words_are_not_lost(self):  # review of this item
        self.app.store.save_settings({'speech_recognition': 'cloud'})
        for failure in (http.client.IncompleteRead(b'half'), http.client.BadStatusLine('x'), TypeError('sequence item 0: expected str instance'),
                        KeyError('text'), OSError('socket closed'), providers.ProviderError('Qwen speech recognition: no text in the answer.')):
            with patch.dict(os.environ, QWEN, clear=True), self.local as local, patch.object(providers, 'transcribe', side_effect=failure):
                result = self.app.transcribe_speech(self.body)
            self.assertEqual((result['text'], result['engine']), ('local words', 'this PC'), repr(failure))
            self.assertTrue(result['cloud_error'])
            self.assertNotIn('sequence item', result['cloud_error'])  # nothing of Python's own wording
            local.assert_called_once()
        with patch.dict(os.environ, QWEN, clear=True), self.local, patch.object(providers, 'transcribe', return_value={'text': None}):
            self.assertEqual(self.app.transcribe_speech(self.body)['engine'], 'this PC')
        # When this PC cannot either, the owner is told both reasons.
        with patch.dict(os.environ, QWEN, clear=True), patch.object(self.app.local_stt, 'transcribe', side_effect=ValueError('Local speech model is not installed. Run setup_local_voice.py first.')), \
                patch.object(providers, 'transcribe', side_effect=providers.ProviderError('Qwen speech recognition: Authentication failed. Check your local credentials. (HTTP 401)')):
            with self.assertRaises(ValueError) as both:
                self.app.transcribe_speech(self.body)
        self.assertIn('Local speech model is not installed', str(both.exception))
        self.assertIn('Authentication failed', str(both.exception))

    def test_never_the_cloud_while_the_emergency_stop_holds(self):
        self.app.store.save_settings({'speech_recognition': 'cloud'})
        self.app.emergency_stop('pc', 'test')
        with patch.dict(os.environ, QWEN, clear=True), self.local as local, patch.object(providers, 'transcribe', side_effect=AssertionError('nothing is sent')):
            self.assertEqual(self.app.transcribe_speech(self.body)['engine'], 'this PC')
        local.assert_called_once()

    def test_a_recording_that_is_not_one_is_refused_in_the_cloud_too(self):
        self.app.store.save_settings({'speech_recognition': 'cloud'})
        with patch.dict(os.environ, QWEN, clear=True), self.local as local, patch.object(providers, 'transcribe', side_effect=AssertionError('nothing is sent')):
            for bad in ({'data': 'not base64!'}, {'data': base64.b64encode(bytes(100)).decode()}, {'data': base64.b64encode(bytes(3201)).decode()}, {}):
                with self.assertRaises(ValueError):
                    self.app.transcribe_speech(bad)
        local.assert_not_called()

    def test_the_setting(self):
        store = self.app.store
        self.assertEqual(store.save_settings({'speech_recognition': 'cloud'})['speech_recognition'], 'cloud')
        for bad in ('whisper', '', 'CLOUD', True):
            with self.assertRaises(ValueError):
                store.save_settings({'speech_recognition': bad})
        with store.connect() as db:  # a value this version does not know reads as the private default
            db.execute("INSERT OR REPLACE INTO settings VALUES ('speech_recognition', '\"somewhere\"')")
        self.assertEqual(Store(store.root).settings()['speech_recognition'], 'local')


class RouteTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.server = Server(('127.0.0.1', 0), Handler)
        self.app = self.server.app = App(folder.name)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.body = {'data': base64.b64encode(PCM).decode()}

    def post(self, path):
        request = urllib.request.Request(f'http://127.0.0.1:{self.server.server_port}{path}', data=json.dumps(self.body).encode(),
                                         headers={'Content-Type': 'application/json', 'Cookie': 'jarvis_session=' + self.app.session})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def test_the_voice_lab_stays_on_this_pc_whatever_the_setting_says(self):  # review of this item
        self.app.store.save_settings({'speech_recognition': 'cloud'})
        with patch.dict(os.environ, QWEN, clear=True), patch.object(providers, 'transcribe', side_effect=AssertionError('the voice lab sends nothing')), \
                patch.object(self.app.local_stt, 'transcribe', return_value={'text': 'local words', 'local': True}) as local:
            self.assertEqual(self.post('/api/voice-lab/transcribe'), (200, {'text': 'local words', 'local': True}))
        local.assert_called_once()

    def test_the_windows_microphone_has_its_own_route_and_the_old_cloud_route_is_gone(self):
        self.app.store.save_settings({'speech_recognition': 'cloud'})
        with patch.dict(os.environ, QWEN, clear=True), patch.object(providers, 'transcribe', return_value={'text': 'cloud words'}) as cloud:
            status, result = self.post('/api/speech-to-text')
        self.assertEqual((status, result['text'], result['engine']), (200, 'cloud words', 'Qwen'))
        cloud.assert_called_once()
        # The older route sent any recording to the cloud whatever the setting said: it no longer exists.
        with patch.dict(os.environ, QWEN, clear=True), patch.object(providers, 'transcribe', side_effect=AssertionError('nothing is sent')):
            self.assertEqual(self.post('/api/transcribe')[0], 404)


if __name__ == '__main__':
    unittest.main()
