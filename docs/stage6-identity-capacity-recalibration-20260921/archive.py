import pathlib,json,hashlib,zipfile,shutil,os
R=pathlib.Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
host=read(R/'final-host-state.json');assert not host['matching'] and not host['diagnosticTraces']
assert read(R/'final-preservation.json')['mediumEvidenceUnchanged']
out=R.parent/(R.name+'-archive');out.mkdir(exist_ok=False)
target=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 IDENTITY CAPACITY RECALIBRATION 20260921')
assert not target.exists()
files={}
for label,root in [('report',R),('sacrificial-capacity',pathlib.Path(read(R/'capacity-faults.json')['root']))]:
 for p in root.rglob('*'):
  assert not p.is_symlink() and not p.is_junction()
  if p.is_file():
   assert p.name not in ('.env','archive-verification.json')
   files[label+'/'+p.relative_to(root).as_posix()]=p
manifest=[dict(name=n,bytes=p.stat().st_size,sha256=sha(p)) for n,p in sorted(files.items())]
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
with zipfile.ZipFile(out/'evidence.zip','x',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
 for n,p in sorted(files.items()):z.write(p,n)
 z.write(out/'manifest.json','manifest.json')
for p in out.iterdir():
 with p.open('r+b',buffering=0) as f:os.fsync(f.fileno())
target.mkdir()
for n in ('manifest.json','evidence.zip'):
 shutil.copy2(out/n,target/n);assert sha(out/n)==sha(target/n)
shutil.copy2(R/'REPORT.md',target/'REPORT.md');assert sha(R/'REPORT.md')==sha(target/'REPORT.md')
with zipfile.ZipFile(target/'evidence.zip') as z:
 assert len(z.infolist())==len(manifest)+1
 assert z.read('manifest.json')==(out/'manifest.json').read_bytes()
 for r in manifest:
  with z.open(r['name']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==r['sha256']
  assert z.getinfo(r['name']).file_size==r['bytes']
receipt=dict(status='HASH_VERIFIED',members=len(manifest)+1,path=str(target),zipSHA256=sha(target/'evidence.zip'),manifestSHA256=sha(target/'manifest.json'),reportSHA256=sha(target/'REPORT.md'),acceptance='BLOCKED',historicalArchiveUnchanged=True)
(R/'archive-verification.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
