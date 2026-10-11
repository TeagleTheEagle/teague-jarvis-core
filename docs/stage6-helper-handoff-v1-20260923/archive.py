"""Seal only this action and its synthetic candidate; no live or protected access."""
import pathlib, os, stat, json, hashlib, zipfile, datetime

R = pathlib.Path(__file__).parent
C = pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\d45028a56e344926a311c04ba01f6a80\code')
A = pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 HELPER HANDOFF 20260923')

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def stable(p):
    s = p.stat()
    h = sha(p)
    t = p.stat()
    assert (s.st_size, s.st_mtime_ns) == (t.st_size, t.st_mtime_ns), str(p)
    return s.st_size, s.st_mtime_ns, h

def check_sources():
    before = json.loads((R / 'before.json').read_text())
    for row in before['inputs']:
        assert stable(pathlib.Path(row['path'])) == (row['bytes'], row['mtimeNs'], row['sha256']), row['path']
    rows = json.loads((C / 'small-source-v3.json').read_text())
    assert len(rows) == 235
    for row in rows:
        size, _, digest = stable(C / row['name'])
        assert (size, digest) == (row['bytes'], row['sha256']), row['name']
    assert sha(C / 'small-source-v3.json') == '6a86a4f287388c8c58b3df4333792217b5205305f2157043a5a2ba5456c0b15b'
    return len(before['inputs']), len(rows)

check_sources()
assert not A.exists(), 'Archive destination already exists; no overwrite permitted'
items, exclusions = [], []
for base, prefix in ((R, 'action'), (C, 'candidate')):
    assert not (base.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    for root, dirs, files in os.walk(base, topdown=True, followlinks=False):
        root = pathlib.Path(root)
        for n in list(dirs):
            p = root / n
            if n in ('__pycache__', '.pytest_cache') or p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                dirs.remove(n)
                exclusions.append({'path': str(p), 'reason': 'cache or reparse fixture; never followed'})
        for n in sorted(files):
            p = root / n
            s = p.lstat()
            if s.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT or n.lower().startswith('.env') or p.suffix.lower() in ('.pyc', '.zip'):
                exclusions.append({'path': str(p), 'reason': 'reparse, environment, cache or nested synthetic archive; original retained'})
                continue
            assert p.resolve().is_relative_to(base.resolve()), str(p)
            size, mtime, digest = stable(p)
            items.append({'member': prefix + '/' + p.relative_to(base).as_posix(), 'source': str(p), 'bytes': size, 'mtimeNs': mtime, 'sha256': digest})
items.sort(key=lambda x: x['member'])
assert len({x['member'].casefold() for x in items}) == len(items)
inventory = {'schema': 'stage6-handoff-offline-archive-v1', 'createdUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'purpose': 'Offline implementation evidence only; not live acceptance', 'files': items, 'exclusions': exclusions}
encoded = (json.dumps(inventory, indent=2, sort_keys=True) + '\n').encode()
A.mkdir(parents=True, exist_ok=False)
manifest = A / 'archive-manifest.json'
with manifest.open('xb') as f:
    f.write(encoded)
archive = A / 'helper-handoff-offline-evidence.zip'
with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    z.writestr('archive-manifest.json', encoded)
    for row in items:
        z.write(row['source'], row['member'])
print(json.dumps({'phase': 'archive_written', 'members': len(items) + 1}), flush=True)
with zipfile.ZipFile(archive) as z:
    assert len(z.namelist()) == len(items) + 1 == len(set(z.namelist()))
    assert z.read('archive-manifest.json') == encoded
    for row in items:
        with z.open(row['member']) as f:
            digest = hashlib.file_digest(f, 'sha256').hexdigest()
        assert digest == row['sha256'] and z.getinfo(row['member']).file_size == row['bytes'], row['member']
        assert stable(pathlib.Path(row['source'])) == (row['bytes'], row['mtimeNs'], row['sha256']), row['source']
preserved, candidate = check_sources()
receipt = {'status': 'PASS', 'archive': str(archive), 'archiveBytes': archive.stat().st_size, 'archiveSHA256': sha(archive), 'manifest': str(manifest), 'manifestSHA256': sha(manifest), 'verifiedMembers': len(items) + 1, 'payloadFiles': len(items), 'excludedEntries': len(exclusions), 'preservedInputsReverified': preserved, 'candidateFilesReverified': candidate, 'liveRun': False, 'UAC': False, 'protectedAccess': False, 'productionChange': False, 'receiptOutsideArchive': 'Receipt is a separate verified sidecar to avoid circular hashing'}
data = (json.dumps(receipt, indent=2) + '\n').encode()
for p in (A / 'archive-receipt.json', R / 'archive-receipt.json'):
    with p.open('xb') as f:
        f.write(data)
assert sha(A / 'archive-receipt.json') == sha(R / 'archive-receipt.json')
print(json.dumps(receipt), flush=True)
