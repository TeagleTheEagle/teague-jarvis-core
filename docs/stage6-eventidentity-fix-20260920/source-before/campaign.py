"""Synthetic monitoring campaign. Source paths are fixed in workload/hash workers."""
import pathlib,sys,time,json,subprocess,traceback,ctypes as c,ctypes.wintypes as w,datetime,shutil
from journal import Reader,PublisherWatch,ticks
from finalize import accepted,durable_write,sync_file,sha
R=pathlib.Path(__file__).parent;run=sys.argv[1];assert run in ('loads','loads2','dry1','dry2');out=R/run
plan=[('idle',30),('disk',100),('sustained',150),('cpu',40),('Dhash',90)] if run.startswith('loads') else [('hash-before',60),('sustained',120),('hash-after',60)]
def save(n,v):(out/n).write_text(json.dumps(v,indent=2))
ident=json.loads((out/'ready.json').read_text());watch=PublisherWatch(ident);reader=Reader(out/'heartbeat.jsonl',ident,liveness=watch.check)
samples=[];phases=[];probes=[];probe_handles=[];child=None;status='LIVE_MONITOR_HEALTHY';error=None
try:
 for mode,duration in plan:
  phase={'mode':mode,'duration_requested':duration,'start_qpc':ticks(),'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};phases.append(phase);save('phases.json',phases)
  if mode!='idle':
   command=[sys._base_executable,'-B',str(R/'hash_sources.py'),run,mode.split('-')[1]] if mode.startswith('hash-') else [sys._base_executable,'-B',str(R/'workload.py'),run,mode,str(duration)]
   child=subprocess.Popen(command,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE);phase['pid']=child.pid;save('phases.json',phases)
  began=time.perf_counter();lastprobe=-5
  while (child is not None and child.poll() is None) or (mode=='idle' and time.perf_counter()-began<duration):
   if (out/'monitor-failure.json').exists():raise RuntimeError('monitor failed')
   now=ticks()
   try:v=reader.poll()
   except BaseException:
    save('rejected-poll.json',{'qpc_before_poll':now,'qpc_after_poll':ticks(),'last_record':reader.last,'computed_age_after_exception':None if reader.last is None else (ticks()-reader.last['ticks'])/ident['frequency'],'phase':mode});raise
   samples.append(dict(v,qpc=now,phase=mode))
   if time.perf_counter()-began-lastprobe>=5:
    t=ticks();p=subprocess.Popen([str(R/'J6Probe.exe')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);probe_handles.append(p);p.wait(timeout=5)
    if any(pr['pid']==p.pid for pr in probes):raise RuntimeError('Probe PID reused despite retained handle')
    times=[w.FILETIME() for _ in range(4)]
    if not watch.k.GetProcessTimes(int(p._handle),*[c.byref(x) for x in times]):raise c.WinError(c.get_last_error())
    probes.append({'pid':p.pid,'created':str((times[0].dwHighDateTime<<32)|times[0].dwLowDateTime),'start_qpc':t,'end_qpc':ticks(),'phase':mode,'exit':p.returncode,'handle_retained_through_finalization':True});lastprobe=time.perf_counter()-began
   if time.perf_counter()-began>duration+15:raise RuntimeError('workload exceeded bounded completion')
   time.sleep(.05)
  if child is not None:
   _,err=child.communicate(timeout=1)
   if child.returncode:raise RuntimeError('workload failure '+err.decode(errors='replace'))
   child=None
  reader.poll();phase['end_qpc']=ticks();phase['status']='COMPLETE';save('phases.json',phases)
except BaseException:
 status='FAILED_CLOSED';error=traceback.format_exc();save('collector-failure.json',{'error':error,'qpc':ticks()})
finally:
 (out/'workload-stop').touch()
 if child is not None:
  try:child.communicate(timeout=15)
  except subprocess.TimeoutExpired:child.kill();child.communicate();save('workload-forced-cleanup.json',{'pid':child.pid,'method':'retained directly launched Popen handle'})
 save('collector-samples.json',samples);save('probes.json',probes);save('phases.json',phases);save('collector-finished.json',{'status':status,'error':error,'qpc':ticks()});reader.close()
try:
 # The live phase is now over. Final durability has a separate bounded 60-second deadline.
 end=time.perf_counter()+60
 while watch.k.WaitForSingleObject(watch.handle,0)==258:
  if time.perf_counter()>end:raise RuntimeError('Final monitor durability/exit deadline exceeded; no acceptance')
  time.sleep(.05)
 watch.k.GetExitCodeProcess.argtypes=[w.HANDLE,c.POINTER(w.DWORD)];code=w.DWORD()
 if not watch.k.GetExitCodeProcess(watch.handle,c.byref(code)):raise c.WinError(c.get_last_error())
 save('monitor-exit.json',{'identity':ident,'exit_code':code.value})
 if code.value!=0:raise RuntimeError('Monitor failed finalization/exit')
finally:watch.close()
if status!='LIVE_MONITOR_HEALTHY':print(status);sys.exit(1)
# Resource sampler has an independent exit; require its complete output before finalization.
end=time.perf_counter()+10
while not (out/'resources-complete').exists():
 if time.perf_counter()>end:raise RuntimeError('Resource evidence missing')
 time.sleep(.05)
p=subprocess.Popen([sys._base_executable,'-B',str(R/'finalize.py'),run],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
try:stdout,stderr=p.communicate(timeout=60)
except subprocess.TimeoutExpired:
 p.kill();stdout,stderr=p.communicate();save('finalization-failure.json',{'error':'Final evidence deadline exceeded','pid':p.pid,'exit':p.returncode});raise
save('finalizer-process.json',{'pid':p.pid,'exit_code':p.returncode,'stdout':stdout.decode(errors='replace'),'stderr':stderr.decode(errors='replace')})
if not accepted(out,p.returncode):raise RuntimeError('Durable finalization/archive verification failed')
receipt={'status':'SACRIFICIAL_RUN_ACCEPTED','live_status':status,'evidence_status':'EVIDENCE_DURABLY_FINALIZED','finalizer_pid':p.pid,'finalizer_exit':p.returncode,'manifest_sha256':sha(out/'evidence-manifest.json')}
durable_write(out/'acceptance.json',receipt);shutil.copyfile(out/'acceptance.json',out/'archive'/'acceptance.json');sync_file(out/'archive'/'acceptance.json')
assert sha(out/'acceptance.json')==sha(out/'archive'/'acceptance.json')
print(json.dumps(receipt),flush=True)
