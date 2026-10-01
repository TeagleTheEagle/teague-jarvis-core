"""Read-only TEST identity check; never terminates a process."""
import ctypes as c,ctypes.wintypes as w,datetime,json,pathlib
R=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
k=c.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
k.GetProcessTimes.argtypes=[w.HANDLE]+[c.POINTER(w.FILETIME)]*4;k.CloseHandle.argtypes=[w.HANDLE]
identities=[]
for run in ('smoke','repeat1','repeat2'):
 d=R/run;identities.append(dict(read(d/'ready.json'),run=run,role='monitor'))
 for p in read(d/'probes.json'):identities.append(dict(p,run=run,role='probe'))
 for p in read(d/'phases.json'):
  if 'worker_identity' in p:identities.append(dict(p['worker_identity'],run=run,role='workload'))
rows=[]
for v in identities:
 row={key:v[key] for key in ('pid','created','run','role')};handle=k.OpenProcess(0x1000,False,v['pid'])
 if not handle:
  code=c.get_last_error();row.update(status='ABSENT' if code==87 else 'UNVERIFIED',winerror=code)
 else:
  try:
   ft=[w.FILETIME() for _ in range(4)]
   if not k.GetProcessTimes(handle,*[c.byref(t) for t in ft]):row.update(status='UNVERIFIED',winerror=c.get_last_error())
   else:
    actual=str((ft[0].dwHighDateTime<<32)|ft[0].dwLowDateTime)
    row.update(observed_creation=actual,status='MATCHING_PROCESS_EXISTS' if actual==v['created'] else 'PID_REUSED_UNRELATED')
  finally:k.CloseHandle(handle)
 rows.append(row)
out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'identity_records':len(rows),'matching':sum(r['status']=='MATCHING_PROCESS_EXISTS' for r in rows),'unverified':sum(r['status']=='UNVERIFIED' for r in rows),
 'rows':rows,'retained_monitor_exit_codes':{r:read(R/r/'monitor-exit.json')['exit_code'] for r in ('smoke','repeat1','repeat2')},
 'resource_exit_codes':{r:read(R/r/'resource-exit.json')['exit'] for r in ('smoke','repeat1','repeat2')},'no_process_terminated_by_this_check':True}
with (R/'cleanup.json').open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k!='rows'}))
if out['matching'] or out['unverified']:raise SystemExit(1)
