"""Read-only reconstruction after failed finalization. Does not repair evidence."""
import pathlib,json,hashlib,statistics,collections,ctypes as c,ctypes.wintypes as w,difflib,ast
R=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(n,x):
 with (R/n).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
CODE=pathlib.Path(read(R/'plan.json')['live_code'])
k=c.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
k.GetProcessTimes.argtypes=[w.HANDLE]+[c.POINTER(w.FILETIME)]*4;k.GetProcessTimes.restype=w.BOOL
k.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];k.WaitForSingleObject.restype=w.DWORD;k.CloseHandle.argtypes=[w.HANDLE]
def check(pid,created):
 h=k.OpenProcess(0x1000|0x100000,False,int(pid))
 if not h:
  e=c.get_last_error();return dict(pid=pid,created=str(created),state='ABSENT' if e==87 else 'UNCONFIRMED',winerror=e)
 try:
  t=[w.FILETIME() for _ in range(4)]
  if not k.GetProcessTimes(h,*[c.byref(x) for x in t]):raise c.WinError(c.get_last_error())
  actual=str((t[0].dwHighDateTime<<32)|t[0].dwLowDateTime);state=k.WaitForSingleObject(h,0)
  return dict(pid=pid,created=str(created),actualCreated=actual,state='REUSED_NOT_OUR_PROCESS' if actual!=str(created) else 'EXITED' if state==0 else 'LIVE' if state==258 else 'UNCONFIRMED')
 finally:k.CloseHandle(h)
def dist(xs):
 if not xs:return None
 xs=sorted(xs);n=len(xs)
 def pct(q):
  pos=(n-1)*q;i=int(pos);return xs[i]+(xs[min(i+1,n-1)]-xs[i])*(pos-i)
 return dict(n=n,min=xs[0],median=statistics.median(xs),p95=pct(.95) if n>=20 else None,p99=pct(.99) if n>=100 else None,max=xs[-1])
rows=[];runs=[];ids=[];drift=[];failure=[]
for d in sorted(CODE.iterdir()):
 if not d.is_dir() or not (d/'case.json').exists():continue
 case=read(d/'case.json');raw=read(d/'probe-timings.json');events=[json.loads(x) for x in (d/'events.jsonl').read_text().splitlines()];counts=collections.Counter((x['pid'],x['kind']) for x in events)
 hb=[json.loads(x) for x in (d/'heartbeat.jsonl').read_text().splitlines()];samples=read(d/'collector-samples.json');f=hb[0]['frequency'];q=read(d/'queue-state.json');entries=read(d/'queue-entries.json');fine=read(d/'fine-trace.json');identity=read(d/'ready.json')
 ids.append(dict(run=d.name,role='monitor',**check(identity['pid'],identity['created'])))
 for p in read(d/'phases.json'):
  if 'worker_identity' in p:ids.append(dict(run=d.name,role='workload',**check(p['worker_identity']['pid'],p['worker_identity']['created'])))
 missing=[]
 for p in raw:
  t=p['finalKernelTimes'];b=p['clockAfter'];mid=(b['qpcBefore']+b['qpcAfter'])/2
  def mapped(ft):return mid+(int(ft)-int(b['filetime']))*f/1e7
  x=dict(run=d.name,mode=case['mode'],control=p['control'],pid=p['pid'],created=t[0],exit=t[1],kernelLifetime=(int(t[1])-int(t[0]))/1e7,createProcessSeconds=(p['createProcessReturnedQpc']-p['createProcessCalledQpc'])/f,mainWaitSeconds=(p.get('mainWaitReturnedQpc',p.get('timeoutCaughtQpc'))-p['mainWaitEnteredQpc'])/f,observerLatencyEstimate=(p['observerReturnedQpc']-mapped(t[1]))/f,timedOut=p['timedOut'],actualExitCode=p['actualExitCode'],kernelCPU=int(t[2])/1e7,userCPU=int(t[3])/1e7)
  n=p.get('nativeMarkers')
  if n:x.update(creationToEntryEstimate=(n['firstActivityQpc']-mapped(t[0]))/f,entryAfterCreateReturn=(n['firstActivityQpc']-p['createProcessReturnedQpc'])/f,markerSetup=(n['workBeginQpc']-n['firstActivityQpc'])/f,workSeconds=(n['workEndQpc']-n['workBeginQpc'])/f,exitTailEstimate=(mapped(t[1])-n['exitBeginQpc'])/f)
  rows.append(x);ids.append(dict(run=d.name,role='probe',**check(p['pid'],t[0])))
  assert p['finalHandleState']==p['observerResult']==p['actualExitCode']==0
  if counts[p['pid'],'start']!=1 or counts[p['pid'],'stop']!=1:missing.append(dict(pid=p['pid'],control=p['control'],starts=counts[p['pid'],'start'],stops=counts[p['pid'],'stop']))
 fs=[];pending={}
 for item in fine:
  stage=item['stage'];thread=item['nativeThread']
  for name in ('event.exists','event.stat','event.File.AppendAllText','journal.size','journal.write','journal.flush','finish.query'):
   if stage==name+'.begin':pending[thread,name]=item['qpc']
   elif stage==name+'.end' and (thread,name) in pending:fs.append(dict(stage=name,seconds=(item['qpc']-pending.pop((thread,name)))/f))
 run=dict(run=d.name,mode=case['mode'],count=len(raw),timeouts=sum(x['timedOut'] for x in raw),starts=sum(x['kind']=='start' for x in events),stops=sum(x['kind']=='stop' for x in events),missing=missing,heartbeatInterval=max((b['ticks']-a['ticks'])/f for a,b in zip(hb,hb[1:])),heartbeatAge=max(x['age'] for x in samples),maxFilesystem=max(fs,key=lambda x:x['seconds']) if fs else None,queue=q,externalCollisions=len(entries)-len(set(x['eventId'] for x in entries)),internalCollisions=len(entries)-len(set(x['queueSequence'] for x in entries)),monitorExit=read(d/'monitor-exit.json')['exit_code'],resourceExit=read(d/'resource-exit.json')['exit'],durableResultPresent=(d/'monitor-result.json').exists(),forcedCleanup=(d/'workload-forced-cleanup.json').exists())
 if (d/'monitor-failure.json').exists():
  trace=read(d/'loop-trace.json');pipeline=read(d/'pipeline.json');lastDrain=[x for x in trace if x['stage']=='drain.end'][-1]
  residue=[x for x in entries if not x['removed']]
  failure.append(dict(run=d.name,failure=read(d/'monitor-failure.json'),queue=q,residue=residue,lastDrain=lastDrain,finalEnumeration=[x for x in trace if x['stage'].startswith('final.enumeration')],pendingEvidence=[x for x in pipeline if x['stage'] in ('preunsubscribe.pending','teardown.discard')],allExpectedHandlesExited=True,notACollisionCorrection=True))
 for original in read(d/'source-hashes.json'):
  if sha(pathlib.Path(original['path']))!=original['sha256'].lower():drift.append(original)
 runs.append(run)
