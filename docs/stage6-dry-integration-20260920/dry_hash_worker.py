"""Two hash passes only. Manifest/acceptance occurs after independent closure."""
import sys,pathlib,hashlib,time,traceback
from workspace import run_dir,activate_temp
from dry_contract import load,inventory,save,advance
from dry_health import Health
def snapshot(root,contract,health,number):
 source=pathlib.Path(contract['source']);result={};begin=time.perf_counter_ns()
 if inventory(source)!=contract['inventory']:raise RuntimeError('Pre-hash metadata changed')
 for name,meta in contract['inventory'].items():
  if (root/'workload-stop').exists():raise RuntimeError('Workload cancellation')
  p=source/name;h=hashlib.sha256();health.check()
  with p.open('rb') as f:
   while b:=f.read(4194304):
    if (root/'workload-stop').exists():raise RuntimeError('Workload cancellation')
    health.check();h.update(b)
  if dict(bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns)!=meta:raise RuntimeError('Source metadata changed while hashing')
  result[name]=dict(meta,sha256=h.hexdigest())
 save(root/('hash-pass-'+str(number)+'.json'),dict(beginQpcNs=begin,endQpcNs=time.perf_counter_ns(),files=result));return result
def main(root):
 contract=load(root);health=Health(root)
 try:
  first=snapshot(root,contract,health,1);advance(root,'WORKLOAD_RUNNING','HASH1_COMPLETE','hash-pass-1.json')
  second=snapshot(root,contract,health,2)
  if first!=second:raise RuntimeError('Independent hash passes differ')
  advance(root,'HASH1_COMPLETE','HASH2_COMPLETE','hash-pass-2.json')
  if inventory(pathlib.Path(contract['source']))!=contract['inventory']:raise RuntimeError('Post-hash metadata changed')
  save(root/'metadata-verified.json',dict(status='PASS',files=len(second),bytes=sum(x['bytes'] for x in second.values())))
  advance(root,'HASH2_COMPLETE','METADATA_VERIFIED','metadata-verified.json')
 except BaseException:save(root/'hash-failure.json',dict(error=traceback.format_exc()));raise
 finally:health.close();save(root/'hash-health-samples.json',health.samples)
if __name__=='__main__':
 root=run_dir(sys.argv[1]);activate_temp(root);main(root)
