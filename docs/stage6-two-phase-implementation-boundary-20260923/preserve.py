import pathlib,json,hashlib,zipfile
R=pathlib.Path(__file__).resolve().parent;D=R.parent/'stage6-helper-cleanup-review-20260923';T=R.parent/'stage6-two-phase-contract-review-20260923';V=R.parent/'stage6-checker-v2-20260923';P=R.parent/'stage6-small-live-v2-20260923'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for x in read(T/'integrity.json')['localDiagnosisFiles']:assert sha(pathlib.Path(x['path']))==x['sha256']
assert sha(T/'REVIEW.md')==read(T/'integrity.json')['reviewSHA256']
cfg=read(V/'candidate.json');C=pathlib.Path(cfg['code']);O=pathlib.Path(cfg['original'])
for x in cfg['originalFiles']:assert sha(O/x['name'])==x['sha256']
for x in read(V/'final-verification.json')['source']:assert sha(C/x['name'])==x['sha256']
archives=[]
for folder in (D,P):
 r=read(folder/'archive-receipt.json');assert sha(pathlib.Path(r['archive']))==r['archiveSHA256'];archives.append(r)
with (R/'preservation.json').open('x') as f:json.dump(dict(status='PASS',originalHashesVerified=183,candidateHashesVerified=194,diagnosisOriginalFilesVerified=6,contractReviewUnchanged=True,archives=archives,implementationStarted=False),f,indent=2)
items=[]
for prefix,root in (('boundary',R),('approved-contract-review',T),('diagnosis',D)):
 for p in root.iterdir():
  if p.is_file():items.append((prefix+'/'+p.name,p))
approval=pathlib.Path(r'C:\Users\jonny\.codex\attachments\f428fd27-6ffa-4070-b4a2-4a5fd86152b3\Pasted text.txt');items.append(('owner-approval.txt',approval))
items.sort();manifest=[dict(path=n,bytes=p.stat().st_size,sha256=sha(p)) for n,p in items]
dest=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 TWO PHASE CONTRACT PRESERVATION 20260923');dest.mkdir(exist_ok=False)
with (dest/'manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
archive=dest/'evidence.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for n,p in items:z.write(p,n)
with zipfile.ZipFile(archive) as z:
 assert len(z.namelist())==len(manifest)
 for x in manifest:
  b=z.read(x['path']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
for x,(_,p) in zip(manifest,items):assert sha(p)==x['sha256']
receipt=dict(status='PASS',membersVerified=len(manifest),archive=str(archive),archiveSHA256=sha(archive),manifestSHA256=sha(dest/'manifest.json'))
for p in (R/'archive-receipt.json',dest/'receipt.json'):
 with p.open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt,indent=2))
