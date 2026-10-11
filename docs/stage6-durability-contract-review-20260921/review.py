from pathlib import Path
import json,hashlib,zipfile,uuid,shutil
R=Path(__file__).parent;P=R.parent/'stage6-writer-identity-diagnosis-20260921'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(name,obj):
 with (R/name).open('x',encoding='utf8') as f:json.dump(obj,f,indent=2)
freeze=json.loads((P/'freeze.json').read_text());receipt=json.loads((P/'archive-verification.json').read_text())
for x in freeze['checks']:assert sha(Path(x['path']))==x['sha256'],x['path']
archive=Path(receipt['archive']);assert sha(archive)==receipt['zipSHA256']
mf=archive.parent/'manifest.json';assert sha(mf)==receipt['manifestSHA256']
m=json.loads(mf.read_text());checks=[]
with zipfile.ZipFile(archive) as z:
 assert len(z.namelist())==receipt['members']==382
 assert z.read('manifest.json')==mf.read_bytes()
 assert set(z.namelist())=={x['name'] for x in m['files']}|{'manifest.json'}
 for x in m['files']:
  with z.open(x['name']) as f:
   h=hashlib.sha256();size=0
   for b in iter(lambda:f.read(1048576),b''):h.update(b);size+=len(b)
  assert size==x['bytes'] and h.hexdigest()==x['sha256'],x['name']
  assert sha(Path(x['source']))==x['sha256'],x['source']
  checks.append({'path':x['source'],'sha256':x['sha256']})
references=[
 Path(r'C:\Users\jonny\.codex\attachments\caff454c-50cd-4832-ad79-23ead1f2966b\Pasted text.txt'),
 Path(r'C:\Users\jonny\.codex\attachments\6ca20665-0e62-480f-a0e6-015a78999e74\Pasted text.txt'),
 Path(r'C:\Users\jonny\.codex\attachments\d4604b3d-f2a6-443e-a1a7-9e6a12a80b5c\Pasted text.txt'),
 R.parent/'stage6-dual-cleanup-20260920/DESIGN.md',
 R.parent/'stage6-cleanup-integration-review-20260920/REPORT.md',
 Path(freeze['newCode'])/'cleanup_checker.py',Path(freeze['newCode'])/'AuthoritativeEvents.cs']
snap=R/'references';snap.mkdir(exist_ok=False);refs=[]
for i,p in enumerate(references):
 n=f'{i:02d}-'+p.name
 with (snap/n).open('xb') as f:f.write(p.read_bytes())
 refs.append({'path':str(p),'snapshot':n,'sha256':sha(p)})
run=uuid.uuid4().hex;(R/'final'/run).mkdir(parents=True,exist_ok=False)
with (R/'host_preflight.ps1').open('xb') as f:f.write((R.parent/'stage6-evidence-restoration-20260921/host_preflight.ps1').read_bytes())
save('preservation.json',{'frozen116':'UNCHANGED','otherFrozenChecks':6,'archive':str(archive),'archiveSHA256':receipt['zipSHA256'],'membersVerified':382,'archiveSourceFilesVerified':checks,'references':refs,'hostRun':run,'protectedVMAccessed':False,'productionChanged':False})
print(json.dumps({'hostRun':run,'archiveVerified':382,'frozenVerified':116}))
