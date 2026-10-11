import pathlib,json,hashlib,zipfile,sys,collections
R=pathlib.Path(__file__).parent;P=R.parent/'stage6-dataset-rehome-20260920'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=read(P/'failure-summary.json');F=pathlib.Path(s['run']);C=F.parent;receipt=read(P/'archive-verification.json');A=pathlib.Path(receipt['path'])
assert sha(A/'evidence.zip')==receipt['zipSHA256'] and sha(A/'archive-manifest.json')==receipt['manifestSHA256']
m=read(A/'archive-manifest.json')
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==receipt['members']==196
 for x in m['files']:
  assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256']==sha(pathlib.Path(x['source']))
 assert z.read('archive-manifest.json')==(A/'archive-manifest.json').read_bytes()
for x in read(C/'run-source.json'):assert sha(C/x['name'])==x['sha256']
frozen=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns) for p in sorted(F.rglob('*')) if p.is_file()]
def save(n,v):
 with (R/n).open('x') as f:json.dump(v,f,indent=2)
save('freeze.json',dict(archive=receipt,rawFiles=frozen,sourceManifest=read(C/'run-source.json'),sourceManifestSHA256=sha(C/'run-source.json'),protectedAccess=False))
sys.path.insert(0,str(C));import cleanup_checker
d=cleanup_checker.load(F);v=cleanup_checker.check(d);assert v['status']=='PASS'
p=next(x for x in read(F/'probe-timings.json') if x['pid']==23408)
k=next(x for x in d['kernel']['rows'] if (x['pid'],x['created'])==(p['pid'],p['initialKernelTimes'][0]));origin=p['launchRequestedQpc'];freq=p['frequency'];rel=lambda q:(q-origin)/freq
desc=[x for x in d['kernel']['rows'] if x['parentSequence']==k['sequence']]
parent=next(x for x in d['kernel']['rows'] if x['sequence']==k['parentSequence'])
def event(pid,kind):return next(x for x in d['events'] if x['pid']==pid and x['kind']==kind)
def persisted(e):return next(x['persistedQpc'] for x in d['receipts'] if x['queueSequence']==e['queueSequence'])
e=event(23408,'stop');timeline=[]
def add(name,q,source):timeline.append(dict(stage=name,qpc=q,secondsFromProbeLaunch=rel(q),source=source))
for name,key in [('launch','launchRequestedQpc'),('CreateProcess begin','createProcessCalledQpc'),('CreateProcess returned','createProcessReturnedQpc'),('handle acquired','handleRetainedQpc'),('hard deadline observed','failureCaughtQpc'),('independent wait returned timeout','observerReturnedQpc'),('final probe cleanup reconciliation','reconciledQpc')]:add(name,p[key],'probe-timings.json')
for name,key in [('kernel process start','startQpc'),('kernel exit event','stopQpc'),('kernel tracer observed signaled handle','signalObservedQpc'),('kernel STOP callback','stopCallbackQpc')]:add(name,k[key],'etw-result.json')
for x in desc:add('child '+str(x['pid'])+' created',x['startQpc'],'kernel parent sequence '+x['parentSequence']);add('child '+str(x['pid'])+' exit',x['stopQpc'],'etw-result.json')
add('application STOP callback',e['receivedQpc'],'app-events.jsonl');add('application STOP persisted',persisted(e),'app-receipts.json')
sam=next(x for x in read(F/'sampler-results.json')['queries'] if x['pid']==7712)
sk=next(x for x in d['kernel']['rows'] if (x['pid'],x['created'])==(7712,sam['created']))
for name,key in [('sampler query requested','launchQpc'),('sampler CreateProcess began','createBeginQpc'),('sampler CreateProcess returned','createReturnedQpc'),('sampler resumed','resumeQpc'),('sampler cleanup began','cleanupBeginQpc'),('sampler cleanup returned failed','cleanupEndQpc')]:add(name,sam[key],'sampler-results.json')
add('sampler kernel process start',sk['startQpc'],'etw-result.json');add('sampler kernel exit',sk['stopQpc'],'etw-result.json');add('sampler signal observed',sk['signalObservedQpc'],'etw-result.json')
se=event(7712,'stop');add('sampler STOP callback',se['receivedQpc'],'app-events.jsonl');add('sampler STOP persisted',persisted(se),'app-receipts.json')
save('timeline.json',dict(frequency=freq,originQpc=origin,clock='Windows QPC same host',events=sorted(timeline,key=lambda x:x['qpc']),unknown=['probe entry marker','intended work begin/end','internal initialization/cleanup','exact kernel signal instant','sampler worker entry','sampler normal query work begin/end','individual termination API entry/return'],probe=p,kernelProbe=k,parent=parent,children=desc,sampler=sam,kernelSampler=sk))
assert sha(C/'J6Probe.exe')==sha(pathlib.Path(r'C:\Windows\System32\whoami.exe'))
st=read(F/'stage-timing.json');groups=collections.defaultdict(list)
for x in st['spans']:groups[x['stage']].append(x['seconds'])
obs=sam['jobCleanupObservations'];overlap=max(0,min(sk['stopQpc'],k['stopQpc'])-max(sam['createBeginQpc'],k['startQpc']))/freq
summary=dict(archiveVerifiedMembers=196,rawFilesFrozen=len(frozen),probeImageSHA256=sha(C/'J6Probe.exe'),probeIsByteIdenticalToSystemWhoami=True,probeLifetimeSeconds=(int(k['exitFiletime'])-int(k['created']))/1e7,probeCreationCallSeconds=(p['createProcessReturnedQpc']-p['createProcessCalledQpc'])/freq,probeCPU100ns=p['finalKernelTimes'][2:],childCount=len(desc),childCreatedAfterSeconds=(int(desc[0]['created'])-int(k['created']))/1e7,childLifetimeSeconds=(int(desc[0]['exitFiletime'])-int(desc[0]['created']))/1e7,childAliveAtHardDeadline=any(x['startQpc']<=p['failureCaughtQpc']<x['stopQpc'] for x in desc),probeDelayStage='UNKNOWN: after process creation, before late console-helper creation; no internal entry/stack evidence',samplerCreateSeconds=(sam['createReturnedQpc']-sam['createBeginQpc'])/freq,samplerElapsedBeforeResumeSeconds=(sam['resumeQpc']-sam['launchQpc'])/freq,samplerCleanupSeconds=(sam['cleanupEndQpc']-sam['cleanupBeginQpc'])/freq,samplerPredicateObservations=len(obs),samplerPredicateSpanSeconds=(obs[-1]['qpc']-obs[0]['qpc'])/freq,samplerQueryMode=sam['mode'],samplerReason=sam['reason'],samplerCleanupUnprovenAtBoundary=True,samplerEventualExitProved=True,temporalOverlapSeconds=overlap,commonCause='NOT_ESTABLISHED',heartbeatMax=max(x['interval'] for x in d['heartbeat']),monitorLongest=max(st['spans'],key=lambda x:x['seconds']),monitorStageMaxima={k:max(v) for k,v in groups.items()},timingOverflow=st['overflow'],lifecycle={k:v[k] for k in ('status','total','appStarts','appStops','handleConfirmed','kernelPostExit','insufficient','externalEventIdentifierCollisions','queueIdentityCollisions')},queue=d['app']['queue'],samplerHasDiskTelemetry=False,securityScanningTelemetry='NOT_CAPTURED',protectedAccess=False,productionChanged=False)
save('preserved-summary.json',summary);save('exit-review.json',v)
print(json.dumps({k:v for k,v in summary.items() if k!='monitorStageMaxima'},indent=2))
