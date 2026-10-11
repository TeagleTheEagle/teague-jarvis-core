import json,hashlib,zipfile,uuid
from pathlib import Path
R=Path(__file__).parent
A=R.parent/'stage6-acceptance-amendment-20260921'
P=R.parent/'stage6-durability-contract-review-20260921'
C=Path(r'D:\JARVIS-STAGE6-LIVE\0febafa860ad4fc1aee8d72669c3484a\code')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,o):
 with p.open('x',encoding='utf8') as f:json.dump(o,f,indent=2)
checked=[]
for x in json.loads((A/'verification-after.json').read_text())['checked']:
 assert sha(Path(x['path']))==x['sha256'],x['path'];checked.append(x)
archives=[]
for base in (A,P):
 receipt=json.loads((base/'archive-verification.json').read_text());zpath=Path(receipt['archive']);mf=zpath.parent/'manifest.json'
 assert sha(zpath)==receipt['archiveSHA256'] and sha(mf)==receipt['manifestSHA256']
 manifest=json.loads(mf.read_text())['files']
 with zipfile.ZipFile(zpath) as z:
  assert len(z.namelist())==receipt['membersVerified'] and z.read('manifest.json')==mf.read_bytes()
  for x in manifest:
   b=z.read(x['path']);assert len(b)==x['size'] and hashlib.sha256(b).hexdigest()==x['sha256']
   assert sha(base/x['path'])==x['sha256']
 archives.append(receipt)
historical=R.parent/'stage6-event-integration-20260921/REPORT.md'
assert 'Historical21 AMBIGUOUS/1 UNMATCHED unchanged' in historical.read_text()
run=uuid.uuid4().hex;(R/'final'/run).mkdir(parents=True,exist_ok=False)
with (R/'host_preflight.ps1').open('xb') as f:f.write((R.parent/'stage6-evidence-restoration-20260921/host_preflight.ps1').read_bytes())
save(R/'preservation.json',dict(checks=checked,archives=archives,historical=dict(path=str(historical),sha256=sha(historical),ambiguous=21,unmatched=1),source=str(C),hostRun=run,protectedAccess=False))
print(json.dumps(dict(hostRun=run,checks=len(checked),archives=[x['membersVerified'] for x in archives])))
