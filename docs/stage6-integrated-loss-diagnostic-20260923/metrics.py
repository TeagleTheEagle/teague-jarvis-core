import pathlib,json,hashlib,collections
R=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cfg=read(R/'candidate.json');C=pathlib.Path(cfg['code']);run=pathlib.Path(read(R/'normal-run.json')['root'])
marks=read(run/'integration-launcher.json');invoke=next(x['qpc'] for x in marks if x['event']=='HELPER_INVOCATION');returned=next(x['qpc'] for x in marks if x['event']=='HELPER_RETURN')
channels={}
for role,d in [('authority',run),('detail',run/'detail')]:
 t=read(d/'loss-telemetry.json');e=read(d/'etw-result.json');freq=t['frequency']
 assert t['errors']==0 and t['callbacks']==t['selected']+t['rejected']
 assert all(p['end']>=p['begin'] and p['status']==0 for p in t['phases'])
 assert any(p['phase']=='periodic' for p in t['snapshots'])
 assert all(p['end']>=p['begin'] and p['status']==0 for p in t['snapshots'])
 assert all(p['eventsLost']==p['realtimeBuffersLost']==p['logBuffersLost']==0 for p in t['snapshots'])
 channels[role]=dict(callbacks=t['callbacks'],selected=t['selected'],rejected=t['rejected'],snapshots=len(t['snapshots']),actualBuffers=sorted(set(p['numberOfBuffers'] for p in t['snapshots'])),eventsLost=e['eventsLost'],maxQuerySeconds=max((p['end']-p['begin'])/freq for p in t['snapshots']),metrics={k:dict(count=v['count'],maxSeconds=v['maxTicks']/freq,totalSeconds=v['totalTicks']/freq) for k,v in t['metrics'].items()},phases=t['phases'])
observer=read(run/'observer-identities.json')['app'];counts=collections.Counter();phase=collections.Counter();observerPhase=collections.Counter();records=0
manifest=read(run/'detail/startup-events.json')
for seg in manifest['segments']:
 p=run/'detail'/seg['name'];assert sha(p)==seg['sha256']
 for line in p.read_text().splitlines():
  x=json.loads(line);records+=1;counts[x['pid']]+=1
  stage='before' if x['qpc']<invoke else 'during' if x['qpc']<=returned else 'after';phase[stage]+=1
  if x['pid']==observer['pid']:observerPhase[stage]+=1
one=read(run/'hash-pass-1.json');two=read(run/'hash-pass-2.json');assert one['files']==two['files']
for n,x in one['files'].items():
 p=C/'small-synthetic'/n;assert sha(p)==x['sha256'] and p.stat().st_size==x['bytes'] and p.stat().st_mtime_ns==x['mtime_ns']
cov=read(R/'coverage-failure-detail.json')['coverage'];k=read(run/'etw-result.json');writer=read(run/'kernel-authority-result.json');app=read(run/'app-result.json')
report=dict(status='INTEGRATED_DIAGNOSTIC_EVIDENCE_FAIL',run=str(run),telemetryStatus='PASS',historicalLossCause='UNCONFIRMED',channels=channels,collectorSeconds=(returned-invoke)/10000000,detailRecords=records,applicationObserverPID=observer['pid'],applicationObserverRecords=counts[observer['pid']],applicationObserverShare=counts[observer['pid']]/records,detailPhases=dict(phase),observerPhases=dict(observerPhase),coverage=cov,hashesMatch=True,metadataPreserved=True,files=len(one['files']),bytes=sum(x['bytes'] for x in one['files'].values()),kernelIdentities=len(k['rows']),kernelPersisted=writer['written'],maxHeartbeat=max(x['interval'] for x in read(run/'app-heartbeats.json')),appQueue=app['queue'],sampler=read(run/'sampler-results.json'),nativeBridge=read(run/'native-bridge-cleanup.json'),tree=read(run/'tree-handles.json'),attempts=1,retries=0,acceptanceGranted=False)
with (R/'metrics.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps({x:report[x] for x in ('status','collectorSeconds','detailRecords','applicationObserverShare','kernelIdentities','kernelPersisted','maxHeartbeat')},indent=2))
print(json.dumps({x:cov[x] for x in ('requiredIdentities','verifiedIdentities','missingRequired','contradictory')},indent=2))
print(json.dumps({k:{x:v[x] for x in ('callbacks','selected','snapshots','actualBuffers','maxQuerySeconds')} for k,v in channels.items()},indent=2))
