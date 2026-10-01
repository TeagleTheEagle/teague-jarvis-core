"""Windows TEST pipe transport. No production imports, credentials or endpoints."""
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
import os
import struct
import time

k=c.WinDLL('kernel32',use_last_error=True)
a=c.WinDLL('advapi32',use_last_error=True)
def api(lib,name,args,result=w.BOOL):
    f=getattr(lib,name);f.argtypes=args;f.restype=result;return f
H=w.HANDLE;D=w.DWORD;P=c.c_void_p
api(k,'CloseHandle',[H]);api(k,'LocalFree',[P],P)
api(k,'CreateFileW',[w.LPCWSTR,D,D,P,D,D,H],H)
api(k,'CreateNamedPipeW',[w.LPCWSTR,D,D,D,D,D,D,P],H)
api(k,'ConnectNamedPipe',[H,P]);api(k,'DisconnectNamedPipe',[H])
api(k,'ReadFile',[H,P,D,c.POINTER(D),P]);api(k,'WriteFile',[H,P,D,c.POINTER(D),P])
api(k,'GetOverlappedResult',[H,P,c.POINTER(D),w.BOOL]);api(k,'CancelIoEx',[H,P])
api(k,'CreateEventW',[P,w.BOOL,w.BOOL,w.LPCWSTR],H)
api(k,'WaitForSingleObject',[H,D],D)
api(k,'GetHandleInformation',[H,c.POINTER(D)])
api(k,'GetNamedPipeServerProcessId',[H,c.POINTER(D)])
api(k,'GetNamedPipeClientProcessId',[H,c.POINTER(D)])
api(k,'OpenProcess',[D,w.BOOL,D],H)
api(k,'GetProcessTimes',[H]+[c.POINTER(w.FILETIME)]*4)
api(k,'GetExitCodeProcess',[H,c.POINTER(D)])
api(k,'QueryFullProcessImageNameW',[H,D,w.LPWSTR,c.POINTER(D)])
api(a,'OpenProcessToken',[H,D,c.POINTER(H)])
api(a,'GetTokenInformation',[H,c.c_int,P,D,c.POINTER(D)])
api(a,'ConvertSidToStringSidW',[P,c.POINTER(w.LPWSTR)])
api(a,'ConvertStringSecurityDescriptorToSecurityDescriptorW',[w.LPCWSTR,D,c.POINTER(P),c.POINTER(D)])
api(a,'GetSecurityInfo',[H,c.c_int,D,P,P,P,P,c.POINTER(P)],D)
api(a,'ConvertSecurityDescriptorToStringSecurityDescriptorW',[P,D,D,c.POINTER(w.LPWSTR),c.POINTER(D)])

class SA(c.Structure):_fields_=[('size',D),('descriptor',P),('inherit',w.BOOL)]
class OV(c.Structure):_fields_=[('internal',c.c_size_t),('high',c.c_size_t),('offset',D),('offsetHigh',D),('event',H)]
class Rejected(Exception):pass

def check(ok):
    if not ok:raise OSError(c.get_last_error(),'Windows test pipe operation failed')
    return ok

