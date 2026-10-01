"""Sacrificial subsets; never performs protected hashing or acceptance sealing."""
import pathlib,sys,json,hashlib,time,os,zipfile
from workspace import run_dir,activate_temp
from journal import ticks
root=run_dir(sys.argv[1]);activate_temp(root);phase=sys.argv[2]
assert phase in 'BCDEF'
source=pathlib.Path(r'C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-heartbeat-journal-20260918\sacrificial')
trace=[]
def note(stage,**kw):trace.append(dict(stage=stage,qpc=ticks(),**kw))
def check():
 if (root/'workload-stop').exists():raise RuntimeError('Diagnostic workload cancelled')
def save(n,v):
 note('write.begin',file=n)
 with (root/n).open('x') as f:json.dump(v,f,sort_keys=True,indent=2)
 note('write.end',file=n)
def snapshot(number):
 note('enumerate.begin',passNumber=number);files=sorted(source.iterdir());note('enumerate.end',passNumber=number)
 if len(files)!=12 or any(not p.is_file() or p.suffix!='.bin' or p.is_symlink() or p.is_junction() for p in files):raise RuntimeError('Exact sacrificial source required')
 result={}
 for p in files:
  check();note('stat.before',file=p.name,passNumber=number);before=p.stat();h=hashlib.sha256();note('open.begin',file=p.name,passNumber=number)
  with p.open('rb') as f:
   note('open.end',file=p.name,passNumber=number)
   while True:
    check();a=ticks();b=f.read(4194304);c=ticks();h.update(b);e=ticks()
    trace.append(dict(stage='read.hash',file=p.name,passNumber=number,start=a,readEnd=c,end=e,bytes=len(b)))
    if not b:break
  note('file.closed',file=p.name,passNumber=number);after=p.stat()
  if before.st_size!=after.st_size or before.st_mtime_ns!=after.st_mtime_ns:raise RuntimeError('Sacrificial metadata changed')
  result[p.name]=dict(size=after.st_size,mtime_ns=after.st_mtime_ns,sha256=h.hexdigest())
 return result
try:
 note('entry');first=snapshot(1);save('pass1.json',first)
 if phase in 'CDEF':
  second=snapshot(2);save('pass2.json',second)
  if first!=second:raise RuntimeError('Sacrificial hash mismatch')
 if phase in 'DEF':save('synthetic-manifest.json',dict(synthetic=True,files=first));save('synthetic-manifest-hash.json',dict(sha256=hashlib.sha256((root/'synthetic-manifest.json').read_bytes()).hexdigest()))
 if phase in 'EF':
  members=['pass1.json','pass2.json','synthetic-manifest.json','synthetic-manifest-hash.json'];note('archive.begin')
  with zipfile.ZipFile(root/'synthetic-evidence.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
   for n in members:z.write(root/n,n)
  with (root/'synthetic-evidence.zip').open('r+b',buffering=0) as f:os.fsync(f.fileno())
  with zipfile.ZipFile(root/'synthetic-evidence.zip') as z:
   for n in members:
    if z.read(n)!=(root/n).read_bytes():raise RuntimeError('Synthetic archive verification failed')
  note('archive.verified')
 if phase=='F':
  note('reconciliation.begin');assert first==second;assert len(first)==12;note('reconciliation.end')
 note('completed')
except BaseException:
 import traceback
 note('failure',traceback=traceback.format_exc());raise
finally:
 with (root/'worker-trace.json').open('x') as f:json.dump(trace,f,indent=2)
