"""Known synthetic helper. Delays/output are explicit test injection, never acceptance probes."""
import time
entry=time.perf_counter_ns()
import os,sys,pathlib,json,subprocess,ctypes as c,ctypes.wintypes as w
root=pathlib.Path(sys.argv[1]);mode=sys.argv[2]
if root.drive.upper()!='D:' or 'JARVIS-STAGE6-LIVE' not in root.parts:raise RuntimeError('Sacrificial D scope required')
f=(root/('internal-'+str(os.getpid())+'.jsonl')).open('x',encoding='utf-8')
def mark(stage,**kw):f.write(json.dumps(dict(stage=stage,monotonicNs=time.perf_counter_ns(),pid=os.getpid(),parentPid=os.getppid(),**kw))+'\n');f.flush()
mark('entry',observedEntryNs=entry,initializationBeginNs=entry);mark('initialization.end')
mark('work.begin')
if mode in ('output','late','nonzero'):
 for _ in range(256):os.write(1,b'O'*8192);os.write(2,b'E'*8192)
 mark('output.completed')
 if mode=='late':time.sleep(15.5) # Deliberately beyond fixed deadlines; focused fixture only.
elif mode=='leaf':time.sleep(float(sys.argv[3]))
elif mode in ('child-first','parent-first','orphan'):
 delay='0.2' if mode=='child-first' else '1.5'
 mark('child.launch.begin')
 p=subprocess.Popen([sys._base_executable,'-B',__file__,str(root),'leaf',delay],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,close_fds=True,creationflags=0x08000000)
 mark('child.launch.end',childPid=p.pid)
 # Allow actual child startup to be observable; bounded readiness of test fixture only.
 end=time.monotonic()+5
 while not (root/('internal-'+str(p.pid)+'.jsonl')).exists():
  if time.monotonic()>end:raise RuntimeError('Fixture child entry missing')
  time.sleep(.01)
 if mode=='child-first':mark('child.wait.begin');p.wait(timeout=5);mark('child.wait.end')
 else:time.sleep(.1)
elif mode=='trace':
 mark('identity.begin');k=c.WinDLL('kernel32');a=c.WinDLL('advapi32');k.GetCurrentProcess.restype=w.HANDLE;a.OpenProcessToken.argtypes=[w.HANDLE,w.DWORD,c.POINTER(w.HANDLE)];k.CloseHandle.argtypes=[w.HANDLE]
 token=w.HANDLE()
 if not a.OpenProcessToken(k.GetCurrentProcess(),8,c.byref(token)):raise c.WinError()
 k.CloseHandle(token);mark('identity.end')
 mark('filesystem.begin');p=root/('synthetic-'+str(os.getpid())+'.bin')
 with p.open('xb') as b:b.write(b'synthetic-only')
 with p.open('rb') as b:assert b.read()==b'synthetic-only'
 mark('filesystem.end')
else:raise RuntimeError('Unknown fixture mode')
mark('work.end');mark('cleanup.begin');mark('stdout.close.begin');os.close(1);mark('stdout.close.end');mark('stderr.close.begin');os.close(2);mark('stderr.close.end');mark('cleanup.end');mark('return-main');f.close()
sys.exit(7 if mode=='nonzero' else 0)
