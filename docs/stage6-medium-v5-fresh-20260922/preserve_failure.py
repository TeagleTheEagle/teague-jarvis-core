import collections, hashlib, json, os, statistics, zipfile
from pathlib import Path

R=Path(__file__).resolve().parent
A=Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 MEDIUM V5 FRESH FAILURE 20260922')
def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf8') as f:
        json.dump(v,f,indent=2,sort_keys=True); f.write('\n');f.flush();os.fsync(f.fileno())
pre=load(R/'preflight.json');C=Path(pre['code']);root=Path(pre['root'])
frozen=load(R/'candidate-frozen.json')['files']
for x in frozen:assert sha(x['path'])==x['sha256'],x['path']
for x in pre['copies']:assert sha(x['source'])==x['sha256'],x['source']
old=R.parent/'stage6-medium-v5-20260922'
receipt=load(old/'archive-verification.json');archive=Path(receipt['archive']);manifest=archive.parent/'manifest.json'
assert sha(archive)==receipt['archiveSHA256'] and sha(manifest)==receipt['manifestSHA256']
with zipfile.ZipFile(archive) as z:
    assert len(z.namelist())==receipt['membersVerified']==len(set(z.namelist()))
    assert z.read('manifest.json')==manifest.read_bytes()
    for x in load(manifest)['files']:
        b=z.read(x['name']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
host=load(R/'final/f2684f56d4d241439c2453ddac80fa27/final-host-state.json')
assert host['status']=='PASS' and host['matchingProcessCount']==host['diagnosticTraceCount']==0
launch=load(root/'launcher-result.json');failure=load(root/'identity-worker-failure.json');closure=load(root/'identity-handle-closure.json')
assert launch['kernelExit']==launch['applicationExit']==0 and launch['workerExit']==1
assert launch['kernelExited'] and launch['applicationExited'] and launch['workerExited']
assert failure['failure']=="JSONDecodeError('Expecting value: line 1 column 1 (char 0)')"
assert len(failure['rows'])==len(closure['rows'])==4 and closure['allExited']
assert not (root/'identity-probes.json').exists()
bad=failure['rows'][-1];trace=load(root/'stage-timing.json');freq=trace['frequency']
overlap=[s for s in trace['spans'] if s['stage']=='output.app-health.json' and s['start']<=bad['failureCaughtQpc']<=s['end']]
assert len(overlap)==1
app=load(root/'app-result.json');kernel=load(root/'etw-result.json');writer=load(root/'kernel-authority-result.json');m=load(root/'kernel-authority-manifest.json');heartbeats=load(root/'app-heartbeats.json');health=load(root/'live-health-checks.json')
assert app['success'] and app['queue']['remaining']==0
kernel_rows=kernel['rows'];instances=[(r['pid'],r['created']) for r in kernel_rows]
assert len(instances)==len(set(instances))
for p,c in zip(failure['rows'],closure['rows']):
    assert p['pid']==c['pid'] and p['initialKernelTimes'][0]==c['times'][0] and c['exited']
    matches=[r for r in kernel_rows if (r['pid'],r['created'])==(p['pid'],c['times'][0])]
    assert len(matches)==1 and matches[0]['exitFiletime']==c['times'][1]
kernel_summary=dict(observedInstances=len(kernel_rows),starts=sum(bool(r['startQpc']) for r in kernel_rows),stops=sum(bool(r['stopQpc']) for r in kernel_rows),allObservedStopped=all(r['stopQpc'] and int(r['exitFiletime'])>0 for r in kernel_rows),handlesMarkedClosed=all(r['handleClosed'] for r in kernel_rows),eventsLost=kernel['eventsLost'],realtimeBuffersLost=kernel['realtimeBuffersLost'],buffersLost=kernel['buffersLost'],faults=kernel['faults'],processes=[dict(pid=r['pid'],created=r['created'],parentPid=r['parentPid'],sequence=r['sequence'],parentSequence=r['parentSequence'],image=r['image'],startQpc=r['startQpc'],stopQpc=r['stopQpc'],exitFiletime=r['exitFiletime'],exitCode=r['exitCode'],handleRetained=r['handleRetained'],handleClosed=r['handleClosed']) for r in kernel_rows])
assert kernel_summary['allObservedStopped'] and kernel_summary['handlesMarkedClosed']
lifetimes=[(int(c['times'][1])-int(c['times'][0]))/1e7 for c in closure['rows']]
diagnosis=dict(status='STRONG_CAUSAL_EVIDENCE',failure=failure['failure'],pid=bad['pid'],created=bad['initialKernelTimes'][0],qpcFrequency=freq,failureCaughtQpc=bad['failureCaughtQpc'],healthWriteSpan=overlap[0],failureSecondsAfterWriteSpanStart=(bad['failureCaughtQpc']-overlap[0]['start'])/freq,
    sourceReader=dict(path=str(C/'qualified_worker.py'),line=18,behavior='Read app-health.json and immediately parse JSON during health callback'),
    sourceWriter=dict(path=str(C/'timed_monitor.ps1'),line=5,behavior='FileMode.Create truncates existing app-health.json, FileShare.Read permits concurrent readers; serialize/write/flush then close'),
    exactReadBytes='UNKNOWN: not retained',exactTruncationSyscallTime='UNKNOWN: available timing wraps the complete Save operation',
    tracebackLimit='Worker preserves exception repr, not original health callback traceback; static wait path contains one JSON parse, in health callback.',
    maxHeartbeatSeconds=max(x['interval'] for x in heartbeats),maxSuccessfulHealthAgeSeconds=max(x['age'] for x in health),probeLifetimesSeconds=lifetimes,maxProbeSeconds=max(lifetimes),hardDeadlineViolations=sum(bool(p.get('hardDeadlineFailure')) for p in failure['rows']),
    completedProbeRows=3,startedProbes=4,declaredProbes=64,fullWorkloadComplete=False,
    kernel=kernel_summary,applicationQueue=app['queue'],applicationFinalization=app['durableFinalization'],
    correctionProposed='Publish complete immutable health records using an existing proven D: publication protocol; review narrow reader/writer integration. Preserve creation-bound publisher checks, explicit unhealthy state, malformed-record rejection and strict 10-second health limit. No JSON-error swallowing, last-good-unbounded reuse or retries.',
    mandatoryReview='Confirm publication choice under Windows sharing semantics and bound active artifact growth; test concurrent read/write and interrupted publication before any new medium run.',
    productionChanged=False,protectedAccess=False)
save(R/'diagnosis.json',diagnosis)
source_inventory=[]
for p in sorted(root.rglob('*')):
    assert not p.is_symlink() and not p.is_junction()
    if p.is_file():source_inventory.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p),mtimeNs=p.stat().st_mtime_ns))
