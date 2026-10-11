import pathlib,json,hashlib,zipfile,statistics,os
R=pathlib.Path(__file__).parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frozen=read(R/'freeze.json');s=read(R/'preserved-summary.json');timeline=read(R/'timeline.json')
F=pathlib.Path(frozen['rawFiles'][0]['path']).parent;C=F.parent;N=C/'narrow-1e4b8986e27742f7b47df58b26969ec1';n=read(N/'result.json');host=read(R/'host-final.json')
assert n['status']=='NO_ORIGINAL_FAILURE_REPRODUCED' and n['sourceMetadataPreserved'] and not n['sourceDrift']
assert not host['liveIdentityMatches'] and not host['relevantProcesses'] and not host['traces'] and host['traceExit']==0
for x in frozen['rawFiles']:
 p=pathlib.Path(x['path']);st=p.stat();assert st.st_size==x['bytes'] and st.st_mtime_ns==x['mtime_ns'] and sha(p)==x['sha256']
for x in frozen['sourceManifest']:assert sha(C/x['name'])==x['sha256']
assert sha(C/'run-source.json')==frozen['sourceManifestSHA256']
originalArchive=pathlib.Path(frozen['archive']['path'])
assert sha(originalArchive/'evidence.zip')==frozen['archive']['zipSHA256'] and sha(originalArchive/'archive-manifest.json')==frozen['archive']['manifestSHA256']
distributions={}
for condition in ('idle','synthetic-D-hash'):
 rows=[x for x in n['probes'] if x['condition']==condition];values=sorted((int(x['finalKernelTimes'][1])-int(x['finalKernelTimes'][0]))/1e7 for x in rows)
 distributions[condition]=dict(count=len(rows),minimum=min(values),median=statistics.median(values),maximum=max(values),maxCreate=max((x['createProcessReturnedQpc']-x['createProcessCalledQpc'])/x['frequency'] for x in rows),deadlineFailures=sum(bool(x['hardDeadlineFailure']) for x in rows))
