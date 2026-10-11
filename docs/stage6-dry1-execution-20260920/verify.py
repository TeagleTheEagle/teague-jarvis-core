import pathlib,json,hashlib,zipfile,datetime
R=pathlib.Path(__file__).parent;pre=json.loads((R/'preflight.json').read_text());C=pathlib.Path(pre['code'])
run=C/'integrated-dry1-8c2cbaeef9d04a8080b9bcf22fae89cd';repo=R.parent.parent
def read(n):return json.loads((run/n).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,x):
 with (R/n).open('x') as f:json.dump(x,f,indent=2)
kernel=read('etw-result.json');known={}
for x in kernel['rows']:known[(x['pid'],x['created'])]=dict(pid=x['pid'],created=x['created'],role='kernel-observed',kernelExit=x['exitFiletime'])
for role,x in read('observer-identities.json').items():known[(x['pid'],x['created'])]=dict(pid=x['pid'],created=x['created'],role=role,kernelExit=None)
launch=read('launcher.json');known[(launch['pid'],launch['creationFiletime'])]=dict(pid=launch['pid'],created=launch['creationFiletime'],role='launcher',kernelExit=None)
put('known-identities.json',list(known.values()))
assert read('integration-result.json')['status']=='DRY_RUN_1_PASS'
assert read('contract.json')['scenario']=='dry1' and read('contract.json')['source']==pre['source']
assert not any((run/n).exists() for n in ('primary-failure.json','hash-failure.json','launcher-error.txt'))
state=read('state.json');assert state['phase']=='VERIFIED' and state['sequence']==12 and not state['failed']
assert [x['phase'] for x in state['history']]==['PREPARED','OBSERVERS_READY','WORKLOAD_RUNNING','HASH1_COMPLETE','HASH2_COMPLETE','METADATA_VERIFIED','WORKLOAD_CLOSED','OBSERVERS_CLOSED','CLEANUP_VERIFIED','FINALIZED','MANIFESTED','ARCHIVED','VERIFIED']
assert all(a['qpc']<b['qpc'] for a,b in zip(state['history'],state['history'][1:]))
one=read('hash-pass-1.json');two=read('hash-pass-2.json');assert one['files']==two['files'] and len(one['files'])==12
assert one['beginQpcNs']<one['endQpcNs']<=two['beginQpcNs']<two['endQpcNs']
before={x['name']:dict(bytes=x['size'],mtime_ns=x['mtime_ns']) for x in pre['syntheticInventory']}
source=pathlib.Path(pre['source']);after={p.name:dict(bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns) for p in source.iterdir()}
assert after==before==read('contract.json')['inventory']
assert all(dict(bytes=x['bytes'],mtime_ns=x['mtime_ns'])==before[n] for n,x in one['files'].items())
cleanup=read('integrated-cleanup.json');assert cleanup['status']=='PASS' and cleanup['insufficient']==0 and not cleanup['errors'] and cleanup['primaryFailure'] is None
assert cleanup['total']==cleanup['handleConfirmed']+cleanup['kernelPostExit']==cleanup['appStarts']==cleanup['appStops']==cleanup['kernelCreates']==cleanup['kernelExits']
assert cleanup['queueIdentityCollisions']==0 and all(not x['errors'] for x in cleanup['identities'])
producer=read('stress-result.json');assert producer['status']=='DIAGNOSTIC_COMPLETE' and producer['primary_failure'] is None
for n in ('app-exit.json','launcher-result.json'):
 v=read(n);assert v['exited'] and v['exitCode']==0
