"""Diagnostic-only bounded ladder. No acceptance run, threshold edit, or protected path."""
import pathlib,sys,json,hashlib,time,threading,uuid,os,traceback
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\e23d36c0a24246c996aa28e5d5561863\code');sys.path.insert(0,str(C))
from workspace import new_run,activate_temp
from probe_timing import Probe,K,process_times
from journal import ticks,frequency
from evidence_support import TreeTracker,put
from bounded_sampler import query
from baseline_contract import approved,inventory
root=new_run('narrow-'+uuid.uuid4().hex);activate_temp(root);os.chdir(C)
frozen=json.loads((C/'run-source.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for x in frozen:assert sha(C/x['name'])==x['sha256']
source=approved(C/'large-synthetic');before=inventory(source);tail=source/'tail.img'
tree=TreeTracker();probes=[];queries=[];failure=None;loadstop=threading.Event();loadrow={};loadthread=None
put(root/'plan.json',dict(kind='BOUNDED_DIAGNOSTIC_NOT_ACCEPTANCE',idleProbes=20,hashProbes=60,hashReadCapPerCycle=64*2**20,hashLoadMaxSeconds=35,source=str(tail),samplerCases=['normal','slow','cancellation'],hardDeadline=13.6,independentObserverSeconds=15,querySeconds=2,cleanupMilliseconds=2000,protectedAccess=False,root=str(root),sourceManifest=frozen))
print('NARROW_RUN '+str(root),flush=True)
def loadwork():
 begin=ticks();cycles=0;total=0;h=None
 try:
  while not loadstop.is_set() and (ticks()-begin)/frequency()<35:
   h=hashlib.sha256()
   with tail.open('rb',buffering=0) as f:
    for _ in range(16):
     if loadstop.is_set():break
     b=f.read(4*2**20);h.update(b);total+=len(b)
   cycles+=1
  loadrow.update(beginQpc=begin,endQpc=ticks(),cycles=cycles,totalBytes=total,lastPartialDigest=h.hexdigest() if h else None)
 except BaseException:loadrow['error']=traceback.format_exc()
def do_probe(condition,index):
 p=Probe(C/'J6Probe.exe');tree.register(p.process,'diagnostic-probe',[str(C/'J6Probe.exe')]);error=None
 try:
  if p.wait_approved(lambda:None,lambda x:None,ticks()/frequency()+13.6)!=0:raise RuntimeError('Probe nonzero exit')
  p.finish_observation()
  if p.row['independentObserverFailed']:raise RuntimeError('Independent observer failed')
 except BaseException:error=traceback.format_exc()
 finally:
  # Existing post-failure exit observation only, never a new acceptance budget.
  if error:loadstop.set();K.WaitForSingleObject(int(p.process._handle),30000);p.finish_observation()
  p.row.update(condition=condition,ordinal=index,diagnosticError=error)
  if p.row['finalHandleState']==0:p.process._handle.Close();p.row['parentHandleClosed']=True
  else:p.row['parentHandleClosed']=False
  probes.append(p.row);put(root/('probe-'+str(index)+'.json'),p.row)
 if error:raise RuntimeError('Probe failure reproduced; stop ladder')
try:
 for i in range(20):do_probe('idle',i);time.sleep(.1)
 print('IDLE_COMPLETE 20',flush=True)
 loadthread=threading.Thread(target=loadwork);loadthread.start()
 for i in range(20,80):do_probe('synthetic-D-hash',i);time.sleep(.3)
 loadstop.set();loadthread.join(5)
 if loadthread.is_alive() or loadrow.get('error'):raise RuntimeError('Hash load cleanup failed')
 print('HASH_COMPARISON_COMPLETE 60',flush=True)
 for i,(name,mode) in enumerate([('normal','normal'),('delayed','slow'),('cancellation','hung')]):
  cancel=threading.Event();timer=None
  if name=='cancellation':timer=threading.Timer(.1,cancel.set);timer.start()
  try:q=query(root,mode,i,cancel,tree)
  finally:
   if timer:timer.cancel();timer.join()
  q['case']=name;queries.append(q);put(root/('sampler-'+name+'.json'),q)
  if not q.get('allExited') or not q.get('handleClosed') or (name=='normal' and q['status']!='AVAILABLE'):raise RuntimeError('Sampler failure reproduced; stop ladder')
  print('SAMPLER '+name+' '+q['status'],flush=True)
except BaseException:failure=traceback.format_exc();print('STOPPED_ON_FAILURE',flush=True)
finally:
 loadstop.set()
 if loadthread:loadthread.join(5)
 put(root/'load.json',loadrow)
 cleanup=tree.finish(root,20)
 preserved=inventory(source)==before
 drift=[x['name'] for x in frozen if sha(C/x['name'])!=x['sha256']]
 if not preserved or drift or not cleanup['allExited'] or not cleanup['allHandlesClosed'] or not cleanup['threadStopped']:failure=failure or 'Preservation/cleanup failure'
 out=dict(status='REPRODUCED_OR_FAILED' if failure else 'NO_ORIGINAL_FAILURE_REPRODUCED',failure=failure,probes=probes,samplers=queries,load=loadrow,cleanup=cleanup,sourceMetadataPreserved=preserved,sourceDrift=drift,root=str(root),heartbeat='NOT_MEASURED: standalone diagnostic, not monitored acceptance',eventEvidence='No new ETW/CIM subscriptions; retained handles/Toolhelp only. Short-lived child coverage not claimed.',protectedAccess=False,productionChanged=False)
 put(root/'result.json',out)
 print(json.dumps(dict(status=out['status'],root=str(root),probes=len(probes),samplers=len(queries),allExited=cleanup['allExited'],allHandlesClosed=cleanup['allHandlesClosed'],failure=failure)),flush=True)
sys.exit(bool(failure))
