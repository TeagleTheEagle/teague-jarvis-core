"""Summarize the stopped run; never retries, seals acceptance, or edits raw evidence."""
import pathlib,json,hashlib,sys,collections
R=pathlib.Path(__file__).parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
copy=read(R/'copy-result.json');C=pathlib.Path(copy['workspace']);F=C/'protected-3148cf4d88354dd0aff4ec47ea0182ef'
sys.path.insert(0,str(C));import cleanup_checker,baseline_contract
load=lambda n:read(F/n)
life=cleanup_checker.evaluate(F)
with (R/'completed-exit-review.json').open('x') as f:json.dump(life,f,indent=2)
assert life['status']=='PASS' and life['insufficient']==0
before=read(R/'metadata-before.json');after=read(R/'metadata-after.json')
for kind in ('old','new'):assert {x['path']:x for x in before[kind]}=={x['path']:x for x in after[kind]}
assert baseline_contract.inventory(pathlib.Path(copy['destination']))==load('contract.json')['inventory']
old=pathlib.Path(copy['source']);cal=read(pathlib.Path(copy['calibration']))
assert sha(pathlib.Path(copy['calibration']))==copy['calibrationSHA256']
for x in cal['created']:
 s=(old/x['path']).stat();assert s.st_size==x['bytes'] and s.st_mtime_ns==x['mtime_ns']
candidate=read(R.parent/'stage6-large-revalidation-20260920'/'candidate.json')
counts={}
for kind,root,manifest in [('collector',pathlib.Path(candidate['collector']),'baseline-source.json'),('diagnostic',pathlib.Path(candidate['diagnostic']),'hardening-hashes.json'),('integration',C,'run-source.json')]:
 rows=read(root/manifest)
 for x in rows:assert sha(root/x['name'])==x['sha256']
 counts[kind]=len(rows)
for x in load('source-hashes.json'):assert sha(C/x['name'])==x['sha256']
probes=load('probe-timings.json');failed=[x for x in probes if x['hardDeadlineFailure'] or x['independentObserverFailed']]
details=[]
for x in failed:
 freq=x['frequency'];origin=x['launchRequestedQpc']
 details.append(dict(pid=x['pid'],created=x['initialKernelTimes'][0],image=x['executable'],parentPid=x['parentPid'],kernelLifetimeSeconds=(int(x['finalKernelTimes'][1])-int(x['finalKernelTimes'][0]))/1e7,creationCallSeconds=(x['createProcessReturnedQpc']-x['createProcessCalledQpc'])/freq,deadlineObservedSeconds=(x['failureCaughtQpc']-origin)/freq,observerElapsedSeconds=(x['observerReturnedQpc']-x['observerWaitEnteredQpc'])/freq,observerResult=x['observerResult'],deadlineHandleState=x['immediateHandleState'],finalHandleState=x['finalHandleState'],finalExitCode=x['actualExitCode'],kernelExitFiletime=x['finalKernelTimes'][1]))
sampler=load('sampler-results.json');bad=[x for x in sampler['queries'] if not x['allExited'] or not x['handleClosed']]
kernel=load('etw-result.json');samplerDetails=[]
for x in bad:
 k=next(k for k in kernel['rows'] if (k['pid'],k['created'])==(x['pid'],x['created']))
 samplerDetails.append(dict(pid=x['pid'],created=x['created'],status=x['status'],creationCallSeconds=(x['createReturnedQpc']-x['createBeginQpc'])/1e7,cleanupObservationSeconds=(x['cleanupEndQpc']-x['cleanupBeginQpc'])/1e7,allExitedAtBoundary=x['allExited'],handleClosed=x['handleClosed'],handleStateAtBoundary=x['handleState'],jobActiveBeforeClose=x['jobActiveBeforeClose'],terminationRequested=x.get('terminationRequested'),kernelExitFiletime=k['exitFiletime'],kernelExitCode=k['exitCode'],kernelHandleClosed=k['handleClosed'],kernelSignalObservedQpc=k['signalObservedQpc']))
