import pathlib,sys,json,hashlib,zipfile,uuid,shutil
R=pathlib.Path(__file__).parent;H=R.parent/'stage6-evidence-restoration-20260921';sys.path.insert(0,str(H))
from evidence_io import create_bytes,create_json,create_run
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
P=R.parent/'stage6-instance-stream-design-20260921'
f=load(P/'freeze.json')
for x in f['checks']:assert sha(pathlib.Path(x['path']))==x['sha256'],x['path']
assert sha(P/'final-host-state.json')=='c01b96eecf05c4b29723b900d0543d104fe0f514487886339f080d3d709b17cb'
verified=[]
for directory,hashkey in [(P,'zipSHA256'),(R.parent/'stage6-authoritative-integration-20260921','sha256'),(H,'zipSHA256')]:
 receipt=load(directory/'archive-verification.json');a=pathlib.Path(receipt['path'])/'evidence.zip';assert sha(a)==receipt[hashkey]
 with zipfile.ZipFile(a) as z:
  assert len(z.namelist())==len(set(z.namelist()))==receipt['members']
  m=json.loads(z.read('manifest.json'))
  for x in m['files']:
   with z.open(x['name']) as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==x['sha256']
 verified.append(dict(path=str(a),sha256=sha(a),members=receipt['members']))
for old in f['archives']:
 a=pathlib.Path(old['path'])/'evidence.zip';assert sha(a)==old['zipSHA256'];verified.append(dict(path=str(a),sha256=sha(a),membersPreviouslyVerified=old['members']))
root=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE')/('event-integration-'+uuid.uuid4().hex);root.mkdir(exist_ok=False);code=root/'code';code.mkdir(exist_ok=False)
copied=[]
for x in f['checks'][:116]:
 p=pathlib.Path(x['path']);create_bytes(code/p.name,p.read_bytes());assert sha(code/p.name)==x['sha256'];copied.append(dict(name=p.name,sha256=x['sha256']))
# New host preflight tool, never the historical overwrite-capable entry point.
create_bytes(R/'evidence_io.py',(H/'evidence_io.py').read_bytes())
create_bytes(R/'host_preflight.ps1',(H/'host_preflight.ps1').read_bytes())
(R/'final').mkdir(exist_ok=False);rid=uuid.uuid4().hex;create_run(R/'final',rid)
create_json(R/'plan.json',dict(code=str(code),root=str(root),preflightRunId=rid,frozenChecks=f['checks'],copied=copied,archives=verified,protectedAccess=False,productionChanged=False))
print(json.dumps(dict(code=str(code),preflightRunId=rid,candidateHashes=116,archives=verified)))
