"""Read-only post-run measurements; never invokes an acceptance checker/finalizer."""
import pathlib,json,hashlib,zipfile
R=pathlib.Path(__file__).parent
P=R.parent/'stage6-helper-handoff-v1-20260923'
v=json.loads((R/'preflight-result.json').read_text());C=pathlib.Path(v['candidate']);root=pathlib.Path(v['runRoot'])
pres=C.parent/'preservation-v4'/('FAILURE-EVIDENCE-'+v['run'])
def read(n):return json.loads((root/n).read_text(encoding='utf-8-sig'))
def sha(p):
 with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(n,x):
 with (R/n).open('x',encoding='utf8') as f:json.dump(x,f,indent=2)
origin=read('cleanup-origin-v3.json');freq=10000000;start=origin['cleanupEntryQpc'];end=origin['deadlineQpc'];assert end-start==20*freq
o=read('helper-handoff-obligations-v1.json');a=read('helper-handoff-acquired-v1.json');obs=read('helper-handoff-observed-v1.json');phase=read('phase-a-v3.json');tree=read('tree-handles.json');kernel=read('etw-result.json');detail=read('detail/etw-result.json')
assert a['obligationsSHA256']==sha(root/'helper-handoff-obligations-v1.json')==obs['obligationsSHA256']
assert obs['acquiredSHA256']==sha(root/'helper-handoff-acquired-v1.json')
assert o['binding']==a['binding']==obs['binding'] and o['binding']['run']==v['run']
assert o['binding']['workspaceBindingSHA256']==v['workspaceBindingSHA256']
measure=[]
for h in a['helpers']:
 local=next(x for x in tree['rows'] if (x['pid'],x['created'])==(h['pid'],h['created']))
 kr=next(x for x in kernel['rows'] if (x['pid'],x['created'],x['sequence'])==(h['pid'],h['created'],h['sequence']))
 assert kr['handleIdentity']==h['handleIdentity'] and kr['handleCreated']==h['created'] and kr['handlePid']==h['pid']
 assert kr['parentSequence']==h['parent']['sequence'] and kr['handleImage']==h['handleImage']
 assert kr['imageStateBefore']==kr['imageStateAfter']==258
 assert h['verificationQpc']<a['preparedQpc']<obs['observedQpc']<local['localCloseQpc']<local['localCloseReturnedQpc']<end
 times={k:h[k] for k in ('acquisitionBeginQpc','acquisitionReturnQpc','creationVerifiedQpc','imageBeginQpc','imageEndQpc','verificationQpc')}
 times.update(cleanupEntryQpc=start,obligationPreparedQpc=o['preparedQpc'],acquiredPreparedQpc=a['preparedQpc'],observedQpc=obs['observedQpc'],localCloseQpc=local['localCloseQpc'],localCloseReturnedQpc=local['localCloseReturnedQpc'],phaseACompletedQpc=phase['completedQpc'],helperKernelStopQpc=kr['stopQpc'],helperHandleSignalObservedQpc=kr['signalObservedQpc'])
 measure.append(dict(pid=h['pid'],created=h['created'],sequence=h['sequence'],parent=h['parent'],timingsQpc=times,secondsRelativeToCleanup={k:(x-start)/freq for k,x in times.items()},verifiedMinusCloseMilliseconds=(h['verificationQpc']-local['localCloseQpc'])/freq*1000,verificationLeadMilliseconds=(local['localCloseQpc']-h['verificationQpc'])/freq*1000,acquisitionLeadMilliseconds=(local['localCloseQpc']-h['acquisitionReturnQpc'])/freq*1000,receiptPublicationQpc='UNKNOWN; prepared before publication; complete before observedQpc',obligationPublicationQpc='UNKNOWN; prepared before publication; read by authority before receipt preparation',orderingObservation='CONSISTENT; not acceptance because authoritative trace loss occurred'))
telemetry={}
for channel,prefix,result in [('authority','',kernel),('detail','detail/',detail)]:
 d=read(prefix+'loss-diagnostic-v2.json');t=read(prefix+'loss-telemetry.json');unavailable=[s for s in d['samples'] if s.get('eventsLost') is None];samples=[s for s in d['samples'] if s.get('eventsLost') is not None];prev=None;increments=[]
 for s in samples:
  if s['eventsLost']>(prev['eventsLost'] if prev else 0):increments.append(dict(previousQpc=prev['endQpc'] if prev else None,observedQpc=s['endQpc'],increment=s['eventsLost']-(prev['eventsLost'] if prev else 0),cumulative=s['eventsLost']))
  prev=s
 near=[]
 if increments:
  lo=increments[0]['previousQpc'];hi=increments[-1]['observedQpc']
  for i,s in enumerate(samples):
   if lo-freq<=s['endQpc']<=hi+freq:
    dt=(s['endQpc']-samples[i-1]['endQpc'])/freq if i else None
    near.append(dict(qpc=s['endQpc'],eventsLost=s['eventsLost'],freeBuffers=s['freeBuffers'],numberOfBuffers=s['numberOfBuffers'],callbacksCompleted=s['callbackDelta'],callbacksReceived=s['receivedDelta'],completedPerSecond=s['callbackDelta']/dt if dt else None,receivedPerSecond=s['receivedDelta']/dt if dt else None,consumerCpuDeltaMs=(s['cpu100ns']-samples[i-1]['cpu100ns'])/10000 if i else None,activeCallbackQpc=s['activeCallbackQpc'],deliveryLagMaxMs=s['deliveryLag']['maxTicks']/freq*1000,queue=s['queue']))
  spans=[dict(**x,durationMs=(x['endQpc']-x['beginQpc'])/freq*1000) for x in d['slowSpans'] if x['beginQpc']<=hi+freq and x['endQpc']>=lo-freq]
 else:spans=[]
 telemetry[channel]=dict(eventsLost=result['eventsLost'],faults=result['faults'],realtimeBuffersLost=result['realtimeBuffersLost'],buffersLost=result['buffersLost'],minFreeBuffers=min(s['freeBuffers'] for s in samples),maxNumberOfBuffers=max(s['numberOfBuffers'] for s in samples),lossIncrements=increments,nearLoss=near,slowSpansNearLoss=spans,totalCallbacks=t['callbacks'],maxCallbackMs=t['metrics']['callback']['maxTicks']/freq*1000,maxDeliveryLagMs=max(s['deliveryLag']['maxTicks'] for s in samples)/freq*1000,queueHighItems=d['queueHighItems'],queueHighBytes=d['queueHighBytes'],finalQueue=d['finalQueue'],diagnosticErrors=d['errors'],diagnosticOverflow=d['overflow'],unavailableCounterSamples=[{k:s.get(k) for k in ('sequence','beginQpc','endQpc','status','eventsLost')} for s in unavailable],configuration=d['configuration'])
