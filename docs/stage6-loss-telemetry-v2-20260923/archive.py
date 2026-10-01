"""Archive only this new TEST action; never reads VM, production, credentials or datasets."""
from pathlib import Path
import json,hashlib,zipfile
R=Path(__file__).parent
A=Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 ETW LOSS TELEMETRY V2 OFFLINE 20260923')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert json.loads((R/'final-preservation.json').read_text())['status']=='PASS'
c=json.loads((R/'final-host-census.json').read_text());assert not c['processes'] and not c['traces'] and not c['unknown']
rows=[]
for p in sorted(R.rglob('*')):
 if not p.is_file():continue
 if p.name=='.env' or p.suffix.lower() in ('.key','.pfx','.pem') or p.is_symlink():raise ValueError('UNEXPECTED_SENSITIVE_OR_LINK_PATH')
 rows.append(dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
A.mkdir(exist_ok=False)
with zipfile.ZipFile(A/'evidence.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for x in rows:z.write(R/x['path'],x['path'])
with (A/'manifest.json').open('x') as f:json.dump({'files':rows},f,indent=2)
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==len(rows)
 for x in rows:
  assert hashlib.sha256(z.read(x['path'])).hexdigest()==x['sha256']
  assert z.getinfo(x['path']).file_size==x['bytes'] and sha(R/x['path'])==x['sha256']
receipt={'status':'HASH_VERIFIED','archive':str(A/'evidence.zip'),'members':len(rows),'archiveSHA256':sha(A/'evidence.zip'),'manifestSHA256':sha(A/'manifest.json'),'sourceManifestSHA256':sha(R/'candidate/small-source-v3.json'),'diagnosticOnly':True,'liveRun':False,'productionChange':False,'protectedAccess':False}
for p in (A/'receipt.json',R/'archive-receipt.json'):
 with p.open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
