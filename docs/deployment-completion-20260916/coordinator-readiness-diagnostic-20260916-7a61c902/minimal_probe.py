"""Observational reproduction only. No implementation changes, retries or fault injection.

Six coordinator-only starts, then the exact pre-failure stop/next-coordinator
sequence once. Stops before issuing the next restart authorization. The original
read and cleanup methods run unchanged. sys.settrace captures exceptions before
harness.read can swallow them; never records frame locals/configuration/tokens.
"""
from pathlib import Path
import datetime as dt,hashlib,json,os,sys,time,traceback
D=Path(__file__).resolve().parent;R=D.parents[2]
sys.path.insert(0,str(R));sys.path.insert(0,str(R/'tests/lifecycle_stage4'))
from fixtures import RestartCampaign
data={'purpose':'minimal readiness diagnostic, not acceptance','started':time.time(),'observations':[], 'trials':[], 'cleanup':[], 'paid_calls':0,'production_operations':0,'source_changes':False,'injected_faults':False,'full_suite':False}
def save():(D/'minimal-result.json').write_text(json.dumps(data,indent=2),encoding='utf8')
def record(kind,**fields):
 data['observations'].append({'at':time.time(),'monotonic_ns':time.perf_counter_ns(),'kind':kind,**fields});save()
c=RestartCampaign();c.path=D/'minimal-original-fixture-records.json'
data['controller_peer']=c.peer
data['environment']={k:v for k,v in c.env.items()}
data['execution']={'executable':sys.executable,'base_executable':sys._base_executable,'cwd':os.getcwd(),'argv':sys.argv,'host_context':True}
originals={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in ('tests/lifecycle_stage4/fixtures.py','tests/lifecycle_stage1/harness.py','stage4_runtime.py','tests/lifecycle_stage2/pipe_transport.py','tests/lifecycle_stage2/bootstrap.py')}
data['before_source_hashes']=originals;save()
def trace(frame,event,arg):
 filename=frame.f_code.co_filename.replace('\\','/')
 if filename.endswith('/lifecycle_stage1/harness.py') and frame.f_code.co_name=='read' and Path(frame.f_locals['path']).name.startswith('coordinator-'):
  path=str(frame.f_locals['path'])
  if event=='call':record('read_enter',path=path)
  elif event=='return':record('read_return',path=path,result_type=type(arg).__name__,is_none=arg is None)
  elif event=='exception':
   et,ex,tb=arg;record('original_read_exception',path=path,error=et.__name__,errno=getattr(ex,'errno',None),winerror=getattr(ex,'winerror',None),source=filename,line=frame.f_lineno,traceback=''.join(traceback.format_exception(et,ex,tb)))
  return trace
 if filename.endswith('/lifecycle_stage4/fixtures.py') and frame.f_code.co_name=='coordinator':
  if event=='line' and frame.f_lineno in (1021,1022,1023):record('coordinator_boundary',line=frame.f_lineno,pid=frame.f_locals['proc'].pid)
  return trace
 return None
def peer_observation(item):
 p=item['process'];v={'pid':p.pid,'launch_command':p.args,'namespace':item['root'].name,'ready':item.get('ready')}
 try:v['live_peer']=c.r.transport.identity(p.pid)
 except Exception as ex:v['identity_observation_error']=type(ex).__name__+': '+str(ex)
 return v
success=False
try:
 sys.settrace(trace)
 for i in range(6):
  root,identity=c.namespace();core=c.core_config(identity)
  record('trial_begin',mode='coordinator_only',trial=i+1,root=str(root))
  item=c.coordinator(root,core);data['trials'].append({'mode':'coordinator_only','trial':i+1,**peer_observation(item)})
  c.close(item);record('trial_closed',pid=item['process'].pid,exit=item['process'].returncode)
 root,identity=c.namespace();core=c.core_config(identity)
 record('trial_begin',mode='exact_before_intent_setup',root=str(root))
 old_coordinator,old_core=c.start(root,core)
 data['trials'].append({'mode':'before_stop_coordinator',**peer_observation(old_coordinator),'core_identity':old_core})
 c.stop(root,core,old_core);c.close(old_coordinator)
 record('old_core_and_coordinator_stopped',core=old_core,coordinator=old_coordinator['ready']['identity'])
 fresh=c.core_config(identity)
 next_coordinator=c.coordinator(root,fresh,'before-intent')
 data['trials'].append({'mode':'after_stop_next_coordinator','restart_grant_issued':False,**peer_observation(next_coordinator)})
 c.close(next_coordinator)
 record('next_coordinator_closed_no_restart_issued',pid=next_coordinator['process'].pid,exit=next_coordinator['process'].returncode)
 success=True
except BaseException as ex:
 data['failure']={'error':type(ex).__name__,'traceback':traceback.format_exc()};record('probe_failed',error=type(ex).__name__)
finally:
 sys.settrace(None)
 for root,core,identity in c.cores:
  if c.r.exclusion.process_identity(identity['pid'])=={'pid':identity['pid'],'created':identity['created']}:
   try:c.stop(root,core,identity);data['cleanup'].append({'core':identity,'method':'original authenticated stop','result':'exited'})
   except Exception as ex:data['cleanup'].append({'core':identity,'result':'retained','error':type(ex).__name__,'traceback':traceback.format_exc()})
 for item in c.coordinators:
  p=item['process'];entry=peer_observation(item)
  if p.poll() is None:
   try:c.close(item);entry['method']='original authenticated close'
   except Exception as ex:
    entry['original_cleanup_failure']={'error':type(ex).__name__,'traceback':traceback.format_exc()}
    # Observe the existing 120-second service deadline, never repair item['ready'],
    # reauthenticate, kill, delete evidence or grant new cleanup authority here.
    until=time.monotonic()+125
    while p.poll() is None and time.monotonic()<until:
     save();time.sleep(.25)
    entry['method']='observed existing idle deadline after original cleanup failure'
  entry['exit']=p.poll();entry['exited']=p.poll() is not None
  if p.poll() is not None:
   for label in ('stdout','stderr'):
    content=getattr(p,label).read();name=f'coordinator-{p.pid}-{label}.log';(D/name).write_text(content,encoding='utf8');entry[label]={'file':name,'bytes':len(content.encode())}
  data['cleanup'].append(entry);save()
 data['roots']=[str(x) for x in c.roots]
 data['all_test_coordinators_exited']=all(x['process'].poll() is not None for x in c.coordinators)
 data['all_recorded_test_cores_absent']=all(c.r.exclusion.process_identity(i['pid'])!={'pid':i['pid'],'created':i['created']} for _,_,i in c.cores)
 data['after_source_hashes']={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in originals}
 data['source_unchanged']=data['after_source_hashes']==originals
 data['completed']=time.time();data['success']=success;save()
 print(json.dumps({'readiness_trials':len(data['trials']),'success':success,'original_read_exceptions':sum(x['kind']=='original_read_exception' for x in data['observations']),'coordinators_exited':data['all_test_coordinators_exited'],'cores_absent':data['all_recorded_test_cores_absent'],'source_unchanged':data['source_unchanged'],'evidence':str(D/'minimal-result.json')}))
 if not success:raise SystemExit(1)
