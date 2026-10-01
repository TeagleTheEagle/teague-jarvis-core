"""Read-only evidence inspection. Does not launch/import the collector or hash bulk data."""
import pathlib,json,hashlib,zipfile,shutil,datetime
R=pathlib.Path(__file__).parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
O=pathlib.Path('D:/JARVIS-STAGE6-LIVE/1c1f5d0c390b42cc9ba9f4f6221dabc6/code')
H=pathlib.Path('D:/JARVIS-STAGE6-LIVE/2ef4a4641a234b7dbfdce8db88cb1e39/code')
C=pathlib.Path('D:/JARVIS-STAGE6-LIVE/e23d36c0a24246c996aa28e5d5561863/code')
prior=R.parent/'stage6-internal-startup-trace-20260921';sp=read(prior/'followup-plan.json');S=pathlib.Path(sp['code'])
checks=[]
for kind,root,manifest in [('collector',O,read(O/'baseline-source.json')),('diagnostic',H,read(H/'hardening-hashes.json')),('integration',C,read(C/'run-source.json')),('startup-trace',S,sp['diagnosticHashes'])]:
 for x in manifest:
  actual=sha(root/x['name']);checks.append(dict(kind=kind,path=str(root/x['name']),expected=x['sha256'],actual=actual,pass_=actual==x['sha256']))
  if actual!=x['sha256']:raise RuntimeError('SOURCE DRIFT '+str(root/x['name']))
cal=O/'calibration.json';assert sha(cal)=='8876f2fe62b3e4cf23f22289bf9f318acf1f8159da62d4912cec3d1a9f268753'
manifest=C/'rehome-1ae56ff933c9432b8e90ce326cb86c8c/dataset-manifest.json';assert sha(manifest)=='7ed9f3581dedd5ff391599c20b460f8090af57cd0d0b8fe8e4e0826babda1fb0'
dataset=read(manifest);T=pathlib.Path(dataset['root']);assert T==C/'large-synthetic'
assert not any(p.lstat().st_file_attributes&0x400 for p in (T,*T.parents))
actualFiles={p.relative_to(T).as_posix():p for p in T.rglob('*') if p.is_file()}
assert set(actualFiles)=={x['path'] for x in dataset['files']}
metadata=[]
for x in dataset['files']:
 p=actualFiles[x['path']];st=p.lstat();assert not st.st_file_attributes&0x400 and st.st_nlink==1 and st.st_size==x['bytes'] and st.st_mtime_ns==x['mtime_ns']
 metadata.append(dict(path=str(p),bytes=st.st_size,mtime_ns=st.st_mtime_ns,contentHash='NOT_RECOMPUTED_THIS_PREFLIGHT'))
assert len(metadata)==12 and sum(x['bytes'] for x in metadata)==59665402098
archives=[]
for name in ('stage6-internal-startup-trace-20260921','stage6-call-tracing-20260921','stage6-dataset-rehome-20260920'):
 receipt=read(R.parent/name/'archive-verification.json');A=pathlib.Path(receipt['path']);assert sha(A/'evidence.zip')==receipt['zipSHA256'] and sha(A/'archive-manifest.json')==receipt['manifestSHA256']
 with zipfile.ZipFile(A/'evidence.zip') as z:
  m=read(A/'archive-manifest.json');rows=m['files'] if isinstance(m,dict) else m
  assert len(z.namelist())==receipt['members'];assert z.read('archive-manifest.json')==(A/'archive-manifest.json').read_bytes()
  for x in rows:assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256']
 archives.append(receipt)
citations=[]
for path,needles in [(C/'large_launch.ps1',['J6BaselineTrace.exe','large_collect.py','timed_monitor.ps1']),(C/'large_collect.py',["probe=Probe("]),(S/'startup_driver.py',['J6EntryObserve.exe']),(S/'entry_observer.cpp',['DEBUG_ONLY_THIS_PROCESS','PE_ENTRY_EXECUTED']),(S/'startup_trace.cpp',['static Row* Target','startup.size()>=200000'])]:
 lines=path.read_text().splitlines()
 for needle in needles:
  for n,line in enumerate(lines,1):
   if needle in line:citations.append(dict(path=str(path),line=n,text=line))
out=dict(status='BLOCKED',reason='STARTUP_TRACE_NOT_INTEGRATED_WITH_FROZEN_LARGE_COLLECTOR',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sourceChecks=checks,calibrationHashVerified=True,datasetManifestHashVerified=True,datasetMetadata=metadata,datasetFullContentHash='NOT_RUN_AFTER_INTEGRATION_BLOCKER',archivesVerified=archives,DfreeBytes=shutil.disk_usage(C).free,codeEvidence=citations,observersStarted=False,largeRunStarted=False,sourceChanged=False,protectedAccess=False,productionChanged=False)
with (R/'preflight.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ('sourceChecks','datasetMetadata','archivesVerified','codeEvidence')}))
print('source counts', {k:sum(x['kind']==k for x in checks) for k in ('collector','diagnostic','integration','startup-trace')})
