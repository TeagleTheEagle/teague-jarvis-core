import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parent
dest = Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 DURABILITY CONTRACT REVIEW 20260921')
if dest.exists():
    raise RuntimeError('Refusing to reuse archive destination')
paths = sorted((p for p in root.rglob('*') if p.is_file()), key=lambda p: p.relative_to(root).as_posix())
if any(p.name in {'manifest.json', 'archive-verification.json', 'evidence.zip'} for p in paths):
    raise RuntimeError('Refusing to reuse finalized review')
rows = []
for p in paths:
    if p.is_symlink():
        raise RuntimeError('Unexpected symbolic link')
    data = p.read_bytes()
    rows.append({'path': p.relative_to(root).as_posix(), 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
manifest = (json.dumps({'status': 'ACCEPTANCE_CONTRACT_REVIEW_REQUIRED', 'files': rows}, sort_keys=True, indent=2) + '\n').encode()
with (root / 'manifest.json').open('xb') as f:
    f.write(manifest)
dest.mkdir()
with zipfile.ZipFile(dest / 'evidence.zip', 'x', compression=zipfile.ZIP_DEFLATED) as z:
    for row, p in zip(rows, paths):
        data = p.read_bytes()
        if hashlib.sha256(data).hexdigest() != row['sha256']:
            raise RuntimeError('Source changed during archive')
        z.writestr(row['path'], data)
    z.writestr('manifest.json', manifest)
with (dest / 'manifest.json').open('xb') as f:
    f.write(manifest)
with zipfile.ZipFile(dest / 'evidence.zip') as z:
    if len(z.namelist()) != len(rows) + 1 or len(set(z.namelist())) != len(z.namelist()):
        raise RuntimeError('Archive member mismatch')
    if z.read('manifest.json') != manifest:
        raise RuntimeError('Manifest mismatch')
    for row in rows:
        data = z.read(row['path'])
        if len(data) != row['size'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise RuntimeError('Archive payload mismatch')
if (dest / 'manifest.json').read_bytes() != manifest:
    raise RuntimeError('Canonical manifest mismatch')
receipt = {'status': 'PASS', 'verifiedUtc': datetime.now(timezone.utc).isoformat(), 'archive': str(dest / 'evidence.zip'), 'membersVerified': len(rows) + 1, 'archiveBytes': (dest / 'evidence.zip').stat().st_size, 'archiveSHA256': hashlib.sha256((dest / 'evidence.zip').read_bytes()).hexdigest(), 'manifestSHA256': hashlib.sha256(manifest).hexdigest(), 'reportSHA256': hashlib.sha256((root / 'REPORT.md').read_bytes()).hexdigest()}
receipt_bytes = (json.dumps(receipt, sort_keys=True, indent=2) + '\n').encode()
for folder in (root, dest):
    with (folder / 'archive-verification.json').open('xb') as f:
        f.write(receipt_bytes)
if (dest / 'archive-verification.json').read_bytes() != receipt_bytes:
    raise RuntimeError('Canonical receipt mismatch')
print(json.dumps(receipt))
