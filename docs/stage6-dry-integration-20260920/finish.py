import pathlib,json,hashlib,re,zipfile
R=pathlib.Path(__file__).parent;plan=json.loads((R/'plan.json').read_text());C=pathlib.Path(plan['code']);prior=R.parent/'stage6-dual-cleanup-20260920';repo=R.parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,x):
 with (R/n).open('x') as f:json.dump(x,f,indent=2)
before=json.loads((R/'source-before.json').read_text());pres=[]
for x in before:
 actual=sha(pathlib.Path(x['path']));candidate=sha(C/x['name']);pres.append(dict(name=x['name'],original=x['path'],before=x['sha256'],originalAfter=actual,candidateAfter=candidate,unchanged=actual==candidate==x['sha256']))
assert all(x['unchanged'] for x in pres);put('original-source-preservation.json',pres)
final=json.loads((R/'candidate-source.json').read_text());assert all(sha(C/x['name'])==x['sha256'] for x in final)
put('final-source.json',[dict(x,path=str(C/x['name'])) for x in final])
app=[]
for x in json.loads((prior/'application-preservation.json').read_text())['files']:
 actual=sha(repo/x['path']);app.append(dict(path=x['path'],sha256=actual,unchanged=actual==x['sha256']))
assert all(x['unchanged'] for x in app);put('application-preservation.json',dict(allUnchanged=True,files=app))
receipt=json.loads((prior/'archive-verification.json').read_text());assert sha(prior/'evidence.zip')==receipt['zipSHA256'];assert sha(prior/'archive-manifest.json')==receipt['manifestSHA256']
put('historical-archive-after.json',dict(zipSHA256=receipt['zipSHA256'],manifestSHA256=receipt['manifestSHA256'],unchanged=True))
live=C/'integrated-miniature-807c92300b9049e8b5bb553c15e41d5c'
def read(n):return json.loads((live/n).read_text(encoding='utf-8-sig'))
result=read('integration-result.json');assert result['status']=='MINIATURE_INTEGRATION_PASS' and not result['dryRunExecuted']
cleanup=read('integrated-cleanup.json');assert cleanup['status']=='PASS';kernel=read('etw-result.json')
known={}
for row in kernel['rows']:known[(row['pid'],row['created'])]=dict(pid=row['pid'],created=row['created'],role='kernel',kernelExit=row['exitFiletime'])
for role,row in read('observer-identities.json').items():known[(row['pid'],row['created'])]=dict(pid=row['pid'],created=row['created'],role=role,kernelExit=None)
launcher=read('launcher.json');known[(launcher['pid'],launcher['creationFiletime'])]=dict(pid=launcher['pid'],created=launcher['creationFiletime'],role='launcher',kernelExit=None)
put('known-identities.json',list(known.values()))
one=read('hash-pass-1.json');two=read('hash-pass-2.json');assert one['files']==two['files']
worker=next(x for x in read('stress-result.json')['launched'] if x['role']=='hash-worker');kw=next(x for x in kernel['rows'] if x['pid']==worker['pid'] and x['created']==worker['created']);freq=read('etw-ready.json')['frequency']
assert kw['startQpc']/freq<=one['beginQpcNs']/1e9<one['endQpcNs']/1e9<=two['beginQpcNs']/1e9<two['endQpcNs']/1e9<=kw['stopQpc']/freq
source=pathlib.Path(read('contract.json')['source']);assert all(dict(bytes=(source/n).stat().st_size,mtime_ns=(source/n).stat().st_mtime_ns,sha256=sha(source/n))==x for n,x in one['files'].items())
archive=read('archive-verification.json');assert sha(live/'evidence.zip')==archive['sha256'];members=read('archive-manifest.json')
with zipfile.ZipFile(live/'evidence.zip') as z:
 assert len(z.namelist())==archive['members']
 for x in members:assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256']
metrics=dict(run=str(live),result=result,cleanup={k:v for k,v in cleanup.items() if k not in ('identities','outsideKernel','outsideAppEvents')},syntheticCount=len(one['files']),syntheticBytes=sum(x['bytes'] for x in one['files'].values()),hashesMatch=True,hashesInsideKernelWorkerLifetime=True,sourcePreserved=True,phaseState=read('state.json'),heartbeatMax=max(x['interval'] for x in read('app-heartbeats.json')),hashHeartbeatMaxAge=max(x['age'] for x in read('hash-health-samples.json')),collectorHeartbeatMaxAge=max(x['age'] for x in read('collector-health-samples.json')),app=read('app-result.json'),archive=archive,probeCount=len(read('probe-timings.json')),probeMaxConfirmedSeconds=max(x['policy']['confirmedElapsed'] for x in read('probe-timings.json')),hardDeadlineViolations=sum(bool(x.get('hardDeadlineFailure')) for x in read('probe-timings.json')))
put('miniature-summary.json',metrics)
reg=next(C.glob('integration-regress-*/results.json'));commands=json.loads(reg.read_text());assert len(commands)==8 and all(x['exit']==0 for x in commands)
counts={n:int(re.search(r'Ran (\d+) tests',(reg.parent/(n+'.stderr')).read_text()).group(1)) for n in ('integration','dual','kernel','hardening')}
probe=json.loads(next(C.glob('probe-policy-*/result.json')).read_text());monitor=json.loads((C/'focused-result.json').read_text());counts.update(probe=probe['executed'],monitor=monitor['executed'])
queue=json.loads(next(C.glob('queue-tests-*/result.json')).read_text(encoding='utf-8-sig'));fin=json.loads(next(C.glob('finalization-tests-*/result.json')).read_text(encoding='utf-8-sig'))
put('regression-summary.json',dict(unittestCounts=counts,total=sum(counts.values()),queueAssertions=queue['results']['checks'],finalizationAssertions=fin['checks'],queue=queue,finalization=fin,commands=commands))
full=repo/'docs/stage6-heartbeat-journal-20260918/sacrificial';inputs=[dict(name=p.name,size=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns) for p in sorted(full.iterdir()) if p.is_file()]
assert len(inputs)==12;put('full-input-availability.json',dict(files=inputs,bytes=sum(x['size'] for x in inputs),hashingPerformed=False,launchScript=str(C/'dry_launch.ps1'),launchScriptExists=(C/'dry_launch.ps1').is_file(),fullDryRunExecuted=False))
print(json.dumps(dict(originalSources=len(pres),applicationFiles=len(app),candidateFiles=len(final),unitTests=sum(counts.values()),miniature=result,heartMax=metrics['heartbeatMax'])))
