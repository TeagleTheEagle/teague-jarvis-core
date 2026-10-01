"""New outer repetition only. Original fixture and launch function unchanged."""
import sys,runpy,time,json,pathlib
from context_config import R,PREV,PRECISE,FIXTURE,LIVE,load,sha,put
class OutputPaths:
 def __init__(self,raw):self.raw=raw
 def __truediv__(self,name):
  if name=='J6AttributionFixture.exe':return FIXTURE/name
  if name=='raw':return self.raw
  raise RuntimeError('Unexpected original launcher path operation: '+str(name))
 def __str__(self):return str(FIXTURE)
def validate(rows,batch):
 assert len(rows)==80
 for i in range(40):
  two=rows[2*i:2*i+2]
  assert [x['variant'] for x in two]==([0,1] if i%2==0 else [1,0])
  assert [x['position'] for x in two]==[0,1]
  for row in two:
   assert row['block']==i and row['callbacks']==1000000 and row['dispatcherCpu100ns']>0 and row['wallSeconds']>0
   assert row['name'] in ['BASELINE_DISABLED','FULL_ENABLED_REFERENCE']
 return 40
if __name__=='__main__':
 pre=load(R/'preservation-before.json');assert sha(R/'protocol.json')==pre['protocolSHA256']
 for row in pre['originalHarness']:assert sha(row['path'])==row['sha256']
 # Original module definitions only; its __main__, selftest and attribution paths never execute.
 sys.path.insert(0,str(PREV));namespace=runpy.run_path(str(PREV/'run.py'),run_name='unchanged_original_launcher');sys.path.pop(0)
 launch=namespace['launch'];assert launch.__code__.co_filename==str(PREV/'run.py')
 put(R/'repetition-driver-freeze.json',[dict(path=str(p),sha256=sha(p)) for p in sorted(R.glob('*.py'))])
 started=time.monotonic();pairs=0
 try:
  for batch in range(16):
   if time.monotonic()-started>5400:raise RuntimeError('Fixed outer time bound reached; no extra launches')
   assert sha(FIXTURE/'J6AttributionFixture.exe')==pre['fixtureSHA256']
   folder=LIVE/f'batch-{batch:02}';folder.mkdir()
   launch.__globals__['W']=OutputPaths(folder)
   print(json.dumps(dict(batchStarting=batch+1,maximumBatches=16)),flush=True)
   rows=launch('reference');pairs+=validate(rows,batch)
   identity=load(folder/'reference-exit.json')
   assert identity['exitCode']==0 and identity['waitResult']==0 and not identity['closeErrors']
   assert identity['initialProcess']['createdFILETIME']==identity['finalProcess']['createdFILETIME']
   assert identity['initialThread']['createdFILETIME']==identity['finalThread']['createdFILETIME']
   assert identity['sha256']==pre['fixtureSHA256'] and identity['cwd']==str(FIXTURE)
   print(json.dumps(dict(completedBatches=batch+1,completedPairs=pairs,elapsedSeconds=round(time.monotonic()-started,1))),flush=True)
  put(R/'execution.json',dict(status='COMPLETE',batches=16,pairs=pairs,elapsedSeconds=time.monotonic()-started,exclusions=[],retries=0,attributionVariantsExecuted=False))
 except BaseException as e:
  put(R/'execution.json',dict(status='BENCHMARK_METHOD_DEFECTIVE',completedPairs=pairs,error=repr(e),noRetry=True));raise
