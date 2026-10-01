import pathlib,json,hashlib,zipfile,shutil,os,datetime
R=pathlib.Path(__file__).parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
host=read(R/'final-host-cleanup.json');assert not host['matchingLive'] and not host['unknown'] and not host['liveDiagnosticsOrVirtualBox'] and not host['traceSessions']
sources={};artifacts=[]
for directory in ('','batched-candidate','medium-candidate'):
 base=R/directory;C=pathlib.Path(read(base/'plan.json')['code'])
 for x in read(base/'candidate-hashes.json'):assert sha(C/x['name'])==x['sha256']
 label=directory or 'initial-candidate'
 for p in C.rglob('*'):
  st=p.lstat();assert not st.st_file_attributes&0x400
  if p.is_file():
   assert p.name!='.env';name=label+'/'+p.relative_to(C).as_posix();sources[name]=p
   if p.parent==C:artifacts.append(dict(path=str(p),sha256=sha(p),bytes=st.st_size))
(R/'all-integration-artifacts.json').write_text(json.dumps(artifacts,indent=2))
for p in R.rglob('*'):
 if p.is_file() and p.name!='archive-verification.json':sources['report/'+p.relative_to(R).as_posix()]=p
C=pathlib.Path(read(R/'medium-candidate/plan.json')['code']);out=C.parent/'final-evidence-archive';out.mkdir(exist_ok=False)
manifest=[dict(name=n,bytes=p.stat().st_size,sha256=sha(p)) for n,p in sorted(sources.items())]
(out/'archive-manifest.json').write_text(json.dumps(manifest,indent=2))
with zipfile.ZipFile(out/'evidence.zip','x',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
 for n,p in sources.items():z.write(p,n)
 z.write(out/'archive-manifest.json','archive-manifest.json')
for p in out.iterdir():
 with p.open('r+b',buffering=0) as f:os.fsync(f.fileno())
target=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 TRACE CAPACITY NATIVE ENTRY 20260921');target.mkdir(exist_ok=False)
for n in ('archive-manifest.json','evidence.zip'):shutil.copy2(out/n,target/n);assert sha(out/n)==sha(target/n)
shutil.copy2(R/'REPORT.md',target/'REPORT.md');assert sha(target/'REPORT.md')==sha(R/'REPORT.md')
with zipfile.ZipFile(target/'evidence.zip') as z:
 assert len(z.namelist())==len(manifest)+1
 for x in manifest:assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256']
 assert z.read('archive-manifest.json')==(out/'archive-manifest.json').read_bytes()
receipt=dict(path=str(target),members=len(manifest)+1,zipSHA256=sha(target/'evidence.zip'),manifestSHA256=sha(target/'archive-manifest.json'),reportSHA256=sha(target/'REPORT.md'),status='HASH_VERIFIED',acceptance='TRACE_INTEGRATION_STILL_DEFECTIVE',failuresPreserved=True)
(R/'archive-verification.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
