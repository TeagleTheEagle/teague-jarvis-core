"""Archive this new nonsecret review only, after read-only evidence inspection ends."""
from pathlib import Path
import hashlib,json,zipfile,os,shutil,datetime
R=Path(__file__).parent
DEST=Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 PROBE REQUIREMENT REVIEW 20260920')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,sort_keys=True);f.flush();os.fsync(f.fileno())
if DEST.exists():raise RuntimeError('Refuse to overwrite archive')
shutil.copyfile(R.parent/'review_probe_requirement.py',R/'review_probe_requirement.py')
paths=sorted(p for p in R.iterdir() if p.is_file())
if any(p.name.startswith('.env') or p.is_symlink() or p.is_junction() for p in paths):raise RuntimeError('Unexpected archive input')
manifest=[dict(name=p.name,sha256=sha(p),size=p.stat().st_size) for p in paths]
write(R/'manifest.json',dict(decision='REVISE_PROBE_ACCEPTANCE_MODEL',implementation=False,files=manifest))
with zipfile.ZipFile(R/'review-evidence.zip','x',zipfile.ZIP_DEFLATED) as z:
 for p in paths:z.write(p,p.name)
 z.write(R/'manifest.json','manifest.json')
def verify(root):
 with zipfile.ZipFile(root/'review-evidence.zip') as z:
  if len(z.namelist())!=len(manifest)+1 or set(z.namelist())!={x['name'] for x in manifest}|{'manifest.json'}:raise RuntimeError('Member mismatch')
  for x in manifest:
   data=z.read(x['name'])
   if len(data)!=x['size'] or hashlib.sha256(data).hexdigest()!=x['sha256']:raise RuntimeError('Hash mismatch')
  if z.read('manifest.json')!=(root/'manifest.json').read_bytes():raise RuntimeError('Manifest mismatch')
verify(R)
DEST.mkdir(parents=True,exist_ok=False)
for name in ('review-evidence.zip','manifest.json','REPORT.md','proposed-model.json','preservation-verification.json'):
 with (R/name).open('rb') as src,(DEST/name).open('xb') as out:shutil.copyfileobj(src,out);out.flush();os.fsync(out.fileno())
 if sha(R/name)!=sha(DEST/name):raise RuntimeError('Copy mismatch')
verify(DEST)
for x in manifest:
 if sha(R/x['name'])!=x['sha256']:raise RuntimeError('Review changed during archive')
receipt=dict(status='HASH_VERIFIED',path=str(DEST),members=len(manifest)+1,zipSHA256=sha(DEST/'review-evidence.zip'),manifestSHA256=sha(DEST/'manifest.json'),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),decision='REVISE_PROBE_ACCEPTANCE_MODEL',implementation=False)
write(R/'archive-verification.json',receipt);write(DEST/'archive-verification.json',receipt)
print(json.dumps(receipt))