samplers=[]
for x in n['samplers']:samplers.append(dict(case=x['case'],status=x['status'],reason=x.get('reason'),created=x['created'],pid=x['pid'],createSeconds=(x['createReturnedQpc']-x['createBeginQpc'])/1e7,queryAndCleanupSeconds=(x['cleanupEndQpc']-x['launchQpc'])/1e7,cleanupSeconds=(x['cleanupEndQpc']-x['cleanupBeginQpc'])/1e7,allExited=x['allExited'],handleClosed=x['handleClosed'],jobActive=x['jobActiveBeforeClose']))
q=timeline['sampler'];obs=q['jobCleanupObservations'];gap=max((v['qpc']-u['qpc'])/1e7 for u,v in zip(obs,obs[1:]))
summary=dict(status='INCONCLUSIVE',reproductionStatus=n['status'],probeDistributions=distributions,samplers=samplers,load=n['load'],observedRetainedIdentities=len(n['cleanup']['rows']),allRetainedExited=n['cleanup']['allExited'],allRetainedHandlesClosed=n['cleanup']['allHandlesClosed'],treeStopped=n['cleanup']['threadStopped'],originalRawFilesUnchanged=len(frozen['rawFiles']),candidateHashesUnchanged=len(frozen['sourceManifest']),originalArchiveMembersVerified=196,originalArchiveUnchanged=True,cleanupObservationGapSeconds=gap,probeDelayStage='UNKNOWN',samplerDelayStage='CreateProcessW call; later process-signal cleanup predicate not satisfied in bound',commonCause='NOT_ESTABLISHED',newRuntimeCorrection=False,thresholdChange=False,productionChanged=False,protectedAccess=False,baselineEligible=False,limitations=['Narrow load repeatedly hashes the first 64 MiB of one synthetic D: file and is cache-friendly; not equivalent to a 59.7 GB two-pass run','No fresh ETW/CIM observer; retained handles/Toolhelp only, no claim of complete short-lived child event coverage','Historical probe internal entry/work/exit markers and blocking stacks absent','No measured disk queues, filesystem filter latency, security scans or thread scheduling trace'],nextAction='Owner review of narrow startup/thread-wait trace proposal; no acceptance retry')
with (R/'diagnosis-summary.json').open('x') as f:json.dump(summary,f,indent=2)
times='\n'.join(f"| {x['secondsFromProbeLaunch']:.6f} | {x['stage']} | {x['source']} |" for x in timeline['events'])
ds='\n'.join(f"| {key} | {x['count']} | {x['minimum']:.6f} | {x['median']:.6f} | {x['maximum']:.6f} | {x['maxCreate']:.6f} | {x['deadlineFailures']} |" for key,x in distributions.items())
sq='\n'.join(f"| {x['case']} | {x['status']} / {x['reason'] or 'normal response'} | {x['createSeconds']:.6f} | {x['queryAndCleanupSeconds']:.6f} | {x['cleanupSeconds']:.6f} | {x['allExited']} / {x['handleClosed']} / {x['jobActive']} |" for x in samplers)
report=f'''# Stage 6 preserved probe and sampler diagnosis

**Final status: INCONCLUSIVE**

The original probe and sampler failures remain failures. They overlap, but the current evidence establishes neither a common cause nor independent causes. Bounded sacrificial testing did not reproduce either original failure. No correction, deadline increase, full-size campaign, acceptance retry or protected baseline capture was performed.

## 1. PID 23408 timeline

Identity: PID 23408, creation FILETIME 134343831274954036, kernel sequence 32578, parent PID 9808 / sequence 32179. Image `{C / 'J6Probe.exe'}`. SHA-256 `{s['probeImageSHA256']}`, byte-identical to the currently installed `C:\\Windows\\System32\\whoami.exe`.

QPC frequency 10,000,000 Hz. Time zero is the saved probe launch request, QPC {timeline['originQpc']}. The table uses raw same-host monotonic measurements, not reconstructed wall-clock guesses. Event timestamps, callback timestamps and observed signaled-handle timestamps are distinct.

| Seconds from probe launch | Observation | Evidence |
|---:|---|---|
{times}

Probe entry, work begin/end, internal cleanup/return and exact kernel-handle signaling instant are **UNKNOWN**. The retained-handle observation bounds the exit signal; it is not substituted for the exact signaling instant. Kernel creation-to-exit FILETIME duration is 17.1945539s. Launch-to-kernel-exit QPC is slightly different because process creation follows launch.

## 2. Process tree, handles and I/O

Parent: Python collector PID 9808, created 134343830676760972, sequence 32179, launched by PID 24372. Its command is supported by the frozen launcher source: the existing Python executable with `-B`, `large_collect.py`, and this run name. It exits 1 after failure cleanup.

Exactly one kernel-sequence-qualified probe child is recorded: `C:\\Windows\\System32\\conhost.exe`, PID 4792, created 134343831446664454, sequence 32581, parentSequence 32578. It was created 17.1710418 seconds after probe creation, lived 0.0244561 seconds, and exited 0 approximately 0.000944 seconds after the probe. It did not exist at the 13.6-second probe deadline. No earlier child is recorded; kernel loss counters are clear and historical event reconciliation passed. Child command line is **UNKNOWN**, not inferred.

The probe has no arguments, uses cwd `{C}`, CREATE_NO_WINDOW, stdout/stderr DEVNULL and Popen's default close_fds=True. There are no stdout/stderr pipes to fill. The retained TreeTracker and kernel tracer independently bind handles to creation times and report exits/handle closure. A full inherited-handle table, opened-file list and thread-wait stacks were not captured. The child's late appearance does not prove console attachment was the blocking operation.

## 3. Delay-owning probe stage

CreateProcess returned after 0.0053532s. Almost the entire 17.195s process lifetime precedes the recorded console-helper creation. This excludes a long parent CreateProcess call and an already-running recorded child as explanations for this probe's deadline breach. It does **not** distinguish initialization, an internal security lookup, scheduler delay, blocking I/O, or another pre-helper activity. Recorded process CPU accounting is zero ticks; accounting granularity does not prove that no user instructions executed. Classification: **UNKNOWN**.

## 4–5. Sampler timeline and failed boundary

Sampler query ordinal 6, mode `normal`, PID 7712, creation FILETIME 134343831405852703, kernel sequence 32579; it is a sibling of the probe, not its child. The fixed command uses the existing Python executable, `-B`, `sampler_worker.py`, this run name, mode normal, and a per-query Local\\J6Secondary mapping name. No arbitrary caller command is accepted. CreateProcessW uses CREATE_SUSPENDED | CREATE_NO_WINDOW, bInheritHandles=False, followed by bounded Job assignment and ResumeThread. No stdout/stderr capture pipe is created; results use the existing 4096-byte mapping.

CreateProcessW consumed **12.0594708s**. The launch-based two-second query budget was already expired before ResumeThread at +13.099995s. Its normal query would read GlobalMemoryStatusEx/GetSystemTimes and return JSON, but no result or internal worker-entry timestamp exists. The original timeout/cancellation reason was overwritten by REQUIRED_CLEANUP_UNPROVEN. Source sequencing and elapsed time support an exhausted-query-budget interpretation; the report does not invent an absent recorded branch reason.

Cleanup began at +13.134754s and returned at +18.501294s: **5.3665398s**. Existing code uses a two-second predicate loop, then (if still unsignaled) one existing two-second handle wait after closing the Job. These are not a single two-second end-to-end cleanup deadline. The 47 predicate observations span 3.35438s, with one **{gap:.7f}s observation gap**. Individual WaitForSingleObject/QueryInformationJobObject/sleep/TerminateJobObject call entry/exit timings are not present, so the owner of that gap is UNKNOWN.

At the failed boundary, Job active count was zero but the retained process handle remained unsignaled. Both predicates are required. A recorded termination request succeeded; eventual kernel exit code 230 (0xE6, the existing sampler termination code) was observed at +19.203184s, after cleanup had already failed. Thread eventually stopped. Job-empty alone was correctly not accepted as process-exit proof. No evidence justifies relaxing this rule.

## 6. Temporal relationship

Probe lifetime overlaps sampler creation/cleanup for 16.1550308s. The probe starts first; sampler creation begins +1.040279s, returns +13.099750s, then both remain unresolved across the probe deadline. The sampler observation gap overlaps the independent probe wait's late return. A shared external stall is plausible but **UNCONFIRMED**. Different observed blocking stages do not prove independent causes. No causal arrow is established.

## 7–9. Monitor, events and cleanup

Historical heartbeat maximum: **1.0561466s**, below unchanged 10s threshold. Longest instrumented stage: wait.event, 1.0553855s; no timing overflow. Historical 372 STARTs / 372 STOPs reconciled to 372 kernel identities, 343 retained-handle exits plus 29 qualified post-exit cases. All 809 queued events persisted and were removed; zero remaining, four external EventIdentifier collisions, zero internal queue collisions. Observer durable finalization succeeded.

Final historical exit proof is separate from the failed sampler deadline. Fresh final host checks found zero matches among **517 recorded PID/creation identities** (375 historical including launcher/observers, plus 142 newly observed retained identities), zero matching diagnostic/VirtualBox processes and zero diagnostic trace sessions. Fresh TreeTracker reports all acquired handles signaled and closed, no recorded tracker errors, and its thread stopped. Short-lived reproduction helpers were not exhaustively traced with ETW/CIM; complete new child-event coverage is not claimed.

Last successful historical resource sample before the stalls recorded 28% memory load and 24,584,843,264 available physical bytes. It is not a sample during the stall. Disk metrics were explicitly NOT_COLLECTED; no scheduler-stack, Defender/filter latency or image-load wait trace exists. No storage/security root cause is asserted.

## 10. Bounded reproduction results

Command: existing Python executable, `-B`, `{R / 'narrow_reproduction.py'}`. Fresh run: `{N}`. All live artifacts and process-local TEMP/TMP remained on D:. No UAC, ETW/CIM observer, VirtualBox or JARVIS Core was launched.

| Condition | Probes | Min lifetime s | Median s | Max s | Max CreateProcess s | Deadline failures |
|---|---:|---:|---:|---:|---:|---:|
{ds}

Hashing repeatedly read up to the first 64 MiB of the existing synthetic tail.img, with a 35-second maximum worker budget. Actual load duration was {(n['load']['endQpc']-n['load']['beginQpc'])/1e7:.6f}s; {n['load']['totalBytes']:,} logical bytes read across {n['load']['cycles']} cycles. This cache-friendly 64 MiB working set does not simulate the full 59.7 GB storage footprint, and logical read throughput is not physical disk throughput. No full dataset hash pass or protected-size acceptance run was repeated. Original dataset inventory/metadata remained unchanged.

| Sampler case | Result | Create s | Total query + cleanup s | Cleanup s | Exited / handle closed / Job active |
|---|---|---:|---:|---:|---|
{sq}

Delayed mode is the existing intentional five-second sleep with the unchanged two-second query budget; missing telemetry plus proven cleanup is expected. Cancellation used the existing hung fixture and a 0.1s cancellation signal. These injected missing-result cases are not reproductions of REQUIRED_CLEANUP_UNPROVEN. All three retained exits were proved. No original failure reproduced, so no automatic retry or expanded test ladder occurred. Fresh heartbeat/event acceptance was not attempted or claimed.

## 11–13. Decision, minimum correction and uncertainty

**INCONCLUSIVE.** The sampler's prolonged process-creation call and later unsatisfied exit predicate are established observations. The probe's internal delay-owning operation and any shared underlying cause remain unknown. Neither COMMON_CAUSE_STRONG_EVIDENCE nor INDEPENDENT_FAILURES_STRONG_EVIDENCE is supported. No functional correction is presently justified; therefore none was implemented.

Smallest proposed next diagnostic change, for review: add timestamps around the fixed sampler's individual creation/resume/terminate/wait/accounting calls, and capture narrowly bounded startup/thread-wait evidence for the same fixed probe/sampler images under a small sacrificial load. Preserve existing Job ownership, retained identities, fail-closed rules and 13.6/15/10-second limits. Any additional elevated tracing must use the existing per-run approval boundary or receive separate review. Do not switch helpers, loosen cleanup predicates, or extend budgets merely because small tests pass. An entry/exit-instrumented native control can be a comparison only; it must not silently replace the accepted probe.

## 14–18. Preservation, eligibility, archive and final status

- Protected VM/configuration: **NOT ACCESSED**. No real baseline hashes, configuration reads or VirtualBox operations.
- Production JARVIS: **UNCHANGED**. Only new diagnostic/evidence scripts were added under this report directory, with fresh sacrificial evidence on D:.
- Frozen failed run: all **40 raw files** preserve hash, size and modification time; all **100 candidate source hashes** and the source-manifest hash remain unchanged.
- Original **196-member archive** fully hash-verified before testing and unchanged afterward. Its SHA-256 remains `{frozen['archive']['zipSHA256']}`. New archive receipt is separate and does not reclassify the failed run.
- Protected-baseline eligibility: **BLOCKED / UNAUTHORIZED**.
- Final status: **INCONCLUSIVE**.

All historical long-probe and heartbeat-delay causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Rollback: no candidate/runtime changes to undo. Preserve both old and new evidence; leave the failed run unchanged. No deletions, retries, acceptance sealing or protected-baseline steps are authorized by this result.
'''
with (R/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
paths=[('report/'+p.name,p) for p in sorted(R.iterdir()) if p.is_file()]
for label,root in [('preserved-failed-run',F),('bounded-reproduction',N)]:
 for p in sorted(root.rglob('*')):
  assert not p.lstat().st_file_attributes&0x400
  if p.is_file():paths.append((label+'/'+p.relative_to(root).as_posix(),p))
paths.extend(('unchanged-candidate/'+x['name'],C/x['name']) for x in frozen['sourceManifest'])
paths.append(('unchanged-candidate/run-source.json',C/'run-source.json'))
assert len({name for name,p in paths})==len(paths)
rows=[]
for name,p in paths:
 assert p.name!='.env' and not p.lstat().st_file_attributes&0x400
 rows.append(dict(name=name,source=str(p),sha256=sha(p),bytes=p.stat().st_size))
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 PRESERVED PROBE SAMPLER DIAGNOSIS 20260921');A.mkdir(exist_ok=False)
raw=(json.dumps(dict(status='INCONCLUSIVE',kind='DIAGNOSIS_ONLY_NOT_ACCEPTANCE',files=rows),sort_keys=True,indent=2)+'\n').encode()
with (A/'archive-manifest.json').open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
with zipfile.ZipFile(A/'evidence.zip','x',zipfile.ZIP_DEFLATED) as z:
 for x in rows:z.write(x['source'],x['name'])
 z.writestr('archive-manifest.json',raw)
with (A/'evidence.zip').open('r+b',buffering=0) as f:os.fsync(f.fileno())
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==len(rows)+1
 for x in rows:assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256']==sha(pathlib.Path(x['source']))
 assert z.read('archive-manifest.json')==raw
with (A/'REPORT.md').open('xb') as f:f.write((R/'REPORT.md').read_bytes());f.flush();os.fsync(f.fileno())
receipt=dict(status='HASH_VERIFIED',disposition='INCONCLUSIVE',path=str(A),members=len(rows)+1,zipSHA256=sha(A/'evidence.zip'),manifestSHA256=sha(A/'archive-manifest.json'),reportSHA256=sha(A/'REPORT.md'),protectedBaselineAuthorized=False)
for root in (R,A):
 with (root/'archive-verification.json').open('x') as f:json.dump(receipt,f,indent=2);f.flush();os.fsync(f.fileno())
print(json.dumps(receipt))
