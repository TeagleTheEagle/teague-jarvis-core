"""Explicit nonsecret acceptance evidence archive; never copy TEST credential state."""
from pathlib import Path
import hashlib,json,shutil
D=Path(__file__).resolve().parent;R=D.parents[2]
target=Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE4 FINAL ACCEPTANCE 20260917')
assert not target.exists(),'Never overwrite existing acceptance evidence'
source=json.loads((D/'final-integrity.json').read_text())['correction_source']
for row in source:
    p=R/row['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['after']
    dest=D/'validated-correction-source'/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
rows=[]
for p in sorted(D.rglob('*')):
    if not p.is_file():continue
    assert p.name!='.env' and p.suffix not in ('.sqlite3','.db','.pem','.key')
    rows.append({'path':str(p.relative_to(D)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(D/'archive-manifest.json').write_text(json.dumps({'destination':str(target),'files':rows},indent=2))
target.mkdir(parents=True)
for row in rows:
    src=D/row['path'];dst=target/row['path'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    assert hashlib.sha256(dst.read_bytes()).hexdigest()==row['sha256']
shutil.copyfile(D/'archive-manifest.json',target/'archive-manifest.json')
assert (D/'archive-manifest.json').read_bytes()==(target/'archive-manifest.json').read_bytes()
result={'destination':str(target),'files_verified':len(rows)+1,'status':'PASS','manifest_sha256':hashlib.sha256((D/'archive-manifest.json').read_bytes()).hexdigest()}
(D/'archive-verification.json').write_text(json.dumps(result,indent=2));shutil.copyfile(D/'archive-verification.json',target/'archive-verification.json')
assert (D/'archive-verification.json').read_bytes()==(target/'archive-verification.json').read_bytes()
print(json.dumps(result))
