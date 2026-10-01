"""TEST-only measurement verifier. Does not grant lifecycle acceptance."""
import collections,hashlib,json,math,stat
from pathlib import Path
SCHEMA='stage6-writer-telemetry-v1'
def need(x,reason):
 if not x:raise ValueError(reason)
def pairs(xs):
 d={}
 for k,v in xs:need(k not in d,'DUPLICATE_KEY');d[k]=v
 return d
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('NONFINITE')))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def integer(n):return type(n) is int and n>=0
def stats(ticks,f):
 need(ticks and all(integer(x) for x in ticks) and type(f) is int and f>0,'TIMING_SAMPLE')
 v=sorted(ticks);return dict(count=len(v),meanSeconds=sum(v)/len(v)/f,maxSeconds=v[-1]/f,p95Seconds=v[math.ceil(.95*len(v))-1]/f)
def validate(t,m,w):
 need(set(t)=={'schema','frequency','capacity','snapshotBytes','allocatedBytes','overflow','backpressure','lag','windows','snapshots'},'TELEMETRY_FIELDS')
 need(t['schema']==SCHEMA and t['overflow'] is False,'TELEMETRY_SCHEMA_OR_OVERFLOW')
 f=t['frequency'];need(type(f) is int and f>0,'FREQUENCY')
 need(t['capacity']==65536 and t['snapshotBytes']==80 and t['allocatedBytes']==5242880,'MEMORY_BOUND')
 need(w['fault']==0 and w['threadsExited'] and w['attempted']==w['accepted']==w['written']==m['accepted']>0,'WRITER_FAILURE')
 seg=m['segments'];need(seg and len(seg)==len(w['segments']),'SEGMENT_COVERAGE')
 flush=[];hashes=[];st={};wait=[];ft=[]
 fields={'enqueued','dequeued','completed','flushBegin','flushEnd','hashBegin','hashEnd','waitBegin','waitEnd'}
 for i,(s,z) in enumerate(zip(seg,w['segments'])):
  need(s['number']==i and s['states']==[0,1,2,3,4] and z['states']==[0,1,2,3,4,5],'SEGMENT_STATES')
  need({k:v for k,v in s.items() if k!='states'}=={k:v for k,v in z.items() if k!='states'},'MANIFEST_CONFLICT')
  a=s['timing'];need(set(a)==fields and all(integer(v) for v in a.values()),'TIMING_FIELDS')
  order=[a[k] for k in ('enqueued','dequeued','flushBegin','flushEnd','hashBegin','hashEnd','completed')]
  need(order[0]>0 and order==sorted(order),'TIMING_ORDER')
  need((a['waitBegin']==a['waitEnd']==0) or 0<a['waitBegin']<=a['waitEnd']<=a['enqueued'],'WAIT_TIMING')
  if a['waitBegin']:wait.append(a['waitEnd']-a['waitBegin'])
  flush.append(a['flushEnd']-a['flushBegin']);hashes.append(a['hashEnd']-a['hashBegin']);ft.append(a['dequeued']-a['enqueued']);st[i]=s
 def approx(a,b):return type(a) in (int,float) and math.isfinite(a) and math.isclose(a,b,rel_tol=1e-9,abs_tol=2/f)
 need(approx(w['flushSeconds'],sum(flush)/f) and approx(w['maxFlushSeconds'],max(flush)/f) and approx(w['hashSeconds'],sum(hashes)/f),'AGGREGATE_CONFLICT')
 bp=t['backpressure'];need(set(bp)=={'started','completed','interrupted','ticks'} and all(integer(x) for x in bp.values()),'BACKPRESSURE_FIELDS')
 need(bp['started']==bp['completed']==len(wait) and bp['interrupted']==0 and bp['ticks']==sum(wait),'BACKPRESSURE_CONFLICT')
 rows=t['snapshots'];need(2<=len(rows)<=65536,'SNAPSHOT_COUNT')
 q=collections.deque();fq=collections.deque();active=None;fa=None;inflight={};pending=set();admit={};deqlag=[];complag=[];seen=collections.Counter();credits={};peaks=[0,0,0];prev=0
 for index,x in enumerate(rows):
  need(type(x) is list and len(x)==10 and all(integer(v) for v in x),'SNAPSHOT_FIELDS')
  tick,kind,id,raw,depth,count,size,queued,pc,pb=x
  need(tick>=prev and tick>0,'SNAPSHOT_TIME');prev=tick;seen[kind]+=1
  if kind==0:need(index==0 and id==raw==0,'INITIAL_STATE')
  elif kind==1:
   need(id==len(admit)+1 and raw>0,'ADMISSION_SEQUENCE');admit[id]=tick;inflight[id]=raw;q.append(id)
  elif kind==2:
   need(active is None and q and q.popleft()==id and inflight[id]==raw,'DEQUEUE_IDENTITY');active=id;deqlag.append(tick-admit[id])
  elif kind==3:
   need(active==id and inflight[id]==raw,'WRITE_IDENTITY');active=None;del inflight[id];complag.append(tick-admit[id])
  elif kind==4:
   need(id in st and id not in pending and len(pending)<2 and st[id]['timing']['enqueued']<=tick,'FINALIZER_ADMISSION');pending.add(id);fq.append(id)
  elif kind==5:
   need(fa is None and fq and fq.popleft()==id and st[id]['timing']['dequeued']<=tick,'FINALIZER_DEQUEUE');fa=id
  elif kind==6:
   need(fa==id and id in pending and st[id]['timing']['completed']<=tick,'FINALIZER_COMPLETION');fa=None;pending.remove(id)
  elif kind==7:need(index==len(rows)-1 and not inflight and not pending and not q and not fq and active is None and fa is None,'FINAL_QUEUE_STATE')
  elif kind==8:
   need(len(pending)==2 and id not in credits and 0<st[id]['timing']['waitBegin']<=tick,'WAIT_START');credits[id]=tick
  elif kind==9:
   need(len(pending)<2 and id in credits and st[id]['timing']['waitEnd']<=tick,'WAIT_END');del credits[id]
  else:raise ValueError('INVALID_OR_FAILED_TRANSITION')
  need([depth,count,size,queued,pc,pb]==[len(q),len(inflight),sum(inflight.values()),len(fq),len(pending),sum(st[n]['bytes'] for n in pending)],'QUEUE_STATE_CONFLICT')
  need(depth<=count<=65536 and size<=67108864 and queued<=pc<=2,'QUEUE_BOUND')
  peaks=[max(peaks[0],count),max(peaks[1],size),max(peaks[2],pc)]
 need(seen[0]==seen[7]==1 and seen[1]==seen[2]==seen[3]==m['accepted'] and seen[4]==seen[5]==seen[6]==len(seg),'TRANSITION_COVERAGE')
 need(not credits and seen[8]==seen[9]==bp['started'],'WAIT_COVERAGE')
 need(peaks==[w['peakQueueItems'],w['peakQueueBytes'],w['peakPending']],'HIGH_WATER_CONFLICT')
 expected=dict(dequeued=len(deqlag),completed=len(complag),dequeueTicks=sum(deqlag),maxDequeueTicks=max(deqlag),completionTicks=sum(complag),maxCompletionTicks=max(complag))
 need(t['lag']==expected,'LAG_CONFLICT')
 win=t['windows'];need(set(win)=={'firstWrite','lastWrite','firstFinal','lastFinal'} and all(integer(v) and v>0 for v in win.values()),'WINDOW_FIELDS')
 need(rows[0][0]<=win['firstWrite']<=win['lastWrite']<=rows[-1][0] and rows[0][0]<=win['firstFinal']<=win['lastFinal']<=rows[-1][0],'WINDOW_ORDER')
 return dict(schema=SCHEMA,status='TELEMETRY_VERIFIED_NOT_LIFECYCLE_ACCEPTANCE',segments=len(seg),snapshots=len(rows),flush=stats(flush,f),readbackHashVerification=stats(hashes,f),backpressure=bp,writerDequeueLag=stats(deqlag,f),writerCompletionLag=stats(complag,f),finalizerQueueLag=stats(ft,f),slowHeartbeatWarnings='NOT CONFIGURED',heartbeatFailureSeconds=10)
def verify(root,prefix='kernel-authority'):
 root=Path(root);m=load(root/(prefix+'-manifest.json'));w=load(root/(prefix+'-result.json'));seal=load(root/(prefix+'-seal.json'))
 need(seal['manifestSHA256']==sha(root/(prefix+'-manifest.json')),'MANIFEST_HASH')
 ref=m['telemetry'];need(ref==w['telemetry'] and set(ref)=={'schema','name','sha256'} and ref['schema']==SCHEMA and ref['name']==prefix+'-telemetry.json','TELEMETRY_BINDING')
 path=root/ref['name'];need(not (path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT) and sha(path)==ref['sha256'],'TELEMETRY_HASH_OR_REPARSE')
 t=load(path);return validate(t,m,w)
