import json,sys,uuid,time,hashlib
from pathlib import Path
R=Path(__file__).parent;C=Path(json.loads((R/'candidate.json').read_text())['code']);sys.path.insert(0,str(C))
from workspace import new_run,activate_temp
from native_bridge import NativeBridge
from probe_timing import Probe,process_times
from journal import ticks,frequency
root=new_run('early-rapid-'+uuid.uuid4().hex);activate_temp(root);b=NativeBridge(root);b.install();ps=[];failure=None;checks=[]
try:
 for i in range(24):
  p=Probe(C/'J6Probe.exe');ps.append(p);p.wait_approved(lambda:None,lambda v:None,ticks()/frequency()+30);p.finish_observation()
 b.close()
 for p in ps:
  pid=p.row['pid'];created=p.row['initialKernelTimes'][0];ep=root/f'early-image-{pid}-{created}.json';early=json.loads(ep.read_text());n=json.loads((root/f'native-{pid}-{created}.json').read_text())
  assert early['source']=='creator-owned-handle' and early['handlePid']==pid and early['created']==early['handleCreated']==created
  assert early['success'] and early['imageError']==0 and early['processState']==258
  assert Path(early['image'])==C/'J6Probe.exe'
  assert early['createEndQpc']<=early['handleAcquiredQpc']<=early['queryBeginQpc']<=early['queryEndQpc']<n['identityPersistedQpc']<n['entryQpc']<n['signalObservedQpc']
  assert n['finalWait']==0 and not n['fault'] and not n['deadlineExceeded'] and p.row['observerResult']==0
  checks.append(dict(pid=pid,created=created,image=early['image'],earlySHA256=hashlib.sha256(ep.read_bytes()).hexdigest(),queryBeforeEntryTicks=n['entryQpc']-early['queryEndQpc'],lifetimeSeconds=(int(n['exitFiletime'])-int(created))/1e7,passed=True))
except BaseException as e:failure=repr(e)
finally:
 closures=[]
 for p in ps:
  p.observer.join(16);exited=p.process.poll() is not None
  closures.append(dict(pid=p.row['pid'],created=p.row['initialKernelTimes'][0],exited=exited,times=process_times(p.process)))
  if exited:p.process._handle.Close()
 result=dict(status='PASS' if failure is None and len(checks)==24 and all(x['exited'] for x in closures) else 'FAIL',failure=failure,checks=checks,closures=closures,run=str(root),actualPIDReuse=len(ps)-len({p.row['pid'] for p in ps}),kernelObservers=False)
 with (root/'rapid-result.json').open('x') as f:json.dump(result,f,indent=2)
 with (R/'rapid-result.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(dict(status=result['status'],failure=failure,count=len(checks),run=str(root))))
 if result['status']!='PASS':raise SystemExit(1)
