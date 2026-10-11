import hashlib,json,os,shutil,uuid,zipfile
from pathlib import Path
R=Path(__file__).parent; P=R.parent/'stage6-small-combined-20260922'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
rc=load(P/'archive-verification.json'); archive=Path(rc['archive']); manifest=archive.parent/'manifest.json'
assert sha(archive)==rc['archiveSHA256']=='47f321e7c8861611e300239eb9d33c7171b5e3422e6495e6fe93a794867d1bc0'
assert sha(manifest)==rc['manifestSHA256']=='c6ebb7895243d0da824a0bd84e2c5df54d9df535fa83cf1df01e9bdbf39349fc'
checks=[]
with zipfile.ZipFile(archive) as z:
 assert len(z.namelist())==len(set(z.namelist()))==324
 assert z.read('manifest.json')==manifest.read_bytes()
 for x in load(manifest)['files']:
  b=z.read(x['name']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']==sha(x['source']),x['name']
  checks.append(dict(path=x['source'],sha256=x['sha256']))
for name in ('candidate-frozen.json','adapter-frozen.json'):
 for x in load(P/name)['files']:
  assert sha(x['path'])==x['sha256'];checks.append(x)
assert load(P/'combined-tests-v2.json')['passed']==31
assert load(P/'combined-tests.json')['passed']==30
assert sha(P/'acceptance-seal.json')=='184f2be21d0c6e576a5f671d266a3f35662e729bcce79692e73e8bbba30059e7'
source=Path(load(P/'preflight.json')['code']);frozen=source/'cleanup_checker.py'
assert sha(frozen)=='e6fbefd3fd463c6c8e09d0e8273a81b46ee2806515cae05e7837ea905a3e69d6'
historical=R.parent/'stage6-durability-contract-review-20260921/REPORT.md'
assert '21 AMBIGUOUS / 1 UNMATCHED' in historical.read_text(encoding='utf-8');checks.append(dict(path=str(historical),sha256=sha(historical)))
work=Path(r'D:\JARVIS-STAGE6-LIVE')/uuid.uuid4().hex
work.mkdir(); C=work/'checker-v2';C.mkdir();(work/'fixtures').mkdir()
copied=[]
for src,name in [(frozen,'frozen_reference.py'),(frozen,'checker_v2.py'),(P/'combined.py','combined.py'),(P/'coverage.py','coverage.py'),(R.parent/'stage6-durable-kernel-20260921/qualification.py','qualification.py'),(source/'process_instances.py','process_instances.py'),(source/'application_authority.py','application_authority.py')]:
 dst=C/name
 with dst.open('xb') as f:f.write(src.read_bytes())
 copied.append(dict(source=str(src),sourceSHA256=sha(src),candidate=str(dst),initialSHA256=sha(dst)))
host=uuid.uuid4().hex;(R/'final'/host).mkdir(parents=True)
with (R/'host_preflight.ps1').open('xb') as f:f.write((P/'host_preflight.ps1').read_bytes())
save(R/'preflight.json',dict(status='EVIDENCE_PASS_HOST_PENDING',workspace=str(work),candidate=str(C),source=str(source),frozen=str(frozen),frozenSHA256=sha(frozen),copied=copied,checks=checks,archive=rc,hostRun=host,protectedAccess=False,productionChanged=False))
print(json.dumps(dict(status='EVIDENCE_PASS_HOST_PENDING',candidate=str(C),hostRun=host,comparisons=len(checks),archiveMembers=324)))
