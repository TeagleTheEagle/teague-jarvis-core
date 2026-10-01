import pathlib,json,hashlib,difflib
R=pathlib.Path(__file__).parent;plan=json.loads((R/'plan.json').read_text());C=pathlib.Path(plan['live_code']);old=R.parent/'stage6-kernel-child-trace-20260920'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,x):
 with (R/n).open('x') as f:json.dump(x,f,indent=2)
before=json.loads((R/'source-before.json').read_text());pres=[];changes=[]
for x in before:
 p=pathlib.Path(x['path']);pres.append(dict(path=str(p),sha256=sha(p),unchanged=sha(p)==x['sha256']))
 now=C/x['name']
 if sha(now)!=x['sha256']:
  changes.append(dict(name=x['name'],before=x['sha256'],after=sha(now)))
  if now.suffix in ('.py','.ps1','.cs','.cpp'):
   with (R/(now.name+'.diff')).open('x') as f:f.writelines(difflib.unified_diff(p.read_text().splitlines(True),now.read_text().splitlines(True),fromfile=str(p),tofile=str(now)))
assert all(x['unchanged'] for x in pres);put('inherited-source-preservation.json',pres)
assert {x['name'] for x in changes}=={'kernel_trace.cpp','J6KernelTrace.exe'}
sources=[dict(path=str(p),name=p.name,sha256=sha(p)) for p in sorted(C.iterdir()) if p.is_file() and p.suffix in ('.py','.ps1','.cs','.cpp','.exe')]
put('final-source.json',sources)
put('source-changes.json',dict(modified=changes,added=[x for x in sources if x['name'] not in {b['name'] for b in before}],productionRuntimeChanged=False))
app=[];repo=R.parent.parent
for x in json.loads((old/'application-preservation.json').read_text())['files']:
 p=repo/x['path'];app.append(dict(path=x['path'],sha256=sha(p),matchesPrevious=sha(p)==x['sha256']))
put('application-preservation.json',dict(files=app,allUnchanged=all(x['matchesPrevious'] for x in app)))
assert all(x['matchesPrevious'] for x in app)
known={};runs=[]
for root in sorted(C.glob('dual-*')):
 if not root.is_dir() or not(root/'launcher.json').exists():continue
 launch=json.loads((root/'launcher.json').read_text(encoding='utf-8-sig'));known[(launch['pid'],launch['creationFiletime'])]=dict(pid=launch['pid'],created=launch['creationFiletime'],role='launcher',kernelExit=None)
 if not(root/'etw-result.json').exists():continue
 kernel=json.loads((root/'etw-result.json').read_text());observers=json.loads((root/'observer-identities.json').read_text(encoding='utf-8-sig'))
 for x in kernel['rows']:known[(x['pid'],x['created'])]=dict(pid=x['pid'],created=x['created'],role='kernel-observed',kernelExit=x['exitFiletime'])
 for role,x in observers.items():known[(x['pid'],x['created'])]=dict(pid=x['pid'],created=x['created'],role=role,kernelExit=None)
 file=root/('cleanup-checker-reviewed.json' if (root/'cleanup-checker-reviewed.json').exists() else 'cleanup-checker-result.json')
 result=json.loads(file.read_text());heart=json.loads((root/'app-heartbeats.json').read_text());appresult=json.loads((root/'app-result.json').read_text(encoding='utf-8-sig'))
 frozen=json.loads((root/'source-hashes.json').read_text(encoding='utf-8-sig'));drift=[x['name'] for x in frozen if sha(C/x['name']).lower()!=x['sha256'].lower()]
 runs.append(dict(run=str(root),result={k:v for k,v in result.items() if k not in ('identities','outsideAppEvents','outsideKernel','preservedImageQueryErrors')},maxHeartbeat=max(x['interval'] for x in heart),queue=appresult['queue'],imageQueryErrors=len(result.get('preservedImageQueryErrors',[])),sourceChangesSinceRun=drift,outsideKernel=result['outsideKernel'],outsideAppEventCount=len(result['outsideAppEvents'])))
put('known-identities.json',list(known.values()));put('campaign-summary.json',runs)
assert len(runs)==2 and all(x['result']['status']=='PASS' for x in runs)
final=next(x for x in runs if x['run'].endswith('dual-07290815162f45d69e0ce858641f5d9a'));assert not final['sourceChangesSinceRun']
historical=[]
for name in ('evidence.zip','archive-manifest.json'):
 receipt=json.loads((old/'archive-verification.json').read_text());expect=receipt['zipSHA256' if name=='evidence.zip' else 'manifestSHA256'];actual=sha(old/name);assert actual==expect;historical.append(dict(path=str(old/name),sha256=actual,unchanged=True))
put('historical-archive-after.json',historical)
print(json.dumps(dict(originalDiagnosticSources=len(pres),applicationFiles=len(app),applicationUnchanged=True,finalSourceFiles=len(sources),runs=len(runs),knownIdentities=len(known),finalSourceDrift=final['sourceChangesSinceRun'])))
