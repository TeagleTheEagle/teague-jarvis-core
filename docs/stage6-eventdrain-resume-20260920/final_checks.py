"""Post-run, read-only identity/source reconciliation. Never terminates a process."""
import ctypes as c, ctypes.wintypes as w, pathlib, json, hashlib, datetime
R=pathlib.Path(__file__).resolve().parent
RUNS=('a1','minimal','persist-d','none','dhash','a2','a3')
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):
    with (R/n).open('x',encoding='utf-8') as f: json.dump(v,f,indent=2)
k=c.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
k.GetProcessTimes.argtypes=[w.HANDLE]+[c.POINTER(w.FILETIME)]*4;k.GetProcessTimes.restype=w.BOOL
k.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];k.WaitForSingleObject.restype=w.DWORD
k.CloseHandle.argtypes=[w.HANDLE];k.CloseHandle.restype=w.BOOL
def check(pid,created):
    h=k.OpenProcess(0x1000|0x100000,False,int(pid))
    if not h:
        err=c.get_last_error()
        return dict(pid=pid,expectedCreation=str(created),state='ABSENT' if err==87 else 'UNCONFIRMED',winerror=err)
    try:
        ts=[w.FILETIME() for _ in range(4)]
        if not k.GetProcessTimes(h,*[c.byref(t) for t in ts]):raise c.WinError(c.get_last_error())
        actual=str((ts[0].dwHighDateTime<<32)|ts[0].dwLowDateTime)
        wait=k.WaitForSingleObject(h,0)
        state='PID_REUSED_NOT_OUR_PROCESS' if actual!=str(created) else 'EXITED' if wait==0 else 'LIVE' if wait==258 else 'UNCONFIRMED'
        return dict(pid=pid,expectedCreation=str(created),observedCreation=actual,state=state,wait=wait)
    finally:k.CloseHandle(h)
results=[];drift=[];cleanup=[]
frozen=('monitor.ps1','event_queue.cs','LoopTiming.cs','EventTap.cs','journal.py','workload.py','resources.ps1','J6Probe.exe','collect.py','launch.ps1')
for name in RUNS:
    d=R/name;identity=read(d/'ready.json');ex=read(d/'monitor-exit.json');phase=read(d/'phases.json')[0]
    results.append(dict(run=name,role='monitor',**check(identity['pid'],identity['created'])))
    worker=phase.get('worker_identity')
    if worker:results.append(dict(run=name,role='hash-worker',**check(worker['pid'],worker['created'])))
    retained=read(d/'retained-handle-verification.json')
    for p in retained:results.append(dict(run=name,role='probe',**check(p['pid'],p['times'][0])))
    resource=read(d/'resource-exit.json') if (d/'resource-exit.json').exists() else None
    cleanup.append(dict(run=name,monitorExit=ex['exit_code'],workerExit=phase.get('worker_exit'),resourceExit=None if resource is None else resource['exit'],retainedProbes=len(retained),kernelExitTimesPresent=all(int(p['times'][1])>int(p['times'][0]) for p in retained),forcedCleanup=(d/'workload-forced-cleanup.json').exists()))
    old={pathlib.Path(x['path']).name:x['sha256'].lower() for x in read(d/'source-hashes.json')}
    for n in frozen:
        if old[n]!=sha(R/n):drift.append(dict(run=name,file=n))
uncertain=[v for v in results if v['state'] in ('LIVE','UNCONFIRMED')]
bad=[v for v in cleanup if v['monitorExit']!=0 or v['workerExit']!=0 or v['resourceExit'] not in (None,0) or not v['kernelExitTimesPresent'] or v['forcedCleanup']]
save('final-identity-source-check.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),identities=results,cleanup=cleanup,frozenDiagnosticFiles=list(frozen),hashComparisons=len(RUNS)*len(frozen),sourceDrift=drift,unexplainedIdentities=uncertain,cleanupProblems=bad,method='OpenProcess query/synchronize only; creation time plus signalled state. No termination. Resource process exits separately proven by retained Popen communicate.',protectedAccess=False,productionChanges=False,status='PASS' if not (uncertain or bad or drift) else 'FAIL'))
print(json.dumps(dict(identities=len(results),sourceDrift=len(drift),unexplainedIdentities=len(uncertain),cleanupProblems=len(bad))))
if uncertain or bad or drift:raise SystemExit(1)
