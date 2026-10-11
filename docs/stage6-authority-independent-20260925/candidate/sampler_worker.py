"""Fixed secondary telemetry only; no caller code, filesystem query or command API."""
import ctypes as c,ctypes.wintypes as w,sys,json,pathlib,time,os,mmap,struct
from workspace import run_dir
root=run_dir(sys.argv[1]);mode=sys.argv[2];name=sys.argv[3]
assert mode in ('normal','slow','hung','exception','crash') and name.startswith('Local\\J6Secondary-'+root.name+'-')
if mode=='slow':time.sleep(5)
if mode=='hung':time.sleep(60)
if mode=='exception':raise RuntimeError('Injected secondary telemetry exception')
if mode=='crash':os._exit(7)
class MEM(c.Structure):_fields_=[('length',w.DWORD),('load',w.DWORD)]+[(n,c.c_ulonglong) for n in ('totalPhysical','availablePhysical','totalPage','availablePage','totalVirtual','availableVirtual','extended')]
k=c.WinDLL('kernel32',use_last_error=True);m=MEM();m.length=c.sizeof(m)
if not k.GlobalMemoryStatusEx(c.byref(m)):raise c.WinError(c.get_last_error())
v=[w.FILETIME() for _ in range(3)]
if not k.GetSystemTimes(*[c.byref(x) for x in v]):raise c.WinError(c.get_last_error())
out=dict(pid=os.getpid(),monotonicNs=time.perf_counter_ns(),memoryLoad=m.load,availablePhysical=m.availablePhysical,systemTimes100ns=[(x.dwHighDateTime<<32)|x.dwLowDateTime for x in v],diskMetrics='NOT_COLLECTED',secondary=True)
raw=json.dumps(out).encode();assert len(raw)<4000
with mmap.mmap(-1,4096,tagname=name) as view:view[:4+len(raw)]=struct.pack('<I',len(raw))+raw
