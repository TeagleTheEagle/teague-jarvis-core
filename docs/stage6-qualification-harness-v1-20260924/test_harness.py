from prepare import *
from analyze import *
import subprocess,time,tempfile,copy
checks=0
def check(x,label):
 global checks
 if not x:raise AssertionError(label)
 checks+=1
def rejects(fn,label):
 try:fn()
 except (ValueError,KeyError,TypeError):check(True,label);return
 raise AssertionError(label)
exe=C/'J6FinalQualification.exe';before=sha(exe)
attempt=len(list(R.glob('selftest*-exit.json')))+1
for label,args,expected in [('selftest',['--selftest'],0),('wrong-protocol',['--qualify','not-the-protocol'],90),('wrong-mode',['--not-a-mode'],90)]:
 start=time.monotonic()
 with (R/f'{label}-{attempt}.stdout').open('xb') as out,(R/f'{label}-{attempt}.stderr').open('xb') as err:
  p=subprocess.Popen([str(exe)]+args,cwd=C,stdout=out,stderr=err);code=p.wait(timeout=60)
 write(R/f'{label}-{attempt}-exit.json',dict(pid=p.pid,code=code,exited=True,seconds=time.monotonic()-start,benchmarkExecuted=False))
 check(code==expected,label)
selftest=load(R/f'selftest-{attempt}.stdout');check(selftest['status']=='PASS' and not selftest['benchmarkExecuted'],'semantic selftest')
ph=sha(C/'protocol.json')
rows=[dict(kind='header',schema='j6.final-overhead.raw.v1',protocolSHA256=ph,pid=1,created=1,tid=1,frequency=10000000)]
for b in range(60):
 for pos,arm in enumerate(['ABC','BCA','CAB','ACB','CBA','BAC'][b%6]):
  chunks=[];total=wall=0;digest=0
  for i in range(123):
   n=8192 if i<122 else 576;dt=n*(100 if arm=='A' else 102 if arm=='B' else 100);base=i*10000000
   chunks.append([i%11,(i//11)%2,n,base,0,base+dt,0,1,1,base,base+dt,7]);total+=dt;wall+=dt;digest=((digest^7)*1099511628211)&((1<<64)-1)
  rows.append(dict(kind='trial',block=b,position=pos,arm=arm,warmup=20000,callbacks=1000000,cpu100ns=total,wallTicks=wall,workloadDigest=digest,chunks=chunks))
rows.append(dict(kind='complete',blocks=60,trials=180,callbacks=180000000,warmup=3600000))
blocks=validate(rows,0,ph);check(len(blocks)==60,'fixed complete synthetic validation')
check(analyze(blocks)['numericalScreen']=='FINAL_OVERHEAD_SCREEN_PASSED','synthetic interval calculator')
check(analyze(blocks)['finalStatus']=='INCONCLUSIVE','no silent drift acceptance')
rejects(lambda:validate(rows,97,ph),'nonzero exit')
rejects(lambda:validate(rows,0,'wrong'),'protocol identity')
for field,value in [('schema','unknown'),('tid',0),('frequency',0)]:
 bad=copy.deepcopy(rows);bad[0][field]=value;rejects(lambda:validate(bad,0,ph),field)
for field,value in [('arm','X'),('warmup',0),('callbacks',999),('position',2),('cpu100ns',0),('workloadDigest',0)]:
 bad=copy.deepcopy(rows);bad[1][field]=value;rejects(lambda:validate(bad,0,ph),field)
for index,value in [(2,1),(7,99),(9,-1),(5,0)]:
 bad=copy.deepcopy(rows);bad[1]['chunks'][0][index]=value;rejects(lambda:validate(bad,0,ph),'chunk integrity')
rejects(lambda:validate(rows[:-1],0,ph),'incomplete')
rejects(lambda:verify_binding(dict(files=[dict(path=str(exe),sha256='0'*64)],protocol=str(C/'protocol.json'),protocolSHA256=ph)),'binary hash')
rejects(lambda:verify_binding(dict(files=[],protocol=str(C/'protocol.json'),protocolSHA256='0'*64)),'binding hash')
with tempfile.TemporaryDirectory(dir=C/'temp') as d:
 p=pathlib.Path(d)/'bad.jsonl';p.write_text('{broken');rejects(lambda:load_raw(p),'malformed JSON')
check(sha(exe)==before,'binary unchanged')
write(R/'offline-tests-final.json',dict(status='PASS',pythonChecks=checks,native=selftest,syntheticStatisticsOnly=True,qualificationExecuted=False))
print(json.dumps(dict(status='PASS',checks=checks,native=selftest)))
