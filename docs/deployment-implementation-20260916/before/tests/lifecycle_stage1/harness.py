"""TEST ONLY, Windows, standard library only. Never import production JARVIS.

Cooperative-process identity experiment, NOT authentication or a deployment host.
"""
import ctypes as c
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
import hashlib
from contextlib import nullcontext

if os.name != 'nt':
    raise RuntimeError('Windows test harness only')
k = c.WinDLL('kernel32', use_last_error=True)
k.CreateFileW.argtypes = [w.LPCWSTR,w.DWORD,w.DWORD,c.c_void_p,w.DWORD,w.DWORD,w.HANDLE]
k.CreateFileW.restype = w.HANDLE
k.CloseHandle.argtypes = [w.HANDLE]
k.GetHandleInformation.argtypes = [w.HANDLE,c.POINTER(w.DWORD)]
k.GetFileAttributesW.argtypes = [w.LPCWSTR]
k.GetFileAttributesW.restype = w.DWORD
k.OpenProcess.argtypes = [w.DWORD,w.BOOL,w.DWORD]
k.OpenProcess.restype = w.HANDLE
k.GetProcessTimes.argtypes = [w.HANDLE]+[c.POINTER(w.FILETIME)]*4
k.GetExitCodeProcess.argtypes = [w.HANDLE,c.POINTER(w.DWORD)]

BASE = Path(__file__).absolute().parent / 'evidence'

def validate(root):
    root = Path(os.path.abspath(root))
    if not root.is_relative_to(BASE) or root == BASE:
        raise ValueError('TEST namespace required')
    for p in [root, *root.parents]:
        attrs = k.GetFileAttributesW(str(p))
        if attrs == 0xffffffff or attrs & 0x400:
            raise ValueError('Missing or reparse directory')
    if (root/'TEST_ONLY').read_text() != 'NO PRODUCTION SERVICES':
        raise ValueError('Missing test identity')
    return root

class Busy(Exception): pass

class Lock:
    def __init__(self, root, name):
        root = validate(root)
        if name not in ('supervisor.lock','core.lock'):
            raise ValueError('Unknown lock')
        target=root/name
        attrs=k.GetFileAttributesW(str(target))
        if attrs != 0xffffffff and attrs & (0x400|0x10):
            raise ValueError('Invalid lock file')
        # No sharing (including delete), OPEN_ALWAYS, non-inheritable SECURITY_ATTRIBUTES=NULL.
        self.handle=k.CreateFileW(str(target),0xc0000000,0,None,4,0x00200080,None)
        if self.handle == c.c_void_p(-1).value:
            error=c.get_last_error()
            if error == 32: raise Busy('Lock owned')
            raise OSError(error,'Lock access failed')
        flags=w.DWORD()
        if not k.GetHandleInformation(self.handle,c.byref(flags)) or flags.value & 1:
            self.close();raise RuntimeError('Inheritable lock')
    def close(self):
        if self.handle is not None:
            k.CloseHandle(self.handle);self.handle=None
    def __enter__(self):return self
    def __exit__(self,*args):self.close()

def process_identity(pid):
    h=k.OpenProcess(0x1000,False,pid)
    if not h:return None
    try:
        creation,exit_,kernel,user=[w.FILETIME() for _ in range(4)]
        status=w.DWORD()
        if not k.GetExitCodeProcess(h,c.byref(status)) or status.value != 259:return None
        if not k.GetProcessTimes(h,*map(c.byref,(creation,exit_,kernel,user))):return None
        return {'pid':pid,'created':(creation.dwHighDateTime<<32)|creation.dwLowDateTime}
    finally:k.CloseHandle(h)

k.CreateMutexW.argtypes = [c.c_void_p,w.BOOL,w.LPCWSTR]
k.CreateMutexW.restype = w.HANDLE
k.WaitForSingleObject.argtypes = [w.HANDLE,w.DWORD]
k.WaitForSingleObject.restype = w.DWORD
k.ReleaseMutex.argtypes = [w.HANDLE]

class IPCGuardError(RuntimeError): pass

class IPCGuard:
    """TEST-only, short file critical section; never a Core lifetime lock."""
    def __init__(self,path,deadline=None):
        path=Path(path)
        if path.name not in ('challenge.json','response.json'):
            raise ValueError('Not an identity IPC file')
        root=validate(path.parent)
        digest=hashlib.sha256(str(root).casefold().encode('utf8')).hexdigest()
        self.handle=k.CreateMutexW(None,False,'Global\\TEAGUE-TEST-IPC-'+digest)
        if not self.handle:raise IPCGuardError('IPC guard creation failed: '+str(c.get_last_error()))
        self.owned=False
        flags=w.DWORD()
        if not k.GetHandleInformation(self.handle,c.byref(flags)) or flags.value & 1:
            k.CloseHandle(self.handle);self.handle=None
            raise IPCGuardError('Invalid IPC guard handle')
        remaining=.25 if deadline is None else min(.25,max(0,deadline-time.monotonic()))
        result=k.WaitForSingleObject(self.handle,int(remaining*1000))
        if result==0:
            self.owned=True
            # Even the target attribute query belongs inside file coordination.
            attrs=k.GetFileAttributesW(str(path))
            if attrs != 0xffffffff and attrs & (0x400|0x10):
                self.__exit__(None,None,None)
                raise ValueError('Invalid identity IPC file')
            return
        if result==0x80:k.ReleaseMutex(self.handle)
        k.CloseHandle(self.handle);self.handle=None
        raise IPCGuardError('IPC guard '+('abandoned' if result==0x80 else 'timeout' if result==258 else 'wait failed'))
    def __enter__(self):return self
    def __exit__(self,*args):
        try:
            if self.owned and not k.ReleaseMutex(self.handle):
                raise IPCGuardError('IPC guard release failed')
        finally:k.CloseHandle(self.handle);self.handle=None;self.owned=False

