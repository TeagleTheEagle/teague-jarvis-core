import pathlib,json,hashlib,zipfile,os,shutil,datetime
R=pathlib.Path(__file__).parent;plan=json.loads((R/'plan.json').read_text());C=pathlib.Path(plan['code']);D=pathlib.Path(plan['archive'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,sort_keys=True,indent=2);f.flush();os.fsync(f.fileno())
h=json.loads((R/'host-final.json').read_text());assert not h['matchingLive'] and not h['scopedProcesses'] and not h['traceSessions'] and h['traceQueryExit']==0
assert json.loads((R/'application-preservation.json').read_text())['allUnchanged']
for x in json.loads((R/'final-source.json').read_text()):assert sha(pathlib.Path(x['path']))==x['sha256']
for x in json.loads((R/'source-before.json').read_text()):assert sha(pathlib.Path(x['path']))==x['sha256']
syntax=[]
for base in (R,C):
 for p in base.glob('*.py'):compile(p.read_bytes(),str(p),'exec');syntax.append(str(p))
put(R/'python-syntax.json',dict(status='PASS',files=syntax,operation='compile in memory; no import/pyc'))
files=[]
for prefix,base in [('report',R),('candidate',C)]:
 for directory,dirs,names in os.walk(base,followlinks=False):
  for n in dirs+names:
   p=pathlib.Path(directory)/n
   if p.is_symlink() or p.is_junction():raise RuntimeError('Reparse artifact refused')
  for n in names:
   p=pathlib.Path(directory)/n
   if n.startswith('.env') or n.lower() in ('credentials.json','secrets.json'):raise RuntimeError('Secret/environment artifact refused')
   files.append(dict(name=prefix+'/'+p.relative_to(base).as_posix(),source=str(p),size=p.stat().st_size,sha256=sha(p)))
files.sort(key=lambda x:x['name']);put(R/'archive-manifest.json',dict(status='DRY_RUN_HARNESS_VALIDATED',dryRun1Executed=False,dryRun2Executed=False,files=files))
with zipfile.ZipFile(R/'evidence.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
 for x in files:z.write(x['source'],x['name'])
 z.write(R/'archive-manifest.json','archive-manifest.json')
with (R/'evidence.zip').open('r+b',buffering=0) as f:os.fsync(f.fileno())
def verify(base):
 with zipfile.ZipFile(base/'evidence.zip') as z:
  assert len(z.namelist())==len(files)+1
  assert set(z.namelist())=={x['name'] for x in files}|{'archive-manifest.json'}
  assert z.read('archive-manifest.json')==(base/'archive-manifest.json').read_bytes()
  for x in files:
   b=z.read(x['name']);assert len(b)==x['size'] and hashlib.sha256(b).hexdigest()==x['sha256']
verify(R)
for x in files:assert sha(pathlib.Path(x['source']))==x['sha256']
if D.exists():raise RuntimeError('Archive destination already exists; do not overwrite')
D.mkdir(parents=True)
for n in ('evidence.zip','archive-manifest.json','REPORT.md','DESIGN.md','DRY-RUN-1-PROCEDURE.md','disposition.json','miniature-summary.json','regression-summary.json','source-before.json','final-source.json','host-final.json'):
 with (R/n).open('rb') as a,(D/n).open('xb') as b:shutil.copyfileobj(a,b);b.flush();os.fsync(b.fileno())
 assert sha(R/n)==sha(D/n)
verify(D)
receipt=dict(status='HASH_VERIFIED',validationStatus='DRY_RUN_HARNESS_VALIDATED',members=len(files)+1,path=str(D),zipSHA256=sha(D/'evidence.zip'),manifestSHA256=sha(D/'archive-manifest.json'),dryRun1Executed=False,dryRun2Executed=False,protectedBaselineAuthorized=False,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
put(R/'archive-verification.json',receipt);put(D/'archive-verification.json',receipt)
assert sha(R/'archive-verification.json')==sha(D/'archive-verification.json');print(json.dumps(receipt))
