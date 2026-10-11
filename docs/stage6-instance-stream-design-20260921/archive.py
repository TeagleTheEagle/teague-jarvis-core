import pathlib,json,hashlib,zipfile,os,shutil,datetime
R=pathlib.Path(__file__).parent
T=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\instance-stream-62cd5dabd4cb46b593990f1fae4b2a28')
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 INSTANCE STREAM DESIGN 20260921')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
freeze=load(R/'freeze.json')
for row in freeze['checks']:assert sha(pathlib.Path(row['path']))==row['sha256'],row['path']
for row in load(R/'prototype-hashes.json'):assert sha(pathlib.Path(row['path']))==row['sha256'],row['path']
historical=[]
for row in freeze['archives']:
 base=pathlib.Path(row['path']);zips=list(base.glob('*.zip'));assert len(zips)==1
 assert sha(zips[0])==row['zipSHA256']
 historical.append(dict(path=str(zips[0]),sha256=row['zipSHA256'],membersPreviouslyVerified=row['members']))
entries=[]
for prefix,base in [('report',R),('sacrificial',T)]:
 for p in sorted(base.rglob('*')):
  if not p.is_file():continue
  assert not p.is_symlink() and not (p.stat().st_file_attributes & 0x400),str(p)
  assert p.name.lower() not in ('.env','credentials.json'),str(p)
  if p.name=='archive-verification.json':continue
  entries.append((prefix+'/'+p.relative_to(base).as_posix(),p))
assert len({n for n,p in entries})==len(entries)
manifest={'format':'sha256-evidence-v1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'BLOCKED','historicalArchiveChecks':historical,'files':[{'name':n,'bytes':p.stat().st_size,'sha256':sha(p)} for n,p in entries]}
payload=(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode()
out=R.parent/'stage6-instance-stream-design-20260921-evidence-final.zip'
with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
 for n,p in entries:z.write(p,n)
 z.writestr('manifest.json',payload)
with out.open('r+b') as f:os.fsync(f.fileno())
def verify(p):
 with zipfile.ZipFile(p) as z:
  assert len(z.namelist())==len(set(z.namelist()))==len(entries)+1
  assert z.read('manifest.json')==payload
  for row in manifest['files']:
   with z.open(row['name']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256'],row['name']
 return len(entries)+1
count=verify(out)
A.mkdir(parents=False,exist_ok=False)
dest=A/'evidence.zip'
with out.open('rb') as src,dest.open('xb') as target:
 shutil.copyfileobj(src,target,1024*1024);target.flush();os.fsync(target.fileno())
with (A/'manifest.json').open('xb') as f:f.write(payload);f.flush();os.fsync(f.fileno())
assert sha(dest)==sha(out)
assert verify(dest)==count
for n,p in entries:assert sha(p)==next(x['sha256'] for x in manifest['files'] if x['name']==n),str(p)
receipt=dict(status='HASH_VERIFIED',acceptance='BLOCKED',members=count,path=str(A),zipSHA256=sha(dest),manifestSHA256=sha(A/'manifest.json'),reportSHA256=sha(R/'REPORT.md'),bytes=dest.stat().st_size,historicalEvidenceUnchanged=True,frozenCandidateHashesUnchanged=116,failuresPreserved=True)
data=(json.dumps(receipt,indent=2)+'\n').encode()
for p in [R/'archive-verification.json',A/'archive-verification.json']:
 with p.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert (R/'archive-verification.json').read_bytes()==(A/'archive-verification.json').read_bytes()
print(json.dumps(receipt))
