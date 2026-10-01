import pathlib,json,hashlib,zipfile,os,datetime
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'freeze.json').read_text())['newCode'])
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def durable(p,b):
 with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
root=C.parent/'finalized-writer-identity';root.mkdir(exist_ok=False)
dest=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 WRITER IDENTITY DIAGNOSIS 20260921')
assert not dest.exists()
files=[]
for prefix,base in [('report',R),('diagnostic',C)]:
 for p in sorted(base.rglob('*')):
  if not p.is_file():continue
  assert not p.is_symlink() and not p.is_junction()
  assert p.name!='.env' and '__pycache__' not in p.parts
  files.append({'source':str(p),'name':prefix+'/'+p.relative_to(base).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
m=json.dumps({'format':'stage6-diagnostic-evidence-v1','status':'BOTH_BOUNDARIES_STILL_DEFECTIVE','files':files,'protectedVMAccessed':False,'productionChanged':False,'mediumRun':False,'largeRun':False},indent=2,sort_keys=True).encode()
durable(root/'manifest.json',m)
zpath=root/'evidence.zip'
with zipfile.ZipFile(zpath,'x',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
 for x in files:z.write(x['source'],x['name'])
 z.writestr('manifest.json',m)
with zpath.open('r+b') as f:f.flush();os.fsync(f.fileno())
def verify(p):
 with zipfile.ZipFile(p) as z:
  assert set(z.namelist())=={x['name'] for x in files}|{'manifest.json'}
  assert z.read('manifest.json')==m
  for x in files:
   h=hashlib.sha256();size=0
   with z.open(x['name']) as f:
    for b in iter(lambda:f.read(1048576),b''):h.update(b);size+=len(b)
   assert size==x['bytes'] and h.hexdigest()==x['sha256'],x['name']
verify(zpath)
dest.mkdir(exist_ok=False)
for name in ['evidence.zip','manifest.json']:
 with (root/name).open('rb') as src,(dest/name).open('xb') as out:
  for b in iter(lambda:src.read(1048576),b''):out.write(b)
  out.flush();os.fsync(out.fileno())
 assert sha(root/name)==sha(dest/name)
durable(dest/'REPORT.md',(R/'REPORT.md').read_bytes())
verify(dest/'evidence.zip')
for x in files:assert sha(pathlib.Path(x['source']))==x['sha256'],x['source']
result={'status':'HASH_VERIFIED','acceptance':'BOTH_BOUNDARIES_STILL_DEFECTIVE','members':len(files)+1,'bytes':zpath.stat().st_size,'archive':str(dest/'evidence.zip'),'manifestSHA256':sha(dest/'manifest.json'),'zipSHA256':sha(dest/'evidence.zip'),'reportSHA256':sha(dest/'REPORT.md'),'liveProcesses':0,'traceSessions':0,'protectedVMAccessed':False,'productionChanged':False}
b=json.dumps(result,indent=2).encode();durable(R/'archive-verification.json',b);durable(dest/'archive-verification.json',b)
print(json.dumps(result))
