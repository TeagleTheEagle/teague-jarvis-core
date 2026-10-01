"""Fixed diagnostic adapter; frozen collector semantics and real process identities retained."""
import time
ENTRY_NS=time.perf_counter_ns()
import sys
from workspace import CODE,run_dir,activate_temp
from integration_marks import Marks

def main(root,case):
 import large_collect as collector
 import secondary_sampling
 marks=Marks(root,'collector',ENTRY_NS);status='EXCEPTION'
 originalManaged=collector.Managed;originalProbe=collector.Probe;originalQuery=secondary_sampling.query
 class Managed(originalManaged):
  def __init__(self,args,root,role,tracker=None):
   marks.add('HELPER_INVOCATION',helper=role)
   args=list(args)
   if role=='hash-worker':
    assert args[2]==str(CODE/'baseline_hash_worker.py')
    args[2]=str(CODE/'traced_hash_worker.py');args.append(case)
   try:super().__init__(args,root,role,tracker)
   except BaseException as exc:
    marks.add('HELPER_EXCEPTION',helper=role,exceptionType=type(exc).__name__);raise
   marks.add('HELPER_CREATED',helper=role,helperPid=self.p.pid,helperCreated=str(self.identity['created']))
  def finish(self,seconds=15):
   marks.add('HELPER_WAIT',helper=self.role,helperPid=self.p.pid)
   result=super().finish(seconds)
   marks.add('HELPER_RETURN',helper=self.role,helperPid=self.p.pid,exitCode=result['exit'],handleState=result['handleState'])
   return result
 class Probe(originalProbe):
  def __init__(self,*args,**kwargs):
   marks.add('HELPER_INVOCATION',helper='lifecycle-probe')
   try:super().__init__(*args,**kwargs)
   except BaseException as exc:
    marks.add('HELPER_EXCEPTION',helper='lifecycle-probe',exceptionType=type(exc).__name__);raise
   marks.add('HELPER_CREATED',helper='lifecycle-probe',helperPid=self.process.pid)
  def finish_observation(self):
   result=super().finish_observation()
   marks.add('HELPER_RETURN',helper='lifecycle-probe',helperPid=self.process.pid,exitCode=self.process.poll(),observerFailed=self.row.get('independentObserverFailed'))
   return result
 def query(*args,**kwargs):
  marks.add('HELPER_INVOCATION',helper='resource-sampler')
  try:result=originalQuery(*args,**kwargs)
  except BaseException as exc:
   marks.add('HELPER_EXCEPTION',helper='resource-sampler',exceptionType=type(exc).__name__);raise
  marks.add('HELPER_RETURN',helper='resource-sampler',helperPid=result.get('pid'),helperCreated=str(result.get('created')),allExited=result.get('allExited'),handleClosed=result.get('handleClosed'))
  return result
 try:
  collector.Managed=Managed;collector.Probe=Probe;secondary_sampling.query=query
  marks.add('COLLECTOR_START',case=case)
  result=collector.main(root)
  status='RETURNED' if result==0 else 'FAILED';marks.add('COLLECTOR_RETURN',exitCode=result)
  return result
 except BaseException as exc:
  marks.add('EXCEPTION',exceptionType=type(exc).__name__);raise
 finally:
  collector.Managed=originalManaged;collector.Probe=originalProbe;secondary_sampling.query=originalQuery
  marks.close(status)
if __name__=='__main__':
 root=run_dir(sys.argv[1]);activate_temp(root)
 case=sys.argv[2];assert case in ('normal','hash-start-failure')
 sys.exit(main(root,case))
