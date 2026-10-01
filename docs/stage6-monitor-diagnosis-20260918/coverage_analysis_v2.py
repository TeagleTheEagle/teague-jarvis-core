import pathlib,json,datetime as dt,collections
R=pathlib.Path(__file__).parent;D=R/'event-coverage-v2'
ev=[json.loads(s) for s in (D/'events.jsonl').read_text().splitlines()]
probes=json.loads((D/'probes.json').read_text(encoding='utf-8-sig'))
assert len({p['PID'] for p in probes})==len(probes),'PID reuse requires disambiguation'
stamp=lambda s:dt.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
matches=[]
for p in probes:
 related=[e for e in ev if e['PID']==p['PID']]
 a=[e for e in related if e['Kind']=='start'];b=[e for e in related if e['Kind']=='stop']
 matches.append({'PID':p['PID'],'RequestedName':p['Name'],'StartCount':len(a),'StopCount':len(b),'StopName':b[0]['Name'] if b else None,
 'LaunchWaitUpperBoundSeconds':stamp(p['AfterUtc'])-stamp(p['BeforeUtc']),
 'StartReceivedAfterLaunchBeginSeconds':stamp(a[0]['ReceivedUtc'])-stamp(p['BeforeUtc']) if a else None})
result={'Trials':len(matches),'MatchedStarts':sum(m['StartCount']==1 for m in matches),'MatchedStops':sum(m['StopCount']==1 for m in matches),
 'MinimumLaunchWaitUpperBoundSeconds':min(m['LaunchWaitUpperBoundSeconds'] for m in matches),
 'MaxStartReceiptAfterLaunchBeginSeconds':max(m['StartReceivedAfterLaunchBeginSeconds'] for m in matches),
 'Limitation':'TIME_CREATED reflects WMI event creation; do not treat as exact process birth/death or minimum detectable lifetime. PIDs unique within this bounded probe set, not general identity proof.',
 'Pairs':matches}
(R/'coverage-analysis-v2.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='Pairs'},indent=2))
share=json.loads((R/'sharing-results.json').read_text());print('Closed-reader successful replacements',sum(x['AfterReaderClosedSucceeded'] is True for x in share))
resources=[json.loads(s) for s in (R/'resources-v2.jsonl').read_text().splitlines()];cpus={}
for r in resources:
 for p in r['Processes']:
  if p['CPU'] is not None:cpus.setdefault(str(p['PID']),{'Name':p['Name'],'Values':[]})['Values'].append(p['CPU'])
cpu={pid:{'Name':v['Name'],'CPUSecondsObservedDelta':max(v['Values'])-min(v['Values'])} for pid,v in cpus.items()}
(R/'process-cpu-summary.json').write_text(json.dumps(cpu,indent=2))
