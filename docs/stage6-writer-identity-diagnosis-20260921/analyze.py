import json,hashlib,sys,statistics,collections,math
from pathlib import Path
R=Path(__file__).parent;C=Path(json.loads((R/'freeze.json').read_text())['newCode']);sys.path.insert(0,str(C));import application_authority
def save(n,v):
 with (R/n).open('x',encoding='utf8') as f:json.dump(v,f,indent=2)
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def distribution(v):
 v=sorted(v)
 return dict(count=len(v),min=min(v),median=statistics.median(v),p95=v[math.ceil(.95*(len(v)-1))],p99=v[math.ceil(.99*(len(v)-1))],max=max(v)) if v else {'count':0}
def prefix(root,m):
 expected=1;sizes=[]
 for seg in m['segments']:
  p=root/seg['name'];h=hashlib.sha256();n=0
  for line in p.open('rb'):
   h.update(line);row=json.loads(line);assert row['seq']==expected;expected+=1;n+=1;sizes.append(len(line))
  assert h.hexdigest()==seg['sha256'] and n==seg['records']
 assert expected-1==m['persisted']
 return {'sequenceGaps':0,'duplicates':0,'verifiedPrefixRecords':expected-1,'sizes':dict(distribution(sizes),mean=statistics.mean(sizes))}
writers=[]
for run in sorted(C.glob('writer-*')):
 if not (run/'app-authority.json').exists():continue
 m=load(run/'app-authority.json');t=load(run/'timings.json');z=load(run/'result.json');fq=t['frequency'];verified=prefix(run,m)
 stages=[dict(x,seconds=x['ticks']/fq,maxSeconds=x['max']/fq,medianSeconds=x['median']/fq,p95Seconds=x['p95']/fq,p99Seconds=x['p99']/fq) for x in t['stages']]
 intervals=[]
 for a,b in zip(t['queue'],t['queue'][1:]):
  dt=(b['qpc']-a['qpc'])/fq
  if dt>0:intervals.append({'seconds':dt,'producerRate':(b['accepted']-a['accepted'])/dt,'consumerRate':(b['persisted']-a['persisted'])/dt,'queueGrowthRate':(b['queue']-a['queue'])/dt,'from':a,'to':b})
 writer=dict(path=str(run),result=z,manifest=m,stages=stages,intervals=intervals,verification=verified,producerAverage=m['accepted']/z['producerSeconds'],endToEndConsumer=m['persisted']/z['totalSeconds'],endToEndBytes=m['bytes']/z['totalSeconds'])
 try:writer['reader']=application_authority.verify(run);assert not m['fault']
 except ValueError as e:assert m['fault'];writer['readerRejectsFailedRun']=str(e)
 writers.append(writer)
save('writer-analysis.json',writers)
ir=Path(load(R/'identity-run-corrected.json')['path']);k=load(ir/'etw-result.json');probes=load(ir/'identity-probes.json')['rows'];closed=load(ir/'identity-handle-closure.json')['rows'];events=[json.loads(l) for l in (ir/'app-events.jsonl').read_text(encoding='utf-8-sig').splitlines()];tap=load(ir/'app-tap.json');hb=load(ir/'app-heartbeats.json')
out=[];local=[];latency=collections.defaultdict(list)
for p in probes:
 pid=p['pid'];created=p['initialKernelTimes'][0];ks=[x for x in k['rows'] if x['pid']==pid];assert len(ks)==1 and ks[0]['created']==created
 kr=ks[0];n=load(ir/f'native-{pid}-{created}.json');cl=next(x for x in closed if x['pid']==pid)
 assert n['created']==created and n['entryQpc']>0 and n['finalWait']==0 and n['observerResult']==0 and not n['deadlineExceeded'] and not n['fault']
 assert p['finalKernelTimes'][:2]==cl['times'][:2] and p['finalKernelTimes'][0]==kr['created'] and p['finalKernelTimes'][1]==kr['exitFiletime'] and kr['handleRetained']
 ev=[e for e in events if e['pid']==pid];assert len(ev)==2 and {e['kind'] for e in ev}=={'start','stop'}
 for e in ev:
  kind=e['kind'];delay=(e['receivedQpc']-kr['startQpc' if kind=='start' else 'stopQpc'])/1e7
  latency[kind].append(delay);latency[p['case']+'-'+kind].append(delay)
  assert e['receivedQpc']<cl['closedQpc']
  row=dict(eventInstanceId=ir.name+':'+str(e['queueSequence']),raw=e,canonicalCandidates=[{'pid':pid,'created':created,'sequence':kr['sequence']}],result='AMBIGUOUS',selected=None,reason='No independent process-instance key in raw CIM event; one candidate in controlled kernel scope does not exclude older delayed instance outside scope',localExperimentCandidateCount=1,correlationVersion='diagnostic-no-force-match-v1',deliverySeconds=delay,eventGenerationAfterKernelExit100ns=int(e['nativeTime'])-int(kr['exitFiletime']),handleHeldAtDelivery=True)
  out.append(row)
 local.append(dict(pid=pid,created=created,sequence=kr['sequence'],case=p['case'],nativeEntryQpc=n['entryQpc'],kernelNativeHandleAgreement=True,handleClosed=cl['exited'],exitSeconds=(int(cl['times'][1])-int(created))/1e7))
