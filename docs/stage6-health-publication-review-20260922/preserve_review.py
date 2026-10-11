import hashlib,json,os,zipfile
from pathlib import Path
R=Path(__file__).resolve().parent
P=R.parent/'stage6-medium-v5-fresh-20260922'
A=Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 HEALTH PUBLICATION REVIEW 20260922')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):
    with p.open('x',encoding='utf8') as f:json.dump(x,f,indent=2);f.flush();os.fsync(f.fileno())
frozen=load(P/'candidate-frozen.json')['files']
for x in frozen:assert sha(x['path'])==x['sha256'],x['path']
old=load(P/'archive-verification.json');zpath=Path(old['archive']);manifest=zpath.parent/'manifest.json'
assert sha(zpath)==old['archiveSHA256'] and sha(manifest)==old['manifestSHA256']
with zipfile.ZipFile(zpath) as z:
    assert len(z.namelist())==len(set(z.namelist()))==old['membersVerified']
    assert z.read('manifest.json')==manifest.read_bytes()
    for x in load(manifest)['files']:
        b=z.read(x['name']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
save(R/'preservation.json',dict(status='PASS',candidateFilesVerified=len(frozen),failedArchiveMembersVerified=old['membersVerified'],failedArchiveSHA256=old['archiveSHA256'],implementation=False,testsRun=0,mediumAttempts=0,protectedAccess=False,productionChanged=False))
sources=[('review/'+p.name,p) for p in sorted(R.iterdir()) if p.is_file()]
sources += [('prior-reference/'+n,P/n) for n in ('diagnosis.json','final-disposition.json','archive-verification.json','candidate-frozen.json')]
rows=[dict(name=n,source=str(p),bytes=p.stat().st_size,sha256=sha(p)) for n,p in sources]
assert not A.exists();A.mkdir()
save(A/'manifest.json',dict(status='REVIEW_COMPLETE_IMPLEMENTATION_PROPOSED',files=rows))
with (A/'evidence.zip').open('xb') as f:
    with zipfile.ZipFile(f,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for x in rows:z.write(x['source'],x['name'])
        z.write(A/'manifest.json','manifest.json')
    f.flush();os.fsync(f.fileno())
with zipfile.ZipFile(A/'evidence.zip') as z:
    assert len(z.namelist())==len(set(z.namelist()))==len(rows)+1
    assert z.read('manifest.json')==(A/'manifest.json').read_bytes()
    for x in rows:
        b=z.read(x['name']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']==sha(x['source'])
for x in frozen:assert sha(x['path'])==x['sha256']
receipt=dict(status='PASS',archive=str(A/'evidence.zip'),membersVerified=len(rows)+1,archiveSHA256=sha(A/'evidence.zip'),manifestSHA256=sha(A/'manifest.json'),reviewSHA256=sha(R/'REVIEW.md'))
save(R/'archive-verification.json',receipt);save(A/'archive-verification.json',receipt)
assert sha(R/'archive-verification.json')==sha(A/'archive-verification.json')
print(json.dumps(receipt))
