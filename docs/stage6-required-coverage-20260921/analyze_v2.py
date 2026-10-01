import json,sys,importlib.util,hashlib,collections,ctypes,pathlib
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-durable-kernel-20260921';C=Path(json.loads((R/'candidate-frozen.json').read_text())['code']);root=Path(json.loads((R/'run.json').read_text())['path'])
spec=importlib.util.spec_from_file_location('qualification',P/'qualification.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
sys.path.insert(0,str(C));from process_instances import InstanceTable
import application_authority
O=R/'analysis-v2';O.mkdir()
def save(name,v):
 with (O/name).open('x') as f:json.dump(v,f,indent=2)
def load(n):return q.load(root/n)
mapping={};k32=ctypes.WinDLL('kernel32',use_last_error=True);k32.QueryDosDeviceW.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_ulong];k32.QueryDosDeviceW.restype=ctypes.c_ulong
for drive in ('C:','D:'):
 b=ctypes.create_unicode_buffer(32768)
 if not k32.QueryDosDeviceW(drive,b,len(b)):raise ctypes.WinError(ctypes.get_last_error())
 mapping[drive]=b.value
save('volume-map.json',dict(mapping=mapping,mechanism='QueryDosDeviceW; no protected file access'))
def norm(s):
 s=s.replace('/','\\').lower()
 if s.startswith('\\\\?\\'):s=s[4:]
 for drive,dev in mapping.items():
  if s.startswith(dev.lower()+'\\'):s=drive.lower()+s[len(dev):];break
 return str(pathlib.PureWindowsPath(s))
events,manifest,writer=q.stream(root,'kernel-authority');kernel=load('etw-result.json');ready=load('etw-ready.json');probes=load('identity-probes.json')['rows'];closures=load('identity-handle-closure.json');native=[];handles=[]
q.require(closures['allExited'] and closures['failure'] is None,'HANDLE_CLOSURE_FAILURE')
for p in probes:
 pid=p['pid'];created=p['initialKernelTimes'][0];n=load(f'native-{pid}-{created}.json');native.append(n)
 matches=[r for r in kernel['rows'] if (r['pid'],r['created'])==(pid,created)];q.require(len(matches)==1,'PROBE_UNIQUE_KERNEL_IDENTITY');r=matches[0]
 closed=[h for h in closures['rows'] if h['pid']==pid];q.require(len(closed)==1 and closed[0]['times'][:2]==p['finalKernelTimes'][:2],'INDEPENDENT_CLOSURE_IDENTITY')
 q.require(not p['hardDeadlineFailure'] and not p['independentObserverFailed'] and p['observerResult']==0 and p['finalHandleState']==0,'PROBE_DEADLINE_OR_WAIT')
 q.require(p['finalKernelTimes'][0]==r['created'] and p['finalKernelTimes'][1]==r['exitFiletime'] and p['actualExitCode']==r['exitCode'],'PROBE_HANDLE_CONTRADICTION')
 images=[e['path'] for e in n['events'] if e['event']=='create_process_debug'];q.require(len(images)==1 and norm(images[0])==norm(r['image'])==norm(p['executable']),'EXACT_IMAGE_CONTRADICTION')
 q.require(n['created']==created and n['exitFiletime']==r['exitFiletime'] and n['exitCode']==r['exitCode'] and n['observerResult']==0,'NATIVE_HANDLE_CONTRADICTION')
 q.require(len([e for e in n['events'] if e['event']=='PE_ENTRY_EXECUTED'])==1,'PE_ENTRY_COUNT')
 handles.append(dict(pid=pid,created=created,image=norm(images[0]),exitFiletime=p['finalKernelTimes'][1],exitCode=p['actualExitCode'],exited=closed[0]['exited'],closed=closed[0]['closedQpc']>p['reconciledQpc']))

# Explicit format adapter for supporting CIM correlation ONLY. Raw kernel records remain
# unchanged and are independently subjected to strict acquisition/coverage checks below.
import copy
correlationRows=copy.deepcopy(kernel['rows']);adapted=[]
for row in correlationRows:
 if row.get('handleCreated')=='0':
  q.require(not row['handleRetained'] and row['reason']=='OPEN_PROCESS_FAILED' and row['openError']==87 and row['stopQpc']<row['handleAttemptBeginQpc']<=row['handleAttemptQpc'] and norm(row['image'])=='c:\\windows\\system32\\conhost.exe','INVALID_ABSENT_HANDLE_SENTINEL')
  adapted.append(dict(pid=row['pid'],created=row['created'],field='handleCreated',rawValue='0',adapterValue=None,reason='explicit unavailable handle-query sentinel; strictly qualified post-exit console helper'))
  row['handleCreated']=None
save('format-adaptation.json',adapted)
table=InstanceTable(correlationRows,kernel['session']);cimraw=[json.loads(l) for l in (root/'app-events.jsonl').read_text(encoding='utf-8-sig').splitlines()];cim=[]
for e in cimraw:
 out=table.correlate(e);out['token']=root.name+':'+str(e['queueSequence']);q.require(out['result'] in ('AMBIGUOUS','UNMATCHED') and out['selected'] is None,'FORCED_CIM');cim.append(out)
