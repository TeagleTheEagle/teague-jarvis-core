"""Build review artifacts. Does not install or launch anything."""
import difflib
import hashlib
import json
from pathlib import Path
import shutil

stage=Path(__file__).resolve().parent
live=stage.parent.parent
paths=['assistant_capabilities.py','actions.py','server.py','inspection_jobs.py','inspection_runtime.py',
       'static/app.js','static/assistant-controls.js','static/index.html','static/inspection-client.js',
       'desktop/main.cjs','desktop/preload.cjs']
manifest=[];patches=[]
for name in paths:
    original=live/name;candidate=stage/'candidate'/name
    before=original.read_bytes() if original.exists() else None
    after=candidate.read_bytes()
    if before==after:continue
    manifest.append({'path':name,'before_sha256':hashlib.sha256(before).hexdigest() if before is not None else None,
                     'candidate_sha256':hashlib.sha256(after).hexdigest()})
    if before is not None:
        backup=stage/'before'/name;backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(before)
    patches.extend(difflib.unified_diff((before or b'').decode('utf-8').replace('\r\n','\n').splitlines(True),after.decode('utf-8').replace('\r\n','\n').splitlines(True),fromfile='before/'+name,tofile='candidate/'+name))
(stage/'manifest.json').write_text(json.dumps({'status':'prepared_not_installed','files':manifest},indent=2),encoding='utf-8')
(stage/'changes.diff').write_text(''.join(patches),encoding='utf-8')
print(json.dumps({'files':len(manifest),'paths':[r['path'] for r in manifest],'status':'prepared_not_installed'}))
