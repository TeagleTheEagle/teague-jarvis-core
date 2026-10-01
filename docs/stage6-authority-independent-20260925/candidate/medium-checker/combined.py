"""Versioned TEST combined adapter. Does not import or modify frozen checker."""
import json,importlib.util,collections
from pathlib import Path
from coverage import coverage,identity
R=Path(__file__).parent
spec=importlib.util.spec_from_file_location('kernel_contract',R/'qualification.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
require=q.require

def read_bundle(root,analysis,host):
 root=Path(root);analysis=Path(analysis)
 require(root.drive.upper()=='D:' and root.parts[1]=='JARVIS-STAGE6-LIVE','LIVE_ROOT')
 events,manifest,writer=q.stream(root,'kernel-authority')
 expected={s['name'] for s in manifest['segments']};actual={p.name for p in root.glob('kernel-authority-*.jsonl')}
 require(actual==expected,'SEGMENT_SET_MISMATCH')
 return dict(root=str(root),events=events,manifest=manifest,writer=writer,kernel=q.load(root/'etw-result.json'),
  structural=q.load(analysis/'qualification-inputs.json'),coverage=q.load(analysis/'coverage-live-inputs.json'),
  qualification=q.load(analysis/'qualification-result.json'),cim=q.load(analysis/'cim-correlations.json'),
  launch=q.load(root/'launcher-result.json'),app=q.load(root/'app-result.json'),bridge=q.load(root/'native-bridge-cleanup.json'),
  hb=q.load(root/'app-heartbeats.json'),health=q.load(root/'live-health-checks.json'),host=q.load(host),
  manifests=dict(authoritative=str(root/'kernel-authority-manifest.json'),sha256=q.sha(root/'kernel-authority-manifest.json')))

def validate(b,*,declaration):
 m,w=b['manifest'],b['writer'];require(len(m['segments'])>=declaration['minimumSegments'],'MULTIPLE_SEGMENTS_REQUIRED')
 require(w['fault']==0 and w['threadsExited'] and w['remaining']==0,'FINALIZER_OR_WRITER_FAILURE')
 require(w['pendingLimit']==2 and 0<=w['peakPending']<=2,'FINALIZER_BACKLOG_LIMIT')
 require(w['peakQueueItems']<=65536 and w['peakQueueBytes']<=67108864,'WRITER_QUEUE_LIMIT')
 require(len(w['segments'])==len(m['segments']),'INCOMPLETE_MANIFEST')
 for a,z in zip(m['segments'],w['segments']):
  require(a['states']==[0,1,2,3,4] and z['states']==[0,1,2,3,4,5],'SEGMENT_STATE')
  require({k:v for k,v in a.items() if k!='states'}=={k:v for k,v in z.items() if k!='states'},'RESULT_MANIFEST_CONFLICT')
 require(w['written']==w['accepted']==w['attempted']==m['accepted']==len(b['events']),'AUTHORITATIVE_TOTAL')
 structural=dict(b['structural'],events=b['events'],kernel=b['kernel'],cim=b['cim'])
 kr=q.qualify(**structural)
 c=dict(b['coverage'],events=b['events']);expected=c['expected']
 canonical=lambda x:(int(x['pid']),str(x['created']),str(x['sequence']))
 require({canonical(x) for x in expected}=={canonical(x) for x in b['kernel']['rows']} and len(expected)==len(b['kernel']['rows']),'REQUIRED_INVENTORY_MISMATCH')
 classes=collections.Counter(x['role'] for x in expected)
 require(classes['DIRECT_PROBE']==declaration['directProbes'] and classes['DIRECT_WORKER']==declaration['directWorkers'],'DECLARED_WORKLOAD_MISSING')
 cv=coverage(**c);require(cv['status']=='PASS' and cv['missingRequired']==cv['contradictory']==0 and cv['verifiedIdentities']==cv['requiredIdentities'],'INDEPENDENT_VERIFICATION_FAILURE')
 launch=b['launch'];require(launch['error'] is None and all(launch[k] is True for k in ('applicationExited','workerExited','kernelExited')) and all(launch[k]==0 for k in ('applicationExit','workerExit','kernelExit')),'CLEANUP_FAILURE')
 a=b['app'];cq=a['queue'];require(a['success'] and a['unsubscribed'] and a['durableFinalization'] and not a['error'] and not a['tapErrors'] and not a['tapOverflow'],'SECONDARY_COLLECTOR_FAILURE')
 require(not cq['failed'] and cq['remaining']==0 and cq['enqueued']==cq['selected']==cq['persisted']==cq['removed']==len(b['cim']),'SECONDARY_QUEUE_FAILURE')
 require(b['bridge']['allThreadsExited'] and not b['bridge']['errors'],'NATIVE_CLEANUP_FAILURE')
 require(b['hb'] and b['health'] and all(0<=h['interval']<10 for h in b['hb']) and all(0<=h['age']<10 for h in b['health']),'HEARTBEAT_FAILURE')
 aa=b['qualification']['applicationAuthority']
 require(b['qualification']['status']=='PASS' and b['qualification']['deadlineViolations']==0 and aa['records']>0 and aa['sequenceGaps']==0 and bool(aa['manifestSHA256']),'QUALIFICATION_FAILURE')
 require(b['host']['status']=='PASS' and b['host']['matchingProcessCount']==b['host']['diagnosticTraceCount']==0,'HOST_CLEANUP_FAILURE')
 helper=[x for x in cv['identities'] if x['role']=='OS_CONSOLE_HELPER'];post=sum(x['qualifiedPostExit'] for x in helper)
 return dict(schema='stage6-medium-combined-v1',run=b['root'],contract='STAGE6-TEST-KERNEL-INSTANCE-20260921-v1 + owner creator/helper clarification',
  verificationStatus='PASS',acceptanceSealed=False,archiveStatus='PENDING',
  identitySchema=['captureScope','pid','creationFiletime','kernelProcessSequence'],
  authoritative=dict(records=len(b['events']),starts=kr['starts'],stops=kr['stops'],canonicalIdentities=kr['unique'],falseUnique=kr['falseUnique'],ambiguity=kr['authoritativeAmbiguous'],identities=kr['identities']),
  durable=dict(segments=len(m['segments']),first=m['segments'][0]['first'],last=m['segments'][-1]['last'],gaps=0,duplicates=0,missing=0,failed=0,hashes='PASS',manifest=b['manifests'],segmentManifest=m,finalizerHighWater=w['peakPending'],writerHighWater=w['peakQueueItems'],writerHighWaterBytes=w['peakQueueBytes'],maxFlushSeconds=w['maxFlushSeconds'],progressWhileFinalizing=w['progressedWhileFinalizing']),
  verification=dict(classes=dict(classes),coverage=cv,creatorImages=classes['DIRECT_PROBE']+classes['DIRECT_WORKER'],tracerHelperSuccess=len(helper)-post,qualifiedPostExitHelpers=post,failedHelpers=0,nativeEntries=b['qualification']['realNativeCount']),
  secondary=dict(counts=dict(collections.Counter(x['result'] for x in b['cim'])),persisted=len(b['cim']),queue=cq,authority=False),
  health=dict(maxHeartbeat=max(h['interval'] for h in b['hb']),maxAge=max(h['age'] for h in b['health']),deadlineViolations=0,observers='CLOSED',writer='CLOSED',finalizer='CLOSED'),
  finalization=dict(authoritativeQueue='DRAINED',finalizerQueue='DRAINED',allSegments='HASH_VERIFIED_AND_MANIFESTED',secondaryQueue='DRAINED',kernelTrace='CLOSED',nativeThreads='CLOSED',cleanup=b['host']))
