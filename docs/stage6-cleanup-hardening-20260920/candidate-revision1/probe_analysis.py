import pathlib,json,sys,statistics,collections
from workspace import run_dir
R=run_dir(sys.argv[1])
def read(n):return json.loads((R/n).read_text(encoding='utf-8-sig'))
rows=read('probe-timings.json');events=[json.loads(x) for x in (R/'events.jsonl').read_text().splitlines()];counts=collections.Counter((x['pid'],x['kind']) for x in events)
def dist(xs):
 xs=sorted(xs);n=len(xs)
 def percentile(p):
  i=(n-1)*p;l=int(i);return xs[l]+(xs[min(l+1,n-1)]-xs[l])*(i-l)
 return dict(n=n,min=xs[0],median=statistics.median(xs),p95=percentile(.95) if n>=20 else None,p99=percentile(.99) if n>=100 else None,max=xs[-1]) if n else None
measurements=[]
for p in rows:
 f=p['frequency'];ts=p['finalKernelTimes'];b=p['clockAfter'];mid=(b['qpcBefore']+b['qpcAfter'])/2
 exitq=mid+(int(ts[1])-int(b['filetime']))*f/1e7
 item=dict(pid=p['pid'],created=ts[0],exit=ts[1],kernelLifetime=(int(ts[1])-int(ts[0]))/1e7,createProcessSeconds=(p['createProcessReturnedQpc']-p['createProcessCalledQpc'])/f,popenSeconds=(p['popenReturnedQpc']-p['launchRequestedQpc'])/f,mainWaitSeconds=(p.get('mainWaitReturnedQpc',p.get('timeoutCaughtQpc'))-p['mainWaitEnteredQpc'])/f,observerLatencyEstimate=(p['observerReturnedQpc']-exitq)/f,bridgeWidth=(b['qpcAfter']-b['qpcBefore'])/f,timedOut=p['timedOut'],actualExitCode=p['actualExitCode'],kernelSeconds=int(ts[2])/1e7,userSeconds=int(ts[3])/1e7,firstInstruction=None,workBegin=None,workEnd=None,exitInitiated=None)
 before=p['clockBefore'];offsetBefore=(before['qpcBefore']+before['qpcAfter'])/2/f-int(before['filetime'])/1e7;offsetAfter=mid/f-int(b['filetime'])/1e7;item['bridgeOffsetChange']=offsetAfter-offsetBefore
 if p['finalHandleState']!=0 or counts[p['pid'],'start']!=1 or counts[p['pid'],'stop']!=1:raise RuntimeError('Retained-handle lifecycle evidence mismatch')
 measurements.append(item)
a=read('analysis.json');e=read('event-analysis.json');fsnames=('event.exists','event.stat','event.File.AppendAllText','journal.size','journal.write','journal.flush','finish.query')
result=dict(run=R.name,acceptance=False,mode=read('case.json')['mode'],count=len(rows),timeoutCount=sum(x['timedOut'] for x in measurements),slowWarningCount=sum(bool(x.get('slowWarnings')) for x in rows),exitsZero=all(x['actualExitCode']==0 for x in measurements),lifetime=dist([x['kernelLifetime'] for x in measurements]),creation=dist([x['createProcessSeconds'] for x in measurements]),popen=dist([x['popenSeconds'] for x in measurements]),wait=dist([x['mainWaitSeconds'] for x in measurements]),observationEstimate=dist([x['observerLatencyEstimate'] for x in measurements]),heartbeatInterval=a['maxHeartbeatInterval'],heartbeatAge=a['maxHeartbeatAge'],longestDrain=e['maxDrain']['seconds'],longestFilesystem=max((a['stageMaxima'][n] for n in fsnames),key=lambda x:x['seconds']),starts=e['starts'],stops=e['stops'],internalCollisions=a['internalCollisions'],externalCollisions=a['externalCollisions'],measurements=measurements,note='Native work/first-instruction/exit-initiation unobserved. Exit observation estimate uses UTC/QPC bridges, not exact kernel signal time. New owner-approved model: 5 s warning, 13.6 s hard deadline; no historical result changed.')
with (R/'probe-analysis.json').open('x') as out:json.dump(result,out,indent=2)
print(json.dumps({k:v for k,v in result.items() if k not in ('measurements','longestFilesystem')}))