save(R/'run-preservation.json',dict(files=source_inventory,candidateHashesVerified=len(frozen),priorSourceHashesVerified=len(pre['copies']),previousBlockedArchiveMembersVerified=receipt['membersVerified'],previousBlockedArchiveSHA256=receipt['archiveSHA256']))
disposition=dict(status='MEDIUM_VALIDATION_FAILED',stage6='INCOMPLETE',accepted=False,runId=root.name,attempts=1,retries=0,
    failedPhase='Fourth idle probe health callback',reason=failure['failure'],liveCheckerAcceptance='NOT RUN: incomplete workload',
    diagnosticClassification='STRONG_CAUSAL_EVIDENCE: concurrent health-file overwrite/read',liveDiagnosticProcesses=0,diagnosticTraceSessions=0,
    candidateHashesVerified=len(frozen),productionChanged=False,protectedAccess=False,largeRun=False,
    nextAction='Review a separate narrow TEST health-publication correction with concurrent-reader and interrupted-write regressions; preserve this frozen failed run.')
save(R/'final-disposition.json',disposition)
report=f'''# Stage 6 fresh medium attempt — preserved health-read failure

**MEDIUM_VALIDATION_FAILED. Stage 6 remains INCOMPLETE.**

Run `{root.name}` used the corrected `stage6-checker-telemetry-v5` candidate and one fresh identity. Both owner UAC steps succeeded. One attempt, no retry. The previous stopped attempt remains BLOCKED and its 190-member archive was independently reverified.

## Failure and supported cause

The fourth idle probe (PID {bad['pid']}, creation identity `{bad['initialKernelTimes'][0]}`) raised `{failure['failure']}` in its wait/health path. Three completed probe rows and a fourth failure row were preserved. Only 4 of 64 declared probes started; the churn and overlap phases did not run. The worker exited 1. Both observers exited 0 through normal cleanup.

The worker health callback reads and immediately parses `app-health.json` (`qualified_worker.py:18`). The observer uses `FileMode.Create` with `FileShare.Read`, truncates that same file, then serializes, writes and flushes it (`timed_monitor.ps1:5`, called at line 39). The health callback is the only JSON parse in the static wait path; the publisher handle check itself does not parse JSON.

The failure-caught QPC `{bad['failureCaughtQpc']}` lies inside `output.app-health.json` span `{overlap[0]['start']}` to `{overlap[0]['end']}` at {freq} ticks/second. It was caught {(bad['failureCaughtQpc']-overlap[0]['start'])/freq:.7f} seconds after that span began; the full span lasted {overlap[0]['seconds']:.7f} seconds. This is strong causal evidence of a reader observing an incomplete health publication. Exact read bytes and the truncate syscall timestamp were not preserved; do not claim they were observed. The original callback stack was reduced to exception repr by the worker.

This is a TEST monitor-health transport finding. It does not establish a production JARVIS defect, a v5 compatibility-checker regression, or a historical Windows/storage cause. The strict checker was not evaluated against the incomplete workload; no missing workload or identity evidence was manufactured.

## Observations, not acceptance substitution

| Item | Observed result |
|---|---|
| Fresh preparation | 11/11 checks; 160 hashes; previous 1,766 archive members verified |
| Started / fully recorded probes | 4 / 3 of 64 required |
| Four probe retained-handle closures | All signaled/exited; creation times and kernel exit times agree |
| Probe lifetimes | {lifetimes} seconds |
| Recorded hard deadline violations | 0 |
| Maximum heartbeat interval | {diagnosis['maxHeartbeatSeconds']:.7f} seconds, below unchanged 10-second limit |
| Maximum successful health-read age | {diagnosis['maxSuccessfulHealthAgeSeconds']:.7f} seconds; failed read has no valid age |
| Slow heartbeat warnings | NOT CONFIGURED, per approved policy |
| Observed kernel lifecycle rows | {kernel_summary['observedInstances']} instances, {kernel_summary['starts']} starts / {kernel_summary['stops']} stops |
| Kernel loss counters / faults | {kernel_summary['eventsLost']} / {kernel_summary['realtimeBuffersLost']} / {kernel_summary['buffersLost']} / {kernel_summary['faults']} |
| Application queue | {app['queue']['enqueued']} enqueued / {app['queue']['persisted']} persisted / {app['queue']['removed']} removed; remaining {app['queue']['remaining']} |
| Application finalization | {app['durableFinalization']} |
| Final host census | Zero matching processes and zero trace sessions at {host['utc']} |
| Frozen candidate / prior candidate | {len(frozen)} / {len(pre['copies'])} hashes unchanged |
| Full lifecycle qualification / checker | NOT RUN; declared medium workload incomplete |
| Protected VM / configuration access | NONE |
| Production change | NONE |

All observed kernel rows have stop/exit evidence and tracer handles marked closed. This is cleanup evidence for the partial run, not a full non-vacuous medium qualification. Qualified-helper rules and CIM ambiguity classification were not bypassed or guessed. Independent artifacts are preserved for later inspection.

## Minimum proposed correction — not implemented

Review only the TEST health-file publication boundary between `timed_monitor.ps1` and `qualified_worker.py`. Prefer complete immutable records using the already-proven D: publication mechanism, with a bounded reader that cannot observe an in-progress record as a completed health snapshot. Retain creation-bound publisher verification, explicit unhealthy-state rejection, strict malformed-record handling and the unchanged 10-second freshness limit. Do not swallow JSON errors or add arbitrary retries/timeouts. Confirm Windows sharing behavior and bounded file growth in the design.

Focused validation should deterministically hold a writer between opening and completing publication while reading concurrently; exercise truncation/partial payload, interrupted publication, malformed completed payload, wrong publisher identity, stale/future health and publisher exit. Then run the affected monitor/heartbeat/queue/finalization regressions before seeking a new fresh medium attempt. The frozen run and its candidate must remain unchanged.

## Preservation and scope

No candidate source changes after freeze. Only the three recorded fresh-run path/identity bindings changed during preparation. No deadline, heartbeat, authority, security, queue or publication rule was altered. No runtime correction or acceptance commit. No large dataset, protected baseline hashing, VirtualBox operation or production access.

Historical 21 AMBIGUOUS / 1 UNMATCHED remain unchanged. Historical probe/sampler/storage delay causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Rollback: leave this stopped candidate unselected and preserve it and its evidence. No production rollback, VM change, termination or deletion is needed. Canonical archive: `{A/'evidence.zip'}`. The hash-verification receipt confirms preservation only; it cannot turn this failed attempt into a pass.
'''
with (R/'REPORT.md').open('x',encoding='utf8') as f:f.write(report);f.flush();os.fsync(f.fileno())
rows=[]
for label,base in [('review',R),('candidate-and-run',C)]:
    for p in sorted(base.rglob('*')):
        assert not p.is_symlink() and not p.is_junction(),p
        if p.is_file():
            assert p.name!='.env' and '__pycache__' not in p.parts,p
            rows.append(dict(name=label+'/'+p.relative_to(base).as_posix(),source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
assert not A.exists();A.mkdir()
save(A/'manifest.json',dict(status=disposition['status'],accepted=False,runId=root.name,files=rows))
with (A/'evidence.zip').open('xb') as out:
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for x in rows:z.write(x['source'],x['name'])
        z.write(A/'manifest.json','manifest.json')
    out.flush();os.fsync(out.fileno())
with zipfile.ZipFile(A/'evidence.zip') as z:
    assert len(z.namelist())==len(set(z.namelist()))==len(rows)+1
    assert z.read('manifest.json')==(A/'manifest.json').read_bytes()
    for x in rows:
        b=z.read(x['name']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']==sha(x['source'])
for x in frozen:assert sha(x['path'])==x['sha256']
receipt=dict(status='PASS',membersVerified=len(rows)+1,archive=str(A/'evidence.zip'),archiveBytes=(A/'evidence.zip').stat().st_size,archiveSHA256=sha(A/'evidence.zip'),manifestSHA256=sha(A/'manifest.json'),reportSHA256=sha(R/'REPORT.md'))
save(R/'archive-verification.json',receipt);save(A/'archive-verification.json',receipt);save(A/'final-disposition.json',disposition)
assert sha(R/'archive-verification.json')==sha(A/'archive-verification.json')
assert sha(R/'final-disposition.json')==sha(A/'final-disposition.json')
print(json.dumps(dict(disposition=disposition,archive=receipt,heartbeat=diagnosis['maxHeartbeatSeconds'],lifetimes=lifetimes,kernelIdentities=kernel_summary['observedInstances'],overlap=overlap)))
