# Stage 6 fresh medium attempt — preserved health-read failure

**MEDIUM_VALIDATION_FAILED. Stage 6 remains INCOMPLETE.**

Run `identity-fb816854880943888ef68df7d4dec0c8` used the corrected `stage6-checker-telemetry-v5` candidate and one fresh identity. Both owner UAC steps succeeded. One attempt, no retry. The previous stopped attempt remains BLOCKED and its 190-member archive was independently reverified.

## Failure and supported cause

The fourth idle probe (PID 18476, creation identity `134345245237272106`) raised `JSONDecodeError('Expecting value: line 1 column 1 (char 0)')` in its wait/health path. Three completed probe rows and a fourth failure row were preserved. Only 4 of 64 declared probes started; the churn and overlap phases did not run. The worker exited 1. Both observers exited 0 through normal cleanup.

The worker health callback reads and immediately parses `app-health.json` (`qualified_worker.py:18`). The observer uses `FileMode.Create` with `FileShare.Read`, truncates that same file, then serializes, writes and flushes it (`timed_monitor.ps1:5`, called at line 39). The health callback is the only JSON parse in the static wait path; the publisher handle check itself does not parse JSON.

The failure-caught QPC `3573060420495` lies inside `output.app-health.json` span `3573060415307` to `3573061160287` at 10000000 ticks/second. It was caught 0.0005188 seconds after that span began; the full span lasted 0.0744980 seconds. This is strong causal evidence of a reader observing an incomplete health publication. Exact read bytes and the truncate syscall timestamp were not preserved; do not claim they were observed. The original callback stack was reduced to exception repr by the worker.

This is a TEST monitor-health transport finding. It does not establish a production JARVIS defect, a v5 compatibility-checker regression, or a historical Windows/storage cause. The strict checker was not evaluated against the incomplete workload; no missing workload or identity evidence was manufactured.

## Observations, not acceptance substitution

| Item | Observed result |
|---|---|
| Fresh preparation | 11/11 checks; 160 hashes; previous 1,766 archive members verified |
| Started / fully recorded probes | 4 / 3 of 64 required |
| Four probe retained-handle closures | All signaled/exited; creation times and kernel exit times agree |
| Probe lifetimes | [0.0731132, 0.0845864, 0.087985, 0.0703282] seconds |
| Recorded hard deadline violations | 0 |
| Maximum heartbeat interval | 1.1054521 seconds, below unchanged 10-second limit |
| Maximum successful health-read age | 0.9029511 seconds; failed read has no valid age |
| Slow heartbeat warnings | NOT CONFIGURED, per approved policy |
| Observed kernel lifecycle rows | 12 instances, 12 starts / 12 stops |
| Kernel loss counters / faults | 0 / 0 / 0 / 0 |
| Application queue | 52 enqueued / 52 persisted / 52 removed; remaining 0 |
| Application finalization | True |
| Final host census | Zero matching processes and zero trace sessions at 2026-09-22T04:23:04.0801949Z |
| Frozen candidate / prior candidate | 160 / 160 hashes unchanged |
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

Rollback: leave this stopped candidate unselected and preserve it and its evidence. No production rollback, VM change, termination or deletion is needed. Canonical archive: `C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 MEDIUM V5 FRESH FAILURE 20260922\evidence.zip`. The hash-verification receipt confirms preservation only; it cannot turn this failed attempt into a pass.
