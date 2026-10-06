import base64
import io
import os
import unittest
import wave
from unittest.mock import patch
import providers


def wav(frames, rate=24000):
    out = io.BytesIO()
    with wave.open(out, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(frames)
    return out.getvalue()


class QwenVoiceTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'DASHSCOPE_API_KEY': 'test-key', 'QWEN_TTS_VOICE': 'jarvis-voice-id'}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_chunks_respect_limit_and_keep_every_word(self):
        text = ' '.join(f'Sentence number {i} has a few ordinary words in it.' for i in range(40)) + ' ' + 'x' * 1200
        chunks = providers.speech_chunks(text)
        self.assertTrue(all(0 < len(c) <= providers.QWEN_TTS_CHUNK for c in chunks))
        self.assertEqual(''.join(''.join(chunks).split()), ''.join(text.split()))
        self.assertTrue(chunks[0].endswith('.'))  # splits at sentence ends where possible

    def test_wav_clips_join_into_one_valid_file(self):
        joined = providers.join_audio([wav(b'\x01\x00' * 100), wav(b'\x02\x00' * 50)])
        with wave.open(io.BytesIO(joined), 'rb') as w:
            self.assertEqual(w.getnframes(), 150)
            self.assertEqual(w.getframerate(), 24000)
        self.assertEqual(providers.audio_mime(joined), 'audio/wav')
        self.assertEqual(providers.audio_mime(b'ID3\x04rest'), 'audio/mpeg')
        with self.assertRaises(providers.ProviderError):
            providers.join_audio([wav(b'\x00\x00' * 10), wav(b'\x00\x00' * 10, rate=16000)])

    def test_synthesis_request_and_presigned_download(self):
        calls = []
        def fake_request(url, data=None, headers=None, method=None, raw=False, timeout=35):
            calls.append((url, data, headers, raw))
            if raw:
                return wav(b'\x01\x00' * 100)
            return {'output': {'audio': {'url': 'https://dashscope-result-sgp.oss-ap-southeast-1.aliyuncs.com/a.wav', 'data': ''}}}
        with patch.object(providers, 'request', side_effect=fake_request):
            audio = providers.speech('Good evening, sir. All systems are ready.', 'auto')
        self.assertEqual(audio[:4], b'RIFF')
        url, body, headers, _ = calls[0]
        self.assertEqual(url, 'https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation')
        self.assertEqual(body['model'], 'qwen3-tts-vc-2026-01-22')
        self.assertEqual(body['input']['voice'], 'jarvis-voice-id')
        self.assertEqual(headers['Authorization'], 'Bearer test-key')
        download_url, _, download_headers, raw = calls[1]
        self.assertTrue(raw)
        self.assertIsNone(download_headers)  # the key is never sent to the audio download link

    def test_inline_audio_needs_no_download(self):
        with patch.object(providers, 'request', return_value={'output': {'audio': {'data': base64.b64encode(wav(b'\x01\x00' * 100)).decode()}}}) as request:
            providers.speech('Hello.', 'qwen')
        self.assertEqual(request.call_count, 1)

    def test_audio_links_outside_alibaba_cloud_are_refused(self):
        for url in ('https://evil.example/a.wav', 'http://evil.example/a.wav', 'https://aliyuncs.com.evil.example/a.wav',
                    'https://x.aliyuncs.com:8443/a.wav', 'ftp://x.aliyuncs.com/a.wav', 'http://aliyuncs.com/a.wav',
                    'http://[x.aliyuncs.com/a.wav', 5, ''):
            with patch.object(providers, 'request', return_value={'output': {'audio': {'url': url}}}) as request, \
                    self.assertRaises(providers.ProviderError):
                providers.speech('Hello.', 'qwen')
            self.assertEqual(request.call_count, 1)
        with patch.object(providers, 'request', return_value={'output': {'audio': {}}}) as request, \
                self.assertRaises(providers.ProviderError):
            providers.speech('Hello.', 'qwen')  # neither sound nor link in the answer
        self.assertEqual(request.call_count, 1)

    def test_plain_http_link_to_an_alibaba_file_server_is_fetched_over_https(self):
        # Seen on 2026-10-06: Alibaba's Beijing result server answers with http:// links; it speaks https at the same name.
        link = 'http://dashscope-result-bj.oss-cn-beijing.aliyuncs.com/1d/a1/sound.wav?Expires=1&OSSAccessKeyId=k&Signature=s%2F'
        calls = []
        def fake_request(url, data=None, headers=None, method=None, raw=False, timeout=35):
            calls.append((url, headers, raw))
            return wav(bytes([1, 0]) * 100) if raw else {'output': {'audio': {'url': link}}}
        with patch.object(providers, 'request', side_effect=fake_request):
            audio = providers.speech('Hello.', 'qwen')
        self.assertEqual(audio[:4], b'RIFF')
        self.assertEqual(calls[1], ('https://dashscope-result-bj.oss-cn-beijing.aliyuncs.com/1d/a1/sound.wav?Expires=1&OSSAccessKeyId=k&Signature=s%2F', None, True))
        self.assertEqual(providers.qwen_result_link('https://dashscope-result-sgp.oss-ap-southeast-1.aliyuncs.com/a.wav'),
                         'https://dashscope-result-sgp.oss-ap-southeast-1.aliyuncs.com/a.wav')
        self.assertIsNone(providers.qwen_result_link('http://dashscope-result-bj.oss-cn-beijing.aliyuncs.com:99999/a.wav'))
        self.assertEqual(providers.qwen_result_link('http://x.aliyuncs.com:80/A/B.wav?k=V'), 'https://x.aliyuncs.com/A/B.wav?k=V')
        self.assertEqual(providers.qwen_result_link('https://x.aliyuncs.com:443/a.wav'), 'https://x.aliyuncs.com/a.wav')
        self.assertIsNone(providers.qwen_result_link(None))
        self.assertIsNone(providers.qwen_result_link(['https://x.aliyuncs.com/a.wav']))

    def test_auto_prefers_qwen_only_when_configured(self):
        os.environ.update(FISH_API_KEY='fish-key', FISH_VOICE_ID='fish-voice')
        self.assertEqual(providers.capabilities()['voice_provider'], 'qwen')
        os.environ.pop('QWEN_TTS_VOICE')
        self.assertEqual(providers.capabilities()['voice_provider'], 'fish')
        with patch.object(providers, 'request', return_value=b'x' * 200) as request:
            providers.speech('Hello.', 'auto')
        self.assertIn('fish.audio', request.call_args.args[0])
        with self.assertRaisesRegex(providers.ProviderError, 'QWEN_TTS_VOICE'):
            providers.speech('Hello.', 'qwen')  # explicit choice never silently falls back

    def test_voice_profile_setting_accepts_qwen(self):
        import tempfile
        from store import Store
        with tempfile.TemporaryDirectory() as folder:
            store = Store(folder)
            store.save_settings({'voice_profile': 'qwen'})
            self.assertEqual(store.settings()['voice_profile'], 'qwen')


    def test_tts_url_override_for_workspace_accounts_is_alibaba_only(self):
        os.environ['DASHSCOPE_BASE_URL'] = 'https://ws1.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1'
        os.environ['DASHSCOPE_TTS_URL'] = 'https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation'
        self.assertEqual(providers.qwen_tts_url(), os.environ['DASHSCOPE_TTS_URL'])
        os.environ['DASHSCOPE_TTS_URL'] = 'https://evil.example/tts'
        with patch.object(providers, 'request') as request, self.assertRaises(providers.ProviderError):
            providers.speech('Hello.', 'qwen')
        request.assert_not_called()


if __name__ == '__main__':
    unittest.main()
