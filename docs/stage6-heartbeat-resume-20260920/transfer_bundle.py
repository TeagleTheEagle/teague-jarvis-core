"""Copy a sealed archive only. Never enumerate original fixture or VM paths."""
import datetime, hashlib, json, os, pathlib, shutil, zipfile
R=pathlib.Path(__file__).resolve().parent
D=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 HEARTBEAT RESUME 20260920')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate(base):
    manifest=json.loads((base/'archive-payload-manifest.json').read_text())
    with zipfile.ZipFile(base/'evidence-payload.zip') as z:
        if len(z.namelist())!=len(manifest['files'])+1 or set(z.namelist())!={r['path'] for r in manifest['files']}|{'archive-payload-manifest.json'}:raise RuntimeError('Member mismatch')
        if z.read('archive-payload-manifest.json')!=(base/'archive-payload-manifest.json').read_bytes():raise RuntimeError('Manifest mismatch')
        for row in manifest['files']:
            content=z.read(row['path'])
            if len(content)!=row['bytes'] or hashlib.sha256(content).hexdigest()!=row['sha256']:raise RuntimeError('Member hash mismatch')
        if z.read('REPORT.md')!=(base/'REPORT.md').read_bytes():raise RuntimeError('Report mismatch')
    return len(manifest['files'])+1
if __name__=='__main__':
    if D.exists():raise RuntimeError('Refusing overwrite')
    count=validate(R);D.mkdir(parents=True,exist_ok=False)
    for name in ('REPORT.md','archive-payload-manifest.json','evidence-payload.zip'):
        with (R/name).open('rb') as r,(D/name).open('xb') as w:
            shutil.copyfileobj(r,w);w.flush();os.fsync(w.fileno())
        if sha(R/name)!=sha(D/name):raise RuntimeError('Copy mismatch')
    if validate(D)!=count:raise RuntimeError('Destination member mismatch')
    receipt={'status':'HASH_VERIFIED_FAILURE_EVIDENCE_ARCHIVE','archive':str(D),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'payload_members_hash_verified':count,'source_archive_files_hash_verified_including_receipt':4,
             'historical_originals_unchanged':352,'monitor_acceptance':False,
             'zip_sha256':sha(D/'evidence-payload.zip'),'manifest_sha256':sha(D/'archive-payload-manifest.json')}
    data=json.dumps(receipt,indent=2,sort_keys=True).encode()
    for base in (R,D):
        with (base/'archive-verification.json').open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    if sha(R/'archive-verification.json')!=sha(D/'archive-verification.json'):raise RuntimeError('Receipt mismatch')
    print(json.dumps(receipt))
