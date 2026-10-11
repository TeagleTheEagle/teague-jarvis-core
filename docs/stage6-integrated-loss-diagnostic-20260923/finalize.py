import pathlib,json,hashlib,zipfile
R=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cfg=read(R/'candidate.json');C=pathlib.Path(cfg['code']);run=pathlib.Path(read(R/'normal-run.json')['root'])
for x in cfg['files']:assert sha(C/x['name'])==x['sha256'],x['name']
old=read(R.parent/'stage6-large-small-integration-20260922/candidate.json')
for x in old['files']:assert sha(pathlib.Path(old['code'])/x['name'])==x['sha256'],x['name']
T=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\f40cb16a8a384236b05179bc8f2aea6b\code');telemetry=read(R.parent/'stage6-loss-telemetry-20260922/integrity.json')['candidate']
for x in telemetry:assert sha(T/x['name'])==x['sha256'],x['name']
receipt=read(R.parent/'stage6-loss-telemetry-20260922/archive-receipt.json');assert sha(pathlib.Path(receipt['archive']))==receipt['archiveSHA256']
frozen=dict(status='PASS',currentFiles=len(cfg['files']),previousIntegrationFiles=len(old['files']),telemetryFiles=len(telemetry),currentManifestSHA256=sha(C/'small-source.json'),priorArchiveSHA256=receipt['archiveSHA256'],runFiles=[dict(name=str(p.relative_to(run)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(run.rglob('*')) if p.is_file()])
with (R/'final-integrity.json').open('x') as f:json.dump(frozen,f,indent=2)
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 INTEGRATED LOSS DIAGNOSTIC 20260923 693f0cd1');A.mkdir(exist_ok=False)
items=[]
for prefix,base in [('report',R),('candidate',C)]:
 for p in sorted(base.rglob('*')):
  if p.is_file():
   assert not p.is_symlink() and not (p.stat().st_file_attributes&0x400) and p.name!='.env'
   items.append((p,prefix+'/'+p.relative_to(base).as_posix()))
manifest={name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p,name in items}
with (A/'manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
archive=A/'evidence.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
 for p,name in items:z.write(p,name)
with zipfile.ZipFile(archive) as z:
 assert set(z.namelist())==set(manifest)
 for name,v in manifest.items():
  b=z.read(name);assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256']
for p,name in items:assert sha(p)==manifest[name]['sha256']
result=dict(status='PASS',membersVerified=len(manifest),archive=str(archive),archiveSHA256=sha(archive),manifestSHA256=sha(A/'manifest.json'),sourceCounts=[len(cfg['files']),len(old['files']),len(telemetry)])
for p in (A/'receipt.json',R/'archive-receipt.json'):
 with p.open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result,indent=2))
