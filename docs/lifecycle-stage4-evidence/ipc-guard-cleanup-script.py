import ctypes as c, json, hashlib, subprocess, time
from ctypes import wintypes as w
from pathlib import Path
b=Path.cwd(); e=b/'docs/lifecycle-stage4-evidence'; old=json.loads((e/'electron-challenge-diagnosis-followup.json').read_text()); root=b/'tests/lifecycle_stage1/evidence/TEST-STAGE4-664be26d9d7b4aaeb0eb80553005546c'
k=c.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
k.GetProcessTimes.argtypes=[w.HANDLE]+[c.POINTER(w.FILETIME)]*4
k.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,c.POINTER(w.DWORD)]
k.TerminateProcess.argtypes=[w.HANDLE,w.UINT];k.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];k.CloseHandle.argtypes=[w.HANDLE]
rows=json.loads(subprocess.check_output(['powershell','-NoProfile','-Command',"@(Get-CimInstance Win32_Process -Filter 'ProcessId=26784 OR ProcessId=24164' | Select-Object ProcessId,ParentProcessId,CreationDate,ExecutablePath,CommandLine) | ConvertTo-Json -Depth 3"],text=True) or '[]');rows=rows if isinstance(rows,list) else [rows]
checks=[];handles={};before={p:hashlib.sha256((b/p).read_bytes()).hexdigest() for p in old['preserved_hashes']}
try:
 assert (root/'TEST_ONLY').read_text()=='NO PRODUCTION SERVICES'
 assert json.loads((root/'core.json').read_text())==old['expected_core_identity']
 for key,pid in [('live_core_identity',26784),('launcher',24164)]:
  row=next((r for r in rows if r['ProcessId']==pid),None)
  if row is None: checks.append({'pid':pid,'already_absent':True});continue
  handle=k.OpenProcess(0x101001,False,pid)
  if not handle:raise c.WinError(c.get_last_error())
  handles[pid]=handle; times=[w.FILETIME() for _ in range(4)]
  if not k.GetProcessTimes(handle,*map(c.byref,times)):raise c.WinError(c.get_last_error())
  created=(times[0].dwHighDateTime<<32)|times[0].dwLowDateTime
  size=w.DWORD(32768); buf=c.create_unicode_buffer(size.value)
  if not k.QueryFullProcessImageNameW(handle,0,buf,c.byref(size)):raise c.WinError(c.get_last_error())
  digest=hashlib.sha256(Path(buf.value).read_bytes()).hexdigest()
  assert created==old[key]['created'] and digest==old[key]['exe_digest']
  assert str(root).lower() in row['CommandLine'].lower() and '--app-worker' in row['CommandLine'] and 'fixtures.py' in row['CommandLine']
  checks.append({'pid':pid,'created':created,'exe_digest':digest,'executable':buf.value,'cim':row,'verified':True,'terminated':False})
 # Both identities have passed; termination uses the same held handles.
 if 26784 in handles and k.WaitForSingleObject(handles[26784],0)==258:
  if not k.TerminateProcess(handles[26784],0xE004):raise c.WinError(c.get_last_error())
  next(x for x in checks if x['pid']==26784)['terminated']=True
  assert k.WaitForSingleObject(handles[26784],5000)==0
 if 24164 in handles:
  result=k.WaitForSingleObject(handles[24164],10000)
  if result==258:
   if not k.TerminateProcess(handles[24164],0xE004):raise c.WinError(c.get_last_error())
   next(x for x in checks if x['pid']==24164)['terminated']=True
   assert k.WaitForSingleObject(handles[24164],5000)==0
 for x in checks:
  if x['pid'] in handles:x['exit_observed']=k.WaitForSingleObject(handles[x['pid']],0)==0
 assert all(hashlib.sha256((b/p).read_bytes()).hexdigest()==v for p,v in before.items())
 result={'checks':checks,'method':'Authenticated shutdown attempted first; retained recovery required verified handle termination','evidence_unchanged':True,'before_hashes':before,'status':'PASS'}
except Exception as exc:
 import traceback
 result={'checks':checks,'status':'STOP_DISCREPANCY','traceback':traceback.format_exc()}
finally:
 for handle in handles.values():k.CloseHandle(handle)
(e/'ipc-guard-approved-cleanup.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['checks']));print(result['status'])
