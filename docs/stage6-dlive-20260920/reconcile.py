"""Offline evidence reconciliation only, after the campaign stopped."""
import pathlib,json,hashlib,collections,ctypes as c,ctypes.wintypes as w,datetime,difflib,os
R=pathlib.Path(__file__).resolve().parent;CODE=pathlib.Path(json.loads((R/'workspace-plan.json').read_text())['live_code'])
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
k=c.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
k.GetProcessTimes.argtypes=[w.HANDLE]+[c.POINTER(w.FILETIME)]*4;k.GetProcessTimes.restype=w.BOOL
k.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];k.WaitForSingleObject.restype=w.DWORD;k.CloseHandle.argtypes=[w.HANDLE]
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
results=[];identities=[];drift=[];totals=collections.Counter()
for d in sorted(CODE.glob('stress-*')):
 if not d.is_dir():continue
 a=read(d/'analysis.json');e=read(d/'event-analysis.json');h=read(d/'retained-handle-verification.json');ready=read(d/'ready.json');phases=read(d/'phases.json');taps=read(d/'tap.json')
 identities.append(dict(run=d.name,role='monitor',**check(ready['pid'],ready['created'])))
 for phase in phases:
  if 'worker_identity' in phase:
   p=phase['worker_identity'];identities.append(dict(run=d.name,role='workload',**check(p['pid'],p['created'])))
 for p in h:identities.append(dict(run=d.name,role='probe',**check(p['pid'],p['times'][0])))
 old={pathlib.Path(x['path']).name:x['sha256'].lower() for x in read(d/'source-hashes.json')}
 for n,digest in old.items():
  if sha(CODE/n)!=digest:drift.append(dict(run=d.name,file=n))
 if read(d/'monitor-exit.json')['exit_code'] or read(d/'resource-exit.json')['exit'] or any(p.get('worker_exit',0)!=0 for p in phases):raise RuntimeError('Cleanup exit failure')
 if any(int(p['times'][1])<=int(p['times'][0]) for p in h):raise RuntimeError('Missing probe kernel exit')
 groups={key:sum(t['kind']==kind and t['stage']==stage for t in taps) for key,kind,stage in [('startCallback','start','A-callback'),('stopCallback','stop','A-callback'),('startEnqueued','start','A-enqueue'),('stopEnqueued','stop','A-enqueue')]}
 liveNames=('event.exists','event.stat','event.File.AppendAllText','journal.size','journal.write','journal.flush','finish.query')
 fs=max((a['stageMaxima'][n] for n in liveNames),key=lambda v:v['seconds'])
 hb=max((a['stageMaxima'][n] for n in ('journal.size','journal.write','journal.flush','record')),key=lambda v:v['seconds'])
 result=dict(run=d.name,mode=a['config']['mode'],status='PASS' if (d/'acceptance.json').exists() else 'FAIL',expectedPairs=len(h),starts=e['starts'],stops=e['stops'],**groups,externalCollisions=a['externalCollisions'],internalCollisions=a['internalCollisions'],heartbeatInterval=a['maxHeartbeatInterval'],heartbeatAge=a['maxHeartbeatAge'],maxDrain=e['maxDrain']['seconds'],longestLiveFileCall=fs,longestHeartbeatOperation=hb,eventWrite=e['substageMaxima']['event.File.AppendAllText']['seconds'],queueDepth=e['maxQueueDepth'],lockWait=e['longestLockWait']['seconds'],lockHold=e['longestLockHold']['seconds'],probeTimeout=(d/'collector-failure.json').exists(),durableFlush=read(d/'monitor-result.json')['journalDurableFlush'],acceptanceFinalized=(d/'EVIDENCE-DURABLY-FINALIZED.json').exists(),forcedCleanup=(d/'workload-forced-cleanup.json').exists())
 results.append(result)
 for key in ('starts','stops','externalCollisions','internalCollisions'):totals[key]+=result[key]
 # Static and materialized evidence containment; reject any reparse artifacts.
 for base,dirs,files in os.walk(d):
  for name in dirs+files:
   p=pathlib.Path(base)/name
   if p.is_symlink() or p.is_junction() or not p.resolve().is_relative_to(d.resolve()):raise RuntimeError('Run artifact escape')
prior=[]
for row in read(R/'pre-change-hashes.json'):
 p=pathlib.Path(row['path']);st=p.stat();prior.append(dict(path=str(p),unchanged=sha(p)==row['sha256'] and st.st_size==row['size'] and st.st_mtime_ns==row['mtime_ns']))
if not all(v['unchanged'] for v in prior):raise RuntimeError('Prior source changed')
save(R/'source-preservation.json',prior)
diffs=[]
for p in sorted((R/'before').iterdir()):
 if p.suffix in ('.py','.cs','.ps1'):diffs.extend(difflib.unified_diff(p.read_text(encoding='utf-8-sig').splitlines(True),(R/'candidate'/p.name).read_text(encoding='utf-8-sig').splitlines(True),fromfile='before/'+p.name,tofile='candidate/'+p.name))
with (R/'final-source.diff').open('x',encoding='utf-8') as f:f.writelines(diffs)
save(R/'final-source-hashes.json',[dict(name=p.name,sha256=sha(p),d_copy_matches=sha(p)==sha(CODE/p.name)) for p in sorted((R/'candidate').iterdir()) if p.is_file()])
unresolved=[v for v in identities if v['state'] in ('LIVE','UNCONFIRMED')]
save(R/'identity-reconciliation.json',dict(identities=identities,unresolved=unresolved,sourceDrift=drift,retainedHandlesConfirmAllProbeExits=True))
save(R/'campaign-summary.json',dict(status='MONITOR_STILL_DEFECTIVE',runs=results,totals=totals,focused=read(CODE/'focused-result.json'),sourceDrift=drift,unresolvedIdentities=unresolved,stoppedAfter='D7 C hashing / D9 recurring probe timeout',remainingWorkloads='NOT RUN',threeRepetitions='NOT RUN',dry1='NOT RUN',dry2='NOT RUN',protectedAccess=False,productionChanged=False,eligibility='NOT JUSTIFIED'))
print(json.dumps(dict(status='MONITOR_STILL_DEFECTIVE',runs=results,totals=totals,identityChecks=len(identities),unresolved=unresolved,sourceDrift=drift),indent=2))
