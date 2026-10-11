import hashlib, json, pathlib, zipfile

root = pathlib.Path(__file__).resolve().parent
dest = pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 COMBINED TRACE LOSS DIAGNOSIS 20260922')
dest.mkdir(exist_ok=False)
files = sorted(p for p in root.rglob('*') if p.is_file())
manifest = [{'path':p.relative_to(root).as_posix(), 'bytes':p.stat().st_size, 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
with (dest/'manifest.json').open('x', encoding='utf-8') as f:
    json.dump(manifest, f, indent=2)
archive = dest/'evidence.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
    for p in files:
        z.write(p,p.relative_to(root).as_posix())
with zipfile.ZipFile(archive) as z:
    assert len(z.namelist()) == len(manifest)
    for item in manifest:
        data=z.read(item['path'])
        assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']
for item in manifest:
    assert hashlib.sha256((root/item['path']).read_bytes()).hexdigest()==item['sha256']
receipt={'status':'PASS','membersVerified':len(manifest),'archive':str(archive),'archiveSHA256':hashlib.sha256(archive.read_bytes()).hexdigest(),'manifestSHA256':hashlib.sha256((dest/'manifest.json').read_bytes()).hexdigest()}
for p in [dest/'receipt.json',root/'archive-receipt.json']:
    with p.open('x',encoding='utf-8') as f: json.dump(receipt,f,indent=2)
print(json.dumps(receipt,indent=2))
