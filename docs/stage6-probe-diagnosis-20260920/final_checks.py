"""Post-run source/evidence validation and read-only timing correlation."""
import pathlib,json,hashlib,ast,time,collections,sys,importlib.util
R=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(n,x):
 with (R/n).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
CODE=pathlib.Path(read(R/'plan.json')['live_code'])
syntax=[]
for p in sorted(list(CODE.glob('*.py'))+list(R.glob('*.py'))):
 ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p));syntax.append(str(p))
save('python-syntax.json',dict(status='PASS',method='ast.parse; no imports, bytecode or runtime execution',files=syntax))
prior=R.parent/'stage6-dlive-20260920'
oldReceipt=read(prior/'archive-verification.json');oldzip=prior/'evidence.zip';oldmanifest=prior/'archive-manifest.json'
oldOk=sha(oldzip)==oldReceipt['zip_sha256'] and sha(oldmanifest)==oldReceipt['manifest_sha256']
if not oldOk:raise RuntimeError('Previous evidence archive changed')
save('prior-archive-preservation.json',dict(unchanged=True,zipSHA256=sha(oldzip),manifestSHA256=sha(oldmanifest),receipt=oldReceipt))
clock=time.get_clock_info('perf_counter')
if clock.implementation!='QueryPerformanceCounter()':raise RuntimeError('Do not assume perf_counter/QPC shared origin')
overlaps=[];probeChecks=[]
for d in sorted(CODE.iterdir()):
 if not d.is_dir() or not (d/'case.json').exists():continue
 a=read(d/'probe-analysis.json');rows=read(d/'probe-timings.json');work=d/f"workload-{a['mode']}.json";reads=read(work)['reads'] if work.exists() else []
 for p in rows:
  f=p['frequency'];m=next(x for x in a['measurements'] if x['pid']==p['pid'])
  assert p['launchRequestedQpc']<=p['createProcessCalledQpc']<=p['createProcessReturnedQpc']<=p['popenReturnedQpc']<=p['mainWaitEnteredQpc']
  assert p['observerResult']==p['finalHandleState']==p['actualExitCode']==0
  assert int(p['finalKernelTimes'][1])>int(p['finalKernelTimes'][0])
  if p['timedOut']:assert p['immediateHandleState']==258 and m['kernelLifetime']>5 and 5<=m['mainWaitSeconds']<5.1
  probeChecks.append(dict(run=d.name,pid=p['pid'],status='CONSISTENT',timedOut=p['timedOut']))
  if m['kernelLifetime']>.5:
   start=p['launchRequestedQpc']/f;end=p['observerReturnedQpc']/f
   matching=[dict(start=x[0],seconds=x[1],bytes=x[2],overlapSeconds=max(0,min(end,x[0]+x[1])-max(start,x[0]))) for x in reads if x[1]>.1 and x[0]<end and x[0]+x[1]>start]
   overlaps.append(dict(run=d.name,pid=p['pid'],lifetime=m['kernelLifetime'],timedOut=p['timedOut'],slowReadOverlap=matching,note='Temporal overlap is not a thread stack, blocked-call identity or proof of causation.'))
save('timing-consistency.json',dict(status='PASS',probes=len(probeChecks),checks=probeChecks))
save('slow-probe-read-overlap.json',dict(clock=vars(clock),rows=overlaps))
sys.path.insert(0,str(CODE));import workspace
pathchecks=[]
def rejected(name,action):
 try:action()
 except (ValueError,RuntimeError):pathchecks.append(dict(name=name,status='PASS'));return
 raise AssertionError(name)
rejected('C root rejected',lambda:workspace.check_path('C:/temp/probe'))
rejected('D sibling rejected',lambda:workspace.check_path('D:/unrelated/probe'))
rejected('parent traversal rejected',lambda:workspace.check_path(CODE/'../escape'))
rejected('malformed run rejected',lambda:workspace.run_dir('../escape'))
for d in CODE.iterdir():
 if d.is_dir() and (d/'case.json').exists():
  for name in ('heartbeat.jsonl','events.jsonl','collector-finished.json','temp','probe-timings.json'):
   assert workspace.check_path(d/name).drive.upper()=='D:'
save('path-integrity.json',dict(status='PASS',negativeCases=pathchecks,existingSevenRunsContained=True,source='unchanged workspace.py; not a rerun of full 69-test relocation suite'))
queue=next(CODE.glob('queue-tests-*/result.json'));q=read(queue)
assert q['status']=='PASS' and q['results']['checks']==222
save('queue-regression.json',dict(path=str(queue),result=q))
print(json.dumps(dict(pythonFiles=len(syntax),timedProbes=len(probeChecks),slowProbes=len(overlaps),queueChecks=222,priorArchiveUnchanged=oldOk,pathChecks='PASS')))
