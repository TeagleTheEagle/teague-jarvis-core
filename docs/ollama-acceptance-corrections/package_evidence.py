"""Package only approved nonsecret correction source and evidence."""
from pathlib import Path
import difflib
import hashlib
import json
import shutil
import subprocess

base = Path(__file__).resolve().parent
root = base.parent.parent
files = ['stage4_ollama_transport.py', 'stage4_client.cjs',
         'tests/test_stage4_ollama_transport.py', 'tests/build_real_ollama_probe.py',
         'tests/real_ollama_validation.py']
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
protected = json.loads((base / 'protected-before.json').read_text(encoding='utf-8-sig'))
checks = [{'path': x['Path'], 'unchanged': digest(Path(x['Path'])).upper() == x['Hash']}
          for x in protected]
assert all(x['unchanged'] for x in checks)
diff = []
for name in files:
    src = root / name
    dst = base / 'source' / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    if src.suffix == '.py':
        compile(src.read_text(encoding='utf-8-sig'), name, 'exec')
    diff.extend(difflib.unified_diff((base / 'before' / name).read_text(encoding='utf-8-sig').splitlines(True),
                                   src.read_text(encoding='utf-8-sig').splitlines(True),
                                   fromfile='before/' + name, tofile='after/' + name))
(base / 'source-changes.diff').write_text(''.join(diff), encoding='utf-8')
node = Path(r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe')
subprocess.run([str(node), '--check', str(root / 'stage4_client.cjs')], check=True)
screenshot = root / 'tests/lifecycle_stage1/evidence/TEST-STAGE4-3d806fc8153248aa9a5f27f5e7ebd23d/teague-acdbce98-4abb-490a-b16b-198c85d351d1.png'
shutil.copyfile(screenshot, base / 'electron-final-answer.png')
(base / 'validation.json').write_text(json.dumps({
    'protected_files': checks, 'python_compilation': 'PASS', 'javascript_syntax': 'PASS',
    'visual_inspection': 'Performed: screenshot shows 4 in existing response container, no thinking or artificial overlay',
    'source_files': files, 'screenshot_original': str(screenshot),
    'paid_openai_calls': 0, 'production_activation': False, 'stage5_started': False
}, indent=2), encoding='utf-8')
manifest = {str(p.relative_to(base)).replace('\\', '/'): digest(p)
            for p in sorted(base.rglob('*')) if p.is_file() and p.name != 'SHA256.json'}
(base / 'SHA256.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps({'files_hashed': len(manifest), 'protected_files_unchanged': len(checks),
                  'manifest_sha256': digest(base / 'SHA256.json')}))
