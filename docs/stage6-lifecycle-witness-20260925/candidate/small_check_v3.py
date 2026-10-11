"""Strict small integration qualifier. No large/protected acceptance claim."""
import sys,json,ctypes,pathlib,hashlib,collections
from workspace import CODE,run_dir
sys.path.insert(0,str(CODE/'medium-checker'))
import qualification as q,telemetry,application_authority
from small_coverage_v2 import coverage,identity,normalize
from small_binding_v3 import validate
from trace_segments import verify as trace_verify
from process_instances import InstanceTable
from journal import Reader,frequency

def check(root):
 from completed_v3 import verify_complete
 phase=verify_complete(root)
 load=lambda n:q.load(root/n)
 d=validate(root,load('small-declaration-v3.json'));normal=d['case']=='normal'
 launch=load('launcher-result.json')
 q.require(launch['error'] is None and all(launch[x] is True for x in ('applicationExited','detailExited','kernelExited')) and all(launch[x]==0 for x in ('applicationExit','detailExit','kernelExit')),'OBSERVER_CLEANUP')
 q.require((launch['workExit']==0) if normal else (launch['workExit']==1),'COLLECTOR_STATUS')
 kernel=load('etw-result.json');detail=load('detail/etw-result.json')
 for field in ('faults','eventsLost','realtimeBuffersLost','buffersLost','flushResult','stopResult','consumerResult'):q.require(detail[field]==0,'DETAIL_'+field)
 q.require(detail['requestedStop'],'DETAIL_NOT_CLOSED')
 detailed=trace_verify(root/'detail');q.require(detailed['records']>0,'EMPTY_DETAIL')
 detail_ids={(x['pid'],x['created']) for x in detail['rows']}
 events,manifest,writer=q.stream(root,'kernel-authority');measurements=telemetry.verify(root)
 observations=load('observer-identities.json');launcher=load('launcher-identity.json')
 mapping={};k=ctypes.WinDLL('kernel32',use_last_error=True)
 for drive in ('C:','D:'):
  b=ctypes.create_unicode_buffer(32768);q.require(k.QueryDosDeviceW(drive,b,len(b))>0,'VOLUME_MAP');mapping[drive]=b.value
 norm=lambda s:normalize(s,mapping)
 roles={};collector_marks=list(root.glob('integration-collector-*.json'));q.require(len(collector_marks)==1,'COLLECTOR_MARKERS')
 cm=q.load(collector_marks[0]);q.require(cm[0]['event']=='ENTRY' and cm[-1]['event']=='FINAL_SHUTDOWN','COLLECTOR_MARKER_CLOSURE')
 collector=identity(cm[0]);roles[collector]='DIRECT_WORKER'
 worker=load('hash-worker-cleanup.json');roles[identity(worker)]='DIRECT_WORKER'
 q.require(worker['parentHandleClosed'] and worker['handleState']==0 and all(worker[x]['eof'] and not worker[x]['error'] for x in ('stdout','stderr')),'HASH_WORKER_CLEANUP')
 sampler=load('sampler-results.json');q.require(sampler['threadExited'] and sampler['queries'],'SAMPLER_NOT_EXERCISED')
 for s in sampler['queries']:
  q.require(s.get('allExited') and s.get('handleClosed') and not s.get('cleanupObservationTimedOut'),'SAMPLER_CLEANUP')
  roles[identity(s)]='DIRECT_WORKER'
 probes=load('probe-timings.json');q.require(probes,'PROBES_NOT_EXERCISED')
 for p in probes:
  q.require(not p['hardDeadlineFailure'] and not p['independentObserverFailed'] and p['observerResult']==p['finalHandleState']==p['actualExitCode']==0,'PROBE_FAILURE')
  roles[(p['pid'],p['initialKernelTimes'][0])]='DIRECT_PROBE'
 roles[identity(observations['app'])]='APPLICATION_OBSERVER';roles[identity(observations['detail'])]='DETAIL_OBSERVER'
 expected=[];handles=[];native=[];retained=[];byseq={r['sequence']:r for r in kernel['rows']}
 for r in kernel['rows']:
  key=identity(r)
  if r['parentPid']==launcher['pid']:parent=int(r['created'])>=int(launcher['created'])
  else:
   p=byseq.get(r['parentSequence']);parent=bool(p and p['pid']==r['parentPid'] and int(p['created'])<=int(r['created'])<=int(p['exitFiletime']))
  q.require(parent,'PARENT_INSTANCE')
  role=roles.get(key)
  if role is None:
   q.require(norm(r['image'])=='c:\\windows\\system32\\conhost.exe','UNKNOWN_HELPER');role='OS_CONSOLE_HELPER'
  expected.append(dict(r,role=role,parentVerified=parent))
  if role in ('DIRECT_WORKER','DIRECT_PROBE'):
   q.require(key in detail_ids,'DIRECT_MISSING_DETAILED_TRACE')
   n=load(f"native-{r['pid']}-{r['created']}.json");native.append(n)
   ep=root/f"early-image-{r['pid']}-{r['created']}.json";e=q.load(ep)
   q.require(identity(e)==key and norm(e['image'])==norm(r['image']),'EARLY_IMAGE_BINDING')
   h=dict(e,retained=True,exited=n['finalWait']==0,closed=True,exitFiletime=n['exitFiletime'],exitCode=n['exitCode'],identityPersistedQpc=n['identityPersistedQpc'],evidenceSHA256=q.sha(ep));handles.append(h)
   retained.append(dict(pid=r['pid'],created=r['created'],image=e['image'],exited=n['finalWait']==0,closed=True,exitFiletime=n['exitFiletime'],exitCode=n['exitCode']))
  else:
   handles.append(dict(pid=r['pid'],created=r['created'],handleCreated=r['handleCreated'],image=r['handleImage'],imageError=r['imageError'],source='tracer-opened-handle',queryBeginQpc=r['imageBeginQpc'],queryEndQpc=r['imageEndQpc'],retained=r['handleRetained'],exited=r['signalObservedQpc']>0,closed=r['handleClosed'],exitFiletime=r['exitFiletime'],exitCode=r['exitCode'],qualifiedPostExit=not r['handleRetained'],reason=r['reason'],openError=r['openError'],attemptBegin=r['handleAttemptBeginQpc'],attemptEnd=r['handleAttemptQpc']))
 q.require(set(roles).issubset({identity(r) for r in expected}),'DECLARED_PROCESS_MISSING')
 from tracker_adapter_v3 import adapt
 handles=adapt(root,expected,handles,kernel,mapping,collector)
 cov=coverage(expected,events,handles,native,mapping);q.require(cov['status']=='PASS','EVIDENCE_COVERAGE: '+str(cov['errors']))
 app=load('app-result.json');q.require(app['success'] and app['unsubscribed'] and app['durableFinalization'] and not app['error'],'APPLICATION_FINALIZATION')
 queue=app['queue'];q.require(not queue['failed'] and queue['remaining']==0 and queue['enqueued']==queue['selected']==queue['persisted']==queue['removed'],'QUEUE_CLOSURE')
 supporting=application_authority.verify(root);_,cimraw,receipts=application_authority.load_inputs(root)
 q.require(len(cimraw)==len(receipts)==queue['persisted'],'CIM_COUNT')
 import copy
 supporting_rows=copy.deepcopy(kernel['rows'])
 for r in supporting_rows:
  if r.get('handleCreated')=='0':
   q.require(not r['handleRetained'] and r['openError']==87 and r['stopQpc']<r['handleAttemptBeginQpc']<=r['handleAttemptQpc'] and norm(r['image'])=='c:\\windows\\system32\\conhost.exe','INVALID_HANDLE_SENTINEL')
   r['handleCreated']=None
 table=InstanceTable(supporting_rows,kernel['session']);cim=[table.correlate(e) for e in cimraw]
 result=q.qualify(events,kernel,retained,native,cim)
 q.require(load('native-bridge-cleanup.json')['allThreadsExited'] and not load('native-bridge-cleanup.json')['errors'],'NATIVE_BRIDGE_CLOSURE')
 tree=load('tree-handles.json');q.require(tree['localFinalized'] and tree['allHandlesClosed'] and tree['threadStopped'],'TREE_LOCAL_CLOSURE')
 hb=load('app-heartbeats.json');q.require(hb and all(0<=h['interval']<10 for h in hb),'HEARTBEAT')
 ready=load('app-ready.json');ident=dict(run=root.name,pid=ready['pid'],created=ready['created'],frequency=frequency())
 journal=Reader(root/'app-health.jsonl',ident,lambda:0,None)
 try:
  # Offline structural closure, not a replacement for live health observations.
  journal.clock=lambda: journal.last['ticks'] if journal.last else ready['qpc']
  journal.poll();q.require(not journal.pending,'PARTIAL_FINAL_HEALTH')
 finally:journal.close()
 if normal:
  one=load('hash-pass-1.json');two=load('hash-pass-2.json');meta=load('metadata-verified.json')
  q.require(one['files']==two['files'] and meta['files']==12 and meta['bytes']==786432,'HASH_OR_METADATA')
  q.require(load('state.json')['phase']=='WORKLOAD_CLOSED','WORKFLOW_CLOSURE')
 else:
  q.require(not (root/'metadata-verified.json').exists() and (root/'primary-failure.json').exists(),'CONTROLLED_FAILURE_NOT_REJECTED')
  q.require(b'CONTROLLED_HASH_START_FAILURE' in (root/'hash-worker-stderr.bin').read_bytes(),'WRONG_FAILURE')
 return dict(status='SMALL_NORMAL_PASS_PENDING_ARCHIVE' if normal else 'CONTROLLED_FAILURE_REJECTED_PENDING_ARCHIVE',run=root.name,identities=result['unique'],starts=result['starts'],stops=result['stops'],cim=result['cim'],coverage=cov,detail=detailed,writerTelemetry=measurements,queue=queue,maxHeartbeat=max(h['interval'] for h in hb),samplerQueries=len(sampler['queries']),probes=len(probes),supporting=supporting,largeEligible=False)
if __name__=='__main__':
 root=run_dir(sys.argv[1]);result=check(root)
 with (root/'small-check-result-v3.json').open('x') as f:json.dump(result,f,indent=2)
 print(result['status'])
