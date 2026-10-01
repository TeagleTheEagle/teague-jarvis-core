"""Copy only this new, nonsecret diagnostic evidence folder; never overwrite."""
from pathlib import Path
import hashlib,json,shutil,time
D=Path(__file__).resolve().parent
T=Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\JARVIS COORDINATOR READINESS DIAGNOSTIC 2026-09-16')/D.name
assert D.name=='coordinator-readiness-diagnostic-20260916-7a61c902'
assert not T.exists(), 'Archive already exists; do not overwrite'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in D.rglob('*') if p.is_file())
assert all(p.suffix in ('.py','.json','.md','.log') or p.name in ('TEST_ONLY','stop') for p in files)
assert all(p.name not in ('SHA256.json','archive-verification.json') for p in files)
manifest=[{'path':p.relative_to(D).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]
(D/'SHA256.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
files.append(D/'SHA256.json');T.mkdir(parents=True,exist_ok=False);checks=[]
for p in files:
 relative=p.relative_to(D);q=T/relative;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
 checks.append({'path':relative.as_posix(),'sha256':sha(p),'match':sha(p)==sha(q)})
assert all(x['match'] for x in checks)
receipt={'at':time.time(),'destination':str(T),'files_verified':len(checks),'mismatches':0,'files':checks,'scope':'only this diagnostic evidence directory; excludes TEST runtime directories/databases/private configurations and credentials'}
(D/'archive-verification.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
shutil.copyfile(D/'archive-verification.json',T/'archive-verification.json')
assert sha(D/'archive-verification.json')==sha(T/'archive-verification.json')
print(json.dumps({'files_verified':len(checks),'receipt_verified':True,'destination':str(T)}))
