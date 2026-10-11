import sys,time,json,os
from workspace import CODE,run_dir,activate_temp
from native_bridge import NativeBridge
from probe_timing import Probe,process_times
from journal import ticks,frequency
root=run_dir(sys.argv[1]);activate_temp(root)
def save(name,obj):
 with (root/name).open('x') as f:json.dump(obj,f,indent=2)
b=NativeBridge(root);b.install();probes=[];failure=None
try:
 for case in ('idle','churn','overlap'):
  for i in range(4):
   group=[]
   for j in range(2 if case=='overlap' else 1):
    p=Probe(CODE/'J6Probe.exe');p.row.update(case=case,index=i);group.append(p);probes.append(p)
   for p in group:
    p.wait_approved(lambda:None,lambda v:None,time.monotonic()+30)
    p.finish_observation()
   if case=='idle':time.sleep(.1)
 b.close()
 save('identity-probes.json',{'frequency':frequency(),'rows':[p.row for p in probes],'handlesRemainRetained':True,'qpc':ticks(),'failure':None})
 deadline=time.monotonic()+60
 while not (root/'release-handles').exists():
  if time.monotonic()>deadline:raise TimeoutError('Fixed diagnostic handle-release bound')
  time.sleep(.05)
except BaseException as e:
 failure=repr(e)
 save('identity-worker-failure.json',{'failure':failure,'rows':[p.row for p in probes]})
finally:
 closure=[]
 for p in probes:
  p.observer.join(16)
  exited=p.process.poll() is not None
  closure.append({'pid':p.process.pid,'times':process_times(p.process),'exited':exited,'closedQpc':ticks()})
  if exited:p.process._handle.Close()
 save('identity-handle-closure.json',{'rows':closure,'allExited':all(x['exited'] for x in closure),'failure':failure})
if failure:raise RuntimeError(failure)
