"""Apply or roll back only this reviewed package, after explicit user approval."""
import argparse
import hashlib
import json
import os
from pathlib import Path

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

def install(stage, rollback=False, apply=False):
    stage=Path(stage).resolve();live=stage.parent.parent.resolve()
    manifest=json.loads((stage/'manifest.json').read_text(encoding='utf-8'))
    allowed={'assistant_capabilities.py','actions.py','server.py','inspection_jobs.py','inspection_runtime.py','static/app.js','static/assistant-controls.js','static/index.html','static/inspection-client.js','desktop/main.cjs','desktop/preload.cjs'}
    prepared=[]
    for row in manifest['files']:
        name=row['path']
        if name not in allowed:raise ValueError('Unexpected file in update.')
        target=live/name
        if not target.resolve().is_relative_to(live) or target.is_symlink():raise ValueError('Update target escapes application directory.')
        expected=row['candidate_sha256'] if rollback else row['before_sha256']
        if digest(target)!=expected:raise ValueError('Source changed; review again before proceeding: '+name)
        source=stage/('before' if rollback else 'candidate')/name
        desired=row['before_sha256'] if rollback else row['candidate_sha256']
        if desired is not None and digest(source)!=desired:raise ValueError('Review artifact changed: '+name)
        prepared.append((target,source,desired))
    if not apply:return {'status':'validated_only','files':len(prepared)}
    # All paths and hashes are checked before any mutation. Record enough state
    # to restore earlier replacements if an I/O error interrupts installation.
    replaced=[]
    try:
        for target,source,desired in prepared:
            old=target.read_bytes() if target.exists() else None
            if desired is None:target.unlink()
            else:
                temp=target.with_name(target.name+'.capability-update.tmp')
                with temp.open('xb') as out:out.write(source.read_bytes())
                os.replace(temp,target)
            replaced.append((target,old))
    except Exception:
        for target,old in reversed(replaced):
            if old is None:target.unlink(missing_ok=True)
            else:target.write_bytes(old)
        raise
    return {'status':'rolled_back' if rollback else 'installed_restart_required','files':len(prepared)}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');parser.add_argument('--rollback',action='store_true')
    args=parser.parse_args();print(json.dumps(install(Path(__file__).parent,args.rollback,args.apply)))