pm=json.loads((pres/'FAILURE-MANIFEST.json').read_text());pr=json.loads((pres/'preservation-result.json').read_text());zpath=next(pres.glob('*.zip'))
assert sha(zpath)==pr['archiveSHA256'] and sha(pres/'FAILURE-MANIFEST.json')==pr['manifestSHA256']
with zipfile.ZipFile(zpath) as z:
 assert len(z.namelist())==pr['verifiedArchiveMembers']==len(set(z.namelist()))
 for row in pm['preserved']:
  with z.open('evidence/'+row['path']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
  assert sha(root/row['path'])==row['sha256']
pass1=read('hash-pass-1.json');pass2=read('hash-pass-2.json');assert pass1['files']==pass2['files']
for row in json.loads((C/'small-source-v3.json').read_text()):assert sha(C/row['name'])==row['sha256']
assert sha(C/'small-source-v3.json')==v['sourceManifestSHA256']
for row in json.loads((P/'before.json').read_text())['inputs']:
 p=pathlib.Path(row['path']);s=p.stat();assert (s.st_size,s.st_mtime_ns,sha(p))==(row['bytes'],row['mtimeNs'],row['sha256'])
for row in v['dataset']:
 p=C/row['name'];assert (p.stat().st_mtime_ns,sha(p))==(row['mtimeNs'],row['sha256'])
marks=read('integration-launcher.json');collector=next(x for x in kernel['rows'] if x['pid']==o['collector']['pid'] and x['created']==o['collector']['created'])
summary=dict(status='TRACE_DIAGNOSTIC_RUN_FAILED',run=v['run'],firstRecordedRejection=read('rejected-v3.json'),terminalFailure=read('terminal-failure-v3.json'),historicalTraceLossCause='UNCONFIRMED',handoff=measure,telemetry=telemetry,hashPasses=dict(files=12,bytes=786432,match=True,metadataUnchanged=True,durationsSeconds=[(x['endQpcNs']-x['beginQpcNs'])/1e9 for x in (pass1,pass2)]),maximumHeartbeatSeconds=max(x['interval'] for x in read('app-heartbeats.json')),collectorKernelExitQpc=collector['stopQpc'],launcherMilestones=marks,failureShutdownSeconds=(next(x['qpc'] for x in marks if x['event']=='FINAL_SHUTDOWN')-start)/freq,terminalReceipt='NOT PRODUCED',preShutdownCensus='NOT PRODUCED',successObserverShutdown='NOT COMPLETED; failure-only shutdown used',acceptanceFinalCensus='NOT PRODUCED',postFailureCensus=json.loads((R/'final-census.json').read_text()),failureCensusSeconds=(pm['censusAfterLocks']['completedQpc']-start)/freq,checker='NOT INVOKED',successFinalizer='NOT INVOKED',failureArchive=dict(status=pr['status'],verifiedMembers=pr['verifiedArchiveMembers'],sha256=pr['archiveSHA256'],missingAcceptanceArtifacts=pm['missingArtifacts'],allExistingRunFilesPreserved=len(pm['preserved'])==pm['existingFileCount'],recordedIdentities=pm['recordedInstanceCensus']['knownInstanceCount'],cleanupProven=pm['cleanupProven']),preservation=dict(candidateFiles=235,priorInputs=334,sourceManifestSHA256=sha(C/'small-source-v3.json'),frozenCheckerSHA256=sha(C/'medium-checker/frozen_reference.py'),protectedAccess=False,productionChange=False),retry=False)
write('measurements.json',summary)
print(json.dumps(dict(status=summary['status'],handoffLeadMs=measure[0]['verificationLeadMilliseconds'],acquisitionLeadMs=measure[0]['acquisitionLeadMilliseconds'],failureShutdownSeconds=summary['failureShutdownSeconds'],failureCensusSeconds=summary['failureCensusSeconds'],loss={k:x['eventsLost'] for k,x in telemetry.items()},maxHeartbeat=summary['maximumHeartbeatSeconds'],archiveMembers=pr['verifiedArchiveMembers'])))
