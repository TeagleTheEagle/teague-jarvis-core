"""Offline diagnostic reconciliation. Never grants monitor/baseline acceptance."""
import pathlib,json,hashlib,ctypes as c,ctypes.wintypes as w,difflib,collections,datetime,os
R=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(n,v):
 with (R/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
CODE=pathlib.Path(read(R/'plan.json')['live_code'])
k=c.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
k.GetProcessTimes.argtypes=[w.HANDLE]+[c.POINTER(w.FILETIME)]*4;k.GetProcessTimes.restype=w.BOOL
k.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];k.WaitForSingleObject.restype=w.DWORD
k.CloseHandle.argtypes=[w.HANDLE]
def check(pid,created):
 h=k.OpenProcess(0x1000|0x100000,False,int(pid))
 if not h:
  e=c.get_last_error();return dict(pid=pid,created=str(created),state='ABSENT' if e==87 else 'UNCONFIRMED',winerror=e)
 try:
  ts=[w.FILETIME() for _ in range(4)]
  if not k.GetProcessTimes(h,*[c.byref(t) for t in ts]):raise c.WinError(c.get_last_error())
  actual=str((ts[0].dwHighDateTime<<32)|ts[0].dwLowDateTime);wait=k.WaitForSingleObject(h,0)
  return dict(pid=pid,created=str(created),actualCreated=actual,wait=wait,state='REUSED_NOT_OUR_PROCESS' if actual!=str(created) else 'EXITED' if wait==0 else 'LIVE' if wait==258 else 'UNCONFIRMED')
 finally:k.CloseHandle(h)
results=[];identities=[];drift=[];timeouts=[];totals=collections.Counter();containment=[]
for d in sorted(CODE.iterdir()):
 if not d.is_dir() or not (d/'case.json').exists():continue
 a=read(d/'probe-analysis.json');raw=read(d/'probe-timings.json');events=[json.loads(x) for x in (d/'events.jsonl').read_text().splitlines()]
 tap=read(d/'tap.json');e=read(d/'event-analysis.json');monitor=read(d/'monitor-result.json');phases=read(d/'phases.json');identity=read(d/'ready.json')
 identities.append(dict(run=d.name,role='monitor',**check(identity['pid'],identity['created'])))
 for p in raw:identities.append(dict(run=d.name,role='probe',**check(p['pid'],p['finalKernelTimes'][0])))
 for p in phases:
  if 'worker_identity' in p:identities.append(dict(run=d.name,role='workload',**check(p['worker_identity']['pid'],p['worker_identity']['created'])))
 if read(d/'monitor-exit.json')['exit_code'] or read(d/'resource-exit.json')['exit'] or any(p.get('worker_exit',0)!=0 for p in phases):raise RuntimeError('Cleanup exit error')
 for p in read(d/'source-hashes.json'):
  if sha(pathlib.Path(p['path']))!=p['sha256'].lower():drift.append(p)
 summary={key:value for key,value in a.items() if key!='measurements'}
 summary.update(collector=read(d/'collector-finished.json')['status'],durableFlush=monitor['journalDurableFlush'],maxQueueDepth=e['maxQueueDepth'],lockWait=e['longestLockWait']['seconds'],lockHold=e['longestLockHold']['seconds'],forcedCleanup=(d/'workload-forced-cleanup.json').exists(),originalAnalyzer=read(d/'analysis.json')['monitorHealth'])
 summary['callbacks']={kind:sum(x['kind']==kind and x['stage']=='A-callback' for x in tap) for kind in ('start','stop')}
 summary['enqueued']={kind:sum(x['kind']==kind and x['stage']=='A-enqueue' for x in tap) for kind in ('start','stop')}
 if (d/f"workload-{a['mode']}.json").exists():
  work=read(d/f"workload-{a['mode']}.json");summary['workload']=dict(seconds=work['seconds'],bytes=work['bytes'],cpuIterations=work['cpu_iterations'],maxReadSeconds=max((x[1] for x in work['reads']),default=None))
 for p in raw:
  if not p['timedOut']:continue
  f=p['frequency'];origin=p['launchRequestedQpc'];b=p['clockAfter'];mid=(b['qpcBefore']+b['qpcAfter'])/2
  def relative(q):return (q-origin)/f
  def mapped(ft):return relative(mid+(int(ft)-int(b['filetime']))*f/1e7)
  keys=('createProcessCalledQpc','createProcessReturnedQpc','popenReturnedQpc','identityCapturedQpc','observerWaitEnteredQpc','mainWaitEnteredQpc','timeoutCaughtQpc','immediateHandleCheckQpc','observerReturnedQpc','reconciledQpc')
  trace=dict(run=d.name,pid=p['pid'],created=p['finalKernelTimes'][0],relativeToLaunchSeconds={key:relative(p[key]) for key in keys},kernelCreationEstimate=mapped(p['finalKernelTimes'][0]),kernelExitEstimate=mapped(p['finalKernelTimes'][1]),mainWaitToObserverSeconds=(p['observerReturnedQpc']-p['mainWaitEnteredQpc'])/f,immediateHandleState=p['immediateHandleState'],actualExitCode=p['actualExitCode'],metrics=next(x for x in a['measurements'] if x['pid']==p['pid']),events=[x for x in events if x['pid']==p['pid']],tap=[x for x in tap if x['pid']==p['pid']],missing=['first instruction','work begin','work end','exit initiation','exact kernel handle-signal instant'])
  timeouts.append(trace)
 for base,dirs,files in os.walk(d):
  for name in dirs+files:
   p=pathlib.Path(base)/name
   if p.is_symlink() or p.is_junction() or not p.resolve().is_relative_to(d.resolve()) or p.drive.upper()!='D:':raise RuntimeError('Live evidence containment failure')
 containment.append(dict(run=d.name,allArtifactsD=True,reparseEscape=False))
 results.append(summary)
 for key in ('count','timeoutCount','starts','stops','externalCollisions','internalCollisions'):totals[key]+=a[key]
