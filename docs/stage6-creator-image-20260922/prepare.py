import json,hashlib,zipfile,uuid
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-required-coverage-20260921'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[];receipts=[]
for folder in ('stage6-required-coverage-20260921','stage6-early-image-20260922'):
 rc=json.loads((R.parent/folder/'archive-verification.json').read_text());a=Path(rc['archive']);m=a.parent/'manifest.json'
 assert sha(a)==rc['archiveSHA256'] and sha(m)==rc['manifestSHA256'];rows=json.loads(m.read_text())['files']
 with zipfile.ZipFile(a) as z:
  assert len(z.namelist())==rc['membersVerified'] and z.read('manifest.json')==m.read_bytes()
  for x in rows:
   b=z.read(x['name']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']==sha(Path(x['source']));checks.append(dict(path=x['source'],sha256=x['sha256']))
 receipts.append(rc)
for x in json.loads((P/'preflight.json').read_text())['checks']:assert sha(Path(x['path']))==x['sha256'];checks.append(x)
f=json.loads((P/'candidate-frozen.json').read_text())
for x in f['files']:assert sha(Path(x['path']))==x['sha256'];checks.append(x)
run=uuid.uuid4().hex;(R/'final'/run).mkdir(parents=True)
with (R/'host_preflight.ps1').open('xb') as o:o.write((P/'host_preflight.ps1').read_bytes())
with (R/'preflight.json').open('x') as o:json.dump(dict(status='PASS',hostRun=run,checks=checks,archives=receipts,code=f['code']),o,indent=2)
print(json.dumps(dict(status='PASS',hostRun=run,comparisons=len(checks))))
