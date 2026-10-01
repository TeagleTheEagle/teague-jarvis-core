"""Bounded in-memory diagnostic call timing. No argument/environment contents recorded."""
import ctypes as c,ctypes.wintypes as w,threading,time,subprocess,types,mmap,struct,json
from journal import ticks,frequency
ROWS=[];LIMIT=200000;OVERFLOW=0;LOCAL=threading.local();MAPS=[];RESTORE=[]
def label(value):LOCAL.value=value
def wrap(name,fn):
 def measured(*args,**kwargs):
  global OVERFLOW
  # Enumerated-process API repetition is covered by whole-scan/discovery spans.
  # Keep exact launch, sampler and independent observer calls; never enlarge cap.
  if getattr(LOCAL,'value','background')=='background' and name.startswith(('probe_timing.','evidence_support.')):return fn(*args,**kwargs)
  last=c.get_last_error();begin=ticks();tid=threading.get_native_id();error=None;result=None
  c.set_last_error(last)
  try:result=fn(*args,**kwargs);return result
  except BaseException as ex:error=type(ex).__name__;raise
  finally:
   saved=c.get_last_error();end=ticks()
   if len(ROWS)<LIMIT:
    row=dict(call=name,beginQpc=begin,endQpc=end,seconds=(end-begin)/frequency(),thread=tid,scope=getattr(LOCAL,'value','background'),error=error)
    if name=='winapi.CreateProcess' and isinstance(result,tuple):row['createdHandlesPidTid']=list(result)
    if name.endswith(('WaitForSingleObject','ResumeThread','TerminateJobObject','TerminateProcess','QueryInformationJobObject','CloseHandle')) and isinstance(result,int):row['returnValue']=result
    if name.endswith('WaitForSingleObject') and len(args)>1:row['requestedMilliseconds']=args[1]
    if name.endswith(('WaitForSingleObject','CloseHandle','GetProcessTimes','GetExitCodeProcess','ResumeThread')) and args:
     h=getattr(args[0],'value',args[0])
     if isinstance(h,int):row['handleValue']=h
    ROWS.append(row)
   else:OVERFLOW+=1
   c.set_last_error(saved)
 return measured
def patch(obj,name,prefix):
 if not hasattr(obj,name):return
 old=getattr(obj,name);RESTORE.append((obj,name,old));setattr(obj,name,wrap(prefix+'.'+name,old))
def install():
 import probe_timing as p,bounded_sampler as b,evidence_support as e
 original_observe=p.Probe.observe
 def observed(self):
  label('probe-independent-observer:'+str(self.process.pid))
  return wrap('probe.independent_observer_total',original_observe)(self)
 p.Probe.observe=observed
 patch(e.TreeTracker,'scan','tree');patch(e.TreeTracker,'add','tree')
 for name in ('CreateProcess','CreatePipe','DuplicateHandle','GetStdHandle','CloseHandle','GetFileType'):patch(subprocess._winapi,name,'winapi')
 for name in ('_get_handles','_get_devnull','_make_inheritable','_execute_child'):patch(subprocess.Popen,name,'Popen')
 patch(subprocess,'list2cmdline','subprocess')
 seen=set()
 for mod in (p,b,e):
  if id(mod.K) in seen:continue
  seen.add(id(mod.K))
  for name in ('CreateProcessW','CreateJobObjectW','SetInformationJobObject','AssignProcessToJobObject','ResumeThread','TerminateJobObject','TerminateProcess','QueryInformationJobObject','WaitForSingleObject','CloseHandle','OpenProcess','DuplicateHandle','GetProcessTimes','GetExitCodeProcess','QueryFullProcessImageNameW','CreateToolhelp32Snapshot','Process32FirstW','Process32NextW'):patch(mod.K,name,mod.__name__)
 # Module-local proxies avoid global changes to sleep or mapping semantics.
 b.time=types.SimpleNamespace(monotonic=time.monotonic,sleep=wrap('sampler.poll_sleep',time.sleep))
 def mapping(*args,**kwargs):
  name=kwargs.get('tagname','')
  if name.startswith('Local\\J6Secondary-'):
   diag=mmap.mmap(-1,65536,tagname=name+'-calls');diag[:]=bytes(65536);MAPS.append((name,diag))
  return mmap.mmap(*args,**kwargs)
 b.mmap=types.SimpleNamespace(mmap=wrap('sampler.mapping_setup',mapping))
def internal():
 rows=[]
 for name,view in MAPS:
  count=struct.unpack('<I',view[:4])[0];assert count<=1000
  for i in range(count):
   ns,pid,stage=struct.unpack('<QI48s',view[8+i*60:8+(i+1)*60]);rows.append(dict(pid=pid,perfCounterNs=ns,stage=stage.split(b'\0')[0].decode()))
  view.close()
 return rows
class Pressure:
 """Optional read-only PDH counters, sampled off the launcher thread."""
 def __init__(self):
  self.rows=[];self.errors=[];self.stop=threading.Event();self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()
 def run(self):
  class Value(c.Structure):_fields_=[('status',w.DWORD),('value',c.c_double)]
  pdh=c.WinDLL('pdh');pdh.PdhOpenQueryW.argtypes=[w.LPCWSTR,c.c_size_t,c.POINTER(w.HANDLE)];pdh.PdhAddEnglishCounterW.argtypes=[w.HANDLE,w.LPCWSTR,c.c_size_t,c.POINTER(w.HANDLE)];pdh.PdhCollectQueryData.argtypes=[w.HANDLE];pdh.PdhGetFormattedCounterValue.argtypes=[w.HANDLE,w.DWORD,c.c_void_p,c.POINTER(Value)];pdh.PdhCloseQuery.argtypes=[w.HANDLE]
  q=w.HANDLE();handles=[]
  try:
   rc=pdh.PdhOpenQueryW(None,0,c.byref(q))
   if rc:raise RuntimeError('PdhOpenQuery '+str(rc))
   paths=[r'\Processor(_Total)\% Processor Time',r'\Memory\Available MBytes']
   for drive in ('C:','D:'):
    paths.extend('\\LogicalDisk('+drive+')\\'+metric for metric in ('Disk Reads/sec','Disk Writes/sec','Avg. Disk sec/Read','Avg. Disk sec/Write','Current Disk Queue Length'))
   for path in paths:
    h=w.HANDLE();rc=pdh.PdhAddEnglishCounterW(q,path,0,c.byref(h))
    if rc:self.errors.append(dict(counter=path,error=rc))
    else:handles.append((path,h))
   while not self.stop.is_set() and len(self.rows)<1000:
    begin=ticks();rc=pdh.PdhCollectQueryData(q);values={}
    for path,h in handles:
     v=Value();err=pdh.PdhGetFormattedCounterValue(h,0x200,None,c.byref(v));values[path]=dict(value=v.value if not err and v.status in (0,1) else None,error=err,status=v.status)
    self.rows.append(dict(beginQpc=begin,endQpc=ticks(),collectResult=rc,counters=values));self.stop.wait(.25)
  except BaseException as ex:self.errors.append(repr(ex))
  finally:
   if q:pdh.PdhCloseQuery(q)
 def close(self):
  self.stop.set();self.thread.join(2);return dict(rows=self.rows,errors=self.errors,threadExited=not self.thread.is_alive(),scope='Optional coarse PDH counters; no scheduling/security stack attribution')
