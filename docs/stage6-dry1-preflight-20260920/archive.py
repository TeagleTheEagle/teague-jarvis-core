import pathlib,json,hashlib,zipfile,os,shutil
R=pathlib.Path(__file__).parent
D=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 DRY1 PREFLIGHT 20260920')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,sort_keys=True,indent=2);f.flush();os.fsync(f.fileno())
p=json.loads((R/'preflight.json').read_text());h=json.loads((R/'host.json').read_text())
assert not h['matchingLive'] and not h['scopedProcesses'] and not h['remainingDiagnosticTraceSessions'] and h['etwQueryExit']==0
for x in p['candidateHashes']:assert sha(pathlib.Path(x['path']))==x['expected']
files=[dict(name=f.name,sha256=sha(f),size=f.stat().st_size) for f in sorted(R.iterdir()) if f.is_file()]
put(R/'archive-manifest.json',dict(status='BLOCKED',files=files,baselineHashing=False,dryRunExecuted=False))
with zipfile.ZipFile(R/'evidence.zip','x',zipfile.ZIP_DEFLATED) as z:
 for f in files:z.write(R/f['name'],f['name'])
 z.write(R/'archive-manifest.json','archive-manifest.json')
with (R/'evidence.zip').open('r+b',buffering=0) as f:os.fsync(f.fileno())
def verify(base):
 with zipfile.ZipFile(base/'evidence.zip') as z:
  assert len(z.namelist())==len(files)+1
  for f in files:assert hashlib.sha256(z.read(f['name'])).hexdigest()==f['sha256']
  assert z.read('archive-manifest.json')==(base/'archive-manifest.json').read_bytes()
verify(R);D.mkdir(exist_ok=False)
for n in ('REPORT.md','preflight.json','host.json','archive-manifest.json','evidence.zip'):
 with (R/n).open('rb') as a,(D/n).open('xb') as b:shutil.copyfileobj(a,b);b.flush();os.fsync(b.fileno())
 assert sha(R/n)==sha(D/n)
verify(D)
v=dict(status='HASH_VERIFIED',disposition='BLOCKED',members=len(files)+1,archive=str(D),zipSHA256=sha(D/'evidence.zip'),manifestSHA256=sha(D/'archive-manifest.json'))
put(R/'archive-verification.json',v);put(D/'archive-verification.json',v);print(json.dumps(v))
