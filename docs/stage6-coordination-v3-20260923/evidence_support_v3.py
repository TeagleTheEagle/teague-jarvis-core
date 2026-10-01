"""Versioned TEST tracker: only exact collector-associated console helpers may pend."""
import pathlib,time,json,os
import evidence_support as previous
from evidence_support import K,times,image,Managed,Ledger
from journal import ticks,frequency
from coordination_v3 import write_once,need,norm,digest,SCHEMA,before

class TreeTracker(previous.TreeTracker):
 def __init__(self,collector_anchor=False,run_root=None):
  super().__init__(collector_anchor=collector_anchor,run_root=None)
  if run_root is not None:
   try:
    from tracker_adapter_v3 import binding
    self.runBinding=binding(run_root,self.anchor['pid'],self.anchor['created'])
   except BaseException:
    self.stop.set();self.thread.join(2)
    if self.anchorHandle and not self.thread.is_alive():K.CloseHandle(self.anchorHandle);self.anchorHandle=None
    raise
 def eligible(self,r):
  return bool(self.anchor and r['parentPid']==self.anchor['pid'] and r['role'].startswith('descendant:') and r.get('imageCapture',{}).get('valid') is True and norm(r['image'])==r'c:\windows\system32\conhost.exe')
 def finish(self,root,seconds=20):
  need(seconds==20,'FIXED_CLEANUP_BUDGET');root=pathlib.Path(root)
  entry=ticks();end=entry+20*frequency()
  write_once(root/'cleanup-origin-v3.json',dict(cleanupEntryQpc=entry,deadlineQpc=end,frequency=frequency()))
  while ticks()<end:
   self.scan()
   if all(r['signalObservedQpc'] is not None or self.eligible(r) for r in self.snapshot()):break
   time.sleep(.02)
  self.stop.set();self.thread.join(max(0,min(2,(end-ticks())/frequency())))
  need(not self.thread.is_alive(),'TRACKER_JOIN')
  with self.lock:
   for key,h in self.handles.items():
    r=self.rows[key]
    if r['signalObservedQpc'] is None:need(self.eligible(r),'NON_HELPER_PENDING')
    r['stateAtClose']=int(K.WaitForSingleObject(h,0))
    if r['stateAtClose']==0 and r['signalObservedQpc'] is None:
     ts=times(h);code=previous.w.DWORD();need(K.GetExitCodeProcess(h,previous.c.byref(code)) and ts[0]==r['created'],'LATE_LOCAL_SIGNAL_IDENTITY')
     r.update(signalObservedQpc=ticks(),exitFiletime=ts[1],exitCode=code.value)
    r['localCloseQpc']=ticks()
    r['closed']=bool(K.CloseHandle(h));need(r['closed'],'LOCAL_CLOSE')
   rows=self.snapshot()
  need(rows and not self.errors and ticks()<end,'LOCAL_FAILURE_OR_DEADLINE')
  state=int(K.WaitForSingleObject(self.anchorHandle,0));self.anchor['stateAtClose']=state
  self.anchor['closeQpc']=ticks();self.anchor['closed']=bool(K.CloseHandle(self.anchorHandle));self.anchorHandle=None
  need(state==258 and self.anchor['closed'],'ANCHOR_CLOSE')
  descendants=[dict(pid=r['pid'],created=r['created'],parentPid=r['parentPid'],capture=r['imageCapture'],closed=r['closed'],exitFiletime=r['exitFiletime'],exitCode=r['exitCode'],localCloseQpc=r['localCloseQpc'],stateAtClose=r['stateAtClose'],eligibleConsoleHelper=self.eligible(r)) for r in rows]
  from tracker_adapter_v3 import binding
  self.runBinding=binding(root,self.anchor['pid'],self.anchor['created'])
  doc=dict(binding=self.runBinding,schema='stage6-independent-tree-support-v3',supportingOnly=True,kernelQualification='NOT_PERFORMED',anchor=self.anchor,descendants=descendants,capacity=self.capacity,errors=self.errors,valid=True)
  write_once(root/'tree-image-support.json',doc)
  result=dict(rows=rows,errors=[],threadStopped=True,allExited=all(r['signalObservedQpc'] is not None for r in rows),allHandlesClosed=True,supportingEvidenceValid=True,localFinalized=True,cleanupEntryQpc=entry,deadlineQpc=end,qpc=ticks(),scanCount=self.scans,maxScanSeconds=self.maxScan)
  write_once(root/'tree-handles.json',result);return result

