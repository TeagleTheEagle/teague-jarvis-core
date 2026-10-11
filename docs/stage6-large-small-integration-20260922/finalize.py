import pathlib,json,hashlib,zipfile,datetime
R=pathlib.Path(__file__).parent
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda p,v:p.write_text(json.dumps(v,indent=2),encoding='utf8')
candidate=load(R/'candidate.json');C=pathlib.Path(candidate['code']);run=load(R/'normal-run.json');root=pathlib.Path(run['root'])
frozen=load(C/'small-source.json');bad=[x['name'] for x in frozen if sha(C/x['name'])!=x['sha256']]
old=load(R.parent/'stage6-health-journal-candidate-20260922/candidate-frozen.json')['files']
oldbad=[x['path'] for x in old if sha(pathlib.Path(x['path']))!=x['sha256']]
assert not bad and not oldbad
oldbase=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\e55504d627d24f24a6f56f9e2435230b\code')
before={str(pathlib.Path(x['path']).relative_to(oldbase)):x for x in old}
changes=[dict(name=x['name'],before=before.get(x['name'],{}).get('sha256'),after=x['sha256']) for x in frozen if before.get(x['name'],{}).get('sha256')!=x['sha256']]
save(R/'final-hashes.json',dict(candidateFiles=len(frozen),candidateMismatches=bad,priorFiles=len(old),priorMismatches=oldbad,changes=changes))
launch=load(root/'launcher-result.json');kernel=load(root/'etw-result.json');detail=load(root/'detail/etw-result.json');app=load(root/'app-result.json');hb=load(root/'app-heartbeats.json')
one=load(root/'hash-pass-1.json');two=load(root/'hash-pass-2.json');metadata=load(root/'metadata-verified.json');tree=load(root/'tree-handles.json');sampler=load(root/'sampler-results.json')
data={p.name:dict(bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns,sha256=sha(p)) for p in (C/'small-synthetic').iterdir()}
assert one['files']==two['files']
assert all(data[n]['bytes']==v['bytes'] and data[n]['mtime_ns']==v['mtime_ns'] and data[n]['sha256']==v['sha256'] for n,v in one['files'].items())
metrics=dict(status='SMALL_INTEGRATION_FAILED',case='normal',attempts=1,retries=0,files=12,bytes=786432,hashesMatch=True,metadataPreserved=True,kernelEventsLost=kernel['eventsLost'],detailEventsLost=detail['eventsLost'],kernelRows=len(kernel['rows']),detailRows=len(detail['rows']),kernelPersistedRecords=load(root/'kernel-authority-result.json')['written'],detailPersistedRecords=load(root/'detail/startup-events.json')['persisted'],maxHeartbeat=max(x['interval'] for x in hb),samplerQueries=len(sampler['queries']),samplerThreadExited=sampler['threadExited'],treeAllExited=tree['allExited'],treeAllHandlesClosed=tree['allHandlesClosed'],treeThreadStopped=tree['threadStopped'],launcher=launch,queue=app['queue'],controlledFailure='NOT RUN',largeEligibility=False,rootCause='UNCONFIRMED')
save(R/'metrics.json',metrics)
save(R/'execution-notes.json',dict(focused=dict(command=[r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe','-B',str(C/'test_small_binding.py')],exit=0,tests=10,subtestMutationFields=15),live=dict(command=['run.ps1','-Case','normal'],exit=0,meaning='collection closed pending checker; not acceptance'),checker=dict(command=['python','-B',str(C/'small_check.py'),root.name],exit=1,error='ValueError: OBSERVER_CLEANUP'),cleanupCensusPreparationError='Malformed 1467a499e7ed49d493a53d079a374995f RunId rejected by ValidatePattern before querying; fresh valid ID subsequently used. No workload retry.'))
changes_text='\n'.join('- '+x['name'] for x in changes if not x['name'].startswith('small-synthetic'))
report=f'''# Stage 6 bounded large integration: small sacrificial attempt

**SMALL_INTEGRATION_FAILED — ETW event loss in both trace channels. Stage 6 INCOMPLETE.**

Fresh candidate: `{C}`
Fresh normal run: `{root}`

## Implemented TEST integration

Separate versioned small declaration/checker, unchanged native binaries and writer implementations. The health adapter consumes the validated append-only journal and retains creation-verified live handles for authority, detailed and application observers. The existing native RunCollector entry invokes the existing traced collector. A copied traced_collect.py performs PREPARED -> OBSERVERS_READY inside the traced collector, avoiding an untraced Python control child after observers start. Direct collector/hash worker/sampler/probe classes require creator-owned early image/native evidence; the new explicit DETAIL_OBSERVER class uses the existing tracer-handle requirements. Unknown classes still reject.

The two unchanged native tracers run separately with distinct output directories, shared exact launcher identity, and independent loss/error checks. Elevated processes accept their existing fixed monitoring arguments only. Three individually identified UAC prompts were approved; normal orchestration stayed non-elevated. Cleanup order is collector/helpers -> application observer -> detailed tracer -> authoritative tracer. No process was force-terminated by this campaign.

Changed/new candidate integration/configuration files (exact before/after hashes in final-hashes.json):
{changes_text}

Twelve newly generated 64 KiB synthetic files are the only dataset. Explicit synthetic-only allowlist, protected access false, no external data path. Existing 59.7 GB dataset not accessed. Frozen medium candidate and its declarations/checker remain unchanged. The copied medium entry points are not selected by this candidate.

## Validation actually executed

- New focused suite: 10/10 unittest tests, including 15 declaration mutations and three observer-exit subcases. No fabricated extra test count.
- Existing monitor regressions: 69/69 PASS, zero errors/failures/skips.
- Queue regression: 222 assertions PASS, including 10,000-event collision stress (zero internal collisions/loss/duplicate/sibling deletion).
- Existing finalization regression: **137 assertions PASS in this execution**. Historical counts are not substituted.
- Syntax: six Python files and one PowerShell launcher PASS.
- One actual small normal integration attempt; collector exit 0, application observer exit 0, authority and detailed tracers both exit 95.
- Both SHA-256 passes agree for 12 files / 786,432 bytes; metadata and current source content agree. Hash worker reported 0.313 seconds total, including its setup/metadata work.
- Maximum heartbeat interval: {metrics['maxHeartbeat']} seconds, below unchanged 10-second boundary.
- Application queue: {app['queue']['enqueued']} enqueued/persisted/removed, zero remaining; durable application finalization reported success.
- Authoritative tracer: {kernel['eventsLost']} eventsLost; {len(kernel['rows'])} recorded instances / {metrics['kernelPersistedRecords']} persisted lifecycle records. These counts DO NOT prove complete lifecycle coverage in a lossy run.
- Detailed tracer: {detail['eventsLost']} eventsLost; {metrics['detailPersistedRecords']} accepted/persisted detail records. Persisting admitted records does not repair upstream ETW loss.
- Both tracers requested stop, flushed/stopped/consumed with API result 0 and internal fault counter 0; their nonzero loss counters correctly produced exit 95.
- Strict checker failed at OBSERVER_CLEANUP. Subsequent coverage/manifest acceptance predicates were NOT represented as passed. Controlled startup-failure run, real-evidence checker mutation suite, integrated sustained capacity test and large run NOT RUN after this failure.

## Failure meaning and narrow next investigation

Established: the simultaneous two-tracer configuration lost ETW events despite healthy application heartbeat and successful small hashing. Loss is independently reported by each tracer. This is a TEST acceptance failure, not evidence of a production JARVIS defect.

Not established: why loss occurred, the precise interval, whether causes were shared, whether initialization/flush bursts, provider volume, callback work, storage, scheduling or contention contributed. No cause is assigned by speculation. Unchanged medium success does not establish capacity for this combined configuration. Historical delay causes remain UNCONFIRMED.

Minimum next step is a bounded TEST trace-loss diagnosis: record per-session loss/buffer statistics at capture stages and correlate callback/consumer/drain progress with existing detailed timing. Preserve the failed run; do not re-run acceptance or increase queues, ETW buffers, deadlines or heartbeat limits simply to pass. Writer/sink redesign was explicitly outside this integration approval and remains a review boundary if needed. Current authority duration remains 180 seconds; large duration/capacity is not qualified.

## Cleanup, preservation and rollback

Collector tree proof: all exited={tree['allExited']}, all handles closed={tree['allHandlesClosed']}, tracker stopped={tree['threadStopped']}. Native bridge: four threads exited, no errors. Sampler: one query, bounded cleanup and supervisor exit recorded. Fresh independent host census at 2026-09-22T08:09:08.1509364Z found zero matching processes and zero diagnostic trace sessions. A mistyped census run-ID was rejected before the query; the successful fresh census is separately preserved. This was not a workload retry.

{len(frozen)} frozen candidate files and 162 prior medium files rehashed without drift. No native binary changes; no Core/runtime/production changes; no protected VM/configuration access; no VirtualBox launch. No acceptance commit. No changes to the 10/13.6/15-second safety limits.

Rollback: deselect this new TEST candidate; keep its source and all failed evidence. No production restore or deletion required. All evidence remains local pending the separately written archive verification receipt; archival is successful only when that receipt reports PASS.

Historical 21 AMBIGUOUS / 1 UNMATCHED unchanged. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
'''
with (R/'REPORT.md').open('x',encoding='utf8') as f:f.write(report)
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 SMALL LARGE INTEGRATION FAILURE 20260922 ac2f7b10');A.mkdir(exist_ok=False)
files=[]
for prefix,base in [('review',R),('candidate',C)]:
 for p in sorted(base.rglob('*')):
  if p.is_file():
   assert not p.is_symlink() and not (p.stat().st_file_attributes&0x400)
   assert p.name not in ('.env',)
   files.append((p,prefix+'/'+p.relative_to(base).as_posix()))
manifest={n:dict(bytes=p.stat().st_size,sha256=sha(p)) for p,n in files}
mp=A/'manifest.json';save(mp,manifest)
zp=A/'evidence.zip'
with zipfile.ZipFile(zp,'x',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
 for p,n in files:z.write(p,n)
with zipfile.ZipFile(zp) as z:
 assert set(z.namelist())==set(manifest)
 for n,v in manifest.items():
  b=z.read(n);assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256']
receipt=dict(status='PASS',membersVerified=len(manifest),archive=str(zp),archiveBytes=zp.stat().st_size,archiveSHA256=sha(zp),manifestSHA256=sha(mp),reportSHA256=sha(R/'REPORT.md'))
save(A/'archive-verification.json',receipt);save(R/'archive-verification.json',receipt)
print(json.dumps(receipt))
