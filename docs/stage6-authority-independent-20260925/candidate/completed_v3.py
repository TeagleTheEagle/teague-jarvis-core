"""Completed-evidence verification only; never controls a live observer."""
from coordination_v3 import *
def verify_terminal(root,kernel=None):
 root=pathlib.Path(root);p=load(root/'phase-a-v3.json');r=load(root/'terminal-v3.json')
 c=p['collector'];n=load(root/f"native-{c['pid']}-{c['created']}.json")
 observed=load(root/'terminal-observed-v3.json')
 rows=terminal(p,r,digest(root/'phase-a-v3.json'),observed['observedQpc'],n)
 need(observed['receiptSHA256']==digest(root/'terminal-v3.json'),'RECEIPT_CHANGED')
 for name,sha in p['localEvidence'].items():
  need(pathlib.Path(name).name==name and digest(root/name)==sha,'LOCAL_EVIDENCE_CHANGED')
 if kernel is None:kernel=load(root/'etw-result.json')
 need(kernel['session']==p['binding']['kernelSession'],'FINAL_KERNEL_SESSION')
 for key in ('faults','eventsLost','realtimeBuffersLost','buffersLost','flushResult','stopResult','consumerResult'):
  need(kernel[key]==0,'FINAL_KERNEL_'+key)
 km={identity(x):x for x in kernel['rows']};need(len(km)==len(kernel['rows']),'FINAL_KERNEL_DUPLICATE')
 for key,r in rows.items():
  need(key in km,'FINAL_KERNEL_MISSING');k=km[key]
  for f in ('sequence','parentPid','parentSequence','handleCreated','handleImage','startQpc','stopQpc','signalObservedQpc','exitFiletime','exitCode'):
   need(k[f]==r[f],'FINAL_KERNEL_CONTRADICTION_'+f)
  need(k['handleClosed'] is True,'FINAL_HANDLE_OPEN')
 return p
def verify_complete(root):
 root=pathlib.Path(root)
 for n in ('rejected-v3.json','primary-failure.json','launcher-failure.json'):
  need(not (root/n).exists(),'PRESERVED_FAILURE_'+n)
 p=verify_terminal(root)
 census(p,load(root/'workload-census-v3.json'))
 closure(p,load(root/'external-exits-v3.json'))
 census(p,load(root/'final-census-v3.json'),True)
 tail=load(root/'observer-tail-v3.json')
 need(tail['binding']==p['binding'] and tail['phaseASHA256']==digest(root/'phase-a-v3.json') and tail['sequence']==2 and tail['kind']=='observer-tail','TAIL_BINDING')
 before(p,tail['capturedQpc'])
 k=load(root/'etw-result.json');tm={identity(r):r for r in tail['rows']};km={identity(r):r for r in k['rows']}
 need(set(tm)==set(km),'TAIL_INCOMPLETE')
 for key,r in tm.items():
  for f in ('sequence','stopQpc','signalObservedQpc'):need(r[f]==km[key][f],'TAIL_CONTRADICTION')
 verify_timeline(root,p)
 return p

def verify_timeline(root,p):
 marks=load(root/'integration-launcher.json');by={}
 for row in marks:
  if row['event'] in by:raise Rejected('DUPLICATE_STATE_MARKER')
  by[row['event']]=row
 required=('RUN_ACTIVE','COLLECTOR_LOCAL_FINALIZING','LOCAL_EVIDENCE_FINALIZED_PENDING_EXTERNAL_EXIT','COLLECTOR_EXITED','TERMINAL_EVIDENCE_PENDING','TERMINAL_EVIDENCE_COMPLETE','PRE_SHUTDOWN_WORKLOAD_CENSUS_COMPLETE','OBSERVER_SHUTDOWN_ALLOWED','FINAL_SHUTDOWN')
 need(all(n in by for n in required),'STATE_MARKER_MISSING')
 points=[by[n]['qpc'] for n in required];need(points==sorted(points),'STATE_MARKER_ORDER')
 pre=load(root/'workload-census-v3.json');ex=load(root/'external-exits-v3.json');final=load(root/'final-census-v3.json')
 need(p['completedQpc']<=by['COLLECTOR_EXITED']['qpc'],'LOCAL_PHASE_ORDER')
 need(pre['completedQpc']<=by['OBSERVER_SHUTDOWN_ALLOWED']['qpc']<=ex['observers']['application']['exitQpc'],'EARLY_SHUTDOWN')
 need(ex['observers']['authority']['exitQpc']<=by['FINAL_SHUTDOWN']['qpc']<=ex['launcherExitQpc']<=final['startedQpc']<=final['completedQpc']<p['deadlineQpc'],'FINAL_CENSUS_ORDER')
 return True
