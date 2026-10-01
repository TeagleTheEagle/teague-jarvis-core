import json,hashlib,zipfile,ast
from pathlib import Path
R=Path(__file__).parent;C=Path(json.loads((R/'candidate.json').read_text())['code'])
A=Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 DURABLE KERNEL QUALIFICATION 20260921')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(p,o):
 with p.open('x',encoding='utf8') as f:json.dump(o,f,indent=2)
assert not A.exists()
state=json.loads((R/'final-source.json').read_text())
host=json.loads((R/'final'/state['hostRun']/'final-host-state.json').read_text());assert host['status']=='PASS'
for x in state['currentFiles']:assert sha(Path(x['path']))==x['sha256']
for x in json.loads((R/'preservation.json').read_text())['checks']:assert sha(Path(x['path']))==x['sha256']
for p in R.glob('*.py'):ast.parse(p.read_text())
rows=[]
for prefix,base in (('review',R),('candidate',C)):
 for p in sorted(base.rglob('*')):
  if p.is_file():
   assert not p.is_symlink() and p.name!='.env' and p.suffix.lower() not in ('.pem','.key')
   rows.append(dict(name=prefix+'/'+p.relative_to(base).as_posix(),source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
A.mkdir();save(A/'manifest.json',dict(status='BLOCKED',reason='TRACER_UAC_CANCELED',files=rows))
with zipfile.ZipFile(A/'evidence.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
 for x in rows:z.write(x['source'],x['name'])
 z.write(A/'manifest.json','manifest.json')
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==len(rows)+1 and len(set(z.namelist()))==len(rows)+1
 assert z.read('manifest.json')==(A/'manifest.json').read_bytes()
 for x in rows:
  h=hashlib.sha256();n=0
  with z.open(x['name']) as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
  assert n==x['bytes'] and h.hexdigest()==x['sha256'] and sha(Path(x['source']))==x['sha256']
receipt=dict(status='PASS',archive=str(A/'evidence.zip'),membersVerified=len(rows)+1,archiveBytes=(A/'evidence.zip').stat().st_size,archiveSHA256=sha(A/'evidence.zip'),manifestSHA256=sha(A/'manifest.json'),reportSHA256=sha(R/'REPORT.md'))
save(R/'archive-verification.json',receipt);save(A/'archive-verification.json',receipt)
assert sha(R/'archive-verification.json')==sha(A/'archive-verification.json')
print(json.dumps(receipt))
