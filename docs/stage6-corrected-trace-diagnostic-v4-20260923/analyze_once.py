"""Read-only post-run analysis; cannot launch, retry, finalize or alter a run."""
import pathlib,json,hashlib,sys,importlib.util,collections,statistics,os
R=pathlib.Path(__file__).parent;P=R.parent/'stage6-path-filter-fix-20260923';pre=json.loads((P/'preflight.json').read_text());C=pathlib.Path(pre['candidate']);root=pathlib.Path(pre['root'])
pres=pathlib.Path(pre['preservationDestination'])/('FAILURE-EVIDENCE-'+root.name)
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(n,v):
 with (R/n).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.flush();os.fsync(f.fileno())
sys.path.insert(0,str(C));import failure_preserve_v4 as fp;import workspace_binding_v4 as b
census=fp.host_census(root);write('final-census.json',census)
assert census['available'] and census['processes']==[] and census['traces']==[] and census['unknown']==[]
receipt=read(pres/'preservation-result.json');archive=next(pres.glob('*.zip'));verified=fp.verify_archive(archive,(pres/'FAILURE-MANIFEST.json').read_bytes());write('failure-archive-independent-verification.json',verified)
assert sha(archive)==receipt['archiveSHA256'] and sha(pres/'FAILURE-MANIFEST.json')==receipt['manifestSHA256']
assert not (root/'v3-seal.json').exists() and not (root/'v3-archive-receipt.json').exists()
before=read(P/'candidate-before.json')
for x in before:
 p=pathlib.Path(x['path']);s=p.stat();assert(s.st_size,s.st_mtime_ns,sha(p))==(x['bytes'],x['mtimeNs'],x['sha256'])
assert sha(C/'small-source-v3.json')==pre['manifestSHA256'] and sha(root/b.NAME)==pre['bindingSHA256']
b.runtime_policy();b.verify(root,check_environment=False)
old=R.parent/'stage6-workspace-binding-v4-20260923';original=read(old/'before.json')
for x in original['inputs']:
 p=pathlib.Path(x['path']);s=p.stat();assert(s.st_size,s.st_mtime_ns,sha(p))==(x['bytes'],x['mtimeNs'],x['sha256'])
