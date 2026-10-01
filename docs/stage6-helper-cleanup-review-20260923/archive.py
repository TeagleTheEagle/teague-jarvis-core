import pathlib,json,hashlib,zipfile
R=pathlib.Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
dest=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 HELPER CLEANUP ORDER REVIEW 20260923');dest.mkdir(exist_ok=False)
files=sorted(p for p in R.iterdir() if p.is_file());manifest=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in files]
with (dest/'manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
archive=dest/'evidence.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.name)
with zipfile.ZipFile(archive) as z:
 for m in manifest:
  b=z.read(m['path']);assert len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==m['sha256']
for m in manifest:assert sha(R/m['path'])==m['sha256']
r=dict(status='PASS',membersVerified=len(manifest),archive=str(archive),archiveSHA256=sha(archive),manifestSHA256=sha(dest/'manifest.json'))
for p in (R/'archive-receipt.json',dest/'receipt.json'):
 with p.open('x') as f:json.dump(r,f,indent=2)
print(json.dumps(r,indent=2))
