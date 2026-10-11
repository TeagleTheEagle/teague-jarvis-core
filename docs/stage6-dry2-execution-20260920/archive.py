import pathlib,json,hashlib,zipfile,os,shutil,datetime
R=pathlib.Path(__file__).parent;pre=json.loads((R/'preflight.json').read_text());v=json.loads((R/'run-verification.json').read_text());run=pathlib.Path(v['run']);C=pathlib.Path(pre['code']);repo=R.parent.parent
D=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 DRY RUN 2 20260920')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,sort_keys=True,indent=2);f.flush();os.fsync(f.fileno())
h=json.loads((R/'host-after.json').read_text());assert not h['matchingLive'] and not h['scopedProcesses'] and not h['traceSessions'] and h['traceQueryExit']==0
for x in pre['candidateHashes']:assert sha(pathlib.Path(x['path']))==x['expected']
for x in pre['applicationHashes']:assert sha(repo/x['path'])==x['expected']
# Reverify the entire first-run canonical archive and original evidence without mutation.
prior=pre['archive'];old=pathlib.Path(prior['path'])
assert sha(old/'evidence.zip')==prior['zipSHA256'] and sha(old/'archive-manifest.json')==prior['manifestSHA256']
oldmanifest=json.loads((old/'archive-manifest.json').read_text())
with zipfile.ZipFile(old/'evidence.zip') as z:
 assert len(z.namelist())==131
 for item in oldmanifest['files']:
  assert hashlib.sha256(z.read(item['name'])).hexdigest()==item['sha256']
  assert sha(pathlib.Path(item['source']))==item['sha256']
 assert z.read('archive-manifest.json')==(old/'archive-manifest.json').read_bytes()
files=[]
for prefix,base in [('report',R),('run',run)]:
 for directory,dirs,names in os.walk(base,followlinks=False):
  for n in dirs+names:
   p=pathlib.Path(directory)/n
   if p.is_symlink() or p.is_junction():raise RuntimeError('Reparse artifact refused')
  for n in names:
   p=pathlib.Path(directory)/n
   if n.startswith('.env') or n.lower() in ('credentials.json','secrets.json'):raise RuntimeError('Secrets not allowed')
   files.append(dict(name=prefix+'/'+p.relative_to(base).as_posix(),source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
for x in pre['candidateHashes']:
 p=pathlib.Path(x['path']);files.append(dict(name='candidate/'+x['name'],source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
files.sort(key=lambda x:x['name']);put(R/'archive-manifest.json',dict(status='DRY_RUN_2_PASS',files=files,dryRun2Executed=True,protectedBaselineAuthorized=False))
with zipfile.ZipFile(R/'evidence.zip','x',zipfile.ZIP_DEFLATED) as z:
 for x in files:z.write(x['source'],x['name'])
 z.write(R/'archive-manifest.json','archive-manifest.json')
with (R/'evidence.zip').open('r+b',buffering=0) as f:os.fsync(f.fileno())
def verify(base):
 with zipfile.ZipFile(base/'evidence.zip') as z:
  assert len(z.namelist())==len(files)+1
  assert set(z.namelist())=={x['name'] for x in files}|{'archive-manifest.json'}
  for x in files:
   b=z.read(x['name']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
  assert z.read('archive-manifest.json')==(base/'archive-manifest.json').read_bytes()
verify(R)
for x in files:assert sha(pathlib.Path(x['source']))==x['sha256']
D.mkdir(parents=True,exist_ok=False)
for n in ('REPORT.md','PROPOSED-PROTECTED-BASELINE.md','disposition.json','preflight.json','run-verification.json','host-before.json','host-after.json','archive-manifest.json','evidence.zip'):
 with (R/n).open('rb') as a,(D/n).open('xb') as b:shutil.copyfileobj(a,b);b.flush();os.fsync(b.fileno())
 assert sha(R/n)==sha(D/n)
verify(D)
receipt=dict(status='HASH_VERIFIED',validationStatus='DRY_RUN_2_PASS',members=len(files)+1,path=str(D),zipSHA256=sha(D/'evidence.zip'),manifestSHA256=sha(D/'archive-manifest.json'),baselineManifestSHA256=v['manifestSHA256'],dryRun2Executed=True,protectedBaselineAuthorized=False,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
put(R/'archive-verification.json',receipt);put(D/'archive-verification.json',receipt);assert sha(R/'archive-verification.json')==sha(D/'archive-verification.json');print(json.dumps(receipt))
