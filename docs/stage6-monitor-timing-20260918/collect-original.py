import pathlib,sys,time,json,subprocess,traceback,datetime
from journal import Reader,PublisherWatch,ticks
R=pathlib.Path(__file__).parent
run=sys.argv[1];assert run.replace('-','').isalnum();out=R/run
plan={'stepped':[('idle',30),('low',25),('moderate',30),('full',35),('sustained',150)],'isolation':[('cpu',40),('disk',50),('Dhash',50)]}[sys.argv[2]]
def save(n,v):(out/n).write_text(json.dumps(v,indent=2))
ident=json.loads((out/'ready.json').read_text());watch=PublisherWatch(ident);reader=Reader(out/'heartbeat.jsonl',ident,liveness=watch.check)
samples=[];phases=[];probes=[];child=None;status='DIAGNOSTIC_COMPLETE';error=None
try:
 for mode,duration in plan:
  phase={'mode':mode,'duration_requested':duration,'start_qpc':ticks(),'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};phases.append(phase);save('phases.json',phases)
  if mode!='idle':
   child=subprocess.Popen([sys._base_executable,'-B',str(R/'workload.py'),run,mode,str(duration)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
   phase['pid']=child.pid;save('phases.json',phases)
  began=time.perf_counter();lastprobe=-10
  while time.perf_counter()-began<duration or child is not None and child.poll() is None:
   if (out/'monitor-failure.json').exists():raise RuntimeError('monitor failed')
   now=ticks()
   try:v=reader.poll()
   except BaseException:
    save('rejected-poll.json',{'qpc_before_poll':now,'qpc_after_poll':ticks(),'last_record':reader.last,'computed_age_after_exception':None if reader.last is None else (ticks()-reader.last['ticks'])/ident['frequency'],'phase':mode});raise
   samples.append(dict(v,qpc=now,phase=mode))
   if time.perf_counter()-began-lastprobe>=10:
    t=ticks();p=subprocess.Popen([str(R/'J6Probe.exe')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);p.wait(timeout=5);probes.append({'pid':p.pid,'start_qpc':t,'end_qpc':ticks(),'phase':mode,'exit':p.returncode});lastprobe=time.perf_counter()-began
   if time.perf_counter()-began>duration+15:raise RuntimeError('workload exceeded bounded completion')
   time.sleep(.05)
  if child is not None:
   _,err=child.communicate(timeout=1)
   if child.returncode:raise RuntimeError('workload failure '+err.decode(errors='replace'))
   child=None
  phase['end_qpc']=ticks();phase['status']='COMPLETE';save('phases.json',phases)
except BaseException:
 status='FAILED_CLOSED';error=traceback.format_exc();save('collector-failure.json',{'error':error,'qpc':ticks()})
finally:
 (out/'workload-stop').touch()
 if child is not None:
  try:child.communicate(timeout=15)
  except subprocess.TimeoutExpired:
   # Only this directly launched synthetic child, never any external process.
   child.kill();child.communicate();save('workload-forced-cleanup.json',{'pid':child.pid,'method':'retained Popen handle after stop deadline','source':str(R/'workload.py')})
 save('collector-samples.json',samples);save('probes.json',probes);save('phases.json',phases)
 save('collector-finished.json',{'status':status,'error':error,'qpc':ticks()});reader.close();watch.close()
print(status,flush=True)
if status!='DIAGNOSTIC_COMPLETE':sys.exit(1)
