"""Archive finalized diagnostic evidence only; never changes source/history."""
import pathlib,json,hashlib,os,zipfile,shutil,sys,datetime
R=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
plan=read(R/'plan.json');CODE=pathlib.Path(plan['live_code']);DEST=pathlib.Path(plan['archive'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,sort_keys=True,indent=2);f.flush();os.fsync(f.fileno())
def verify(root):
 m=read(root/'archive-manifest.json')
 with zipfile.ZipFile(root/'evidence.zip') as z:
  names={x['name'] for x in m['files']}|{'archive-manifest.json'}
  if len(z.namelist())!=len(names) or set(z.namelist())!=names:raise RuntimeError('Member mismatch')
  if z.read('archive-manifest.json')!=(root/'archive-manifest.json').read_bytes():raise RuntimeError('Manifest mismatch')
  for row in m['files']:
   data=z.read(row['name'])
   if len(data)!=row['size'] or hashlib.sha256(data).hexdigest()!=row['sha256']:raise RuntimeError('Member hash mismatch')
 return len(names)
if sys.argv[1]=='seal':
 host=read(R/'final-host-state.json');ident=read(R/'identity-reconciliation.json')
 if any(host[k] for k in ('virtualbox','probes','workspaceProcesses')) or ident['unresolved'] or ident['sourceDrift']:raise RuntimeError('Final process/source state uncertain')
 files=[]
 for prefix,base in (('report',R),('live',CODE)):
  for directory,dirs,names in os.walk(base,followlinks=False):
   for n in dirs+names:
    p=pathlib.Path(directory)/n
    if p.is_symlink() or p.is_junction():raise RuntimeError('Reparse artifact refused')
   for n in names:
    p=pathlib.Path(directory)/n
    if n.startswith('.env'):raise RuntimeError('Environment file refused')
    files.append(dict(name=prefix+'/'+p.relative_to(base).as_posix(),source=str(p),size=p.stat().st_size,sha256=sha(p)))
 files.sort(key=lambda x:x['name'])
 put(R/'archive-manifest.json',dict(status=read(R/'disposition.json')['status'],acceptance=False,files=files))
 with zipfile.ZipFile(R/'evidence.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
  for row in files:z.write(row['source'],row['name'])
  z.write(R/'archive-manifest.json','archive-manifest.json')
 with (R/'evidence.zip').open('r+b',buffering=0) as f:os.fsync(f.fileno())
 count=verify(R)
 for row in files:
  if sha(pathlib.Path(row['source']))!=row['sha256']:raise RuntimeError('Source changed during archive')
 print(json.dumps(dict(members=count,sha256=sha(R/'evidence.zip'))))
elif sys.argv[1]=='transfer':
 count=verify(R)
 if DEST.exists():raise RuntimeError('Destination exists: refuse overwrite')
 DEST.mkdir(parents=True,exist_ok=False)
 for n in ('evidence.zip','archive-manifest.json','REPORT.md','diagnostic-summary.json','timeout-timelines.json'):
  with (R/n).open('rb') as a,(DEST/n).open('xb') as b:shutil.copyfileobj(a,b);b.flush();os.fsync(b.fileno())
  if sha(R/n)!=sha(DEST/n):raise RuntimeError('Transfer mismatch')
 if verify(DEST)!=count:raise RuntimeError('Archive mismatch')
 receipt=dict(status='HASH_VERIFIED',diagnosticStatus=read(R/'disposition.json')['status'],acceptance=False,path=str(DEST),members=count,zipSHA256=sha(DEST/'evidence.zip'),manifestSHA256=sha(DEST/'archive-manifest.json'),utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 put(R/'archive-verification.json',receipt);put(DEST/'archive-verification.json',receipt)
 if sha(R/'archive-verification.json')!=sha(DEST/'archive-verification.json'):raise RuntimeError('Receipt mismatch')
 print(json.dumps(receipt))
else:raise RuntimeError('Unknown archive operation')
