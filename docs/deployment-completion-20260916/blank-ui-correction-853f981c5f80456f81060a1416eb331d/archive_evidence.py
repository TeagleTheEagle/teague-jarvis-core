"""Archive only this reviewed nonsecret evidence set; never copy TEST runtime state."""
import hashlib
import json
import shutil
from pathlib import Path

source = Path(__file__).resolve().parent
destination = Path('C:/Users/jonny/OneDrive/Desktop/TEAGUE INDUSTRIES DATABASE/06 SOURCE RECORDS/JARVIS BLANK UI CORRECTION 2026-09-16/853f981c5f80456f81060a1416eb331d')
assert not destination.exists(), 'Preserve existing archive; do not overwrite'
allowed = {'.json', '.log', '.txt', '.md', '.py', '.cjs', '.png', '.jpg', '.diff'}
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
files = sorted(p for p in source.rglob('*') if p.is_file())
assert all(p.suffix.lower() in allowed and not p.is_symlink() for p in files)
assert not any(p.name.lower().endswith(('.dpapi', '.key', '.token', '.db', '.sqlite3')) or p.name.lower().startswith('.env') for p in files)
assert not (source/'SHA256.json').exists()
manifest = [{'path': str(p.relative_to(source)), 'bytes': p.stat().st_size, 'sha256': digest(p)} for p in files]
(source/'SHA256.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
files.append(source/'SHA256.json')
verified = []
for p in files:
    target = destination/p.relative_to(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(p, target)
    match = digest(p) == digest(target)
    verified.append({'path': str(p.relative_to(source)), 'sha256': digest(p), 'match': match})
    assert match
receipt = {'source': str(source), 'destination': str(destination), 'files_copied_and_verified': len(verified), 'mismatches': 0, 'files': verified,
           'exclusions': 'No packages, databases, bindings, TEST credentials, production data or provider credentials. Only this diagnostic evidence folder.',
           'scope': 'Narrow archival instead of broad Sync-TeagueIndustries.ps1, to preserve the authorized file scope and avoid unrelated runtime/evidence material.'}
(source/'archive-verification.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
shutil.copyfile(source/'archive-verification.json', destination/'archive-verification.json')
assert digest(source/'archive-verification.json') == digest(destination/'archive-verification.json')
print(json.dumps({'destination': str(destination), 'files_copied_and_verified': len(verified), 'receipt_also_verified': True, 'mismatches': 0}))
