"""Integrity/archival only. No imports from or execution of validation candidates."""
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PREVIOUS = ROOT.parent / 'stage6-durability-contract-review-20260921'
DEST = Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 ACCEPTANCE AMENDMENT 20260921')
ALLOWED = (
    ROOT.parent,
    Path(r'D:\JARVIS-STAGE6-LIVE'),
    Path(r'C:\Users\jonny\.codex\attachments'),
    DEST.parent,
)

def check_path(path):
    path = Path(path).resolve(strict=True)
    if not any(path.is_relative_to(p.resolve(strict=True)) for p in ALLOWED):
        raise RuntimeError('Evidence path outside allowed evidence roots')
    return path

def digest(path):
    h = hashlib.sha256()
    with check_path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()

def read(path):
    return json.loads(check_path(path).read_text(encoding='utf-8-sig'))

def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')

def verify(label):
    if label not in ('before', 'after'):
        raise ValueError('Invalid verification phase')
    freeze = read(ROOT.parent / 'stage6-writer-identity-diagnosis-20260921/freeze.json')
    previous = read(PREVIOUS / 'preservation.json')
    rows = freeze['checks'] + previous['archiveSourceFilesVerified'] + previous['references']
    checked = []
    for row in rows:
        value = digest(row['path'])
        if value != row['sha256']:
            raise RuntimeError('Preserved source/evidence hash mismatch: ' + row['path'])
        checked.append({'path': row['path'], 'sha256': value})
    receipt = read(PREVIOUS / 'archive-verification.json')
    archive = check_path(receipt['archive'])
    if digest(archive) != receipt['archiveSHA256']:
        raise RuntimeError('Prior archive hash mismatch')
    manifest_path = archive.parent / 'manifest.json'
    if digest(manifest_path) != receipt['manifestSHA256']:
        raise RuntimeError('Prior manifest hash mismatch')
    manifest = read(manifest_path)
    with zipfile.ZipFile(archive) as z:
        expected = {r['path'] for r in manifest['files']} | {'manifest.json'}
        if len(z.namelist()) != len(expected) or set(z.namelist()) != expected:
            raise RuntimeError('Prior archive member mismatch')
        if z.read('manifest.json') != manifest_path.read_bytes():
            raise RuntimeError('Prior embedded manifest mismatch')
        for row in manifest['files']:
            data = z.read(row['path'])
            if len(data) != row['size'] or hashlib.sha256(data).hexdigest() != row['sha256']:
                raise RuntimeError('Prior archive payload mismatch')
            if digest(PREVIOUS / row['path']) != row['sha256']:
                raise RuntimeError('Prior review file changed')
    result = dict(status='PASS', phase=label, utc=datetime.now(timezone.utc).isoformat(), frozenChecks=len(freeze['checks']), preservedSourceChecks=len(previous['archiveSourceFilesVerified']), referenceChecks=len(previous['references']), priorReviewArchiveMembers=len(expected), checked=checked, runtimeTestsRun=0, protectedVMAccessed=False, productionChanged=False)
    save(ROOT / ('verification-' + label + '.json'), result)
    print(json.dumps({k: v for k, v in result.items() if k != 'checked'}))

def archive():
    before, after = read(ROOT / 'verification-before.json'), read(ROOT / 'verification-after.json')
    if before['status'] != 'PASS' or after['status'] != 'PASS' or before['checked'] != after['checked']:
        raise RuntimeError('Preservation mismatch')
    if DEST.exists():
        raise RuntimeError('Refusing to overwrite archive')
    files = sorted((p for p in ROOT.rglob('*') if p.is_file()), key=lambda p: p.relative_to(ROOT).as_posix())
    if any(p.name in ('manifest.json', 'archive-verification.json') for p in files):
        raise RuntimeError('Already finalized')
    rows = [{'path': p.relative_to(ROOT).as_posix(), 'size': p.stat().st_size, 'sha256': digest(p)} for p in files]
    save(ROOT / 'manifest.json', {'contract': 'STAGE6-TEST-KERNEL-INSTANCE-20260921-v1', 'status': 'CONTRACT_AMENDMENT_APPLIED', 'runtimeValidated': False, 'files': rows})
    manifest = (ROOT / 'manifest.json').read_bytes()
    DEST.mkdir()
    with zipfile.ZipFile(DEST / 'evidence.zip', 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for row, path in zip(rows, files):
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != row['sha256']:
                raise RuntimeError('Review changed during archive')
            z.writestr(row['path'], data)
        z.writestr('manifest.json', manifest)
    with (DEST / 'manifest.json').open('xb') as stream:
        stream.write(manifest)
    with zipfile.ZipFile(DEST / 'evidence.zip') as z:
        if len(z.namelist()) != len(rows) + 1 or len(set(z.namelist())) != len(z.namelist()):
            raise RuntimeError('New archive member mismatch')
        if z.read('manifest.json') != manifest or (DEST / 'manifest.json').read_bytes() != manifest:
            raise RuntimeError('New manifest mismatch')
        for row in rows:
            data = z.read(row['path'])
            if len(data) != row['size'] or hashlib.sha256(data).hexdigest() != row['sha256']:
                raise RuntimeError('New archive verification failed')
    receipt = dict(status='PASS', archive=str(DEST / 'evidence.zip'), membersVerified=len(rows) + 1, archiveSHA256=digest(DEST / 'evidence.zip'), manifestSHA256=digest(DEST / 'manifest.json'), archiveBytes=(DEST / 'evidence.zip').stat().st_size)
    save(ROOT / 'archive-verification.json', receipt)
    save(DEST / 'archive-verification.json', receipt)
    if digest(ROOT / 'archive-verification.json') != digest(DEST / 'archive-verification.json'):
        raise RuntimeError('Receipt copy mismatch')
    print(json.dumps(receipt))

if __name__ == '__main__':
    if sys.argv[1:] == ['archive']:
        archive()
    elif len(sys.argv) == 2:
        verify(sys.argv[1])
    else:
        raise ValueError('Use before, after or archive')
