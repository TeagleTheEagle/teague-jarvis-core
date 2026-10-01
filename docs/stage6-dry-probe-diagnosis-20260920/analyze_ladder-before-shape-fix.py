import pathlib,json,hashlib,statistics,ctypes as c,ctypes.wintypes as w,difflib
R=pathlib.Path(__file__).parent;plan=json.loads((R/'plan.json').read_text());D=pathlib.Path(plan['live_code'])
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):
 with (R/n).open('x') as f:json.dump(v,f,indent=2)
k=c.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE;k.GetProcessTimes.argtypes=[w.HANDLE]+[c.POINTER(w.FILETIME)]*4;k.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];k.CloseHandle.argtypes=[w.HANDLE]
def identity(pid,created):
 h=k.OpenProcess(0x1000|0x100000,False,int(pid))
 if not h:return dict(pid=pid,created=str(created),state='ABSENT' if c.get_last_error()==87 else 'UNCONFIRMED',winerror=c.get_last_error())
 try:
  v=[w.FILETIME() for _ in range(4)]
  if not k.GetProcessTimes(h,*[c.byref(x) for x in v]):raise c.WinError(c.get_last_error())
  actual=str((v[0].dwHighDateTime<<32)|v[0].dwLowDateTime);status=k.WaitForSingleObject(h,0)
  return dict(pid=pid,created=str(created),actual=actual,state='REUSED_NOT_OUR_PROCESS' if actual!=str(created) else 'EXITED' if status==0 else 'LIVE' if status==258 else 'UNCONFIRMED')
 finally:k.CloseHandle(h)
def dist(v):return dict(n=len(v),min=min(v),median=statistics.median(v),max=max(v)) if v else None
results=[];identities=[];drift=[]
for root in sorted(D.glob('ladder-*')):
 if not root.is_dir():continue
 def get(n,default=None):return read(root/n) if (root/n).exists() else default
 cfg=get('case.json');raw=get('probe-timings.json',[]);events=[json.loads(x) for x in (root/'events.jsonl').read_text().splitlines()] if (root/'events.jsonl').exists() else [];tap=get('tap.json',[]);h=[json.loads(x) for x in (root/'heartbeat.jsonl').read_text().splitlines()];samples=get('collector-samples.json',[]);cohorts={};rows=[]
 for p in raw:
  f=p['frequency'];base=p['launchRequestedQpc'];ts=p.get('finalKernelTimes');m=p.get('nativeMarkers');row=dict(pid=p['pid'],control=p['control'],createSeconds=(p['createProcessReturnedQpc']-p['createProcessCalledQpc'])/f,popenSeconds=(p['popenReturnedQpc']-base)/f,hardFailure=p.get('hardDeadlineFailure'),warningCount=len(p.get('slowWarnings',[])),observerResult=p.get('observerResult'),finalHandle=p.get('finalHandleState'),exitCode=p.get('actualExitCode'),kernelLifetime=(int(ts[1])-int(ts[0]))/1e7 if ts and int(ts[1]) else None)
  if m:
   row.update(entrySeconds=(m['firstActivityQpc']-base)/f,initializationSeconds=(m['initializationCompleteQpc']-m['firstActivityQpc'])/f,workSeconds=(m['workEndQpc']-m['workBeginQpc'])/f,cleanupSeconds=(m['cleanupEndQpc']-m['cleanupBeginQpc'])/f,preExitSeconds=(m['exitBeginQpc']-base)/f)
  if ts and int(ts[1]):
   b=p['clockAfter'];exitq=(b['qpcBefore']+b['qpcAfter'])/2+(int(ts[1])-int(b['filetime']))*f/1e7
   row.update(exitSinceLaunchEstimate=(exitq-base)/f,observerLatencyEstimate=(p['observerReturnedQpc']-exitq)/f,teardownEstimate=(exitq-m['exitBeginQpc'])/f if m else None)
  rows.append(row);cohorts.setdefault(p['control'],[]).append(row);identities.append(dict(run=root.name,role='probe',**identity(p['pid'],p['initialKernelTimes'][0])))
 for n in ('ready.json','launch.json'):
  v=get(n)
  if v:identities.append(dict(run=root.name,role=n,**identity(v['pid'],v['created'])))
 for v in get('tracked-helpers.json',[]):identities.append(dict(run=root.name,**identity(v['pid'],v['created']),role=v['role']))
 pids={x['pid'] for x in raw};children=[x for x in tap if x['stage']=='B-WMI-callback' and x['kind']=='start' and x.get('parentPid') in pids]
 cohorts={k:{metric:dist([x[metric] for x in group if x.get(metric) is not None]) for metric in ('kernelLifetime','createSeconds','entrySeconds','initializationSeconds','workSeconds','cleanupSeconds','teardownEstimate','observerLatencyEstimate')} for k,group in cohorts.items()}
 lifecycle=[]
 for p in raw:
  lifecycle.append(dict(pid=p['pid'],**{kind:sum(x['kind']==kind and x['pid']==p['pid'] for x in events) for kind in ('start','stop')}))
 worker=get('worker-trace.json',[]);reads=[x for x in worker if x['stage']=='read.hash'];resources=get('resources.json',[])
 workerTimes=dict(totalSeconds=(worker[-1]['qpc']-worker[0]['qpc'])/1e7 if worker else None,longestRead=max(((x['readEnd']-x['start'])/1e7 for x in reads),default=None),longestHash=max(((x['end']-x['readEnd'])/1e7 for x in reads),default=None),bytes=sum(x['bytes'] for x in reads),traceEvents=len(worker))
 for p in get('source-hashes.json',[]):
  if sha(pathlib.Path(p['path']))!=p['sha256'].lower():drift.append(p)
 result=dict(run=root.name,phase=cfg['phase'],result=get('diagnostic-result.json'),cohorts=cohorts,rows=rows,childrenObserved=children,childEvidenceLimitation='WMI tree observation, no independent kernel child-launch counter; no missing-event guarantee for unrelated names',heartbeatMax=max(((b['ticks']-a['ticks'])/a['frequency'] for a,b in zip(h,h[1:])),default=None),heartbeatAgeMax=max((x['age'] for x in samples),default=None),starts=sum(x['kind']=='start' for x in events),stops=sum(x['kind']=='stop' for x in events),lifecycle=lifecycle,queue=get('queue-state.json'),tapState=get('tap-state.json'),worker=workerTimes,resourceSamples=len(resources),resourceFailure=(root/'resource-failure.txt').read_text() if (root/'resource-failure.txt').exists() else None,resourceCounterMax=max(((x['counterEnd']-x['counterStart'])/1e7 for x in resources),default=None),monitorExit=get('monitor-exit.json'),cleanup=get('cleanup-observations.json'),acceptanceSealed=False)
 results.append(result)
