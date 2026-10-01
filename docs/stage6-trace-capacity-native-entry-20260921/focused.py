import pathlib,json,sys,subprocess,uuid,hashlib,shutil
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'plan.json').read_text())['code']);sys.path.insert(0,str(C))
from trace_segments import verify
checks=[]
def check(name,value):
 checks.append(dict(name=name,pass_=bool(value)))
 if not value:raise AssertionError(name)
for name,count,limit,inject,byteLimit,passes in [('near',19,20,0,4096,True),('exact',20,20,0,4096,True),('overflow',21,20,0,4096,False),('writer',20,20,1,4096,False),('disk-full',20,20,2,4096,False),('segment-create',20,20,3,4096,False),('storage-bound',20,20,0,64,False)]:
 root=C/('sink-'+name+'-'+uuid.uuid4().hex);root.mkdir()
 p=subprocess.run([str(C/'J6SinkTest.exe'),str(root),str(count),str(limit),str(inject),str(byteLimit)],capture_output=True,timeout=10)
 m=json.loads((root/'sink-result.json').read_text());(root/'startup-events.json').write_text(json.dumps(m))
 check(name+' exit',(p.returncode==0)==passes);check(name+' fault',(m['fault']==0)==passes)
 if passes:
  v=verify(root);check(name+' records',v['records']==count);check(name+' segmentation',v['segments']>1)
  if name=='exact':
   segment=next(root.glob('trace-*.jsonl'));original=segment.read_bytes();segment.write_bytes(original+b'bad')
   try:verify(root)
   except AssertionError:checks.append(dict(name='segment verification rejects tampering',pass_=True))
   else:raise AssertionError('tamper accepted')
   segment.write_bytes(original);verify(root)
 else:
  try:verify(root)
  except AssertionError:checks.append(dict(name=name+' verifier rejects',pass_=True))
  else:raise AssertionError('failed trace accepted')
(R/'sink-tests.json').write_text(json.dumps(checks,indent=2));print('sink assertions',len(checks),'PASS')
