"""Own-child native debugger on its creating thread; actual Popen/Job identities preserved."""
import ctypes as c,ctypes.wintypes as w,threading,time,_winapi,pathlib,sys,json
from workspace import CODE,check_path
from journal import ticks
K=c.WinDLL('kernel32',use_last_error=True)
K.GetCurrentProcess.restype=w.HANDLE
K.DuplicateHandle.argtypes=[w.HANDLE,w.HANDLE,w.HANDLE,c.POINTER(w.HANDLE),w.DWORD,w.BOOL,w.DWORD];K.DuplicateHandle.restype=w.BOOL
K.CloseHandle.argtypes=[w.HANDLE];K.DebugSetProcessKillOnExit.argtypes=[w.BOOL];K.DebugSetProcessKillOnExit.restype=w.BOOL
class NativeBridge:
 def __init__(self,root):
  self.root=check_path(root);self.threads=[];self.errors=[];self.created=[]
  self.dll=c.WinDLL(str(CODE/'J6OwnedEntry.dll'))
  self.dll.TraceOwned.argtypes=[w.HANDLE,w.HANDLE,w.DWORD,w.DWORD,w.LPCWSTR,c.c_longlong,w.BOOL];self.dll.TraceOwned.restype=c.c_int
  self.original=_winapi.CreateProcess
  import bounded_sampler
  self.sampler=bounded_sampler;self.originalSampler=bounded_sampler.K.CreateProcessW
 def duplicate(self,h):
  out=w.HANDLE();selfhandle=K.GetCurrentProcess()
  if not K.DuplicateHandle(selfhandle,h,selfhandle,c.byref(out),0,False,2):raise c.WinError(c.get_last_error())
  return out.value
 def run(self,create,is_probe):
  ready=threading.Event();box={};launch=ticks()
  def thread():
   hp=ht=None
   try:
    original,ph,th,pid,tid=create()
    if not K.DebugSetProcessKillOnExit(False):raise c.WinError(c.get_last_error())
    hp=self.duplicate(ph);ht=self.duplicate(th)
    box['result']=original;self.created.append(pid);ready.set()
    result=self.dll.TraceOwned(hp,ht,pid,tid,str(self.root),launch,is_probe)
    if result not in (0,97):self.errors.append(dict(pid=pid,nativeResult=result))
   except BaseException as exc:box['error']=exc;self.errors.append(dict(error=type(exc).__name__))
   finally:
    ready.set()
    if ht:K.CloseHandle(ht)
    if hp:K.CloseHandle(hp)
  t=threading.Thread(target=thread,name='owned-native-entry');self.threads.append(t);t.start()
  # No new launch allowance: this is the original CreateProcess call's duration.
  ready.wait()
  if 'error' in box:raise box['error']
  return box['result']
 def create(self,*args):
  a=list(args);exe=pathlib.Path(a[0] or a[1].split(' ')[0].strip('"'))
  if exe.resolve() not in ((CODE/'J6Probe.exe').resolve(),pathlib.Path(sys._base_executable).resolve()):raise ValueError('Unapproved native child image')
  a[5]|=2 # DEBUG_ONLY_THIS_PROCESS; all other handle/stdio/creation flags unchanged.
  def make():
   result=self.original(*a);return result,*result
  return self.run(make,exe.name=='J6Probe.exe')
 def create_sampler(self,*args):
  a=list(args)
  if pathlib.Path(a[0]).resolve()!=pathlib.Path(sys._base_executable).resolve():raise ValueError('Sampler image mismatch')
  command=a[1].value;expected=str(CODE/'sampler_worker.py')
  if expected not in command:raise ValueError('Sampler script mismatch')
  a[1]=c.create_unicode_buffer(command.replace(expected,str(CODE/'traced_sampler_worker.py'),1));a[5]|=2
  def make():
   ok=self.originalSampler(*a)
   if not ok:raise c.WinError(c.get_last_error())
   pi=c.cast(a[9],c.POINTER(self.sampler.INFO)).contents
   return ok,pi.process,pi.thread,pi.pid,pi.tid
  return self.run(make,False)
 def install(self):_winapi.CreateProcess=self.create;self.sampler.K.CreateProcessW=self.create_sampler
 def close(self):
  _winapi.CreateProcess=self.original;self.sampler.K.CreateProcessW=self.originalSampler
  end=time.monotonic()+2
  for t in self.threads:t.join(max(0,end-time.monotonic()))
  result=dict(threadCount=len(self.threads),allThreadsExited=all(not t.is_alive() for t in self.threads),createdPids=self.created,errors=self.errors)
  with (self.root/'native-bridge-cleanup.json').open('x') as f:json.dump(result,f,indent=2)
  if not result['allThreadsExited'] or self.errors:raise RuntimeError('Native debug bridge cleanup failed')
