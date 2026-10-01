import pathlib,json,hashlib,zipfile,os
R=pathlib.Path(__file__).resolve().parent
C=pathlib.Path(json.loads((R/'candidate.json').read_text())['code'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((R/'final-verification.json').read_text())['status']=='PASS'
dest=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 CHECKER V2 FOCUSED COMPLETION 20260923')
pairs=[]
for prefix,root in (('report',R),('candidate',C)):
 for base,dirs,names in os.walk(root,followlinks=False):
  for n in dirs+names:
   p=pathlib.Path(base)/n
   assert not p.lstat().st_file_attributes&0x400,('reparse',str(p))
  for n in names:
   p=pathlib.Path(base)/n
   assert n.lower() not in ('.env','.env.local','credentials.json','secrets.json'),('unexpected secret filename',str(p))
   pairs.append((prefix+'/'+p.relative_to(root).as_posix(),p))
pairs.sort();manifest=[dict(path=n,bytes=p.stat().st_size,sha256=sha(p)) for n,p in pairs]
dest.mkdir(exist_ok=False)
with (dest/'manifest.json').open('x') as f:json.dump(manifest,f,indent=2);f.flush();os.fsync(f.fileno())
archive=dest/'evidence.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for n,p in pairs:z.write(p,n)
with archive.open('r+b',buffering=0) as f:os.fsync(f.fileno())
with zipfile.ZipFile(archive) as z:
 assert set(z.namelist())=={x['path'] for x in manifest}
 for x in manifest:
  b=z.read(x['path']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
for x,(_,p) in zip(manifest,pairs):assert sha(p)==x['sha256']
receipt=dict(status='PASS',membersVerified=len(manifest),archive=str(archive),archiveBytes=archive.stat().st_size,archiveSHA256=sha(archive),manifestSHA256=sha(dest/'manifest.json'),sourcePostArchiveHashesVerified=True)
for p in (R/'canonical-archive-receipt.json',dest/'receipt.json'):
 with p.open('x') as f:json.dump(receipt,f,indent=2);f.flush();os.fsync(f.fileno())
print(json.dumps(receipt,indent=2))
