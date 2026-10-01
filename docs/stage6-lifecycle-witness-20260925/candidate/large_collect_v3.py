"""Real producer adapter for the unchanged dual-evidence cleanup contract."""
import os,sys,time,traceback
from workspace import CODE,run_dir,activate_temp
from baseline_contract import load,save,advance,state
from dry_health import Health
from evidence_support_v3 import TreeTracker,Managed,Ledger
from probe_timing import Probe,K,process_times
from journal import ticks,frequency
from secondary_sampling import SecondarySampler
def main(root):
 contract=load(root);ledger=Ledger(root);tree=TreeTracker(collector_anchor=True,run_root=root);health=None;worker=None;sampler=None;probes=[];handles=[];launched=[];results=[]
 def secondary(stage,fn):
  try:return fn()
  except BaseException:ledger.fail(stage)
 def warning(v):
  with (root/'warnings.jsonl').open('a') as f:
   import json
   f.write(json.dumps(v)+'\n');f.flush()
 try:
  health=Health(root);advance(root,'OBSERVERS_READY','WORKLOAD_RUNNING');deadline=ticks()/frequency()+contract['thresholds']['campaign']
  sampler=SecondarySampler(root,tree,launched,ledger)
  worker=Managed([sys._base_executable,'-B',str(CODE/'baseline_hash_worker.py'),root.name],root,'hash-worker',tree);launched.append(worker.identity)
  while worker.p.poll() is None or len(probes)<2:
   health.check()
   if ledger.primary:raise RuntimeError('Required diagnostic evidence failed')
   if ticks()/frequency()+13.6>=deadline:raise RuntimeError('Fixed campaign admission deadline')
   probe=Probe(CODE/'J6Probe.exe');probes.append(probe);tree.register(probe.process,'lifecycle-probe')
   launched.append(dict(pid=probe.process.pid,created=process_times(probe.process)[0],role='lifecycle-probe',parentPid=os.getpid()))
   if probe.wait_approved(health.check,warning,deadline)!=0:raise RuntimeError('Nonzero probe exit')
   probe.finish_observation()
   if probe.row['independentObserverFailed']:raise RuntimeError('Independent 15-second observation failed')
   ts=process_times(probe.process);handles.append(dict(pid=probe.process.pid,times=ts,exit=probe.process.returncode,handleState=int(K.WaitForSingleObject(int(probe.process._handle),0))))
   time.sleep(.3) # Existing producer pacing; never a deadline adjustment.
  done=worker.finish(15);results.append(done)
  if done['handleState']!=0 or done['exit']!=0 or any(not done.get(n,{}).get('eof') or done[n].get('error') for n in ('stdout','stderr')):raise RuntimeError('Hash worker exit/output failed; preserve hash-failure and captured stderr')
  health.check()
  if state(root)['phase']!='METADATA_VERIFIED':raise RuntimeError('Hash workflow incomplete')
 except BaseException:ledger.fail('integrated-collection')
 finally:
  secondary('workload-stop',lambda:(root/'workload-stop').touch())
  if worker and not worker.finished:
   done=secondary('worker-cleanup',lambda:worker.finish(15))
   if done:
    results.append(done)
    if done['handleState']!=0 or done['exit']!=0:ledger.fail('worker-cleanup','Worker not cleanly exited')
  for probe in probes:
   def close_probe(probe=probe):
    p=probe.process;signal=int(K.WaitForSingleObject(int(p._handle),30000)) # Post-failure evidence only.
    if not probe.row.get('reconciledQpc'):probe.finish_observation()
    if probe.row.get('independentObserverFailed'):raise RuntimeError('Independent observer failure remains a failure')
    if signal!=0:raise RuntimeError('Probe remains alive; do not terminate implicitly')
    if not any(x['pid']==p.pid for x in handles):handles.append(dict(pid=p.pid,times=process_times(p),exit=p.poll(),handleState=signal))
    p._handle.Close()
   secondary('probe-cleanup',close_probe)
  if sampler:secondary('sampler-close',sampler.close)
  proof=secondary('tree-cleanup',lambda:tree.finish(root,20))
  if not proof or not proof.get('supportingEvidenceValid',False) or not proof['localFinalized'] or not proof['allHandlesClosed'] or not proof['threadStopped']:ledger.fail('tree-cleanup','Incomplete retained tree')
  if health:health.close();secondary('health-samples',lambda:save(root/'collector-health-samples.json',health.samples))
  secondary('probe-timings',lambda:save(root/'probe-timings.json',[x.row for x in probes]))
  secondary('probe-handles',lambda:save(root/'retained-handle-verification.json',handles))
  if not ledger.primary:secondary('workload-closure',lambda:advance(root,'METADATA_VERIFIED','WORKLOAD_CLOSED'))
  save(root/'stress-result.json',dict(ledger.result(),scenario=contract['scenario'],producer='large_collect.py',collectorPid=os.getpid(),launched=launched,results=results))
 return 1 if ledger.primary else 0
if __name__=='__main__':
 root=run_dir(sys.argv[1]);activate_temp(root);sys.exit(main(root))
