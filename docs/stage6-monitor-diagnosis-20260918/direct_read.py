"""Read/hash only the sacrificial file with Windows unbuffered I/O; no global cache changes."""
import ctypes as c, ctypes.wintypes as w, pathlib, time, json, hashlib, datetime as dt
R=pathlib.Path(__file__).parent; path=R/'synthetic-1GiB.bin'; k=c.WinDLL('kernel32',use_last_error=True)
k.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,c.c_void_p,w.DWORD,w.DWORD,w.HANDLE];k.CreateFileW.restype=w.HANDLE
k.VirtualAlloc.argtypes=[c.c_void_p,c.c_size_t,w.DWORD,w.DWORD];k.VirtualAlloc.restype=c.c_void_p
k.ReadFile.argtypes=[w.HANDLE,c.c_void_p,w.DWORD,c.POINTER(w.DWORD),c.c_void_p];k.ReadFile.restype=w.BOOL
k.SetFilePointerEx.argtypes=[w.HANDLE,c.c_longlong,c.c_void_p,w.DWORD];k.SetFilePointerEx.restype=w.BOOL
k.CloseHandle.argtypes=[w.HANDLE];k.VirtualFree.argtypes=[c.c_void_p,c.c_size_t,w.DWORD]
h=k.CreateFileW(str(path),0x80000000,1,None,3,0x20000000|0x08000000,None)
if h==c.c_void_p(-1).value:raise c.WinError(c.get_last_error())
buf=k.VirtualAlloc(None,4*1024*1024,0x3000,4)
if not buf:raise c.WinError(c.get_last_error())
start=time.monotonic();total=0;lat=[];hasher=hashlib.sha256();status='COMPLETED';error=None
utc=lambda:dt.datetime.now(dt.timezone.utc).isoformat()
begin=utc()
try:
 while time.monotonic()-start<60 and not (R/'stop.json').exists():
  if (R/'monitor-failure.json').exists():raise RuntimeError('Monitor failure')
  heartbeat=json.loads((R/'heartbeat.json').read_text())
  age=time.time()-dt.datetime.fromisoformat(heartbeat['Utc'].replace('Z','+00:00')).timestamp()
  if age>10 or heartbeat['Violations']:raise RuntimeError('Unchanged monitoring rule failed')
  got=w.DWORD();t=time.monotonic()
  if not k.ReadFile(h,buf,4*1024*1024,c.byref(got),None):raise c.WinError(c.get_last_error())
  lat.append(time.monotonic()-t)
  if not got.value:
   if not k.SetFilePointerEx(h,0,None,0):raise c.WinError(c.get_last_error())
   continue
  hasher.update(c.string_at(buf,got.value));total+=got.value
except BaseException as exc:status='FAILED';error=str(exc)
finally:
 k.CloseHandle(h);k.VirtualFree(buf,0,0x8000)
 (R/'direct-read-result.json').write_text(json.dumps({'Status':status,'Error':error,'StartedUtc':begin,'EndedUtc':utc(),'Bytes':total,'Seconds':time.monotonic()-start,'ReadLatenciesSec':lat,'Flags':'FILE_FLAG_NO_BUFFERING | FILE_FLAG_SEQUENTIAL_SCAN; sacrificial file only'}))
print(status,total,flush=True)
