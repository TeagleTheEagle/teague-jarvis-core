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

    def test_preload_skips_missing_model_and_loads_installed_model_once(self):
        import sys
        from unittest.mock import patch
        self.assertFalse(self.engine.preload())          # nothing installed: no load, no error
        (self.engine.directory / 'model.bin').touch()
        loads = []
        fake = SimpleNamespace(WhisperModel=lambda *args, **kwargs: loads.append(kwargs) or SimpleNamespace())
        with patch.dict(sys.modules, {'faster_whisper': fake}):
            self.assertTrue(self.engine.preload())
            self.assertFalse(self.engine.preload())      # already loaded
        self.assertEqual(len(loads), 1)
        self.assertTrue(loads[0]['local_files_only'])    # never downloads during warm-up
        self.assertTrue(self.engine.status()['loaded'])
        self.assertTrue(self.engine.lock.acquire(False))  # lock released after warm-up
        self.engine.lock.release()

    def test_request_during_warm_up_waits_instead_of_failing_busy(self):
        import threading, time
        (self.engine.directory / 'model.bin').touch()
        def transcribe(samples, **kwargs):
            return iter([SimpleNamespace(text=' Ready. ')]), None
        self.engine.lock.acquire()
        self.engine.warming.set()          # simulate preload() in progress
        def finish_warm_up():
            time.sleep(0.3)
            self.engine.model = SimpleNamespace(transcribe=transcribe)
            self.engine.warming.clear()
            self.engine.lock.release()
        threading.Thread(target=finish_warm_up).start()
        result = self.engine.transcribe({'data': base64.b64encode(bytes(3200)).decode()})
        self.assertEqual(result['text'], 'Ready.')
