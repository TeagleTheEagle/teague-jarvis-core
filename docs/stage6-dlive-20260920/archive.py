"""Seal failed evidence only after all collection has ended; never grants acceptance."""
import pathlib,json,hashlib,os,zipfile,shutil,sys,datetime
R=pathlib.Path(__file__).resolve().parent;plan=json.loads((R/'workspace-plan.json').read_text());CODE=pathlib.Path(plan['live_code']);DEST=pathlib.Path(plan['archive'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sync(p):
 with p.open('r+b',buffering=0) as f:os.fsync(f.fileno())
def put(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,sort_keys=True,indent=2);f.flush();os.fsync(f.fileno())
def verify(root):
 m=json.loads((root/'archive-manifest.json').read_text())
 with zipfile.ZipFile(root/'evidence.zip') as z:
  expected={r['name'] for r in m['files']}|{'archive-manifest.json'}
  if len(z.namelist())!=len(expected) or set(z.namelist())!=expected:raise RuntimeError('Membership mismatch')
  if z.read('archive-manifest.json')!=(root/'archive-manifest.json').read_bytes():raise RuntimeError('Manifest mismatch')
  for row in m['files']:
   data=z.read(row['name'])
   if len(data)!=row['size'] or hashlib.sha256(data).hexdigest()!=row['sha256']:raise RuntimeError('Member hash mismatch')
 return len(expected)
if sys.argv[1]=='seal':
 final=json.loads((R/'final-host-state.json').read_text(encoding='utf-8-sig'))
 if any(final[k] for k in ('virtualbox','probes','workspaceProcesses')):raise RuntimeError('Process snapshot not clear')
 identity=json.loads((R/'identity-reconciliation.json').read_text())
 if identity['unresolved'] or identity['sourceDrift']:raise RuntimeError('Identity/source uncertainty')
 files=[]
 def fail(e):raise e
 for prefix,base in (('report',R),('live',CODE)):
  for directory,dirs,names in os.walk(base,followlinks=False,onerror=fail):
   for n in dirs+names:
    p=pathlib.Path(directory)/n
    if p.is_symlink() or p.is_junction():raise RuntimeError('Reparse artifact refused')
   for n in names:
    if n.startswith('.env'):raise RuntimeError('Secret environment file refused')
    p=pathlib.Path(directory)/n;sync(p);files.append(dict(name=prefix+'/'+p.relative_to(base).as_posix(),source=str(p),size=p.stat().st_size,sha256=sha(p)))
 files.sort(key=lambda v:v['name']);put(R/'archive-manifest.json',dict(status='MONITOR_STILL_DEFECTIVE',purpose='Failed acceptance evidence preservation; not monitor acceptance',files=files))
 with zipfile.ZipFile(R/'evidence.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
  for row in files:z.write(row['source'],row['name'])
  z.write(R/'archive-manifest.json','archive-manifest.json')
 sync(R/'evidence.zip');count=verify(R)
 for row in files:
  if sha(pathlib.Path(row['source']))!=row['sha256']:raise RuntimeError('Evidence changed during seal')
 print(json.dumps(dict(members=count,sha256=sha(R/'evidence.zip'))))
elif sys.argv[1]=='transfer':
 count=verify(R)
 if DEST.exists():raise RuntimeError('No overwrite')
 DEST.mkdir(parents=True,exist_ok=False)
 names=('evidence.zip','archive-manifest.json','REPORT.md','campaign-summary.json','live-path-inventory-final.json')
 for n in names:
  with (R/n).open('rb') as a,(DEST/n).open('xb') as b:shutil.copyfileobj(a,b);b.flush();os.fsync(b.fileno())
  if sha(R/n)!=sha(DEST/n):raise RuntimeError('Transfer mismatch')
 if verify(DEST)!=count:raise RuntimeError('Destination member mismatch')
 receipt=dict(status='HASH_VERIFIED',acceptance='MONITOR_STILL_DEFECTIVE',archive=str(DEST),members=count,zip_sha256=sha(DEST/'evidence.zip'),manifest_sha256=sha(DEST/'archive-manifest.json'),utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 put(R/'archive-verification.json',receipt);put(DEST/'archive-verification.json',receipt)
 if sha(R/'archive-verification.json')!=sha(DEST/'archive-verification.json'):raise RuntimeError('Receipt mismatch')
 print(json.dumps(receipt))
else:raise RuntimeError('Unknown mode')
