import pathlib,json,hashlib,zipfile,shutil,subprocess,uuid
R=pathlib.Path(__file__).resolve().parent
OLD=pathlib.Path('D:/JARVIS-STAGE6-LIVE/631d1b7ca4ff4c509c02a015ff1a6ce6/code')
PREV=R.parent/'stage6-dry-probe-diagnosis-20260920'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):
 with (R/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
checks=[]
for folder in (PREV,R.parent/'stage6-probe-acceptance-20260920'):
 m=json.loads((folder/'archive-manifest.json').read_text())
 with zipfile.ZipFile(folder/'evidence.zip') as z:
  for row in m['files']:
   b=z.read(row['name']);assert len(b)==row['size'] and hashlib.sha256(b).hexdigest()==row['sha256']
 checks.append(dict(path=str(folder/'evidence.zip'),sha256=sha(folder/'evidence.zip'),members=len(m['files'])+1))
save('historical-preservation-before.json',checks)
files=[p for p in sorted(OLD.iterdir()) if p.is_file()]
save('source-before.json',[dict(path=str(p),name=p.name,size=p.stat().st_size,sha256=sha(p)) for p in files])
repo=R.parent.parent
state={}
for name,args in [('head',['rev-parse','HEAD']),('branch',['branch','--show-current']),('status',['status','--porcelain=v1','-unormal'])]:
 p=subprocess.run(['git','-C',str(repo),*args],capture_output=True,text=True);state[name]=dict(exit=p.returncode,stdout=p.stdout,stderr=p.stderr)
# Application tracked bytes, excluding evidence documents; never read .env.
p=subprocess.run(['git','-C',str(repo),'ls-files','-z'],capture_output=True,check=True)
state['trackedApplication']=[dict(path=n,sha256=sha(repo/n)) for n in p.stdout.decode().split('\0') if n and not n.startswith(('docs/','.env')) and (repo/n).is_file()]
save('repository-before.json',state)
CODE=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';CODE.mkdir(parents=True,exist_ok=False)
for p in files:shutil.copyfile(p,CODE/p.name)
save('plan.json',dict(live_code=str(CODE),previous=str(OLD),report=str(R),archive=str(pathlib.Path('C:/Users/jonny/OneDrive/Desktop/TEAGUE INDUSTRIES DATABASE/06 SOURCE RECORDS/STAGE6 CLEANUP HARDENING 20260920')),diagnosticOnly=True,protectedBaselineAuthorized=False))
print(CODE)
