import pathlib,json,sys,hashlib,collections,datetime,difflib
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'candidate-v5.json').read_text())['code']);F=C/'hardening-cf2a523b5ef74f7380411829d2fd1477'
sys.path.insert(0,str(C));import cleanup_checker
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def put(n,v):
 with (R/n).open('x') as f:json.dump(v,f,indent=2)
v=cleanup_checker.evaluate(F);assert v['status']=='PASS' and not v['primaryFailure'] and v['producerStatus']=='DIAGNOSTIC_COMPLETE'
t=read(F/'stage-timing.json');s=t['spans'];freq=t['frequency'];assert t['overflow']==0
for x in s:assert x['start']<=x['end'] and x['loop']>=0 and abs(x['seconds']-(x['end']-x['start'])/freq)<1e-8
groups=collections.defaultdict(list)
for x in s:groups[x['stage']].append(x)
required=['loop.wake','event.source.read','callback.A-callback','callback.A-enqueue','queue.lock.acquire.Select','event.selection','event.serialization','evidence.path','event.File.AppendAllText','queue.exact.RemoveAt','heartbeat.creation','heartbeat.history.append','heartbeat.publish.overwrite','flush.durable','control.file.check','process.inspection.preflight','process.inspection.identity','wait.event']
assert all(groups[k] for k in required)
loops=[x['loop'] for x in groups['loop.wake']];assert loops==list(range(1,len(loops)+1))
summary={k:dict(count=len(a),maxSeconds=max(x['seconds'] for x in a)) for k,a in sorted(groups.items())}
sampler=read(F/'sampler-results.json');assert len(sampler)==7 and sampler[0]['status']=='AVAILABLE'
assert all(x['allExited'] and x['handleClosed'] and x['jobActiveBeforeClose']==0 for x in sampler)
assert all(x['status']=='MISSING' for x in sampler[1:])
injected=next(x for x in sampler if x['case']=='cleanup-timeout');assert injected['cleanupObservationTimedOut'] and (injected['cleanupEndQpc']-injected['cleanupBeginQpc'])/freq>=2
assert injected['postInjectionProof']['handleState']==0 and injected['postInjectionProof']['jobActive']==0
hb=read(F/'app-heartbeats.json');assert max(x['interval'] for x in hb)<10
data=cleanup_checker.load(F);rows=data['kernel']['rows'];app=data['events'];receipts={x['queueSequence']:x for x in data['receipts']};probes=read(F/'probe-timings.json');timelines=[]
for p in probes:
 assert not p['hardDeadlineFailure'] and not p['independentObserverFailed'] and p['finalHandleState']==0
 k=next(x for x in rows if x['pid']==p['pid'] and x['created']==p['initialKernelTimes'][0]);stop=[x for x in app if x['pid']==p['pid'] and x['kind']=='stop'];assert len(stop)==1
 a=stop[0];taps=[x for x in data['tap'] if x['stage']=='A-callback' and x['pid']==p['pid'] and x['kind']=='stop' and x['nativeTime']==a['nativeTime']];assert len(taps)==1
 markers=p.get('nativeMarkers',{})
 timeline=dict(pid=p['pid'],created=k['created'],launchRequest=p['launchRequestedQpc'],createProcessReturn=p['createProcessReturnedQpc'],handleRetained=p['handleRetainedQpc'],entry=markers.get('firstActivityQpc','UNKNOWN'),workBegin=markers.get('workBeginQpc','UNKNOWN'),workEnd=markers.get('workEndQpc','UNKNOWN'),cleanupBegin=markers.get('cleanupBeginQpc','UNKNOWN'),cleanupEnd=markers.get('cleanupEndQpc','UNKNOWN'),exitBegin=markers.get('exitBeginQpc','UNKNOWN'),kernelExit=k['stopQpc'],retainedSignalObserved=p['observerReturnedQpc'],applicationStopCallback=taps[0]['qpc'],applicationStopEnqueued=a['receivedQpc'],applicationStopPersisted=receipts[a['queueSequence']]['persistedQpc'],children=[dict(pid=x['pid'],created=x['created'],kernelStart=x['startQpc'],kernelStop=x['stopQpc']) for x in rows if x['parentSequence']==k['sequence']])
 timelines.append(timeline)
put('process-timeline-final.json',dict(frequency=freq,notice='Observed signal times are observation bounds; uninstrumented whoami internal stages UNKNOWN.',probes=timelines,allKernelIdentities=rows))
put('timing-coverage-final.json',dict(status='PASS',frequency=freq,spans=len(s),points=len(t['points']),overflow=t['overflow'],loopCount=len(loops),requiredStages=required,stages=summary,evidenceExistenceCheck=t['evidenceExistenceCheck'],optionalResourceInspection=t['optionalResourceInspection']))
out=dict(status='PASS',run=str(F),identities=v['total'],handleConfirmed=v['handleConfirmed'],qualifiedPostExit=v['kernelPostExit'],starts=v['appStarts'],stops=v['appStops'],unexplained=v['insufficient'],lineageUnknown=len(v['lineageUnknown']),externalEventIdentifierCollisions=v['externalEventIdentifierCollisions'],queueIdCollisions=v['queueIdentityCollisions'],queue=data['app']['queue'],probeCount=len(probes),instrumentedProbes=sum('nativeMarkers' in p for p in probes),maxProbeLifetimeSeconds=max((int(p['finalKernelTimes'][1])-int(p['finalKernelTimes'][0]))/1e7 for p in probes),maxHeartbeatInterval=max(x['interval'] for x in hb),deadlineViolations=0,sampler=[dict(case=x['case'],status=x['status'],reason=x.get('reason'),seconds=(x['cleanupEndQpc']-x['launchQpc'])/freq,cleanupSeconds=(x['cleanupEndQpc']-x['cleanupBeginQpc'])/freq,jobEmpty=x['jobActiveBeforeClose']==0,allExited=x['allExited']) for x in sampler],timingSpans=len(s),stageCount=len(groups),durableFinalization=data['app']['durableFinalization'],kernelLosses={k:data['kernel'][k] for k in ('faults','eventsLost','realtimeBuffersLost','buffersLost')},acceptanceScope='Bounded diagnostic infrastructure only')
put('combined-summary-final.json',out)
O=pathlib.Path(json.loads((R/'candidate.json').read_text())['original']);baseline=read(O/'baseline-source.json');changes=[]
for x in baseline:
 p=O/x['name'];assert hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256']
 q=C/x['name'];h=hashlib.sha256(q.read_bytes()).hexdigest()
 if h!=x['sha256']:
  changes.append(dict(name=x['name'],before=x['sha256'],after=h,kind='generated-evidence' if x['name'] in {'extended-delay-result.json','probe-handle-regression.json'} else 'diagnostic-source'))
  if q.suffix in {'.py','.ps1','.cs'}:(R/(q.name+'.final.diff')).write_text(''.join(difflib.unified_diff(p.read_text().splitlines(True),q.read_text().splitlines(True),fromfile=str(p),tofile=str(q))))
current=read(C/'hardening-hashes.json')
for x in current:assert hashlib.sha256((C/x['name']).read_bytes()).hexdigest()==x['sha256']
put('source-integrity-final.json',dict(originalFilesVerified=len(baseline),candidateFilesVerified=len(current),changes=changes,added=[x for x in current if x['name'] not in {b['name'] for b in baseline}],originalUnchanged=True,productionModified=False,protectedAccess=False))
print(json.dumps(out))
