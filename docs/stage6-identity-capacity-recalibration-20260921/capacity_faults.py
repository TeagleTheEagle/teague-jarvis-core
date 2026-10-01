"""Small sacrificial sink runs and evidence mutations. No tracing or VM access."""
import pathlib,json,hashlib,subprocess,uuid,shutil,sys,copy,time
R=pathlib.Path(__file__).parent
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\f469b94b665e4808af1c5bb6aa46b207\code')
sys.path.insert(0,str(C))
from trace_segments import verify
import cleanup_checker
T=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE')/('capacity-forensics-'+uuid.uuid4().hex)
T.mkdir(exist_ok=False);out=[]
def save():
 (R/'capacity-faults.json').write_text(json.dumps(dict(root=str(T),checks=out,scope='Small real sink writes; reduced finite budgets. Not peak throughput or full conservative-capacity qualification.'),indent=2))
def check(n,v):
 out.append(dict(name=n,pass_=bool(v)));save();assert v,n
def reject(root):
 try:verify(root)
 except (AssertionError,OSError,ValueError):return True
 return False
exe=C/'J6SinkTest.exe';expected=next(x['sha256'] for x in json.loads((R.parent/'stage6-trace-capacity-native-entry-20260921/medium-candidate/candidate-hashes.json').read_text()) if x['name']=='J6SinkTest.exe')
check('frozen executable SHA256',hashlib.sha256(exe.read_bytes()).hexdigest()==expected)
for name,count,limit,inject,bytes_,good in [('near',19,20,0,4096,True),('exact',20,20,0,4096,True),('overflow',21,20,0,4096,False),('writer',20,20,1,4096,False),('disk-full-simulation',20,20,2,4096,False),('segment-create',20,20,3,4096,False),('storage-bound',20,20,0,64,False)]:
 root=T/name;root.mkdir();begin=time.perf_counter_ns()
 p=subprocess.Popen([str(exe),str(root),str(count),str(limit),str(inject),str(bytes_)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 import ctypes,ctypes.wintypes as w
 K=ctypes.WinDLL('kernel32',use_last_error=True);K.GetProcessTimes.argtypes=[w.HANDLE]+[ctypes.POINTER(w.FILETIME)]*4
 ts=[w.FILETIME() for _ in range(4)];assert K.GetProcessTimes(int(p._handle),*(ctypes.byref(x) for x in ts))
 created=(ts[0].dwHighDateTime<<32)|ts[0].dwLowDateTime
 code=p.wait(timeout=10);K.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];signal=K.WaitForSingleObject(int(p._handle),0)
 check(name+' retained process exit',signal==0);p._handle.Close()
 m=json.loads((root/'sink-result.json').read_text());(root/'startup-events.json').write_text(json.dumps(m))
 (root/'process-identity.json').write_text(json.dumps(dict(pid=p.pid,created=str(created),image=str(exe),sha256=expected,exit=code,handleSignaled=signal==0,handleClosed=True,durationNs=time.perf_counter_ns()-begin)))
 check(name+' process/fault disposition',(code==0)==good and (m['fault']==0)==good)
 if good:
  v=verify(root);check(name+' complete segments',v['records']==count and v['segments']>1)
 else:check(name+' rejects incomplete evidence',reject(root))
base=T/'exact'
for name in ('missing-segment','corrupt-segment','wrong-hash','manifest-omits-segment','duplicate-segment-name','nonzero-loss-fault'):
 root=T/name;shutil.copytree(base,root);m=json.loads((root/'startup-events.json').read_text());seg=root/m['segments'][0]['name']
 if name=='missing-segment':seg.rename(root/'removed-segment.evidence')
 elif name=='corrupt-segment':seg.write_bytes(seg.read_bytes()+b'bad')
 elif name=='wrong-hash':m['segments'][0]['sha256']='0'*64
 elif name=='manifest-omits-segment':m['segments'].pop()
 elif name=='duplicate-segment-name':m['segments'][1]['name']=m['segments'][0]['name']
 else:m['fault']=1
 (root/'startup-events.json').write_text(json.dumps(m));check(name,reject(root))
B=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\3316657ba1864413a0c95ea1dc7bf6ff\code\protected-5d26ae153ea2490da7ca1ec16d97c124')
d=cleanup_checker.load(B);d['kernel']['eventsLost']=1
check('nonzero actual ETW loss field rejects full cleanup',cleanup_checker.check(d)['status']=='FAIL')
# Existing file must not be overwritten by CREATE_NEW. Preserve its hash.
root=T/'no-overwrite';root.mkdir();old=root/'trace-00000.jsonl';old.write_bytes(b'preserved sacrificial sentinel\n');before=old.read_bytes()
p=subprocess.run([str(exe),str(root),'20','20','0','4096'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10)
check('CREATE_NEW leaves old segment unchanged',p.returncode!=0 and old.read_bytes()==before)
print(json.dumps(dict(checks=len(out),passed=sum(x['pass_'] for x in out),root=str(T))))
