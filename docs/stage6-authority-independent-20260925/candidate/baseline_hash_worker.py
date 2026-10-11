"""Read-only recursive hashing through verified file handles; no source mutations."""
import pathlib,sys,time,hashlib,traceback,ctypes,ctypes.wintypes as w,msvcrt,os
from workspace import run_dir,activate_temp
from baseline_contract import load,inventory,metadata,approved,save,advance,install_write_guard
from dry_health import Health
K=ctypes.WinDLL('kernel32',use_last_error=True)
K.GetFinalPathNameByHandleW.argtypes=[w.HANDLE,w.LPWSTR,w.DWORD,w.DWORD];K.GetFinalPathNameByHandleW.restype=w.DWORD
def opened_path(f):
 b=ctypes.create_unicode_buffer(32768);n=K.GetFinalPathNameByHandleW(msvcrt.get_osfhandle(f.fileno()),b,len(b),0)
 if not 0<n<len(b):raise ctypes.WinError(ctypes.get_last_error())
 return pathlib.Path(b.value.removeprefix('\\\\?\\'))
def checked_open(p,base,expected):
 # Final handle path is checked BEFORE reading, including a parent-link substitution.
 f=p.open('rb',buffering=0)
 try:
  final=opened_path(f);s=os.fstat(f.fileno())
  if final!=p or not final.is_relative_to(base) or s.st_ino!=expected['fileId'] or s.st_dev!=expected['volume'] or s.st_nlink!=1:raise ValueError('Opened handle path/identity escape')
  if metadata(p)!={k:expected[k] for k in metadata(p)}:raise ValueError('Source changed before read')
  return f
 except BaseException:f.close();raise
def snapshot(root,v,health,number,deadline):
 base=approved(v['source']);result={};durations={};begin=time.perf_counter_ns()
 if inventory(base)!=v['inventory']:raise RuntimeError('Pre-hash inventory changed')
 def check():
  health.check()
  if time.monotonic()>=deadline:raise TimeoutError('Finite baseline worker deadline')
  if (root/'workload-stop').exists():raise RuntimeError('Workload cancellation')
 for name,meta in v['inventory'].items():
  p=base/name;h=hashlib.sha256();count=0;start=time.perf_counter_ns();check()
  with checked_open(p,base,meta) as f:
   while True:
    check();b=f.read(4*2**20)
    if not b:break
    h.update(b);count+=len(b)
   handleAfter=os.fstat(f.fileno())
  if count!=meta['bytes'] or handleAfter.st_mtime_ns!=meta['mtime_ns'] or handleAfter.st_size!=meta['bytes'] or dict(metadata(p),fullPath=str(p),relativePath=name)!=meta:raise RuntimeError('Source mutation while hashing')
  result[name]=dict(meta,sha256=h.hexdigest());durations[name]=(time.perf_counter_ns()-start)/1e9
 if inventory(base)!=v['inventory']:raise RuntimeError('Post-pass inventory changed')
 save(root/('hash-pass-'+str(number)+'.json'),dict(beginQpcNs=begin,endQpcNs=time.perf_counter_ns(),files=result,perFileSeconds=durations));return result
def main(root):
 v=load(root);health=Health(root);started=time.monotonic();deadline=started+v['thresholds']['campaign'];install_write_guard(root)
 try:
  one=snapshot(root,v,health,1,deadline);advance(root,'WORKLOAD_RUNNING','HASH1_COMPLETE','hash-pass-1.json')
  two=snapshot(root,v,health,2,deadline)
  if one!=two:raise RuntimeError('Independent hashes differ')
  advance(root,'HASH1_COMPLETE','HASH2_COMPLETE','hash-pass-2.json')
  # Explicit synthetic long-observation phase, independently reported; never counted as hash throughput.
  while time.monotonic()-started<v['thresholds']['hold']:
   health.check()
   if (root/'workload-stop').exists() or time.monotonic()>=deadline:raise RuntimeError('Long observation cancelled/expired')
   time.sleep(.2)
  if inventory(pathlib.Path(v['source']))!=v['inventory']:raise RuntimeError('Final source metadata drift')
  save(root/'metadata-verified.json',dict(status='PASS',files=len(two),bytes=sum(x['bytes'] for x in two.values()),elapsedSeconds=time.monotonic()-started,longObservationTarget=v['thresholds']['hold']))
  advance(root,'HASH2_COMPLETE','METADATA_VERIFIED','metadata-verified.json')
 except BaseException:save(root/'hash-failure.json',dict(error=traceback.format_exc()));raise
 finally:health.close();save(root/'hash-health-samples.json',health.samples)
if __name__=='__main__':
 root=run_dir(sys.argv[1]);activate_temp(root);main(root)
