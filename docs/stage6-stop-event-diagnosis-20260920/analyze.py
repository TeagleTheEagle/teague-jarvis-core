"""Join independent handle evidence with observed notification stages, without synthesis."""
import collections,datetime,hashlib,json,math,pathlib,statistics,sys,time
R=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def lines(p):return [json.loads(x) for x in p.read_text(encoding='utf-8-sig').splitlines()]
def dist(v):
 if not v:return {'count':0,'median':None,'p95':None,'p99':None,'max':None}
 v=sorted(v);n=len(v)
 return {'count':n,'min':v[0],'median':statistics.median(v),'p95':v[math.ceil(.95*n)-1] if n>=20 else None,
         'p99':v[math.ceil(.99*n)-1] if n>=100 else None,'max':v[-1]}
def analyze(run):
 d=R/run
 if (d/'analysis.json').exists():raise RuntimeError('Preserve earlier analysis')
 probes=read(d/'probes.json');tap=read(d/'tap.json');pipe=read(d/'pipeline.json');persist=lines(d/'events.jsonl')
 tr=read(d/'loop-trace.json');ident=read(d/'ready.json');f=ident['frequency'];phases=read(d/'phases.json');resources=read(d/'resources.json')
 finished=read(d/'collector-finished.json');freeze=next(x['qpc'] for x in tr if x['stage']=='collection.freeze');unsub=next(x['qpc'] for x in tr if x['stage']=='unsubscribe.begin')
 now=time.perf_counter_ns()/1e9*f
 rows=[];lat=collections.defaultdict(list)
 for p in probes:
  item={'pid':p['pid'],'creation_filetime':p['created'],'kernel_exit_filetime':p['kernel_exit_filetime'],'phase':p['phase'],'handle_exit':p['handle_signalled'],'exit_code':p['exit']}
  for kind in ('start','stop'):
   a=[t for t in tap if t['stage']=='A-callback' and t['kind']==kind and t['pid']==p['pid']]
   q=[t for t in tap if t['stage']=='A-enqueue' and t['kind']==kind and t['pid']==p['pid']]
   b=[t for t in tap if t['stage']=='B-WMI-callback' and t['kind']==kind and t['pid']==p['pid']]
   # Source identifier -> kind; pipeline rows carry identifiers, not inferred exit events.
   ids={t['source'] for t in tap if t['stage']=='A-enqueue' and t['kind']==kind}
   flow=[x for x in pipe if x['pid']==p['pid'] and x['source'] in ids]
   ev=[x for x in persist if x['pid']==p['pid'] and x['kind']==kind]
   count={'A_callback':len(a),'A_enqueued':len(q),'A_drained':sum(x['stage']=='drain' for x in flow),
          'A_serialized':sum(x['stage']=='serialized' for x in flow),'A_write_completed':sum(x['stage']=='persisted' for x in flow),
          'A_persisted_records':len(ev),'B_WMI_callback':len(b),
          'A_reconciled':int(len(ev)==1 and len(a)==1 and len(q)==1 and sum(x['stage']=='persisted' for x in flow)==1)}
   item[kind]={'counts':count,'callback':a,'enqueue':q,'parallel_observer':b,'pipeline':flow,'persisted':ev,
               'after_workload_completion':any(x['qpc']>finished['qpc'] for x in a+q),
               'after_collection_freeze':any(x['qpc']>freeze for x in a+q),
               'reconciliation_qpc':now}
   base=int(p['created'] if kind=='start' else p['kernel_exit_filetime'])
   if len(a)==1:
    lat[(p['phase'],kind,'kernel_lifecycle_to_native_notification_s')].append((int(a[0]['nativeTime'])-base)/1e7)
    native=int(a[0]['nativeTime'])/1e7-11644473600
    received=datetime.datetime.fromisoformat(a[0]['utc'].replace('Z','+00:00')).timestamp()
    lat[(p['phase'],kind,'native_notification_to_callback_tap_wall_s')].append(received-native)
   if len(a)==len(q)==1:lat[(p['phase'],kind,'callback_tap_to_enqueue_signed_s')].append((q[0]['qpc']-a[0]['qpc'])/f)
   def stage(n):return [x for x in flow if x['stage']==n]
   if len(q)==1 and len(stage('drain'))==1:lat[(p['phase'],kind,'queue_residence_s')].append((stage('drain')[0]['qpc']-q[0]['qpc'])/f)
   for metric,left,right in [('drain_to_serialized_s','drain','serialized'),('serialization_s','serialize.begin','serialized'),('evidence_append_s','write.begin','persisted')]:
    if len(stage(left))==len(stage(right))==1:lat[(p['phase'],kind,metric)].append((stage(right)[0]['qpc']-stage(left)[0]['qpc'])/f)
   if len(stage('persisted'))==1:lat[(p['phase'],kind,'persisted_to_offline_reconciliation_s')].append((now-stage('persisted')[0]['qpc'])/f)
  item['comparison']={'both_STOP':bool(item['stop']['counts']['A_persisted_records'] and item['stop']['counts']['B_WMI_callback']),
   'only_A_STOP':bool(item['stop']['counts']['A_persisted_records'] and not item['stop']['counts']['B_WMI_callback']),
   'only_B_STOP':bool(not item['stop']['counts']['A_persisted_records'] and item['stop']['counts']['B_WMI_callback']),
   'neither_STOP':bool(not item['stop']['counts']['A_persisted_records'] and not item['stop']['counts']['B_WMI_callback']),
   'independent_kernel_handle_exit':p['handle_signalled']}
  rows.append(item)
 summaries=[]
 for phase in phases:
  selected=[r for r in rows if r['phase']==phase['mode']];totals={}
  for kind in ('start','stop'):
   totals[kind]={key:sum(r[kind]['counts'][key] for r in selected) for key in selected[0][kind]['counts']} if selected else {}
  counters=collections.defaultdict(list)
  for sample in resources:
   if sample['endQpc']>=phase['start_qpc'] and sample['qpc']<=phase.get('end_qpc',finished['qpc']):
    for x in sample['counters']:counters[x['Path']].append(x['CookedValue'])
  summaries.append({'phase':phase,'expected_starts':len(selected),'expected_exits':len(selected),'handle_exits':sum(r['handle_exit'] for r in selected),
    'counts':totals,'observer_comparison':{k:sum(r['comparison'][k] for r in selected) for k in selected[0]['comparison']} if selected else {},
    'resource_distributions':{k:dist(v) for k,v in counters.items()}})
 keys=collections.Counter((t['source'],t['eventId']) for t in tap if t['stage']=='A-enqueue')
 globalids=collections.Counter(t['eventId'] for t in tap if t['stage']=='A-enqueue')
 missing=[{'pid':r['pid'],'created':r['creation_filetime'],'phase':r['phase'],'start':r['start']['counts'],'stop':r['stop']['counts']} for r in rows if any(v!=1 for kind in ('start','stop') for v in r[kind]['counts'].values())]
 result={'run':run,'probes':len(probes),'phases':summaries,'missing_or_duplicated':missing,'rows':rows,
 'latencies':[{'phase':k[0],'kind':k[1],'metric':k[2],'seconds':dist(v)} for k,v in lat.items()],
 'duplicate_source_eventids':[{'key':list(k),'count':v} for k,v in keys.items() if v!=1],
 'duplicate_global_eventids':[{'id':k,'count':v} for k,v in globalids.items() if v!=1],
 'late_after_collector_finish':[{'pid':r['pid'],'kind':k} for r in rows for k in ('start','stop') if r[k]['after_workload_completion']],
 'late_after_collection_freeze':[{'pid':r['pid'],'kind':k} for r in rows for k in ('start','stop') if r[k]['after_collection_freeze']],
 'teardown_pending':[x for x in pipe if x['stage'] in ('preunsubscribe.pending','teardown.discard')],
 'tap_state':read(d/'tap-state.json'),'maximum_age':max(x['age'] for x in read(d/'collector-samples.json')),
 'queue_max':max(x['detail']['depth'] for x in tr if x['stage']=='queue.query.end'),
 'freeze_qpc':freeze,'unsubscribe_qpc':unsub,'collector_finish_qpc':finished['qpc'],
 'limitations':['Raw native provider emissions are not directly counted.','Observer B uses same Windows WMI provider through separate COM transport; independent kernel exit handles are separate from notifications.',
 'Raw callback tap follows existing handler registration; signed callback-to-enqueue deltas can be negative.','Offline reconciliation latency includes intentional analysis delay.',
 'p95 omitted below 20 samples; p99 omitted below 100 samples.','Wall-time FILETIME comparisons are distinct from monotonic local pipeline latency.']}
 with (d/'analysis.json').open('x',encoding='utf-8') as f_:json.dump(result,f_,indent=2,sort_keys=True)
 print(json.dumps({'run':run,'probes':len(probes),'missing':missing,'tap_state':result['tap_state'],'max_age':result['maximum_age'],'pending_at_teardown':len(result['teardown_pending']),
 'phases':[{'mode':p['phase']['mode'],'expected':p['expected_starts'],'stop':p['counts']['stop']} for p in summaries]}))
if __name__=='__main__':
 for run in sys.argv[1:]:analyze(run)
