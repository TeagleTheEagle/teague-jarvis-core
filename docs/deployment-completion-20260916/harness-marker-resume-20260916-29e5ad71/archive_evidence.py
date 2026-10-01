"""Archive only the nonsecret evidence from this stopped TEST run; no overwrite."""
from pathlib import Path
import hashlib,json,re,shutil,time
D=Path(__file__).resolve().parent
T=Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\JARVIS HARNESS MARKER VALIDATION 2026-09-16')/D.name
assert D.name=='harness-marker-resume-20260916-29e5ad71' and not T.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in D.rglob('*') if p.is_file())
assert all(p.suffix in ('.py','.json','.md','.log','.patch') for p in files)
assert all(p.name not in ('SHA256.json','archive-verification.json','secret-scan.json') for p in files)
hits=[]
for p in files:
    text=p.read_text(encoding='utf-8-sig')
    if re.search(r'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',text):hits.append(p.relative_to(D).as_posix())
    if p.suffix=='.json':
        def walk(value):
            if isinstance(value,dict):
                for k,v in value.items():
                    if re.fullmatch(r'(?:api_key|openai_api_key|password|private_key|management_token|controller_token|bootstrap_token|secret|credential|token)',k,re.I) and isinstance(v,str) and v:hits.append(p.relative_to(D).as_posix()+':'+k)
                    walk(v)
            elif isinstance(value,list):
                for v in value:walk(v)
        walk(json.loads(text))
assert not hits,'Potential secret material; do not archive'
scan={'at':time.time(),'files_scanned':len(files),'potential_secret_locations':hits,
      'scope':'Nonsecret explicitly selected test source snapshots, test reports, logs and collection scripts only. No live TEST configs/databases or credentials. Pattern/key scan supplements this allowlist; it is not a universal secret detector.'}
(D/'secret-scan.json').write_text(json.dumps(scan,indent=2),encoding='utf8');files.append(D/'secret-scan.json')
(D/'SHA256.json').write_text(json.dumps([{'path':p.relative_to(D).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files],indent=2),encoding='utf8')
files.append(D/'SHA256.json');T.mkdir(parents=True,exist_ok=False);checks=[]
for p in files:
    relative=p.relative_to(D);target=T/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    checks.append({'path':relative.as_posix(),'sha256':sha(p),'match':sha(p)==sha(target)})
assert all(x['match'] for x in checks)
receipt={'at':time.time(),'destination':str(T),'files_verified':len(checks),'mismatches':0,'files':checks,
         'excluded':'Unrelated working-tree files, production data/configuration, runtime databases, provider/bootstrap/session credentials and heavy packages'}
(D/'archive-verification.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
shutil.copyfile(D/'archive-verification.json',T/'archive-verification.json')
assert sha(D/'archive-verification.json')==sha(T/'archive-verification.json')
print(json.dumps({'files_verified':len(checks),'receipt_verified':True,'destination':str(T),'mismatches':0}))
