import pathlib,json,hashlib,shutil,uuid
R=pathlib.Path(__file__).parent;old=json.loads((R/'candidate-v2.json').read_text());O=pathlib.Path(old['code'])
for x in old['hashes']:assert hashlib.sha256((O/x['name']).read_bytes()).hexdigest()==x['sha256']
D=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';D.mkdir(parents=True)
for p in O.iterdir():
 if p.is_file() and p.name!='hardening-hashes.json':shutil.copyfile(p,D/p.name)
p=D/'bounded_sampler.py';s=p.read_text();a=s.index('   state=K.WaitForSingleObject(pi.process,CLEANUP_MS)');b=s.index('   r.update(handleState=',a)
s=s[:a]+'''   # Process signaling and Job accounting are distinct predicates. Use the
   # existing two-second cleanup budget for BOTH, rather than one instantaneous
   # Job read after an already-signaled process wait.
   cleanup_deadline=time.monotonic()+CLEANUP_MS/1000
   observations=[];acc=ACCOUNT();q=False;state=258
   while True:
    state=K.WaitForSingleObject(pi.process,0)
    q=K.QueryInformationJobObject(job,1,c.byref(acc),c.sizeof(acc),None)
    observations.append(dict(qpc=ticks(),handleState=state,jobActive=acc.active if q else None))
    if state==0 and q and acc.active==0:break
    if time.monotonic()>=cleanup_deadline:break
    time.sleep(.01) # Predicate polling inside the unchanged bounded wait.
   r['jobCleanupObservations']=observations
   r['jobActiveBeforeClose']=acc.active if q else None
   K.CloseHandle(job);job=None
   if state==258:state=K.WaitForSingleObject(pi.process,CLEANUP_MS)
'''+s[b:]
p.write_text(s)
# Direct real-process sampler checks, no UAC/VM/provider operations.
test='''import json,threading,sys,uuid
from workspace import new_run,activate_temp
from bounded_sampler import query
from evidence_support import put
root=new_run('sampler-tests-'+uuid.uuid4().hex);activate_temp(root);results=[]
for i,(case,mode) in enumerate([('normal','normal'),('slow','slow'),('hung','hung'),('exception','exception'),('cancellation','hung'),('cleanup-timeout','hung'),('crash','crash')]):
 cancel=threading.Event();timer=None
 if case=='cancellation':timer=threading.Timer(.1,cancel.set);timer.start()
 row=query(root,mode,i,cancel,cleanup_injection=case=='cleanup-timeout');row['case']=case;results.append(row)
 if timer:timer.cancel();timer.join()
 if not row.get('allExited'):break
put(root/'sampler-results.json',results)
good=len(results)==7 and results[0]['status']=='AVAILABLE' and all(x['status']=='MISSING' and x.get('allExited') and x.get('handleClosed') for x in results[1:])
print(json.dumps(dict(path=str(root),cases=len(results),passAll=good,statuses=[(x['case'],x['status']) for x in results])))
sys.exit(not good)
'''
(D/'test_sampler_real.py').write_text(test)
manifest=[dict(name=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(D.iterdir()) if p.is_file()];(D/'hardening-hashes.json').write_text(json.dumps(manifest,indent=2))
with (R/'candidate-v3.json').open('x') as f:json.dump(dict(code=str(D),previous=str(O),hashes=manifest,correction='Wait for process signal AND empty Job within existing 2000ms cleanup budget.'),f,indent=2)
print(D)
