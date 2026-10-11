import pathlib,sys,time,os,json
from evidence_support import TreeTracker,Managed,Ledger,put
root=pathlib.Path(sys.argv[1]);code=pathlib.Path(__file__).parent
tracker=TreeTracker();ledger=Ledger(root); launched=[];results=[]
try:
 for batch in range(6):
  group=[]
  for n in range(4):
   m=Managed([str(code/'J6Probe.exe')],root,f'probe-{batch}-{n}',tracker);group.append(m);launched.append(m)
  for m in group:
   r=m.finish(13.6);results.append(r)
   if r['handleState']!=0:raise RuntimeError('Stress helper exceeded bounded wait; preserve and stop')
 for batch,mode in enumerate(('child-first','parent-first','orphan')):
  group=[]
  for n in range(4):
   m=Managed([sys._base_executable,'-B',str(code/'trace_fixture.py'),str(root),mode],root,f'{mode}-{n}',tracker);group.append(m);launched.append(m)
  for m in group:
   r=m.finish(13.6);results.append(r)
   if r['handleState']!=0 or r['exit']!=0:raise RuntimeError('Synthetic parent did not complete normally')
except BaseException:ledger.fail('stress')
finally:
 for m in launched:
  if not m.finished:ledger.cleanup.append(m.finish(15))
 tree=tracker.finish(root,20);ledger.cleanup.append(tree)
 if not tree['allExited'] or not tree['allHandlesClosed']:ledger.fail('tree-cleanup','Retained tree did not completely exit/close')
 put(root/'stress-result.json',dict(ledger.result(),launched=[m.identity for m in launched],results=results,collectorPid=os.getpid()))
 print(json.dumps(dict(status=ledger.result()['status'],launched=len(launched),retained=len(tree['rows']))))
raise SystemExit(1 if ledger.primary else 0)
