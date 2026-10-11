import pathlib,json,hashlib,collections
R=pathlib.Path(__file__).parent;P=R.parent/'stage6-large-small-integration-20260922'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):
 with (R/n).open('x') as f:json.dump(v,f,indent=2)
run=load(P/'normal-run.json');C=pathlib.Path(run['code']);root=pathlib.Path(run['root']);a=load(R/'analysis.json')
old=pathlib.Path(load(R.parent/'stage6-trace-capacity-native-entry-20260921/batched-candidate/plan.json')['code'])
baseline={x['name']:x['sha256'] for x in load(R.parent/'stage6-trace-capacity-native-entry-20260921/batched-candidate/candidate-hashes.json')}
link={}
for name in ('J6StartupTrace.exe','startup_trace.cpp','trace_sink.hpp'):
 p=old/name;h=sha(p);assert h==baseline[name]
 link[name]=dict(historicalPath=str(p),historicalSHA256=h,currentSHA256=sha(C/name) if (C/name).exists() else None)
 if (C/name).exists():assert sha(C/name)==h
save('verified-build-lineage.json',link)
times=load(R/'timeline.json');end=next(x['qpc'] for x in times if x['stage']=='launcher:HELPER_RETURN');begin=next(x['qpc'] for x in times if x['stage']=='launcher:HELPER_INVOCATION');app=a['observers']['app']
counts=collections.Counter();sub=collections.Counter();peaks=collections.Counter()
for s in load(root/'detail/startup-events.json')['segments']:
 with (root/'detail'/s['name']).open() as f:
  for line in f:
   x=json.loads(line);phase='before_collector' if x['qpc']<begin else 'during_collector' if x['qpc']<=end else 'after_collector'
   counts[phase]+=1
   if x['pid']==app['pid'] and x['created']==app['created']:sub[phase]+=1
   if a['detailEventPeak1s']['beginQpc']<=x['qpc']<a['detailEventPeak1s']['beginQpc']+10000000:peaks[(str(x['pid']),x['provider'])]+=1
stats=dict(counts=dict(counts),applicationObserverCounts=dict(sub),observerShare=sum(sub.values())/a['detailRecords'],peakBreakdown=[dict(pid=k[0],provider=k[1],records=v) for k,v in peaks.most_common()],collectorElapsedSeconds=(end-begin)/10000000,authorityWriter=a['authorityWriter'],note='Counts are delivered/persisted records only. Loss counter has no per-phase sampling, and unpersisted events cannot be assigned to a subject or phase.')
save('phase-analysis.json',stats)
print(json.dumps({k:v for k,v in stats.items() if k!='authorityWriter'}))
print(json.dumps({k:v for k,v in a['authorityWriter'].items() if k not in ('segments','telemetry')}))
