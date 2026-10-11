import json,pathlib,statistics,datetime as dt
R=pathlib.Path(__file__).parent
def lines(n):return [json.loads(s) for s in (R/n).read_text(encoding='utf-8-sig').splitlines() if s]
def stats(a):
 a=sorted(a)
 return dict(n=len(a),min=a[0],p50=statistics.median(a),p95=a[int((len(a)-1)*.95)],max=a[-1]) if a else None
ts=lines('timings.jsonl');obs=lines('observations.jsonl');waits=lines('waits.jsonl');events=lines('events.jsonl');probes=lines('probes.jsonl');resources=lines('resources-v2.jsonl')
freq=json.loads((R/'ready.json').read_text())['StopwatchFrequency']
out={'heartbeat_interval_seconds':stats([(b['LoopTicks']-a['LoopTicks'])/freq for a,b in zip(ts,ts[1:])]),
 'write_seconds':stats([(r['WrittenTicks']-r['DrainedTicks'])/freq for r in ts]),
 'drain_seconds':stats([(r['DrainedTicks']-r['LoopTicks'])/freq for r in ts]),
 'wait_seconds':stats([(r['AfterTicks']-r['BeforeTicks'])/freq for r in waits]),
 'observed_age_by_phase':{p:stats([r['Age'] for r in obs if r['Phase']==p]) for p in sorted({r['Phase'] for r in obs})},
 'heartbeat_read_seconds':stats([r['ReadEndMonotonic']-r['ReadStartMonotonic'] for r in obs]),
 'monitor_cpu_seconds':ts[-1]['ProcessCPU']-ts[0]['ProcessCPU'],
 'monitor_elapsed_seconds':(ts[-1]['LoopTicks']-ts[0]['LoopTicks'])/freq,
 'probes_launched':len(probes),'start_events':sum(e['Kind']=='start' for e in events),'stop_events':sum(e['Kind']=='stop' for e in events)}
starts={r['PID']:r for r in events if r['Kind']=='start'};stops={r['PID']:r for r in events if r['Kind']=='stop'}
out['missing_start_pids']=[r['PID'] for r in probes if r['PID'] not in starts]
out['missing_stop_pids']=[r['PID'] for r in probes if r['PID'] not in stops]
out['paired_native_lifetime_seconds']=stats([(int(stops[p]['NativeFileTime'])-int(starts[p]['NativeFileTime']))/1e7 for p in starts if p in stops])
out['event_delivery_latency_seconds']=stats([dt.datetime.fromisoformat(e['ReceivedUtc'].replace('Z','+00:00')).timestamp()-(int(e['NativeFileTime'])/1e7-11644473600) for e in events])
out['probe_wall_lifetime_upper_bound_seconds']=stats([(dt.datetime.fromisoformat(p['AfterUtc'])-dt.datetime.fromisoformat(p['BeforeUtc'])).total_seconds() for p in probes])
counter={}
for row in resources:
 for c in row['Counters']:counter.setdefault(c['Path'],[]).append(c['CookedValue'])
out['resource_counters']={k:stats(v) for k,v in counter.items()};out['resource_samples']=len(resources)
out['wall_minus_monotonic_interval_delta_seconds']=stats([(dt.datetime.fromisoformat(b['WallStart'].replace('Z','+00:00'))-dt.datetime.fromisoformat(a['WallStart'].replace('Z','+00:00'))).total_seconds()-(b['LoopTicks']-a['LoopTicks'])/freq for a,b in zip(ts,ts[1:])])
(R/'analysis.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
