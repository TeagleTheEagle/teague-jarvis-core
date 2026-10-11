import hashlib,json,os,shutil,uuid,zipfile
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-checker-integration-20260922';S=R.parent/'stage6-small-combined-20260922'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
checks=[];archives=[]
for source in (P,S):
 rc=load(source/'archive-verification.json');a=Path(rc['archive']);m=a.parent/'manifest.json'
 assert sha(a)==rc['archiveSHA256'] and sha(m)==rc['manifestSHA256']
 with zipfile.ZipFile(a) as z:
  assert len(z.namelist())==len(set(z.namelist()))==rc['membersVerified'] and z.read('manifest.json')==m.read_bytes()
  for x in load(m)['files']:
   b=z.read(x['name']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']==sha(x['source']),x['name'];checks.append(dict(path=x['source'],sha256=x['sha256']))
 archives.append(rc)
old=Path(load(P/'preflight.json')['candidate']);runtime=Path(load(S/'preflight.json')['code'])
for x in load(P/'candidate-freeze.json')['files']+load(S/'candidate-frozen.json')['files']:
 assert sha(x['path'])==x['sha256'];checks.append(x)
assert load(P/'acceptance-seal.json')['tests']==114 and load(P/'acceptance-seal.json')['failed']==0
assert sha(runtime/'cleanup_checker.py')=='e6fbefd3fd463c6c8e09d0e8273a81b46ee2806515cae05e7837ea905a3e69d6'
assert shutil.disk_usage('D:/').free>=2*1024**3
C=Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';C.mkdir(parents=True)
copies=[]
for p in runtime.iterdir():
 if p.is_file():
  assert p.name!='.env' and not p.is_symlink()
  with (C/p.name).open('xb') as f:f.write(p.read_bytes())
  copies.append(dict(source=str(p),path=str(C/p.name),sha256=sha(p)))
checker=C/'medium-checker';checker.mkdir()
for p in old.iterdir():
 if p.is_file():
  with (checker/p.name).open('xb') as f:f.write(p.read_bytes())
  copies.append(dict(source=str(p),path=str(checker/p.name),sha256=sha(p)))
host=uuid.uuid4().hex;(R/'final'/host).mkdir(parents=True)
with (R/'host_preflight.ps1').open('xb') as f:f.write((P/'host_preflight.ps1').read_bytes())
run='identity-'+uuid.uuid4().hex;root=C/run;root.mkdir();(root/'temp').mkdir();(root/'analysis').mkdir()
save(R/'preflight.json',dict(status='HASHES_PASS_HOST_PENDING',code=str(C),checker=str(checker),originalRuntime=str(runtime),originalChecker=str(old),run=run,root=str(root),hostRun=host,checks=checks,copies=copies,archives=archives,dFree=shutil.disk_usage('D:/').free))
save(R/'run.json',dict(run=run,path=str(root)))
print(json.dumps(dict(status='HASHES_PASS_HOST_PENDING',code=str(C),hostRun=host,run=run,hashComparisons=len(checks),archiveMembers=[x['membersVerified'] for x in archives])))
