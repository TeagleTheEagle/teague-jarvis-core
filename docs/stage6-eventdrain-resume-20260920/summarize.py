import pathlib,json,hashlib,sys,collections,datetime
R=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cases=[]
 for n in ('a1','minimal','persist-d','none','dhash','a2','a3'):
  d=R/n
  if not (d/'event-analysis.json').exists():cases.append(dict(run=n,status='NOT RUN/INCOMPLETE'));continue
  a=read(d/'analysis.json');e=read(d/'event-analysis.json');s=e['substageMaxima']
  case=dict(run=n,status=e['monitorHealth'],coverage=e['coverage'],interval=e['maxHeartbeatInterval'],age=e['maxHeartbeatAge'],drain=e['maxDrain']['seconds'],maxBatch=e['maxBatch'],maxDepth=e['maxQueueDepth'],maxEvent=e['maxEvent']['seconds'],lockWait=e['longestLockWait']['seconds'],lockHold=e['longestLockHold']['seconds'],exists=s['event.exists']['seconds'],stat=s['event.stat']['seconds'],write=s['event.File.AppendAllText']['seconds'],eventMetadata=s['event.metadata']['seconds'],remove=s['queue.exact.RemoveAt']['seconds'],starts=e['starts'],stops=e['stops'],externalCollisions=e['externalCollisions'],internalCollisions=e['internalCollisions'],waitOverrun=a['waitDeadlineOverrun'],observerJitter=a['independentSleepObserverMaxExcess'],traceOverhead=a['traceInstrumentationMaxSeconds'],gcPauseSeconds=a['gcPauseDeltaSeconds'],telemetry=e['telemetry'])
  case['storage']={k:v for k,v in a['storageAndCpu'].items() if '(1 c:)' in k or '(0 d:)' in k}
  case['cpu']={k:v for k,v in a['storageAndCpu'].items() if 'processor(_total)' in k or 'memory' in k}
  cases.append(case)
 print(json.dumps(cases,indent=2))
 if len(sys.argv)>1 and sys.argv[1]=='save':
  with (R/'campaign-summary.json').open('x') as f:json.dump(cases,f,indent=2)
if __name__=='__main__':main()
