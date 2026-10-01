"""Read completed small-run evidence only; no process launch or dataset modification."""
import pathlib,json,hashlib,collections,datetime
R=pathlib.Path(__file__).parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(R/'plan.json');C=pathlib.Path(plan['code']);checks=[]
def check(name,condition):
 checks.append(dict(name=name,passed=bool(condition)))
 if not condition:raise AssertionError(name)
for x in plan['sourceChecks']:check('prior source '+x['path'],sha(pathlib.Path(x['path']))==x['sha256'])
for x in read(R/'candidate-hashes.json'):check('current source '+x['name'],sha(C/x['name'])==x['sha256'])
for x in plan['smallFiles']:
 p=pathlib.Path(plan['source'])/x['name'];s=p.stat()
 check('small source preserved '+x['name'],s.st_size==x['bytes'] and s.st_mtime_ns==x['mtime_ns'] and sha(p)==x['sha256'])
runs=[];identities=[]
for case,name in [('normal','protected-cda0e6c7d5774746afaef2d4e93602f8'),('controlled-startup-failure','protected-f188cd5baa194c3c9c307e33427bf8e3')]:
 p=C/name;r=lambda n:read(p/n)
 cleanup=r('integrated-cleanup.json' if case=='normal' else 'controlled-cleanup.json')
 check(case+' dual cleanup',cleanup['status']=='PASS' and cleanup['insufficient']==0 and cleanup['appStarts']==cleanup['appStops']==cleanup['total'])
 kernel=r('etw-result.json');trace=r('startup-events.json');app=r('app-result.json');launcher=r('launcher-result.json')
 check(case+' kernel loss/fault free',all(kernel[k]==0 for k in ('faults','eventsLost','realtimeBuffersLost','buffersLost','flushResult','stopResult','consumerResult')))
 check(case+' trace complete',trace['overflow']==0 and bool(trace['events']))
 check(case+' queue closure',app['success'] and app['queue']['remaining']==0 and app['queue']['enqueued']==app['queue']['persisted']==app['queue']['removed'])
 check(case+' observer exit',launcher['exited'] and launcher['exitCode']==0 and r('app-exit.json')['exited'] and r('app-exit.json')['exitCode']==0)
 heartbeat=max(x['interval'] for x in r('app-heartbeats.json'));check(case+' heartbeat',0<=heartbeat<10)
 lm=r('integration-launcher.json');check(case+' launcher entry/shutdown',lm[0]['event']=='LAUNCHER_ENTRY' and lm[-1]['event']=='FINAL_SHUTDOWN')
 sidecars={}
 for f in p.glob('integration-*-*.json'):
  rows=read(f);role=rows[0]['role'];sidecars[role]=rows
  check(case+' '+role+' entry/final',rows[0]['event']=='ENTRY' and rows[-1]['event']=='FINAL_SHUTDOWN')
  check(case+' '+role+' monotonic',all(a['qpc']<=b['qpc'] for a,b in zip(rows,rows[1:])))
  check(case+' '+role+' identity',any(k['pid']==rows[0]['pid'] and k['created']==rows[0]['created'] for k in kernel['rows']))
 check(case+' both marker roles',set(sidecars)=={'collector','hash-worker'})
 collector=sidecars['collector'];helperReturns={x['helper'] for x in collector if x['event']=='HELPER_RETURN'}
 check(case+' helper invocation/return',helperReturns=={'hash-worker','lifecycle-probe','resource-sampler'})
 check(case+' collector status marker',collector[-2]['event']=='COLLECTOR_RETURN' and collector[-2]['exitCode']==launcher['workExit'])
 covered={x['pid'] for x in trace['events']};roles={x['role']:x['pid'] for x in r('stress-result.json')['launched']}
 check(case+' detailed helper trace',all(pid in covered for pid in roles.values()) and r('stress-result.json')['collectorPid'] in covered)
 if case=='normal':
  a=r('hash-pass-1.json')['files'];b=r('hash-pass-2.json')['files']
  check('normal both passes identical',a==b)
  for x in plan['smallFiles']:check('normal expected preintegration hash '+x['name'],b[x['name']]['sha256']==x['sha256'])
  check('normal unchanged success semantics',r('stress-result.json')['status']=='DIAGNOSTIC_COMPLETE' and r('integration-result.json')['status']=='SYNTHETIC_PROTECTED_MODE_PASS' and r('state.json')['phase']=='VERIFIED')
  check('normal manifest hash',sha(p/'baseline-manifest.json')==r('baseline-manifest-hash.json')['sha256'])
 else:
  check('controlled failure remains failure',r('stress-result.json')['status']=='FAILED' and launcher['workExit']==1)
  check('controlled worker exception preserved',any(x['event']=='EXCEPTION' and x['controlled'] for x in sidecars['hash-worker']))
  check('controlled no hash/no success manifest',not any((p/n).exists() for n in ('hash-pass-1.json','hash-pass-2.json','baseline-manifest.json','integration-result.json')))
  check('controlled actual error',b'CONTROLLED_HASH_START_FAILURE' in (p/'hash-worker-stderr.bin').read_bytes())
 identities.extend(dict(pid=x['pid'],created=x['created'],image=x['image']) for x in kernel['rows'])
 launch=r('launcher.json');identities.append(dict(pid=launch['pid'],created=launch['creationFiletime'],image=launch['image']))
 identities.extend(r('observer-identities.json').values())
 runs.append(dict(case=case,path=str(p),identities=cleanup['total'],retained=cleanup['handleConfirmed'],qualifiedPostExit=cleanup['kernelPostExit'],starts=cleanup['appStarts'],stops=cleanup['appStops'],heartbeatMax=heartbeat,traceEvents=len(trace['events']),traceCapacity=200000,traceOverflow=trace['overflow'],providers=dict(collections.Counter(x['provider'] for x in trace['events'])),eventsByPid=dict(collections.Counter(x['pid'] for x in trace['events'])),detailedRoles=roles,cleanup='PASS',primaryStatus=r('stress-result.json')['status'],normalArchive=r('archive-verification.json') if case=='normal' else None))
summary=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='BLOCKED',blocker='LARGE_RUN_TRACE_RETENTION_CAPACITY_NOT_VALIDATED',runs=runs,checks=len(checks),passed=sum(x['passed'] for x in checks),failed=sum(not x['passed'] for x in checks),largeRunExecuted=False,protectedAccess=False,productionChanges=False,historicalCauses='UNCONFIRMED',markerLimitation='Python wrapper entry is not native PE entry. Standalone J6EntryObserve debug-register experiment is not inserted into collector probe creation.',capacityLimitation='Existing 200000-event cap unchanged. Small normal run already retained 155105 events. Frozen large campaign admits repeated probes during a 788-second hold; previous 80-probe standalone trace retained 183217 events. Full large helper coverage cannot be certified from these small tests.')
(R/'checks.json').write_text(json.dumps(checks,indent=2));(R/'analysis.json').write_text(json.dumps(summary,indent=2));(R/'identities.json').write_text(json.dumps(identities,indent=2))
print(json.dumps(summary,indent=2))
