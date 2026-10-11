"""Seal nonsecret evidence using explicit enumeration failures; no protected paths."""
import json, os, pathlib, zipfile
from prepare import R, OLD, REPO, digest, inventory
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write_new(p,data):
    with p.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
if __name__=='__main__':
    if inventory(OLD)!=read(R/'preserved-inventory-before.json'):raise RuntimeError('Original evidence drift')
    for v in read(R/'validation-source-copy.json'):
        if digest(R/v['path'])!=v['sha256'] or digest(OLD/v['path'])!=v['sha256']:raise RuntimeError('Candidate source drift')
    for v in read(R/'preexisting-tracked-changes.json'):
        p=REPO/v['path']
        if (digest(p) if p.is_file() else None)!=v['sha256']:raise RuntimeError('Preexisting tracked change drift')
    files=[]
    def fail(error):raise error
    for root,dirs,names in os.walk(R,onerror=fail,followlinks=False):
        for name in dirs+names:
            if (pathlib.Path(root)/name).is_symlink():raise RuntimeError('Unexpected link')
        for name in names:
            p=pathlib.Path(root)/name
            if name.startswith('.env'):raise RuntimeError('Secret path refused')
            files.append({'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)})
    files.sort(key=lambda r:r['path'])
    manifest={'purpose':'Failed monitor validation evidence; not an acceptance receipt','files':files}
    write_new(R/'archive-payload-manifest.json',json.dumps(manifest,sort_keys=True,indent=2).encode())
    with zipfile.ZipFile(R/'evidence-payload.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
        for row in files:z.write(R/row['path'],row['path'])
        z.write(R/'archive-payload-manifest.json','archive-payload-manifest.json')
    with (R/'evidence-payload.zip').open('r+b') as f:os.fsync(f.fileno())
    import hashlib
    with zipfile.ZipFile(R/'evidence-payload.zip') as z:
        if set(z.namelist())!={r['path'] for r in files}|{'archive-payload-manifest.json'}:raise RuntimeError('Member mismatch')
        for row in files:
            if hashlib.sha256(z.read(row['path'])).hexdigest()!=row['sha256'] or digest(R/row['path'])!=row['sha256']:raise RuntimeError('Payload hash mismatch')
    print(json.dumps({'sealed_payload_files':len(files),'zip_members':len(files)+1,'zip_sha256':digest(R/'evidence-payload.zip')}))
