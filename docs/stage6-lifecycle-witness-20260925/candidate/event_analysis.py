import pathlib,json,collections,sys
R=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def one(name):
 d=R/name;a=read(d/'analysis.json');rows=read(d/'loop-trace.json');freq=read(d/'ready.json')['frequency'];q=read(d/'queue-state.json');taps=read(d/'tap.json');events=[json.loads(s) for s in (d/'events.jsonl').read_text().splitlines()]
 drains=[];start=None
 for r in rows:
  if r['stage']=='drain.begin':start=r
  elif r['stage']=='drain.end' and start:drains.append(dict(start=start['qpc'],end=r['qpc'],seconds=(r['qpc']-start['qpc'])/freq,processed=r['detail']['drained'],remaining=r['detail']['backlog']));start=None
 pairs=collections.defaultdict(list)
 for t in taps:pairs[(t['pid'],t['kind'])].append(t)
 lags=[]
 for key,group in pairs.items():
  cb=[t for t in group if t['stage']=='A-callback'];eq=[t for t in group if t['stage']=='A-enqueue']
  if len(cb)==len(eq)==1:lags.append(dict(pid=key[0],kind=key[1],signedCallbackToEnqueue=(eq[0]['qpc']-cb[0]['qpc'])/freq))
 stages=a['stageMaxima'];names=('event.File.AppendAllText','event.exists','event.stat','event.metadata','event.payload','entry.properties','event.serialize','queue.identity.lookup','queue.item.read','queue.reference.Index','queue.exact.RemoveAt')
 sub={n:stages.get(n) for n in names}
 largest=max((v for v in sub.values() if v is not None),key=lambda v:v['seconds'])
 result=dict(run=name,monitorHealth=a['monitorHealth'],coverage=a['coverage'],maxHeartbeatInterval=a['maxHeartbeatInterval'],maxHeartbeatAge=a['maxHeartbeatAge'],maxDrain=max(drains,key=lambda x:x['seconds']),maxBatch=max(v['processed'] for v in drains),maxQueueDepth=q['maxDepth'],drains=drains,maxEvent=stages.get('event'),substageMaxima=sub,longestIndividualSubstage=largest,
  longestLockWait=max((v for k,v in stages.items() if k.startswith('lock.') and k.endswith('.wait')),key=lambda x:x['seconds']),longestLockHold=max((v for k,v in stages.items() if k.startswith('lock.') and k.endswith('.hold')),key=lambda x:x['seconds']),
  starts=sum(e['kind']=='start' for e in events),stops=sum(e['kind']=='stop' for e in events),externalCollisions=a['externalCollisions'],internalCollisions=a['internalCollisions'],producerObserverLags=lags,producerScheduling='Not directly measured. Signed callback/enqueue tap deltas are observer timing, not kernel scheduling. Callback tap attaches after original handler.',consumerScheduling='Per-thread CPU versus wall timing and wait overruns; exact kernel scheduler cause not measured.',telemetry=a['config']['telemetry'])
 with (d/'event-analysis.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps({k:result[k] for k in ('run','monitorHealth','coverage','maxHeartbeatInterval','maxHeartbeatAge','maxDrain','longestIndividualSubstage','longestLockWait','longestLockHold','starts','stops')}))
if __name__=='__main__':one(sys.argv[1])
