"""Finalize nonsecret diagnostic evidence after all live collection stops."""
import pathlib,json,hashlib,zipfile,os,shutil,datetime
r=pathlib.Path(__file__).parent;p=json.loads((r/'plan.json').read_text());code=pathlib.Path(p['live_code']);dest=pathlib.Path(p['archive'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,sort_keys=True,indent=2);f.flush();os.fsync(f.fileno())
host=json.loads((r/'host-final.json').read_text());app=json.loads((r/'application-preservation.json').read_text())
assert not host['matchingLive'] and not host['scopedProcesses'] and not host['remainingJ6KernelSessions'] and host['etwQueryExit']==0
assert app['allUnchanged']
for x in json.loads((r/'final-source.json').read_text()):assert sha(pathlib.Path(x['path']))==x['sha256']
syntax=[]
for base in (r,code):
 for q in base.glob('*.py'):compile(q.read_bytes(),str(q),'exec');syntax.append(str(q))
put(r/'python-syntax.json',dict(status='PASS',files=syntax,operation='compile bytes in memory; no module execution or pyc output'))
put(r/'disposition.json',dict(status='INCONCLUSIVE',childKernelIdentityStress='PASS',fullRetainedHandleCoverage='INCOMPLETE',historical87='UNKNOWN',hardDeadlineReproducedThisPass=False,legacyCollectorFailures='PRESERVED',protectedBaselineEligible=False,protectedAccess=False,productionChanged=False))
files=[]
for prefix,base in [('report',r),('live',code)]:
 for directory,dirs,names in os.walk(base,followlinks=False):
  for n in dirs+names:
   q=pathlib.Path(directory)/n
   if q.is_symlink() or q.is_junction():raise RuntimeError('Reparse artifact refused')
  for n in names:
   q=pathlib.Path(directory)/n
   if n.startswith('.env'):raise RuntimeError('Environment file refused')
   files.append(dict(name=prefix+'/'+q.relative_to(base).as_posix(),source=str(q),size=q.stat().st_size,sha256=sha(q)))
files.sort(key=lambda x:x['name']);put(r/'archive-manifest.json',dict(status='INCONCLUSIVE',protectedBaselineAuthorized=False,files=files))
with zipfile.ZipFile(r/'evidence.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
 for x in files:z.write(x['source'],x['name'])
 z.write(r/'archive-manifest.json','archive-manifest.json')
with (r/'evidence.zip').open('r+b',buffering=0) as f:os.fsync(f.fileno())
def verify(base):
 with zipfile.ZipFile(base/'evidence.zip') as z:
  assert len(z.namelist())==len(files)+1
  assert set(z.namelist())=={x['name'] for x in files}|{'archive-manifest.json'}
  assert z.read('archive-manifest.json')==(base/'archive-manifest.json').read_bytes()
  for x in files:
   b=z.read(x['name']);assert len(b)==x['size'] and hashlib.sha256(b).hexdigest()==x['sha256']
verify(r)
for x in files:assert sha(pathlib.Path(x['source']))==x['sha256']
if dest.exists():raise RuntimeError('Archive destination already exists; no overwrite')
dest.mkdir(parents=True)
for n in ('evidence.zip','archive-manifest.json','REPORT.md','disposition.json','campaign-summary.json','report-metrics.json','final-source.json','historical-87-coverage.json','host-final.json'):
 with (r/n).open('rb') as a,(dest/n).open('xb') as b:shutil.copyfileobj(a,b);b.flush();os.fsync(b.fileno())
 assert sha(r/n)==sha(dest/n)
verify(dest)
receipt=dict(status='HASH_VERIFIED',validationStatus='INCONCLUSIVE',members=len(files)+1,path=str(dest),zipSHA256=sha(dest/'evidence.zip'),manifestSHA256=sha(dest/'archive-manifest.json'),protectedBaselineAuthorized=False,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
put(r/'archive-verification.json',receipt);put(dest/'archive-verification.json',receipt)
assert sha(r/'archive-verification.json')==sha(dest/'archive-verification.json')
print(json.dumps(receipt))
