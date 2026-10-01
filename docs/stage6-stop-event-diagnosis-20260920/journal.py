"""Sacrificial Stage 6 monitoring protocol; contains no VM/runtime operations."""
import ctypes, json, os, time
from pathlib import Path
MAX_BYTES=1024*1024
MAX_LINE=4096
STALE_SECONDS=10.0
class Unhealthy(RuntimeError): pass
def ticks():
    n=ctypes.c_longlong()
    if not ctypes.windll.kernel32.QueryPerformanceCounter(ctypes.byref(n)):raise OSError('QPC failed')
    return n.value
def frequency():
    n=ctypes.c_longlong()
    if not ctypes.windll.kernel32.QueryPerformanceFrequency(ctypes.byref(n)):raise OSError('QPF failed')
    return n.value
def encode(record):return (json.dumps(record,sort_keys=True,separators=(',',':'))+'\n').encode('utf-8')
def append(stream,record):
    data=encode(record)
    if len(data)>MAX_LINE or stream.tell()+len(data)>MAX_BYTES:raise Unhealthy('journal capacity exceeded')
    if stream.write(data)!=len(data):raise Unhealthy('short write')
    stream.flush()
class PublisherWatch:
    def __init__(self,identity):
        import ctypes.wintypes as w
        self.k=ctypes.WinDLL('kernel32',use_last_error=True)
        self.k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];self.k.OpenProcess.restype=w.HANDLE
        self.k.GetProcessTimes.argtypes=[w.HANDLE]+[ctypes.POINTER(w.FILETIME)]*4
        self.k.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];self.k.CloseHandle.argtypes=[w.HANDLE]
        self.handle=self.k.OpenProcess(0x1000|0x100000,False,identity['pid'])
        if not self.handle:raise ctypes.WinError(ctypes.get_last_error())
        values=[w.FILETIME() for _ in range(4)]
        if not self.k.GetProcessTimes(self.handle,*[ctypes.byref(v) for v in values]):
            self.close();raise ctypes.WinError(ctypes.get_last_error())
        actual=(values[0].dwHighDateTime<<32)|values[0].dwLowDateTime
        if str(actual)!=identity['created']:self.close();raise Unhealthy('process creation identity mismatch')
    def check(self):
        if self.k.WaitForSingleObject(self.handle,0)!=258:raise Unhealthy('publisher exited or inaccessible')
    def close(self):
        if self.handle:self.k.CloseHandle(self.handle);self.handle=None
class Reader:
    def __init__(self,path,identity,clock=ticks,liveness=None):
        self.path=Path(path);self.identity=identity;self.clock=clock;self.failed=False
        self.stream=self.path.open('rb',buffering=0);s=os.fstat(self.stream.fileno());self.file_id=(s.st_dev,s.st_ino)
        self.pending=b'';self.sequence=0;self.last=None;self.offset=0;self.liveness=liveness
    def close(self):self.stream.close()
    def poll(self):
        if self.failed:raise Unhealthy('run already invalidated')
        try:return self._poll()
        except BaseException:
            self.failed=True
            raise
    def _poll(self):
        if self.liveness:self.liveness()
        s=self.path.stat()
        if (s.st_dev,s.st_ino)!=self.file_id or s.st_size<self.offset:raise Unhealthy('rotation/truncation rejected')
        if s.st_size>MAX_BYTES:raise Unhealthy('journal capacity exceeded')
        b=self.stream.read(MAX_BYTES+1)
        if len(b)>MAX_BYTES:raise Unhealthy('read bound exceeded')
        self.offset+=len(b);self.pending+=b
        parts=self.pending.split(b'\n');self.pending=parts.pop()
        if len(self.pending)>MAX_LINE:raise Unhealthy('partial record exceeds bound')
        for line in parts:
            if not line or len(line)>MAX_LINE:raise Unhealthy('invalid record size')
            row=json.loads(line)
            for key in ('run','pid','created','frequency'):
                if row.get(key)!=self.identity[key]:raise Unhealthy('publisher identity mismatch')
            if type(row.get('seq')) is not int or row['seq']!=self.sequence+1:raise Unhealthy('duplicate/skipped sequence')
            if type(row.get('ticks')) is not int or row['ticks']<=0:raise Unhealthy('invalid monotonic time')
            if self.last and row['ticks']<self.last['ticks']:raise Unhealthy('time regressed')
            if row.get('state')!='ACTIVE' or row.get('violations')!=0 or row.get('pump')!=row['seq']:raise Unhealthy('event pump not healthy')
            if not isinstance(row.get('utc'),str) or not row['utc']:raise Unhealthy('missing publisher timestamp')
            self.sequence=row['seq'];self.last=row
        if self.last is None:raise Unhealthy('no complete heartbeat')
        age=(self.clock()-self.last['ticks'])/self.identity['frequency']
        if age<0 or age>STALE_SECONDS:raise Unhealthy('stale/future heartbeat')
        return {'sequence':self.sequence,'age':age,'partial_bytes':len(self.pending)}
