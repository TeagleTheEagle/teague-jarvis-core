"""Diagnostic-only collector with independently retained tree handles and bounded output.
 Never seals Stage 6 acceptance. No protected data; no implicit process termination.
 """
import os,sys,json,time,traceback,pathlib,ctypes as c,ctypes.wintypes as w
from workspace import CODE,run_dir,activate_temp
from evidence_support import Ledger,Managed,TreeTracker,put
from journal import Reader,PublisherWatch,ticks,frequency
from probe_timing import Probe,K,process_times
from controls import make_probe
root=run_dir(sys.argv[1]);activate_temp(root);config=json.loads((root/'case.json').read_text());phase=config['phase'];assert phase in 'ABCDE'
ledger=Ledger(root);tree=TreeTracker();watch=None;reader=None;worker=None;resource=None;helpers=[];measured=[];samples=[];probes=[];handle_rows=[]
def save(n,v):put(root/n,v)
def secondary(stage,fn):
 try:return fn()
 except BaseException:ledger.fail(stage);return None
def health():
 if (root/'monitor-failure.json').exists():raise RuntimeError('Monitor failed')
 v=reader.poll();samples.append(dict(v,qpc=ticks()))
 if v['age']>=10 or not reader.last.get('subscriberHealthy') or reader.last.get('queueFailure'):raise RuntimeError('Monitor health rejected')
def warning(v):
 with (root/'warnings.jsonl').open('a') as f:f.write(json.dumps(v)+'\n');f.flush()
def finish_helper(m):
 r=m.finish();ledger.cleanup.append(r)
 if r['handleState']!=0 or any(not r.get(n,{}).get('eof') or r[n].get('error') for n in ('stdout','stderr')):raise RuntimeError('Incomplete helper exit/output: '+m.role)
 if r['exit']!=0:raise RuntimeError('Nonzero helper exit: '+m.role)
 return r
try:
 deadline=time.monotonic()+25
 while not (root/'ready.json').exists():
  if (root/'monitor-failure.json').exists() or time.monotonic()>=deadline:raise RuntimeError('Monitor not ready')
  time.sleep(.05)
 identity=json.loads((root/'ready.json').read_text(encoding='utf-8-sig'));watch=PublisherWatch(identity);reader=Reader(root/'heartbeat.jsonl',identity,liveness=watch.check)
 save('collector-identity.json',dict(pid=os.getpid(),parentPid=os.getppid(),qpc=ticks(),phase=phase))
 pwsh=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
 resource=Managed([pwsh,'-NoProfile','-File',str(CODE/'resources.ps1'),'-Run',root.name],root,'resource',tree)
 began=time.monotonic();campaign_deadline=ticks()/frequency()+90
 if phase!='A':
  args=([sys._base_executable,'-B',str(CODE/'ladder_worker.py'),root.name,'C'] if phase=='E' else [sys._base_executable,'-B',str(CODE/'workload.py'),root.name,dict(B='disk',C='sustained',D='Dhash')[phase],'18'])
  worker=Managed(args,root,'workload',tree)
 i=0
 while (phase=='A' and time.monotonic()-began<12) or (worker and worker.p.poll() is None):
  health()
  if ticks()/frequency()+13.6>=campaign_deadline:raise RuntimeError('Bounded diagnostic case deadline')
  # Unchanged whoami remains the principal probe; native controls are separately labelled.
  variant='C_D' if i%3 else 'D_D';item=make_probe(variant);i+=1;measured.append(item);tree.register(item.process,'probe:'+variant,[item.row['executable'],*item.row['arguments']])
  item.row['treeRegisteredQpc']=ticks()
  code=item.wait_approved(health,warning,campaign_deadline)
  if code:raise RuntimeError('Probe nonzero exit')
  ts=process_times(item.process);probes.append(dict(pid=item.process.pid,created=ts[0],kernel_exit_filetime=ts[1],exit=code,start_qpc=item.row['launchRequestedQpc'],end_qpc=ticks(),retained_handle=True,handle_signalled=True))
  if phase=='E' and i<=3:
   h=Managed([sys._base_executable,'-B',str(CODE/'trace_fixture.py'),str(root),'child-first' if i==1 else 'trace'],root,'tracehelper-'+str(i),tree);helpers.append(h)
  time.sleep(.3)
 if worker:finish_helper(worker)
 health()
