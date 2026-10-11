"""Synthetic-only capture rehearsal. Never accepts external source paths."""
import pathlib,sys,os,json,time,hashlib,subprocess,ctypes as c,ctypes.wintypes as w,traceback,datetime
from journal import Reader,PublisherWatch
ROOT=pathlib.Path(__file__).parent.resolve()
def save(p,data):p.write_text(json.dumps(data,sort_keys=True,indent=2),encoding='utf-8')
def prepare():
 src=ROOT/'sacrificial';src.mkdir()
 with (src/'large.bin').open('xb') as f:
  for _ in range(256):f.write(os.urandom(4*1024*1024))
 for n in range(11):(src/f'small-{n:02}.bin').write_bytes(os.urandom(4096))
 for name in ('dry1','dry2'):(ROOT/name).mkdir()
 save(ROOT/'synthetic-source.json',{'files':12,'large_bytes':1073741824,'generated':datetime.datetime.now(datetime.timezone.utc).isoformat()})
def run(name):
 assert name in ('dry1','dry2');out=ROOT/name;src=ROOT/'sacrificial'
 ident=json.loads((out/'ready.json').read_text());watch=PublisherWatch(ident);reader=Reader(out/'heartbeat.jsonl',ident,liveness=watch.check)
 started=time.monotonic();samples=[];probes=[];bytes_read=0;passes=0;before={};read_lat=[]
 def health():
  if (out/'monitor-failure.json').exists():raise RuntimeError('Monitor failure recorded')
  v=reader.poll();samples.append(dict(v,elapsed=time.monotonic()-started))
 def digest(path,direct=False):
  nonlocal bytes_read
  hsh=hashlib.sha256()
  if not direct:
   with path.open('rb') as f:
    while True:
     health();b=f.read(4*1024*1024)
     if not b:break
     hsh.update(b);bytes_read+=len(b)
  else:
   k=c.WinDLL('kernel32',use_last_error=True)
   k.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,c.c_void_p,w.DWORD,w.DWORD,w.HANDLE];k.CreateFileW.restype=w.HANDLE
   k.VirtualAlloc.argtypes=[c.c_void_p,c.c_size_t,w.DWORD,w.DWORD];k.VirtualAlloc.restype=c.c_void_p
   k.ReadFile.argtypes=[w.HANDLE,c.c_void_p,w.DWORD,c.POINTER(w.DWORD),c.c_void_p];k.ReadFile.restype=w.BOOL
   k.CloseHandle.argtypes=[w.HANDLE];k.VirtualFree.argtypes=[c.c_void_p,c.c_size_t,w.DWORD]
   handle=k.CreateFileW(str(path),0x80000000,1,None,3,0x20000000|0x08000000,None)
   if handle==c.c_void_p(-1).value:raise c.WinError(c.get_last_error())
   buf=k.VirtualAlloc(None,4194304,0x3000,4)
   if not buf:k.CloseHandle(handle);raise c.WinError(c.get_last_error())
   try:
    while True:
     health();got=w.DWORD();t=time.monotonic()
     if not k.ReadFile(handle,buf,4194304,c.byref(got),None):raise c.WinError(c.get_last_error())
     read_lat.append(time.monotonic()-t)
     if not got.value:break
     hsh.update(c.string_at(buf,got.value));bytes_read+=got.value
   finally:k.CloseHandle(handle);k.VirtualFree(buf,0,0x8000)
  return hsh.hexdigest()
 try:
  health()
  paths=sorted(src.iterdir());assert len(paths)==12
  for p in paths:
   s=p.stat();before[p.name]={'size':s.st_size,'mtime_ns':s.st_mtime_ns,'sha256':digest(p,p.name=='large.bin')}
  while time.monotonic()-started<120:
   assert digest(src/'large.bin',True)==before['large.bin']['sha256'];passes+=1
   if len(probes)<20:
    t=time.time_ns();p=subprocess.Popen([str(ROOT/'J6Probe.exe')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);p.wait(timeout=5)
    probes.append({'pid':p.pid,'started_ns':t,'finished_ns':time.time_ns(),'exit':p.returncode});assert p.returncode==0
  for p in paths:
   s=p.stat();assert {'size':s.st_size,'mtime_ns':s.st_mtime_ns,'sha256':digest(p,p.name=='large.bin')}==before[p.name]
  health();save(out/'collector-finished.json',{'status':'HASHING_COMPLETE','utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
  end=time.monotonic()+10
  while not (out/'monitor-result.json').exists():
   if (out/'monitor-failure.json').exists():raise RuntimeError('Monitor final failure')
   if time.monotonic()>end:raise RuntimeError('Monitor final result missing')
   time.sleep(.05)
  final=json.loads((out/'monitor-result.json').read_text());assert final['status']=='PASS' and final['violations']==0 and final['run']==ident['run']
  events=[json.loads(s) for s in (out/'events.jsonl').read_text(encoding='utf-8-sig').splitlines()]
  for p in probes:
   for kind in ('start','stop'):assert sum(e['pid']==p['pid'] and e['kind']==kind and e['name'].lower().startswith('j6probe') for e in events)==1
  assert len({p['pid'] for p in probes})==len(probes),'ambiguous reused probe PID'
  beats=[json.loads(s) for s in (out/'heartbeat.jsonl').read_text(encoding='utf-8-sig').splitlines()]
  intervals=[(b['ticks']-a['ticks'])/ident['frequency'] for a,b in zip(beats,beats[1:])];ordered=sorted(intervals)
  manifest={'synthetic_only':True,'identity':ident,'source':before,'monitor':final,'events_expected':len(probes)*2,'events_captured':len(events),'ten_second_threshold_unchanged':True}
  save(out/'sacrificial-manifest.json',manifest);mh=hashlib.sha256((out/'sacrificial-manifest.json').read_bytes()).hexdigest()
  (out/'sacrificial-manifest.sha256').write_text(mh+'\n')
  result={'status':'PASS','seconds':time.monotonic()-started,'bytes_hashed':bytes_read,'repeated_large_passes':passes,'source_files':12,'source_unchanged':True,'manifest_sha256':mh,'maximum_age':max(v['age'] for v in samples),'interval_min':min(intervals),'interval_median':ordered[len(ordered)//2],'interval_p95':ordered[int((len(ordered)-1)*.95)],'interval_max':max(intervals),'read_errors':0,'write_errors':0,'expected_starts':len(probes),'captured_starts':sum(e['kind']=='start' for e in events),'expected_stops':len(probes),'captured_stops':sum(e['kind']=='stop' for e in events),'maximum_unbuffered_read_seconds':max(read_lat)}
  save(out/'result.json',result);print(json.dumps(result),flush=True)
 except BaseException:
  save(out/'collector-failure.json',{'traceback':traceback.format_exc(),'elapsed':time.monotonic()-started});save(out/'collector-finished.json',{'status':'FAILED'});raise
 finally:
  save(out/'collector-samples.json',samples);save(out/'probes.json',probes);save(out/'unbuffered-read-seconds.json',read_lat);reader.close();watch.close()
if __name__=='__main__':
 if sys.argv[1]=='prepare':prepare()
 else:run(sys.argv[1])
