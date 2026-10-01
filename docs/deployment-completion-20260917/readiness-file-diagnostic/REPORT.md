# Stage 4 readiness publication diagnosis

Stage 4 remains INCOMPLETE. Production unchanged; no acceptance commit; Stage 5 not started.

## Evidence

The preceding current-source targeted run executed 25 tests: 24 passed, 1 failed. Test 25 encountered a real PermissionError in fixtures.py coordinator_readiness, Path.read_text, before its intended injected exception. Both real TEST coordinators completed authenticated cleanup and exited 0; the subsequent process census found both absent. Preserve ../readiness-resume-20260917/targeted.json and targeted.log unchanged.

Current writer: stage4_runtime.py serve_test_coordinator calls exclusion.write exactly once. The helper closes the temporary JSON writer then calls os.replace. Current reader waits for destination existence, then attempts one strict Path.read_text. The old helper swallowed OSError/ValueError and returned None; that suppression has already been removed from this coordinator reader.

File-only experiment: probe.py creates unique disposable files, performs the same temporary.write_text -> os.replace sequence in a writer thread, and attempts a single strict destination read. It launches no Core, client or provider. No retries or permission changes. Separate trials wait for writer completion as a control.

Evidence: run-2854bc79da2b4158b1cc07930168db1d/result.json

| Condition | Trials | Valid reads | Read failures |
|---|---:|---:|---:|
| Read overlaps rename/publication | 500 | 10 | 490 |
| Read after writer completion | 500 | 500 | 0 |

All 490 failures were PermissionError errno 13 with supplementary thread-local UCRT doserrno 32 (sharing violation). Python winerror was absent. Records preserve original tracebacks and read/replace timings. This is not a native syscall/handle trace. File threads all joined; no subprocesses were launched. This test exercises Windows file sharing independently of JARVIS authentication.

## Disposition

C — lifecycle/readiness synchronization defect is experimentally supported: destination visibility is observable before replacement finishes, and opening with the normal reader can fail in that interval. B — harness synchronization is the affected boundary. Attribution of the specific earlier coordinator run remains inferred because it did not record writer timing/native error. The original historical Stage 1 root cause remains UNCONFIRMED; do not merge that incident with these experiments.

## Minimum proposed correction

Use a bounded publication-complete notification from the TEST coordinator fixture after the readiness write returns. The parent waits for that notification before its single strict read; then all existing independent PID/creation/executable, namespace, epoch and authenticated pipe checks still run. Notification is only sequencing, never identity or authority. EOF, timeout, writer failure, malformed JSON and identity mismatch remain errors. Do not add read retries, arbitrary sleeps, change ACLs or weaken authentication. Installed-fixture callers must be audited before integrating so no caller bypasses the notification.

No correction is implemented in this diagnostic. The required focused suite failed, so restart/full acceptance were not advanced. Next validation must cover notification-before-write rejection, delayed publication, child exit, original-error preservation, authenticated partial-startup cleanup and existing installed fixture compatibility, followed by the approved restart/lifecycle order.

## Changes and rollback

Only this diagnostic script, report and new isolated evidence were added in this continuation. Runtime, fixtures, Stage 1 locks, response-commit and production source were not changed. Rollback requires no runtime action: these are standalone diagnostics and immutable evidence. Retain the failed runs.
