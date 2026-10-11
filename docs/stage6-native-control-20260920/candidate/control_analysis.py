import pathlib,json,sys,statistics,collections
from workspace import run_dir
R=run_dir(sys.argv[1])
def read(n):return json.loads((R/n).read_text(encoding='utf-8-sig'))
def dist(xs):
 if not xs:return None
 xs=sorted(xs);n=len(xs)
 def pct(p):
  x=(n-1)*p;i=int(x);return xs[i]+(xs[min(i+1,n-1)]-xs[i])*(x-i)
 return dict(n=n,min=xs[0],median=statistics.median(xs),p95=pct(.95) if n>=20 else None,p99=pct(.99) if n>=100 else None,max=xs[-1])
metrics=read('probe-analysis.json');raw=read('probe-timings.json');rows=[]
checksum=1
for _ in range(10000):checksum=(checksum*1664525+1013904223)&0xffffffff
for p in raw:
 m=next(x for x in metrics['measurements'] if x['pid']==p['pid']);m['control']=p['control'];f=p['frequency'];b=p['clockAfter'];mid=(b['qpcBefore']+b['qpcAfter'])/2
 def qpc(ft):return mid+(int(ft)-int(b['filetime']))*f/1e7
 n=p.get('nativeMarkers')
 if n:
  if n['result']!=(checksum if p['control'].startswith('B_') else 1):raise RuntimeError('Unexpected helper work result')
  m.update(firstActivityQpc=n['firstActivityQpc'],entryAfterCreateReturn=(n['firstActivityQpc']-p['createProcessReturnedQpc'])/f,creationToEntryEstimate=(n['firstActivityQpc']-qpc(p['finalKernelTimes'][0]))/f,markerSetup=(n['workBeginQpc']-n['firstActivityQpc'])/f,workSeconds=(n['workEndQpc']-n['workBeginQpc'])/f,preExitQpc=n['exitBeginQpc'],exitTailEstimate=(qpc(p['finalKernelTimes'][1])-n['exitBeginQpc'])/f)
 rows.append(m)
groups={}
for control in sorted(set(x['control'] for x in rows)):
 values=[x for x in rows if x['control']==control]
 groups[control]=dict(count=len(values),timeouts=sum(x['timedOut'] for x in values),over1=sum(x['kernelLifetime']>1 for x in values),over3=sum(x['kernelLifetime']>3 for x in values),over5=sum(x['kernelLifetime']>5 for x in values))
 for key in ('kernelLifetime','createProcessSeconds','observerLatencyEstimate','entryAfterCreateReturn','creationToEntryEstimate','markerSetup','workSeconds','exitTailEstimate'):
  groups[control][key]=dist([x[key] for x in values if key in x])
result=dict(run=R.name,mode=read('case.json')['mode'],acceptance=False,groups=groups,rows=rows,heartbeatInterval=metrics['heartbeatInterval'],heartbeatAge=metrics['heartbeatAge'],starts=metrics['starts'],stops=metrics['stops'],timeouts=metrics['timeoutCount'],longestFilesystem=metrics['longestFilesystem'],limits=dict(probe=5,heartbeat=10))
with (R/'control-analysis.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
