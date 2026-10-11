"""Bounded additive diagnostic markers. No control commands or environment capture."""
import os,time,json,ctypes as c,ctypes.wintypes as w
from journal import ticks,frequency
from workspace import check_path
class Marks:
 def __init__(self,root,role,entry_ns):
  self.root=check_path(root);self.role=role;self.rows=[];self.saved=False
  k=c.WinDLL('kernel32',use_last_error=True)
  k.GetCurrentProcess.restype=w.HANDLE
  k.GetProcessTimes.argtypes=[w.HANDLE]+[c.POINTER(w.FILETIME)]*4
  ts=[w.FILETIME() for _ in range(4)]
  if not k.GetProcessTimes(k.GetCurrentProcess(),*[c.byref(x) for x in ts]):raise c.WinError(c.get_last_error())
  self.created=(ts[0].dwHighDateTime<<32)|ts[0].dwLowDateTime
  self.add('ENTRY',pythonEntryNs=entry_ns,markerMeaning='Python wrapper entry; not PE entry or first OS instruction')
 def add(self,event,**fields):
  if len(self.rows)>=10000:raise RuntimeError('Integration marker budget exceeded')
  self.rows.append(dict(event=event,role=self.role,pid=os.getpid(),parentPid=os.getppid(),created=str(self.created),qpc=ticks(),frequency=frequency(),monotonicNs=time.perf_counter_ns(),**fields))
 def close(self,status):
  self.add('FINAL_SHUTDOWN',status=status)
  with (self.root/f'integration-{self.role}-{os.getpid()}.json').open('x',encoding='utf-8') as f:
   json.dump(self.rows,f,indent=2);f.flush();os.fsync(f.fileno())
  self.saved=True
