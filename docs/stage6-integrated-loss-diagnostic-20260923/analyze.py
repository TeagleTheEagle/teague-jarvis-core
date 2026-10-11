import pathlib,json,sys,hashlib,collections
R=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cfg=read(R/'candidate.json');C=pathlib.Path(cfg['code']);run=pathlib.Path(read(R/'normal-run.json')['root'])
sys.path.insert(0,str(C));import small_check
try:qualification=small_check.check(run)
except Exception as e:
 with (R/'diagnostic-check-failure.json').open('x') as f:json.dump(dict(type=type(e).__name__,error=str(e),run=str(run)),f,indent=2)
 raise
assert all(sha(C/x['name'])==x['sha256'] for x in cfg['files'])
for n,row in read(run/'hash-pass-1.json')['files'].items():
 p=C/'small-synthetic'/n;assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes'] and p.stat().st_mtime_ns==row['mtime_ns']
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
  stage='before' if x['qpc']<invoke else 'during' if x['qpc']<=returned else 'after'
  phase[stage]+=1
  if x['pid']==observer['pid']:observerPhase[stage]+=1
report=dict(status='SMALL_INTEGRATED_DIAGNOSTIC_PASS',diagnosticOnly=True,acceptanceGranted=False,run=str(run),channels=channels,collectorSeconds=(returned-invoke)/10000000,detailRecords=records,applicationObserverPID=observer['pid'],applicationObserverRecords=counts[observer['pid']],applicationObserverShare=counts[observer['pid']]/records,detailPhases=dict(phase),observerPhases=dict(observerPhase),qualification=qualification,sourceHashesVerified=len(cfg['files']),historicalCause='UNCONFIRMED',retries=0)
with (R/'analysis.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps({k:v for k,v in report.items() if k not in ('qualification','channels')},indent=2))
print(json.dumps({k:dict(callbacks=v['callbacks'],snapshots=v['snapshots'],actualBuffers=v['actualBuffers'],maxCallbackSeconds=v['metrics']['callback']['maxSeconds'],maxQuerySeconds=v['maxQuerySeconds']) for k,v in channels.items()},indent=2))
print(json.dumps({k:qualification[k] for k in ('identities','starts','stops','cim','maxHeartbeat','probes','samplerQueries')},indent=2))
