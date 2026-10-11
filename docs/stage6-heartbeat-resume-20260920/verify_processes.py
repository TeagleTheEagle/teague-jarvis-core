"""Read-only PID+creation-time reconciliation. No termination or VM API calls."""
import ctypes as c, ctypes.wintypes as w, json, pathlib, datetime
from prepare import R, OLD, save
k=c.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
k.GetProcessTimes.argtypes=[w.HANDLE]+[c.POINTER(w.FILETIME)]*4
k.CloseHandle.argtypes=[w.HANDLE]
identities=[]
for base in (OLD,R):
    for p in base.glob('*/process-evidence.json'):
        v=json.loads(p.read_text())['publisher_identity'];identities.append(dict(v,evidence=str(p)))
    p=base/'probe-handle-regression.json'
    if p.exists():
        identities.extend(dict(v,evidence=str(p)) for v in json.loads(p.read_text())['identities'])
    for run in ('loads','loads2'):
        p=base/run/'ready.json'
        if p.exists():identities.append(dict(json.loads(p.read_text(encoding='utf-8-sig')),evidence=str(p)))
        p=base/run/'probes.json'
        if p.exists():identities.extend(dict(v,evidence=str(p)) for v in json.loads(p.read_text(encoding='utf-8-sig')) if 'created' in v)
rows=[]
for v in identities:
    h=k.OpenProcess(0x1000,False,v['pid'])
    row={'pid':v['pid'],'expected_creation':str(v['created']),'evidence':v['evidence']}
    if not h:
        code=c.get_last_error();row.update(winerror=code,status='ABSENT' if code==87 else 'UNVERIFIED')
    else:
        try:
            values=[w.FILETIME() for _ in range(4)]
            if not k.GetProcessTimes(h,*[c.byref(t) for t in values]):
                row.update(status='UNVERIFIED',winerror=c.get_last_error())
            else:
                created=str((values[0].dwHighDateTime<<32)|values[0].dwLowDateTime)
                row.update(observed_creation=created,status='MATCHING_PROCESS_EXISTS' if created==str(v['created']) else 'PID_REUSED_UNRELATED')
        finally:k.CloseHandle(h)
    rows.append(row)
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'identity_records':len(rows),
        'matching':sum(r['status']=='MATCHING_PROCESS_EXISTS' for r in rows),
        'unverified':sum(r['status']=='UNVERIFIED' for r in rows),'rows':rows,
        'limitations':'Only identities with preserved PID and creation time checked. No inference from PID alone; no process terminated.'}
save('process-identity-check.json',report)
print(json.dumps({k:v for k,v in report.items() if k!='rows'}))
