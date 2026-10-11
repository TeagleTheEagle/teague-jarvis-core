import json,hashlib,zipfile,os,ast,datetime
from pathlib import Path
R=Path(__file__).parent;pre=json.loads((R/'preflight.json').read_text());C=Path(pre['code']);run=Path(json.loads((R/'run.json').read_text())['path'])
A=Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 SMALL COMBINED 20260922')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
allchecks=pre['checks']+json.loads((R/'candidate-frozen.json').read_text())['files']+json.loads((R/'adapter-frozen.json').read_text())['files']
for x in allchecks:assert sha(Path(x['path']))==x['sha256'],x['path']
state=json.loads((R/'preservation-after.json').read_text());host=R/'final'/state['hostRun']/'final-host-state.json'
assert json.loads(host.read_text())['status']=='PASS'
interface=json.loads((R/'combined-interface.json').read_text());assert interface['verificationStatus']=='PASS' and interface['acceptanceSealed'] is False
assert json.loads((R/'combined-tests-v2.json').read_text())['passed']==31
for p in R.glob('*.py'):ast.parse(p.read_text())
sources=[]
bases=[('review',R),('live-run',run)]
for n in ('combined-tests.json','combined-tests-v2.json'):bases.append((n[:-5]+'-fixtures',Path(json.loads((R/n).read_text())['fixtureRoot'])))
for prefix,base in bases:
 for p in sorted(base.rglob('*')):
  if p.is_file():
   assert not p.is_symlink() and p.name!='.env' and '__pycache__' not in p.parts
   sources.append((prefix+'/'+p.relative_to(base).as_posix(),p))
for p in sorted(C.iterdir()):
 if p.is_file():
  assert p.name!='.env' and not p.is_symlink();sources.append(('candidate/'+p.name,p))
for p in (R.parent/'stage6-creator-image-20260922/DESIGN.md',R.parent/'stage6-acceptance-amendment-20260921/CONTRACT.md'):
 sources.append(('reference/'+p.parent.name+'-'+p.name,p))
sources.append(('review/REPORT.md',R/'REPORT.md'));member_count=len(sources)+1
with (R/'REPORT.md').open('x',encoding='utf8') as f:f.write((R/'REPORT-DRAFT.md').read_text().replace('{archive_members}',str(member_count)));f.flush();os.fsync(f.fileno())
rows=[dict(name=n,source=str(p),bytes=p.stat().st_size,sha256=sha(p)) for n,p in sources]
assert not A.exists();A.mkdir()
save(A/'manifest.json',dict(schema='stage6-small-combined-archive-v1',run=str(run),files=rows,combinedAcceptance='Pending independent verification and final sidecar',interfaceSHA256=sha(R/'combined-interface.json')))
with (A/'evidence.zip').open('xb') as stream:
 with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as z:
  for x in rows:z.write(x['source'],x['name'])
  z.write(A/'manifest.json','manifest.json')
 stream.flush();os.fsync(stream.fileno())
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==len(set(z.namelist()))==member_count
 assert z.read('manifest.json')==(A/'manifest.json').read_bytes()
 for x in rows:
  b=z.read(x['name']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']==sha(Path(x['source']))
 for name in ('review/REPORT.md','review/INTERFACE.md','review/combined-interface.json'):assert name in z.namelist()
for x in allchecks:assert sha(Path(x['path']))==x['sha256']
receipt=dict(status='PASS',archive=str(A/'evidence.zip'),membersVerified=member_count,archiveBytes=(A/'evidence.zip').stat().st_size,archiveSHA256=sha(A/'evidence.zip'),manifestSHA256=sha(A/'manifest.json'),reportSHA256=sha(R/'REPORT.md'))
save(R/'archive-verification.json',receipt);save(A/'archive-verification.json',receipt)
assert sha(R/'archive-verification.json')==sha(A/'archive-verification.json')
seal=dict(schema='stage6-small-combined-acceptance-v1',status='SMALL_COMBINED_VALIDATED',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),run=str(run),archiveSHA256=receipt['archiveSHA256'],manifestSHA256=receipt['manifestSHA256'],archiveReceiptSHA256=sha(R/'archive-verification.json'),reportSHA256=receipt['reportSHA256'],interfaceSHA256=sha(R/'combined-interface.json'),sourcePreservationSHA256=sha(R/'preservation-after.json'),cleanupSHA256=sha(host),frozenCheckerSHA256=state['checkerSHA256'],nextGateAuthorized=False)
save(R/'acceptance-seal.json',seal);save(A/'acceptance-seal.json',seal)
assert sha(R/'acceptance-seal.json')==sha(A/'acceptance-seal.json')
save(R/'seal-verification.json',dict(status='PASS',acceptanceSealSHA256=sha(R/'acceptance-seal.json'),archiveSidecar=str(A/'acceptance-seal.json')))
print(json.dumps(dict(receipt=receipt,acceptanceSealSHA256=sha(R/'acceptance-seal.json'),status=seal['status'])))
