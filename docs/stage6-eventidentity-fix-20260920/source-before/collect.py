"""Sacrificial probes/loads. Handle exit evidence never becomes a STOP notification."""
import ctypes as c,ctypes.wintypes as w,datetime,json,pathlib,subprocess,sys,time,traceback
from journal import Reader,PublisherWatch,ticks
R=pathlib.Path(__file__).resolve().parent
run=sys.argv[1];assert run in ('smoke','repeat1','repeat2')
out=R/run;assert out.is_dir()
def save(n,v):(out/n).write_text(json.dumps(v,indent=2),encoding='utf-8')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
deadline=time.monotonic()+20
while not (out/'ready.json').exists():
 if (out/'monitor-failure.json').exists():raise RuntimeError('Monitor startup failed; evidence preserved')
 if time.monotonic()>deadline:raise RuntimeError('Monitor did not become ready; no probes started')
 time.sleep(.1)
identity=json.loads((out/'ready.json').read_text(encoding='utf-8-sig'));watch=PublisherWatch(identity)
reader=Reader(out/'heartbeat.jsonl',identity,liveness=watch.check)
k=watch.k;k.GetExitCodeProcess.argtypes=[w.HANDLE,c.POINTER(w.DWORD)]
def process_times(p):
 v=[w.FILETIME() for _ in range(4)]
 if not k.GetProcessTimes(int(p._handle),*[c.byref(x) for x in v]):raise c.WinError(c.get_last_error())
 return [str((x.dwHighDateTime<<32)|x.dwLowDateTime) for x in v]
pwsh=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
resource=subprocess.Popen([pwsh,'-NoProfile','-File',str(R/'resources.ps1'),'-Run',run],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,creationflags=0x08000000)
plan=[('idle',4)] if run=='smoke' else [('idle',20),('disk',100),('sustained',40),('cpu',20),('Dhash',40)]
probes=[];handles=[];samples=[];phases=[];child=None;status='DIAGNOSTIC_COMPLETED';error=None
try:
 for mode,duration in plan:
  phase={'mode':mode,'start_qpc':ticks(),'start_utc':utc(),'duration_requested':duration};phases.append(phase);save('phases.json',phases)
  if mode!='idle':
   child=subprocess.Popen([sys._base_executable,'-B',str(R/'workload.py'),run,mode,str(duration)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,creationflags=0x08000000)
   phase['worker_identity']={'pid':child.pid,'created':process_times(child)[0]}
  began=time.monotonic();last=-1
  while (child is not None and child.poll() is None) or (mode=='idle' and time.monotonic()-began<duration):
   if (out/'monitor-failure.json').exists():raise RuntimeError('Monitor failed')
   sample=reader.poll();samples.append(dict(sample,qpc=ticks(),phase=mode))
   if time.monotonic()-began-last>=1:
    launched=ticks();launchutc=utc();p=subprocess.Popen([str(R/'J6Probe.exe')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=0x08000000);handles.append(p)
    created=process_times(p)[0];code=p.wait(timeout=5);completed=ticks();times=process_times(p)
    if any(v['pid']==p.pid for v in probes):raise RuntimeError('Duplicate PID under retained handles')
    if created!=times[0] or k.WaitForSingleObject(int(p._handle),0)!=0:raise RuntimeError('Handle identity/exit mismatch')
    probes.append({'pid':p.pid,'created':created,'kernel_exit_filetime':times[1],'exit':code,'start_qpc':launched,'end_qpc':completed,
     'launch_utc':launchutc,'wait_completion_utc':utc(),'phase':mode,'retained_handle':True,'handle_signalled':True})
    save('probes.json',probes);last=time.monotonic()-began
    if code:raise RuntimeError('Probe exit not zero')
   if time.monotonic()-began>duration+15:raise RuntimeError('Workload exceeded existing bounded completion')
   time.sleep(.05)
  if child:
   _,err=child.communicate(timeout=1)
   if child.returncode:raise RuntimeError('Workload failed: '+err.decode(errors='replace'))
   child=None
  reader.poll();phase.update(end_qpc=ticks(),status='COMPLETE');save('phases.json',phases);print(mode+' COMPLETE',flush=True)
except BaseException:
 status='FAILED_CLOSED';error=traceback.format_exc();save('collector-failure.json',{'error':error,'qpc':ticks()})
finally:
 (out/'workload-stop').touch()
 if child:
  try:child.communicate(timeout=15)
  except subprocess.TimeoutExpired:
   child.kill();child.communicate();save('workload-cleanup.json',{'pid':child.pid,'method':'retained directly launched handle'})
 save('probes.json',probes);save('collector-samples.json',samples);save('phases.json',phases)
 save('collector-finished.json',{'status':status,'error':error,'qpc':ticks(),'utc':utc()});reader.close()
try:
 end=time.monotonic()+60
 while k.WaitForSingleObject(watch.handle,0)==258:
  if time.monotonic()>end:raise RuntimeError('Diagnostic monitor finalization deadline; identity retained in ready.json')
  time.sleep(.05)
 code=w.DWORD()
 if not k.GetExitCodeProcess(watch.handle,c.byref(code)):raise c.WinError(c.get_last_error())
 save('monitor-exit.json',{'identity':identity,'exit_code':code.value})
 resource.communicate(timeout=10)
 save('resource-exit.json',{'pid':resource.pid,'exit':resource.returncode})
 verified=[]
 for p in handles:
  if k.WaitForSingleObject(int(p._handle),0)!=0:raise RuntimeError('Probe still live')
  verified.append({'pid':p.pid,'times':process_times(p),'exit':p.returncode})
 save('retained-handle-verification.json',verified)
 if code.value or status=='FAILED_CLOSED':raise RuntimeError('Diagnostic run failed; preserved evidence')
finally:watch.close()
print(json.dumps({'run':run,'status':status,'probes':len(probes),'acceptance':False}),flush=True)
