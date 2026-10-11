import pathlib,json,hashlib,zipfile,uuid,shutil
R=pathlib.Path(__file__).parent; P=R.parent/'stage6-instance-stream-design-20260921'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
f=read(P/'freeze.json')
for x in f['checks']:assert sha(pathlib.Path(x['path']))==x['sha256'],x['path']
a=read(P/'archive-verification.json');base=pathlib.Path(a['path']);assert sha(base/'evidence.zip')==a['zipSHA256'];manifest=read(base/'manifest.json')
assert sha(base/'manifest.json')==a['manifestSHA256']
with zipfile.ZipFile(base/'evidence.zip') as z:
 assert len(z.namelist())==a['members']==143
 for x in manifest['files']:
  with z.open(x['name']) as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==x['sha256']
source=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\f469b94b665e4808af1c5bb6aa46b207\code')
dest=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE')/('authoritative-'+uuid.uuid4().hex)/'code';dest.mkdir(parents=True)
copied=[]
for x in f['checks'][:116]:
 p=pathlib.Path(x['path']);assert p.parent==source,p
 shutil.copy2(p,dest/p.name);assert sha(dest/p.name)==x['sha256'];copied.append(dict(name=p.name,sha256=x['sha256']))
plan=dict(source=str(source),code=str(dest),originalChecks=f['checks'],copied=copied,priorArchive=a,protectedAccess=False,productionChanged=False)
with (R/'preflight.json').open('x') as h:json.dump(plan,h,indent=2)
print(json.dumps(dict(code=str(dest),candidateChecks=len(copied),archiveMembers=143)))
