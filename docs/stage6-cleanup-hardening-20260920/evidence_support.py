"""Sacrificial evidence infrastructure only; never grants process termination authority."""
import ctypes as c,ctypes.wintypes as w,os,json,pathlib,threading,time,subprocess,traceback,hashlib
from journal import ticks,frequency
from probe_timing import K,process_times
K.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];K.OpenProcess.restype=w.HANDLE
K.CloseHandle.argtypes=[w.HANDLE];K.CloseHandle.restype=w.BOOL
K.GetCurrentProcess.restype=w.HANDLE
K.DuplicateHandle.argtypes=[w.HANDLE,w.HANDLE,w.HANDLE,c.POINTER(w.HANDLE),w.DWORD,w.BOOL,w.DWORD];K.DuplicateHandle.restype=w.BOOL
K.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,c.POINTER(w.DWORD)];K.QueryFullProcessImageNameW.restype=w.BOOL
class PE(c.Structure):
 _fields_=[('dwSize',w.DWORD),('cntUsage',w.DWORD),('th32ProcessID',w.DWORD),('th32DefaultHeapID',c.c_size_t),('th32ModuleID',w.DWORD),('cntThreads',w.DWORD),('th32ParentProcessID',w.DWORD),('pcPriClassBase',w.LONG),('dwFlags',w.DWORD),('szExeFile',w.WCHAR*260)]
K.CreateToolhelp32Snapshot.argtypes=[w.DWORD,w.DWORD];K.CreateToolhelp32Snapshot.restype=w.HANDLE
K.Process32FirstW.argtypes=[w.HANDLE,c.POINTER(PE)];K.Process32NextW.argtypes=[w.HANDLE,c.POINTER(PE)]
def times(h):
 v=[w.FILETIME() for _ in range(4)]
 if not K.GetProcessTimes(h,*[c.byref(x) for x in v]):raise c.WinError(c.get_last_error())
 return [str((x.dwHighDateTime<<32)|x.dwLowDateTime) for x in v]
def image(h):
 b=c.create_unicode_buffer(32768);n=w.DWORD(len(b))
 if not K.QueryFullProcessImageNameW(h,0,b,c.byref(n)):raise c.WinError(c.get_last_error())
 return b.value
def put(p,v):
 with pathlib.Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2);f.flush()
class Ledger:
 def __init__(self,root):
  self.root=pathlib.Path(root);p=self.root/'primary-failure.json';self.primary=json.loads(p.read_text()) if p.exists() else None;self.secondary=[];self.cleanup=[]
 def fail(self,stage,error=None):
  r=dict(stage=stage,qpc=ticks(),error=traceback.format_exc() if error is None else str(error))
  if self.primary is None:
   self.primary=r;put(self.root/'primary-failure.json',r)
  else:
   self.secondary.append(r)
   with (self.root/'secondary-failures.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(r)+'\n');f.flush()
  return r
 def result(self):return dict(status='FAILED' if self.primary else 'DIAGNOSTIC_COMPLETE',primary_failure=self.primary,secondary_failures=self.secondary,cleanup_results=self.cleanup,acceptance=False)
class OutputCapture:
 """Drain both streams concurrently; retain bounded prefix, hash/count discarded tail.
 Prefix flushed as received, so a parent exception/death cannot erase prior bytes.
 A missing EOF/receipt is incomplete evidence, never successful capture.
 """
 def __init__(self,stream,path,limit=65536):
  self.stream=stream;self.path=pathlib.Path(path);self.limit=limit;self.total=0;self.kept=0;self.eof=False;self.error=None;self.sha=hashlib.sha256();self.t=threading.Thread(target=self.drain,daemon=True);self.t.start()
 def drain(self):
  try:
   with self.path.open('xb',buffering=0) as f:
    while True:
     b=os.read(self.stream.fileno(),8192)
     if not b:break
     self.total+=len(b);self.sha.update(b);n=min(len(b),self.limit-self.kept)
     if n:f.write(b[:n]);self.kept+=n
    self.eof=True
  except BaseException:self.error=traceback.format_exc()
  finally:self.stream.close()
 def finish(self):
  self.t.join(2)
  r=dict(totalBytes=self.total,storedBytes=self.kept,truncated=self.total>self.limit,limit=self.limit,eof=self.eof,threadAlive=self.t.is_alive(),error=self.error,streamSHA256=self.sha.hexdigest(),qpc=ticks())
  put(self.path.with_suffix(self.path.suffix+'.json'),r);return r
class Managed:
 def __init__(self,args,root,role,tracker=None):
  self.role=role;self.root=pathlib.Path(root);self.launch=ticks()
  self.p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=0x08000000,close_fds=True)
  self.returned=ticks();self.identity=dict(pid=self.p.pid,created=process_times(self.p)[0],role=role,parentPid=os.getpid(),image=image(int(self.p._handle)),launchQpc=self.launch,createReturnedQpc=self.returned,handleRetainedQpc=ticks(),command=args)
  # Arguments are fixed sacrificial paths/integers only. No environment dump.
  if tracker:tracker.register(self.p,role,args)
  self.stdout=OutputCapture(self.p.stdout,self.root/(role+'-stdout.bin'));self.stderr=OutputCapture(self.p.stderr,self.root/(role+'-stderr.bin'));self.finished=None
 def finish(self,seconds=15):
  if self.finished:return self.finished
  start=ticks();state=int(K.WaitForSingleObject(int(self.p._handle),int(seconds*1000)))
  r=dict(self.identity,cleanupBeginQpc=start,observedQpc=ticks(),handleState=state,times=process_times(self.p),exit=self.p.poll())
  if state==0:
   r.update(stdout=self.stdout.finish(),stderr=self.stderr.finish());self.p._handle.Close();r['parentHandleClosed']=True
  else:r.update(parentHandleClosed=False,outputIncomplete=True)
  self.finished=r;put(self.root/(self.role+'-cleanup.json'),r);return r
