import hashlib
import json
import os
from pathlib import Path
import zipfile

R = Path(__file__).resolve().parent
C = Path(r'D:\JARVIS-STAGE6-LIVE\d880e9c8957c44b69fb5f90e0c6ec2f5\code')
run = C / 'identity-a21311ab301145e6a5d5338a0c5c665a'
A = Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 MEDIUM V5 BLOCKED 20260922')

def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.file_digest(Path(p).open('rb'), 'sha256').hexdigest()

def save(p, obj):
    with Path(p).open('x', encoding='utf8') as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write('\n'); f.flush(); os.fsync(f.fileno())

frozen = load(R / 'candidate-frozen.json')['files']
pre = load(R / 'preflight.json')
for x in frozen:
    assert sha(x['path']) == x['sha256'], x['path']
for x in pre['copies']:
    assert sha(x['source']) == x['sha256'], x['source']
hostpath = R / 'final/540672b174b840bf983b1123175306f4/final-host-state.json'
host = load(hostpath)
assert host['status'] == 'PASS' and host['matchingProcessCount'] == host['diagnosticTraceCount'] == 0
result = load(run / 'launcher-result.json')
assert result['error'] == 'Second prompt gate expired'
assert result['kernelExited'] and result['kernelExit'] == 0
assert result['applicationExit'] is None and result['workerExit'] is None
for name in ('allow-app-prompt', 'app-ready.json', 'worker-created.json', 'identity-probes.json'):
    assert not (run / name).exists(), name
file_timeline = []
for p in sorted(run.rglob('*')):
    assert not p.is_symlink() and not p.is_junction()
    if p.is_file():
        file_timeline.append(dict(path=str(p), bytes=p.stat().st_size, mtimeNs=p.stat().st_mtime_ns, sha256=sha(p)))
save(R / 'failed-run-preservation.json', dict(files=file_timeline, candidateHashesVerified=len(frozen), priorSourceHashesVerified=len(pre['copies']), finalHostEvidence=str(hostpath), finalHostSHA256=sha(hostpath)))
disposition = dict(status='BLOCKED', stage6='INCOMPLETE', runId=run.name, attempts=1, retries=0,
    cause='Second prompt gate expired: orchestrator did not release the gate within the existing 120-second bound after kernel readiness.',
    kernelTracerStarted=True, kernelTracerExit=0, applicationObserverStarted=False, workerStarted=False,
    mediumWorkload='NOT RUN', checkerLiveAcceptance='NOT RUN', acceptance=False,
    candidateHashesVerified=len(frozen), liveDiagnosticProcesses=0, diagnosticTraceSessions=0,
    productionChanged=False, protectedFilesAccessed=False, largeRun=False, timeoutChanged=False,
    historicalCauses='UNCONFIRMED', nextAction='Review and authorize a separate fresh medium attempt; do not reuse this run identity.')
