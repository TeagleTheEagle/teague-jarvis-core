import pathlib,json,hashlib,zipfile,sys,os,shutil,datetime
R=pathlib.Path(__file__).parent;D=R.parent;sys.path.insert(0,str(D/'stage6-narrow-preflight-20260920'))
from verification import verify_hash,verify_candidate
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def archive(folder):
 receipt=read(D/folder/'archive-verification.json');a=pathlib.Path(receipt['path']);raw=verify_hash(a/'archive-manifest.json',receipt['manifestSHA256']);verify_hash(a/'evidence.zip',receipt['zipSHA256']);m=json.loads(raw);files=m['files'] if isinstance(m,dict) else m
 with zipfile.ZipFile(a/'evidence.zip') as z:
  assert len(z.namelist())==receipt['members']==len(files)+1
  assert len(set(z.namelist()))==len(z.namelist())
  for x in files:assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256']
  assert z.read('archive-manifest.json')==raw
 return receipt,files
try:
 archives={};members={}
 for n in ('stage6-dry1-execution-20260920','stage6-dry2-execution-20260920','stage6-protected-integration-20260920','stage6-targeted-hardening-20260920'):
  archives[n],members[n]=archive(n)
 C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\1c1f5d0c390b42cc9ba9f4f6221dabc6\code');H=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\2ef4a4641a234b7dbfdce8db88cb1e39\code')
 oldidx={x['name']:x for x in members['stage6-protected-integration-20260920']};idx={x['name']:x for x in members['stage6-targeted-hardening-20260920']}
 verify_hash(C/'baseline-source.json',oldidx['candidate/baseline-source.json']['sha256']);count=verify_candidate(C,read(C/'baseline-source.json'))
 verify_hash(H/'hardening-hashes.json',idx['candidate-v6/hardening-hashes.json']['sha256']);hc=verify_candidate(H,read(H/'hardening-hashes.json'))
 a=verify_hash(C/'calibration.json',oldidx['candidate/calibration.json']['sha256']);b=verify_hash(D/'stage6-protected-integration-20260920'/'calibration.json',oldidx['report/calibration.json']['sha256']);assert a==b;cal=json.loads(a);S=C/'large-synthetic';assert pathlib.Path(cal['source'])==S
 actual=[]
 for directory,dirs,names in os.walk(S,followlinks=False):
  for n in dirs+names:
   p=pathlib.Path(directory)/n;assert not p.lstat().st_file_attributes&0x400
  for n in names:actual.append((pathlib.Path(directory)/n).relative_to(S).as_posix())
 assert sorted(actual)==sorted(x['path'] for x in cal['created'])
 for x in cal['created']:
  s=(S/x['path']).lstat();assert s.st_size==x['bytes'] and s.st_mtime_ns==x['mtime_ns']
 free=shutil.disk_usage(H).free;assert free>2**30
 out=dict(status='PASS_PENDING_HOST_CHECK',collector=str(C),diagnostic=str(H),collectorHashes=count,diagnosticHashes=hc,archives=archives,calibrationUnchanged=True,source=str(S),fileCount=len(actual),totalBytes=cal['totalBytes'],largestFile=max(cal['created'],key=lambda x:x['bytes']),DfreeBytes=free,protectedAccess=False,productionChanged=False,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
except BaseException as ex:
 out=dict(status='FAIL',error=repr(ex),protectedAccess=False,productionChanged=False)
 with (R/'preflight.json').open('x') as f:json.dump(out,f,indent=2)
 raise
with (R/'preflight.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k!='archives'}))
