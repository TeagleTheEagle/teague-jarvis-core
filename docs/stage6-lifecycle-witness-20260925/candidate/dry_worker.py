"""Hash twelve preexisting sacrificial artifacts only; no VM paths."""
import pathlib,json,hashlib,sys,os,time
from workspace import run_dir,activate_temp
root=run_dir(sys.argv[1]);activate_temp(root)
source=pathlib.Path(r'C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-heartbeat-journal-20260918\sacrificial')
def snapshot():
 files=sorted(source.iterdir())
 if len(files)!=12 or any(not p.is_file() or p.suffix!='.bin' or p.is_symlink() or p.is_junction() for p in files):raise RuntimeError('Exact sacrificial 12-file input required')
 result={}
 for p in files:
  if (root/'workload-stop').exists():raise RuntimeError('Dry run cancelled')
  before=p.stat();h=hashlib.sha256()
  with p.open('rb') as f:
   while b:=f.read(4194304):
    if (root/'workload-stop').exists():raise RuntimeError('Dry run cancelled')
    h.update(b)
  after=p.stat()
  if before.st_size!=after.st_size or before.st_mtime_ns!=after.st_mtime_ns:raise RuntimeError('Sacrificial input changed')
  result[p.name]=dict(size=after.st_size,mtime_ns=after.st_mtime_ns,sha256=h.hexdigest())
 return result
def save(n,x):
 with (root/n).open('x') as f:json.dump(x,f,sort_keys=True,indent=2)
before=snapshot();save('source-before.json',before);after=snapshot();save('source-after.json',after)
if before!=after:raise RuntimeError('Sacrificial before/after mismatch')
save('baseline-manifest.json',dict(synthetic=True,source=str(source),files=before,protectedAccess=False))
save('baseline-manifest-hash.json',dict(sha256=hashlib.sha256((root/'baseline-manifest.json').read_bytes()).hexdigest()))