before=[];diff=[]
for row in read(R/'source-before.json'):
 p=pathlib.Path(row['path']);st=p.stat();before.append(dict(path=str(p),unchanged=sha(p)==row['sha256'] and st.st_size==row['size'] and st.st_mtime_ns==row['mtime_ns']))
 q=R/'candidate'/p.name
 if p.suffix in ('.py','.ps1','.cs') and q.exists():diff.extend(difflib.unified_diff(p.read_text(encoding='utf-8-sig').splitlines(True),q.read_text(encoding='utf-8-sig').splitlines(True),fromfile='previous/'+p.name,tofile='diagnostic/'+p.name))
if not all(x['unchanged'] for x in before):raise RuntimeError('Previous diagnostic source mutated')
final=[]
for row in read(R/'candidate-hashes.json'):
 n=row['name'];actual=sha(CODE/n);ok=actual==row['sha256']==sha(R/'candidate'/n);final.append(dict(name=n,sha256=actual,unchanged=ok))
 if not ok:drift.append(dict(name=n))
save('source-preservation.json',before);save('final-source-hashes.json',final)
with (R/'diagnostic-source.diff').open('x',encoding='utf-8') as f:f.writelines(diff)
save('live-containment.json',containment)
unresolved=[x for x in identities if x['state'] in ('LIVE','UNCONFIRMED')]
save('identity-reconciliation.json',dict(identities=identities,unresolved=unresolved,sourceDrift=drift))
save('timeout-timelines.json',timeouts)
old=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\ab1566cc23dd43cab43afef00cba5940\code\stress-hash-317f8edced6f46e6935d2328f62d56b9')
oldfiles=('retained-handle-verification.json','collector-failure.json','events.jsonl','tap.json','analysis.json','monitor-exit.json')
oldhashes=[dict(path=str(old/n),sha256=sha(old/n),size=(old/n).stat().st_size) for n in oldfiles]
oldprobe=next(x for x in read(old/'retained-handle-verification.json') if x['pid']==12080)
save('historical-reconstruction.json',dict(pid=12080,handleRecord=oldprobe,kernelLifetimeSeconds=(int(oldprobe['times'][1])-int(oldprobe['times'][0]))/1e7,events=[json.loads(x) for x in (old/'events.jsonl').read_text().splitlines() if json.loads(x)['pid']==12080],tap=[x for x in read(old/'tap.json') if x['pid']==12080],failure=read(old/'collector-failure.json'),sourceArtifacts=oldhashes,missing=['T0 launch requested','T1 CreateProcess returned','first instruction','work start/end','exit initiation','exact handle-signal instant','per-process later handle-observation timestamp','actual exit code'],classification='UNKNOWN within process lifetime; historical cause unconfirmed'))
save('diagnostic-summary.json',dict(status='PENDING_REVIEW',acceptance=False,runs=results,totals=dict(totals),sourceDrift=drift,unresolvedIdentities=unresolved,protectedAccess=False,productionChanged=False,baselineEligibility='NOT AUTHORIZED / NOT JUSTIFIED'))
print(json.dumps(dict(runs=len(results),totals=dict(totals),identityChecks=len(identities),unresolved=unresolved,sourceDrift=drift)))
