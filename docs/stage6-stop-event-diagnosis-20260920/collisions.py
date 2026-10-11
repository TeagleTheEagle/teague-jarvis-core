"""Localize real loss to cross-source duplicate IDs and the sibling removal interval."""
import collections,json,pathlib,sys
R=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
for run in sys.argv[1:]:
 d=R/run;a=read(d/'analysis.json');tap=read(d/'tap.json');pipeline=read(d/'pipeline.json');groups=collections.defaultdict(list)
 for t in tap:
  if t['stage']=='A-enqueue':groups[t['eventId']].append(t)
 collisions=[]
 for id,events in groups.items():
  if len(events)<2:continue
  flow=[p for p in pipeline if p['eventId']==id]
  removed=[p for p in flow if p['stage']=='removed']
  missing=[e for e in events if not any(p['stage']=='drain' and p['source']==e['source'] and p['pid']==e['pid'] for p in flow)]
  collisions.append({'id':id,'enqueued':events,'pipeline':flow,'not_drained':missing,
   'missing_already_enqueued_when_sibling_removed':all(any(m['qpc']<p['qpc'] for p in removed) for m in missing),
   'same_pid_start_and_stop':len({e['pid'] for e in events})==1 and {e['kind'] for e in events}=={'start','stop'}})
 missing_count=sum(len(c['not_drained']) for c in collisions)
 result={'run':run,'cross_source_duplicate_ids':len(collisions),'lost_events_matching_collisions':missing_count,
 'total_missing_events':sum(1 for r in a['rows'] for k in ('start','stop') if r[k]['counts']['A_persisted_records']==0),
 'all_missing_already_queued_before_sibling_removal':all(c['missing_already_enqueued_when_sibling_removed'] for c in collisions),
 'collisions':collisions}
 with (d/'collision-analysis.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
 print(json.dumps({k:v for k,v in result.items() if k!='collisions'}))
