import pathlib,json,zipfile,hashlib,os,shutil,datetime
r=pathlib.Path(__file__).parent
dest=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 CLEANUP INTEGRATION REVIEW 20260920')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,sort_keys=True,indent=2);f.flush();os.fsync(f.fileno())
files=[]
for p in sorted(r.iterdir()):
 if not p.is_file() or p.is_symlink() or p.name.startswith('.env'):raise RuntimeError('Unexpected review artifact')
 files.append(dict(name=p.name,size=p.stat().st_size,sha256=sha(p)))
put(r/'archive-manifest.json',dict(status='BLOCKED',files=files))
with zipfile.ZipFile(r/'evidence.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
 for x in files:z.write(r/x['name'],x['name'])
 z.write(r/'archive-manifest.json','archive-manifest.json')
def verify(base):
 with zipfile.ZipFile(base/'evidence.zip') as z:
  assert set(z.namelist())=={x['name'] for x in files}|{'archive-manifest.json'}
  assert len(z.namelist())==len(files)+1
  assert z.read('archive-manifest.json')==(base/'archive-manifest.json').read_bytes()
  for x in files:
   b=z.read(x['name']);assert len(b)==x['size'] and hashlib.sha256(b).hexdigest()==x['sha256']
verify(r)
assert not dest.exists();dest.mkdir(parents=True)
for n in ('evidence.zip','archive-manifest.json','REPORT.md','disposition.json','97-identity-preflight.json','source-prechange-hashes.json'):
 with (r/n).open('rb') as a,(dest/n).open('xb') as b:shutil.copyfileobj(a,b);b.flush();os.fsync(b.fileno())
 assert sha(r/n)==sha(dest/n)
verify(dest)
for x in files:assert sha(r/x['name'])==x['sha256']
for x in json.loads((r/'source-prechange-hashes.json').read_text()):assert sha(pathlib.Path(x['path']))==x['sha256']
old=json.loads((r/'prior-archive-verification.json').read_text())
assert sha(r.parent/'stage6-kernel-child-trace-20260920/evidence.zip')==old['sha256']
v=dict(status='HASH_VERIFIED',reviewStatus='BLOCKED',members=len(files)+1,path=str(dest),zipSHA256=sha(dest/'evidence.zip'),manifestSHA256=sha(dest/'archive-manifest.json'),prior1436MemberArchiveUnchanged=True,sourceHashesUnchanged=61,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
put(r/'archive-verification.json',v);put(dest/'archive-verification.json',v)
assert sha(r/'archive-verification.json')==sha(dest/'archive-verification.json')
print(json.dumps(v))
