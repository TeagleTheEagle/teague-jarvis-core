"""Synthetic bytes only; no VM reads. Not an acceptance run."""
import pathlib,json,os,time,hashlib,shutil,math
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'candidate.json').read_text())['code']);S=C/'large-synthetic'
assert not S.exists();assert shutil.disk_usage(C).free>140*2**30
S.mkdir();(S/'Snapshots').mkdir();(S/'Logs').mkdir()
total=59665402098
sizes=[32*2**30,16*2**30,7*2**30]+[8192,4096,65536,131072,1024,262144,524288,1048576]
sizes.append(total-sum(sizes));assert min(sizes)>0
names=['base.vdi','Snapshots/child.vdi','Snapshots/grandchild.vdi','machine.vbox','machine.vbox-prev','machine.nvram','Snapshots/state.nvram','Logs/VBox.log','misc.data','noextension','notes.txt','tail.img']
block=os.urandom(4*2**20);created=[]
for name,size in zip(names,sizes):
 p=S/name;start=time.perf_counter();remaining=size
 with p.open('xb',buffering=0) as f:
  while remaining:
   n=min(len(block),remaining);written=f.write(block[:n]);assert written==n;remaining-=n
  os.fsync(f.fileno())
 created.append(dict(path=name,bytes=size,seconds=time.perf_counter()-start,mtime_ns=p.stat().st_mtime_ns));print('CREATED '+name+' '+str(size),flush=True)
passes=[]
for i in (1,2):
 rows=[];start=time.perf_counter()
 for name in names:
  p=S/name;begin=time.perf_counter();h=hashlib.sha256()
  with p.open('rb',buffering=0) as f:
   while b:=f.read(4*2**20):h.update(b)
  rows.append(dict(path=name,bytes=p.stat().st_size,sha256=h.hexdigest(),seconds=time.perf_counter()-begin))
 result=dict(number=i,seconds=time.perf_counter()-start,files=rows);passes.append(result);print('HASH PASS '+str(i)+' '+str(result['seconds']),flush=True)
assert [(x['path'],x['sha256']) for x in passes[0]['files']]==[(x['path'],x['sha256']) for x in passes[1]['files']]
for x in created:assert (S/x['path']).stat().st_mtime_ns==x['mtime_ns']
slow=max(p['seconds'] for p in passes);estimate=2*slow;campaign=math.ceil((2*estimate+30)/30)*30;monitor=campaign+120
out=dict(source=str(S),synthetic=True,totalBytes=total,created=created,passes=passes,conservativeTwoPassSeconds=estimate,bytesPerSecond=total/slow,campaignSeconds=campaign,monitorSeconds=monitor,longRunTargetSeconds=math.ceil(estimate*1.5),derivation='2x slowest full pass for expected two passes; campaign=ceil30(2x expected+30s); monitor=campaign+120s closure/start reserve; long run >=1.5x expected',cachedLogicalReads=True,protectedAccess=False)
with (C/'calibration.json').open('x') as f:json.dump(out,f,indent=2)
with (R/'calibration.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ('created','passes')}),flush=True)