prior=pathlib.Path(original['predecessor']).parent/'verify_preservation.py';exec(compile(prior.read_text().split('result=')[0],str(prior),'exec'),{'__file__':str(prior)})
mod=R.parent/'stage6-loss-telemetry-v2-20260923/diagnostic_review.py';spec=importlib.util.spec_from_file_location('readonly_diagnostic_review',mod);review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
sessions={}
for channel,base in (('authority',root),('detail',root/'detail')):
 d=read(base/'loss-diagnostic-v2.json');ready=read(base/'etw-ready.json');final=read(base/'etw-result.json');hz=d['frequency'];samples=d['samples'];good=[s for s in samples if s['status']==0]
 assert final['session']==ready['session']==d['session']
 try:qualification=review.verify(d,run=root.name,session=ready['session'],channel=channel,frequency=ready['frequency'])
 except Exception as exc:qualification=dict(telemetryValid=False,error=type(exc).__name__+': '+str(exc))
 transitions=[];previous=0;lastzero=None
 for s in good:
  if s['eventsLost']==0:lastzero=s['sequence']
  if s['eventsLost']!=previous:
   transitions.append(dict(sequence=s['sequence'],beginQpc=s['beginQpc'],endQpc=s['endQpc'],previous=previous,current=s['eventsLost'],secondsFromOrigin=(s['beginQpc']-d['originQpc'])/hz,lastZeroSequence=lastzero));previous=s['eventsLost']
 rates=[]
 for a,s in zip(samples,samples[1:]):
  elapsed=(s['endQpc']-a['endQpc'])/hz
  if elapsed>0:rates.append(dict(qpc=s['endQpc'],receivedPerSecond=s['receivedDelta']/elapsed,completedPerSecond=s['callbackDelta']/elapsed,consumerCPUSecondsDelta=(s['cpu100ns']-a['cpu100ns'])/1e7,elapsedSeconds=elapsed))
 groups=collections.defaultdict(list)
 for s in d['slowSpans']:groups[s['operation']].append((s['endQpc']-s['beginQpc'])/hz)
 lag=[s['deliveryLag'] for s in samples];bins=[sum(x['bins'][i] for x in lag) for i in range(64)];lagcount=sum(x['count'] for x in lag)
 window=None
 if transitions:
  center=transitions[0]['beginQpc'];window=dict(samples=[s for s in samples if abs(s['beginQpc']-center)<=2*hz],slowSpans=[s for s in d['slowSpans'] if s['beginQpc']<=center+2*hz and s['endQpc']>=center-2*hz])
 q=d['finalQueue'];names=['items','bytes','pendingSegments','admitted','persisted','persistedBytes','finalizations']
 sessions[channel]=dict(session=d['session'],telemetrySHA256=sha(base/'loss-diagnostic-v2.json'),qualification=qualification,configuration=d['configuration'],sampleCount=len(samples),validQuerySamples=len(good),queryErrors=[dict(sequence=s['sequence'],status=s['status'],qpc=s['beginQpc'],afterStop=s['beginQpc']>=d['stopBeginQpc']) for s in samples if s['status']],telemetryErrors=d['errors'],telemetryOverflow=d['overflow'],finalEventsLost=final['eventsLost'],finalRealtimeBuffersLost=final['realtimeBuffersLost'],finalLogBuffersLost=final['buffersLost'],authorityFaults=final['faults'],firstLoss=transitions[0] if transitions else None,lastLoss=transitions[-1] if transitions else None,lossTransitions=transitions,minSampledFreeBuffers=min(s['freeBuffers'] for s in good),maxSampledNumberOfBuffers=max(s['numberOfBuffers'] for s in good),captureSampleSpanSeconds=(samples[-1]['endQpc']-samples[0]['beginQpc'])/hz,maxSampleGapSeconds=max((s['beginQpc']-a['beginQpc'])/hz for a,s in zip(samples,samples[1:])),callbackTotals=dict(received=samples[-1]['received'],completed=samples[-1]['callbacks'],selected=samples[-1]['selected']),wholeCaptureMaxReceivedRate=max(x['receivedPerSecond'] for x in rates),wholeCaptureMaxCompletedRate=max(x['completedPerSecond'] for x in rates),sampledConsumerCPUSeconds=(samples[-1]['cpu100ns']-samples[0]['cpu100ns'])/1e7,wholeCaptureSlowSpans={k:dict(count=len(v),maxSeconds=max(v),totalSeconds=sum(v)) for k,v in groups.items()},deliveryLag=dict(count=lagcount,meanSeconds=sum(x['totalTicks'] for x in lag)/hz/lagcount if lagcount else None,maxSeconds=max(x['maxTicks'] for x in lag)/hz,p95SecondsBounds=[x/hz for x in review.percentile_bounds(dict(bins=bins),.95)] if lagcount else None),queueHighItems=d['queueHighItems'],queueHighBytes=d['queueHighBytes'],maxSampledPendingSegments=max(s['queue'][2] for s in samples),finalQueue=dict(zip(names,q)),firstLossWindow=window,nearLossRates='NOT APPLICABLE — no loss increment' if not transitions else window,nearLossCPU='NOT APPLICABLE — no loss increment' if not transitions else window,nearLossLag='NOT APPLICABLE — no loss increment' if not transitions else window,bufferPressurePrecededLoss='NOT ESTABLISHED — no loss increment' if not transitions else 'REQUIRES ANALYSIS',consumerStallPrecededLoss='NOT ESTABLISHED — no loss increment' if not transitions else 'REQUIRES ANALYSIS')
