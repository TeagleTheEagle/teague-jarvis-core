"""F1/F2 read-only source audit and sacrificial evidence measurement before edits."""
import pathlib,json,hashlib,statistics,math
ROOT=pathlib.Path(__file__).resolve().parent;R=ROOT/'stage6-finalization-20260920';R.mkdir(exist_ok=False)
sources=[pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\fb8ef11d2c4d44cca4d352d4a9fdfc93\code'),pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\90e9469000dd4530a86b98fad67d7089\code')]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[];provenance=[]
for code in sources:
 for d in sorted(code.iterdir()):
  if not d.is_dir() or not (d/'probe-timings.json').exists():continue
  case=read(d/'case.json');tap=read(d/'tap.json');pipeline=read(d/'pipeline.json');q=read(d/'queue-entries.json')
  for n in ('case.json','probe-timings.json','tap.json','pipeline.json','queue-entries.json'):
   p=d/n;provenance.append(dict(path=str(p),sha256=sha(p)))
  for p in read(d/'probe-timings.json'):
   b=p['clockAfter'];f=p['frequency'];exitq=(b['qpcBefore']+b['qpcAfter'])/2+(int(p['finalKernelTimes'][1])-int(b['filetime']))*f/1e7
   callback=[t for t in tap if t['pid']==p['pid'] and t['kind']=='stop' and t['stage']=='A-callback']
   enq=[t for t in tap if t['pid']==p['pid'] and t['kind']=='stop' and t['stage']=='A-enqueue']
   drain=[t for t in pipeline if t['pid']==p['pid'] and t['stage']=='drain' and t['source'].startswith('J6TimingStop-')]
   persisted=[t for t in pipeline if t['pid']==p['pid'] and t['stage']=='persisted' and t['source'].startswith('J6TimingStop-')]
   if len(callback)!=1 or len(enq)!=1:raise RuntimeError('Missing/duplicate callback; bound cannot be inferred')
   row=dict(run=d.name,mode=case['mode'],pid=p['pid'],created=p['finalKernelTimes'][0],exitFiletime=p['finalKernelTimes'][1],callback=(callback[0]['qpc']-exitq)/f,enqueue=(enq[0]['qpc']-exitq)/f,drain=(drain[0]['qpc']-exitq)/f if len(drain)==1 else None,persisted=(persisted[0]['qpc']-exitq)/f if len(persisted)==1 else None,callbackAfterTwoSeconds=(callback[0]['qpc']-exitq)/f>2,clockBridgeWidth=(b['qpcAfter']-b['qpcBefore'])/f)
   rows.append(row)
def stats(v):
 v=sorted(v);n=len(v)
 def pct(p):
  z=(n-1)*p;i=int(z);return v[i]+(v[min(i+1,n-1)]-v[i])*(z-i)
 return dict(n=n,min=v[0],median=statistics.median(v),p95=pct(.95) if n>=20 else None,p99=pct(.99) if n>=100 else None,max=v[-1])
groups={mode:{key:stats([r[key] for r in rows if r['mode']==mode and r[key] is not None]) for key in ('callback','enqueue','drain','persisted')} for mode in ('idle','disk','sustained','cpu','Dhash')}
maximum=max(max(r['callback'],r['enqueue']) for r in rows);margin=max(1.0,maximum*.5);quiet=math.ceil((maximum+margin)*10)/10
summary=dict(samples=len(rows),groups=groups,maxObservedCallbackOrEnqueue=maximum,safetyMargin=margin,quietSeconds=quiet,rounding='ceil to 0.1 s',rationale='Observed maximum plus 50% margin, minimum one second. Finite empirical guard, not proof of a Windows maximum. Expected START/STOP coverage remains mandatory independently; missing event must fail at bounded finalization deadline.',oldGraceSeconds=2,lateAfterOldGrace=sum(r['callbackAfterTwoSeconds'] for r in rows),oldPostCollectorDeadlineSeconds=60,inputs='preserved sacrificial measurements, not fresh execution',clockUncertainty='QPC/precise FILETIME bridges; exact signal instant unobserved; primary callback tap attached after original handler')
for name,data in [('latency-samples.json',rows),('latency-summary.json',summary),('latency-input-hashes.json',provenance)]:
 with (R/name).open('x') as out:json.dump(data,out,indent=2)
source=sources[-1];audit=[]
for n in ('collect.py','monitor.ps1','event_queue.cs','EventTap.cs','journal.py','probe_timing.py'):
 p=source/n;st=p.stat();audit.append(dict(path=str(p),sha256=sha(p),size=st.st_size,mtime_ns=st.st_mtime_ns))
with (R/'audit-source-hashes.json').open('x') as out:json.dump(audit,out,indent=2)
print(json.dumps(summary,indent=2))
