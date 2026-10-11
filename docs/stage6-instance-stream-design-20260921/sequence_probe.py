"""Supported SDK SystemBasicProcessInformation + exact owned-process handles.
Creates only fixed harmless probes suspended for identity observation, then resumes.
Does not equate snapshot sequence with ETW payload sequence without measurement.
"""
import ctypes as c,ctypes.wintypes as w,pathlib,json,hashlib,time,os
R=pathlib.Path(__file__).parent;plan=json.loads((R/'plan.json').read_text());C=pathlib.Path(plan['code']);T=pathlib.Path(plan['root'])/'sequence-checks';T.mkdir()
class US(c.Structure):_fields_=[('Length',w.USHORT),('MaximumLength',w.USHORT),('Buffer',c.c_void_p)]
class BASIC(c.Structure):_fields_=[('NextEntryOffset',w.ULONG),('UniqueProcessId',w.HANDLE),('InheritedFromUniqueProcessId',w.HANDLE),('SequenceNumber',c.c_ulonglong),('ImageName',US)]
class SI(c.Structure):_fields_=[('cb',w.DWORD),('lpReserved',w.LPWSTR),('lpDesktop',w.LPWSTR),('lpTitle',w.LPWSTR),('dwX',w.DWORD),('dwY',w.DWORD),('dwXSize',w.DWORD),('dwYSize',w.DWORD),('dwXCountChars',w.DWORD),('dwYCountChars',w.DWORD),('dwFillAttribute',w.DWORD),('dwFlags',w.DWORD),('wShowWindow',w.WORD),('cbReserved2',w.WORD),('lpReserved2',c.c_void_p),('hStdInput',w.HANDLE),('hStdOutput',w.HANDLE),('hStdError',w.HANDLE)]
class PI(c.Structure):_fields_=[('hProcess',w.HANDLE),('hThread',w.HANDLE),('dwProcessId',w.DWORD),('dwThreadId',w.DWORD)]
K=c.WinDLL('kernel32',use_last_error=True);N=c.WinDLL('ntdll');N.NtQuerySystemInformation.argtypes=[w.ULONG,c.c_void_p,w.ULONG,c.POINTER(w.ULONG)];N.NtQuerySystemInformation.restype=c.c_long
K.CreateProcessW.argtypes=[w.LPCWSTR,w.LPWSTR,c.c_void_p,c.c_void_p,w.BOOL,w.DWORD,c.c_void_p,w.LPCWSTR,c.POINTER(SI),c.POINTER(PI)];K.CreateProcessW.restype=w.BOOL
K.GetProcessTimes.argtypes=[w.HANDLE]+[c.POINTER(w.FILETIME)]*4;K.GetProcessTimes.restype=w.BOOL
K.ResumeThread.argtypes=[w.HANDLE];K.ResumeThread.restype=w.DWORD;K.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];K.CloseHandle.argtypes=[w.HANDLE]
K.GetExitCodeProcess.argtypes=[w.HANDLE,c.POINTER(w.DWORD)]
def times(h):
 a=[w.FILETIME() for _ in range(4)];assert K.GetProcessTimes(h,*(c.byref(x) for x in a));return [(x.dwHighDateTime<<32)|x.dwLowDateTime for x in a]
def snapshot(wanted):
 # SDK enum 252 and documented structure; finite 4 MiB buffer, no unbounded retries.
 buf=c.create_string_buffer(4*1024*1024);used=w.ULONG();begin=time.perf_counter_ns();status=N.NtQuerySystemInformation(252,buf,len(buf),c.byref(used));end=time.perf_counter_ns()
 if status!=0:raise RuntimeError('Documented query unavailable/insufficient bounded buffer: '+hex(status&0xffffffff))
 offset=0;found={}
 while True:
  assert offset+c.sizeof(BASIC)<=used.value<=len(buf);r=BASIC.from_buffer(buf,offset);pid=int(r.UniqueProcessId or 0)
  if pid in wanted:
   assert pid not in found and r.SequenceNumber
   found[pid]=dict(pid=pid,parentPid=int(r.InheritedFromUniqueProcessId or 0),sequence=str(r.SequenceNumber),queryBeginNs=begin,queryEndNs=end)
  if not r.NextEntryOffset:break
  assert r.NextEntryOffset>=c.sizeof(BASIC);offset+=r.NextEntryOffset
 return found
exe=C/'J6Probe.exe';assert hashlib.sha256(exe.read_bytes()).hexdigest()==plan['probeSHA256'];active=[];result=[];failure=None
try:
 for i in range(8):
  si=SI();si.cb=c.sizeof(si);pi=PI();cmd=c.create_unicode_buffer('"'+str(exe)+'"');begin=time.perf_counter_ns()
  if not K.CreateProcessW(str(exe),cmd,None,None,False,0x08000000|0x4,None,str(C),c.byref(si),c.byref(pi)):raise c.WinError(c.get_last_error())
  active.append(dict(pi=pi,begin=begin,created=times(pi.hProcess)[0],resumed=False))
 wanted={x['pi'].dwProcessId for x in active};first=snapshot(wanted);second=snapshot(wanted);assert set(first)==set(second)==wanted
 for x in active:
  pi=x['pi'];f=first[pi.dwProcessId];s=second[pi.dwProcessId];assert f['sequence']==s['sequence'] and f['parentPid']==os.getpid() and x['created']==times(pi.hProcess)[0]
  x.update(first=f,second=s)
 assert len({v['sequence'] for v in first.values()})==8
except BaseException as e:failure=repr(e)
finally:
 for x in active:
  pi=x['pi'];resume=K.ResumeThread(pi.hThread);x['resumed']=resume!=0xffffffff
 for x in active:
  pi=x['pi'];remaining=max(0,13.6-(time.perf_counter_ns()-x['begin'])/1e9);wait=K.WaitForSingleObject(pi.hProcess,int(remaining*1000));row=dict(pid=pi.dwProcessId,created=str(x['created']),resumed=x['resumed'],wait=wait,first=x.get('first'),second=x.get('second'))
  if wait==0:
   ts=times(pi.hProcess);ec=w.DWORD();assert K.GetExitCodeProcess(pi.hProcess,c.byref(ec));row.update(exit=str(ts[1]),exitCode=ec.value,creationStable=ts[0]==x['created']);row['handlesClosed']=bool(K.CloseHandle(pi.hThread) and K.CloseHandle(pi.hProcess))
  else:failure='Exact owned helper cleanup not proven; no forced termination'
  result.append(row)
 out=dict(status='PASS' if not failure else 'FAIL',failure=failure,rows=result,api='NtQuerySystemInformation(SystemBasicProcessInformation=252), SDK winternl.h',independentHandleCreation=True,etwSequenceEquivalence='NOT TESTED; no equivalence assumed',cimIdentity='NOT AVAILABLE from this snapshot after an unknown delayed incarnation',startupTiming='Not a performance measurement; deliberate suspended creation')
 (R/'sequence-probe.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(status=out['status'],processes=len(result),failure=failure)))
if failure:raise SystemExit(1)