save(R / 'final-disposition.json', disposition)
report = f'''# Stage 6 corrected-checker medium attempt

**BLOCKED. Stage 6 remains INCOMPLETE.**

Run: `{run.name}`. One attempt; no retry.

The kernel tracer reached readiness. The orchestration did not release `allow-app-prompt` within the existing 120-second gate. The launcher recorded `Second prompt gate expired`, requested normal tracer closure and exited with error. This is an execution-orchestration failure before the medium workload, not evidence of a checker, collector, or JARVIS runtime defect. It is not classified as owner UAC denial.

The independent application observer and worker were never launched. Their exit codes are null; the launcher's true `applicationExited`/`workerExited` values represent absent processes, not successful executions. No medium probes, hash workload or public acceptance evaluation ran. No acceptance claim is made from the tracer's empty collection or normal shutdown.

## Evidence and cleanup

- Kernel-ready artifact modification time: 2026-09-22T04:13:44.0073646Z.
- Launcher-failure artifact modification time: 2026-09-22T04:15:44.1686699Z.
- Launcher-result artifact modification time: 2026-09-22T04:15:45.8623614Z.
- These are observed file timestamps, not invented internal monotonic timestamps.
- Kernel tracer exited with code 0. No forced termination was used.
- Final independent host census at {host['utc']}: zero matching diagnostic/VirtualBox processes and zero diagnostic trace sessions.
- All {len(frozen)} frozen candidate source hashes and {len(pre['copies'])} prior source hashes match.
- Preflight verified 1,766 members across the two prior archives; 11 preparation checks passed. These do not substitute for the unexecuted medium workload.
- The failed run's files and hashes are preserved in `failed-run-preservation.json` and the canonical archive.

## Scope and preservation

No timeout, deadline, heartbeat, queue, authentication, authority or checker rule changed. Only fresh-run declaration/intent/launcher-path bindings were prepared before the source freeze, with their diffs retained. No protected VM/configuration access, VirtualBox launch, production change, large validation, protected hashing or acceptance commit occurred.

Prior failures and statuses remain unchanged. Historical 21 AMBIGUOUS / 1 UNMATCHED remain unchanged; historical delay causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

## Next action and rollback

Review this stopped attempt before a separately authorized fresh medium run. Use a new identity, unchanged limits and the validated v5 checker. The orchestration must observe first-tracer readiness and release the existing second-prompt gate promptly, then request the second owner UAC approval. No new timeout or harness correction is justified by this failure.

Rollback requires no production action: leave this stopped candidate and all evidence preserved. No automatic retry, deletion or resumed launch is permitted for this run.

Canonical archive: `{A / 'evidence.zip'}`. Its verified receipt is required; archive success does not change the BLOCKED disposition.
'''
with (R / 'REPORT.md').open('x', encoding='utf8') as f:
    f.write(report); f.flush(); os.fsync(f.fileno())
rows = []
for label, base in [('review', R), ('candidate-and-run', C)]:
    for p in sorted(base.rglob('*')):
        assert not p.is_symlink() and not p.is_junction(), p
        if p.is_file():
            assert p.name != '.env' and '__pycache__' not in p.parts, p
            rows.append(dict(name=label+'/'+p.relative_to(base).as_posix(), source=str(p), bytes=p.stat().st_size, sha256=sha(p)))
assert not A.exists()
A.mkdir()
save(A / 'manifest.json', dict(status='BLOCKED', accepted=False, files=rows))
with (A / 'evidence.zip').open('xb') as out:
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for x in rows:
            z.write(x['source'], x['name'])
        z.write(A / 'manifest.json', 'manifest.json')
    out.flush(); os.fsync(out.fileno())
with zipfile.ZipFile(A / 'evidence.zip') as z:
    assert len(z.namelist()) == len(set(z.namelist())) == len(rows)+1
    assert z.read('manifest.json') == (A / 'manifest.json').read_bytes()
    for x in rows:
        b = z.read(x['name'])
        assert len(b) == x['bytes'] and hashlib.sha256(b).hexdigest() == x['sha256'] == sha(x['source'])
for x in frozen:
    assert sha(x['path']) == x['sha256']
receipt = dict(status='PASS', membersVerified=len(rows)+1, archive=str(A / 'evidence.zip'),
    archiveBytes=(A / 'evidence.zip').stat().st_size, archiveSHA256=sha(A / 'evidence.zip'),
    manifestSHA256=sha(A / 'manifest.json'), reportSHA256=sha(R / 'REPORT.md'))
save(R / 'archive-verification.json', receipt)
save(A / 'archive-verification.json', receipt)
save(A / 'final-disposition.json', disposition)
assert sha(R / 'archive-verification.json') == sha(A / 'archive-verification.json')
assert sha(R / 'final-disposition.json') == sha(A / 'final-disposition.json')
print(json.dumps(dict(disposition=disposition, archive=receipt)))
