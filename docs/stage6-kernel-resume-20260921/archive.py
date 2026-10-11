import json,hashlib,zipfile,ast
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-durable-kernel-20260921';C=Path(json.loads((R/'preflight.json').read_text())['code']);run=Path(json.loads((R/'run.json').read_text())['path']);fixtures=Path(json.loads((R/'contract-tests.json').read_text())['fixtureRoot'])
A=Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 KERNEL RESUME 20260921')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,o):
 with p.open('x',encoding='utf8') as f:json.dump(o,f,indent=2)
assert not A.exists();state=json.loads((R/'preservation-after.json').read_text());assert json.loads((R/'final'/state['hostRun']/'final-host-state.json').read_text())['status']=='PASS'
old=json.loads((P/'archive-verification.json').read_text());oldmanifest=json.loads((Path(old['archive']).parent/'manifest.json').read_text())
for x in oldmanifest['files']:assert sha(Path(x['source']))==x['sha256']
for p in R.glob('*.py'):ast.parse(p.read_text())
rows=[]
for prefix,base in (('review',R),('real-run',run),('fault-fixtures',fixtures)):
 for p in sorted(base.rglob('*')):
  if p.is_file():
   assert not p.is_symlink() and p.name!='.env'
   rows.append(dict(name=prefix+'/'+p.relative_to(base).as_posix(),source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
for p in (P/'qualification.py',C/'qualified_worker.py',C/'qualified_launch.ps1',C/'authority_trace.cpp',C/'durable_sink.hpp',R.parent/'stage6-acceptance-amendment-20260921/CONTRACT.md'):
 rows.append(dict(name='references/'+p.name,source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
A.mkdir();save(A/'manifest.json',dict(status='KERNEL_AUTHORITY_STILL_DEFECTIVE',files=rows))
with zipfile.ZipFile(A/'evidence.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
 for x in rows:z.write(x['source'],x['name'])
 z.write(A/'manifest.json','manifest.json')
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==len(rows)+1 and len(set(z.namelist()))==len(rows)+1
 assert z.read('manifest.json')==(A/'manifest.json').read_bytes()
 for x in rows:
  b=z.read(x['name']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'] and sha(Path(x['source']))==x['sha256']
receipt=dict(status='PASS',archive=str(A/'evidence.zip'),membersVerified=len(rows)+1,archiveBytes=(A/'evidence.zip').stat().st_size,archiveSHA256=sha(A/'evidence.zip'),manifestSHA256=sha(A/'manifest.json'),reportSHA256=sha(R/'REPORT.md'))
save(R/'archive-verification.json',receipt);save(A/'archive-verification.json',receipt)
assert sha(R/'archive-verification.json')==sha(A/'archive-verification.json')
print(json.dumps(receipt))