timing=load('stage-timing.json');groups=collections.defaultdict(list)
for x in timing['spans']:groups[x['stage']].append(x['seconds'])
samples=load('hash-health-samples.json')+load('collector-health-samples.json');hb=load('app-heartbeats.json');app=load('app-result.json');tree=load('tree-handles.json')
host=read(R/'host-final.json');assert not host['processes'] and not host['diagnosticTraces'] and host['traceExit']==0
sourceManifest=pathlib.Path(copy['run'])/'dataset-manifest.json';assert sha(sourceManifest)==copy['manifestSHA256']
out=dict(status='PROTECTED_COLLECTOR_STILL_DEFECTIVE',run=str(F),runId=F.name,copyStatus=copy['status'],preflight='PASS',source=copy['source'],destination=copy['destination'],fileCount=copy['fileCount'],totalBytes=copy['totalBytes'],largestFile=max(copy['copyAndSourceHash'],key=lambda x:x['bytes']),copyManifestSHA256=copy['manifestSHA256'],copySeconds=copy['seconds'],hashPass1='INCOMPLETE_CANCELLED_AFTER_PROBE_FAILURE',hashPass2='NOT_RUN',fullHashDurations=None,completePassThroughput=None,monitoredHashEquality='NOT_ESTABLISHED',sourceMetadataAclPreserved=True,oldAndNewMetadataEntries=30,sourceHashes=counts,configurationOnlyChange=read(R/'configuration-change.json'),probeCount=len(probes),deadlineViolations=len(failed),probeFailures=details,sampler=dict(queries=len(sampler['queries']),missing=sampler['missing'],threadExited=sampler['threadExited'],failures=samplerDetails),maxHeartbeatInterval=max(x['interval'] for x in hb),maxHeartbeatAge=max(x['age'] for x in samples),timing=dict(stageCount=len(groups),spanCount=len(timing['spans']),overflow=timing['overflow'],longest=max(timing['spans'],key=lambda x:x['seconds']),maxima={k:max(v) for k,v in groups.items()}),lifecycle={k:life[k] for k in ('status','total','handleConfirmed','kernelPostExit','insufficient','appStarts','appStops','kernelCreates','kernelExits','externalEventIdentifierCollisions','queueIdentityCollisions')},childHelperCount=life['total']-1,lineageAmbiguities=len(life['lineageUnknown']),queue=app['queue'],observerDurableFinalization=app['durableFinalization'],treeAllExited=tree['allExited'],treeHandlesClosed=tree['allHandlesClosed'],treeThreadStopped=tree['threadStopped'],retainedImageQueryLimitations=tree['errors'],acceptanceFinalization='NOT_RUN_FAILURE_PRESERVED',acceptanceManifest='NOT_CREATED',liveDiagnosticProcesses=0,traceSessions=0,protectedVmAccess=False,productionChanged=False,protectedBaselineEligible=False,historicalDelayCause='UNCONFIRMED',historicalStage1Cause='UNCONFIRMED',currentDelayCause='UNCONFIRMED',retry=False,thresholdChanges=False)
with (R/'failure-summary.json').open('x') as f:json.dump(out,f,indent=2)
identities=[dict(pid=x['pid'],created=x['created'],image=x['image']) for x in life['identities']]
launcher=load('launcher.json');identities.append(dict(pid=launcher['pid'],created=launcher['creationFiletime'],image=launcher['image']))
identities.extend(load('observer-identities.json').values())
with (R/'recorded-identities.json').open('x') as f:json.dump(identities,f,indent=2)
print(json.dumps({k:out[k] for k in ('status','sourceHashes','probeFailures','sampler','maxHeartbeatInterval','maxHeartbeatAge','lifecycle','queue','sourceMetadataAclPreserved','liveDiagnosticProcesses','traceSessions')},indent=2))
