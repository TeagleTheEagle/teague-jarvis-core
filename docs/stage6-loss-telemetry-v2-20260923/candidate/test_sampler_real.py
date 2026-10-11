import json,threading,sys,uuid
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
