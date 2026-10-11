import pathlib,json,zipfile,os,shutil,datetime
from verification import *
R=pathlib.Path(__file__).parent;P=R.parent/'stage6-protected-integration-20260920'
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 PROTECTED COLLECTOR INTEGRATION 20260920')
receipt=dict(zipSHA256='63e10c9ee43c7eb310fe98fd9f7667fdca20281c14e434ae7df4111677173482',manifestSHA256='40d118d007e9287686c61997421d53f8ff31c4da5637b79b20d4b52dfb7d0ff9',members=1333)
m=verify_archive(A,receipt);index={x['name']:x for x in m['files']}
with zipfile.ZipFile(A/'evidence.zip') as z:
 plan=json.loads(z.read('report/candidate.json'));frozen=json.loads(z.read('report/candidate-source.json'))
C=pathlib.Path(plan['code']);assert C==pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\1c1f5d0c390b42cc9ba9f4f6221dabc6\code')
verify_hash(C/'baseline-source.json',index['candidate/baseline-source.json']['sha256']);count=verify_candidate(C,frozen)
cal,other=verify_calibration([(P/'calibration.json',index['report/calibration.json']['sha256']),(C/'calibration.json',index['candidate/calibration.json']['sha256'])]);assert cal==other
S=pathlib.Path(cal['source']);assert S==C/'large-synthetic'
actual=[]
for directory,dirs,names in os.walk(S,followlinks=False):
 for name in dirs+names:
  p=pathlib.Path(directory)/name
  if p.lstat().st_file_attributes&0x400:raise ValueError('Reparse in current synthetic dataset')
 for name in names:actual.append((pathlib.Path(directory)/name).relative_to(S).as_posix())
assert sorted(actual)==sorted(x['path'] for x in cal['created'])
for x in cal['created']:
 s=(S/x['path']).lstat();assert s.st_size==x['bytes'] and s.st_mtime_ns==x['mtime_ns']
assert shutil.disk_usage(C).free>2**30
with (R/'candidate.json').open('x') as f:json.dump(plan,f,indent=2)
shutil.copyfile(P/'pre_live.ps1',R/'pre_live.ps1')
out=dict(status='PASS_PENDING_HOST_CHECK',candidateHashes=count,calibrationHashes='UNCHANGED',archiveMembers=1333,archive=receipt,syntheticFiles=len(actual),syntheticBytes=cal['totalBytes'],metadata='UNCHANGED',generatedHistoricalPathsOpened=0,priorRunNames=sorted(p.name for p in C.glob('protected-*') if p.is_dir()),protectedAccess=False,productionChanged=False,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
with (R/'preflight.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:x for k,x in out.items() if k!='priorRunNames'}))
