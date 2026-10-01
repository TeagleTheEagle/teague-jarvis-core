import pathlib,json,sys,datetime,statistics
R=pathlib.Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def utc(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
def analyze(name):
 d=R/name;tr=read(d/'loop-trace.json');ident=read(d/'ready.json');f=ident['frequency'];beats=[json.loads(s) for s in (d/'heartbeat.jsonl').read_text(encoding='utf-8-sig').splitlines()];phases=read(d/'phases.json');samples=read(d/'collector-samples.json')
 resources=read(d/'resources.json') if (d/'resources.json').exists() else [];events=[json.loads(s) for s in (d/'events.jsonl').read_text(encoding='utf-8-sig').splitlines()] if (d/'events.jsonl').exists() else []
 spans=[];pending={}
 for m in tr:
  stage=m['stage']
  if stage.endswith('.begin'):pending.setdefault(stage[:-6],[]).append(m)
  elif stage.endswith('.end'):
   base=stage[:-4]
   if pending.get(base):
    start=pending[base].pop();spans.append({'stage':base,'start':start['qpc'],'end':m['qpc'],'seconds':(m['qpc']-start['qpc'])/f,'seq':m['seq'],'detail':m['detail']})
 stats={}
 for s in spans:stats.setdefault(s['stage'],[]).append(s['seconds'])
 stats={k:{'count':len(v),'max':max(v),'median':statistics.median(v),'total':sum(v)} for k,v in stats.items()}
 gaps=[{'from_seq':a['seq'],'to_seq':b['seq'],'start':a['ticks'],'end':b['ticks'],'seconds':(b['ticks']-a['ticks'])/f,'from_utc':a['utc'],'to_utc':b['utc']} for a,b in zip(beats,beats[1:])]
 def resource_summary(rows):
  counters=[c for row in rows for c in row['counters']]
  def v(p):return [c['CookedValue'] for c in counters if p in c['Path'].lower()]
  result={}
  for key,pattern in [('cpu_total_peak','processor(_total)'),('context_switches_peak','context switches/sec'),('pages_sec_peak','memory\\pages/sec'),('c_queue_peak','physicaldisk(1 c:)\\current disk queue'),('c_read_latency_peak','physicaldisk(1 c:)\\avg. disk sec/read'),('c_write_latency_peak','physicaldisk(1 c:)\\avg. disk sec/write'),('c_read_bytes_sec_peak','physicaldisk(1 c:)\\disk read bytes/sec'),('c_write_bytes_sec_peak','physicaldisk(1 c:)\\disk write bytes/sec'),('d_read_bytes_sec_peak','physicaldisk(0 d:)\\disk read bytes/sec')]:
   values=v(pattern);result[key]=max(values) if values else None
  values=v('physicaldisk(1 c:)\\% idle time');result['c_active_peak']=max(100-x for x in values) if values else None
  values=v('memory\\available mbytes');result['available_memory_min']=min(values) if values else None
  cpu={}
  for row in rows:
   for p in row['processes']:
    if p['cpuSeconds'] is not None:cpu.setdefault(str(p['pid']),{'name':p['name'],'values':[],'priority':p['priority']})['values'].append(p['cpuSeconds'])
  result['process_cpu_deltas']={pid:{'name':p['name'],'delta_seconds':max(p['values'])-min(p['values']),'priority':p['priority']} for pid,p in cpu.items()}
  return result
 longest=max(gaps,key=lambda g:g['seconds']);delays=[]
 for g in gaps:
  if g['seconds']<=2 and g!=longest:continue
  overlapping=[dict(s,overlap_seconds=max(0,min(s['end'],g['end'])-max(s['start'],g['start']))/f) for s in spans if s['start']<g['end'] and s['end']>g['start']]
  rows=[r for r in resources if r['endQpc']>=g['start'] and r['qpc']<=g['end']]
  delays.append(dict(g,spans=overlapping,resource=resource_summary(rows)))
 phase_results=[]
 for p in phases:
  end=p.get('end_qpc',read(d/'collector-finished.json')['qpc']);local=[g['seconds'] for g in gaps if p['start_qpc']<=g['end']<=end];localsp=[s for s in spans if p['start_qpc']<=s['start']<=end]
  rows=[r for r in resources if r['endQpc']>=p['start_qpc'] and r['qpc']<=end]
  phase_results.append(dict(p,max_interval=max(local) if local else None,median_interval=statistics.median(local) if local else None,stage_max={k:max(s['seconds'] for s in localsp if s['stage']==k) for k in set(s['stage'] for s in localsp)},resources=resource_summary(rows)))
 lat=[]
 for e in events:
  native=int(e['nativeTime'])/1e7-11644473600
  lat.append({'pid':e['pid'],'kind':e['kind'],'native_event_to_drain_seconds':utc(e['utc'])-native,'powershell_queued_to_drain_seconds':utc(e['utc'])-utc(e['queuedUtc'])})
 waits=[s['seconds'] for s in spans if s['stage']=='wait']
 result={'run':name,'collector':read(d/'collector-finished.json'),'monitor':read(d/'monitor-result.json') if (d/'monitor-result.json').exists() else read(d/'monitor-failure.json'),'longest_gap':longest,'stages':stats,'delays_over_two_seconds_and_longest':delays,'phase_results':phase_results,'max_observed_age':max(s['age'] for s in samples),'wait_overrun_upper_bound_seconds':max(0,max(waits)-1),'event_latencies':lat,'events_expected':len(read(d/'probes.json'))*2,'events_captured':len(events),'priority':read(d/'monitor-config.json')['priority'],'resource_summary':resource_summary(resources),'unclosed_stage_markers':pending}
 if (d/'rejected-poll.json').exists():
  rejected=read(d/'rejected-poll.json');seq=rejected['last_record']['seq'];begin=rejected['last_record']['ticks']
  flush=next(s for s in spans if s['stage']=='journal.flush' and s['seq']==seq)
  result['failed_publication_timeline']={'rejected':rejected,'trace':[m for m in tr if m['seq']==seq and m['qpc']<=flush['end']+50000],'flush':flush,'resources_during_flush':resource_summary([r for r in resources if r['endQpc']>=flush['start'] and r['qpc']<=flush['end']]),'no_next_heartbeat':'collector stopped the run after rejection; do not treat adjacent-record max as failure duration'}
 result['max_queue_depth']=max(m['detail']['depth'] for m in tr if m['stage']=='queue.query.end')
 result['max_backlog']=max(m['detail'] for m in tr if m['stage']=='queue.backlog.end')
 (d/'analysis.json').write_text(json.dumps(result,indent=2));print(json.dumps({'run':name,'longest_gap':longest,'stages':stats,'phases':[{k:v for k,v in p.items() if k not in ('resources','stage_max')} for p in phase_results]},indent=2))
for name in sys.argv[1:]:analyze(name)
