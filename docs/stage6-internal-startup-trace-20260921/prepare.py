import pathlib,json,hashlib,zipfile,uuid,shutil
R=pathlib.Path(__file__).parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=R.parent/'stage6-call-tracing-20260921'
receipt=read(old/'archive-verification.json');A=pathlib.Path(receipt['path'])
assert sha(A/'evidence.zip')==receipt['zipSHA256']
assert sha(A/'archive-manifest.json')==receipt['manifestSHA256']
with zipfile.ZipFile(A/'evidence.zip') as z:
 rows=read(A/'archive-manifest.json')['files'];assert len(rows)+1==len(z.namelist())==262
 assert z.read('archive-manifest.json')==(A/'archive-manifest.json').read_bytes()
 for x in rows:assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256']==sha(pathlib.Path(x['source']))
original=read(old/'plan.json'); prior=read(old/'followup-plan.json')
S=pathlib.Path(original['source']); C=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';C.mkdir(parents=True)
for x in original['sourceHashes']:
 p=S/x['name'];assert sha(p)==x['sha256'];shutil.copy2(p,C/x['name'])
for x in prior['diagnosticHashes']:assert sha(pathlib.Path(prior['code'])/x['name'])==x['sha256']
failed=read(R.parent/'stage6-preserved-probe-sampler-diagnosis-20260921'/'freeze.json')
for x in failed['rawFiles']:
 p=pathlib.Path(x['path']);assert sha(p)==x['sha256'] and p.stat().st_mtime_ns==x['mtime_ns']
run='startup-'+uuid.uuid4().hex;(C/run/'temp').mkdir(parents=True)
plan=dict(code=str(C),run=run,root=str(C/run),source=str(S),sourceHashes=original['sourceHashes'],previousArchive=receipt,priorDiagnostic=prior,protectedAccess=False)
with (R/'plan.json').open('x') as f:json.dump(plan,f,indent=2)
print(json.dumps({k:plan[k] for k in ('code','run','root')}))
