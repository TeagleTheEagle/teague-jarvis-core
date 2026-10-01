"""Independent read-only comparison; process exits never substitute for STOP events."""
import pathlib,json,sys,collections
R=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def reconcile(run):
 d=R/run;probes=read(d/'probes.json');taps=read(d/'tap.json');q=read(d/'queue-state.json');entries=read(d/'queue-entries.json');ident=read(d/'ready.json')
 events=[json.loads(s) for s in (d/'events.jsonl').read_text(encoding='utf-8-sig').splitlines()]
 hb=[json.loads(s) for s in (d/'heartbeat.jsonl').read_text().splitlines()];samples=read(d/'collector-samples.json');phases=read(d/'phases.json')
 errors=[]
 def check(ok,msg):
  if not ok:errors.append(msg)
 check(len({p['pid'] for p in probes})==len(probes),'ambiguous PID')
 check(all(p['handle_signalled'] and p['exit']==0 and int(p['kernel_exit_filetime'])>int(p['created']) for p in probes),'kernel exit evidence')
 check(q['enqueued']==q['selected']==q['persisted']==q['removed']==len(events)==len(entries)==len(probes)*2 and q['remaining']==0 and not q['failed'],'queue counts')
 check(len({e['queueSequence'] for e in entries})==len(entries),'internal identity collision')
 check({e['queueSequence'] for e in events}=={e['queueSequence'] for e in entries},'persisted identity mismatch')
 check(all(e['persisted'] and e['removed'] for e in entries),'unprocessed entry')
 check(len({e['queueSequence'] for e in events})==len(events),'duplicate persistence')
 check(read(d/'monitor-exit.json')['exit_code']==0,'monitor exit')
 check(not read(d/'tap-state.json')['errors'] and not read(d/'tap-state.json')['overflow'],'tap failure')
 for name in ('collector-failure.json','monitor-failure.json','queue-failure.json','resource-failure.txt'):
  check(not (d/name).exists(),name)
 for p in probes:
  for k in ('start','stop'):
   check(sum(e['pid']==p['pid'] and e['kind']==k for e in events)==1,f"persisted {p['pid']} {k}")
   for stage in ('A-callback','A-enqueue','B-WMI-callback'):
    check(sum(e['pid']==p['pid'] and e['kind']==k and e['stage']==stage for e in taps)==1,f"{stage} {p['pid']} {k}")
 gaps=[(b['ticks']-a['ticks'])/ident['frequency'] for a,b in zip(hb,hb[1:])]
 check(max(gaps,default=0)<10,'heartbeat interval');check(max((s['age'] for s in samples),default=0)<=10,'heartbeat age')
 rows=[]
 for phase in phases:
  mode=phase['mode'];ps=[p for p in probes if p['phase']==mode];pids={p['pid'] for p in ps};ev=[e for e in events if e['pid'] in pids];ts=[e for e in taps if e['pid'] in pids]
  row=dict(phase=mode,expectedStarts=len(ps),confirmedExits=len(ps))
  for k in ('start','stop'):
   row[k+'Callbacks']=sum(e['kind']==k and e['stage']=='A-callback' for e in ts)
   row[k+'Enqueued']=sum(e['kind']==k and e['stage']=='A-enqueue' for e in ts)
   row[k+'Persisted']=sum(e['kind']==k for e in ev)
  row.update(externalCollisions=len(ev)-len({e['eventIdentifier'] for e in ev}),internalCollisions=len(ev)-len({e['queueSequence'] for e in ev}),maxQueueDepth=max((e['queueDepth'] for e in ts if e['stage']=='A-enqueue'),default=0),maxHeartbeatAge=max((s['age'] for s in samples if s['phase']==mode),default=0),maxHeartbeatInterval=max(((b['ticks']-a['ticks'])/ident['frequency'] for a,b in zip(hb,hb[1:]) if phase['start_qpc']<=b['ticks']<=phase.get('end_qpc',hb[-1]['ticks'])),default=0),writeErrors=int((d/'monitor-failure.json').exists()))
  row['reconciliation']='PASS' if all(row[k]==len(ps) for k in ('startCallbacks','startEnqueued','startPersisted','stopCallbacks','stopEnqueued','stopPersisted')) else 'FAIL';rows.append(row)
 return dict(run=run,status='PASS' if not errors else 'FAIL',errors=errors,probes=len(probes),starts=len([e for e in events if e['kind']=='start']),stops=len([e for e in events if e['kind']=='stop']),externalCollisions=len(events)-len({e['eventIdentifier'] for e in events}),internalCollisions=len(entries)-len({e['queueSequence'] for e in entries}),maxHeartbeatInterval=max(gaps,default=0),maxHeartbeatAge=max((s['age'] for s in samples),default=0),queue=q,phases=rows,independentObserver='Separate WMI subscriber; same provider. Retained process handles independently establish exits.')
if __name__=='__main__':
 result=reconcile(sys.argv[1]);p=R/sys.argv[1]/'reconciliation.json'
 with p.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
 print(json.dumps(result));sys.exit(result['status']!='PASS')
