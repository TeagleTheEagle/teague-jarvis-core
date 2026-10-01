import pathlib,json,hashlib,zipfile,shutil,datetime
R=pathlib.Path(__file__).parent;prior=R.parent/'stage6-dry-integration-20260920';repo=R.parent.parent
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\b675935592fe41d48968e22be8cc6641\code')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,x):
 with (R/n).open('x') as f:json.dump(x,f,indent=2)
sources=json.loads((prior/'final-source.json').read_text());checked=[]
for x in sources:
 actual=sha(pathlib.Path(x['path']));checked.append(dict(path=x['path'],name=x['name'],expected=x['sha256'],actual=actual,unchanged=actual==x['sha256']))
assert all(x['unchanged'] for x in checked)
assert json.loads((C/'integration-source.json').read_text())==json.loads((prior/'candidate-source.json').read_text())
receipt=json.loads((prior/'archive-verification.json').read_text());A=pathlib.Path(receipt['path']);manifest=json.loads((A/'archive-manifest.json').read_text())
assert sha(A/'evidence.zip')==receipt['zipSHA256'] and sha(A/'archive-manifest.json')==receipt['manifestSHA256']
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==1886
 for x in manifest['files']:assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256']
 assert z.read('archive-manifest.json')==(A/'archive-manifest.json').read_bytes()
app=[]
for x in json.loads((prior/'application-preservation.json').read_text())['files']:
 actual=sha(repo/x['path']);app.append(dict(path=x['path'],expected=x['sha256'],actual=actual,unchanged=actual==x['sha256']))
assert all(x['unchanged'] for x in app)
source=repo/'docs/stage6-heartbeat-journal-20260918/sacrificial'
for q in (source,*source.parents):assert not q.is_symlink() and not q.is_junction()
files=sorted(source.iterdir());assert len(files)==12 and all(p.is_file() and p.suffix=='.bin' and not p.is_symlink() and not p.is_junction() for p in files)
inventory=[dict(name=p.name,size=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns) for p in files]
expected=json.loads((prior/'full-input-availability.json').read_text());assert inventory==expected['files']
space=shutil.disk_usage('D:/');assert space.free>sum(x['size'] for x in inventory)*2+1073741824
oldruns=[str(p) for p in C.glob('integrated-dry1-*')];assert not oldruns,'Existing dry1 requires owner review before another run'
put('preflight.json',dict(status='PASS_PENDING_PROCESS_CHECK',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),code=str(C),candidateHashes=checked,applicationHashes=app,archive=receipt,archiveVerifiedMembers=1886,source=str(source),syntheticInventory=inventory,syntheticBytes=sum(x['size'] for x in inventory),DfreeBytes=space.free,priorDry1Runs=oldruns,protectedAccess=False,productionChanged=False,harnessModified=False))
print(json.dumps(dict(candidateFiles=len(checked),applicationFiles=len(app),archiveMembers=1886,syntheticFiles=len(files),syntheticBytes=sum(x['size'] for x in inventory),DfreeGiB=space.free/2**30,status='PASS_PENDING_PROCESS_CHECK')))
