"""Manual offline engine check with Windows synthetic speech; no mic or files recorded."""
import base64
import io
import socket
import subprocess
import wave
from pathlib import Path
from unittest.mock import patch
import numpy as np
from scipy.signal import resample_poly
from local_stt import LocalSTT
import runtime_paths

# The same model the Core loads: bundled inside an installed release, data\ in development.
MODEL = runtime_paths.models_dir() / 'speech-models' / 'base.en'

script = """$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$buffer = New-Object System.IO.MemoryStream
$synth.SetOutputToWaveStream($buffer)
$synth.Speak('The meeting starts at nine tomorrow morning.')
[Convert]::ToBase64String($buffer.ToArray())
$synth.Dispose()
$buffer.Dispose()
"""
if __name__ == '__main__':
    result = subprocess.run(['powershell', '-NoProfile', '-Command', script],
                            capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise SystemExit('Windows synthetic speech unavailable in this execution context.')
    with wave.open(io.BytesIO(base64.b64decode(result.stdout.strip())), 'rb') as wav:
        if wav.getnchannels() != 1 or wav.getsampwidth() != 2:
            raise SystemExit('Unexpected synthetic audio format.')
        samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype='<i2')
        pcm = resample_poly(samples.astype(np.float32), 16000, wav.getframerate()).clip(-32768, 32767).astype('<i2').tobytes()
    engine = LocalSTT(MODEL)
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('Unexpected network connection')):
        for attempt in range(2):
            result = engine.transcribe({'data': base64.b64encode(pcm).decode()})
            print(result, flush=True)
            assert 'meeting' in result['text'].lower() and 'tomorrow' in result['text'].lower()
