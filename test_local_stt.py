import base64
import tempfile
import unittest
from types import SimpleNamespace
from local_stt import LocalSTT


class LocalSpeechTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.engine = LocalSTT(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_rejects_oversize_odd_empty_audio(self):
        for raw in (b'', b'x'*3201, b'x'*960002):
            with self.assertRaises(ValueError):
                self.engine.transcribe({'data': base64.b64encode(raw).decode()})

    def test_missing_model_never_falls_back(self):
        with self.assertRaisesRegex(ValueError, 'not installed'):
            self.engine.transcribe({'data': base64.b64encode(bytes(3200)).decode()})
        self.assertFalse(self.engine.status()['cloud_fallback'])

    def test_busy_rejected_and_lock_released_after_failure(self):
        self.engine.lock.acquire()
        with self.assertRaisesRegex(ValueError, 'busy'):
            self.engine.transcribe({'data': base64.b64encode(bytes(3200)).decode()})
        self.engine.lock.release()
        self.test_missing_model_never_falls_back()
        self.assertTrue(self.engine.lock.acquire(False))
        self.engine.lock.release()

    def test_local_vad_enabled_and_segments_consumed(self):
        (self.engine.directory / 'model.bin').touch()
        def transcribe(samples, **kwargs):
            self.assertTrue(kwargs['vad_filter'])
            self.assertFalse(kwargs['condition_on_previous_text'])
            self.assertEqual(len(samples), 1600)
            return iter([SimpleNamespace(text=' Hello sir. ')]), None
        self.engine.model = SimpleNamespace(transcribe=transcribe)
        result = self.engine.transcribe({'data': base64.b64encode(bytes(3200)).decode()})
        self.assertEqual(result['text'], 'Hello sir.')
        self.assertTrue(result['local'])
