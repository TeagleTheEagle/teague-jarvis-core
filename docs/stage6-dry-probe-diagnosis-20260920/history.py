import pathlib,json,hashlib
R=pathlib.Path(__file__).parent;OLD=pathlib.Path(json.loads((R/'plan.json').read_text())['previous']);D=OLD/'dry1-e778870314ae4c3dbfc5274a9fb7a3d0'
def read(n):return json.loads((D/n).read_text(encoding='utf-8-sig'))
p=next(x for x in read('probe-timings.json') if x['pid']==9240);origin=p['launchRequestedQpc'];f=p['frequency']
def stamp(q):return dict(qpc=q,sinceLaunchSeconds=(q-origin)/f) if q is not None else 'UNKNOWN'
tap=[x for x in read('tap.json') if x['pid']==9240];pipe=[x for x in read('pipeline.json') if x['pid']==9240];queue=read('queue-entries.json');events=[json.loads(x) for x in (D/'events.jsonl').read_text().splitlines()];e=next(x for x in events if x['pid']==9240 and x['kind']=='stop')
def first(rows,stage):return next((x['qpc'] for x in rows if x['stage']==stage),None)
timeline={
 'T0 launch requested':stamp(origin),'T1 CreateProcess returned':stamp(p['createProcessReturnedQpc']),
 'T2 retained handle acquired':'UNKNOWN exact assignment; bounded by CreateProcess return and Popen return; initial identity capture separately recorded',
 'Popen returned':stamp(p['popenReturnedQpc']),'Initial identity recorded':stamp(p['identityCapturedQpc']),
 'T3 process entry marker':'UNKNOWN','T4 intended work started':'UNKNOWN','T5 intended work completed':'UNKNOWN',
 'T6 process-internal cleanup began':'UNKNOWN','T7 hard deadline observed':stamp(p['timeoutCaughtQpc']),
 'T8 independent observer timeout':stamp(p['observerReturnedQpc']),'T9 process exit began':'UNKNOWN','T10 kernel handle signaled':'UNKNOWN',
 'T11 primary STOP callback':stamp(first([x for x in tap if x['kind']=='stop'],'A-callback')),
 'T12 primary STOP enqueued':stamp(first([x for x in tap if x['kind']=='stop'],'A-enqueue')),
 'T13 STOP append completed':stamp(first([x for x in pipe if x['eventId']==e['eventIdentifier']],'persisted')),
 'T14 cleanup fully completed':'UNKNOWN exact instant; collector never captured final exit code/kernel exit time for PID9240; later identity scans found no live matching process'}
resources=read('resources.json');overlap=[x for x in resources if x['qpc']<=e['receivedQpc'] and x['endQpc']>=origin];counters={}
for row in overlap:
 for x in row['counters']:
  if isinstance(x['CookedValue'],(int,float)):counters.setdefault(x['Path'],[]).append(x['CookedValue'])
counterSummary={k:dict(n=len(v),min=min(v),max=max(v)) for k,v in counters.items()}
v=dict(pid=9240,created=p['initialKernelTimes'][0],executable=p['executable'],sha256=hashlib.sha256((OLD/'J6Probe.exe').read_bytes()).hexdigest(),matchesSystemWhoami=hashlib.sha256((OLD/'J6Probe.exe').read_bytes()).digest()==hashlib.sha256(pathlib.Path(r'C:\Windows\System32\whoami.exe').read_bytes()).digest(),parentPid=p['parentPid'],arguments=p['arguments'],cwd=p['cwd'],stdout=p['stdout'],stderr=p['stderr'],close_fds=p['close_fds'],creationflags=p['creationflags'],timeline=timeline,rawProbe=p,primaryTap=tap,pipeline=pipe,stop= e,queue=queue,resourceOverlap=overlap,counterSummary=counterSummary,limitations=['whoami executable is not instrumented; no process-entry marker','child process tree not recorded historically','exact inherited handle table and opened files/pipes/network not traced','resource samples correlate intervals; they do not prove causation','no first-pass manifest recorded; exact hash/read/stat stage during probe lifetime unknown','callback/enqueue ordering is observer timing; attached callback can run after original enqueue handler','cleanup failure overwrote collector summary but primary policyFailure survives in raw row'])
with (R/'historical-reconstruction.json').open('x') as out:json.dump(v,out,indent=2)
print(json.dumps(dict(identity={k:v[k] for k in ('pid','created','sha256','matchesSystemWhoami','parentPid')},timeline=timeline,resourceWindows=len(overlap))))
