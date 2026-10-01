import pathlib,json,hashlib,zipfile,sys,datetime
R=pathlib.Path(__file__).parent;P=R.parent/'stage6-narrow-preflight-20260920'
sys.path.insert(0,str(P));from verification import verify_archive,verify_candidate,verify_hash
receipt=json.loads((P/'archive-verification.json').read_text());A=pathlib.Path(receipt['path']);manifest=verify_archive(A,receipt)
for row in manifest['files']:verify_hash(pathlib.Path(row['source']),row['sha256'])
C=pathlib.Path(json.loads((P/'candidate.json').read_text())['code']);F=C/'protected-3aec3ce0062c42a19077a2bad0571bd7'
candidate=json.loads((C/'baseline-source.json').read_text());assert verify_candidate(C,candidate)==84
def read(n):return json.loads((F/n).read_text(encoding='utf-8-sig'))
def lines(n):return [json.loads(l) for l in (F/n).read_text(encoding='utf-8-sig').splitlines()]
probe=next(x for x in read('probe-timings.json') if x['pid']==24516)
kernel=read('etw-result.json');kr=next(x for x in kernel['rows'] if x['pid']==24516)
origin=probe['launchRequestedQpc'];freq=probe['frequency'];timeline=[]
def event(q,name,detail=None):
 if q:timeline.append(dict(qpc=q,secondsFromProbeLaunch=(q-origin)/freq,event=name,detail=detail))
for k,v in probe.items():
 if k.endswith('Qpc'):event(v,'probe.'+k)
children=[x for x in kernel['rows'] if x['parentPid']==24516]
for x in [kr,*children]:
 for k in ('startQpc','startCallbackQpc','handleAttemptBeginQpc','stopQpc','stopCallbackQpc','signalObservedQpc'):
  event(x[k],str(x['pid'])+'.kernel.'+k)
worker=read('hash-worker-cleanup.json');event(worker['launchQpc'],'hashWorker.launch');event(worker['createReturnedQpc'],'hashWorker.CreateProcessReturned');event(worker['cleanupBeginQpc'],'hashWorker.cleanupBegin');event(worker['observedQpc'],'hashWorker.exitObserved')
hb=read('app-heartbeats.json');app=read('app-result.json')
for h in hb:event(h['qpc'],'heartbeat.calculated',dict(interval=h['interval']))
event(app['error']['qpc'],'heartbeat.error',app['error'])
events=lines('app-events.jsonl');receipts=read('app-receipts.json');byq={x['queueSequence']:x for x in receipts}
intervals=[]
for x in events:
 r=byq[x['queueSequence']];delta=(r['persistedQpc']-x['drainedQpc'])/freq
 intervals.append(dict(pid=x['pid'],kind=x['kind'],queueSequence=x['queueSequence'],drainedQpc=x['drainedQpc'],persistedQpc=r['persistedQpc'],seconds=delta))
 event(x['receivedQpc'],'event.enqueued',dict(pid=x['pid'],kind=x['kind'],queue=x['queueSequence']))
 event(x['drainedQpc'],'event.drain',dict(pid=x['pid'],kind=x['kind'],queue=x['queueSequence']))
 event(r['persistedQpc'],'event.persistedAndRemoved',dict(pid=x['pid'],kind=x['kind'],queue=x['queueSequence']))
resources=read('monitor-resources.json');growth={}
for k in ('privateBytes','workingSet','handles','queueDepth','events','threads','kernelPrivateBytes','kernelHandles','eventBytes'):
 vals=[x[k] for x in resources];known=[v for v in vals if v is not None];growth[k]=dict(first=vals[0],last=vals[-1],min=min(known) if known else None,max=max(known) if known else None,unknown=sum(v is None for v in vals))
hashsamples=read('hash-health-samples.json');last=hb[-1]['qpc']
summary=dict(status='PRESERVED_EVIDENCE_VERIFIED',archive=receipt,candidateHashes=84,failedRun=str(F),probe=probe,kernelProbe=kr,children=children,hashWorker=worker,resourceSamples=len(resources),resourceSpanSeconds=resources[-1]['seconds']-resources[0]['seconds'],growth=growth,queue=app['queue'],drainIntervals=sorted(intervals,key=lambda x:x['seconds'],reverse=True)[:12],heartbeatGapSeconds=(app['error']['qpc']-last)/freq,probeExitToLastHeartbeatSeconds=(last-kr['stopQpc'])/freq,probeExitToHeartbeatErrorSeconds=(app['error']['qpc']-kr['stopQpc'])/freq,hashWorkerExitToLastHeartbeatSeconds=(last-worker['observedQpc'])/freq,hashHealthSamples=len(hashsamples),hashLastSample=hashsamples[-1],dataset=read('contract.json')['source'],unavailable=['process entry/internal work markers','per-file partial hash progress/throughput','C:/D: physical utilization and latency','system CPU/scheduler/page-fault/security trace','individual final heartbeat-loop operation durations'])
with (R/'preserved-analysis.json').open('x') as f:json.dump(summary,f,indent=2)
with (R/'unified-timeline.json').open('x') as f:json.dump(sorted(timeline,key=lambda x:x['qpc']),f,indent=2)
with (R/'preserved-source-manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
print(json.dumps({k:v for k,v in summary.items() if k not in ('probe','kernelProbe','children','hashWorker','archive')}))
print('CHILDREN',json.dumps(children))
