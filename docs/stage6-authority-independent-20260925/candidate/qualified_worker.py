import sys,time,json,os
from workspace import CODE,run_dir,activate_temp
from native_bridge import NativeBridge
from probe_timing import Probe,process_times
from journal import ticks,frequency
from health_reader import HealthReader
root=run_dir(sys.argv[1]);activate_temp(root)
from fresh_binding import bound
_bound,declaration=bound(CODE)
if _bound!=root:raise ValueError('WORKER_RUN_BINDING')
def save(name,obj):
 with (root/name).open('x') as f:json.dump(obj,f,indent=2)
ready=json.loads((root/'app-ready.json').read_text(encoding='utf-8-sig'))
health_reader=HealthReader(root,ready);health_samples=[]
def health():
 v=health_reader.poll()
 health_samples.append(dict(qpc=ticks(),age=v['age']))
probes=[];failure=None
try:
 b=NativeBridge(root);b.install()
 for plan in declaration['cases']:
  case=plan['name']
  for i in range(plan['groups']):
   group=[]
   for j in range(plan['width']):
    p=Probe(CODE/'J6Probe.exe');p.row.update(case=case,index=i);group.append(p);probes.append(p)
   for p in group:
    p.wait_approved(health,lambda v:None,ticks()/frequency()+30)
    p.finish_observation()
   if case=='idle':time.sleep(.1)
 b.close()
 save('identity-probes.json',{'frequency':frequency(),'rows':[p.row for p in probes],'handlesRemainRetained':True,'qpc':ticks(),'failure':None})
 deadline=time.monotonic()+60
 while not (root/'release-handles').exists():
  if time.monotonic()>deadline:raise TimeoutError('Fixed diagnostic handle-release bound')
  time.sleep(.05)
 health_reader.finalize()
except BaseException as e:
 failure=repr(e)
 save('identity-worker-failure.json',{'failure':failure,'rows':[p.row for p in probes]})
finally:
 health_reader.close()
 closure=[]
 for p in probes:
  p.observer.join(16)
  exited=p.process.poll() is not None
  closure.append({'pid':p.process.pid,'times':process_times(p.process),'exited':exited,'closedQpc':ticks()})
  if exited:p.process._handle.Close()
 save('identity-handle-closure.json',{'rows':closure,'allExited':all(x['exited'] for x in closure),'failure':failure})
save('live-health-checks.json',health_samples)
if failure:raise RuntimeError(failure)
