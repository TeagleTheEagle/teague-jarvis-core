"""Post-run observational comparison, never grants monitor acceptance."""
import pathlib,json,hashlib,statistics,collections,difflib,ast
R=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(n,x):
 with (R/n).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
CODE=pathlib.Path(read(R/'plan.json')['live_code']);runs=[];rows=[]
def dist(xs):
 if not xs:return None
 xs=sorted(xs);n=len(xs)
 def pct(q):
  pos=(n-1)*q;i=int(pos);return xs[i]+(xs[min(i+1,n-1)]-xs[i])*(pos-i)
 return dict(n=n,min=xs[0],median=statistics.median(xs),p95=pct(.95) if n>=20 else None,p99=pct(.99) if n>=100 else None,max=xs[-1])
for d in sorted(CODE.iterdir()):
 if not d.is_dir() or not (d/'case.json').exists():continue
 a=read(d/'control-analysis.json');runs.append({k:v for k,v in a.items() if k not in ('rows','groups')})
 for x in a['rows']:rows.append(dict(run=d.name,mode=a['mode'],**x))
groups=[]
for mode in ('idle','disk','sustained','Dhash'):
 for control in ('A_D','A_C','B_D','B_C','D_D','D_C','C_D'):
  g=[x for x in rows if x['mode']==mode and x['control']==control]
  result=dict(mode=mode,control=control,count=len(g),timeouts=sum(x['timedOut'] for x in g),over1=sum(x['kernelLifetime']>1 for x in g),over3=sum(x['kernelLifetime']>3 for x in g),over5=sum(x['kernelLifetime']>5 for x in g))
  for key in ('kernelLifetime','createProcessSeconds','mainWaitSeconds','observerLatencyEstimate','creationToEntryEstimate','entryAfterCreateReturn','markerSetup','workSeconds','exitTailEstimate'):
   result[key]=dist([x[key] for x in g if key in x])
  groups.append(result)
slow=[]
for x in rows:
 if x['kernelLifetime']>.5 or x['createProcessSeconds']>.5:
  stages=[key for key in ('createProcessSeconds','creationToEntryEstimate','markerSetup','workSeconds','exitTailEstimate') if x.get(key,0)>.5]
  slow.append(dict(observedSlowStages=stages,**x))
images=read(R/'helper-images.json')
for x in images:
 x['unchanged']=sha(pathlib.Path(x['cPath']))==sha(pathlib.Path(x['dPath']))==x['sha256']
 if not x['unchanged']:raise RuntimeError('Helper image changed')
save('helper-image-verification.json',images)
old=R.parent/'stage6-probe-diagnosis-20260920';receipt=read(old/'archive-verification.json')
if sha(old/'evidence.zip')!=receipt['zipSHA256'] or sha(old/'archive-manifest.json')!=receipt['manifestSHA256']:raise RuntimeError('Previous archive changed')
save('previous-archive-preservation.json',dict(unchanged=True,receipt=receipt))
syntax=[]
for p in sorted(list(CODE.glob('*.py'))+list(R.glob('*.py'))):ast.parse(p.read_text(encoding='utf-8-sig'));syntax.append(str(p))
save('python-syntax.json',dict(status='PASS',files=syntax,method='AST parse only'))
save('control-summary.json',dict(acceptance=False,groups=groups,runs=runs,totalProbes=len(rows),timeouts=sum(x['timedOut'] for x in rows),starts=sum(x['starts'] for x in runs),stops=sum(x['stops'] for x in runs),maxHeartbeat=max(x['heartbeatInterval'] for x in runs),maxAge=max(x['heartbeatAge'] for x in runs),maxFilesystem=max(x['longestFilesystem']['seconds'] for x in runs)))
save('slow-controls.json',slow)
save('all-control-measurements.json',rows)
print(json.dumps(dict(probes=len(rows),timeouts=sum(x['timedOut'] for x in rows),slow=len(slow),groups=groups),indent=2))
