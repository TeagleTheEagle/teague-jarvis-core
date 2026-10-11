"""One authorized offline invocation; no benchmark/source modification."""
import pathlib,sys,json,hashlib,uuid,datetime,runpy,time
R=pathlib.Path(__file__).resolve().parent
S=R.parent/'stage6-blocked-attribution-v1-20260924'
OLD=R.parent/'stage6-component-attribution-20260924'
def sha(p):
 with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def put(p,v):
 with pathlib.Path(p).open('x',encoding='utf8') as f:json.dump(v,f,indent=2,allow_nan=False)
# Verify before importing any successor code.
for rec in load(S/'final-source-freeze.json'):assert sha(rec['path'])==rec['sha256']
sys.path.insert(0,str(S))
import analyzer_v1 as a
from evidence_v1 import verify_archive,verify_census

def preserved():
 c=a.candidate();counts=[]
 for folder in [S,OLD,R.parent/'stage6-reference-precision-20260924',R.parent/'stage6-precise-overhead-20260924']:
  receipt=load(folder/'archive-receipt.json');counts.append(verify_archive(receipt['archive'],receipt['archiveSHA256']))
 checker=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\a34f91e1db274bf78fc5a80e2a9d417c\code\cleanup_checker.py')
 assert sha(checker)=='e6fbefd3fd463c6c8e09d0e8273a81b46ee2806515cae05e7837ea905a3e69d6'
 assert a.canonical(a.contract())==a.canonical(load(S/'contract-v1.json'))
 return dict(candidate=c,archiveMembers=counts,checker=dict(path=str(checker),sha256=sha(checker)),analyzerSHA256=sha(S/'analyzer_v1.py'))

class OutputPaths:
 def __init__(self,fixture,raw):self.fixture=fixture;self.raw=raw
 def __truediv__(self,name):
  if name=='J6AttributionFixture.exe':return self.fixture/name
  if name=='raw':return self.raw
  raise RuntimeError('Unexpected path operation')
 def __str__(self):return str(self.fixture)

if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='prepare':
  verify_census(load(R/'preflight-census.json'));p=preserved()
  run=uuid.uuid4().hex;w=pathlib.Path(a.run_workspace(run));assert not w.exists();w.mkdir()
  for part in [w,*w.parents]:
   if part.exists():assert not part.stat().st_file_attributes&0x400
  b=a.make_binding(run,str(w),p['candidate']);put(w/'binding.json',b)
  h=a.digest(a.canonical(b));a.validate_binding(b,run,str(w),h,p['candidate'])
  put(R/'run-identity.json',dict(runId=run,workspace=str(w),bindingSHA256=h,bindingFileSHA256=sha(w/'binding.json'),driverSHA256=sha(__file__)))
  put(R/'preflight.json',p)
  print(json.dumps(dict(status='PREFLIGHT_PASS',runId=run,workspace=str(w),bindingSHA256=h,archiveMembers=p['archiveMembers'])))
 elif mode=='run':
  ident=load(R/'run-identity.json');w=pathlib.Path(ident['workspace']);assert sha(__file__)==ident['driverSHA256']
  p=preserved();b=load(w/'binding.json');a.validate_binding(b,ident['runId'],str(w),ident['bindingSHA256'],p['candidate'])
  assert sha(w/'binding.json')==ident['bindingFileSHA256']
  assert sorted(x.name for x in w.iterdir())==['binding.json']
  verify_census(load(R/'preflight-census.json'))
  sys.path.insert(0,str(OLD));ns=runpy.run_path(str(OLD/'run.py'),run_name='unchanged_original_launcher');sys.path.pop(0)
  launch=ns['launch'];assert launch.__code__.co_filename==str(OLD/'run.py')
  fixture=pathlib.Path(p['candidate']['fixtureWorkspace']);launch.__globals__['W']=OutputPaths(fixture,w)
  put(R/'launch-once.json',dict(runId=ident['runId'],utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),mode='attribution',callsAllowed=1,retries=0))
  start=time.monotonic()
  try:
   launch('attribution')
   raw=(w/'attribution.jsonl').read_bytes();exit_bytes=(w/'attribution-exit.json').read_bytes();e=a.strict_json(exit_bytes)
   rows=a.parse_rows(raw)
   receipt=dict(schema='j6.blocked-attribution.execution.v1',runId=ident['runId'],bindingSHA256=ident['bindingSHA256'],rawSHA256=a.digest(raw),exitSHA256=a.digest(exit_bytes),blocks=40,warmupPerArm=20000,warmupEvidence=a.contract()['warmupEvidence'],retries=0,replacements=0,extensions=0,referencePhases=0,interrupted=False,APIError=False,status='COMPLETE')
   a.validate_execution(e,receipt,b,raw,exit_bytes);put(w/'receipt.json',receipt)
   put(R/'execution.json',dict(status='COMPLETE',blocks=40,trials=200,measuredCallbacks=200000000,warmupCallbacks=4000000,warmupEvidence='Pinned source/run declaration; not emitted per arm',elapsedSeconds=time.monotonic()-start,fixtureElapsedSeconds=e['elapsedSeconds'],runId=ident['runId'],retries=0))
   print(json.dumps(load(R/'execution.json')))
  except BaseException as error:
   put(R/'first-failure.json',dict(error=repr(error),elapsedSeconds=time.monotonic()-start,retries=0,permanentlyRejected=True));raise
 else:raise SystemExit('Unknown action')
