import pathlib,json,hashlib,zipfile
R=pathlib.Path(__file__).resolve().parent;P=R.parent/'stage6-tracker-experiment-20260923'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
C=pathlib.Path(json.loads((P/'candidate.json').read_text())['code'])
rows=json.loads((P/'final-source.json').read_text())['files']
for x in rows:assert sha(C/x['name'])==x['sha256'],x['name']
archives=[]
for p in (P,R.parent/'stage6-support-verifier-20260923'):
 r=json.loads((p/'archive-receipt.json').read_text());assert sha(pathlib.Path(r['archive']))==r['archiveSHA256'];archives.append(r)
with (R/'integrity.json').open('x') as f:json.dump(dict(candidate=str(C),candidateHashesVerified=len(rows),files=rows,priorArchivesVerified=archives,implementationPerformed=False,validationRunPerformed=False,protectedAccess=False,productionChanges=False),f,indent=2)
files=sorted(p for p in R.iterdir() if p.is_file())
dest=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 CHECKER INTEGRATION REVIEW 20260923');dest.mkdir(exist_ok=False)
manifest=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in files]
with (dest/'manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
archive=dest/'evidence.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.name)
with zipfile.ZipFile(archive) as z:
 assert len(z.namelist())==len(manifest)
 for m in manifest:
  b=z.read(m['path']);assert len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==m['sha256']
for m in manifest:assert sha(R/m['path'])==m['sha256']
r=dict(status='PASS',membersVerified=len(manifest),archive=str(archive),archiveSHA256=sha(archive),manifestSHA256=sha(dest/'manifest.json'))
for p in (R/'archive-receipt.json',dest/'receipt.json'):
 with p.open('x') as f:json.dump(r,f,indent=2)
print(json.dumps(r,indent=2))
