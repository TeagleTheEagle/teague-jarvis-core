import pathlib,json,hashlib,zipfile,datetime
R=pathlib.Path(__file__).parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda b:hashlib.sha256(b).hexdigest()
live=read(R/'final-live-check.json');assert not live['matchingLive'] and not live['processes'] and not live['traces'] and live['traceExit']==0
v=read(R/'combined-checker-final.json');assert v['status']=='PASS' and not v['primaryFailure']
integrity=read(R/'final-source-reconciliation.json');assert integrity['originalCandidateHashes']==84 and integrity['priorArchiveMembers']==206
final=pathlib.Path(read(R/'candidate-v6.json')['code']);O=pathlib.Path(read(R/'candidate.json')['original'])
for root,n in ((O,'baseline-source.json'),(final,'hardening-hashes.json')):
 for x in read(root/n):assert sha((root/x['name']).read_bytes())==x['sha256']
tests=next(final.glob('hardening-tests-*/result.json'));tr=read(tests);assert tr['tests']==117 and tr['failed']==tr['errors']==tr['skipped']==0
paths=[]
def add(name,p):
 p=pathlib.Path(p)
 assert p.is_file() and not p.lstat().st_file_attributes&0x400
 assert p.name.casefold() not in {'.env','credentials.json','secrets.json'}
 paths.append((name,p))
for p in sorted(R.iterdir()):
 if p.is_file():add('report/'+p.name,p)
for version,n in enumerate(['candidate.json']+['candidate-v'+str(i)+'.json' for i in range(2,7)],1):
 c=pathlib.Path(read(R/n)['code'])
 for p in sorted(c.iterdir()):
  if p.is_file():add('candidate-v'+str(version)+'/'+p.name,p)
 for d in sorted(c.iterdir()):
  if not d.is_dir() or d.lstat().st_file_attributes&0x400:continue
  if d.name.startswith(('hardening-tests-','sampler-tests-','queue-tests-')):
   # Do not traverse disposable unit-test fixtures/reparse directories.
   for p in sorted(d.iterdir()):
    if p.is_file() and p.suffix in ('.json','.txt'):add('tests-v'+str(version)+'/'+d.name+'/'+p.name,p)
  elif d.name.startswith('hardening-'):
   # All raw combined evidence is at the run root; temp contains no retained evidence.
   for p in sorted(d.iterdir()):
    if p.is_file():add('runs-v'+str(version)+'/'+d.name+'/'+p.name,p)
prior=read(R.parent/'stage6-large-correlation-20260920'/'archive-verification.json');P=pathlib.Path(prior['path'])
for n in ('evidence.zip','archive-manifest.json','archive-verification.json'):add('preserved-prior-archive/'+n,P/n)
assert len({n for n,p in paths})==len(paths)
rows=[]
for n,p in paths:
 s=p.stat();rows.append(dict(name=n,source=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(p.read_bytes())))
raw=(json.dumps(dict(kind='BOUNDED_DIAGNOSTIC_INFRASTRUCTURE_VALIDATION_NOT_STAGE6_ACCEPTANCE',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=rows),sort_keys=True,indent=2)+'\n').encode()
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 TARGETED DIAGNOSTIC HARDENING 20260920');A.mkdir(exist_ok=False)
with (A/'archive-manifest.json').open('xb') as f:f.write(raw)
with zipfile.ZipFile(A/'evidence.zip','x',zipfile.ZIP_DEFLATED) as z:
 for x in rows:
  b=pathlib.Path(x['source']).read_bytes();assert sha(b)==x['sha256'];z.writestr(x['name'],b)
 z.writestr('archive-manifest.json',raw)
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==len(rows)+1
 for x in rows:assert sha(z.read(x['name']))==x['sha256']
 assert z.read('archive-manifest.json')==raw
for x in rows:
 p=pathlib.Path(x['source']);s=p.stat();assert s.st_size==x['bytes'] and s.st_mtime_ns==x['mtime_ns'] and sha(p.read_bytes())==x['sha256']
with (A/'REPORT.md').open('xb') as f:f.write((R/'REPORT.md').read_bytes())
assert sha((A/'REPORT.md').read_bytes())==sha((R/'REPORT.md').read_bytes())
out=dict(status='VERIFIED',path=str(A),members=len(rows)+1,zipSHA256=sha((A/'evidence.zip').read_bytes()),manifestSHA256=sha(raw),archiveBytes=(A/'evidence.zip').stat().st_size,sourceFilesReverified=len(rows),finalCandidate=str(final),disposition='DIAGNOSTIC_INFRASTRUCTURE_VALIDATED',protectedBaselineAuthorized=False)
for root in (A,R):
 with (root/'archive-verification.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out))
