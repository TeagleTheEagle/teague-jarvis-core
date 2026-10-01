"""Fixed protocol validation/statistics. Never executes a benchmark."""
import json,statistics,math,hashlib,pathlib
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def validate(rows,exit_code,protocol_hash):
 if exit_code!=0:raise ValueError('nonzero exit')
 if len(rows)!=182:raise ValueError('incomplete or extra output')
 h=rows[0]
 if h.get('schema')!='j6.final-overhead.raw.v1' or h.get('kind')!='header':raise ValueError('unsupported schema')
 if h.get('protocolSHA256')!=protocol_hash:raise ValueError('wrong protocol')
 if not all(isinstance(h.get(k),int) and h[k]>0 for k in ['pid','created','tid','frequency']):raise ValueError('identity/clock')
 schedule=['ABC','BCA','CAB','ACB','CBA','BAC']*10
 groups=[]
 for b in range(60):
  block={};digests=[]
  for pos,arm in enumerate(schedule[b]):
   t=rows[1+3*b+pos]
   if (t.get('kind'),t.get('block'),t.get('position'),t.get('arm'),t.get('warmup'),t.get('callbacks'))!=('trial',b,pos,arm,20000,1000000):raise ValueError('trial order/count')
   chunks=t.get('chunks',[])
   if len(chunks)!=123:raise ValueError('chunk count')
   cpu=wall=count=0;digest=0;last_cpu=None;last_wall=None
   for i,x in enumerate(chunks):
    if len(x)!=12 or not all(isinstance(v,int) and v>=0 for v in x):raise ValueError('malformed chunk')
    s,ch,n,k0,u0,k1,u1,tid0,tid1,w0,w1,d=x
    if (s,ch,n)!=(i%11,(i//11)%2,8192 if i<122 else 576):raise ValueError('workload/count')
    if tid0!=h['tid'] or tid1!=h['tid'] or k1<k0 or u1<u0 or w1<w0:raise ValueError('counter/thread')
    if last_cpu is not None and (k0<last_cpu[0] or u0<last_cpu[1] or w0<last_wall):raise ValueError('counter continuity')
    last_cpu=(k1,u1);last_wall=w1
    cpu+=k1-k0+u1-u0;wall+=w1-w0;count+=n;digest=((digest^d)*1099511628211)&((1<<64)-1)
   if (cpu,wall,count,digest)!=(t.get('cpu100ns'),t.get('wallTicks'),1000000,t.get('workloadDigest')) or cpu<=0 or wall<=0:raise ValueError('totals')
   digests.append([x[11] for x in chunks]);block[arm]=dict(ns=cpu*100/1000000,throughput=1000000/(wall/h['frequency']))
  if digests[0]!=digests[1] or digests[0]!=digests[2]:raise ValueError('different input/output outcomes')
  groups.append(block)
 end=rows[-1]
 if end!={'kind':'complete','blocks':60,'trials':180,'callbacks':180000000,'warmup':3600000}:raise ValueError('missing completion')
 return groups
def interval(values):
 means=[statistics.mean(values[i:i+10]) for i in range(0,60,10)]
 estimate=statistics.mean(means);half=2.570581835636305*statistics.stdev(means)/math.sqrt(6)
 return dict(estimate=estimate,lower=estimate-half,upper=estimate+half,groupMeans=means,halfWidth=half)
def analyze(blocks):
 metrics={'optimizedPercent':[100*(b['C']['ns']/b['A']['ns']-1) for b in blocks],
 'referencePercent':[100*(b['B']['ns']/b['A']['ns']-1) for b in blocks],
 'reuseSavingNs':[b['B']['ns']-b['C']['ns'] for b in blocks],
 'optimizedDeltaNs':[b['C']['ns']-b['A']['ns'] for b in blocks],
 'throughputPercent':[100*(b['C']['throughput']/b['A']['throughput']-1) for b in blocks]}
 stats={k:interval(v) for k,v in metrics.items()};v=metrics['optimizedPercent'];m=statistics.mean(v);xx=list(range(60));slope=sum((i-29.5)*(x-m) for i,x in enumerate(v))/sum((i-29.5)**2 for i in xx)
 residual=[x-m for x in stats['optimizedPercent']['groupMeans']];den=sum(x*x for x in residual)
 position={arm:{str(p):statistics.mean([b[arm]['ns'] for i,b in enumerate(blocks) if ['ABC','BCA','CAB','ACB','CBA','BAC'][i%6].index(arm)==p]) for p in range(3)} for arm in 'ABC'}
 bounds=stats['optimizedPercent'];numerical='FINAL_OVERHEAD_SCREEN_PASSED' if bounds['upper']<=1 else 'OVERHEAD_SCREEN_FAILED' if bounds['lower']>1 else 'OVERHEAD_SCREEN_NOT_ESTABLISHED'
 return dict(statistics=stats,baselineNs=statistics.mean(b['A']['ns'] for b in blocks),optimizedNs=statistics.mean(b['C']['ns'] for b in blocks),numericalScreen=numerical,inferenceStatus='DRIFT_REVIEW_REQUIRED',finalStatus='INCONCLUSIVE',drift=dict(slopePercentagePointsPerBlock=slope,firstHalf=statistics.mean(v[:30]),lastHalf=statistics.mean(v[30:]),treatmentPositionMeans=position,groupedLag1=sum(residual[i]*residual[i-1] for i in range(1,6))/den if den else 0),note='Numerical screen is not final acceptance until declared drift/dependence review is completed. No estimator substitution.')
def load_raw(path):
 try:return [json.loads(x) for x in pathlib.Path(path).read_text().splitlines()]
 except Exception as e:raise ValueError('malformed output') from e
def verify_binding(binding):
 for x in binding['files']:
  if sha(x['path'])!=x['sha256']:raise ValueError('wrong binary/source identity')
 if sha(binding['protocol'])!=binding['protocolSHA256']:raise ValueError('wrong protocol binding')
