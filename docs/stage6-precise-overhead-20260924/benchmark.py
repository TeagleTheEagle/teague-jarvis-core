"""Bounded offline orchestration; original fixture binary and callback code unchanged."""
import ctypes as ct,ctypes.wintypes as w,time,datetime,json,subprocess,sys
from preflight import R,LIVE,load,sha,put
k=ct.WinDLL('kernel32',use_last_error=True)
class SA(ct.Structure):_fields_=[('length',w.DWORD),('descriptor',w.LPVOID),('inherit',w.BOOL)]
class SI(ct.Structure):
    _fields_=[('cb',w.DWORD),('reserved',w.LPWSTR),('desktop',w.LPWSTR),('title',w.LPWSTR),('x',w.DWORD),('y',w.DWORD),('cx',w.DWORD),('cy',w.DWORD),('charsx',w.DWORD),('charsy',w.DWORD),('fill',w.DWORD),('flags',w.DWORD),('show',w.WORD),('reserved2size',w.WORD),('reserved2',ct.POINTER(w.BYTE)),('stdin',w.HANDLE),('stdout',w.HANDLE),('stderr',w.HANDLE)]
class PI(ct.Structure):_fields_=[('process',w.HANDLE),('thread',w.HANDLE),('pid',w.DWORD),('tid',w.DWORD)]
k.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,ct.POINTER(SA),w.DWORD,w.DWORD,w.HANDLE];k.CreateFileW.restype=w.HANDLE
k.CreateProcessW.argtypes=[w.LPCWSTR,w.LPWSTR,ct.c_void_p,ct.c_void_p,w.BOOL,w.DWORD,ct.c_void_p,w.LPCWSTR,ct.POINTER(SI),ct.POINTER(PI)];k.CreateProcessW.restype=w.BOOL
for name in ['GetProcessTimes','GetThreadTimes']:
    getattr(k,name).argtypes=[w.HANDLE]+[ct.POINTER(w.FILETIME)]*4;getattr(k,name).restype=w.BOOL
k.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];k.WaitForSingleObject.restype=w.DWORD
k.GetExitCodeProcess.argtypes=[w.HANDLE,ct.POINTER(w.DWORD)];k.GetExitCodeProcess.restype=w.BOOL
k.CloseHandle.argtypes=[w.HANDLE];k.CloseHandle.restype=w.BOOL
def times(h,thread=False):
    values=[w.FILETIME() for _ in range(4)]
    if not getattr(k,'GetThreadTimes' if thread else 'GetProcessTimes')(h,*[ct.byref(x) for x in values]):raise ct.WinError(ct.get_last_error())
    return dict(zip(['createdFILETIME','exitFILETIME','kernel100ns','user100ns'],[(x.dwHighDateTime<<32)|x.dwLowDateTime for x in values]))
def checked(h):
    if h is None or h==ct.c_void_p(-1).value:raise ct.WinError(ct.get_last_error())
    return h
def run(batch,exe):
    out=LIVE/f'batch-{batch:02}.jsonl';err=LIVE/f'batch-{batch:02}-stderr.txt';security=SA(ct.sizeof(SA),None,True)
    handles=[];pi=PI();rec={'batch':batch,'executable':exe,'sha256':sha(exe),'beginUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':[exe,'benchmark'],'cwd':str(__import__('pathlib').Path(exe).parent),'creationFlags':0,'UAC':False}
    try:
        for path,access,creation in [(str(out),0x40000000,1),(str(err),0x40000000,1),('NUL',0x80000000,3)]:handles.append(checked(k.CreateFileW(path,access,3,ct.byref(security),creation,0x80,None)))
        si=SI();si.cb=ct.sizeof(si);si.flags=0x100;si.stdout,si.stderr,si.stdin=handles
        command=ct.create_unicode_buffer(subprocess.list2cmdline([exe,'benchmark']))
        begin=time.perf_counter_ns()
        if not k.CreateProcessW(exe,command,None,None,True,0,None,rec['cwd'],ct.byref(si),ct.byref(pi)):raise ct.WinError(ct.get_last_error())
        rec.update(pid=pi.pid,primaryThreadId=pi.tid,createProcessNs=time.perf_counter_ns()-begin,processInitial=times(pi.process),threadInitial=times(pi.thread,True))
        put(LIVE/f'batch-{batch:02}-started.json',rec)
        result=k.WaitForSingleObject(pi.process,300000)
        rec['waitResult']=result
        if result!=0:raise RuntimeError('Bounded process wait failed; no replacement batch; retained identity in started record')
        code=w.DWORD()
        if not k.GetExitCodeProcess(pi.process,ct.byref(code)):raise ct.WinError(ct.get_last_error())
        rec.update(exitCode=code.value,processFinal=times(pi.process),threadFinal=times(pi.thread,True),endUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),wallNs=time.perf_counter_ns()-begin)
        if code.value:raise RuntimeError('Fixture nonzero exit')
    finally:
        failures=[]
        for h in [pi.thread,pi.process]+handles:
            if h and not k.CloseHandle(h):failures.append(ct.get_last_error())
        rec['handleCloseErrors']=failures
        put(LIVE/f'batch-{batch:02}-exit.json',rec)
    rows=[json.loads(x) for x in out.read_text().splitlines()]
    assert rows[0]['kind']=='protocol' and rows[0]['pairs']==8 and len(rows)==17
    trials=rows[1:]
    for i in range(8):
        a,b=trials[2*i:2*i+2]
        assert a['pair']==b['pair']==i
        assert a['enabled']==bool(i%2) and b['enabled']!=a['enabled']
        assert a['callbacks']==b['callbacks'] and a['callbacks']>0
        for t in [a,b]:assert t['dispatcherCpu100ns']>0 and t['wallSeconds']>0 and t['frequency']>0
    return len(trials)//2
if __name__=='__main__':
    protocol=load(R/'protocol.json');pre=load(R/'preflight.json');assert sha(R/'protocol.json')==pre['protocolSHA256']
    for row in pre['harnessSources']:assert sha(row['path'])==row['sha256']
    assert sha(protocol['binary'])==protocol['binarySHA256']
    started=time.monotonic();completed=0
    try:
        for batch in range(32):
            if time.monotonic()-started>2400:raise RuntimeError('Campaign bound reached; no additional trials')
            assert sha(protocol['binary'])==protocol['binarySHA256']
            completed+=run(batch,protocol['binary'])
            print(json.dumps(dict(completedBatches=batch+1,completedPairs=completed,elapsedSeconds=round(time.monotonic()-started,1))),flush=True)
        put(R/'execution.json',dict(status='EXECUTION_COMPLETE',batches=32,pairs=completed,elapsedSeconds=time.monotonic()-started,excludedTrials=[],retries=0))
    except BaseException as e:
        put(R/'execution.json',dict(status='BENCHMARK_METHOD_DEFECTIVE',completedPairs=completed,error=repr(e),retries=0))
        raise
