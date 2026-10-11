# Canonical Core Stage 1 — Windows lock harness

11 September 2026. TEST ONLY. Stage 0 direction accepted; Stage 1 implemented independently of production. Stage 2 authentication NOT implemented or authorized. No installer, production lifecycle/data/auth/provider/device changes.

## Result

Final run: 20 discovered tests, **19 passed, 1 skipped**, 0 failures/errors, 28.656 seconds. Forty-six isolated namespaces, 35 Core lock acquisitions, 9 surviving-Core adoptions/reconciliations and 12 RECOVERY_REQUIRED outcomes. No final namespace recorded more than one Core acquisition (a stricter condition than no concurrent owners, for these bounded scenarios). Exclusive acquisition is enforced by Windows, not an application counter. This is experimental evidence, not a proof against all possible schedules or malicious peers.

Cross-session/fast-user-switching remains explicitly UNVERIFIED. Stage 1 same-session evidence passes; unconditional cross-session acceptance is not claimed. No production regression totals are claimed: only the isolated harness and Python compilation ran in this stage. The harness imports no production modules.

## Implementation and primitive

tests/lifecycle_stage1/harness.py is a standard-library-only Windows fixture. It uses CreateFileW with GENERIC_READ|GENERIC_WRITE, share mode zero, OPEN_ALWAYS, FILE_FLAG_OPEN_REPARSE_POINT and NULL security attributes. Each lock is an OS-held exclusive file handle, retained for its owner's lifetime. No file deletion or existence check breaks a lock. Sharing violation means occupied; other errors fail closed. Non-inheritance is checked with GetHandleInformation for every acquired handle.

This primitive was selected because exclusion includes read/write/delete opens and lasts until the handle closes, including owner-process termination. Existing files can be reused without unlinking. NULL security attributes create a non-inheritable handle. These are documented Windows semantics, tested here on Windows with separate processes. [Microsoft CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).

supervisor.lock serializes startup decisions. core.lock is separately owned by the Core fixture and survives supervisor death. A coordinator owning its lock checks Core ownership, then reconciles an existing live fixture or starts one if absence and intent permit. A durable TEST intent record prevents blind retries after uncertain spawning. A durable TEST stop latch prevents restart after explicit stop.

Identity is a TEST namespace, per-start random epoch, PID and OS process creation time, checked against a live process. A fresh file-based challenge/response demonstrates liveness of the cooperative fixture while its code holds core.lock. Metadata alone cannot establish identity; a busy lock with missing/unreconciled identity gives RECOVERY_REQUIRED. This is NOT secure authentication, trusted executable enrollment or proof that an adversarial process owns the handle. No pipe, bearer token, provider key or Stage 2 mechanism was introduced.

## Isolation and assumptions

All workers use stable lock names in an explicitly labelled per-case TEST directory under tests/lifecycle_stage1/evidence/TEST-<run>/TEST-<case>. Namespace directories remain stable throughout every race/recovery in that case and are preserved afterward. Each new run creates fresh independent namespaces. The worker refuses paths outside its fixed evidence base, missing TEST_ONLY markers, missing ancestors, directory lock targets and reparse ancestors/targets. It does not create or discover production data.

Workers run with an explicit minimal Windows environment, no inherited provider configuration, -I isolated Python mode and hidden windows. Lock handles are non-inheritable. No JARVIS App, Store, database, memory, personality, provider, voice or registry is imported/constructed. Generic fixture names “Core” and “coordinator” do not denote assistant implementations.

The test directories inherit workspace ACLs; no ACL/security policy was changed. The path checks assume cooperative processes and no malicious concurrent ancestor replacement. They do not claim race-free production path hardening, hard-link resistance, secure ACL validation or same-user malware protection. The access-denied test uses a readonly fixture file to obtain real Windows error 5, not a simulated exception or a changed user permission. The reparse test creates a junction whose source and target are both inside test evidence; it is retained, not recursively copied into records.

## Cases and repetition

