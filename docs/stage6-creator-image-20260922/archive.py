import json,hashlib,zipfile,ast
from pathlib import Path
R=Path(__file__).parent;pre=json.loads((R/'preflight.json').read_text());frozen=json.loads((R/'candidate-frozen.json').read_text());C=Path(frozen['code']);run=Path(json.loads((R/'run.json').read_text())['path']);rapid=Path(json.loads((R/'rapid-result.json').read_text())['run'])
A=Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 CREATOR IMAGE QUALIFICATION 20260922')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2)
for x in pre['checks']+frozen['files']:assert sha(Path(x['path']))==x['sha256'],x['path']
state=json.loads((R/'preservation-after.json').read_text());assert json.loads((R/'final'/state['hostRun']/'final-host-state.json').read_text())['status']=='PASS'
assert json.loads((R/'analysis/coverage-live-result.json').read_text())['status']=='PASS'
for p in R.glob('*.py'):ast.parse(p.read_text())
rows=[]
for prefix,base in [('review',R),('qualification-run',run),('focused-real-probes',rapid)]:
 for p in sorted(base.rglob('*')):
  if p.is_file():
   assert not p.is_symlink() and p.name!='.env' and '__pycache__' not in p.parts
   rows.append(dict(name=prefix+'/'+p.relative_to(base).as_posix(),source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
for p in sorted(C.iterdir()):
 if p.is_file():
  assert not p.is_symlink() and p.name!='.env'
  rows.append(dict(name='candidate/'+p.name,source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
assert not A.exists();A.mkdir()
save(A/'manifest.json',dict(status='KERNEL_AUTHORITY_QUALIFIED',baseContract='STAGE6-TEST-KERNEL-INSTANCE-20260921-v1',clarification='Owner-approved creator-owned direct processes / existing OS-helper tracer path, 2026-09-22',matrixSHA256=sha(R/'DESIGN.md'),combinedValidation=False,files=rows))
with zipfile.ZipFile(A/'evidence.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
 for x in rows:z.write(x['source'],x['name'])
 z.write(A/'manifest.json','manifest.json')
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==len(set(z.namelist()))==len(rows)+1
 assert z.read('manifest.json')==(A/'manifest.json').read_bytes()
 for x in rows:
  b=z.read(x['name']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']==sha(Path(x['source']))
rc=dict(status='PASS',archive=str(A/'evidence.zip'),membersVerified=len(rows)+1,archiveBytes=(A/'evidence.zip').stat().st_size,archiveSHA256=sha(A/'evidence.zip'),manifestSHA256=sha(A/'manifest.json'),reportSHA256=sha(R/'REPORT.md'))
save(R/'archive-verification.json',rc);save(A/'archive-verification.json',rc)
assert sha(R/'archive-verification.json')==sha(A/'archive-verification.json')
print(json.dumps(rc))
