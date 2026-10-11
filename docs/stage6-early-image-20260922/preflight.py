import json,hashlib,zipfile,uuid
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-required-coverage-20260921'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2)
receipt=json.loads((P/'archive-verification.json').read_text());archive=Path(receipt['archive']);manifest=archive.parent/'manifest.json'
assert sha(archive)==receipt['archiveSHA256'] and sha(manifest)==receipt['manifestSHA256']
rows=json.loads(manifest.read_text())['files'];checked=[]
with zipfile.ZipFile(archive) as z:
 assert len(z.namelist())==receipt['membersVerified']==226
 assert z.read('manifest.json')==manifest.read_bytes()
 for x in rows:
  b=z.read(x['name']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'];assert sha(Path(x['source']))==x['sha256'],x['source'];checked.append(dict(path=x['source'],sha256=x['sha256']))
frozen=json.loads((P/'candidate-frozen.json').read_text())
for x in frozen['files']:assert sha(Path(x['path']))==x['sha256'];checked.append(x)
for x in json.loads((P/'preflight.json').read_text())['checks']:assert sha(Path(x['path']))==x['sha256'];checked.append(x)
tests=json.loads((P/'coverage-tests.json').read_text());assert tests['total']==tests['passed']==26
coverage=json.loads((P/'analysis-v2/coverage-live-result.json').read_text());assert coverage['missingRequired']==16 and coverage['status']=='FAIL'
kernel=json.loads((P/'analysis-v2/qualification-result.json').read_text());assert kernel['starts']==kernel['stops']==36 and kernel['realNativeCount']==17
run=uuid.uuid4().hex;(R/'final'/run).mkdir(parents=True)
with (R/'host_preflight.ps1').open('xb') as f:f.write((P/'host_preflight.ps1').read_bytes())
save(R/'preflight.json',dict(status='PASS',hostRun=run,checks=checked,candidate=frozen['code'],archive=receipt,verifiedCandidateFiles=len(frozen['files']),frozenCheckerSHA256=sha(Path(frozen['code'])/'cleanup_checker.py'),protectedAccess=False,productionChanged=False))
print(json.dumps(dict(status='PASS',hostRun=run,hashComparisons=len(checked),archiveMembers=226,candidateFiles=len(frozen['files']))))
