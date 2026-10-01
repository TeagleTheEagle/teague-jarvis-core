"""Bounded synthetic workload; all allowed paths are fixed below."""
import sys,pathlib,time,hashlib,ctypes as c,ctypes.wintypes as w,json,os
from workspace import CODE as R,run_dir,activate_temp
run,mode,duration=sys.argv[1],sys.argv[2],float(sys.argv[3])
assert run.replace('-','').isalnum() and 0<duration<=160
out=run_dir(run);activate_temp(out)
source=pathlib.Path('C:\\Users\\jonny\\Documents\\Codex\\2026-09-07\\cr\\outputs\\jarvis\\docs\\stage6-heartbeat-journal-20260918\\sacrificial\\large.bin')
if mode=='Dhash':source=pathlib.Path('D:/JARVIS-STAGE6-SACRIFICIAL-TIMING-20260918/large.bin')
assert mode in ('low','moderate','full','sustained','cpu','disk','Dhash')
start=time.perf_counter();reads=[];bytecount=0;iterations=0;handle=None;buf=None;k=None
try:
 if mode!='cpu':
  k=c.WinDLL('kernel32',use_last_error=True)
  k.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,c.c_void_p,w.DWORD,w.DWORD,w.HANDLE];k.CreateFileW.restype=w.HANDLE
  k.VirtualAlloc.argtypes=[c.c_void_p,c.c_size_t,w.DWORD,w.DWORD];k.VirtualAlloc.restype=c.c_void_p
  k.ReadFile.argtypes=[w.HANDLE,c.c_void_p,w.DWORD,c.POINTER(w.DWORD),c.c_void_p];k.ReadFile.restype=w.BOOL
  k.SetFilePointerEx.argtypes=[w.HANDLE,c.c_longlong,c.c_void_p,w.DWORD];k.CloseHandle.argtypes=[w.HANDLE];k.VirtualFree.argtypes=[c.c_void_p,c.c_size_t,w.DWORD]
  handle=k.CreateFileW(str(source),0x80000000,1,None,3,0x20000000|0x08000000,None)
  if handle==c.c_void_p(-1).value:raise c.WinError(c.get_last_error())
  buf=k.VirtualAlloc(None,4194304,0x3000,4)
  if not buf:raise c.WinError(c.get_last_error())
 payload=b'x'*4194304
 while time.perf_counter()-start<duration and not (out/'workload-stop').exists():
  if mode=='cpu':hashlib.sha256(payload).digest();iterations+=1;continue
  n=w.DWORD();t=time.perf_counter()
  if not k.ReadFile(handle,buf,4194304,c.byref(n),None):raise c.WinError(c.get_last_error())
  reads.append([t,time.perf_counter()-t,n.value]);bytecount+=n.value
  if not n.value:
   if not k.SetFilePointerEx(handle,0,None,0):raise c.WinError(c.get_last_error())
   continue
  if mode not in ('disk','low'):hashlib.sha256(c.string_at(buf,n.value)).digest()
  if mode=='low':time.sleep(.12)
  elif mode=='moderate':time.sleep(.02)
 result={'status':'FINISHED','pid':os.getpid(),'mode':mode,'seconds':time.perf_counter()-start,'bytes':bytecount,'cpu_iterations':iterations,'reads':reads}
except BaseException as e:
 import traceback
 result={'status':'FAILED','pid':os.getpid(),'mode':mode,'error':str(e),'traceback':traceback.format_exc(),'reads':reads};raise
finally:
 if handle and handle!=c.c_void_p(-1).value:k.CloseHandle(handle)
 if buf:k.VirtualFree(buf,0,0x8000)
 (out/f'workload-{mode}.json').write_text(json.dumps(result))
