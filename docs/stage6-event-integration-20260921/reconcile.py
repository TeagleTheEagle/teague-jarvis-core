import pathlib,json,hashlib,shutil
from evidence_io import create_json,create_bytes
R=pathlib.Path(__file__).parent;load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));plan=load(R/'plan.json');C=pathlib.Path(load(R/'active-workspace.json')['code'])
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
for x in plan['frozenChecks']:assert sha(pathlib.Path(x['path']))==x['sha256'],x['path']
for x in plan['archives']:assert sha(pathlib.Path(x['path']))==x['sha256'],x['path']
old=R.parent/'stage6-instance-stream-design-20260921';assert sha(old/'final-host-state.json')=='c01b96eecf05c4b29723b900d0543d104fe0f514487886339f080d3d709b17cb'
before={x['name']:x['sha256'] for x in plan['copied']};now=[dict(name=p.name,sha256=sha(p),bytes=p.stat().st_size) for p in sorted(C.iterdir()) if p.is_file()]
changed=[dict(x,before=before[x['name']]) for x in now if x['name'] in before and before[x['name']]!=x['sha256']];added=[x for x in now if x['name'] not in before]
assert set(x['name'] for x in changed)=={'EventTap.cs','event_queue.cs','timed_monitor.ps1','cleanup_checker.py','baseline_finalize.py'}
state=load(R/'final'/load(R/'final-host-plan.json')['runId']/'final-host-state.json');assert state['status']=='PASS' and state['matchingProcessCount']==state['diagnosticTraceCount']==0
prefix=[]
for name in ('high-rate','large-record'):
 v=load(R/(name+'-result.json'));root=pathlib.Path(v['run']);m=v['manifest'];expected=1;total=0;count=0
 for part in m['segments']:
  p=root/part['name'];assert sha(p)==part['sha256'] and p.stat().st_size==part['bytes'];n=0
  with p.open('rb') as f:
   for line in f:
    r=json.loads(line);assert r['seq']==expected;expected+=1;n+=1
  assert n==part['records'];count+=n;total+=part['bytes']
 assert count==m['accepted']==m['persisted'] and m['attempted']==count+1 and m['remaining']==0 and total==m['bytes']
 g=load(root/'generated-load.json');prefix.append(dict(case=name,acceptance='FAIL_PRESERVED',attempted=m['attempted'],accepted=count,persisted=count,rejectedAdmissions=1,segments=len(m['segments']),bytes=total,queueHighWaterItems=m['peakQueueItems'],queueHighWaterBytes=m['peakQueueBytes'],producerRecordsPerSecond=g['recordsPerSecond'],endToEndPersistedRecordsPerSecond=count/g['totalSeconds'],endToEndBytesPerSecond=total/g['totalSeconds'],maximumRolloverSeconds=m['maxRolloverSeconds'],maximumWriteSeconds=m['maxWriteSeconds'],prefixHashesVerified=True,queueEmpty=True))
create_json(R/'failed-prefix-verification.json',prefix)
create_json(R/'candidate-hashes.json',dict(candidate=str(C),changed=changed,added=added,allFiles=now,notPromoted=True,launcherFrozenHashGateNotRegenerated=True))
create_bytes(C/'DO-NOT-LAUNCH-INCOMPLETE.txt',b'Unaccepted integration candidate. Capacity failed; independent CIM instance proof unresolved. Original launcher/source-hash gate intentionally not regenerated. No medium/large run authorized by a passing result. Read current evidence report before any future use.\n')
create_json(R/'final-preservation.json',dict(frozenCandidateChecks=116,additionalChecks=6,archivesUnchanged=len(plan['archives']),historical22='21 AMBIGUOUS;1 UNMATCHED',restoredHostHashUnchanged=True,changedNewCandidateFiles=[x['name'] for x in changed],addedFiles=len(added)+1,finalHost=state,Dfree=shutil.disk_usage(C).free,protectedAccess=False,productionChanged=False,largeDatasetAccess=False,mediumRun=False,thresholdChanges=False))
print(json.dumps(dict(frozenHashes=116,changedNewCandidate=[x['name'] for x in changed],cleanup='PASS',failedCases=prefix,Dfree=shutil.disk_usage(C).free)))