except BaseException:ledger.fail('collection')
finally:
 if watch:
  secondary('producer-close',lambda:save('producer-closed.json',dict(run=identity['run'],qpc=ticks(),new_probes_forbidden=True)))
 secondary('stop-workload',lambda:(root/'workload-stop').touch())
 if worker and worker.finished is None:secondary('worker-cleanup',lambda:finish_helper(worker))
 for h in helpers:secondary('trace-helper-cleanup',lambda h=h:finish_helper(h))
 for item in measured:
  p=item.process
  def reconcile(item=item,p=p):
   start=ticks();state=int(K.WaitForSingleObject(int(p._handle),30000)) # Post-failure evidence collection only.
   item.finish_observation();p.poll();r=dict(pid=p.pid,times=process_times(p),exit=p.returncode,handleState=state,cleanupBeginQpc=start,cleanupEndQpc=ticks())
   ledger.cleanup.append(r);handle_rows.append(r)
   if state!=0:raise RuntimeError('Probe still alive after bounded cleanup observation')
   if item.row.get('independentObserverFailed'):ledger.fail('independent-observer','15-second observer failed; later exit does not erase it')
  secondary('probe-cleanup',reconcile)
 # Persist all partial rows even if an individual handle failed. Never short-circuit the walk.
 for name,value in [('probe-timings.json',[x.row for x in measured]),('probes.json',probes),('retained-handle-verification.json',handle_rows),('collector-samples.json',samples)]:secondary(name,lambda name=name,value=value:save(name,value))
 allprobes=bool(measured) and len(handle_rows)==len(measured) and all(r['handleState']==0 for r in handle_rows)
 if watch:
  secondary('collector-proof',lambda:save('collector-finished.json',dict(run=identity['run'],status='FAILED_CLOSED' if ledger.primary else 'LIVE_MONITOR_HEALTHY',error=ledger.primary,qpc=ticks(),allHandlesExited=allprobes,acceptance=False,identities=[dict(pid=r['pid'],created=r['times'][0],exited=r['times'][1],exit=r['exit']) for r in handle_rows if r['handleState']==0])))
 if reader:secondary('reader-close',reader.close)
 if watch:
  def finish_monitor():
   state=int(K.WaitForSingleObject(watch.handle,60000));code=w.DWORD()
   if not K.GetExitCodeProcess(watch.handle,c.byref(code)):raise c.WinError(c.get_last_error())
   save('monitor-exit.json',dict(identity=identity,exit_code=code.value,handleState=state,qpc=ticks()))
   if state!=0 or code.value:raise RuntimeError('Monitor failed or did not exit')
  secondary('monitor-cleanup',finish_monitor);secondary('monitor-handle-close',watch.close)
 if resource:secondary('resource-cleanup',lambda:finish_helper(resource))
 tree_result=secondary('tree-cleanup',lambda:tree.finish(root))
 if tree_result and (not tree_result['allExited'] or not tree_result['allHandlesClosed'] or tree_result['errors'] or not tree_result['threadStopped']):ledger.fail('tree-proof','Incomplete retained tree cleanup')
 for item in measured:
  if K.WaitForSingleObject(int(item.process._handle),0)==0:
   item.process._handle.Close();ledger.cleanup.append(dict(role='probe-parent-handle',pid=item.process.pid,closed=True,qpc=ticks()))
 # WMI child events are reconciled against retained identities; never manufacture STOPs.
 def reconcile_events():
  taps=json.loads((root/'tap.json').read_text(encoding='utf-8-sig'));taps=taps if isinstance(taps,list) else [taps]
  events=[json.loads(l) for l in (root/'events.jsonl').read_text(encoding='utf-8-sig').splitlines()]
  q=json.loads((root/'queue-state.json').read_text(encoding='utf-8-sig'));rows=tree_result['rows'];missing=[];children=[]
  rootpids={r['pid'] for r in rows}
  for r in taps:
   if r['stage']!='B-WMI-callback' or r['kind']!='start' or r['parentPid'] not in rootpids:continue
   match=[x for x in rows if x['pid']==r['pid'] and x['parentPid']==r['parentPid'] and int(x['created'])<=int(r['nativeTime']) and (not x['exitFiletime'] or int(r['nativeTime'])<=int(x['exitFiletime']))]
   stops=[x for x in taps if x['stage']=='B-WMI-callback' and x['kind']=='stop' and x['pid']==r['pid'] and x['name']==r['name'] and int(x['nativeTime'])>=int(r['nativeTime'])]
   result=dict(start=r,retainedMatches=len(match),stopMatches=len(stops));children.append(result)
   if len(match)!=1 or len(stops)!=1:missing.append(result)
  paired=all(sum(e['pid']==m.process.pid and e['kind']==kind for e in events)==1 for m in measured for kind in ('start','stop'))
  good=paired and not missing and q['remaining']==0 and not q['failed'] and q['enqueued']==q['persisted']==q['removed']
  save('event-tree-reconciliation.json',dict(probeStarts=sum(e['kind']=='start' for e in events),probeStops=sum(e['kind']=='stop' for e in events),children=children,unproven=missing,probePairs=paired,queue=q,complete=good))
  if not good:raise RuntimeError('Event/tree proof incomplete; do not infer child exit from absence')
 secondary('event-tree-reconciliation',reconcile_events)
 save('cleanup-ledger.json',ledger.result())
 result=dict(ledger.result(),phase=phase,probes=len(measured),hardDeadlineReproduced=any(x.row.get('hardDeadlineFailure') for x in measured),cleanupComplete=allprobes and bool(tree_result and tree_result['allExited']),protectedAccess=False)
 save('diagnostic-result.json',result);print(json.dumps(dict(status=result['status'],phase=phase,probes=len(measured),hardDeadlineReproduced=result['hardDeadlineReproduced'],primary=ledger.primary)),flush=True)
 if ledger.primary:sys.exit(1)
