"""Read-only failure reconciliation; writes new report receipts only."""
import pathlib,json,sys,zipfile,os,datetime
from verification import *
R=pathlib.Path(__file__).parent
P=R.parent/'stage6-protected-integration-20260920'
C=pathlib.Path(json.loads((R/'candidate.json').read_text())['code'])
F=C/'protected-3aec3ce0062c42a19077a2bad0571bd7'
prior=json.loads((R/'preflight.json').read_text())
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 PROTECTED COLLECTOR INTEGRATION 20260920')
m=verify_archive(A,prior['archive']);index={x['name']:x for x in m['files']}
with zipfile.ZipFile(A/'evidence.zip') as z: frozen=json.loads(z.read('report/candidate-source.json'))
count=verify_candidate(C,frozen)
verify_hash(C/'baseline-source.json',index['candidate/baseline-source.json']['sha256'])
cal,other=verify_calibration([(P/'calibration.json',index['report/calibration.json']['sha256']),(C/'calibration.json',index['candidate/calibration.json']['sha256'])]);assert cal==other
S=C/'large-synthetic'; names=[]
for d,dirs,files in os.walk(S,followlinks=False):
 for n in dirs+files:
  assert not (pathlib.Path(d)/n).lstat().st_file_attributes&0x400
 for n in files:names.append((pathlib.Path(d)/n).relative_to(S).as_posix())
assert sorted(names)==sorted(x['path'] for x in cal['created'])
for x in cal['created']:
 st=(S/x['path']).lstat();assert st.st_size==x['bytes'] and st.st_mtime_ns==x['mtime_ns']
verify_safety(json.loads((R/'pre-live-after.json').read_text(encoding='utf-8-sig')))
sys.path.insert(0,str(C));import cleanup_checker
check=cleanup_checker.evaluate(F)
with (R/'failed-run-cleanup-check.json').open('x') as f:json.dump(check,f,indent=2)
def read(n):return json.loads((F/n).read_text(encoding='utf-8-sig'))
probes=read('probe-timings.json');bad=[x for x in probes if x.get('hardDeadlineFailure')]
app=read('app-result.json');hb=read('app-heartbeats.json');etw=read('etw-result.json');tree=read('tree-handles.json')
timing=[]
for x in bad:
 freq=x['frequency'];kt=x['finalKernelTimes']
 timing.append(dict(pid=x['pid'],created=kt[0],exit=kt[1],lifetimeSeconds=(int(kt[1])-int(kt[0]))/1e7,createProcessSeconds=(x['createProcessReturnedQpc']-x['createProcessCalledQpc'])/freq,deadlineObservedSeconds=(x['failureCaughtQpc']-x['launchRequestedQpc'])/freq,observerWaitSeconds=(x['observerReturnedQpc']-x['observerWaitEnteredQpc'])/freq,immediateHandleState=x['immediateHandleState'],observerResult=x['observerResult'],exitCode=x['actualExitCode']))
summary=dict(status='PROTECTED_COLLECTOR_STILL_DEFECTIVE',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),run=str(F),candidateHashes=count,priorArchiveMembers=1333,calibration='UNCHANGED',syntheticMetadata='UNCHANGED',syntheticFiles=len(names),syntheticBytes=cal['totalBytes'],probeCount=len(probes),failedProbes=timing,healthyRecordedHeartbeatMax=max(x['interval'] for x in hb),heartbeatErrorGapSeconds=(app['error']['qpc']-hb[-1]['qpc'])/1e7,heartbeatGapCaveat='Error receipt minus last heartbeat; not an instrumented duration of any individual blocking call.',queue=app['queue'],appSuccess=app['success'],durableFinalization=app['durableFinalization'],kernel={k:v for k,v in etw.items() if k not in ('rows',)},treeRows=len(tree['rows']),treeClosed=sum(bool(x['closed']) for x in tree['rows']),treeSignaled=sum(bool(x['signalObservedQpc']) for x in tree['rows']),cleanupChecker={k:v for k,v in check.items() if k not in ('identities','outsideKernel','outsideAppEvents')},liveProcesses=0,traceSessions=0,protectedAccess=False,productionChanged=False,historicalCause='UNCONFIRMED',retry=False)
with (R/'failure-summary.json').open('x') as f:json.dump(summary,f,indent=2)
# Exact identities for a read-only live PID + creation-time comparison.
ids=[dict(pid=x['pid'],created=x['created']) for x in etw['rows']]
ids+=list(read('observer-identities.json').values())
launcher=read('launcher.json');ids.append(dict(pid=launcher['pid'],created=launcher['creationFiletime']))
with (R/'known-identities.json').open('x') as f:json.dump(ids,f,indent=2)
print(json.dumps(summary))