write('telemetry-analysis.json',dict(run=root.name,runStatus='TRACE_DIAGNOSTIC_RUN_FAILED',diagnosisStatus='NO_TRACE_LOSS_REPRODUCED',sessions=sessions,historicalTraceLossCause='UNCONFIRMED',limitations=['Fail-closed early rejection shortens observation; a loss-free attempt does not explain or disprove historical loss.','Whole-capture summaries are not near-loss measurements.','Failed post-stop ETW queries excluded from buffer minima; null EventsLost is not zero.','CPU sampling has OS accounting granularity; authority reported zero does not establish zero actual CPU activity.']))
phase=read(root/'phase-a-v3.json');helper=phase['helpers'][0];etw=read(root/'etw-result.json');match=[x for x in etw['rows'] if x['pid']==helper['pid'] and str(x['created'])==helper['created']];assert len(match)==1;h=match[0];hz=phase['binding']['frequency'];close=helper['localCloseQpc']
handoff=dict(helper=helper,authorityRow=h,retainedAfterLocalCloseSeconds=(h['handleAttemptQpc']-close)/hz,imageBeganAfterLocalCloseSeconds=(h['imageBeginQpc']-close)/hz,startDeliveryDelaySeconds=(h['startCallbackQpc']-h['startQpc'])/hz,required='authority retained handle AND image capture begin before localCloseQpc',predicateSatisfied=h['handleAttemptQpc']<close and h['imageBeginQpc']<close,source=str(C/'terminal_receipt_v3.hpp')+':54',historicalTraceLossCauseNotExplained=True)
write('terminal-rejection.json',handoff)
one=read(root/'hash-pass-1.json');two=read(root/'hash-pass-2.json');assert one['files']==two['files'] and len(one['files'])==12
binding=read(root/b.NAME)
for x in binding['dataset']:
 p=pathlib.Path(x['path']);s=p.stat();assert(s.st_size,s.st_mtime_ns,s.st_ino,s.st_dev,sha(p))==(x['bytes'],x['mtimeNs'],x['fileId'],x['volume'],x['sha256'])
heart=read(root/'app-heartbeats.json');fm=read(pres/'FAILURE-MANIFEST.json')
write('run-summary.json',dict(run=root.name,status='TRACE_DIAGNOSTIC_RUN_FAILED',diagnosis='NO_TRACE_LOSS_REPRODUCED',firstFailure=read(root/'terminal-failure-v3.json'),rejected=read(root/'rejected-v3.json'),launcherResult=read(root/'launcher-result.json'),phaseA=True,terminalReceipt=False,successFinalizerInvoked=False,acceptanceSeal=False,hashPassesMatch=True,datasetMetadataUnchanged=True,files=12,bytes=786432,hashPass1Seconds=(one['endQpcNs']-one['beginQpcNs'])/1e9,hashPass2Seconds=(two['endQpcNs']-two['beginQpcNs'])/1e9,maxHeartbeatSeconds=max(x['interval'] for x in heart),missingAcceptanceArtifacts=fm['missingArtifacts'],failureArchive=receipt,cleanup=dict(eventualHostCleanupProven=fm['EVENTUAL_HOST_CLEANUP_PROVEN'],preserverCensusWithinOriginalDeadline=fm['ACCEPTANCE_CLEANUP_TIMELY'],requiredAcceptanceChainComplete=False,finalMatchingProcesses=0,finalTraceSessions=0),candidateFilesUnchanged=229,frozenCheckerSHA256=sha(C/'medium-checker/frozen_reference.py'),protectedAccess=False,productionChange=False,retry=False,configurationChanges=False))
write('run-inventory.json',[dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,mtimeNs=p.stat().st_mtime_ns,sha256=sha(p)) for p in root.rglob('*') if p.is_file()])
print(json.dumps(dict(summary=read(R/'run-summary.json'),sessions=sessions,handoff=handoff),indent=2))
