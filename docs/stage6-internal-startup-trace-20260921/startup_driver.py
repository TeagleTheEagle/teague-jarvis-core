import pathlib,sys,os,time,json,hashlib,threading,subprocess,traceback,ctypes
from workspace import CODE,run_dir,activate_temp
from evidence_support import TreeTracker,put
from journal import ticks,frequency
root=run_dir(sys.argv[1]);activate_temp(root);os.chdir(CODE)
cfg=json.loads((CODE/'startup-config.json').read_text());cp=pathlib.Path(cfg['cPayload']);dp=root/'D-load.bin'
put(root/'driver-identity.json',dict(pid=os.getpid(),image=sys.executable,admin=bool(ctypes.windll.shell32.IsUserAnAdmin()),qpc=ticks(),frequency=frequency()))
assert not ctypes.windll.shell32.IsUserAnAdmin(),'Diagnostic driver must not be elevated'
block=b'SACRIFICIAL-STARTUP-TRACE\0'*4096
for p in (cp,dp):
 with p.open('xb') as f:
  for i in range(640):f.write(block)
snap={str(p):dict(bytes=p.stat().st_size,mtime=p.stat().st_mtime_ns,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in (cp,dp)}
tree=TreeTracker();results=[];loads=[];stop=threading.Event();worker=None;failure=None;condition='preflight'
def load(path,hashing):
 begin=ticks();total=0;passes=0;error=None
 try:
  while not stop.is_set():
   h=hashlib.sha256()
   with path.open('rb',buffering=0) as f:
    while not stop.is_set():
     b=f.read(4*2**20)
     if not b:break
     if hashing:h.update(b)
     total+=len(b)
   passes+=1
 except BaseException:error=traceback.format_exc()
 loads.append(dict(condition=condition,beginQpc=begin,endQpc=ticks(),bytes=total,passes=passes,error=error))
try:
 index=0
 for condition in ('idle','C-read','C-hash','D-hash'):
  stop.clear();worker=None
  if condition!='idle':
   worker=threading.Thread(target=load,args=(dp if condition=='D-hash' else cp,condition!='C-read'));worker.start()
  for pair in range(10):
   # Alternate order to reduce monotonic cache/order bias.
   for mode in (('minimal','entry') if pair%2==0 else ('entry','minimal')):
    args=[str(CODE/'J6EntryObserve.exe'),str(root),mode,str(index)]
    p=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=0x08000000)
    tree.register(p,'entry-observer',args)
    try:rc=p.wait(timeout=50)
    except subprocess.TimeoutExpired:raise RuntimeError('Diagnostic controller did not finish; preserve and stop')
    finally:
     if p.poll() is not None:p._handle.Close()
    row=json.loads((root/('probe-'+str(index)+'.json')).read_text());row.update(index=index,condition=condition,controllerExit=rc);results.append(row);index+=1
    if rc or row.get('deadlineExceeded') or row.get('fault'):raise RuntimeError('Probe/instrumentation failure preserved; no retry')
    time.sleep(.15)
  stop.set()
  if worker:worker.join(5);assert not worker.is_alive(),'Load cleanup failed'
  print(condition+' 20 probes completed',flush=True)
except BaseException:failure=traceback.format_exc()
finally:
 stop.set()
 if worker:worker.join(5)
 tr=tree.finish(root,20)
 preserved=all(p.stat().st_size==snap[str(p)]['bytes'] and p.stat().st_mtime_ns==snap[str(p)]['mtime'] and hashlib.sha256(p.read_bytes()).hexdigest()==snap[str(p)]['sha256'] for p in (cp,dp))
 if not tr['allExited'] or not tr['allHandlesClosed'] or not tr['threadStopped'] or not preserved:failure=failure or 'Cleanup/preservation failed'
 put(root/'probes.json',results);put(root/'load.json',loads);put(root/'sacrificial-sources.json',snap)
 put(root/'result.json',dict(status='FAILED_STOPPED' if failure else 'DIAGNOSTIC_COMPLETE',failure=failure,count=len(results),sourcesUnchanged=preserved,protectedAccess=False,productionChanged=False))
 print(json.dumps(dict(count=len(results),failure=failure)),flush=True)
sys.exit(bool(failure))