trace=load(ir/'startup-events.json')
for seg in trace['segments']:
 assert hashlib.sha256((ir/seg['name']).read_bytes()).hexdigest()==seg['sha256']
assert trace['accepted']==trace['persisted'] and trace['fault']==0
identity=dict(path=str(ir),realProbeCount=len(probes),realApplicationEvents=len(out),uniqueWithinControlledTable=len(out),independentProvenUniqueMatches=0,ambiguous=len(out),unmatched=0,falseUniqueSelected=0,falseUniqueGuaranteeValidated=False,probes=local,events=out,latencies={a:distribution(b) for a,b in latency.items()},actualProbePIDReuse=0,kernelInstanceCount=len(k['rows']),kernelPIDReuse=len(k['rows'])-len({x['pid'] for x in k['rows']}),kernelFields=k['rows'][0]['startSchema'],kernelStopFields=k['rows'][0]['stopSchema'],kernelFaults=k['faults'],eventsLost=k['eventsLost'],buffersLost=k['buffersLost'],realtimeBuffersLost=k['realtimeBuffersLost'],nativeTraceRecords=trace['persisted'],nativeTraceSegments=len(trace['segments']),maxHeartbeat=max(x['interval'] for x in hb),applicationAuthority=application_authority.verify(ir),applicationResult=load(ir/'app-result.json'),launcherResult=load(ir/'launcher-result.json'),historical='21 AMBIGUOUS / 1 UNMATCHED unchanged',pressureExperiment='NOT RUN: positive discriminator not established; no medium escalation')
save('identity-analysis.json',identity)
focus=next(C.glob('focused-*'));faults=load(focus/'focused-faults.json');checks=[]
for row in faults['runs']:
 for key in ('expectedDisposition','lateRejected','doubleFinishRejected'):checks.append({'case':str(row['fault'])+':'+key,'pass':row[key]});assert row[key]
 try:
  result=application_authority.verify(Path(row['path']));assert row['fault']==0
 except ValueError:assert row['fault']!=0
 checks.append({'case':str(row['fault'])+':reader disposition','pass':True})
assert faults['capacitySticky'];checks.append({'case':'capacity sticky','pass':True})
tapResult=application_authority.verify(focus/'actual-tap');assert tapResult['records']==36000 and tapResult['tapTruncated']==4000
checks.append({'case':'actual tap decoupled beyond 20000','pass':True})
save('focused-results.json',{'assertions':len(checks),'passed':sum(x['pass'] for x in checks),'checks':checks,'tap':tapResult})
print(json.dumps({'writerRuns':len(writers),'focusedChecks':len(checks),'realProbes':len(probes),'realEvents':len(out),'provenUnique':0,'heartbeatMax':identity['maxHeartbeat'],'traceRecords':trace['persisted']}))
