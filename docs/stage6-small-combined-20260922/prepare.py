import json,hashlib,zipfile,uuid
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-creator-image-20260922';D=R.parent/'stage6-durable-kernel-20260921'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[];archives=[]
for folder in (P,D):
 rc=json.loads((folder/'archive-verification.json').read_text());a=Path(rc['archive']);m=a.parent/'manifest.json'
 assert sha(a)==rc['archiveSHA256'] and sha(m)==rc['manifestSHA256']
 with zipfile.ZipFile(a) as z:
  assert len(z.namelist())==rc['membersVerified'] and z.read('manifest.json')==m.read_bytes()
  for x in json.loads(m.read_text())['files']:
   b=z.read(x['name']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']==sha(Path(x['source']));checks.append(dict(path=x['source'],sha256=x['sha256']))
 archives.append(rc)
frozen=json.loads((P/'candidate-frozen.json').read_text())
for x in frozen['files']:assert sha(Path(x['path']))==x['sha256'];checks.append(x)
assert json.loads((P/'coverage-tests.json').read_text())['passed']==44
assert len(json.loads((P/'rapid-result.json').read_text())['checks'])==24
cov=json.loads((P/'analysis/coverage-live-result.json').read_text());assert cov['status']=='PASS' and cov['verifiedIdentities']==36
normal=json.loads((D/'durability-results-f3623c02464c4bdf9862d646eff3b9a0.json').read_text());faults=json.loads((D/'durability-results-67580fee3ea34fc888da9a98889f7e3a.json').read_text())
n=normal['cases'][0];assert n['status']=='PASS' and n['statistics']['result']['accepted']==12000 and len(n['statistics']['result']['segments'])==45
assert len(faults['cases'])==14 and all(x['status']=='PASS' and x['statistics']['result']['fault'] for x in faults['cases'])
for x in faults['cases']:assert not (Path(x['run'])/'durable-seal.json').exists()
host=uuid.uuid4().hex;(R/'final'/host).mkdir(parents=True)
for name in ('host_preflight.ps1','coverage.py','analyze.py'):
 with (R/name).open('xb') as f:f.write((P/name).read_bytes())
with (R/'candidate-frozen.json').open('xb') as f:f.write((P/'candidate-frozen.json').read_bytes())
with (R/'preflight.json').open('x') as f:json.dump(dict(status='PASS',code=frozen['code'],hostRun=host,checks=checks,archives=archives,normalDurability=n,faultEvidence=[dict(fault=x['fault'],status=x['status'],run=x['run']) for x in faults['cases']]),f,indent=2)
print(json.dumps(dict(status='PASS',hostRun=host,comparisons=len(checks),archives=[x['membersVerified'] for x in archives])))
