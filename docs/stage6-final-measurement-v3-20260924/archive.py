"""Bounded immutable non-acceptance archive; no live candidate imports."""
import ast,datetime,hashlib,json,pathlib,zipfile
from prepare import R,C,sha,record,write,load

DEST=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 FINAL MEASUREMENT V3 20260924 a34f91e1')
assert not DEST.exists(),'Never overwrite archival evidence'
assert load(R/'screen-result.json')['status']=='MEASUREMENT_OVERHEAD_CONFLICT'
census=load(R/'final-census.json')
assert census['processCount']==0 and census['traceCount']==0
files=[]
for p in sorted(R.glob('*.py')):
    ast.parse(p.read_text(),filename=str(p));files.append(dict(path=str(p),sha256=sha(p),result='PASS',method='ast.parse'))
write('final-syntax-results.json',files)
entries=[]
for root,prefix in [(R,'report'),(C,'partial-successor')]:
    for p in sorted(root.rglob('*')):
        if not p.is_file():continue
        assert not p.is_symlink() and not p.stat().st_file_attributes&0x400
        assert not p.name.lower().startswith('.env') and p.suffix.lower() not in {'.pem','.key','.token','.sqlite','.sqlite3','.db'},str(p)
        row=record(p);row['name']=prefix+'/'+p.relative_to(root).as_posix();entries.append(row)
assert len(entries)==len({x['name'] for x in entries})
manifest=dict(status='MEASUREMENT_OVERHEAD_CONFLICT',acceptance=False,candidateLiveEligible=False,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),entries=entries)
DEST.mkdir(parents=True)
archive=DEST/'evidence.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for row in entries:
        assert sha(row['path'])==row['sha256'];z.write(row['path'],row['name'])
    z.writestr('archive-manifest.json',json.dumps(manifest,sort_keys=True,indent=2))
members=[]
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
    for row in entries:
        with z.open(row['name']) as f:h=hashlib.file_digest(f,'sha256').hexdigest()
        assert h==row['sha256'];assert z.getinfo(row['name']).file_size==row['bytes']
        assert sha(row['path'])==h
        members.append(dict(name=row['name'],bytes=row['bytes'],sha256=h))
    assert json.loads(z.read('archive-manifest.json'))==manifest
    members.append(dict(name='archive-manifest.json',sha256=hashlib.sha256(z.read('archive-manifest.json')).hexdigest(),bytes=z.getinfo('archive-manifest.json').file_size))
receipt=dict(archive=str(archive),archiveSHA256=sha(archive),bytes=archive.stat().st_size,membersVerified=len(members),manifestSHA256=members[-1]['sha256'],status='VERIFIED_NON_ACCEPTANCE_ARCHIVE',sourceHashesReverified=True,memberHashes=members)
write('archive-receipt.json',receipt)
with (DEST/'archive-receipt.json').open('x') as f:json.dump(receipt,f,indent=2)
assert sha(DEST/'archive-receipt.json')==sha(R/'archive-receipt.json')
print(json.dumps({k:v for k,v in receipt.items() if k!='memberHashes'}))
