import pathlib,json,sys,hashlib,collections
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'diagnostic-workspace.json').read_text())['code']);sys.path.insert(0,str(C));import cleanup_checker
allids=[];summaries=[]
for F in sorted(C.glob('correlation-*')):
 if not F.is_dir():continue
 def read(n):return json.loads((F/n).read_text(encoding='utf-8-sig'))
 check=cleanup_checker.evaluate(F)
 with (R/(F.name+'-cleanup.json')).open('x') as f:json.dump(check,f,indent=2)
 probes=read('probe-timings.json');stages=read('stages.json');hashes=[]
 for p in sorted(F.glob('hash-*.json')):
  v=json.loads(p.read_text())
  if 'partialHash' not in v:continue
  dur=(v['end']-v['begin'])/1e7
  hashes.append(dict(file=p.name,seconds=dur,requestedSeconds=v['requestedSeconds'],bytes=v['bytes'],logicalBytesPerSecond=v['bytes']/dur,canceled=v['canceled'],readMaxSeconds=max((x['readEnd']-x['begin'])/1e7 for x in v['trace']),hashMaxSeconds=max((x['end']-x['readEnd'])/1e7 for x in v['trace'])))
 resources=read('diagnostic-resources.json');counters=collections.defaultdict(list)
 for row in resources['rows']:
  for x in row['counters']:
   if x['Status']==0:counters[x['Path'].split('\\',3)[-1]].append(x['CookedValue'])
 cpu={k:dict(min=min(v),max=max(v),samples=len(v)) for k,v in counters.items()}
 etw=read('etw-result.json');app=read('app-result.json');handles=read('tree-handles.json');producer=read('stress-result.json')
 for x in etw['rows']:allids.append(dict(pid=x['pid'],created=x['created']))
 for x in read('observer-identities.json').values():allids.append(dict(pid=x['pid'],created=x['created']))
 launch=read('launcher.json');allids.append(dict(pid=launch['pid'],created=launch['creationFiletime']))
 scopes={producer['collectorPid']};previous=None
 while previous!=scopes:previous=set(scopes);scopes|={x['pid'] for x in cleanup_checker.load(F)['events'] if x['kind']=='start' and x['parentPid'] in scopes}
 known={x['pid'] for x in etw['rows']};extra=scopes-known
 discrepancy=dict(extraAppPids=sorted(extra),events=[x for x in cleanup_checker.load(F)['events'] if x['pid'] in extra],parentKernel=[x for x in etw['rows'] if x['pid'] in {e['parentPid'] for e in cleanup_checker.load(F)['events'] if e['pid'] in extra}])
 s=dict(run=str(F),probeCount=len(probes),probeMaxSeconds=max(((int(x['finalKernelTimes'][1])-int(x['finalKernelTimes'][0]))/1e7 for x in probes),default=None),hardDeadlineFailures=sum(bool(x.get('hardDeadlineFailure')) for x in probes),heartbeatMaxSeconds=max(x['interval'] for x in read('app-heartbeats.json')),observerSuccess=app['success'],queue=app['queue'],stages=stages,hashing=hashes,resourceSampleCount=len(resources['rows']),resourceCounterMaxSeconds=max(((x['end']-x['begin'])/1e7 for x in resources['rows']),default=None),resourceErrors=resources['errors'],counters=cpu,cleanup={k:v for k,v in check.items() if k not in ('identities','outsideKernel','outsideAppEvents')},tree=dict(allExited=handles['allExited'],allHandlesClosed=handles['allHandlesClosed'],rows=len(handles['rows'])),discrepancy=discrepancy,producerStatus=producer['status'],primary=producer['primary_failure'],resourceHelperCleanup=read('resources-cleanup.json'))
 summaries.append(s)
with (R/'diagnostic-results.json').open('x') as f:json.dump(summaries,f,indent=2)
with (R/'diagnostic-identities.json').open('x') as f:json.dump(allids,f,indent=2)
for s in summaries:print(json.dumps({k:v for k,v in s.items() if k not in ('discrepancy','resourceHelperCleanup','counters','stages','cleanup','primary')}));print('RESOURCE_COUNTERS',json.dumps(s['counters']))
