"""Local-only wake detection. Audio is processed in memory, never persisted."""
import base64
import threading
import time
from pathlib import Path


class WakeDetector:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.lock = threading.Lock()
        self.model = None
        self.client = None
        self.last = 0
        self.triggered = 0

    def load(self):
        if self.model is None:
            from openwakeword.model import Model
            self.model = Model(wakeword_models=[str(self.directory / 'hey_jarvis_v0.1.onnx')],
                               inference_framework='onnx',
                               melspec_model_path=str(self.directory / 'melspectrogram.onnx'),
                               embedding_model_path=str(self.directory / 'embedding_model.onnx'))

    def prepare(self):
        # Initialise and warm inference before the microphone starts producing frames.
        with self.lock:
            if self.model is None:
                import numpy as np
                self.load()
                self.model.predict(np.zeros(5120, dtype=np.int16))
                self.model.reset()
        return {'ready': True}

    def predict(self, body):
        import numpy as np
        client = body.get('client')
        if not isinstance(client, str) or not 1 <= len(client) <= 80:
            raise ValueError('Invalid microphone session.')
        audio = base64.b64decode(body.get('data', ''), validate=True)
        if len(audio) != 10240:
            raise ValueError('Expected 320 ms of 16 kHz mono PCM16.')
        with self.lock:
            self.load()
            now = time.monotonic()
            if self.client != client and now - self.last < 2:
                raise ValueError('Microphone is active in another JARVIS tab. Mute that tab first.')
            if self.client != client or now - self.last > 2:
                self.model.reset()
            self.client, self.last = client, now
            samples = np.frombuffer(audio, dtype='<i2')
            score = max(float(v) for offset in range(0, len(samples), 1280)
                        for v in self.model.predict(samples[offset:offset+1280]).values())
            # Microphone distance and room acoustics vary considerably on Windows;
            # this threshold keeps the phrase responsive while the phrase model
            # still gates activation locally.
            sensitivity = body.get('sensitivity', 'normal')
            threshold = {'low': .55, 'normal': .38, 'high': .28}.get(sensitivity, .38)
            detected = score >= threshold and now - self.triggered > 2
            if detected:
                self.triggered = now
                self.model.reset()
            return {'detected': detected, 'score': round(score, 4)}
