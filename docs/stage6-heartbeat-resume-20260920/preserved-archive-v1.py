"""Create a new scoped nonsecret evidence archive; never overwrite old archives."""
import datetime, hashlib, json, os, pathlib, shutil
from prepare import R, OLD, REPO, digest, inventory

DEST=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 HEARTBEAT RESUME 20260920')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def durable(path,data):
    with path.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
def encode(v):return json.dumps(v,sort_keys=True,indent=2).encode('utf-8')

if __name__=='__main__':
    if DEST.exists():raise RuntimeError('Refusing to overwrite existing archive')
    if inventory(OLD)!=read(R/'preserved-inventory-before.json'):raise RuntimeError('Historical evidence changed')
    for v in read(R/'validation-source-copy.json'):
        if digest(R/v['path'])!=v['sha256'] or digest(OLD/v['path'])!=v['sha256']:raise RuntimeError('Candidate source drift')
    for v in read(R/'preexisting-tracked-changes.json'):
        p=REPO/v['path']
        if (digest(p) if p.is_file() else None)!=v['sha256']:raise RuntimeError('Preexisting tracked change drift')
    manifest=inventory(R)
    for row in manifest:
        parts=pathlib.Path(row['path']).parts
        if any(p.startswith('.env') or p.lower() in ('credentials','secrets','.git') for p in parts):raise RuntimeError('Secret/unrelated path refused')
    durable(R/'archive-manifest.json',encode({'purpose':'Preserved FAILED validation evidence, not monitor acceptance','files':manifest}))
    DEST.mkdir(parents=True,exist_ok=False)
    for row in manifest+[{'path':'archive-manifest.json','sha256':digest(R/'archive-manifest.json')}]:
        src=R/row['path'];dest=DEST/row['path'];dest.parent.mkdir(parents=True,exist_ok=True)
        with src.open('rb') as r,dest.open('xb') as w:
            shutil.copyfileobj(r,w);w.flush();os.fsync(w.fileno())
        if digest(src)!=row['sha256'] or digest(dest)!=row['sha256']:raise RuntimeError('Archive hash mismatch: '+row['path'])
    receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archive':str(DEST),'status':'HASH_VERIFIED_FAILURE_EVIDENCE_ARCHIVE',
             'payload_files_verified':len(manifest),'manifest_files_verified':1,'receipt_files_verified':1,
             'total_source_archive_pairs_verified':len(manifest)+2,'manifest_sha256':digest(R/'archive-manifest.json'),
             'historical_files_unchanged':352,'candidate_source_copies_unchanged':19,
             'monitor_acceptance':False,'protected_baseline_authorized':False}
    data=encode(receipt);durable(R/'archive-verification.json',data);durable(DEST/'archive-verification.json',data)
    if digest(R/'archive-verification.json')!=digest(DEST/'archive-verification.json'):raise RuntimeError('Receipt copy mismatch')
    if inventory(OLD)!=read(R/'preserved-inventory-before.json'):raise RuntimeError('Historical evidence changed after archive')
    print(json.dumps(receipt))
