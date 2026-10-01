"""Bounded diagnostic ladder case. Primary failures never overwritten."""
import pathlib,json,sys,time,subprocess,ctypes as c,ctypes.wintypes as w,traceback,os
from workspace import CODE,run_dir,activate_temp
from journal import Reader,PublisherWatch,ticks,frequency
from probe_timing import process_times,K
from controls import make_probe
root=run_dir(sys.argv[1]);activate_temp(root);phase=sys.argv[2];assert phase in 'ABCDEF'
def save(n,v):
 with (root/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
def append(n,v):
 with (root/n).open('a',encoding='utf-8') as f:f.write(json.dumps(v)+'\n')
def identify(p,role):return dict(role=role,pid=p.pid,created=process_times(p)[0])
deadline=time.monotonic()+25
while not (root/'ready.json').exists():
 if (root/'monitor-failure.json').exists() or time.monotonic()>=deadline:raise RuntimeError('Diagnostic monitor not ready')
 time.sleep(.1)
identity=json.loads((root/'ready.json').read_text(encoding='utf-8-sig'));watch=PublisherWatch(identity);reader=Reader(root/'heartbeat.jsonl',identity,liveness=watch.check)
samples=[];measured=[];tracked=[];primary=None;worker=None;cleanup=[];probes=[];handle_rows=[]
pwsh=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
resource=subprocess.Popen([pwsh,'-NoProfile','-File',str(CODE/'resources.ps1'),'-Run',root.name],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,creationflags=0x08000000)
tracked.append(identify(resource,'resource'));save('collector-identity.json',dict(pid=os.getpid(),parentPid=os.getppid(),qpc=ticks(),phase=phase))
def health():
 if (root/'monitor-failure.json').exists():raise RuntimeError('Monitor failed')
 v=reader.poll();samples.append(dict(v,qpc=ticks()))
 if v['age']>=10 or not reader.last.get('subscriberHealthy') or reader.last.get('queueFailure'):raise RuntimeError('Monitor health rejected')
def warning(v):append('warnings.jsonl',v)
began=ticks();campaign_deadline=began/frequency()+165
try:
 if phase!='A':
  worker=subprocess.Popen([sys._base_executable,'-B',str(CODE/'ladder_worker.py'),root.name,phase],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,creationflags=0x08000000)
  tracked.append(identify(worker,'workload'))
 save('tracked-helpers.json',tracked)
 variants=['C_D','A_D','C_D','B_D','C_D','D_D'];i=0
 while (phase=='A' and (ticks()-began)/frequency()<30) or (worker is not None and worker.poll() is None):
  health()
  if ticks()/frequency()+13.6>=campaign_deadline:raise RuntimeError('Case workload bound reached')
  item=make_probe(variants[i%len(variants)]);i+=1;measured.append(item);append('launches.jsonl',dict(pid=item.process.pid,created=item.row['initialKernelTimes'][0],control=item.row['control'],qpc=item.row['launchRequestedQpc']))
  code=item.wait_approved(health,warning,campaign_deadline)
  if code:raise RuntimeError('Probe nonzero exit')
  ts=process_times(item.process)
  probes.append(dict(pid=item.process.pid,created=ts[0],kernel_exit_filetime=ts[1],exit=code,start_qpc=item.row['launchRequestedQpc'],end_qpc=ticks(),retained_handle=True,handle_signalled=True))
  time.sleep(.2)
 if worker:
  _,err=worker.communicate(timeout=1);save('worker-exit.json',dict(**identify(worker,'workload'),exit=worker.returncode,stderr=err.decode(errors='replace'),times=process_times(worker),qpc=ticks()))
  if worker.returncode:raise RuntimeError('Diagnostic subset workload failed')
 health()
except BaseException:
 primary=dict(qpc=ticks(),traceback=traceback.format_exc());save('primary-failure.json',primary)
finally:
 save('producer-closed.json',dict(run=identity['run'],qpc=ticks(),new_probes_forbidden=True));(root/'workload-stop').touch()
 if worker and not (root/'worker-exit.json').exists():
  try:
   _,err=worker.communicate(timeout=15);save('worker-exit.json',dict(**identify(worker,'workload'),exit=worker.returncode,stderr=err.decode(errors='replace'),times=process_times(worker),qpc=ticks()))
  except BaseException:cleanup.append(dict(role='worker',error=traceback.format_exc()))
 # This bounded cleanup observation does not extend either acceptance/observer deadline.
 for item in measured:
  p=item.process;state=K.WaitForSingleObject(int(p._handle),0)
  record=dict(role='probe',pid=p.pid,created=item.row['initialKernelTimes'][0],cleanupBeginQpc=ticks(),initialState=state)
  end=time.monotonic()+30
  while state==258 and time.monotonic()<end:time.sleep(.05);state=K.WaitForSingleObject(int(p._handle),0)
  record.update(finalState=state,cleanupObservedQpc=ticks())
  try:
   item.finish_observation();p.poll();record.update(times=process_times(p),exit=p.returncode)
   handle_rows.append(dict(pid=p.pid,times=record['times'],exit=p.returncode))
  except BaseException:record['error']=traceback.format_exc()
  cleanup.append(record)
 save('probe-timings.json',[x.row for x in measured]);save('probes.json',probes);save('retained-handle-verification.json',handle_rows);save('collector-samples.json',samples)
 good=all(x.get('finalState')==0 and x.get('exit')==0 for x in cleanup if x['role']=='probe') and len(handle_rows)==len(measured)
 proof=dict(run=identity['run'],status='LIVE_MONITOR_HEALTHY' if primary is None and good else 'FAILED_CLOSED',error=primary,qpc=ticks(),allHandlesExited=good,acceptance=False,identities=[dict(pid=x['pid'],created=x['times'][0],exited=x['times'][1],exit=x['exit']) for x in handle_rows])
 save('collector-finished.json',proof);reader.close()
 end=time.monotonic()+60
 while K.WaitForSingleObject(watch.handle,0)==258 and time.monotonic()<end:time.sleep(.05)
 code=w.DWORD();K.GetExitCodeProcess(watch.handle,c.byref(code));save('monitor-exit.json',dict(identity=identity,exit_code=code.value,handleState=K.WaitForSingleObject(watch.handle,0)));watch.close()
 try:
  _,err=resource.communicate(timeout=10);save('resource-exit.json',dict(**identify(resource,'resource'),exit=resource.returncode,stderr=err.decode(errors='replace'),times=process_times(resource)))
 except BaseException:cleanup.append(dict(role='resource',error=traceback.format_exc()))
 for item in measured:
  if K.WaitForSingleObject(int(item.process._handle),0)==0:item.process._handle.Close();cleanup.append(dict(role='probe-handle-close',pid=item.process.pid,closed=True,qpc=ticks()))
 for helper in (worker,resource):
  if helper is not None and K.WaitForSingleObject(int(helper._handle),0)==0:helper._handle.Close();cleanup.append(dict(role='helper-handle-close',pid=helper.pid,closed=True,qpc=ticks()))
 save('cleanup-observations.json',cleanup)
 hard=any(x.row.get('hardDeadlineFailure') for x in measured)
 result=dict(status='HARD_DEADLINE_REPRODUCED' if hard else 'DIAGNOSTIC_FAILURE' if primary or not good or code.value else 'DIAGNOSTIC_SUBSET_COMPLETED',phase=phase,probes=len(measured),hardDeadline=hard,primary=primary,acceptance=False)
 save('diagnostic-result.json',result);print(json.dumps(result),flush=True)
 if result['status']!='DIAGNOSTIC_SUBSET_COMPLETED':sys.exit(1)