class TreeTracker:
 """Read-only Toolhelp enumeration; retain query/synchronize handles for descendants.
 Root handles duplicated immediately. Identity includes kernel creation time;
 child creation must lie in its recorded parent's lifetime. No kill rights.
 Event reconciliation later exposes missed short-lived children.
 """
 def __init__(self):
  self.rows={};self.handles={};self.lock=threading.RLock();self.errors=[];self.stop=threading.Event();self.scans=0;self.maxScan=0;self.thread=threading.Thread(target=self.loop,daemon=True);self.thread.start()
 def add(self,h,pid,parent,role,args=None):
  ts=times(h);key=(pid,ts[0])
  if key in self.rows:K.CloseHandle(h);return
  # Metadata failure must not discard a kernel handle that was already acquired.
  self.rows[key]=dict(pid=pid,created=ts[0],parentPid=parent,role=role,image='UNKNOWN',command=args if args else 'UNKNOWN',handleIdentity=str(h),handleRetainedQpc=ticks(),startFiletime=ts[0],signalObservedQpc=None,exitFiletime=None,exitCode=None,closed=False)
  self.handles[key]=h
  try:self.rows[key]['image']=image(h)
  except BaseException:
   error=dict(qpc=ticks(),pid=pid,created=ts[0],stage='image-query',error=traceback.format_exc());self.rows[key]['imageError']=error;self.errors.append(error)
 def register(self,p,role,args=None):
  h=w.HANDLE();selfhandle=K.GetCurrentProcess()
  if not K.DuplicateHandle(selfhandle,int(p._handle),selfhandle,c.byref(h),0x100000|0x1000,False,0):raise c.WinError(c.get_last_error())
  with self.lock:self.add(h.value,p.pid,os.getpid(),role,args)
 def scan(self):
  start=ticks();snap=K.CreateToolhelp32Snapshot(2,0)
  if snap==c.c_void_p(-1).value:raise c.WinError(c.get_last_error())
  entries=[]
  try:
   e=PE();e.dwSize=c.sizeof(e);ok=K.Process32FirstW(snap,c.byref(e))
   while ok:entries.append((e.th32ProcessID,e.th32ParentProcessID,e.szExeFile));ok=K.Process32NextW(snap,c.byref(e))
  finally:K.CloseHandle(snap)
  with self.lock:
   # Iterate to cover descendants when child appears before parent in snapshot.
   for _ in range(4):
    added=False
    for pid,parent,name in entries:
     parents=[r for r in self.rows.values() if r['pid']==parent]
     if not parents or any(k[0]==pid for k in self.rows):continue
     h=K.OpenProcess(0x100000|0x1000,False,pid)
     if not h:continue # Late-event reconciliation will mark missing handles.
     try:
      ts=times(h);matches=[r for r in parents if int(r['created'])<=int(ts[0]) and (r['exitFiletime'] is None or int(ts[0])<=int(r['exitFiletime']))]
      if len(matches)!=1:K.CloseHandle(h);continue
      self.add(h,pid,parent,'descendant:'+name);added=True
     except BaseException:K.CloseHandle(h);raise
    if not added:break
   for key,h in self.handles.items():
    r=self.rows[key]
    if r['signalObservedQpc'] is not None:continue
    state=int(K.WaitForSingleObject(h,0));r['lastHandleState']=state
    if state==0:
     ts=times(h);code=w.DWORD()
     if not K.GetExitCodeProcess(h,c.byref(code)):raise c.WinError(c.get_last_error())
     if ts[0]!=r['created']:raise RuntimeError('Retained tree identity changed')
     r.update(signalObservedQpc=ticks(),exitFiletime=ts[1],exitCode=code.value)
    elif state!=258:raise RuntimeError('Invalid retained tree handle')
  self.scans+=1;self.maxScan=max(self.maxScan,(ticks()-start)/frequency())
 def loop(self):
  while not self.stop.is_set():
   try:self.scan()
   except BaseException:self.errors.append(dict(qpc=ticks(),error=traceback.format_exc()))
   self.stop.wait(.01)
 def snapshot(self):
  with self.lock:return [dict(r) for r in self.rows.values()]
 def finish(self,root,seconds=20):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   self.scan()
   if all(r['signalObservedQpc'] is not None for r in self.snapshot()):break
   time.sleep(.02)
  self.stop.set();self.thread.join(2)
  with self.lock:
   for key,h in self.handles.items():
    if self.rows[key]['signalObservedQpc'] is not None:self.rows[key]['closed']=bool(K.CloseHandle(h))
   rows=self.snapshot()
  result=dict(rows=rows,errors=self.errors,threadStopped=not self.thread.is_alive(),allExited=bool(rows) and all(r['signalObservedQpc'] is not None for r in rows),allHandlesClosed=all(r['closed'] for r in rows),scanCount=self.scans,maxScanSeconds=self.maxScan,qpc=ticks())
  put(pathlib.Path(root)/'tree-handles.json',result);return result
