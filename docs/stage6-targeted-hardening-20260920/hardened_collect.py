import sys,threading,time,os,json
from workspace import CODE,run_dir,activate_temp
from evidence_support import Ledger,TreeTracker,put
from dry_health import Health
from probe_timing import Probe,K,process_times
from controls import make_probe
from bounded_sampler import query
from journal import ticks,frequency
root=run_dir(sys.argv[1]);activate_temp(root);ledger=Ledger(root);tree=TreeTracker();health=None;probes=[];launched=[];sampler=[];stop=threading.Event();thread=None
def sample():
 try:
  cases=[('normal','normal'),('slow','slow'),('hung','hung'),('exception','exception'),('cancellation','hung'),('cleanup-timeout','hung'),('crash','crash')]
  for i,(label,mode) in enumerate(cases):
   if stop.is_set():break
   cancel=threading.Event();timer=None
   if label=='cancellation':timer=threading.Timer(.1,cancel.set);timer.start()
   result=query(root,mode,i,cancel,tree,cleanup_injection=label=='cleanup-timeout');result['case']=label;sampler.append(result)
   if timer:timer.cancel();timer.join()
   if result.get('pid'):launched.append(dict(pid=result['pid'],created=result['created'],role='sampler:'+label,parentPid=os.getpid()))
   if result['status']=='CLEANUP_FAILED':raise RuntimeError('Required sampler cleanup failed')
 except BaseException:ledger.fail('sampler-supervisor')
try:
 health=Health(root);thread=threading.Thread(target=sample,name='secondary-sampler');thread.start();deadline=ticks()/frequency()+60
 while len(probes)<12 or thread.is_alive():
  if ledger.primary:raise RuntimeError('Diagnostic evidence failure')
  health.check()
  if ticks()/frequency()+13.6>=deadline:raise RuntimeError('Diagnostic admission bound')
  p=make_probe('A_D') if len(probes)%3==2 else Probe(CODE/'J6Probe.exe');probes.append(p);tree.register(p.process,'diagnostic-probe');launched.append(dict(pid=p.process.pid,created=process_times(p.process)[0],role='probe',parentPid=os.getpid()))
  if p.wait_approved(health.check,lambda v:None,deadline)!=0:raise RuntimeError('Probe failed')
  p.finish_observation()
  if p.row['independentObserverFailed']:raise RuntimeError('Independent observer failed')
  time.sleep(.3)
 if len(sampler)!=7 or sampler[0]['status']!='AVAILABLE':raise RuntimeError('Normal/complete secondary test coverage missing')
 if any(x['status']!='MISSING' for x in sampler[1:]):raise RuntimeError('Injected missing telemetry incorrectly reported successful')
except BaseException:ledger.fail('combined-diagnostic')
finally:
 stop.set()
 if thread:
  thread.join(6)
  if thread.is_alive():ledger.fail('sampler-close','Secondary supervisor has not exited')
 for p in probes:
  try:
   state=int(K.WaitForSingleObject(int(p.process._handle),30000))
   if not p.row.get('reconciledQpc'):p.finish_observation()
   if state!=0:raise RuntimeError('Probe remains alive')
   p.process._handle.Close()
  except BaseException:ledger.fail('probe-cleanup')
 proof=tree.finish(root,20)
 if not proof['allExited'] or not proof['allHandlesClosed']:ledger.fail('tree-cleanup','Unproven descendants')
 if health:health.close();put(root/'collector-health-samples.json',health.samples)
 put(root/'probe-timings.json',[p.row for p in probes]);put(root/'sampler-results.json',sampler)
 put(root/'stress-result.json',dict(ledger.result(),collectorPid=os.getpid(),launched=launched,secondarySamplerComplete=thread is not None and not thread.is_alive()))
sys.exit(1 if ledger.primary else 0)
