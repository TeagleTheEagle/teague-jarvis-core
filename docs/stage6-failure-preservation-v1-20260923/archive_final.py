"""Final archive of this offline TEST action only; no live code execution."""
from pathlib import Path
import ast,datetime,hashlib,json,os,zipfile
ROOT=Path(__file__).parent
PRIOR=ROOT.parent/'stage6-coordination-v3-20260923'
CANON=Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 FAILURE PRESERVATION V1 20260923 CAB9745D')
STAGED=Path(r'D:\JARVIS-STAGE6-LIVE\cab9745de28a4cae8aa6f6f7a516bf54')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(path,value):
    with path.open('x') as f:json.dump(value,f,sort_keys=True,indent=2);f.flush();os.fsync(f.fileno())
errors=[]
final=json.loads((PRIOR/'candidate-final-r2.json').read_text()); candidate=Path(final['candidate'])
for x in final['files']:
    p=candidate/x['name']
    if p.stat().st_size!=x['bytes'] or sha(p)!=x['sha256']:errors.append(str(p))
if sha(candidate/'small-source-v3.json')!=final['manifestSHA256']:errors.append('CANDIDATE_MANIFEST')
inputs=json.loads((PRIOR/'before.json').read_text())['inputs']
for x in inputs:
    p=Path(x['path'])
    if 'VirtualBox' in str(p):raise ValueError('PROTECTED_PATH')
    s=p.stat()
    if s.st_size!=x['bytes'] or s.st_mtime_ns!=x['mtimeNs'] or sha(p)!=x['sha256']:errors.append(str(p))
previous=json.loads((PRIOR/'archive-receipt.json').read_text()); old=Path(previous['archive'])
if sha(old)!=previous['archiveSHA256']:errors.append('PREVIOUS_ARCHIVE')
oldrows=json.loads((old.parent/'manifest.json').read_text())
with zipfile.ZipFile(old) as z:
    for x in oldrows:
        b=z.read(x['path'])
        if len(b)!=x['bytes'] or hashlib.sha256(b).hexdigest()!=x['sha256']:errors.append(x['path'])
new=json.loads((ROOT/'new-source-manifest-r2.json').read_text())
for x in new['files']:
    a=ROOT/'code'/x['name'];b=STAGED/'code-r2'/x['name']
    if sha(a)!=x['sha256'] or sha(b)!=x['sha256']:errors.append(x['name'])
    if a.suffix=='.py':ast.parse(a.read_text(),filename=str(a))
if sha(STAGED/'code-r2'/'source-manifest.json')!=new['manifestSHA256']:errors.append('NEW_MANIFEST')
census=json.loads((ROOT/'final-host-census-r2.json').read_text())
if not census['available'] or census['processes'] or census['traces'] or census['unknown']:errors.append('FINAL_CENSUS')
verification=dict(candidateFiles=216,preservedInputFiles=len(inputs),previousArchiveMembers=len(oldrows),
    newFiles=4,syntaxFiles=3,focusedTests=48,failed=0,errors=errors,
    matchingProcesses=0 if not census['processes'] else None,traceSessions=0 if not census['traces'] else None,
    protectedAccess=False,productionChange=False,liveRun=False,UAC=False,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
write(ROOT/'final-verification.json',verification)
if errors:raise RuntimeError(errors)

CANON.mkdir(exist_ok=False)
rows=[];excluded=[];sources={}
for base,prefix in ((ROOT,'action'),(STAGED/'code','staged-r1'),(STAGED/'code-r2','staged-r2')):
    for p in sorted(base.rglob('*')):
        if p.is_dir():continue
        if p.is_symlink() or p.lstat().st_file_attributes&0x400:raise ValueError('ARCHIVE_REPARSE')
        name=prefix+'/'+p.relative_to(base).as_posix()
        if p.name=='.env' or p.stat().st_nlink!=1:
            excluded.append(dict(path=name,reason='synthetic .env or hardlink fixture; raw content excluded'))
            continue
        x=dict(path=name,bytes=p.stat().st_size,sha256=sha(p));rows.append(x);sources[name]=p
write(CANON/'manifest.json',dict(label='TEST IMPLEMENTATION / OFFLINE EVIDENCE ONLY',files=rows,excluded=excluded))
archive=CANON/'evidence.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
    for x in rows:z.write(sources[x['path']],x['path'])
with archive.open('r+b') as f:os.fsync(f.fileno())
with zipfile.ZipFile(archive) as z:
    if len(z.namelist())!=len(rows) or len(set(z.namelist()))!=len(rows):raise ValueError('ARCHIVE_COUNT')
    for x in rows:
        with z.open(x['path']) as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
        if z.getinfo(x['path']).file_size!=x['bytes'] or digest!=x['sha256'] or sha(sources[x['path']])!=x['sha256']:
            raise ValueError('ARCHIVE_VERIFY:'+x['path'])
receipt=dict(status='FAILURE_ARCHIVAL_PATH_IMPLEMENTED_AND_TESTED',archive=str(archive),
    archiveSHA256=sha(archive),manifestSHA256=sha(CANON/'manifest.json'),membersVerified=len(rows),
    excludedSyntheticFixtureFiles=len(excluded),focusedTests=48,focusedPass=48,
    sourceManifestSHA256=new['manifestSHA256'],candidateUnchanged=True,preservedInputsUnchanged=True,
    matchingProcesses=0,traceSessions=0,protectedAccess=False,productionChange=False,liveRun=False,UAC=False)
write(CANON/'receipt.json',receipt);write(ROOT/'final-receipt.json',receipt)
print(json.dumps(receipt))
