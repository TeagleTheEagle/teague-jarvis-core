import json,subprocess,uuid,time,sys,ctypes,hashlib
from pathlib import Path
from ctypes import wintypes as W
R=Path(__file__).parent;C=Path(json.loads((R/'candidate.json').read_text())['code']);sys.path.insert(0,str(C/'medium-checker'))
import telemetry as tv
import qualification as q
K=ctypes.WinDLL('kernel32',use_last_error=True)
K.GetProcessTimes.argtypes=[W.HANDLE,*([ctypes.POINTER(W.FILETIME)]*4)];K.GetProcessTimes.restype=W.BOOL
K.WaitForSingleObject.argtypes=[W.HANDLE,W.DWORD];K.WaitForSingleObject.restype=W.DWORD
K.QueryFullProcessImageNameW.argtypes=[W.HANDLE,W.DWORD,W.LPWSTR,ctypes.POINTER(W.DWORD)];K.QueryFullProcessImageNameW.restype=W.BOOL
def times(h):
 a,b,c,d=[W.FILETIME() for _ in range(4)];assert K.GetProcessTimes(h,*[ctypes.byref(x) for x in (a,b,c,d)])
 return dict(created=(a.dwHighDateTime<<32)|a.dwLowDateTime,exited=(b.dwHighDateTime<<32)|b.dwLowDateTime)
def save(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2)
campaign=C/('telemetry-tests-'+uuid.uuid4().hex);campaign.mkdir();results=[]
cases=[(0,1),(0,3000),(0,12000)]+[(i,12000) for i in range(1,15)]+[(i,12000) for i in (16,17,18,19)]
for n,(fault,count) in enumerate(cases):
 root=campaign/f'case-{n}-{fault}';root.mkdir();start=time.monotonic();args=[str(C/'J6DurableTest.exe'),str(root),str(fault),str(count)]
 p=subprocess.Popen(args,cwd=C,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 h=W.HANDLE(int(p._handle));initial=times(h);buf=ctypes.create_unicode_buffer(32768);size=W.DWORD(len(buf));assert K.QueryFullProcessImageNameW(h,0,buf,ctypes.byref(size));assert Path(buf.value).resolve()==(C/'J6DurableTest.exe').resolve()
 record=dict(command=args,pid=p.pid,image=buf.value,initial=initial)
 try:
  out,err=p.communicate(timeout=15);record.update(exit=p.returncode,elapsed=time.monotonic()-start,stdout=out,stderr=err,final=times(h),kernelSignaled=K.WaitForSingleObject(h,0)==0)
  assert record['kernelSignaled'] and record['final']['created']==initial['created'] and record['final']['exited']>=initial['created']
  v=json.loads(out)['result'];assert v['threadsExited'] and v['remaining']==0
  if fault:
   assert p.returncode!=0 and v['fault']!=0 and not (root/'durable-seal.json').exists()
  else:
   assert p.returncode==0 and v['fault']==0
   rows,m,w=q.stream(root,'durable');assert len(rows)==count and [x['value'] for x in rows]==list(range(count))
   record['telemetry']=tv.verify(root,'durable')
   if count==1:assert record['telemetry']['backpressure']['started']==0
  record['status']='PASS'
 except BaseException as e:
  record.update(status='FAIL',error=repr(e));save(root/'process.json',record);results.append(record);save(campaign/'results.json',results);raise
 finally:
  if p.poll() is not None:p._handle.Close()
 save(root/'process.json',record);results.append(record)
save(campaign/'results.json',results);save(R/('native-results-'+uuid.uuid4().hex+'.json'),dict(campaign=str(campaign),passed=len(results),results=results))
print(json.dumps(dict(status='PASS',cases=len(results),campaign=str(campaign))))
