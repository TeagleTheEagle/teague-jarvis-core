"""Bounded offline process runner. No ETW or elevated processes."""
import pathlib,sys,runpy,ctypes as ct,ctypes.wintypes as w,subprocess,time,datetime,json,math,statistics
from prepare import R,W,C,load,sha,put
OLD=R.parent/'stage6-precise-overhead-20260924'
sys.path.insert(0,str(OLD))
native=runpy.run_path(str(OLD/'benchmark.py'),run_name='read_only_winapi_definitions')
sys.path.pop(0)
k=native['k'];SA=native['SA'];SI=native['SI'];PI=native['PI'];times=native['times'];checked=native['checked']
def launch(mode):
 exe=W/'J6AttributionFixture.exe';out=W/'raw'/(mode+'.jsonl');err=W/'raw'/(mode+'-stderr.txt');security=SA(ct.sizeof(SA),None,True);handles=[];pi=PI()
 rec=dict(mode=mode,executable=str(exe),sha256=sha(exe),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),cwd=str(W),flags=0,UAC=False)
 try:
  for p,access,creation in [(str(out),0x40000000,1),(str(err),0x40000000,1),('NUL',0x80000000,3)]:handles.append(checked(k.CreateFileW(p,access,3,ct.byref(security),creation,0x80,None)))
  si=SI();si.cb=ct.sizeof(si);si.flags=0x100;si.stdout,si.stderr,si.stdin=handles
  command=ct.create_unicode_buffer(subprocess.list2cmdline([str(exe),mode]));begin=time.monotonic()
  if not k.CreateProcessW(str(exe),command,None,None,True,0,None,str(W),ct.byref(si),ct.byref(pi)):raise ct.WinError(ct.get_last_error())
  rec.update(pid=pi.pid,tid=pi.tid,initialProcess=times(pi.process),initialThread=times(pi.thread,True));put(W/'raw'/(mode+'-started.json'),rec)
  last=0
  while True:
   wait=k.WaitForSingleObject(pi.process,1000)
   if wait==0:break
   if wait!=258:raise RuntimeError('Process wait API failed')
   if time.monotonic()-begin>1200:raise RuntimeError('Offline phase bound exceeded; no replacement')
   if time.monotonic()-last>=30:
    count=len(out.read_text().splitlines());print(json.dumps(dict(mode=mode,completedTrials=count,elapsedSeconds=round(time.monotonic()-begin,1))),flush=True);last=time.monotonic()
  code=w.DWORD()
  if not k.GetExitCodeProcess(pi.process,ct.byref(code)):raise ct.WinError(ct.get_last_error())
  rec.update(exitCode=code.value,waitResult=wait,finalProcess=times(pi.process),finalThread=times(pi.thread,True),elapsedSeconds=time.monotonic()-begin)
  if code.value:raise RuntimeError('Fixture nonzero exit')
 finally:
  errors=[]
  for h in [pi.thread,pi.process]+handles:
   if h and not k.CloseHandle(h):errors.append(ct.get_last_error())
  rec['closeErrors']=errors;put(W/'raw'/(mode+'-exit.json'),rec)
 return [json.loads(s) for s in out.read_text().splitlines()]
def ci(values,critical):
 m=statistics.mean(values);half=critical*statistics.stdev(values)/math.sqrt(len(values));return dict(mean=m,halfwidth=half,lower=m-half,upper=m+half,n=len(values))
def reference(rows):
 assert len(rows)==80;values=[]
 for b in range(40):
  two=rows[b*2:b*2+2];assert [t['variant'] for t in two]==([0,1] if b%2==0 else [1,0])
  assert all(t['callbacks']==1000000 and t['dispatcherCpu100ns']>0 and t['block']==b for t in two)
  a=next(t for t in two if t['variant']==0);z=next(t for t in two if t['variant']==1)
  values.append(100*(z['dispatcherCpu100ns']/a['dispatcherCpu100ns']-1))
 grouped=[statistics.mean(values[i:i+5]) for i in range(0,40,5)];result=ci(grouped,2.364624251)
 low,high=1.191266939782601,1.6088796722099354
 status='BENCHMARK_REPRODUCIBILITY_DEFECT' if result['upper']<low or result['lower']>high else ('MORE_PROFILING_REQUIRED' if result['halfwidth']>.75 else 'REFERENCE_COMPATIBLE')
 put(R/'reference-result.json',dict(status=status,interval=result,pairs=40,pairedPercentValues=values,oldInterval=[low,high],note='Compatibility, not proof of equivalence; no noise exclusions'))
 print(json.dumps(dict(status=status,interval=result)),flush=True);return status
if __name__=='__main__':
 mode=sys.argv[1];assert mode in ['selftest','reference','attribution']
 assert load(R/'generated-code-audit.json')['referenceDispatchObjectInstructionsIdentical']
 if mode=='reference':
  assert load(R/'selftest-result.json')[0]['selftest']=='PASS'
  frozen=[]
  for root in [R,W]:
   for p in sorted(root.iterdir()):
    if p.is_file():frozen.append(dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size))
  put(R/'experiment-source-freeze.json',frozen)
 elif mode=='attribution':
  assert load(R/'reference-result.json')['status']=='REFERENCE_COMPATIBLE'
  for row in load(R/'experiment-source-freeze.json'):assert sha(row['path'])==row['sha256']
 try:
  rows=launch(mode)
  if mode=='selftest':put(R/'selftest-result.json',rows);print(json.dumps(rows))
  elif mode=='reference':reference(rows)
  else:
   assert len(rows)==200
   for b in range(40):
    five=rows[b*5:b*5+5];assert len({t['variant'] for t in five})==5
    assert all(t['block']==b and t['callbacks']==1000000 and t['dispatcherCpu100ns']>0 for t in five)
   put(R/'attribution-execution.json',dict(status='COMPLETE',blocks=40,trials=200,exclusions=[],retries=0));print('Attribution execution complete',flush=True)
 except BaseException as e:
  put(R/(mode+'-failure.json'),dict(error=repr(e),retry=False));raise
