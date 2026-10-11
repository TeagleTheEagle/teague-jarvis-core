"""Post-run read-only evidence reconciliation; no checker/finalizer or retry."""
from pathlib import Path
import json,sys
R=Path(__file__).parent
T=Path(r'D:\JARVIS-STAGE6-LIVE\cab9745de28a4cae8aa6f6f7a516bf54\code-r2')
RUN=Path(r'D:\JARVIS-STAGE6-LIVE\7f204e14c90a497a8476be0e9927e074\code\protected-f117995dd9ef4ed1b33c1b44b1973293')
sys.path.insert(0,str(T));import failure_preserve_v1 as f
host=f.host_census(R);f.write_new(R/'post-run-host-census.json',host)
if not f.census_clean(host,R):raise SystemExit('BLOCKED: FINAL CENSUS')
def load(name):
 p=RUN/name
 return json.loads(p.read_text(encoding='utf-8-sig')) if p.exists() else None
objects={n:load(n) for n in ('etw-result.json','detail/etw-result.json','observer-identities.json',
                           'launcher-identity.json','tree-handles.json','tree-image-support.json')}
instances=f.instance_census(objects);f.write_new(R/'post-run-instance-census.json',instances)
if not instances['clean']:raise SystemExit('BLOCKED: INSTANCE CENSUS')
keys=('success','status','faults','eventsLost','realtimeBuffersLost','buffersLost',
      'flushResult','stopResult','consumerResult','requestedStop','error','session',
      'queue','durableFinalization','heartbeat','timing','counts','applicationEvents')
summaries={n:{k:v for k,v in (load(n) or {}).items() if k in keys} for n in
           ('etw-result.json','detail/etw-result.json','app-result.json','stress-result.json','loss-telemetry.json')}
first=load('hash-pass-1.json');second=load('hash-pass-2.json');origin=load('cleanup-origin-v3.json')
events=load('integration-launcher.json')
timings=[dict(event=x['event'],secondsAfterCleanupEntry=(x['qpc']-origin['cleanupEntryQpc'])/origin['frequency']) for x in events]
result=dict(run=RUN.name,firstSpecificFailure=load('terminal-failure-v3.json'),
   launcherFailure=load('launcher-failure.json'),launcherResult=load('launcher-result.json'),
   hashFiles=len(first['files']),hashPassesEqual=first['files']==second['files'],metadata=load('metadata-verified.json'),
   origin=origin,timeline=timings,summaries=summaries,
   filesPresent={n:(RUN/n).exists() for n in ('phase-a-v3.json','terminal-v3.json','workload-census-v3.json',
                 'observer-tail-v3.json','external-exits-v3.json','final-census-v3.json','v3-check-result.json','v3-seal.json','v3-archive-receipt.json')},
   knownInstances=instances['knownInstanceCount'],hostProcesses=0,traceSessions=0,
   eventualCleanupOnly=True,runRemainsRejected=True)
f.write_new(R/'result-summary.json',result)
inventory=[]
for p in sorted(RUN.rglob('*')):
 if p.is_dir():continue
 f.safe_path(p,RUN)
 if p.stat().st_nlink!=1:raise ValueError('HARDLINK')
 inventory.append(dict(path=p.relative_to(RUN).as_posix(),**f.metadata(p),sha256=f.sha(p)))
f.write_new(R/'failed-run-inventory.json',dict(run=RUN.name,files=inventory,readOnly=True))
print(json.dumps(result))
