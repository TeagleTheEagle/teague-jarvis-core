import json,hashlib,zipfile,uuid
from pathlib import Path
R=Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipts=[];checked=[]
for name in ('stage6-kernel-resume-20260921','stage6-durable-kernel-20260921'):
 P=R.parent/name;rc=json.loads((P/'archive-verification.json').read_text());a=Path(rc['archive']);m=a.parent/'manifest.json'
 assert sha(a)==rc['archiveSHA256'] and sha(m)==rc['manifestSHA256']
 rows=json.loads(m.read_text())['files']
 with zipfile.ZipFile(a) as z:
  assert len(z.namelist())==rc['membersVerified'] and z.read('manifest.json')==m.read_bytes()
  for x in rows:
   b=z.read(x['name']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'];assert sha(Path(x['source']))==x['sha256'],x['source'];checked.append(dict(path=x['source'],sha256=x['sha256']))
 receipts.append(rc)
for x in json.loads((R.parent/'stage6-durable-kernel-20260921/preservation.json').read_text())['checks']:
 assert sha(Path(x['path']))==x['sha256'];checked.append(x)
run=uuid.uuid4().hex;(R/'final'/run).mkdir(parents=True,exist_ok=False)
with (R/'host_preflight.ps1').open('xb') as f:f.write((R.parent/'stage6-kernel-resume-20260921/host_preflight.ps1').read_bytes())
with (R/'preflight.json').open('x') as f:json.dump(dict(status='PASS',checks=checked,archives=receipts,hostRun=run,source=json.loads((R.parent/'stage6-kernel-resume-20260921/preflight.json').read_text())['code']),f,indent=2)
print(json.dumps(dict(hostRun=run,checks=len(checked),archives=[r['membersVerified'] for r in receipts])))
