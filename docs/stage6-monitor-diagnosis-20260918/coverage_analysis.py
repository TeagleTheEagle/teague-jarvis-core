import pathlib,json,datetime as dt,statistics
R=pathlib.Path(__file__).parent;D=R/'event-coverage-v2'
ev=[json.loads(s) for s in (D/'events.jsonl').read_text().splitlines()]
probes=json.loads((D/'probes.json').read_text(encoding='utf-8-sig'))
def stamp(s):return dt.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
matches=[]
for p in probes:
 lo=stamp(p['BeforeUtc']);hi=stamp(p['AfterUtc'])
 related=[e for e in ev if e['PID']==p['PID'] and lo-.1<=int(e['NativeFileTime'])/1e7-11644473600<=hi+.1]
 a=[e for e in related if e['Kind']=='start'];b=[e for e in related if e['Kind']=='stop']
 matches.append({'PID':p['PID'],'RequestedName':p['Name'],'StartCount':len(a),'StopCount':len(b),'StopName':b[0]['Name'] if b else None,
 'NativeLifetimeSeconds':(int(b[0]['NativeFileTime'])-int(a[0]['NativeFileTime']))/1e7 if len(a)==len(b)==1 else None})
lives=[m['NativeLifetimeSeconds'] for m in matches if m['NativeLifetimeSeconds'] is not None]
lat=[stamp(e['ReceivedUtc'])-(int(e['NativeFileTime'])/1e7-11644473600) for e in ev]
result={'Trials':len(matches),'MatchedStarts':sum(m['StartCount']==1 for m in matches),'MatchedStops':sum(m['StopCount']==1 for m in matches),
 'MinimumObservedLifetimeSeconds':min(lives),'MaximumObservedLifetimeSeconds':max(lives),'MaxDeliveryLatencySeconds':max(lat),'Pairs':matches}
(R/'coverage-analysis.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='Pairs'},indent=2))
share=json.loads((R/'sharing-results.json').read_text())
print('Failed replacements subsequently succeed after closing:',sum(x['AfterReaderClosedSucceeded'] is True for x in share))
resources=[json.loads(s) for s in (R/'resources-v2.jsonl').read_text().splitlines()];cpus={}
for r in resources:
 for p in r['Processes']:
  if p['CPU'] is not None:cpus.setdefault(str(p['PID']),{'Name':p['Name'],'Values':[]})['Values'].append(p['CPU'])
cpu={pid:{'Name':v['Name'],'CPUSecondsObservedDelta':max(v['Values'])-min(v['Values'])} for pid,v in cpus.items()}
(R/'process-cpu-summary.json').write_text(json.dumps(cpu,indent=2))