before=[dict(**p,unchanged=sha(pathlib.Path(p['path']))==p['sha256']) for p in read(R/'source-before.json')];frozen=[dict(**p,unchanged=sha(D/p['name'])==p['sha256']) for p in read(R/'diagnostic-source-hashes.json')]
save('ladder-summary.json',results);save('source-preservation.json',before);save('diagnostic-hash-check.json',frozen);save('identity-reconciliation.json',dict(identities=identities,unresolved=[x for x in identities if x['state'] in ('UNCONFIRMED','LIVE')],sourceDrift=drift))
diff=[]
for p in before:
 q=D/p['name']
 if q.suffix in ('.py','.ps1','.cs') and sha(q)!=p['sha256']:diff.extend(difflib.unified_diff(pathlib.Path(p['path']).read_text(encoding='utf-8-sig').splitlines(True),q.read_text(encoding='utf-8-sig').splitlines(True),fromfile='frozen/'+p['name'],tofile='diagnostic/'+p['name']))
with (R/'diagnostic-source.diff').open('x') as f:f.writelines(diff)
print(json.dumps(dict(cases=[dict(phase=x['phase'],status=x['result']['status'],probes=len(x['rows']),starts=x['starts'],stops=x['stops'],maxLifetime=max((p['kernelLifetime'] or 0 for p in x['rows']),default=0),heartbeat=x['heartbeatMax'],children=len(x['childrenObserved']),worker=x['worker']) for x in results],identities=len(identities),unresolved=[x for x in identities if x['state'] in ('UNCONFIRMED','LIVE')],sourceDrift=drift)))
