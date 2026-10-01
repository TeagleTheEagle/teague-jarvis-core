"""Read-only retained observer identity/liveness plus fresh application heartbeat."""
import ctypes as c,ctypes.wintypes as w
from evidence_support import K,times
from journal import ticks,frequency
from dry_contract import read
class Health:
 def __init__(self,root):
  self.root=root;self.handles=[];self.samples=[]
  try:
   self.identities=read(root/'observer-identities.json')
   for role,x in self.identities.items():
    h=K.OpenProcess(0x100000|0x1000,False,x['pid'])
    if not h:raise c.WinError(c.get_last_error())
    self.handles.append((role,h,x['created']))
    if times(h)[0]!=x['created']:raise RuntimeError('Observer creation identity mismatch')
   self.check()
  except BaseException:self.close();raise
 def check(self):
  for role,h,created in self.handles:
   if K.WaitForSingleObject(h,0)!=258 or times(h)[0]!=created:raise RuntimeError('Observer exited or identity changed: '+role)
  v=read(self.root/'app-health.json');now=ticks();age=(now-v['qpc'])/v['frequency']
  if v['pid']!=self.identities['app']['pid'] or v['frequency']!=frequency() or not v['healthy'] or not 0<=age<10:raise RuntimeError('Application heartbeat unhealthy/stale')
  if (self.root/'app-result.json').exists() or (self.root/'etw-result.json').exists():raise RuntimeError('Observer finalized during workload')
  self.samples.append(dict(qpc=now,age=age,appPid=v['pid'],kernelPid=self.identities['etw']['pid']))
  return self.samples[-1]
 def close(self):
  for _,h,_ in self.handles:K.CloseHandle(h)
  self.handles=[]
