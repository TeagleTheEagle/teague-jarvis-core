import pathlib,json,hashlib,difflib,zipfile
R=pathlib.Path(__file__).resolve().parent;cfg=json.loads((R/'candidate.json').read_text());C=pathlib.Path(cfg['code'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
previous=json.loads((R.parent/'stage6-large-small-integration-20260922/candidate.json').read_text())
for x in previous['files']:assert sha(pathlib.Path(previous['code'])/x['name'])==x['sha256'],x['name']
medium=json.loads((R.parent/'stage6-health-journal-candidate-20260922/candidate-frozen.json').read_text())['files']
for x in medium:assert sha(pathlib.Path(x['path']))==x['sha256'],x['path']
builds=list(R.glob('build-*/built-hashes.json'));latest=max(builds,key=lambda p:p.stat().st_mtime_ns)
for x in json.loads(latest.read_text()):
 if x['name']=='live.ps1':
  assert sha(C/x['name'])==sha(R/'live.ps1')
 else:assert sha(C/x['name'])==x['sha256'],x['name']
archiveRoot=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS')
historical=[]
for name,expected in [('STAGE6 SMALL LARGE INTEGRATION FAILURE 20260922 ac2f7b10','1e9de5a21ca32a4f88f5acb4b1306fe56794a6d1b3fcf3a14f7d710d9a4ef141'),('STAGE6 COMBINED TRACE LOSS DIAGNOSIS 20260922','ecea868d7ddb07faaee4691afe45a65d642b41d41287336d1233e716967540cf')]:
 p=archiveRoot/name/'evidence.zip';assert sha(p)==expected;historical.append(dict(path=str(p),sha256=expected))
diffs=R/'final-diffs';diffs.mkdir()
changed=[]
for name in ('authority_trace.cpp','startup_trace.cpp','durable_sink.hpp','trace_sink.hpp'):
 original=pathlib.Path(next(x['path'] for x in cfg['before'] if pathlib.Path(x['path']).name==name))
 before=original.read_text();after=(C/name).read_text()
 (diffs/(name+'.diff')).write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=str(original),tofile=str(C/name))),encoding='utf8')
 changed.append(dict(name=name,before=sha(original),after=sha(C/name)))
frozen=[dict(name=p.name,sha256=sha(p),bytes=p.stat().st_size) for p in sorted(C.iterdir()) if p.is_file()]
integrity=dict(previousCandidateFiles=len(previous['files']),mediumFiles=len(medium),originalCandidatesUnchanged=True,compiledSourceAndBinaryHashesUnchangedSinceFinalBuild=True,changes=changed,candidate=frozen,historicalArchives=historical)
with (R/'integrity.json').open('x') as f:json.dump(integrity,f,indent=2)
dest=archiveRoot/'STAGE6 LOSS TELEMETRY SMALL DIAGNOSTICS 20260922 f40cb16a';dest.mkdir(exist_ok=False)
items=[(p,'report/'+p.relative_to(R).as_posix()) for p in sorted(R.rglob('*')) if p.is_file()]
items += [(p,'candidate/'+p.relative_to(C).as_posix()) for p in sorted(C.rglob('*')) if p.is_file()]
assert all(p.suffix.lower()!='.env' and not p.is_symlink() for p,n in items)
manifest=[dict(path=n,bytes=p.stat().st_size,sha256=sha(p)) for p,n in items]
with (dest/'manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
archive=dest/'evidence.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for p,n in items:z.write(p,n)
with zipfile.ZipFile(archive) as z:
 assert len(z.namelist())==len(manifest)
 for x in manifest:
  b=z.read(x['path']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
for (p,n),x in zip(items,manifest):assert sha(p)==x['sha256']
receipt=dict(status='PASS',membersVerified=len(manifest),archive=str(archive),archiveSHA256=sha(archive),manifestSHA256=sha(dest/'manifest.json'))
for p in (dest/'receipt.json',R/'archive-receipt.json'):
 with p.open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(dict(integrityCounts=[len(previous['files']),len(medium)],receipt=receipt),indent=2))
