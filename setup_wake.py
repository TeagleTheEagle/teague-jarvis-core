"""Run once after installing requirements.txt to fetch official wake models."""
import hashlib
import json
from pathlib import Path
import urllib.request

root = Path(__file__).resolve().parent / 'data' / 'wake-models'
root.mkdir(parents=True, exist_ok=True)
manifest = []
for name in ('melspectrogram.onnx', 'embedding_model.onnx', 'hey_jarvis_v0.1.onnx'):
    url = 'https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/' + name
    path = root / name
    if not path.exists():
        partial = path.with_suffix('.download')
        with urllib.request.urlopen(url, timeout=60) as response:
            partial.write_bytes(response.read())
        partial.replace(path)
    manifest.append({'file': name, 'source': url, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
(root / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print('Local Hey Jarvis models are ready.')