groups=[]
for mode in ('idle','disk','sustained','Dhash'):
 for control in ('A_D','A_C','B_D','B_C','D_D','D_C','C_D'):
  g=[x for x in rows if x['mode']==mode and x['control']==control]
  out=dict(mode=mode,control=control,count=len(g),timeouts=sum(x['timedOut'] for x in g),over1=sum(x['kernelLifetime']>1 for x in g),over3=sum(x['kernelLifetime']>3 for x in g),over5=sum(x['kernelLifetime']>5 for x in g))
  for key in ('kernelLifetime','createProcessSeconds','mainWaitSeconds','observerLatencyEstimate','creationToEntryEstimate','entryAfterCreateReturn','markerSetup','workSeconds','exitTailEstimate'):out[key]=dist([x[key] for x in g if key in x])
  groups.append(out)
previous=[];diff=[]
for x in read(R/'source-before.json'):
 p=pathlib.Path(x['path']);st=p.stat();ok=sha(p)==x['sha256'] and st.st_size==x['size'] and st.st_mtime_ns==x['mtime_ns'];previous.append(dict(path=str(p),unchanged=ok))
 if not ok:raise RuntimeError('Previous source changed')
 if p.suffix in ('.py','.ps1','.cs'):diff.extend(difflib.unified_diff(p.read_text().splitlines(True),(R/'candidate'/p.name).read_text().splitlines(True),fromfile='previous/'+p.name,tofile='diagnostic/'+p.name))
with (R/'diagnostic-source.diff').open('x') as f:f.writelines(diff)
final=[]
for x in read(R/'candidate-hashes.json'):
 ok=sha(CODE/x['name'])==sha(R/'candidate'/x['name'])==x['sha256'];final.append(dict(**x,unchanged=ok))
 if not ok:drift.append(x)
for x in read(R/'helper-images.json'):
 if sha(pathlib.Path(x['cPath']))!=sha(pathlib.Path(x['dPath'])) or sha(pathlib.Path(x['dPath']))!=x['sha256']:raise RuntimeError('Helper location hash mismatch')
save('source-preservation.json',previous);save('final-source-hashes.json',final)
save('identity-reconciliation.json',dict(identities=ids,unresolved=[x for x in ids if x['state'] in ('LIVE','UNCONFIRMED')],sourceDrift=drift))
save('finalization-failure-timeline.json',failure)
save('all-control-measurements.json',rows)
save('slow-controls.json',[x for x in rows if x['kernelLifetime']>.5 or x['createProcessSeconds']>.5])
save('control-summary.json',dict(status='BLOCKED',acceptance=False,runs=runs,groups=groups,totalProbes=len(rows),timeouts=sum(x['timedOut'] for x in rows),starts=sum(x['starts'] for x in runs),stops=sum(x['stops'] for x in runs),maxHeartbeat=max(x['heartbeatInterval'] for x in runs),maxAge=max(x['heartbeatAge'] for x in runs)))
prior=R.parent/'stage6-probe-diagnosis-20260920';receipt=read(prior/'archive-verification.json')
assert sha(prior/'evidence.zip')==receipt['zipSHA256'] and sha(prior/'archive-manifest.json')==receipt['manifestSHA256']
save('prior-archive-preservation.json',dict(unchanged=True,receipt=receipt))
syntax=[]
for p in sorted(list(CODE.glob('*.py'))+list(R.glob('*.py'))):ast.parse(p.read_text(encoding='utf-8-sig'));syntax.append(str(p))
save('python-syntax.json',dict(status='PASS',files=syntax))
print(json.dumps(dict(runs=runs,probes=len(rows),unresolved=[x for x in ids if x['state'] in ('LIVE','UNCONFIRMED')],sourceDrift=drift,slow=[x for x in rows if x['kernelLifetime']>.5]),indent=2))
