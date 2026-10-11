"""Offline timing and coverage analysis; no health repair, retries or runtime mutation."""
import pathlib,json,sys,collections,datetime
R=pathlib.Path(__file__).resolve().parent;O=R.parent/'stage6-eventidentity-fix-20260920'
def read(p):
 raw=p.read_text(encoding='utf-8-sig')
 if not raw.strip() and p.name=='runtime-samples.json':return [] # optional sampling disabled in minimal/none cases
 return json.loads(raw)
def put(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
def heartbeat(d):return [json.loads(s) for s in (d/'heartbeat.jsonl').read_text().splitlines()]
def duration_pairs(rows,freq):
 stacks=collections.defaultdict(list);pairs=[]
 for row in rows:
  stage=row['stage'];thread=row.get('nativeThread',0)
  if stage.endswith('.begin') or stage.endswith('.request') or stage.endswith('.acquired'):
   if stage.endswith('.acquired'):
    key=(thread,stage.removesuffix('.acquired')+'.request')
    if stacks[key]:
     a=stacks[key].pop();pairs.append(dict(stage=stage.removesuffix('.acquired')+'.wait',seconds=(row['qpc']-a['qpc'])/freq,start=a['qpc'],end=row['qpc'],thread=thread,cpuSeconds=(row.get('cpu100ns',0)-a.get('cpu100ns',0))/1e7))
   stacks[(thread,stage)].append(row)
  elif stage.endswith('.end') or stage.endswith('.release'):
   ending='.end' if stage.endswith('.end') else '.release';base=stage.removesuffix(ending);opening='.begin' if ending=='.end' else '.acquired';key=(thread,base+opening)
   if stacks[key]:
    a=stacks[key].pop();pairs.append(dict(stage=base if ending=='.end' else base+'.hold',seconds=(row['qpc']-a['qpc'])/freq,operationOnlySeconds=(row['qpc']-a.get('sampleEndQpc',a['qpc']))/freq,start=a['qpc'],end=row['qpc'],thread=thread,cpuSeconds=(row.get('cpu100ns',0)-a.get('cpu100ns',0))/1e7))
 return pairs
def counters_summary(rows):
 values=collections.defaultdict(list)
 for row in rows:
  for c in row['counters']:
   if isinstance(c['CookedValue'],(float,int)):values[c['Path']].append(c['CookedValue'])
 return {k:dict(min=min(v),max=max(v),mean=sum(v)/len(v),samples=len(v)) for k,v in values.items() if v}
def one(run):
 d=R/run;h=heartbeat(d);identity=read(d/'ready.json');freq=identity['frequency'];trace=read(d/'fine-trace.json');loop=read(d/'loop-trace.json');samples=read(d/'collector-samples.json')
 pairs=duration_pairs(trace,freq);by=collections.defaultdict(list)
 for p in pairs:by[p['stage']].append(p)
 maxima={k:max(v,key=lambda p:p['seconds']) for k,v in by.items()}
 gaps=[dict(seconds=(b['ticks']-a['ticks'])/freq,previous=a,next=b) for a,b in zip(h,h[1:])];longest=max(gaps,key=lambda p:p['seconds'])
 related=sorted([p for p in pairs if p['start']<=longest['next']['ticks'] and p['end']>=longest['previous']['ticks']],key=lambda p:p['seconds'],reverse=True)
 resources=read(d/'resources.json') if (d/'resources.json').exists() else [];runtime=read(d/'runtime-samples.json');wake=read(d/'scheduler-observer.json')
 correlations=[]
 for gap in gaps:
  if gap['seconds']<=2:continue
  a=gap['previous']['ticks'];b=gap['next']['ticks'];rs=[r for r in resources if r['qpc']<=b+freq and r['endQpc']>=a-freq]
  correlations.append(dict(gap=gap,resourceWindows=rs))
 entries=read(d/'queue-entries.json');q=read(d/'queue-state.json');taps=read(d/'tap.json');probes=read(d/'probes.json');events=[json.loads(s) for s in (d/'events.jsonl').read_text().splitlines()]
 errs=[]
 if q['failed'] or q['remaining'] or not q['enqueued']==q['selected']==q['persisted']==q['removed']==len(events)==2*len(probes):errs.append('queue counts')
 for p in probes:
  if not p['handle_signalled'] or p['exit'] or int(p['kernel_exit_filetime'])<=int(p['created']):errs.append('probe exit')
  for k in ('start','stop'):
   if sum(e['kind']==k and e['pid']==p['pid'] for e in events)!=1:errs.append(f'persisted {p["pid"]} {k}')
   for stage in ('A-callback','A-enqueue'):
    if sum(e['kind']==k and e['pid']==p['pid'] and e['stage']==stage for e in taps)!=1:errs.append(f'{stage} {p["pid"]} {k}')
 internal=len(entries)-len({e['queueSequence'] for e in entries})
 if internal:errs.append('internal collision')
 if read(d/'timing-state.json')['overflow']:errs.append('timing overflow')
 cfg=read(d/'case.json');maxage=max((s['age'] for s in samples),default=0);healthFailed=(d/'collector-failure.json').exists() or longest['seconds']>=10 or maxage>10
 result=dict(run=run,config=cfg,monitorHealth='FAIL' if healthFailed else 'PASS_FOR_THIS_DIAGNOSTIC_RUN',acceptance=False,probes=len(probes),coverage='PASS' if not errs else 'FAIL',coverageErrors=errs,queue=q,externalCollisions=len(events)-len({e['eventIdentifier'] for e in events}),internalCollisions=internal,maxHeartbeatInterval=longest['seconds'],maxHeartbeatAge=maxage,longestHeartbeat=longest,owningStageCandidates=related[:10],stageMaxima=maxima,
  waitDeadlineOverrun=max(0,max((p['seconds']-1 for p in by['wait']),default=0)),independentSleepObserverMaxExcess=max((v['excessSeconds'] for v in wake),default=0),traceInstrumentationMaxSeconds=max(((v['sampleEndQpc']-v['qpc'])/freq for v in trace),default=0),
  storageAndCpu=counters_summary(resources),telemetryCounterMaxSeconds=max(((v['counterEnd']-v['counterStart'])/freq for v in resources),default=0),telemetryProcessMaxSeconds=max(((v['endQpc']-v['processStart'])/freq for v in resources),default=0),
  runtime=runtime,resourceProcessSamples=[dict(qpc=v['qpc'],endQpc=v['endQpc'],processes=v['processes']) for v in resources],
  gcPauseDeltaSeconds=(runtime[-1]['pauseTicks']-runtime[0]['pauseTicks'])/1e7 if len(runtime)>1 else None,threadCpuMeaning='GetThreadTimes quantized execution time, not kernel scheduler tracing; wait overrun does not prove starvation',correlationCount=len(correlations))
 put(d/'analysis.json',result);put(d/'storage-correlations.json',correlations)
 print(json.dumps({k:result[k] for k in ('run','monitorHealth','coverage','probes','maxHeartbeatInterval','maxHeartbeatAge','waitDeadlineOverrun','independentSleepObserverMaxExcess','gcPauseDeltaSeconds')}))
 return result
def historical():
 d=O/'loads';h=heartbeat(d);trace=read(d/'loop-trace.json');f=read(d/'ready.json')['frequency'];a,b=max(zip(h,h[1:]),key=lambda p:p[1]['ticks']-p[0]['ticks'])
 relevant=[x for x in trace if a['ticks']<=x['qpc']<=b['ticks']+f/100]
 pub0=next(x for x in relevant if x['stage']=='publication.complete' and x['seq']==a['seq']);pub1=next(x for x in relevant if x['stage']=='publication.complete' and x['seq']==b['seq'])
 timeline=dict(T0_last_publication=pub0,T1_last_success_before_unseparated_span=next(x for x in relevant if x['stage']=='event.serialize.end'),T2_next_attempt='Not separately instrumented: Stamp(serialized), Join-Path, Test-Path, Get-Item precede event.append.begin',T3_region_entry=next(x for x in relevant if x['stage']=='event.append.begin'),T4_region_completion=next(x for x in relevant if x['stage']=='event.append.end'),T5_next_success=next(x for x in relevant if x['stage']=='event.end'),T6_next_publication=pub1)
 resources=read(d/'resources.json');correlated=[r for r in resources if r['qpc']<=b['ticks']+f and r['endQpc']>=a['ticks']-f]
 v=dict(heartbeatRecordInterval=(b['ticks']-a['ticks'])/f,actualPublicationMarkerInterval=(pub1['qpc']-pub0['qpc'])/f,previousHeartbeat=a,nextHeartbeat=b,timeline=timeline,trace=relevant,frequency=f,resourceWindows=correlated,storageAndCpu=counters_summary(correlated),conclusion='Delay localized to event-drain region before heartbeat creation. Exact subcall and I/O-versus-scheduling cause unavailable in historical instrumentation.',historical13_7='UNCONFIRMED',historical14_084='UNCONFIRMED',historicalStage1='UNCONFIRMED')
 put(R/'historical-interval.json',v)
 print(json.dumps(dict(recordInterval=v['heartbeatRecordInterval'],publicationInterval=v['actualPublicationMarkerInterval'],timeline=timeline)))
if __name__=='__main__':historical() if sys.argv[1]=='historical' else one(sys.argv[1])