| Test | Actual coverage/result |
|---|---|
| Two coordinators | 4 rounds; one startup owner, one waiter, one handshake/Core acquisition each |
| Eight coordinators | 4 rounds; one startup owner, seven waiters, one Core each |
| Independent Core | Core holds its lock while supervisor lock is freely acquired |
| Supervisor exits, Core survives | 3 rounds; replacement adopts same identity, no second spawn |
| Crash before spawn | 3 rounds; owner exits abruptly, replacement starts safely |
| Crash after spawn before handshake | 3 rounds with delayed metadata; no second spawn, eventual adoption |
| Core crash | Abrupt exit immediately after lock acquisition and after metadata publication; lock reacquired afterward |
| Stale metadata | Invalid metadata without lock does not count as adoption; controlled start replaces fixture metadata |
| Busy lock, missing identity | RECOVERY_REQUIRED, no spawn |
| Stop/start race | 4 rounds, four coordinators per round against existing Core; no new spawn |
| Handle inheritance | Both supervisor.lock and core.lock tested with close_fds=False child launch; parent exits, child remains alive, lock reacquired |
| Same-user Core contention | 4 rounds of eight Core contenders; one acquisition, seven busy results per round |
| Cross-session | SKIPPED: no second Windows session/user-switch performed |
| Invalid paths/access denied/reparse | Missing directory, directory lock target, actual error 5, junction rejection; pass |
| Other crash boundaries | 3 rounds each after intent/before spawn and after handshake; unknown intent blocks, known survivor adopted |
| Foreign namespace | Non-test directory rejected |
| TerminateProcess | Owned fixture terminated through Popen, real OS lock released |
| Stop then later start | Explicit stop latch retained; no automatic respawn |
| PID reuse protection | Live PID with wrong creation time rejected |
| Busy lock, invalid identity repeated | 3 rounds; no start, RECOVERY_REQUIRED |

Each case records process IDs, monotonic event times, namespace, identity metadata and lifecycle outcomes. The runner waits for recorded Core processes to exit, comparing creation identities rather than killing arbitrary PIDs. Its teardown signals stop and terminates only subprocess handles it created. Core fixtures have a 15-second maximum lifetime as a test safety bound, not a proposed production shutdown policy. Descendant inheritance probes self-exit after three seconds.

## Failure discovered and correction

Initial run: 17 tests, 16 passed/1 skipped in 27.420 seconds. Added an adversarial ordered stop-then-start case. The expanded run exposed missing shutdown intent: after Core stopped, a new coordinator could spawn another fixture. Twenty tests ran in 29.656 seconds, with two assertion failures in that single case (the spawn assertion and teardown's one-acquisition assertion), one skipped. Two sequential acquisitions were observed; this was not demonstrated simultaneous lock ownership.

Correction: check the persistent stop latch under supervisor.lock before any reconciliation/start decision. Final full expanded run passed 19/20 with only the cross-session skip. No production fix was made because this bug was in the new test harness only.

## Evidence and files

- tests/lifecycle_stage1/harness.py — fixture processes, locks and cooperative identity reconciliation.
- tests/lifecycle_stage1/test_stage1.py — multi-process runner, assertions, evidence capture.
- tests/lifecycle_stage1/.gitignore — excludes raw evidence trees (including junction) and Python cache.
- docs/lifecycle-stage1-evidence/initial.json — original successful run.
- docs/lifecycle-stage1-evidence/stop-latch-failure.json — failed expanded run, retained honestly.
- docs/lifecycle-stage1-evidence/final.json — final passing run with all case events.
- This report.

Final tested source SHA256:

    harness.py AF3091281DFF9038AEDC0A25B33CA2F0BDEA9CDAAE435F04DAE2E4ABD4B80885
    test_stage1.py 3320ADCB79276A3E7F05F831BA823EB48D269C82B4649BAAAC4B417661DE9EE3

Re-run from the existing JARVIS repository:

    .\.venv\Scripts\python.exe -I tests/lifecycle_stage1/test_stage1.py

No administrator rights were requested to execute these tests. No login, restart, microphone, screen capture, live provider request or production application launch occurred. Documentation/source/evidence copies alone are saved into the Teague Industries record folder. The discrete commit contains only the seven named Stage 1 files; unrelated working-tree changes remain outside it. The commit ID is reported with delivery.

## Remaining limits and stop

Cross-session behavior needs a later authorized Windows-session test. ACL-denied access under another user, malicious path replacement, hard links, antivirus/filesystem-filter interference, abrupt Windows reboot, power loss and network filesystems were not tested. Locks were tested on this local Windows workspace only. Cooperative challenge files are intentionally not a production authentication mechanism. Ambiguous spawn intent remains recovery-required rather than automatically cleared. Automatic crash restart and production shutdown/restart integration are outside this harness.

STOPPED at Stage 1. Do not activate Stage 2 authentication or any production lifecycle changes until this evidence is reviewed.

