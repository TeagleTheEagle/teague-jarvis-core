"""Read preserved sacrificial evidence only; write new audit outputs only."""
import collections, difflib, json, pathlib, shutil, statistics
from prepare import R, OLD, REPO, digest, inventory, save

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def lines(p):return [json.loads(s) for s in p.read_text(encoding='utf-8-sig').splitlines()]
def distribution(xs):
    if not xs:return None
    xs=sorted(xs)
    return {'count':len(xs),'min':min(xs),'median':statistics.median(xs),
            'p95_nearest_rank':xs[max(0,__import__('math').ceil(.95*len(xs))-1)],'max':max(xs)}

if __name__=='__main__':
    d=OLD/'loads2';frequency=read(d/'ready.json')['frequency']
    beats=lines(d/'heartbeat.jsonl');events=lines(d/'events.jsonl')
    probes=read(d/'probes.json');phases=read(d/'phases.json')
    samples=read(d/'collector-samples.json');trace=read(d/'loop-trace.json')
    resources=read(d/'resources.json');spans=[];pending={}
    for row in trace:
        stage=row['stage']
        if stage.endswith('.begin'):pending.setdefault(stage[:-6],[]).append(row)
        elif stage.endswith('.end'):
            key=stage[:-4]
            if pending.get(key):
                start=pending[key].pop()
                spans.append({'stage':key,'start':start['qpc'],'end':row['qpc'],
                              'seconds':(row['qpc']-start['qpc'])/frequency,'detail':row['detail']})
    gaps=[{'end':b['ticks'],'seconds':(b['ticks']-a['ticks'])/frequency} for a,b in zip(beats,beats[1:])]
    missing=[];results=[]
    for p in probes:
        observed=[e for e in events if e['pid']==p['pid']]
        starts=sum(e['kind']=='start' for e in observed);stops=sum(e['kind']=='stop' for e in observed)
        if (starts,stops)!=(1,1):missing.append({'probe':p,'starts':starts,'stops':stops,'recorded_events':observed})
    for p in phases:
        start,end=p['start_qpc'],p['end_qpc']
        selected=[s for s in spans if start<=s['start']<=end]
        localprobes=[q for q in probes if start<=q['start_qpc']<=end]
        pids={q['pid'] for q in localprobes}
        counters=collections.defaultdict(list)
        for row in resources:
            if row['endQpc']>=start and row['qpc']<=end:
                for c in row['counters']:counters[c['Path']].append(c['CookedValue'])
        # Preserve observed counter names; do not assume disk-number to volume mapping.
        stage_stats={key:distribution([s['seconds'] for s in selected if s['stage']==key]) for key in {s['stage'] for s in selected}}
        local_ages=[s['age'] for s in samples if start<=s.get('qpc',-1)<=end]
        results.append({'phase':p,'duration_seconds':(end-start)/frequency,
                        'heartbeat_intervals':distribution([g['seconds'] for g in gaps if start<=g['end']<=end]),
                        'observed_age':distribution(local_ages),'stage_seconds':stage_stats,
                        'scheduling_wait_overrun_upper_bound_seconds':max([0]+[s['seconds']-1 for s in selected if s['stage']=='wait']),
                        'resource_counters':{k:distribution(v) for k,v in counters.items()},
                        'expected_starts':len(localprobes),'expected_stops':len(localprobes),
                        'captured_starts':sum(e['pid'] in pids and e['kind']=='start' for e in events),
                        'captured_stops':sum(e['pid'] in pids and e['kind']=='stop' for e in events)})
    save('loads2-reconciliation.json',{'historical_run':'loads2','phases':results,
         'maximum_observed_age':max(s['age'] for s in samples),'probe_count':len(probes),
         'distinct_probe_pids':len({p['pid'] for p in probes}),'retained_handle_records':sum(p.get('handle_retained_through_finalization') is True for p in probes),
         'event_counts':dict(collections.Counter(e['kind'] for e in events)), 'missing_events':missing,
         'collector':read(d/'collector-finished.json'),'monitor':read(d/'monitor-result.json'),
         'finalizer':read(d/'finalizer-process.json'),
         'final_drain':[s for s in spans if s['stage']=='drain'][-1],
         'queue_depth_max':max(t['detail']['depth'] for t in trace if t['stage']=='queue.query.end'),
         'backlog_max':max(t['detail'] for t in trace if t['stage']=='queue.backlog.end'),
         'diagnosis':'Three missing stop records; no evidence establishing which event-delivery layer lost them.',
         'acceptance':False})
    changes=[]
    predecessors=[OLD.parent/'stage6-monitor-timing-20260918',OLD.parent/'stage6-heartbeat-journal-20260918']
    for p in sorted(OLD.iterdir()):
        if p.suffix not in ('.py','.ps1','.md'):continue
        previous=next((q/p.name for q in predecessors if (q/p.name).is_file()),None)
        changes.append({'path':str(p),'sha256':digest(p),'comparison':str(previous) if previous else None,
                        'relation':'NEW_RELATIVE_TO_CHECKED_PREDECESSORS' if previous is None else
                        ('IDENTICAL' if digest(previous)==digest(p) else 'CHANGED')})
    save('prior-source-reconciliation.json',changes)
    for label,a,b in [('probe-handles',OLD/'preserved-campaign-v1.py',OLD/'campaign.py'),
                      ('delayed-finalization',OLD/'preserved-delay-test-v1.py',OLD/'test_extended_finalization.py'),
                      ('monitor',predecessors[0]/'monitor.ps1',OLD/'monitor.ps1')]:
        with (R/(label+'.diff')).open('x',encoding='utf-8') as f:
            f.writelines(difflib.unified_diff(a.read_text().splitlines(True),b.read_text().splitlines(True),fromfile=str(a),tofile=str(b)))
    before=read(R/'preserved-inventory-before.json');after=inventory(OLD)
    if before!=after:raise RuntimeError('Preserved evidence changed')
    shutil.copytree(OLD,R/'preserved-original')
    copy_inventory=inventory(R/'preserved-original')
    projection=lambda rows:[(v['path'],v['bytes'],v['sha256']) for v in rows]
    if projection(before)!=projection(copy_inventory):raise RuntimeError('Evidence copy mismatch')
    production=read(R/'preexisting-tracked-changes.json')
    for row in production:
        p=REPO/row['path']
        if (digest(p) if p.is_file() else None)!=row['sha256']:raise RuntimeError('Tracked file changed')
    save('preservation-check.json',{'original_evidence_files':len(before),'unchanged':True,'copy_hash_verified':len(copy_inventory),
         'tracked_files_checked':len(production),'tracked_file_changes_during_this_task':0,
         'protected_VM_access_by_this_task':False,'normal_VirtualBox_configuration_access_by_this_task':False,
         'limitations':['No retroactive proof of historical file access.','Current process snapshots cannot prove absence of short-lived processes between snapshots.','No protected artifact hashes collected, as prohibited.']})
    print(json.dumps({'missing_stop_pids':[m['probe']['pid'] for m in missing],
                      'phases':[{'mode':p['phase']['mode'],'max_interval':p['heartbeat_intervals']['max'],'age':p['observed_age'],'starts':p['captured_starts'],'stops':p['captured_stops']} for p in results],
                      'max_age':max(s['age'] for s in samples),'preserved_hashes_verified':len(before)}))
