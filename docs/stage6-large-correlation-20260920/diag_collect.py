"""Diagnostic ladder only. Reuses unchanged deadline, identity and tree evidence."""
import sys,time,os
from workspace import CODE,run_dir,activate_temp
from evidence_support import Ledger,TreeTracker,Managed,put
from probe_timing import Probe,K,process_times
from dry_health import Health
from journal import ticks,frequency
root=run_dir(sys.argv[1]);mode=sys.argv[2];assert mode in ('ladder','heartbeat');activate_temp(root)
ledger=Ledger(root);tree=TreeTracker();health=None;resource=None;probes=[];workers=[];stages=[];launched=[];start=ticks();deadline=start/frequency()+180
try:
 health=Health(root)
 resource=Managed([r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe','-NoProfile','-File',str(CODE/'diag_resources.ps1'),'-Run',root.name],root,'resources',tree);launched.append(resource.identity)
 for label,seconds in ([('A',0),('B',5),('C',12),('D',20)] if mode=='ladder' else [('heartbeat',30)]):
  stage=dict(label=label,begin=ticks(),probeCount=0);stages.append(stage);worker=None
  if seconds:
   worker=Managed([sys._base_executable,'-B',str(CODE/'diag_hash.py'),root.name,str(seconds),label],root,'hash-'+label,tree);workers.append(worker);launched.append(worker.identity)
  while (worker and worker.p.poll() is None) or (label=='A' and stage['probeCount']<8):
   health.check()
   if ticks()/frequency()+13.6>=deadline:raise RuntimeError('Bounded diagnostic admission expired')
   if mode=='ladder':
    probe=Probe(CODE/'J6Probe.exe');probes.append(probe);tree.register(probe.process,'lifecycle-probe');stage['probeCount']+=1
    launched.append(dict(pid=probe.process.pid,created=process_times(probe.process)[0],parentPid=os.getpid(),role='lifecycle-probe'))
    if probe.wait_approved(health.check,lambda v:None,deadline)!=0:raise RuntimeError('Probe nonzero exit')
    probe.finish_observation()
    if probe.row['independentObserverFailed']:raise RuntimeError('Independent observer failed')
   time.sleep(.3)
  if worker:
   done=worker.finish(15)
   if done['handleState']!=0 or done['exit']!=0:raise RuntimeError('Diagnostic hash worker failed')
  stage['end']=ticks();health.check()
except BaseException:ledger.fail('diagnostic-ladder')
finally:
 (root/'workload-stop').touch()
 (root/'resource-stop').touch()
 if resource:
  try:
   done=resource.finish(15)
   if done['handleState']!=0 or done['exit']!=0:raise RuntimeError('Resource helper cleanup failed')
  except BaseException:ledger.fail('resource-cleanup')
 for worker in workers:
  try:
   done=worker.finish(15)
   if done['handleState']!=0 or done['exit']!=0:raise RuntimeError('Worker cleanup failed')
  except BaseException:ledger.fail('worker-cleanup')
 for probe in probes:
  try:
   state=int(K.WaitForSingleObject(int(probe.process._handle),30000))
   if not probe.row.get('reconciledQpc'):probe.finish_observation()
   if state!=0:raise RuntimeError('Probe still active')
   if probe.row.get('independentObserverFailed'):ledger.fail('independent-observer','15-second failure preserved')
   probe.process._handle.Close()
  except BaseException:ledger.fail('probe-cleanup')
 try:
  proof=tree.finish(root,20)
  if not proof['allExited'] or not proof['allHandlesClosed']:raise RuntimeError('Tree cleanup incomplete')
 except BaseException:ledger.fail('tree-cleanup')
 if health:health.close();put(root/'collector-health-samples.json',health.samples)
 put(root/'probe-timings.json',[p.row for p in probes]);put(root/'stages.json',stages)
 put(root/'stress-result.json',dict(ledger.result(),collectorPid=os.getpid(),launched=launched,mode=mode))
sys.exit(1 if ledger.primary else 0)
