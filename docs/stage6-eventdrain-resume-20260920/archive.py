import pathlib,hashlib,json,zipfile,os,shutil,sys,datetime
R=pathlib.Path(__file__).resolve().parent
D=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 EVENTDRAIN RESUME 20260920')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 with p.open('xb') as f:f.write(json.dumps(v,sort_keys=True,indent=2).encode());f.flush();os.fsync(f.fileno())
def verify(root):
 m=json.loads((root/'archive-manifest.json').read_text())
 with zipfile.ZipFile(root/'evidence.zip') as z:
  expected={r['path'] for r in m['files']}|{'archive-manifest.json'}
  if len(z.namelist())!=len(expected) or set(z.namelist())!=expected:raise RuntimeError('Archive membership mismatch')
  if z.read('archive-manifest.json')!=(root/'archive-manifest.json').read_bytes():raise RuntimeError('Manifest mismatch')
  for r in m['files']:
   b=z.read(r['path'])
   if len(b)!=r['size'] or hashlib.sha256(b).hexdigest()!=r['sha256']:raise RuntimeError('Member mismatch')
  if z.read('REPORT.md')!=(root/'REPORT.md').read_bytes():raise RuntimeError('Report mismatch')
 return len(expected)
if sys.argv[1]=='seal':
 old=json.loads((R/'preserved-before.json').read_text());changed=[]
 for row in old:
  p=pathlib.Path(row['path']);st=p.stat()
  if sha(p)!=row['sha256'] or st.st_size!=row['size'] or st.st_mtime_ns!=row['mtime_ns']:changed.append(str(p))
 put(R/'preservation-final.json',dict(files=len(old),changed=changed))
 if changed:raise RuntimeError('Prior evidence changed')
 put(R/'source-final.json',[dict(path=str(p),sha256=sha(p)) for p in sorted(R.iterdir()) if p.suffix in ('.py','.ps1','.cs','.exe')])
 files=[]
 def fail(e):raise e
 for base,dirs,names in os.walk(R,onerror=fail,followlinks=False):
  for n in dirs+names:
   p=pathlib.Path(base)/n
   if p.is_symlink() or p.is_junction():raise RuntimeError('Reparse path refused')
  for n in names:
   if n.startswith('.env'):raise RuntimeError('Secret path refused')
   p=pathlib.Path(base)/n;files.append(dict(path=p.relative_to(R).as_posix(),size=p.stat().st_size,sha256=sha(p)))
 files.sort(key=lambda x:x['path']);put(R/'archive-manifest.json',dict(purpose='Diagnosis only; no protected baseline acceptance',files=files))
 with zipfile.ZipFile(R/'evidence.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
  for row in files:z.write(R/row['path'],row['path'])
  z.write(R/'archive-manifest.json','archive-manifest.json')
 with (R/'evidence.zip').open('r+b') as f:os.fsync(f.fileno())
 count=verify(R)
 for row in files:
  if sha(R/row['path'])!=row['sha256']:raise RuntimeError('Source mutated during seal')
 print(json.dumps(dict(members=count,sha256=sha(R/'evidence.zip'))))
elif sys.argv[1]=='transfer':
 count=verify(R)
 if D.exists():raise RuntimeError('Archive destination exists')
 D.mkdir(parents=True,exist_ok=False)
 names=('evidence.zip','archive-manifest.json','REPORT.md','campaign-summary.json','MEASUREMENT-PLAN.md')
 for n in names:
  with (R/n).open('rb') as src,(D/n).open('xb') as dest:shutil.copyfileobj(src,dest);dest.flush();os.fsync(dest.fileno())
  if sha(R/n)!=sha(D/n):raise RuntimeError('Transfer mismatch')
 if verify(D)!=count:raise RuntimeError('Destination mismatch')
 result=dict(status='HASH_VERIFIED',members=count,copiedFilesIncludingReceipt=len(names)+1,archive=str(D),zip_sha256=sha(D/'evidence.zip'),manifest_sha256=sha(D/'archive-manifest.json'),utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 put(R/'archive-verification.json',result);put(D/'archive-verification.json',result)
 if sha(R/'archive-verification.json')!=sha(D/'archive-verification.json'):raise RuntimeError('Receipt mismatch')
 print(json.dumps(result))
else:raise RuntimeError('Unknown mode')
