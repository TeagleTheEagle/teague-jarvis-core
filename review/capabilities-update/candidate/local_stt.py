"""Prototype speech recognition: local model, in-memory PCM, no cloud fallback."""
import base64
import threading
import time
from pathlib import Path


class LocalSTT:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.model = None
        self.lock = threading.Lock()

    def status(self):
        return {'installed': (self.directory / 'model.bin').is_file(),
                'loaded': self.model is not None, 'engine': 'Whisper base.en · CPU int8',
                'cloud_fallback': False}

    def transcribe(self, body):
        import numpy as np
        raw = base64.b64decode(body.get('data', ''), validate=True)
        if not 3200 <= len(raw) <= 16000 * 2 * 30 or len(raw) % 2:
            raise ValueError('Expected 0.1–30 seconds of 16 kHz mono PCM16.')
        if not self.lock.acquire(blocking=False):
            raise ValueError('Local transcription is busy. Try again shortly.')
        try:
            if not self.status()['installed']:
                raise ValueError('Local speech model is not installed. Run setup_local_voice.py first.')
            started = time.monotonic()
            if self.model is None:
                from faster_whisper import WhisperModel
                self.model = WhisperModel(str(self.directory), device='cpu', compute_type='int8',
                                          cpu_threads=4, local_files_only=True)
            samples = np.frombuffer(raw, dtype='<i2').astype(np.float32) / 32768
            segments, info = self.model.transcribe(samples, language='en', beam_size=1,
                initial_prompt='JARVIS is the assistant name. Hey Jarvis. Thank you Jarvis. Mr. Teague.',
                vad_filter=True, vad_parameters={'min_silence_duration_ms': 600},
                condition_on_previous_text=False)
            text = ' '.join(segment.text.strip() for segment in segments).strip()
            return {'text': text, 'latency_ms': round((time.monotonic()-started)*1000),
                    'audio_seconds': round(len(samples)/16000, 2), 'local': True}
        finally:
            self.lock.release()