def ipc_guard(path,deadline=None):
    return IPCGuard(path,deadline) if Path(path).name in ('challenge.json','response.json') else nullcontext()

def write(path,data,deadline=None):
    with ipc_guard(path,deadline):
        temporary=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
        temporary.write_text(json.dumps(data),encoding='utf8')
        os.replace(temporary,path)

def read(path,deadline=None):
    with ipc_guard(path,deadline):
        try:return json.loads(path.read_text(encoding='utf8'))
        except (OSError,ValueError):return None

def event(root,kind,**fields):
    write(root/(f'{time.time_ns()}-{os.getpid()}-{kind}.json'),dict(kind=kind,pid=os.getpid(),at=time.perf_counter_ns(),**fields))

def spawn(root,role,phase='normal',close_fds=True):
    # Do not inherit provider keys, tokens or arbitrary environment configuration.
    env={key:os.environ[key] for key in ('SystemRoot','WINDIR','TEMP','TMP') if key in os.environ}
    return subprocess.Popen([sys.executable,'-I',str(Path(__file__).absolute()),role,str(root),phase],
                            env=env,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,close_fds=close_fds,creationflags=0x08000000)

def core(root,phase):
    if phase=='delay-lock':time.sleep(.4)
    with Lock(root,'core.lock'):
        event(root,'core_acquired',identity=process_identity(os.getpid()))
        if phase=='crash-locked':os._exit(71)
        if phase=='delay-metadata':time.sleep(.4)
        identity={**process_identity(os.getpid()),'namespace':root.name,'mode':'TEST','epoch':uuid.uuid4().hex}
        write(root/'core.json',identity)
        event(root,'core_ready',identity=identity)
        if phase=='crash-ready':os._exit(72)
        end=time.monotonic()+15
        last_answered=object()
        while time.monotonic()<end and not (root/'stop').exists():
            request=read(root/'challenge.json')
            if request and request.get('challenge') != last_answered:
                challenge=request.get('challenge')
                write(root/'response.json',dict(identity=identity,challenge=challenge))
                last_answered=challenge
            time.sleep(.015)
        event(root,'core_releasing')

def reconcile(root):
    deadline=time.monotonic()+1
    metadata=read(root/'core.json')
    if not metadata or metadata.get('mode')!='TEST' or metadata.get('namespace')!=root.name:
        return False
    expected={key:metadata.get(key) for key in ('pid','created')}
    if process_identity(expected['pid'])!=expected:return False
    challenge=uuid.uuid4().hex
    write(root/'challenge.json',{'challenge':challenge},deadline)
    while time.monotonic()<deadline:
        response=read(root/'response.json',deadline)
        if response=={'identity':metadata,'challenge':challenge}:
            try:
                with Lock(root,'core.lock'):return False
            except Busy:return True
        time.sleep(.02)
    return False

def coordinator(root,phase):
    deadline=time.monotonic()+5
    while not (root/'go').exists():
        if time.monotonic()>deadline:raise RuntimeError('Barrier timeout')
        time.sleep(.01)
    try:lock=Lock(root,'supervisor.lock')
    except Busy:event(root,'waiter');return
    with lock:
        event(root,'startup_owner')
        if phase=='crash-before-spawn':os._exit(73)
        if (root/'stop').exists():
            event(root,'STOPPED');return
        try:
            with Lock(root,'core.lock'):pass
        except Busy:
            known=reconcile(root)
            if known and phase=='stop':
                (root/'stop').touch();event(root,'stop_requested')
                time.sleep(.2)
            else:event(root,'adopted' if known else 'RECOVERY_REQUIRED')
            return
        if (root/'intent.json').exists():
            event(root,'RECOVERY_REQUIRED');return
        if phase=='stop':
            (root/'stop').touch();event(root,'stopped');return
        write(root/'intent.json',{'mode':'TEST','operation':uuid.uuid4().hex})
        if phase=='crash-intent':os._exit(74)
        child=spawn(root,'core','delay-metadata' if phase=='crash-after-spawn' else 'normal')
        event(root,'spawned',child=child.pid)
        if phase=='crash-after-spawn':os._exit(75)
        deadline=time.monotonic()+3
        while time.monotonic()<deadline and not read(root/'core.json'):time.sleep(.02)
        event(root,'handshake' if reconcile(root) else 'RECOVERY_REQUIRED')
        if phase=='crash-handshake':os._exit(76)
        # Remain owner throughout contention window; no production daemon.
        time.sleep(1)

def main():
    role,folder,phase=sys.argv[1:]
    root=validate(folder)
    try:
        if role=='core':core(root,phase)
        elif role=='coordinator':coordinator(root,phase)
        elif role=='hold':
            with Lock(root,phase):event(root,'holding');time.sleep(10)
        elif role=='inherit':
            with Lock(root,phase):
                child=spawn(root,'sleep','normal',close_fds=False)
                event(root,'child',child=child.pid)
                time.sleep(.2)
        elif role=='sleep':time.sleep(3)
        else:raise ValueError('Unknown role')
    except Busy:event(root,'busy')
    except Exception as exc:event(root,'FAILED_CLOSED',error=type(exc).__name__,code=getattr(exc,'errno',None))

if __name__=='__main__':main()
