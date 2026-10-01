import ctypes,json,subprocess,uuid,time,sys,hashlib
from ctypes import wintypes as W
from pathlib import Path
R=Path(__file__).parent;info=json.loads((R/'candidate.json').read_text());C=Path(info['code']);old=Path(info['old']);sys.path.insert(0,str(C/'medium-checker'));import qualification as q;import telemetry
kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.GetProcessTimes.argtypes=[W.HANDLE,*([ctypes.POINTER(W.FILETIME)]*4)];kernel.GetProcessTimes.restype=W.BOOL;kernel.WaitForSingleObject.argtypes=[W.HANDLE,W.DWORD];kernel.WaitForSingleObject.restype=W.DWORD
def times(h):
 a,b,c,d=[W.FILETIME() for _ in range(4)];assert kernel.GetProcessTimes(h,*[ctypes.byref(x) for x in (a,b,c,d)])
 return dict(created=(a.dwHighDateTime<<32)|a.dwLowDateTime,exit=(b.dwHighDateTime<<32)|b.dwLowDateTime)
root=C/('overhead-'+uuid.uuid4().hex);root.mkdir();rows=[];canonical=None
for i in range(3):
 for name,code in [('baseline',old),('telemetry',C)]:
  dest=root/f'{i}-{name}';dest.mkdir();exe=code/'J6DurableTest.exe';start=time.perf_counter()
  p=subprocess.Popen([str(exe),str(dest),'0','3000'],cwd=code,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);h=W.HANDLE(int(p._handle));creation=times(h)
  out,err=p.communicate(timeout=15);elapsed=time.perf_counter()-start;exit=times(h);signaled=kernel.WaitForSingleObject(h,0)==0;p._handle.Close()
  record=dict(pair=i,kind=name,pid=p.pid,executable=str(exe),executableSHA256=hashlib.sha256(exe.read_bytes()).hexdigest(),created=creation,exitTimes=exit,kernelSignaled=signaled,wallSeconds=elapsed,exit=p.returncode,stdout=out,stderr=err)
  with (dest/'process.json').open('x') as f:json.dump(record,f,indent=2)
  assert p.returncode==0 and signaled and creation['created']==exit['created'] and exit['exit']>0
  events,m,w=q.stream(dest,'durable');digest=hashlib.sha256(json.dumps(events,sort_keys=True).encode()).hexdigest()
  if canonical is None:canonical=digest
  assert digest==canonical and len(events)==3000
  record['statistics']=json.loads(out)
  if name=='telemetry':record['telemetry']=telemetry.verify(dest,'durable')
  rows.append(record)
with (R/'overhead-results.json').open('x') as f:json.dump(dict(status='PASS',cases=6,recordsPerCase=3000,contentEquality=True,rows=rows,limitation='Alternating finite samples on this host, not a controlled causal overhead bound or sustained throughput guarantee.'),f,indent=2)
print(json.dumps(dict(status='PASS',cases=6,times=[dict(pair=r['pair'],kind=r['kind'],wall=r['wallSeconds'],writer=r['statistics']['result']['elapsedSeconds']) for r in rows])))