result=q.qualify(events,kernel,handles,native,cim)
probeIndependentHandles=list(handles)
# Independently verify every parent edge and the declared root, not PID-only ancestry.
byseq={r['sequence']:r for r in kernel['rows']};launcher=load('launcher-identity.json')
q.require(ready['rootPid']==launcher['pid'] and ready['rootCreated']==launcher['created'],'ROOT_IDENTITY')
for r in kernel['rows']:
 if r['parentPid']==launcher['pid']:
  q.require(int(r['created'])>=int(launcher['created']),'ROOT_TIME')
 else:
  parent=byseq.get(r['parentSequence']);q.require(parent and parent['pid']==r['parentPid'] and int(parent['created'])<=int(r['created'])<=int(parent['exitFiletime']),'PARENT_INSTANCE')
launch=load('launcher-result.json');q.require(launch['error'] is None and all(launch[k] is True for k in ('applicationExited','workerExited','kernelExited')) and all(launch[k]==0 for k in ('applicationExit','workerExit','kernelExit')),'LAUNCH_CLEANUP')
app=load('app-result.json');queue=app['queue'];q.require(app['success'] and app['unsubscribed'] and app['durableFinalization'] and not app['error'] and not app['tapErrors'] and not app['tapOverflow'],'CIM_COLLECTOR')
q.require(not queue['failed'] and queue['remaining']==0 and queue['enqueued']==queue['selected']==queue['persisted']==queue['removed']==len(cimraw),'CIM_QUEUE')
receipts=load('app-receipts.json');q.require(len({e['queueSequence'] for e in cimraw})==len(cimraw) and len(receipts)==len(cimraw),'CIM_TOKENS')
for e in cimraw:
 rr=[v for v in receipts if v['queueSequence']==e['queueSequence']];q.require(len(rr)==1 and rr[0]['removed'] and rr[0]['pid']==e['pid'] and rr[0]['kind']==e['kind'] and rr[0]['persistedQpc']>=e['drainedQpc'],'CIM_RECEIPT')
hb=load('app-heartbeats.json');health=load('live-health-checks.json');q.require(hb and health and all(0<=h['interval']<10 for h in hb) and all(0<=h['age']<10 for h in health),'HEARTBEAT')
bridge=load('native-bridge-cleanup.json');q.require(bridge['allThreadsExited'] and not bridge['errors'],'NATIVE_CLEANUP')
appstream=application_authority.verify(root)
result.update(realProbeCount=len(probes),probeCases=dict(collections.Counter(p['case'] for p in probes)),kernelRecords=len(events),kernelSegments=len(manifest['segments']),retained=sum(r['handleRetained'] for r in kernel['rows']),qualifiedPostExit=sum(not r['handleRetained'] for r in kernel['rows']),exactProbeImagesVerified=len(handles),nativeEntriesVerified=len(native),actualPIDReuse=0,actualParentPIDReuse=0,maxHeartbeat=max(h['interval'] for h in hb),maxHeartbeatAge=max(h['age'] for h in health),deadlineViolations=0,applicationAuthority=appstream,queue=queue,writer=writer,run=str(root),combinedAcceptance=False)

from coverage import coverage,identity
declared=load('process-identities.json');wi=load('worker-created.json')
worker=next(d for d in declared if d['role']=='worker');application=next(d for d in declared if d['role']=='application')
q.require(identity(worker)==identity(wi),'WORKER_LAUNCH_IDENTITY')
workerNative=load(f"native-{worker['pid']}-{worker['created']}.json");native.append(workerNative)
probeKeys={identity(h) for h in probeIndependentHandles}
expected=[];handleEvidence=[]
for r in kernel['rows']:
 key=identity(r)
 if key==identity(worker):role='worker';q.require(norm(wi['image'])==norm(r['image']),'WORKER_LAUNCH_IMAGE')
 elif key in probeKeys:role='probe'
 elif key==identity(application):role='infrastructure'
 elif norm(r['image'])=='c:\\windows\\system32\\conhost.exe':role='console'
 else:raise ValueError('UNCLASSIFIED_KERNEL_INSTANCE: '+str(key))
 expected.append(dict(r,role=role,parentVerified=True))
 handleEvidence.append(dict(pid=r['pid'],created=r['created'],handleCreated=r.get('handleCreated'),image=r.get('handleImage',''),imageError=r.get('imageError'),
  retained=r['handleRetained'],exited=r['signalObservedQpc']>0,closed=r['handleClosed'],exitFiletime=r['exitFiletime'],exitCode=r['exitCode'],
  qualifiedPostExit=not r['handleRetained'],reason=r['reason'],openError=r['openError'],attemptBegin=r['handleAttemptBeginQpc'],attemptEnd=r['handleAttemptQpc']))
coverageInputs=dict(expected=expected,events=events,handles=handleEvidence,natives=native,mapping=mapping)
cov=coverage(**coverageInputs)
save('coverage-live-inputs.json',coverageInputs);save('coverage-live-result.json',cov)
result.update(coverage=cov,status=cov['status'],workerNativeEntryVerified=workerNative['entryQpc']>0,realNativeCount=len(native))

save('cim-correlations.json',cim);save('qualification-inputs.json',dict(events=events,kernel=kernel,handles=handles,natives=native,cim=cim));save('qualification-result.json',result)
print(json.dumps({k:v for k,v in result.items() if k not in ('identities','writer','applicationAuthority','queue','coverage')}))

q.require(cov['status']=='PASS','REQUIRED_EVIDENCE_COVERAGE_FAILED')
