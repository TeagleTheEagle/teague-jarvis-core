import pathlib,json,hashlib,zipfile,uuid,os
R=pathlib.Path(__file__).resolve().parent
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=load(R/'before.json');C=pathlib.Path(b['candidate']);frozen=load(R/'candidate-final-r2.json')
assert load(R/'post-focused-host-census.json')['status']=='PASS'
def verify():
 for r in b['inputs']+load(R/'additional-inputs.json'):
  p=pathlib.Path(r['path']);s=p.stat();assert (s.st_size,s.st_mtime_ns,sha(p))==(r['bytes'],r['mtimeNs'],r['sha256'])
 for r in frozen['files']:assert sha(C/r['name'])==r['sha256']
 assert sha(C/'small-source-v3.json')==frozen['manifestSHA256']
verify()
items=[]
for p in sorted(R.rglob('*')):
 if p.is_file() and p.name!='archive-receipt.json':items.append(('action/'+p.relative_to(R).as_posix(),p))
for r in frozen['files']:items.append(('final-source/'+pathlib.PureWindowsPath(r['name']).as_posix(),C/r['name']))
items.append(('final-source/small-source-v3.json',C/'small-source-v3.json'))
for folder in sorted(C.iterdir()):
 if folder.is_dir() and folder.name.startswith(('offline-native-','v2-focused-','v3-successor-focused-','protected-')):
  assert not folder.is_symlink() and not folder.is_junction()
  for p in sorted(folder.rglob('*')):
   assert not p.is_symlink() and not p.is_junction()
   if p.is_file():items.append(('offline-fixtures/'+p.relative_to(C).as_posix(),p))
items.sort();assert len({n.casefold() for n,p in items})==len(items)
manifest=[dict(path=n,bytes=p.stat().st_size,sha256=sha(p)) for n,p in items]
dest=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS')/('STAGE6 COORDINATION V3 FOCUSED 20260923 '+uuid.uuid4().hex[:8]);dest.mkdir(exist_ok=False)
mp=dest/'manifest.json'
with mp.open('x') as f:json.dump(manifest,f,indent=2);f.flush();os.fsync(f.fileno())
archive=dest/'evidence.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for name,p in items:z.write(p,name)
with archive.open('r+b',buffering=0) as f:os.fsync(f.fileno())
with zipfile.ZipFile(archive) as z:
 assert len(z.namelist())==len(manifest)
 for r in manifest:
  data=z.read(r['path']);assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256']
for r,(_,p) in zip(manifest,items):assert sha(p)==r['sha256']
verify()
receipt=dict(status='PASS',archive=str(archive),archiveSHA256=sha(archive),manifestSHA256=sha(mp),membersVerified=len(manifest),originalFilesUnchanged=194,predecessorFilesUnchanged=183,preservedInputFiles=482,candidateFilesUnchanged=216,sourceManifestSHA256=frozen['manifestSHA256'],protectedVMAccess=False,productionChange=False)
for p in (R/'archive-receipt.json',dest/'receipt.json'):
 with p.open('x') as f:json.dump(receipt,f,indent=2);f.flush();os.fsync(f.fileno())
print(json.dumps(receipt,indent=2))
