"""Archive offline TEST evidence only; never traverses protected or runtime roots."""
import pathlib,json,hashlib,os,zipfile,datetime
R=pathlib.Path(__file__).parent;before=json.loads((R/'before.json').read_text());C=pathlib.Path(before['candidate'])
DEST=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 WORKSPACE BINDING V4 OFFLINE 20260923')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,sort_keys=True,indent=2);f.flush();os.fsync(f.fileno())
sample=next(p for p in C.glob('protected-*/workspace-binding-v4.json') if len(read(p).get('dataset',[]))==12)
v=read(sample)
write(R/'BINDING-SCHEMA.json',dict(schema='stage6-workspace-binding-v4',exactEquality=True,extraFieldsAllowed=False,existingSmallDeclarationUnchanged=True,fields=[dict(name=k,type=type(val).__name__,required=True) for k,val in v.items()],validation='Duplicate JSON keys rejected; compare with fresh snapshot of run, current manifest, local files, dataset metadata, runtimes and fixed preservation policy.',dependencyClasses=v['dependencyClasses'],exampleOfflineFixture=str(sample),exampleIsLiveEvidence=False))
rows=[];excluded=[]
for base,label in ((R,'action'),(C,'candidate'),(C.parent/'preservation-v4','failure-fixtures')):
 if not base.exists():continue
 for at,dirs,files in os.walk(base,followlinks=False):
  for name in list(dirs):
   p=pathlib.Path(at)/name
   if p.lstat().st_file_attributes&0x400 or name=='__pycache__':dirs.remove(name);excluded.append(dict(path=str(p),reason='REPARSE_NOT_FOLLOWED' if p.lstat().st_file_attributes&0x400 else 'DISPOSABLE_BYTECODE'))
  for name in files:
   p=pathlib.Path(at)/name
   if p.lstat().st_file_attributes&0x400 or name.casefold().startswith('.env') or p.suffix=='.pyc':excluded.append(dict(path=str(p),reason='REPARSE_OR_ENV_OR_BYTECODE_EXCLUDED'));continue
   s=p.stat();rows.append(dict(path=label+'/'+p.relative_to(base).as_posix(),source=str(p),bytes=s.st_size,mtimeNs=s.st_mtime_ns,sha256=sha(p)))
DEST.mkdir(parents=True,exist_ok=False)
manifest=dict(kind='OFFLINE_TEST_IMPLEMENTATION_EVIDENCE_NOT_LIVE_ACCEPTANCE',timestampUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=sorted(rows,key=lambda r:r['path']),excluded=excluded,protectedAccess=False,productionChange=False,liveRun=False)
write(DEST/'manifest.json',manifest)
archive=DEST/'workspace-binding-v4-offline.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for x in manifest['files']:z.write(x['source'],x['path'])
with archive.open('r+b') as f:os.fsync(f.fileno())
with zipfile.ZipFile(archive) as z:
 assert len(z.namelist())==len(rows)==len(set(z.namelist()))
 for x in rows:
  with z.open(x['path']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==x['sha256']
  assert z.getinfo(x['path']).file_size==x['bytes']
  p=pathlib.Path(x['source']);s=p.stat();assert(s.st_size,s.st_mtime_ns,sha(p))==(x['bytes'],x['mtimeNs'],x['sha256'])
for x in before['inputs']:
 p=pathlib.Path(x['path']);s=p.stat();assert(s.st_size,s.st_mtime_ns,sha(p))==(x['bytes'],x['mtimeNs'],x['sha256'])
receipt=dict(status='VERIFIED',archive=str(archive),archiveBytes=archive.stat().st_size,archiveSHA256=sha(archive),manifestSHA256=sha(DEST/'manifest.json'),members=len(rows),excluded=len(excluded),protectedAccess=False,productionChange=False,liveRun=False,acceptanceEvidence=False)
write(DEST/'archive-receipt.json',receipt);write(R/'archive-receipt.json',receipt)
print(json.dumps(receipt,indent=2))
