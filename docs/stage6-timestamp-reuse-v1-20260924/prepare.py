"""Manifest-bounded preservation and offline-only successor preparation."""
import pathlib,json,hashlib,shutil,datetime
R=pathlib.Path(__file__).parent
D=R.parent
P=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\a34f91e1db274bf78fc5a80e2a9d417c\code')
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\timestamp-reuse-v1-20260924\code')
def load(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def rec(p):
 p=pathlib.Path(p);s=p.stat();assert not s.st_file_attributes&0x400
 h=sha(p);t=p.stat();assert (s.st_size,s.st_mtime_ns)==(t.st_size,t.st_mtime_ns)
 return dict(path=str(p),sha256=h,bytes=s.st_size,mtimeNs=s.st_mtime_ns)
def write(p,v):
 with pathlib.Path(p).open('x',encoding='utf8') as f:json.dump(v,f,indent=2)
if __name__=='__main__':
 assert not C.exists()
 records={}
 def keep(p,expected=None):
  r=rec(p)
  if expected:assert r['sha256']==expected['sha256'],str(p)
  records[str(p)]=r
 for x in load(D/'stage6-final-measurement-v3-20260924'/'before.json')['inputs']:keep(x['path'],x)
 for x in load(D/'stage6-final-measurement-v3-20260924'/'candidate-artifact-manifest.json')['files']:keep(x['path'],x)
 for x in load(D/'stage6-attribution-run-20260924'/'preflight.json')['candidate']['artifacts']:keep(x['path'],x)
 for name in ['stage6-attribution-run-20260924','stage6-timestamp-reuse-review-20260924','stage6-precise-overhead-20260924','stage6-reference-precision-20260924','stage6-final-measurement-v3-20260924']:
  for p in sorted((D/name).iterdir()):
   if p.is_file():keep(p)
 keep(P/'cleanup_checker.py',dict(sha256='e6fbefd3fd463c6c8e09d0e8273a81b46ee2806515cae05e7837ea905a3e69d6'))
 write(R/'before.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),inputs=list(records.values()),candidate=str(C),noProtectedAccess=True))
 C.mkdir(parents=True);(C.parent/'build-temp').mkdir()
 for p in sorted(P.glob('*.hpp')):shutil.copy2(p,C/p.name)
 for name in ['authority_trace_v3.cpp','startup_trace.cpp','loss_measurement_fixture_v3.cpp']:shutil.copy2(P/name,C/name)
 write(C/'semantic-binding-v1.json',dict(schema='j6.lifecycle.callback-body-completion.v1',status='OFFLINE_ONLY_NOT_LIVE_ELIGIBLE',completionSource='existing CallbackScope end',includes=['callback body','handled exceptions','body-local destruction'],excludes=['timer bookkeeping','diagnostic publication','callback return'],historicalValuesInterchangeable=False,capacity=16384,producer='one callback thread per recorder',export='only after producer joined',protectedAccess=False,liveETW=False,finalOverheadQualified=False))
 print(json.dumps(dict(preserved=len(records),candidate=str(C))))
