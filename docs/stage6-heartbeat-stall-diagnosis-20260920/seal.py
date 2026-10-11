import pathlib,json,hashlib,os,zipfile,shutil,sys,datetime
R=pathlib.Path(__file__).resolve().parent
D=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 HEARTBEAT STALL DIAGNOSIS 20260920')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 with p.open('xb') as f:f.write(json.dumps(v,indent=2,sort_keys=True).encode());f.flush();os.fsync(f.fileno())
def verify(root):
 m=json.loads((root/'archive-manifest.json').read_text())
 with zipfile.ZipFile(root/'evidence.zip') as z:
  expected={r['path'] for r in m['files']}|{'archive-manifest.json'}
  if len(z.namelist())!=len(expected) or set(z.namelist())!=expected:raise RuntimeError('Archive set mismatch')
  if z.read('archive-manifest.json')!=(root/'archive-manifest.json').read_bytes():raise RuntimeError('Manifest mismatch')
  for row in m['files']:
   data=z.read(row['path'])
   if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:raise RuntimeError('Archive hash mismatch')
  if z.read('REPORT.md')!=(root/'REPORT.md').read_bytes():raise RuntimeError('Report mismatch')
 return len(expected)
if sys.argv[1]=='seal':
 before=json.loads((R/'preserved-before.json').read_text());changed=[]
 for e in before:
  p=pathlib.Path(e['path']);st=p.stat()
  if sha(p)!=e['sha256'] or st.st_mtime_ns!=e['mtime_ns'] or st.st_size!=e['bytes']:changed.append(str(p))
 put(R/'preservation-final.json',dict(files=len(before),changed=changed,status='PASS' if not changed else 'FAIL',protectedAccess=False))
 if changed:raise RuntimeError('Prior evidence changed')
 put(R/'source-final.json',[dict(path=str(p),sha256=sha(p)) for p in sorted(R.iterdir()) if p.suffix in ('.py','.ps1','.cs','.exe')])
 files=[]
 for p in sorted(R.rglob('*')):
  if p.is_symlink() or p.is_junction():raise RuntimeError('Unexpected link')
  if p.is_file():
   if p.name.startswith('.env'):raise RuntimeError('Secret path refused')
   files.append(dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
 put(R/'archive-manifest.json',dict(status='BLOCKED',files=files))
 with zipfile.ZipFile(R/'evidence.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
  for e in files:z.write(R/e['path'],e['path'])
  z.write(R/'archive-manifest.json','archive-manifest.json')
 with (R/'evidence.zip').open('r+b') as f:os.fsync(f.fileno())
 count=verify(R)
 for e in files:
  if sha(R/e['path'])!=e['sha256']:raise RuntimeError('Source changed during seal')
 print(json.dumps(dict(members=count,sha256=sha(R/'evidence.zip'),preserved=len(before))))
elif sys.argv[1]=='transfer':
 count=verify(R)
 if D.exists():raise RuntimeError('Refuse archive overwrite')
 D.mkdir(parents=True,exist_ok=False)
 for n in ('evidence.zip','archive-manifest.json','REPORT.md','CURRENT-SOURCE-AUDIT.md','REVALIDATION-PLAN.md'):
  with (R/n).open('rb') as a,(D/n).open('xb') as b:shutil.copyfileobj(a,b);b.flush();os.fsync(b.fileno())
  if sha(R/n)!=sha(D/n):raise RuntimeError('Transfer mismatch')
 if verify(D)!=count:raise RuntimeError('Destination mismatch')
 v=dict(status='HASH_VERIFIED',diagnosticStatus='BLOCKED',zipMembers=count,copiedFilesIncludingReceipt=6,archive=str(D),zip_sha256=sha(D/'evidence.zip'),manifest_sha256=sha(D/'archive-manifest.json'),utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 put(R/'archive-verification.json',v);put(D/'archive-verification.json',v)
 if sha(R/'archive-verification.json')!=sha(D/'archive-verification.json'):raise RuntimeError('Receipt mismatch')
 print(json.dumps(v))
else:raise RuntimeError('Unknown action')
