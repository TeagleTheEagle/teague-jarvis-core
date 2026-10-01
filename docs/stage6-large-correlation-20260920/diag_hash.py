"""Bounded sacrificial partial hashing, never a baseline hash pass."""
import sys,pathlib,json,hashlib,time,os
from workspace import run_dir,activate_temp
from evidence_support import put
from journal import ticks,frequency
root=run_dir(sys.argv[1]);activate_temp(root);seconds=int(sys.argv[2]);label=sys.argv[3]
assert seconds in (5,12,20,30) and label in ('B','C','D','heartbeat')
plan=json.loads((pathlib.Path(__file__).parent/'diagnostic-plan.json').read_text());p=pathlib.Path(plan['file']);expected=plan['metadata']
assert p==pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\1c1f5d0c390b42cc9ba9f4f6221dabc6\code\large-synthetic\Snapshots\child.vdi')
for q in (p,*p.parents):assert not q.lstat().st_file_attributes&0x400
before=p.stat();assert before.st_size==expected['bytes'] and before.st_mtime_ns==expected['mtime_ns'] and before.st_ino==expected['fileId']
trace=[];start=ticks();total=0;h=hashlib.sha256();canceled=False
try:
 with p.open('rb',buffering=0) as f:
  while (ticks()-start)/frequency()<seconds and total<8*2**30:
   if (root/'workload-stop').exists():canceled=True;break
   a=ticks();b=f.read(4*2**20);r=ticks()
   if not b:break
   h.update(b);e=ticks();total+=len(b);trace.append(dict(begin=a,readEnd=r,end=e,bytes=len(b),total=total))
 after=p.stat();assert (after.st_size,after.st_mtime_ns,after.st_ino)==(before.st_size,before.st_mtime_ns,before.st_ino)
finally:put(root/('hash-'+label+'.json'),dict(begin=start,end=ticks(),requestedSeconds=seconds,bytes=total,partialHash=h.hexdigest(),canceled=canceled,file=str(p),trace=trace,baselinePass=False))