assert read('launcher-result.json')['workExit']==0
app=read('app-result.json');q=app['queue'];assert app['success'] and app['durableFinalization'] and app['unsubscribed'] and not app['error'] and not app['tapOverflow'] and not app['tapErrors']
assert q['enqueued']==q['selected']==q['persisted']==q['removed'] and q['remaining']==0 and not q['failed']
for name in ('faults','eventsLost','realtimeBuffersLost','buffersLost','flushResult','stopResult','consumerResult'):assert kernel[name]==0
heartbeat=read('app-heartbeats.json');assert heartbeat and all(0<=x['interval']<10 for x in heartbeat)
samples=read('collector-health-samples.json')+read('hash-health-samples.json');assert samples and all(0<=x['age']<10 for x in samples)
probes=read('probe-timings.json');assert probes and all(not x['hardDeadlineFailure'] and not x['independentObserverFailed'] and x['observerResult']==0 and x['actualExitCode']==0 and x['finalHandleState']==0 and x['policy']['confirmedElapsed']<13.6 and x['policy']['exitElapsedEstimate']<13.6 and x['policy']['hardSeconds']==13.6 for x in probes)
for x in pre['candidateHashes']:assert sha(pathlib.Path(x['path']))==x['expected']
for x in pre['applicationHashes']:assert sha(repo/x['path'])==x['expected']
for x in read('source-hashes.json'):assert sha(C/x['name']).lower()==x['sha256'].lower()
manifestHash=sha(run/'baseline-manifest.json');assert manifestHash==read('baseline-manifest-hash.json')['sha256']==read('archive-verification.json')['manifestSHA256']
assert read('baseline-manifest.json')['files']==one['files']
members=read('archive-manifest.json');receipt=read('archive-verification.json');assert receipt['status']=='HASH_VERIFIED' and sha(run/'evidence.zip')==receipt['sha256']
with zipfile.ZipFile(run/'evidence.zip') as z:
 assert len(z.namelist())==receipt['members']==len(members)+1
 assert set(z.namelist())=={x['name'] for x in members}|{'archive-manifest.json'}
 for x in members:
  b=z.read(x['name']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'] and sha(run/x['name'])==x['sha256']
 assert z.read('archive-manifest.json')==(run/'archive-manifest.json').read_bytes()
keys={(x['pid'],x['created']) for x in cleanup['identities']};tracked=[x for x in kernel['rows'] if (x['pid'],x['created']) in keys]
worker=next(x for x in producer['launched'] if x['role']=='hash-worker');kw=next(x for x in tracked if x['pid']==worker['pid'] and x['created']==worker['created']);freq=read('etw-ready.json')['frequency']
assert kw['startQpc']/freq<=one['beginQpcNs']/1e9<two['endQpcNs']/1e9<=kw['stopQpc']/freq
summary=dict(status='PASS_PENDING_FINAL_HOST_CHECK_AND_ARCHIVE',run=str(run),syntheticFiles=12,syntheticBytes=sum(x['bytes'] for x in one['files'].values()),hashPass1='PASS',hashPass2='PASS',hashPass1Seconds=(one['endQpcNs']-one['beginQpcNs'])/1e9,hashPass2Seconds=(two['endQpcNs']-two['beginQpcNs'])/1e9,metadataPreserved=True,cleanup={k:v for k,v in cleanup.items() if k not in ('identities','outsideKernel','outsideAppEvents')},outsideKernel=cleanup['outsideKernel'],outsideApplicationEventCount=len(cleanup['outsideAppEvents']),maximumTrackedLifetimeSeconds=max((int(x['exitFiletime'])-int(x['created']))/1e7 for x in tracked),probeCount=len(probes),maximumProbeConfirmedSeconds=max(x['policy']['confirmedElapsed'] for x in probes),maximumProbeLifetimeSeconds=max((int(x['finalKernelTimes'][1])-int(x['finalKernelTimes'][0]))/1e7 for x in probes),hardDeadlineViolations=0,maximumHeartbeatInterval=max(x['interval'] for x in heartbeat),maximumHeartbeatAge=max(x['age'] for x in samples),queue=q,finalization='PASS',durableFinalization='PASS',manifestSHA256=manifestHash,runArchive=receipt,candidateHashCount=len(pre['candidateHashes']),applicationHashCount=len(pre['applicationHashes']),hashesUnchanged=True,protectedAccess=False,productionChanged=False,dryRun2Executed=False,state=state,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
put('run-verification.json',summary)
print(json.dumps({k:v for k,v in summary.items() if k not in ('cleanup','outsideKernel','queue','state')}))