def identity(pid):
    h=check(k.OpenProcess(0x1000,False,pid))
    try:
        values=[w.FILETIME() for _ in range(4)];exit_=D()
        check(k.GetExitCodeProcess(h,c.byref(exit_)))
        if exit_.value!=259:raise Rejected('PROCESS_DEAD')
        check(k.GetProcessTimes(h,*map(c.byref,values)))
        buf=c.create_unicode_buffer(32768);size=D(len(buf))
        check(k.QueryFullProcessImageNameW(h,0,buf,c.byref(size)))
        with open(buf.value,'rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
        return {'pid':pid,'created':(values[0].dwHighDateTime<<32)|values[0].dwLowDateTime,'exe_digest':digest}
    finally:k.CloseHandle(h)

def current_sid():
    process=check(k.OpenProcess(0x1000,False,os.getpid()));token=H()
    try:
        check(a.OpenProcessToken(process,8,c.byref(token)))
        size=D();a.GetTokenInformation(token,1,None,0,c.byref(size))
        buf=c.create_string_buffer(size.value)
        check(a.GetTokenInformation(token,1,buf,size,c.byref(size)))
        sid=c.cast(buf,c.POINTER(P))[0];text=w.LPWSTR()
        check(a.ConvertSidToStringSidW(sid,c.byref(text)))
        try:return text.value
        finally:k.LocalFree(text)
    finally:
        if token:k.CloseHandle(token)
        k.CloseHandle(process)

def endpoint(name):
    import re
    if not re.fullmatch(r'TEAGUE-TEST-[a-f0-9]{32}',name):raise Rejected('TEST_ENDPOINT_ONLY')
    return '\\\\.\\pipe\\'+name

class Pipe:
    def __init__(self,handle):
        self.h=handle;self.deadline=time.monotonic()+5;flags=D();check(k.GetHandleInformation(handle,c.byref(flags)))
        if flags.value&1:raise Rejected('INHERITED_HANDLE')
    def close(self):
        if self.h is not None:k.CloseHandle(self.h);self.h=None
    def peer(self,server=False):
        pid=D();check((k.GetNamedPipeClientProcessId if server else k.GetNamedPipeServerProcessId)(self.h,c.byref(pid)))
        return identity(pid.value)
    def io(self,operation,buffer=None,size=0,timeout=1200):
        timeout=min(timeout,int(max(0,self.deadline-time.monotonic())*1000))
        if timeout<=0:raise Rejected('DEADLINE')
        ov=OV();ov.event=check(k.CreateEventW(None,True,False,None));count=D()
        try:
            ok=k.ConnectNamedPipe(self.h,c.byref(ov)) if operation=='connect' else getattr(k,operation)(self.h,buffer,size,c.byref(count),c.byref(ov))
            if not ok:
                error=c.get_last_error()
                if operation=='connect' and error==535:return 0
                if error!=997:raise OSError(error,'Pipe disconnected or invalid')
                if k.WaitForSingleObject(ov.event,timeout)!=0:
                    k.CancelIoEx(self.h,c.byref(ov));k.GetOverlappedResult(self.h,c.byref(ov),c.byref(count),True)
                    raise Rejected('IO_TIMEOUT')
                check(k.GetOverlappedResult(self.h,c.byref(ov),c.byref(count),False))
            return count.value
        finally:k.CloseHandle(ov.event)
    def raw(self,data):
        buf=c.create_string_buffer(data)
        if self.io('WriteFile',buf,len(data))!=len(data):raise Rejected('SHORT_WRITE')
    def exact(self,size):
        result=b''
        while len(result)<size:
            buf=c.create_string_buffer(size-len(result));n=self.io('ReadFile',buf,len(buf))
            if not n:raise Rejected('TRUNCATED')
            result+=buf.raw[:n]
        return result
    def send(self,value):
        data=json.dumps(value,separators=(',',':'),sort_keys=True).encode()
        if not 0<len(data)<=8192:raise Rejected('MESSAGE_SIZE')
        self.raw(struct.pack('!I',len(data))+data)
    def receive(self):
        size=struct.unpack('!I',self.exact(4))[0]
        if not 0<size<=8192:raise Rejected('MESSAGE_SIZE')
        try:value=json.loads(self.exact(size).decode('utf8'))
        except (ValueError,UnicodeError):raise Rejected('INVALID_JSON') from None
        if type(value)!=dict:raise Rejected('OBJECT_REQUIRED')
        return value

def listen(name,deny=False):
    sd=P();sddl='D:P(D;;GA;;;'+current_sid()+')' if deny else 'D:P(A;;GA;;;'+current_sid()+')'
    check(a.ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl,1,c.byref(sd),None))
    try:
        sa=SA(c.sizeof(SA),sd,False)
        h=k.CreateNamedPipeW(endpoint(name),3|0x40000000|0x80000,8,1,8192,8192,0,c.byref(sa))
        if h==c.c_void_p(-1).value:raise OSError(c.get_last_error(),'Pipe create rejected')
        return Pipe(h)
    finally:k.LocalFree(sd)

def acl(pipe):
    sd=P();code=a.GetSecurityInfo(pipe.h,6,4,None,None,None,None,c.byref(sd))
    if code:raise OSError(code,'ACL inspection failed')
    text=w.LPWSTR()
    try:
        check(a.ConvertSecurityDescriptorToStringSecurityDescriptorW(sd,1,4,c.byref(text),None))
        return text.value
    finally:
        if text:k.LocalFree(text)
        if sd:k.LocalFree(sd)

def connect(name):
    deadline=time.monotonic()+4
    while True:
        # Identification SQOS: do not grant impersonation privileges to a pipe listener.
        h=k.CreateFileW(endpoint(name),0x80000000|2,0,None,3,0x40000000|0x100000|0x10000,None)
        if h!=c.c_void_p(-1).value:return Pipe(h)
        code=c.get_last_error()
        if code not in (2,231) or time.monotonic()>deadline:raise OSError(code,'Pipe connect rejected')
        time.sleep(.015)
