"""One fixed telemetry worker per unnamed kill-on-close Job; no generic command API."""
import ctypes as c,ctypes.wintypes as w,subprocess,sys,time,threading,json,mmap,struct,uuid
from workspace import CODE
from journal import ticks,frequency
from evidence_support import times,image
K=c.WinDLL('kernel32',use_last_error=True)
class STARTUP(c.Structure):
 _fields_=[('cb',w.DWORD),('reserved',w.LPWSTR),('desktop',w.LPWSTR),('title',w.LPWSTR)]+[(n,w.DWORD) for n in ('x','y','xs','ys','xc','yc','fill','flags')]+[('show',w.WORD),('reserved2',w.WORD),('reservedPtr',c.c_void_p),('stdin',w.HANDLE),('stdout',w.HANDLE),('stderr',w.HANDLE)]
class INFO(c.Structure):_fields_=[('process',w.HANDLE),('thread',w.HANDLE),('pid',w.DWORD),('tid',w.DWORD)]
class BASIC(c.Structure):_fields_=[('perProcess',c.c_longlong),('perJob',c.c_longlong),('flags',w.DWORD),('minWorking',c.c_size_t),('maxWorking',c.c_size_t),('activeLimit',w.DWORD),('affinity',c.c_size_t),('priority',w.DWORD),('scheduling',w.DWORD)]
class IO(c.Structure):_fields_=[(n,c.c_ulonglong) for n in ('readOps','writeOps','otherOps','readBytes','writeBytes','otherBytes')]
class EXT(c.Structure):_fields_=[('basic',BASIC),('io',IO)]+[(n,c.c_size_t) for n in ('processMemory','jobMemory','peakProcess','peakJob')]
class ACCOUNT(c.Structure):_fields_=[(n,c.c_longlong) for n in ('user','kernel','periodUser','periodKernel')]+[(n,w.DWORD) for n in ('faults','total','active','terminated')]
K.CreateJobObjectW.argtypes=[c.c_void_p,w.LPCWSTR];K.CreateJobObjectW.restype=w.HANDLE
K.SetInformationJobObject.argtypes=[w.HANDLE,c.c_int,c.c_void_p,w.DWORD];K.SetInformationJobObject.restype=w.BOOL
K.QueryInformationJobObject.argtypes=[w.HANDLE,c.c_int,c.c_void_p,w.DWORD,c.c_void_p];K.QueryInformationJobObject.restype=w.BOOL
K.CreateProcessW.argtypes=[w.LPCWSTR,w.LPWSTR,c.c_void_p,c.c_void_p,w.BOOL,w.DWORD,c.c_void_p,w.LPCWSTR,c.POINTER(STARTUP),c.POINTER(INFO)];K.CreateProcessW.restype=w.BOOL
K.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE];K.AssignProcessToJobObject.restype=w.BOOL
K.ResumeThread.argtypes=[w.HANDLE];K.ResumeThread.restype=w.DWORD
K.TerminateJobObject.argtypes=[w.HANDLE,w.UINT];K.TerminateJobObject.restype=w.BOOL
K.TerminateProcess.argtypes=[w.HANDLE,w.UINT];K.TerminateProcess.restype=w.BOOL
K.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];K.WaitForSingleObject.restype=w.DWORD
K.CloseHandle.argtypes=[w.HANDLE];K.GetExitCodeProcess.argtypes=[w.HANDLE,c.POINTER(w.DWORD)]
QUERY_SECONDS=2.0;CLEANUP_MS=2000
def query(root,mode,ordinal,cancel,tracker=None,cleanup_injection=False):
 if mode not in ('normal','slow','hung','exception','crash'):raise ValueError('Fixed sampler mode required')
 name='Local\\J6Secondary-'+root.name+'-'+uuid.uuid4().hex;r=dict(mode=mode,ordinal=ordinal,launchQpc=ticks(),status='MISSING',secondary=True,cleanupInjection=cleanup_injection)
 view=mmap.mmap(-1,4096,tagname=name);view[:]=bytes(4096)
 job=K.CreateJobObjectW(None,None);pi=INFO();si=STARTUP();si.cb=c.sizeof(si);assigned=False;resumed=False
 if not job:raise c.WinError(c.get_last_error())
 try:
  lim=EXT();lim.basic.flags=0x2000 # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
  if not K.SetInformationJobObject(job,9,c.byref(lim),c.sizeof(lim)):raise c.WinError(c.get_last_error())
  command=c.create_unicode_buffer(subprocess.list2cmdline([sys._base_executable,'-B',str(CODE/'sampler_worker.py'),root.name,mode,name]))
  r['createBeginQpc']=ticks()
  if not K.CreateProcessW(sys._base_executable,command,None,None,False,0x08000004,None,str(CODE),c.byref(si),c.byref(pi)):raise c.WinError(c.get_last_error())
  r.update(createReturnedQpc=ticks(),pid=pi.pid,created=times(pi.process)[0],image=image(pi.process),handleRetainedQpc=ticks())
  if not K.AssignProcessToJobObject(job,pi.process):raise c.WinError(c.get_last_error())
  assigned=True;r['jobAssignedQpc']=ticks()
  if tracker:tracker.register(type('RetainedSampler',(),dict(pid=pi.pid,_handle=pi.process))(),'sampler:'+mode)
  if K.ResumeThread(pi.thread)==0xffffffff:raise c.WinError(c.get_last_error())
  resumed=True;r['resumeQpc']=ticks();K.CloseHandle(pi.thread);pi.thread=None
  deadline=r['launchQpc']/frequency()+QUERY_SECONDS
  while K.WaitForSingleObject(pi.process,25)==258:
   if cancel.is_set():r['reason']='CANCELED';break
   if ticks()/frequency()>=deadline:r['reason']='QUERY_TIMEOUT';break
  else:
   code=w.DWORD();K.GetExitCodeProcess(pi.process,c.byref(code));r['exitCode']=code.value
   if code.value==0:
    size=struct.unpack('<I',view[:4])[0];assert 0<size<4000
    value=json.loads(view[4:4+size]);assert value['pid']==pi.pid;r.update(status='AVAILABLE',value=value)
   else:r['reason']='QUERY_EXIT_'+str(code.value)
 except BaseException as ex:r['reason']='QUERY_ERROR: '+repr(ex)
 finally:
  if pi.thread:K.CloseHandle(pi.thread)
  if pi.process:
   r['cleanupBeginQpc']=ticks()
   if cleanup_injection:r.update(status='MISSING',reason='INJECTED_CLEANUP_OBSERVATION_TIMEOUT')
   if K.WaitForSingleObject(pi.process,0)==258 or cleanup_injection:
    # Only our handle-bound, suspended-before-assignment worker/job is affected.
    ok=K.TerminateJobObject(job,0xE6) if assigned else K.TerminateProcess(pi.process,0xE6)
    r['terminationRequested']=bool(ok)
   state=K.WaitForSingleObject(pi.process,CLEANUP_MS)
   acc=ACCOUNT();q=K.QueryInformationJobObject(job,1,c.byref(acc),c.sizeof(acc),None)
   r['jobActiveBeforeClose']=acc.active if q else None
   K.CloseHandle(job);job=None # Fail-safe terminates remaining job members.
   if state==258:state=K.WaitForSingleObject(pi.process,CLEANUP_MS)
   r.update(handleState=state,finalTimes=times(pi.process),cleanupEndQpc=ticks(),allExited=state==0 and bool(q) and acc.active==0)
   code=w.DWORD();K.GetExitCodeProcess(pi.process,c.byref(code));r['finalExitCode']=code.value
   K.CloseHandle(pi.process);r['handleClosed']=True
   if not r['allExited']:r.update(status='CLEANUP_FAILED',reason='REQUIRED_CLEANUP_UNPROVEN')
  if job:K.CloseHandle(job)
  view.close()
 return r
