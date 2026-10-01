import pathlib,json
R=pathlib.Path(__file__).resolve().parent;C=pathlib.Path(json.loads((R/'plan.json').read_text(encoding='utf-8-sig'))['live_code']);root=next(C.glob('harden-e-*'))
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
rows=read(root/'probe-timings.json');p=next(x for x in rows if x.get('hardDeadlineFailure'));origin=p['launchRequestedQpc'];f=p['frequency']
def rel(q):return (q-origin)/f if q is not None else 'UNKNOWN'
tap=read(root/'tap.json');pipeline=read(root/'pipeline.json');tree=read(root/'tree-handles.json');worker=read(root/'worker-trace.json')
children=[x for x in tap if x['stage']=='B-WMI-callback' and x['kind']=='start' and x['parentPid']==p['pid']]
childids={x['pid'] for x in children};chrows=[x for x in tree['rows'] if x['pid'] in childids]
target=next(x for x in tree['rows'] if x['pid']==p['pid'])
relevant=[x for x in tap if x['pid']==p['pid'] or x['pid'] in childids]
overlap=[]
for row in worker:
 q=row.get('qpc',row.get('begin',row.get('start',0)));end=row.get('end',q)
 if q<=p['observerReturnedQpc'] and end>=origin:overlap.append(row)
stop=[x for x in tap if x['stage']=='A-callback' and x['kind']=='stop' and x['pid']==p['pid']]
enqueued=[x for x in tap if x['stage']=='A-enqueue' and x['kind']=='stop' and x['pid']==p['pid']]
persisted=[x for x in pipeline if x['stage']=='persisted' and x['pid']==p['pid'] and 'Stop' in x['source']]
v=dict(identity=p,timeline=dict(launch=0,createReturn=rel(p['createProcessReturnedQpc']),mainHandleIdentityCaptured=rel(p['identityCapturedQpc']),duplicateHandleRetained=rel(target['handleRetainedQpc']),internalEntry='UNKNOWN',workBegin='UNKNOWN',workEnd='UNKNOWN',internalCleanup='UNKNOWN',hardFailure=rel(p['timeoutCaughtQpc']),observerWaitResult=p['observerResult'],observerSignalObserved=rel(p['observerReturnedQpc']),treeSignalObserved=rel(target['signalObservedQpc']),stopCallback=[rel(x['qpc']) for x in stop],stopEnqueued=[rel(x['qpc']) for x in enqueued],stopPersisted=[rel(x['qpc']) for x in persisted],kernelExitFiletime=p['finalKernelTimes'][1]),kernelLifetime=(int(p['finalKernelTimes'][1])-int(p['finalKernelTimes'][0]))/1e7,cpuSeconds=(int(p['finalKernelTimes'][2])+int(p['finalKernelTimes'][3]))/1e7,childStartEvents=children,retainedChildren=chrows,events=relevant,workerOverlapping=overlap,workerTraceFields=list(worker[-1]),primary=read(root/'primary-failure.json'),secondary=[json.loads(x) for x in (root/'secondary-failures.jsonl').read_text().splitlines()],workerOutput=read(root/'workload-cleanup.json'),queue=read(root/'queue-state.json'))
with (R/'hard-reproduction.json').open('x') as out:json.dump(v,out,indent=2)
print(json.dumps(dict(timeline=v['timeline'],kernelLifetime=v['kernelLifetime'],cpuSeconds=v['cpuSeconds'],childIds=list(childids),retainedChildren=len(chrows),workerOverlap=len(overlap),workerTraceFields=v['workerTraceFields'])))
