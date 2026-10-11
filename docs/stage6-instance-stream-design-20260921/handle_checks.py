"""Fresh harmless fixed-image processes; Win32 handles only. No fabricated events."""
import pathlib,json,ctypes,ctypes.wintypes as w,subprocess,hashlib,time,collections
R=pathlib.Path(__file__).parent;plan=json.loads((R/'plan.json').read_text());C=pathlib.Path(plan['code']);T=pathlib.Path(plan['root'])/'handle-checks';T.mkdir()
K=ctypes.WinDLL('kernel32',use_last_error=True)
K.GetProcessTimes.argtypes=[w.HANDLE]+[ctypes.POINTER(w.FILETIME)]*4;K.GetProcessTimes.restype=w.BOOL
K.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)];K.QueryFullProcessImageNameW.restype=w.BOOL
K.GetProcessId.argtypes=[w.HANDLE];K.GetProcessId.restype=w.DWORD
K.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];K.OpenProcess.restype=w.HANDLE
K.CloseHandle.argtypes=[w.HANDLE];K.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD]
exe=C/'J6Probe.exe';assert hashlib.sha256(exe.read_bytes()).hexdigest()==plan['probeSHA256']
rows=[]
def times(handle):
 t=[w.FILETIME() for _ in range(4)];assert K.GetProcessTimes(handle,*(ctypes.byref(x) for x in t))
 return [(x.dwHighDateTime<<32)|x.dwLowDateTime for x in t]
def save():
 (R/'handle-checks.json').write_text(json.dumps(dict(rows=rows,count=len(rows),scope='Real Win32 handles, no new ETW/native/CIM session. Not full identity stress.'),indent=2))
for batch in range(8):
 active=[]
 for i in range(8):
  start=time.perf_counter_ns();p=subprocess.Popen([str(exe)],cwd=C,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
  handle=int(p._handle);before=times(handle);image=ctypes.create_unicode_buffer(32768);n=w.DWORD(len(image));assert K.QueryFullProcessImageNameW(handle,0,image,ctypes.byref(n))
  assert pathlib.Path(image.value)==exe and K.GetProcessId(handle)==p.pid
  active.append((p,before,start,image.value))
 for p,before,start,image in active:
  exit_=p.wait(timeout=13.6);h=int(p._handle);after=times(h);assert before[0]==after[0] and after[1]>=after[0] and K.WaitForSingleObject(h,0)==0
  # Independent late acquisition while the original exact object handle remains retained.
  late=K.OpenProcess(0x1000|0x100000,False,p.pid);lateError=0;lateMatches=False
  if late:
   lateTimes=times(late);lateMatches=(lateTimes[0],lateTimes[1])==(after[0],after[1]);assert lateMatches;assert K.CloseHandle(late)
  else:lateError=ctypes.get_last_error()
  p._handle.Close()
  rows.append(dict(batch=batch,pid=p.pid,created=str(after[0]),exitFiletime=str(after[1]),image=image,imageSHA256=plan['probeSHA256'],parentPid=__import__('os').getpid(),exitCode=exit_,creationStable=True,signaled=True,handleClosed=True,lateOpenMatched=lateMatches,lateOpenError=lateError,elapsedNs=time.perf_counter_ns()-start));save()
assert len({(r['pid'],r['created']) for r in rows})==len(rows)
result=dict(processes=len(rows),distinctPids=len({r['pid'] for r in rows}),reusedPidOccurrences=len(rows)-len({r['pid'] for r in rows}),creationStable=sum(r['creationStable'] for r in rows),lateHandleMatches=sum(r['lateOpenMatched'] for r in rows),handleExits=sum(r['signaled'] for r in rows),handlesClosed=sum(r['handleClosed'] for r in rows),falseUniqueMatchesObserved=0,notCovered=['fresh ETW','fresh CIM','fresh native PE','parent PID reuse','reordered application delivery'])
(R/'handle-summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
