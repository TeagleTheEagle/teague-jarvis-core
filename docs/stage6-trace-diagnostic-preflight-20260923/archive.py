"""Archive new non-acceptance preflight evidence; never modifies prior records."""
import hashlib,json,zipfile,os
from pathlib import Path
R=Path(__file__).parent
N=R.parent/'stage6-loss-telemetry-v2-20260923'/'candidate'
A=Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 TRACE DIAGNOSTIC PREFLIGHT BLOCKED 20260923')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
sources={p.name:p for p in R.iterdir() if p.is_file()}
for name in ('baseline-allowlist.json','baseline_contract.py','small_binding_v3.py','small_launch_v3.ps1','owned_entry.cpp','small-source-v3.json'):
 sources['source-reference/'+name]=N/name
rows=[dict(path=name,bytes=p.stat().st_size,sha256=sha(p)) for name,p in sorted(sources.items())]
A.mkdir(exist_ok=False)
with (A/'manifest.json').open('x') as f:json.dump(dict(label='NON-ACCEPTANCE / PREFLIGHT BLOCKED / NO LIVE RUN',files=rows),f,indent=2)
with zipfile.ZipFile(A/'evidence.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
 for name,p in sorted(sources.items()):z.write(p,name)
with (A/'evidence.zip').open('r+b') as f:os.fsync(f.fileno())
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==len(set(z.namelist()))==len(rows)
 for row in rows:
  with z.open(row['path']) as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
  assert actual==row['sha256'] and z.getinfo(row['path']).file_size==row['bytes']
for row in rows:assert sha(sources[row['path']])==row['sha256']
receipt=dict(status='HASH_VERIFIED',acceptance=False,liveRun=False,members=len(rows),archive=str(A/'evidence.zip'),archiveSHA256=sha(A/'evidence.zip'),manifestSHA256=sha(A/'manifest.json'))
for target in (A/'receipt.json',R/'archive-receipt.json'):
 with target.open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