def publish_phase_a(root):
 """Called only after wrapper FINAL_SHUTDOWN and bridge cleanup are written."""
 root=pathlib.Path(root);load=lambda n:json.loads((root/n).read_text())
 need(not (root/'primary-failure.json').exists(),'PRESERVED_FAILURE')
 tree=load('tree-image-support.json');proof=load('tree-handles.json');obs=load('observer-identities.json')
 bridge=load('native-bridge-cleanup.json');need(bridge['allThreadsExited'] and not bridge['errors'],'BRIDGE_CLOSURE')
 marks=list(root.glob('integration-collector-*.json'));need(len(marks)==1,'COLLECTOR_MARKERS')
 m=json.loads(marks[0].read_text());need(m[-1]['event']=='FINAL_SHUTDOWN' and m[-1]['status']=='RETURNED','COLLECTOR_FAILURE')
 anchor=tree['anchor'];collector=dict(pid=anchor['pid'],created=anchor['created'],image=anchor['capture']['image'])
 helpers=[]
 for r in tree['descendants']:
  if r['eligibleConsoleHelper']:
   helpers.append(dict(pid=r['pid'],created=r['created'],image=r['capture']['image'],role='OS_CONSOLE_HELPER',parent=collector,localClosed=r['closed'],localCloseQpc=r['localCloseQpc'],stateAtClose=r['stateAtClose']))
 # Flush every collector-owned evidence file, not live external observer files.
 local=['tree-image-support.json','tree-handles.json','stress-result.json','collector-health-samples.json','probe-timings.json','retained-handle-verification.json','native-bridge-cleanup.json',marks[0].name]
 local += [p.name for p in root.glob('native-*.json') if p.name not in local]
 local += [p.name for p in root.glob('early-image-*.json')]
 local += [p.name for pattern in ('hash-*.json','hash-*.bin','hash-*.bin.json','integration-hash-worker-*.json','integration-sampler-*.json','sampler-results.json','metadata-verified.json','state.json','workload-stop') for p in root.glob(pattern) if p.name not in local]
 local=list(dict.fromkeys(local))
 for name in local:
  with (root/name).open('r+b',buffering=0) as f:os.fsync(f.fileno())
 b=dict(tree['binding']);b.pop('producer');b['schema']=SCHEMA
 phase=dict(binding=b,state='LOCAL_EVIDENCE_FINALIZED_PENDING_EXTERNAL_EXIT',collector=collector,authorityObserver=obs['etw'],helpers=helpers,cleanupEntryQpc=proof['cleanupEntryQpc'],deadlineQpc=proof['deadlineQpc'],admissionsStopped=True,localDurable=True,trackerStopped=True,localHandlesClosed=True,cleanupPass=False,acceptance=False,localEvidence={n:digest(root/n) for n in local},completedQpc=ticks())
 from coordination_v3 import phase_a
 phase_a(phase);write_once(root/'phase-a-v3.json',phase)

def close_bridge_v3(root,bridge):
 """Same native bridge closure, intersect its existing 2s join with cleanup budget."""
 import _winapi
 _winapi.CreateProcess=bridge.original;bridge.sampler.K.CreateProcessW=bridge.originalSampler
 origin=pathlib.Path(root)/'cleanup-origin-v3.json'
 end=time.monotonic()+2
 if origin.exists():
  v=json.loads(origin.read_text());need(v['frequency']==frequency() and v['deadlineQpc']==v['cleanupEntryQpc']+20*frequency(),'BRIDGE_DEADLINE')
  end=min(end,time.monotonic()+max(0,(v['deadlineQpc']-ticks())/frequency()))
 for t in bridge.threads:t.join(max(0,end-time.monotonic()))
 result=dict(threadCount=len(bridge.threads),allThreadsExited=all(not t.is_alive() for t in bridge.threads),createdPids=bridge.created,errors=bridge.errors)
 write_once(pathlib.Path(root)/'native-bridge-cleanup.json',result)
 need(result['allThreadsExited'] and not result['errors'],'NATIVE_BRIDGE_CLEANUP')
