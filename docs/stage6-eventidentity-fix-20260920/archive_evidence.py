import pathlib,json,hashlib,zipfile,os,sys,shutil,datetime
R=pathlib.Path(__file__).resolve().parent
D=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 EVENTIDENTIFIER FIX 20260920')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 with p.open('xb') as f:f.write(json.dumps(v,indent=2,sort_keys=True).encode());f.flush();os.fsync(f.fileno())
def verify(root):
 m=json.loads((root/'archive-manifest.json').read_text())
 with zipfile.ZipFile(root/'evidence.zip') as z:
  expected={r['path'] for r in m['files']}|{'archive-manifest.json'}
  if len(z.namelist())!=len(expected) or set(z.namelist())!=expected:raise RuntimeError('Archive member set mismatch')
  if z.read('archive-manifest.json')!=(root/'archive-manifest.json').read_bytes():raise RuntimeError('Manifest mismatch')
  for r in m['files']:
   b=z.read(r['path'])
   if len(b)!=r['bytes'] or hashlib.sha256(b).hexdigest()!=r['sha256']:raise RuntimeError('Archive member hash mismatch')
  if z.read('REPORT.md')!=(root/'REPORT.md').read_bytes():raise RuntimeError('Report mismatch')
 return len(expected)
if sys.argv[1]=='seal':
 files=[]
 def fail(e):raise e
 for base,dirs,names in os.walk(R,onerror=fail,followlinks=False):
  for n in dirs+names:
   p=pathlib.Path(base)/n
   if p.is_symlink() or p.is_junction():raise RuntimeError('Unexpected reparse path')
  for n in names:
   if n.startswith('.env'):raise RuntimeError('Secret path refused')
   p=pathlib.Path(base)/n;files.append(dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
 files.sort(key=lambda r:r['path']);put(R/'archive-manifest.json',dict(purpose='Sacrificial collision correction and validation; no protected baseline',files=files))
 with zipfile.ZipFile(R/'evidence.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
  for r in files:z.write(R/r['path'],r['path'])
  z.write(R/'archive-manifest.json','archive-manifest.json')
 with (R/'evidence.zip').open('r+b') as f:os.fsync(f.fileno())
 count=verify(R)
 for r in files:
  if sha(R/r['path'])!=r['sha256']:raise RuntimeError('Source changed while sealing')
 print(json.dumps(dict(members=count,sha256=sha(R/'evidence.zip'))))
elif sys.argv[1]=='transfer':
 count=verify(R)
 if D.exists():raise RuntimeError('Never overwrite existing evidence destination')
 D.mkdir(parents=True,exist_ok=False)
 names=('evidence.zip','archive-manifest.json','REPORT.md','summary.json','source-final.json')
 for n in names:
  with (R/n).open('rb') as src,(D/n).open('xb') as dst:shutil.copyfileobj(src,dst);dst.flush();os.fsync(dst.fileno())
  if sha(R/n)!=sha(D/n):raise RuntimeError('Transfer hash mismatch')
 if verify(D)!=count:raise RuntimeError('Destination mismatch')
 result=dict(status='HASH_VERIFIED',archive=str(D),zip_members=count,copied_files_including_receipt=len(names)+1,zip_sha256=sha(D/'evidence.zip'),manifest_sha256=sha(D/'archive-manifest.json'),utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 put(R/'archive-verification.json',result);put(D/'archive-verification.json',result)
 if sha(R/'archive-verification.json')!=sha(D/'archive-verification.json'):raise RuntimeError('Receipt mismatch')
 print(json.dumps(result))
else:raise RuntimeError('Unknown action')
