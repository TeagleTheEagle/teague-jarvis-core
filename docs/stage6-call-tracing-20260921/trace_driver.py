import pathlib,sys,os,time,threading,json,hashlib,traceback
from workspace import CODE,run_dir,activate_temp
from evidence_support import TreeTracker,put
from probe_timing import Probe,K,process_times
from bounded_sampler import query
from journal import ticks,frequency
import call_trace as ct
root=run_dir(sys.argv[1]);activate_temp(root);os.chdir(CODE)
ct.install();ct.label('driver');pressure=ct.Pressure();tree=TreeTracker();probes=[];samplers=[];failure=None;stop=threading.Event();loadthread=None;loadrow={}
put(root/'driver-identity.json',dict(pid=os.getpid(),parentPid=os.getppid(),image=sys.executable,frequency=frequency(),qpc=ticks(),perfCounterNs=time.perf_counter_ns()))
payload=root/'synthetic-load.bin'
with payload.open('xb') as f:
 block=b'SACRIFICIAL-CALL-TRACE-ONLY\0'*4096
 for _ in range(512):f.write(block)
digest=hashlib.sha256(payload.read_bytes()).hexdigest();stat=payload.stat()
def loadwork():
 begin=ticks();total=0
 while not stop.is_set() and (ticks()-begin)/frequency()<35:
  h=hashlib.sha256()
  with payload.open('rb',buffering=0) as f:
   while not stop.is_set():
    b=f.read(4*2**20)
    if not b:break
    h.update(b);total+=len(b)
 loadrow.update(beginQpc=begin,endQpc=ticks(),bytesRead=total)
def one_probe(condition,index):
 ct.label('probe:'+str(index)+':'+condition);p=Probe(CODE/'J6Probe.exe');ct.wrap('tree.retained_handle_registration',tree.register)(p.process,'fixed-probe',[str(CODE/'J6Probe.exe')]);error=None
 try:
  if p.wait_approved(lambda:None,lambda v:None,ticks()/frequency()+13.6)!=0:raise RuntimeError('Probe exit error')
  ct.wrap('probe.observer_join',p.finish_observation)()
  if p.row['independentObserverFailed']:raise RuntimeError('Independent observer failure')
 except BaseException:error=traceback.format_exc();stop.set()
 finally:
  if error:K.WaitForSingleObject(int(p.process._handle),30000);p.finish_observation()
  p.row.update(condition=condition,index=index,diagnosticError=error)
  if p.row['finalHandleState']==0:ct.wrap('probe.parent_handle_close',p.process._handle.Close)();p.row['parentHandleClosed']=True
  else:p.row['parentHandleClosed']=False
  probes.append(p.row)
 if error:raise RuntimeError('Original probe failure reproduced; stop')
try:
 for i in range(20):one_probe('idle',i);time.sleep(.1)
 print('IDLE 20 COMPLETE',flush=True)
 loadthread=threading.Thread(target=loadwork);loadthread.start()
 for i in range(20,80):one_probe('D-small-hash',i);time.sleep(.3)
 stop.set();loadthread.join(5)
 if loadthread.is_alive():raise RuntimeError('Hash load did not stop')
 print('HASH 60 COMPLETE',flush=True)
 for i,(case,mode) in enumerate([('normal-1','normal'),('normal-2','normal'),('normal-3','normal'),('delayed','slow'),('cancelled','hung')]):
  ct.label('sampler:'+case);cancel=threading.Event();timer=None
  if case=='cancelled':timer=threading.Timer(.1,ct.wrap('sampler.cancel_signal',cancel.set));timer.start()
  try:x=ct.wrap('sampler.query_total',query)(root,mode,i,cancel,tree)
  finally:
   if timer:timer.cancel();timer.join()
  x['case']=case;samplers.append(x)
  if not x.get('allExited') or not x.get('handleClosed') or (mode=='normal' and x['status']!='AVAILABLE'):raise RuntimeError('Sampler failure reproduced; stop')
  print('SAMPLER '+case+' '+x['status'],flush=True)
except BaseException:failure=traceback.format_exc();stop.set()
finally:
 ct.label('final-cleanup');stop.set()
 if loadthread:ct.wrap('load.thread_join',loadthread.join)(5)
 treeResult=ct.wrap('tree.final_reconciliation',tree.finish)(root,20)
 resource=pressure.close();markers=ct.internal()
 sourceUnchanged=payload.stat().st_size==stat.st_size and payload.stat().st_mtime_ns==stat.st_mtime_ns and hashlib.sha256(payload.read_bytes()).hexdigest()==digest
 if not treeResult['allExited'] or not treeResult['allHandlesClosed'] or not treeResult['threadStopped'] or not resource['threadExited'] or ct.OVERFLOW or not sourceUnchanged:failure=failure or 'Finalization/cleanup/preservation failed'
 calls=dict(frequency=frequency(),rows=ct.ROWS,overflow=ct.OVERFLOW,internal=markers,slow2=[x for x in ct.ROWS if x['seconds']>=2],slow5=[x for x in ct.ROWS if x['seconds']>=5])
 ct.wrap('evidence.final_write',put)(root/'calls.json',calls)
 put(root/'pressure.json',resource);put(root/'probes.json',probes);put(root/'samplers.json',samplers);put(root/'load.json',loadrow)
 result=dict(status='FAILED_STOPPED' if failure else 'BOUNDED_DIAGNOSTIC_COMPLETE',failure=failure,probes=len(probes),samplers=len(samplers),internalMarkers=len(markers),calls=len(ct.ROWS),overflow=ct.OVERFLOW,cleanup=treeResult,sourceUnchanged=sourceUnchanged,sourceBytes=stat.st_size,sourceSHA256=digest,protectedAccess=False,productionChanged=False,acceptance=False)
 put(root/'result.json',result);put(root/'final-write-timing.json',[x for x in ct.ROWS if x['call']=='evidence.final_write'])
 print(json.dumps({k:v for k,v in result.items() if k!='cleanup'}),flush=True)
sys.exit(bool(failure))
