"""Revised sacrificial wait: 5 s warning, fixed 13.6 s launch deadline."""
import ctypes as c,ctypes.wintypes as w,subprocess,threading,os,time
from journal import ticks,frequency
from probe_policy import wait_tracked,HardDeadline
K=c.WinDLL('kernel32',use_last_error=True)
K.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];K.WaitForSingleObject.restype=w.DWORD
K.GetProcessTimes.argtypes=[w.HANDLE]+[c.POINTER(w.FILETIME)]*4;K.GetProcessTimes.restype=w.BOOL
K.GetExitCodeProcess.argtypes=[w.HANDLE,c.POINTER(w.DWORD)];K.GetExitCodeProcess.restype=w.BOOL
K.GetSystemTimePreciseAsFileTime.argtypes=[c.POINTER(w.FILETIME)]
def ft(v):return (v.dwHighDateTime<<32)|v.dwLowDateTime
def bridge():
 a=ticks();v=w.FILETIME();K.GetSystemTimePreciseAsFileTime(c.byref(v));b=ticks();return dict(qpcBefore=a,qpcAfter=b,filetime=str(ft(v)))
def process_times(p):
 ts=[w.FILETIME() for _ in range(4)]
 if not K.GetProcessTimes(int(p._handle),*[c.byref(t) for t in ts]):raise c.WinError(c.get_last_error())
 return [str(ft(t)) for t in ts]
class Probe:
 def __init__(self,executable,args=None,startupinfo=None):
  args=[] if args is None else args
  self.row=dict(parentPid=os.getpid(),executable=str(executable),arguments=args,cwd=os.getcwd(),stdout='DEVNULL',stderr='DEVNULL',creationflags='CREATE_NO_WINDOW',close_fds=True,frequency=frequency(),clockBefore=bridge(),launchRequestedQpc=ticks())
  original=subprocess._winapi.CreateProcess
  def measured(*args,**kwargs):
   self.row['createProcessCalledQpc']=ticks()
   try:return original(*args,**kwargs)
   finally:self.row['createProcessReturnedQpc']=ticks()
  try:
   subprocess._winapi.CreateProcess=measured
   self.process=subprocess.Popen([str(executable),*args],startupinfo=startupinfo,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=0x08000000)
  finally:subprocess._winapi.CreateProcess=original
  self.row['handleRetainedQpc']=ticks();self.row['popenReturnedQpc']=ticks();self.row['pid']=self.process.pid
  try:self.row['initialKernelTimes']=process_times(self.process);self.row['identityCapturedQpc']=ticks()
  except BaseException as ex:self.row['startupIdentityError']=repr(ex)
  self.observer=threading.Thread(target=self.observe,name='probe-exit-observer',daemon=True);self.observer.start()
 def observe(self):
  self.row['observerWaitEnteredQpc']=ticks()
  self.row['observerResult']=int(K.WaitForSingleObject(int(self.process._handle),15000))
  self.row['observerReturnedQpc']=ticks()
 def wait_approved(self,health,warning,campaign_deadline):
  self.row['mainWaitEnteredQpc']=ticks();self.row['slowWarnings']=[]
  origin=self.row['launchRequestedQpc']/self.row['frequency']
  def identity():
   if self.row.get('startupIdentityError'):raise RuntimeError('Initial process identity unavailable')
   if process_times(self.process)[0]!=self.row['initialKernelTimes'][0]:raise RuntimeError('Probe creation identity mismatch')
  def emit(v):
   v.update(pid=self.process.pid,created=self.row['initialKernelTimes'][0],qpc=ticks())
   self.row['slowWarnings'].append(v);warning(v)
  def exit_elapsed():
   ts=process_times(self.process);b=bridge();f=self.row['frequency']
   q=(b['qpcBefore']+b['qpcAfter'])/2+(int(ts[1])-int(b['filetime']))*f/1e7
   self.row['exitConfirmationBridge']=b
   return (q-self.row['launchRequestedQpc'])/f
  try:
   self.row['policy']=wait_tracked(clock=lambda:ticks()/self.row['frequency'],origin=origin,campaign_deadline=campaign_deadline,wait=lambda ms:int(K.WaitForSingleObject(int(self.process._handle),ms)),identity=identity,health=health,warning=emit,exit_elapsed=exit_elapsed)
   code=self.process.poll()
   if code is None:raise RuntimeError('Signaled retained handle did not provide exit code')
   self.row['mainWaitReturnedQpc']=ticks();self.row['timedOut']=False;self.row['hardDeadlineFailure']=False
   return code
  except BaseException as ex:
   self.row['failureCaughtQpc']=ticks();self.row['hardDeadlineFailure']=isinstance(ex,HardDeadline);self.row['timedOut']=isinstance(ex,HardDeadline)
   self.row['policyFailure']=repr(ex);self.row['immediateHandleState']=int(K.WaitForSingleObject(int(self.process._handle),0))
   if isinstance(ex,HardDeadline):self.row['timeoutCaughtQpc']=ticks()
   raise
 def finish_observation(self):
  self.observer.join(timeout=16)
  self.row['independentObserverFailed']=self.observer.is_alive() or self.row.get('observerResult')!=0
  self.row['finalKernelTimes']=process_times(self.process);self.row['clockAfter']=bridge()
  code=w.DWORD()
  if not K.GetExitCodeProcess(int(self.process._handle),c.byref(code)):raise c.WinError(c.get_last_error())
  self.row['actualExitCode']=code.value;self.row['finalHandleState']=int(K.WaitForSingleObject(int(self.process._handle),0));self.row['reconciledQpc']=ticks()
