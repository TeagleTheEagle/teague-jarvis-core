import pathlib,json,hashlib,zipfile,os,shutil,datetime
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'candidate.json').read_text())['code'])
D=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 PROTECTED COLLECTOR INTEGRATION 20260920')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,sort_keys=True);f.flush();os.fsync(f.fileno())
for name in ('stage6-dry1-execution-20260920','stage6-dry2-execution-20260920'):
 receipt=json.loads((R.parent/name/'archive-verification.json').read_text());a=pathlib.Path(receipt['path']);assert sha(a/'evidence.zip')==receipt['zipSHA256'] and sha(a/'archive-manifest.json')==receipt['manifestSHA256']
 for x in json.loads((a/'archive-manifest.json').read_text())['files']:assert sha(pathlib.Path(x['source']))==x['sha256']
files=[];omitted=[]
for prefix,base in [('report',R),('candidate',C)]:
 for directory,dirs,names in os.walk(base,followlinks=False):
  keep=[]
  for n in dirs:
   p=pathlib.Path(directory)/n
   if p.is_symlink() or p.is_junction():omitted.append(dict(path=str(p),reason='Adversarial reparse fixture; never followed'));continue
   if base==C and p.parent==C and n in ('large-synthetic','dual-9aa6b84f76074c83956a1cb4fad811bc','build-temp'):omitted.append(dict(path=str(p),reason='Large synthetic bytes, unchanged archived historical fixture, or disposable build temporary files'));continue
   if n=='__pycache__':continue
   keep.append(n)
  dirs[:]=keep
  for n in names:
   p=pathlib.Path(directory)/n
   if p.suffix=='.obj':continue
   if p.is_symlink() or p.is_junction():omitted.append(dict(path=str(p),reason='Reparse fixture'));continue
   if n.startswith('.env') or n.lower() in ('credentials.json','secrets.json'):raise RuntimeError('Secret artifact forbidden')
   size=p.stat().st_size
   if size>256*2**20:raise RuntimeError('Unexpected large evidence artifact: '+str(p))
   files.append(dict(name=prefix+'/'+p.relative_to(base).as_posix(),source=str(p),bytes=size,sha256=sha(p)))
assert sum(x['bytes'] for x in files)<2*2**30
files.sort(key=lambda x:x['name'])
put(R/'archive-manifest.json',dict(status='BLOCKED',files=files,omitted=omitted,protectedAccess=False,productionChanged=False))
with zipfile.ZipFile(R/'evidence.zip','x',zipfile.ZIP_DEFLATED) as z:
 for x in files:z.write(x['source'],x['name'])
 z.write(R/'archive-manifest.json','archive-manifest.json')
with (R/'evidence.zip').open('r+b',buffering=0) as f:os.fsync(f.fileno())
def verify(base):
 with zipfile.ZipFile(base/'evidence.zip') as z:
  assert len(z.namelist())==len(files)+1
  for x in files:assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256']
  assert z.read('archive-manifest.json')==(base/'archive-manifest.json').read_bytes()
verify(R)
for x in files:assert sha(pathlib.Path(x['source']))==x['sha256']
D.mkdir(parents=True,exist_ok=False)
for n in ('REPORT.md','DESIGN.md','summary.json','candidate-source.json','calibration.json','pre-live-post-cancel.json','adapter-diff.patch','archive-manifest.json','evidence.zip'):
 with (R/n).open('rb') as a,(D/n).open('xb') as b:shutil.copyfileobj(a,b);b.flush();os.fsync(b.fileno())
 assert sha(R/n)==sha(D/n)
verify(D)
receipt=dict(status='HASH_VERIFIED',validationStatus='BLOCKED',members=len(files)+1,bytes=(D/'evidence.zip').stat().st_size,path=str(D),zipSHA256=sha(D/'evidence.zip'),manifestSHA256=sha(D/'archive-manifest.json'),protectedAccess=False,productionChanged=False,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
put(R/'archive-verification.json',receipt);put(D/'archive-verification.json',receipt);assert sha(R/'archive-verification.json')==sha(D/'archive-verification.json')
print(json.dumps(receipt))
