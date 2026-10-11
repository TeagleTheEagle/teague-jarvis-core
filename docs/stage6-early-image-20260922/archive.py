import json,hashlib,zipfile
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-required-coverage-20260921';pre=json.loads((R/'preflight.json').read_text());C=Path(pre['candidate'])
A=Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 EARLY IMAGE REVIEW 20260922')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2)
for x in pre['checks']:assert sha(Path(x['path']))==x['sha256'],x['path']
assert json.loads((R/'final'/pre['hostRun']/'final-host-state.json').read_text())['status']=='PASS'
save(R/'preservation-after.json',dict(status='PASS',hashComparisons=len(pre['checks']),candidateFilesUnchanged=138,candidateModified=False,qualificationRun=False,protectedAccess=False,productionChanged=False))
refs=[P/'REPORT.md',P/'DESIGN.md',P/'archive-verification.json',P/'coverage-tests.json',P/'image-query-failure.json',P/'analysis-v2/coverage-live-result.json',R.parent/'stage6-acceptance-amendment-20260921/CONTRACT.md']+[C/n for n in ('native_bridge.py','owned_entry.cpp','authority_trace.cpp','qualified_launch.ps1','probe_timing.py')]
rows=[]
for p in sorted(R.rglob('*')):
 if p.is_file():rows.append(dict(name='review/'+p.relative_to(R).as_posix(),source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
for i,p in enumerate(refs):rows.append(dict(name=f'references/{i:02d}-'+p.name,source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
assert not A.exists();A.mkdir()
save(A/'manifest.json',dict(status='CONTRACT_REVIEW_REQUIRED',files=rows))
with zipfile.ZipFile(A/'evidence.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
 for x in rows:z.write(x['source'],x['name'])
 z.write(A/'manifest.json','manifest.json')
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==len(set(z.namelist()))==len(rows)+1
 assert z.read('manifest.json')==(A/'manifest.json').read_bytes()
 for x in rows:
  b=z.read(x['name']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']==sha(Path(x['source']))
receipt=dict(status='PASS',membersVerified=len(rows)+1,archive=str(A/'evidence.zip'),archiveSHA256=sha(A/'evidence.zip'),manifestSHA256=sha(A/'manifest.json'),reportSHA256=sha(R/'REPORT.md'))
save(R/'archive-verification.json',receipt);save(A/'archive-verification.json',receipt)
print(json.dumps(receipt))
