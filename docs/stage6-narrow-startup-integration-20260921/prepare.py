"""Prepare a fresh small-only integration candidate; never enumerate bulk/protected data."""
import pathlib,json,hashlib,shutil,uuid,datetime
R=pathlib.Path(__file__).parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
C=pathlib.Path('D:/JARVIS-STAGE6-LIVE/e23d36c0a24246c996aa28e5d5561863/code')
S=pathlib.Path('D:/JARVIS-STAGE6-LIVE/68b6e62890e742b4bedb13cbb0f49e92/code')
old=read(R.parent/'stage6-large-startup-trace-preflight-20260921/preflight.json')
checks=[]
for x in old['sourceChecks']:
 p=pathlib.Path(x['path']);actual=sha(p)
 assert actual==x['expected'],str(p)
 checks.append(dict(path=str(p),sha256=actual))
code=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code'
code.mkdir(parents=True,exist_ok=False)
rows=read(C/'run-source.json')
for x in rows:
 assert pathlib.Path(x['name']).name==x['name']
 shutil.copy2(C/x['name'],code/x['name'])
 assert sha(code/x['name'])==x['sha256']
for name in ('startup_trace.cpp','J6StartupTrace.exe'):
 shutil.copy2(S/name,code/name)
source=code/'small-sacrificial';source.mkdir()
for i in range(12):
 p=source/f'artifact-{i:02d}.bin';p.write_bytes(bytes([i])*65536)
files=[dict(name=p.name,bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns,sha256=sha(p)) for p in sorted(source.iterdir())]
(code/'baseline-allowlist.json').write_text(json.dumps(dict(approvedProtectedRoots=[],realProtectedAccess=False,syntheticRoots=[str(source)]),indent=2))
limits=read(C/'baseline-limits.json');limits.update(campaign=90,monitor=180,hold=0)
(code/'baseline-limits.json').write_text(json.dumps(limits,indent=2))
plan=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),code=str(code),source=str(source),sourceChecks=checks,preChangeHashes=rows,smallFiles=files,limits=limits,protectedAccess=False,largeDatasetAccess=False)
(R/'plan.json').write_text(json.dumps(plan,indent=2))
print(json.dumps(dict(code=str(code),source=str(source),sourceChecks=len(checks),smallFiles=len(files),smallBytes=sum(x['bytes'] for x in files))))
