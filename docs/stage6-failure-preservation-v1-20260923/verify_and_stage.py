"""This action only: offline source/archive verification, fixed additive staging.
No observer, worker, live driver, UAC, VM or acceptance operation.
"""
import ast
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

ROOT=Path(__file__).parent
PRIOR=ROOT.parent/'stage6-coordination-v3-20260923'
DEST=Path(r'D:\JARVIS-STAGE6-LIVE\cab9745de28a4cae8aa6f6f7a516bf54')
sys.path.insert(0,str(ROOT/'code'))
import failure_preserve_v1 as f

def write(name,v):
    f.write_new(ROOT/name,v)

final=json.loads((PRIOR/'candidate-final-r2.json').read_text())
candidate=Path(final['candidate'])
f.verify_candidate(f.cli_policy())
records=json.loads((PRIOR/'before.json').read_text())['inputs']
errors=[]
for x in records:
    p=Path(x['path'])
    if 'VirtualBox' in str(p):raise ValueError('UNEXPECTED_PROTECTED_PATH')
    s=p.stat()
    if s.st_size!=x['bytes'] or s.st_mtime_ns!=x['mtimeNs'] or f.sha(p)!=x['sha256']:
        errors.append(str(p))
receipt=json.loads((PRIOR/'archive-receipt.json').read_text())
archive=Path(receipt['archive']);manifest=archive.parent/'manifest.json'
if f.sha(archive)!=receipt['archiveSHA256'] or f.sha(manifest)!=receipt['manifestSHA256']:
    errors.append('PRIOR_ARCHIVE_HASH')
members=json.loads(manifest.read_text())
with zipfile.ZipFile(archive) as z:
    if len(z.namelist())!=len(members):errors.append('PRIOR_ARCHIVE_MEMBERS')
    for x in members:
        b=z.read(x['path'])
        if len(b)!=x['bytes'] or hashlib.sha256(b).hexdigest()!=x['sha256']:errors.append(x['path'])
syntax=[]
for p in (ROOT/'code').glob('*.py'):
    ast.parse(p.read_text(),filename=str(p));syntax.append(str(p))
write('post-source-verification.json',dict(candidateFiles=216,preservedInputs=len(records),
      priorArchiveMembers=len(members),errors=errors,syntaxFiles=syntax,
      protectedVMAccess=False,productionChange=False,utc=f.utc()))
if errors:raise RuntimeError(errors)

# Only fixed new paths. Exclusive creation; no overwrite or deletion.
DEST.mkdir(exist_ok=False);(DEST/'code').mkdir();(DEST/'preservation').mkdir()
staged=[]
for src in sorted((ROOT/'code').iterdir()):
    if not src.is_file() or src.suffix not in ('.py','.json'):raise ValueError('UNEXPECTED_CODE_ARTIFACT')
    dst=DEST/'code'/src.name
    with src.open('rb') as a,dst.open('xb') as b:shutil.copyfileobj(a,b)
    if f.sha(src)!=f.sha(dst):raise ValueError('STAGING_HASH')
    staged.append(dict(name=src.name,bytes=dst.stat().st_size,sha256=f.sha(dst)))
f.write_new(DEST/'code'/'source-manifest.json',staged)
write('new-source-manifest.json',dict(stagedRoot=str(DEST/'code'),files=staged,
      manifestSHA256=f.sha(DEST/'code'/'source-manifest.json')))
print(json.dumps(dict(sourceVerification='PASS',syntaxFiles=len(syntax),stagedFiles=len(staged))))
