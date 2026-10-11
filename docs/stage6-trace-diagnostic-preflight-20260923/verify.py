"""Read-only input verification; writes only this new blocked-preflight record."""
import hashlib,json,sys,zipfile,datetime
from pathlib import Path
R=Path(__file__).parent
D=R.parent
S=D/'stage6-loss-telemetry-v2-20260923'
P=D/'stage6-one-small-live-v3-20260923'
O=D/'stage6-coordination-v3-20260923'
C=Path(r'D:\JARVIS-STAGE6-LIVE\7f204e14c90a497a8476be0e9927e074\code')
T=Path(r'D:\JARVIS-STAGE6-LIVE\cab9745de28a4cae8aa6f6f7a516bf54\code-r2')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def archive(receipt,count):
 v=read(receipt);a=Path(v['archive']);m=a.parent/'manifest.json'
 assert sha(a)==v['archiveSHA256'] and sha(m)==v['manifestSHA256']
 rows=read(m);rows=rows['files'] if isinstance(rows,dict) else rows
 with zipfile.ZipFile(a) as z:
  assert len(z.namelist())==len(set(z.namelist()))==len(rows)==count
  for x in rows:
   with z.open(x['path']) as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
   assert actual==x['sha256'] and z.getinfo(x['path']).file_size==x['bytes']
 return dict(path=str(a),members=count,sha256=v['archiveSHA256'])
archives=[archive(S/'archive-receipt.json',299),archive(P/'archive-receipt.json',105)]
F=C/'protected-f117995dd9ef4ed1b33c1b44b1973293'
rows=read(P/'failed-run-inventory.json')['files']
assert len(rows)==len([p for p in F.rglob('*') if p.is_file()])==83
for x in rows:
 p=F/x['path'];s=p.stat()
 assert (s.st_size,s.st_mtime_ns,s.st_ino,sha(p))==(x['bytes'],x['mtimeNs'],x['fileId'],x['sha256'])
old=read(O/'candidate-final-r2.json')
assert sha(C/'small-source-v3.json')==old['manifestSHA256'] and len(old['files'])==216
for x in old['files']:assert sha(C/x['name'])==x['sha256']
assert sha(T/'source-manifest.json')=='e781ed6389dd809805fb89c27b6f838623d4f2da707fcd7a160d22c25249ea28'
tools=read(T/'source-manifest.json');assert len(tools)==4
for x in tools:assert sha(T/x['name'])==x['sha256']
inputs=read(O/'before.json')['inputs'];assert len(inputs)==482
for x in inputs:
 p=Path(x['path']);assert 'virtualbox' not in str(p).lower()
 s=p.stat();assert (s.st_size,s.st_mtime_ns,sha(p))==(x['bytes'],x['mtimeNs'],x['sha256'])
N=S/'candidate';freeze=read(S/'candidate-freeze.json')
assert sha(N/'small-source-v3.json')==freeze['sourceManifestSHA256']
active=read(N/'small-source-v3.json');assert len(active)==217
for x in active:
 p=N/x['name'];assert p.stat().st_size==x['bytes'] and sha(p)==x['sha256']
names={x['name'] for x in active}
assert {'baseline-allowlist.json','small_launch_v3.ps1','baseline_contract.py','small_binding_v3.py'}<=names
allow=read(N/'baseline-allowlist.json')
assert allow['syntheticRoots']==[str(C/'small-synthetic')]
assert allow['approvedProtectedRoots']==[] and allow['realProtectedAccess'] is False
# Static rule proof. No candidate import, source traversal, dataset preparation or launch.
binding=(N/'small_binding_v3.py').read_text()
contract=(N/'baseline_contract.py').read_text()
launcher=(N/'small_launch_v3.ps1').read_text()
assert "root=prepare(str(CODE/'small-synthetic'))" in binding
assert "if str(p) not in allowed['syntheticRoots']:raise ValueError('Unapproved root')" in contract
assert str(C/'J6OwnedEntry.dll').replace('\\','\\\\') in launcher
sys.path.insert(0,str(T))
import failure_preserve_v1 as f
census=f.host_census(R)
result=dict(status='BLOCKED',reason='FROZEN_CANDIDATE_NOT_RELOCATABLE_TO_REQUIRED_FRESH_WORKSPACE',
 utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 verification=dict(successorFiles=217,originalFiles=216,failedRunFiles=83,preservationTools=4,originalInputs=482,archives=archives),
 sourceManifestSHA256=freeze['sourceManifestSHA256'],
 sourcePaths=[dict(path=str(N/name),sha256=sha(N/name)) for name in ('baseline-allowlist.json','baseline_contract.py','small_binding_v3.py','small_launch_v3.ps1','owned_entry.cpp','J6OwnedEntry.dll')],
 evidence=dict(approvedSyntheticRoot=allow['syntheticRoots'][0],freshWorkspaceSourceRejected=True,launcherDLL=str(C/'J6OwnedEntry.dll'),nativeBridgeDerivesCollectorFromRunRoot=True),
 census=census,censusClean=f.census_clean(census,R),
 liveAttempts=0,uacRequests=0,freshRunDirectoriesCreated=0,candidateModified=False,
 checkerInvoked=False,successFinalizerInvoked=False,protectedAccess=False,productionChange=False,
 diagnosis='TRACE_LOSS_CAUSE_UNCONFIRMED',historicalStage1Cause='UNCONFIRMED')
with (R/'preflight.json').open('x') as out:json.dump(result,out,indent=2)
print(json.dumps(result))
