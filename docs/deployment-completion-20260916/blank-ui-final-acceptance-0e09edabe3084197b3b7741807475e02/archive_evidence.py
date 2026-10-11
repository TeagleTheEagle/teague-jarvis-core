"""Copy only this nonsecret blocked-acceptance evidence folder and verify hashes."""
import hashlib,json,shutil
from pathlib import Path
source=Path(__file__).resolve().parent
destination=Path('C:/Users/jonny/OneDrive/Desktop/TEAGUE INDUSTRIES DATABASE/06 SOURCE RECORDS/JARVIS BLANK UI FINAL ACCEPTANCE 2026-09-16/0e09edabe3084197b3b7741807475e02')
assert not destination.exists(),'Preserve previous archives'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in source.rglob('*') if p.is_file())
assert all(p.suffix.lower() in {'.json','.log','.md','.py'} and not p.is_symlink() for p in files)
manifest=[{'path':str(p.relative_to(source)),'bytes':p.stat().st_size,'sha256':digest(p)} for p in files]
(source/'SHA256.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');files.append(source/'SHA256.json')
matches=[]
for p in files:
    target=destination/p.relative_to(source);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    match=digest(p)==digest(target);assert match
    matches.append({'path':str(p.relative_to(source)),'sha256':digest(p),'match':match})
receipt={'destination':str(destination),'files_verified':len(matches),'mismatches':0,'files':matches,
 'exclusions':'No databases, credentials, bindings, production data, heavy runtime/package, or unrelated working-tree files.',
 'scope':'Narrow evidence copy instead of the broad Sync-TeagueIndustries snapshot to honor this gate-only task.'}
(source/'archive-verification.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
shutil.copyfile(source/'archive-verification.json',destination/'archive-verification.json')
assert digest(source/'archive-verification.json')==digest(destination/'archive-verification.json')
print(json.dumps({'destination':str(destination),'files_verified':len(matches),'receipt_verified':True,'mismatches':0}))
