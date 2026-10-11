import ctypes as c,ctypes.wintypes as w,os,sys,json,time,pathlib,datetime as dt
from journal import append,ticks,frequency,Reader
r=pathlib.Path(sys.argv[1]);mode=sys.argv[2]
if r.parent!=pathlib.Path(__file__).parent or not r.name.startswith('process-'):raise RuntimeError('Synthetic fixture only')
if mode=='publisher':
 k=c.WinDLL('kernel32');k.GetCurrentProcess.restype=w.HANDLE;k.GetProcessTimes.argtypes=[w.HANDLE]+[c.POINTER(w.FILETIME)]*4
 values=[w.FILETIME() for _ in range(4)];assert k.GetProcessTimes(k.GetCurrentProcess(),*[c.byref(v) for v in values])
 ident={'run':r.name,'pid':os.getpid(),'created':str((values[0].dwHighDateTime<<32)|values[0].dwLowDateTime),'frequency':frequency()}
 with (r/'journal').open('ab',buffering=0) as f:
  seq=0
  while not (r/'stop').exists():
   if (r/'pause').exists():time.sleep(.02);continue
   seq+=1;append(f,dict(ident,seq=seq,pump=seq,ticks=ticks(),utc=dt.datetime.now(dt.timezone.utc).isoformat(),state='ACTIVE',violations=0))
   if seq==1:(r/'ready.json').write_text(json.dumps(ident))
   time.sleep(.05)
elif mode=='reader':
 ident=json.loads((r/'ready.json').read_text());reader=Reader(r/'journal',ident)
 try:
  while not (r/'stop').exists():
   value=reader.poll()
   if not (r/'reader-ready').exists():(r/'reader-ready').write_text(str(value['sequence']))
   time.sleep(.02)
 finally:reader.close()
elif mode=='hasher':
 import hashlib
 (r/'hasher-ready').write_text(str(os.getpid()))
 while not (r/'stop').exists():hashlib.sha256(b'x'*1048576).digest()
 # No success manifest written by this deliberately crash-only fixture.
else:raise RuntimeError('Unknown mode')
