import pathlib,json,hashlib,zipfile,shutil,datetime
R=pathlib.Path(__file__).parent;P=R.parent/'stage6-protected-integration-20260920';plan=json.loads((P/'candidate.json').read_text());C=pathlib.Path(plan['code'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((P/'archive-verification.json').read_text());A=pathlib.Path(receipt['path'])
assert receipt['zipSHA256']=='63e10c9ee43c7eb310fe98fd9f7667fdca20281c14e434ae7df4111677173482'
assert sha(A/'evidence.zip')==receipt['zipSHA256'];assert sha(A/'archive-manifest.json')==receipt['manifestSHA256']
m=json.loads((A/'archive-manifest.json').read_text())
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==1333
 for x in m['files']:
  assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256']
  p=pathlib.Path(x['source']);assert p.is_relative_to(C) or p.is_relative_to(P)
  assert sha(p)==x['sha256'],'Archived source changed: '+str(p)
 assert z.read('archive-manifest.json')==(A/'archive-manifest.json').read_bytes()
frozen=json.loads((P/'candidate-source.json').read_text());assert frozen==json.loads((C/'baseline-source.json').read_text())
for x in frozen:assert sha(C/x['name'])==x['sha256']
cal=json.loads((P/'calibration.json').read_text());S=pathlib.Path(cal['source']);assert S==C/'large-synthetic'
assert sha(P/'calibration.json')==sha(C/'calibration.json')
actual=sorted(p.relative_to(S).as_posix() for p in S.rglob('*') if p.is_file())
assert actual==sorted(x['path'] for x in cal['created'])
for x in cal['created']:
 p=S/x['path'];s=p.lstat();assert not s.st_file_attributes&0x400 and s.st_size==x['bytes'] and s.st_mtime_ns==x['mtime_ns']
assert shutil.disk_usage(C).free>2**30
before=json.loads((P/'frozen-before.json').read_text())
for x in before['applicationHashes']:assert sha(R.parent.parent/x['path'])==x['expected']
with (R/'candidate.json').open('x') as f:json.dump(plan,f,indent=2)
shutil.copyfile(P/'pre_live.ps1',R/'pre_live.ps1')
out=dict(status='PASS_PENDING_HOST_CHECK',candidateHashes=len(frozen),archiveMembers=1333,archive=receipt,calibrationUnchanged=True,syntheticBytes=cal['totalBytes'],syntheticFiles=len(actual),syntheticMetadataPreserved=True,applicationHashes=len(before['applicationHashes']),DfreeBytes=shutil.disk_usage(C).free,priorRunNames=sorted(p.name for p in C.glob('protected-*') if p.is_dir()),protectedAccess=False,productionChanged=False,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
with (R/'preflight.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ('priorRunNames','archive')}))
