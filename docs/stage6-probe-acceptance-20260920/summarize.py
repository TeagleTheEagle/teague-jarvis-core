"""Offline final reconciliation; run only after live collection ends."""
import pathlib,json,hashlib,collections,difflib,ctypes as c,ctypes.wintypes as w
R=pathlib.Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):
 with (R/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
plan=read(R/'plan.json');CODE=pathlib.Path(plan['live_code'])
k=c.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
k.GetProcessTimes.argtypes=[w.HANDLE]+[c.POINTER(w.FILETIME)]*4;k.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];k.CloseHandle.argtypes=[w.HANDLE]
def identity(pid,created):
 h=k.OpenProcess(0x1000|0x100000,False,int(pid))
 if not h:
  e=c.get_last_error();return dict(pid=pid,created=str(created),state='ABSENT' if e==87 else 'UNCONFIRMED',winerror=e)
 try:
  ts=[w.FILETIME() for _ in range(4)]
  if not k.GetProcessTimes(h,*[c.byref(t) for t in ts]):raise c.WinError(c.get_last_error())
  actual=str((ts[0].dwHighDateTime<<32)|ts[0].dwLowDateTime);wait=k.WaitForSingleObject(h,0)
  return dict(pid=pid,created=str(created),actual=actual,state='REUSED_NOT_OUR_PROCESS' if actual!=str(created) else 'EXITED' if wait==0 else 'LIVE' if wait==258 else 'UNCONFIRMED')
 finally:k.CloseHandle(h)
results=[];identities=[];drift=[]
for d in sorted(CODE.iterdir()):
 if not d.is_dir() or not (d/'case.json').exists():continue
 def opt(n,default=None):return read(d/n) if (d/n).exists() else default
 cfg=read(d/'case.json');rows=opt('probe-timings.json',[]);a=opt('analysis.json',{});pa=opt('probe-analysis.json',{});ea=opt('event-analysis.json',{})
 events=[json.loads(x) for x in (d/'events.jsonl').read_text().splitlines()] if (d/'events.jsonl').exists() else []
 h=[json.loads(x) for x in (d/'heartbeat.jsonl').read_text().splitlines()] if (d/'heartbeat.jsonl').exists() else []
 for p in rows:
  ts=p.get('finalKernelTimes',p.get('initialKernelTimes'))
  if ts:identities.append(dict(run=d.name,role='probe',**identity(p['pid'],ts[0])))
  else:identities.append(dict(run=d.name,role='probe',pid=p.get('pid'),state='UNCONFIRMED'))
 for name in ('ready.json','launch.json'):
  if (d/name).exists():
   p=read(d/name);identities.append(dict(run=d.name,role=name,**identity(p['pid'],p['created'])))
 for p in opt('phases.json',[]):
  if 'worker_identity' in p:identities.append(dict(run=d.name,role='workload',**identity(**p['worker_identity'])))
 for p in read(d/'source-hashes.json'):
  if sha(pathlib.Path(p['path']))!=p['sha256'].lower():drift.append(p)
 fs={n:v for n,v in a.get('stageMaxima',{}).items() if any(s in n.lower() for s in ('file.','file','journal','exists','stat','control','flush'))}
 results.append(dict(run=d.name,mode=cfg['mode'],duration=cfg['duration'],status='PASS' if (d/'acceptance.json').exists() else 'FAIL',probes=len(rows),confirmedExits=sum(p.get('finalHandleState')==0 for p in rows),slowWarnings=sum(bool(p.get('slowWarnings')) for p in rows),hardFailures=sum(p.get('hardDeadlineFailure',False) for p in rows),starts=sum(e['kind']=='start' for e in events),stops=sum(e['kind']=='stop' for e in events),maxProbeLifetime=pa.get('lifetime',{}).get('max'),maxConfirmedElapsed=max((p.get('policy',{}).get('confirmedElapsed',0) for p in rows),default=None),heartbeatMax=max(((b['ticks']-a['ticks'])/a['frequency'] for a,b in zip(h,h[1:])),default=None),heartbeatAge=a.get('maxHeartbeatAge'),longestDrain=ea.get('maxDrain'),longestFilesystem=max(fs.values(),key=lambda x:x['seconds']) if fs else None,externalCollisions=a.get('externalCollisions'),internalCollisions=a.get('internalCollisions'),finalization=opt('finalization-state.json'),durable=opt('EVIDENCE-DURABLY-FINALIZED.json'),failures=[p.name for p in d.glob('*failure.json')],queue=opt('queue-state.json'),analysis=pa))
before=[];diff=[];changes=[]
old={row['name']:row for row in read(R/'source-before.json')}
for row in old.values():
 p=pathlib.Path(row['path']);before.append(dict(path=str(p),unchanged=sha(p)==row['sha256'].lower() and p.stat().st_size==row['size']))
final=[]
for row in read(R/'candidate-hashes.json'):
 name=row['name'];actual=sha(CODE/name);ok=actual==row['sha256'].lower()==sha(R/'candidate'/name);final.append(dict(name=name,sha256=actual,unchanged=ok))
 if not ok:drift.append(dict(name=name))
 prior=old.get(name)
 if not prior or prior['sha256'].lower()!=actual:
  changes.append(dict(name=name,beforeSHA256=prior['sha256'] if prior else None,afterSHA256=actual))
  p=R/'candidate'/name
  if p.suffix in ('.py','.ps1','.cs'):
   previous=pathlib.Path(prior['path']).read_text(encoding='utf-8-sig').splitlines(True) if prior else []
   diff.extend(difflib.unified_diff(previous,p.read_text(encoding='utf-8-sig').splitlines(True),fromfile='before/'+name,tofile='candidate/'+name))
save('source-preservation.json',before);save('final-source-hashes.json',final);save('changes.json',changes)
with (R/'source.diff').open('x',encoding='utf-8') as f:f.writelines(diff)
save('identity-reconciliation.json',dict(identities=identities,unresolved=[x for x in identities if x['state'] in ('LIVE','UNCONFIRMED')],sourceDrift=drift))
save('workload-summary.json',results)
print(json.dumps(dict(runs=[{k:r[k] for k in ('run','status','probes','starts','stops','slowWarnings','hardFailures','heartbeatMax')} for r in results],identities=len(identities),drift=drift)))
