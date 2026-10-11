import pathlib,json
R=pathlib.Path(__file__).resolve().parent;d=R/'loads'
def read(n):return json.loads((d/n).read_text(encoding='utf-8-sig'))
h=[json.loads(s) for s in (d/'heartbeat.jsonl').read_text().splitlines()]
ident=read('ready.json');freq=ident['frequency'];trace=read('loop-trace.json');samples=read('collector-samples.json')
a,b=max(zip(h,h[1:]),key=lambda ab:ab[1]['ticks']-ab[0]['ticks'])
tracegaps=sorted([dict(seconds=(v['qpc']-u['qpc'])/freq,fromStage=u,toStage=v) for u,v in zip(trace,trace[1:]) if u['qpc']<=b['ticks'] and v['qpc']>=a['ticks']],key=lambda x:x['seconds'],reverse=True)
sgaps=sorted([dict(seconds=(v['qpc']-u['qpc'])/freq,previous=u,next=v) for u,v in zip(samples,samples[1:])],key=lambda x:x['seconds'],reverse=True)
result=dict(status='MONITOR_STILL_DEFECTIVE',reason='Offline heartbeat interval exceeds unchanged ten-second acceptance limit',interval=(b['ticks']-a['ticks'])/freq,previousHeartbeat=a,nextHeartbeat=b,largestAdjacentTraceGaps=tracegaps[:10],largestCollectorSampleGaps=sgaps[:5],cause='UNCONFIRMED; adjacent instrumentation localizes elapsed time, not kernel scheduling or I/O cause',stop='No phase 9 expansion or dry1/dry2 executed. Failure detected at final offline reconciliation, after workloads had finished.',queueCorrection='558/558 events persisted and exactly removed; three external collisions; zero internal collisions or residue')
with (R/'workload-failure-analysis.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
