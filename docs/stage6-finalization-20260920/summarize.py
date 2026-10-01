"""Read only completed sacrificial runs; never admits failed evidence."""
import pathlib,json,hashlib,statistics,collections,difflib,ctypes as c,ctypes.wintypes as w
R=pathlib.Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):
 with (R/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
CODE=pathlib.Path(read(R/'plan.json')['live_code'])
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
def distribution(v):
 if not v:return None
 v=sorted(v);n=len(v)
 def pct(p):
  z=(n-1)*p;i=int(z);return v[i]+(v[min(i+1,n-1)]-v[i])*(z-i)
 return dict(n=n,median=statistics.median(v),p95=pct(.95) if n>=20 else None,p99=pct(.99) if n>=100 else None,max=max(v))
results=[];identities=[];drift=[];latencies=[]
for d in sorted(CODE.iterdir()):
 if not d.is_dir() or not (d/'case.json').exists():continue
 cfg=read(d/'case.json');rows=read(d/'probe-timings.json') if (d/'probe-timings.json').exists() else []
 tap=read(d/'tap.json') if (d/'tap.json').exists() else []
 events=[json.loads(x) for x in (d/'events.jsonl').read_text().splitlines()] if (d/'events.jsonl').exists() else []
 h=[json.loads(x) for x in (d/'heartbeat.jsonl').read_text().splitlines()] if (d/'heartbeat.jsonl').exists() else []
 local=[]
 for p in rows:
  identities.append(dict(run=d.name,role='probe',**identity(p['pid'],p['finalKernelTimes'][0])))
  b=p['clockAfter'];freq=p['frequency'];exitq=(b['qpcBefore']+b['qpcAfter'])/2+(int(p['finalKernelTimes'][1])-int(b['filetime']))*freq/1e7
  stops=[x for x in tap if x['pid']==p['pid'] and x['kind']=='stop' and x['stage']=='A-callback']
  if len(stops)==1:
   v=(stops[0]['qpc']-exitq)/freq;local.append(v);latencies.append(dict(run=d.name,pid=p['pid'],callbackSeconds=v))
 for name in ('ready.json','launch.json'):
  if (d/name).exists():
   p=read(d/name);identities.append(dict(run=d.name,role=name,**identity(p['pid'],p['created'])))
 if (d/'phases.json').exists():
  for p in read(d/'phases.json'):
   if 'worker_identity' in p:identities.append(dict(run=d.name,role='workload',**identity(**p['worker_identity'])))
 for p in read(d/'source-hashes.json'):
  if sha(pathlib.Path(p['path']))!=p['sha256'].lower():drift.append(p)
 state=read(d/'finalization-state.json') if (d/'finalization-state.json').exists() else None
 results.append(dict(run=d.name,mode=cfg['mode'],cluster=cfg.get('cluster',1),status='PASS' if (d/'acceptance.json').exists() else 'FAIL',probes=len(rows),confirmedExits=sum(p.get('finalHandleState')==0 for p in rows),timeouts=sum(p.get('timedOut',False) for p in rows),starts=sum(e['kind']=='start' for e in events),stops=sum(e['kind']=='stop' for e in events),callbackLatency=distribution(local),heartbeatMax=max(((b['ticks']-a['ticks'])/a['frequency'] for a,b in zip(h,h[1:])),default=None),finalization=state,failures=[p.name for p in d.glob('*failure.json')],queue=read(d/'queue-state.json') if (d/'queue-state.json').exists() else None,analysis=read(d/'probe-analysis.json') if (d/'probe-analysis.json').exists() else None))
before=[];diff=[]
for row in read(R/'source-before.json'):
 p=pathlib.Path(row['path']);st=p.stat();before.append(dict(path=str(p),unchanged=sha(p)==row['sha256'].lower() and st.st_size==row['size'] and st.st_mtime_ns==row['mtime_ns']))
 q=R/'candidate'/p.name
 if p.suffix in ('.cs','.py','.ps1') and q.exists():diff.extend(difflib.unified_diff(p.read_text(encoding='utf-8-sig').splitlines(True),q.read_text(encoding='utf-8-sig').splitlines(True),fromfile='before/'+p.name,tofile='candidate/'+p.name))
final=[]
for row in read(R/'candidate-hashes-v2.json'):
 name=row['name'];actual=sha(CODE/name);ok=actual==row['sha256'].lower()==sha(R/'candidate'/name);final.append(dict(name=name,sha256=actual,unchanged=ok))
 if not ok:drift.append(dict(name=name))
save('source-preservation.json',before);save('final-source-hashes.json',final)
with (R/'source.diff').open('x',encoding='utf-8') as f:f.writelines(diff)
save('identity-reconciliation.json',dict(identities=identities,unresolved=[x for x in identities if x['state'] in ('LIVE','UNCONFIRMED')],sourceDrift=drift))
save('fresh-latencies.json',latencies);save('workload-summary.json',results)
print(json.dumps(dict(runs=[{k:r[k] for k in ('run','mode','status','probes','starts','stops','timeouts','heartbeatMax')} for r in results],identities=len(identities),drift=drift)))
