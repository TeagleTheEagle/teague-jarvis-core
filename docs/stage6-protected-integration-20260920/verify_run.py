import pathlib,json,hashlib,zipfile,sys,datetime
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'candidate.json').read_text())['code']);name=sys.argv[1];phase=sys.argv[2];run=C/name
assert run.parent==C and name.startswith('protected-')
def read(n):return json.loads((run/n).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
v=read('contract.json');assert v['mode']=='protected_baseline' and v['synthetic'] is True
assert read('integration-result.json')['status']=='SYNTHETIC_PROTECTED_MODE_PASS'
assert read('state.json')['phase']=='VERIFIED' and not read('state.json')['failed']
assert not any((run/n).exists() for n in ('primary-failure.json','hash-failure.json','launcher-error.txt'))
one=read('hash-pass-1.json');two=read('hash-pass-2.json');assert one['files']==two['files'] and len(one['files'])==12
assert one['endQpcNs']<two['beginQpcNs']
assert sum(x['bytes'] for x in one['files'].values())==59665402098
for n,x in one['files'].items():
 p=pathlib.Path(v['source'])/n;s=p.stat();assert s.st_size==x['bytes'] and s.st_mtime_ns==x['mtime_ns'] and s.st_ino==x['fileId']
cleanup=read('integrated-cleanup.json');assert cleanup['status']=='PASS' and not cleanup['errors'] and cleanup['insufficient']==0
assert cleanup['total']==cleanup['appStarts']==cleanup['appStops']==cleanup['kernelCreates']==cleanup['kernelExits']==cleanup['handleConfirmed']+cleanup['kernelPostExit']
k=read('etw-result.json');assert k['requestedStop']
for n in ('faults','eventsLost','realtimeBuffersLost','buffersLost','flushResult','stopResult','consumerResult'):assert k[n]==0
a=read('app-result.json');q=a['queue'];assert a['success'] and a['unsubscribed'] and a['durableFinalization'] and not a['error'] and not a['tapErrors'] and not a['tapOverflow']
assert q['enqueued']==q['persisted']==q['removed']==q['selected'] and q['remaining']==0 and not q['failed']
hb=read('app-heartbeats.json');assert hb and all(0<=x['interval']<10 for x in hb)
hs=read('hash-health-samples.json')+read('collector-health-samples.json');assert hs and all(0<=x['age']<10 for x in hs)
probes=read('probe-timings.json');assert probes and all(not x['hardDeadlineFailure'] and not x['independentObserverFailed'] and x['actualExitCode']==0 and x['finalHandleState']==0 and x['policy']['confirmedElapsed']<13.6 for x in probes)
res=read('monitor-resources.json');assert res
elapsed=read('metadata-verified.json')['elapsedSeconds'];assert elapsed>=v['thresholds']['hold']
manifest=sha(run/'baseline-manifest.json');assert manifest==read('baseline-manifest-hash.json')['sha256']
ar=read('archive-verification.json');assert ar['status']=='HASH_VERIFIED' and sha(run/'evidence.zip')==ar['sha256']
with zipfile.ZipFile(run/'evidence.zip') as z:
 members=read('archive-manifest.json');assert len(z.namelist())==len(members)+1==ar['members']
 for x in members:assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256'] and sha(run/x['name'])==x['sha256']
 assert z.read('archive-manifest.json')==(run/'archive-manifest.json').read_bytes()
for x in json.loads((R/'candidate-source.json').read_text()):assert sha(C/x['name'])==x['sha256']
known={}
for x in k['rows']:known[(x['pid'],x['created'])]=dict(pid=x['pid'],created=x['created'])
for x in read('observer-identities.json').values():known[(x['pid'],x['created'])]=dict(pid=x['pid'],created=x['created'])
l=read('launcher.json');known[(l['pid'],l['creationFiletime'])]=dict(pid=l['pid'],created=l['creationFiletime'])
with (R/(phase+'-identities.json')).open('x') as f:json.dump(list(known.values()),f,indent=2)
summary=dict(status='PASS_PENDING_HOST_CLEANUP',phase=phase,run=str(run),files=12,bytes=sum(x['bytes'] for x in one['files'].values()),hashPassSeconds=[(x['endQpcNs']-x['beginQpcNs'])/1e9 for x in (one,two)],perFileSeconds=[x['perFileSeconds'] for x in (one,two)],metadataPreserved=True,elapsedSeconds=elapsed,heartbeatMax=max(x['interval'] for x in hb),heartbeatAgeMax=max(x['age'] for x in hs),probes=len(probes),deadlineViolations=0,cleanup={n:x for n,x in cleanup.items() if n not in ('identities','outsideKernel','outsideAppEvents')},resources={n:dict(first=res[0][n],last=res[-1][n],max=max(x[n] for x in res)) for n in ('privateBytes','workingSet','handles','kernelPrivateBytes','kernelHandles','queueDepth','eventBytes')},manifestSHA256=manifest,archive=ar,sourceUnchanged=True,protectedAccess=False,productionChanged=False)
with (R/(phase+'-verification.json')).open('x') as f:json.dump(summary,f,indent=2)
print(json.dumps({n:x for n,x in summary.items() if n not in ('perFileSeconds','cleanup','resources')}))
