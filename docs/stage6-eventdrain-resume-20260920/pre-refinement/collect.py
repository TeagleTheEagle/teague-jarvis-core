"""Bounded diagnostic collection; health failures remain latched, never accepted."""
import ctypes as c,ctypes.wintypes as w,datetime,json,pathlib,subprocess,sys,time,traceback,hashlib
from journal import Reader,PublisherWatch,ticks
R=pathlib.Path(__file__).resolve().parent;run=sys.argv[1];out=R/run
config=json.loads((out/'case.json').read_text());mode=config['mode'];duration=config['duration']
assert run in ('smoke','a1','a2','a3','b','c','d','e','f','minimal') and duration in (5,150)
def save(n,v):
 with (out/n).open('w',encoding='utf-8') as f:json.dump(v,f,indent=2)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
deadline=time.monotonic()+20
while not (out/'ready.json').exists():
 if (out/'monitor-failure.json').exists():raise RuntimeError('Monitor startup failed; no probes started')
 if time.monotonic()>deadline:raise RuntimeError('Monitor readiness failed')
 time.sleep(.1)
identity=json.loads((out/'ready.json').read_text(encoding='utf-8-sig'));watch=PublisherWatch(identity)
journal=out/'heartbeat.jsonl' if config['journalVolume']=='C' else pathlib.Path('D:/JARVIS-STAGE6-HEARTBEAT-STALL-20260920')/run/'heartbeat.jsonl'
reader=Reader(journal,identity,liveness=watch.check);k=watch.k;k.GetExitCodeProcess.argtypes=[w.HANDLE,c.POINTER(w.DWORD)]
def times(p):
 v=[w.FILETIME() for _ in range(4)]
 if not k.GetProcessTimes(int(p._handle),*[c.byref(x) for x in v]):raise c.WinError(c.get_last_error())
 return [str((x.dwHighDateTime<<32)|x.dwLowDateTime) for x in v]
pwsh=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
resource=None
if config['telemetry']=='full':resource=subprocess.Popen([pwsh,'-NoProfile','-File',str(R/'resources.ps1'),'-Run',run],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,creationflags=0x08000000)
samples=[];probes=[];handles=[];child=None;status='DIAGNOSTIC_COLLECTION_COMPLETED';error=None;phase={'mode':mode,'start_qpc':ticks(),'start_utc':utc(),'duration_requested':duration}
try:
 if mode!='idle':
  child=subprocess.Popen([sys._base_executable,'-B',str(R/'workload.py'),run,mode,str(duration)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,creationflags=0x08000000)
  phase['worker_identity']={'pid':child.pid,'created':times(child)[0]}
 save('phases.json',[phase]);began=time.monotonic();last=-1
 while (child is not None and child.poll() is None) or (mode=='idle' and time.monotonic()-began<duration):
  if (out/'monitor-failure.json').exists():raise RuntimeError('Monitor failure')
  before=ticks()
  try:v=reader.poll()
  except BaseException:
   save('rejected-poll.json',dict(before=before,after=ticks(),last=reader.last,traceback=traceback.format_exc()));raise
  samples.append(dict(v,qpc=before,pollEnd=ticks(),phase=mode))
  if time.monotonic()-began-last>=1:
   t=ticks();p=subprocess.Popen([str(R/'J6Probe.exe')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=0x08000000);handles.append(p)
   created=times(p)[0];code=p.wait(timeout=5);ts=times(p)
   if any(x['pid']==p.pid for x in probes) or created!=ts[0] or k.WaitForSingleObject(int(p._handle),0)!=0:raise RuntimeError('Probe identity/exit failure')
   probes.append(dict(pid=p.pid,created=created,kernel_exit_filetime=ts[1],exit=code,start_qpc=t,end_qpc=ticks(),phase=mode,retained_handle=True,handle_signalled=True))
   save('probes.json',probes);last=time.monotonic()-began
   if code:raise RuntimeError('Probe exit failed')
  if time.monotonic()-began>duration+15:raise RuntimeError('Existing bounded workload deadline exceeded')
  time.sleep(.05)
 if child:
  _,err=child.communicate(timeout=1);phase['worker_exit']=child.returncode
  if child.returncode:raise RuntimeError('Workload failed '+err.decode(errors='replace'))
  child=None
 reader.poll();phase.update(status='COMPLETE',end_qpc=ticks())
except BaseException:
 status='FAILED_CLOSED';error=traceback.format_exc();save('collector-failure.json',dict(error=error,qpc=ticks()))
finally:
 (out/'workload-stop').touch()
 if child:
  try:child.communicate(timeout=15)
  except subprocess.TimeoutExpired:child.kill();child.communicate();save('workload-forced-cleanup.json',dict(pid=child.pid,method='directly retained child handle'))
  phase['worker_exit']=child.returncode
 phase.setdefault('end_qpc',ticks());save('probes.json',probes);save('phases.json',[phase]);save('collector-samples.json',samples)
 save('collector-finished.json',dict(status=status,error=error,qpc=ticks(),utc=utc(),acceptance=False));reader.close()
try:
 end=time.monotonic()+60
 while k.WaitForSingleObject(watch.handle,0)==258:
  if time.monotonic()>end:raise RuntimeError('Monitor finalization deadline; stop batch')
  time.sleep(.05)
 code=w.DWORD()
 if not k.GetExitCodeProcess(watch.handle,c.byref(code)):raise c.WinError(c.get_last_error())
 save('monitor-exit.json',dict(identity=identity,exit_code=code.value))
 if resource:
  _,err=resource.communicate(timeout=10);save('resource-exit.json',dict(pid=resource.pid,exit=resource.returncode,stderr=err.decode(errors='replace')))
 verified=[]
 for p in handles:
  if k.WaitForSingleObject(int(p._handle),0)!=0:raise RuntimeError('Probe still active')
  verified.append(dict(pid=p.pid,times=times(p),exit=p.returncode))
 save('retained-handle-verification.json',verified)
 if journal!=out/'heartbeat.jsonl':
  data=journal.read_bytes();(out/'heartbeat.jsonl').write_bytes(data)
  save('journal-copy-verification.json',dict(original=str(journal),sha256=hashlib.sha256(data).hexdigest(),copied_sha256=hashlib.sha256((out/'heartbeat.jsonl').read_bytes()).hexdigest()))
 if code.value:raise RuntimeError('Monitor error requires review before next diagnostic run')
finally:watch.close()
print(json.dumps(dict(run=run,status=status,probes=len(probes),acceptance=False)),flush=True)
