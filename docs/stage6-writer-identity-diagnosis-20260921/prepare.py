import hashlib,json,zipfile,uuid,shutil,datetime
from pathlib import Path
R=Path(__file__).parent
E=R.parent/'stage6-event-integration-20260921'
C=Path(r'D:\JARVIS-STAGE6-LIVE\6d305fb9fc7440c5bf485466e9d708df\code')
A=Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 EVENT INTEGRATION 20260921')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(p,o):
 with p.open('x',encoding='utf8') as f:json.dump(o,f,indent=2)
assert not (R/'freeze.json').exists()
checks=json.loads((R.parent/'stage6-instance-stream-design-20260921/freeze.json').read_text())['checks']
for x in checks:assert sha(Path(x['path']))==x['sha256'],x['path']
receipt=json.loads((E/'archive-verification.json').read_text())
assert sha(A/'evidence.zip')==receipt['zipSHA256']
assert sha(A/'manifest.json')==receipt['manifestSHA256']
manifest=json.loads((A/'manifest.json').read_text())['files']
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==262 and len(manifest)==261
 assert set(z.namelist())=={x['name'] for x in manifest}|{'manifest.json'}
 assert z.read('manifest.json')==(A/'manifest.json').read_bytes()
 for x in manifest:
  b=z.read(x['name']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'],x['name']
  prefix,rel=x['name'].split('/',1)
  p=(E if prefix=='report' else C)/rel
  assert p.is_file() and sha(p)==x['sha256'],str(p)
for x in json.loads((E/'plan.json').read_text())['archives']:assert sha(Path(x['path']))==x['sha256']
N=Path(r'D:\JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code'
N.mkdir(parents=True,exist_ok=False)
copied=[]
for p in C.iterdir():
 if p.is_file() and p.suffix in ('.cs','.py','.ps1','.cpp','.h','.exe','.dll','.json','.txt'):
  dest=N/p.name
  with dest.open('xb') as f:f.write(p.read_bytes())
  copied.append({'name':p.name,'sha256':sha(p)})
shutil.copyfile(R.parent/'stage6-evidence-restoration-20260921/host_preflight.ps1',R/'host_preflight.ps1')
run=uuid.uuid4().hex;(R/'final'/run).mkdir(parents=True,exist_ok=False)
save(R/'freeze.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'archiveMembers':262,'archiveSHA256':receipt['zipSHA256'],'allCurrentEvidenceMatchesArchive':True,'newCode':str(N),'copies':copied,'hostRun':run,'historicalQueueTimeSeries':'UNKNOWN — not recorded','protectedAccess':False})
print(json.dumps({'code':str(N),'hostRun':run,'frozenChecks':len(checks),'archiveMembers':262}))
