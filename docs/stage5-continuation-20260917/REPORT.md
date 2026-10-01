# Canonical JARVIS Core — Stage 5 final acceptance report

Date: 2026-09-17. Scope: isolated TEST Integrated Reliability / Failure Attack campaign.

## Disposition

Stage 5 required campaign and final regressions PASS. Completion includes the independently verified cleanup, source integrity and nonsecret archive recorded in `archive-verification.json`. No production activation or later stage is authorized by this report.

| Gate | Result | Current evidence |
|---|---|---|
| 5A baseline/harness reconciliation | PASS | `prior-campaign/baseline.json`; 61 accepted application files verified |
| 5B ownership/recovery stress | PASS, 604 checks | `prior-campaign/5B-b66773f9a0064c67a98174897db4cb64.json` |
| 5C combined request failures | PASS, 587 checks | `5C-afd137866ba84ae9aee51567593dd0c1.json` |
| 5D actual-client resilience | PASS, 71 checks | `5D-3f9ead9f450843c4855dc314f4df0ccc.json`; actual authenticated packaged Electron clients |
| 5E reconciliation | PASS | `regression-reconciliation.json`, `final-census-1789612441505604600.json`, `archive-verification.json` |

The Stage 5 gates contain 1,262 campaign checks. An additional acknowledgement-loss diagnostic passed 114 checks (`ack-loss-9811b9c804914053ba91793ec82845a3.json`). These are not model-quality or hardware tests.

All 33 final Stage 4 regression groups passed. They include 484 unit/desktop tests: 482 passed, 2 existing skips. Separate integration assertion/trial counts must not be added to unit counts as though they were distinct test cases. Particularly: response commit passed 306 trials / 4,748 assertions; event polling passed 43 checks; full startup/crash/restart passed 641 checks. Exact commands, elapsed times, process IDs, log hashes and all invocation results are preserved in `regressions/commands-*.json`. The reconciliation selects successful current invocations while retaining every earlier failure.

## Baseline and production boundaries

Immutable Stage 4 commit: `d6199756f1e1f4495ad6c3de457660cbf1f03e84`.

Tests ran against `../TEST-STAGE5-APP-9b0e19778db44f1287851eec9f860311`, populated from the accepted Stage 4 application snapshot. The 61 application files match their accepted hashes before and after. No runtime/Core correction was made. Unrelated working-tree modifications were not incorporated into the accepted application snapshot.

The actual-client package is `../deployment-test-releases/TEST-PACKAGE-67ec63aa1f1e4b0c845b289a1be09b53`; all 796 manifest entries verify. Manifest SHA-256:
`a4aa4f75aa24608dcc22305af8344a3c04f2305592969d3b95b8c4019d76a625`.
Runtime SHA-256:
`1e1bd911fe49a261d0e852e6901c4c80a2a6312b5b3330aff062b07a523af1a4`.

Production was not launched, restarted, modified or activated. No production database, enrollment, authentication or configuration was changed. No paid/live provider calls were made. Offline provider fixtures are explicitly simulated; their attribution is not evidence of real OpenAI/Qwen generation. Existing interpreter and public ONNX model dependencies were copied/read for established isolated regression tests; physical media remained disabled/deferred.

## Acknowledgement failure: evidence and minimum correction

Preserved failed 5C run: `prior-campaign/5C-7bf1bb52eb4f4901b6cdc52caf8e50da.json` (228 records, 224 passing, 4 failure/cleanup records).

The client observed `IO_TIMEOUT` during the one-use restart execution, but durable authorization/start records and the coordinator's `start_verified` event prove the replacement Core subsequently started and was authenticated. The original harness appended the Core to its cleanup inventory only after the execute acknowledgement and settle succeeded. Therefore an uncertain acknowledgement could leave an already-started TEST Core untracked by normal cleanup. This is an established harness bookkeeping/reconciliation defect; the native I/O delay itself is **UNCONFIRMED**.

`restart-timeout-timeline.json` identifies the observed authorization, claim, readiness-file timestamp and verified identity. Original T0/T1/T3/T7/T8 exact timestamps were not captured. They are explicitly unavailable, not reconstructed from assumptions. File mtimes are supporting observations, not proof of the instant an API call returned. New `*-timeline.json` records capture execute request/reply/timeout and verified cleanup registration times.

`tests/lifecycle_stage5/continued_campaign.py` changes only the TEST driver:

1. Execute the authorization once.
2. On specifically `IO_TIMEOUT`, use the existing authenticated coordinator status operation and unchanged bounded settle.
3. Require STARTED for that exact operation, durably consumed intent, matching coordinator/namespace/data identity and matching verified Core identity.
4. Register that verified Core for cleanup before the replay-denial check.
5. Reject unreconciled/ambiguous state. Do not replay execute, extend timeouts, restore old authority or weaken authentication.

The dedicated diagnostic deliberately drops the acknowledgement **after** a real accepted execution. It proves recovery from an uncertain acknowledgement; it does not claim to reproduce or explain the original Windows I/O delay. Six start/restart acknowledgements were reconciled across three smoke cycles; 114 checks passed. The fresh combined campaign then passed 587 checks.

Initial retained PID 444 was checked by creation time, executable digest and TEST run identity, then terminated via a pinned handle because the original controller had exited and its in-memory credentials were unavailable. Coordinator 18840 had already exited. Evidence: `retained-cleanup.json`. PID 12400 was unrelated PID reuse and was not terminated (`prior-campaign/pid-reuse-supplement.json`).

## Actual clients and preserved startup limitation

`actual-client-1903d5b3d8814cb29fdc417646558add.json` records a bounded `START_READINESS_TIMEOUT`: the Core acquired ownership but published readiness after the coordinator's existing deadline. It failed closed to RECOVERY_REQUIRED, not a fabricated successful start. The precise reason for delayed initialization is unconfirmed. No timeout or runtime was changed. Its Core PID 6472 was identity-reverified and cleaned up; coordinator 15220 exited (`packaged-failure-cleanup.json`).

The unchanged-package comparison then displayed both authenticated STAGE4_TEST interfaces (`teague.png`, `intelligence.png`), truthfully marking physical voice unavailable. That run later encountered a missing test-driver Electron dependency (`actual-client-d5461e860c2e4169bce7e074b44edbb5.json`, 31 passing records and one driver error). It did not invalidate the successful visible UI observations or become a complete resilience PASS.

`tests/lifecycle_stage5/packaged_resilience.py` supplies the existing hash-verified packaged Electron executable to the driver, rather than assuming a source checkout's node_modules binary. The corrected actual-client resilience campaign passed 71 checks including renderer crash/reopen, authenticated reattachment, stale authority rejection, restart, emergency lifecycle and cleanup. No Electron, renderer, GPU flags, production UI or authentication was changed.

Both intermittent timing failures remain disclosed observations. Later passing runs do not establish their OS-level root causes or erase them. Acceptance is bounded to this machine and the tested conditions; timely startup under arbitrary system load is not proven. Bounded timeout/recovery-required remains the applicable fail-closed outcome.

## Final regression dependency corrections

The disposable source snapshot initially omitted dependencies needed by the wider existing regression inventory. These setup failures were preserved and corrected without runtime edits:

| Failure | Evidence-backed correction |
|---|---|
| Stage 3: 43 setup errors, missing `fixture.sql` | Supply the existing synthetic SQL fixture; matching SHA-256 recorded |
| Repair import: missing `wearables` dependency | Supply import-only source from immutable commit; no wearable capability enabled |
| Python: 3 failures / 5 errors before mocked provider | Trace confirms `server.py:446` reads absent `personality.txt`; supply accepted-commit file in disposable copy only |
| Desktop: 32 pass / 3 fail, missing local interpreter | Supply existing Python launcher/config, dependency search path and public ONNX model files in disposable copy |
| Deep Review pipe: missing report directory | Create isolated evidence directory; no source/runtime change |

Dependency manifests: `regression-inputs.json`, `additional-regression-dependencies.json`, `personality-fixture-source.json`, `desktop-test-dependencies.json`. Diagnostic exceptions: `python-missing-fixture-diagnosis.json`. Every failed log remains under `regressions/*-preserved.log`, with original hashes in command records. The diagnostic Python rerun also observed the same failures; it was not a successful validation run.

Final driver removes credential-like environment variables from regression children. Existing offline/network guards remain in place. `harness-source/` preserves the exact new Stage 5 drivers and evidence tooling. These scripts do not change the accepted runtime.

## Persistence, authority and cleanup

The campaign validates real TEST processes, authenticated malformed/foreign requests, session exhaustion, disconnect/reconnect races, one-use restart grants, stale epoch/session rejection, crash recovery, exactly-one-Core contention and UNKNOWN work handling. SQLite inspection verifies response/provenance consistency independently of the external success status.

Final census:

- 0 live recorded TEST identities; 0 uncertain identity checks.
- 0 matching TEST Python/Electron/Node processes.
- 0 transient coordinator readiness, temporary publication or replacement artifacts.
- 79 TEST databases checked read-only: integrity OK; no response/provenance inconsistency, duplicate or orphan assistant message; before/after database hashes unchanged.
- Terminal `stage4-ready.json`, `core.json`, lock files and synthetic databases are intentionally retained as TEST evidence. They are not live discovery authority and are not deleted to break locks. The report distinguishes this retained terminal evidence from leaked transient coordinator readiness.
- Existing failed-run evidence remains preserved. The original `failure-census.json` was briefly overwritten by re-running its old diagnostic, then restored byte-for-byte from its verified archive; the new observation is preserved separately as `precleanup-census.json`. The original final bytes were verified against the archive.

## Limits and deferrals

Approvals: DEFERRED — workflow not present in the Stage 4 product surface.
Uploads: DEFERRED — separate authority/persistence review required.
Physical media: DEFERRED — modeled lease/cancellation tests do not prove hardware capture/playback.

Existing Stage 1 and Stage 2 cross-session/cross-user coverage skips remain explicit. Remote host, clean-machine deployment, production enrollment/cutover, arbitrary-load performance and live provider behavior are not claimed. The earlier restricted-context Electron GPU failure remains an environment finding; the exact missing/inaccessible DLL remains unconfirmed. Actual Electron testing uses the previously approved host context.

HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

## Evidence integrity and rollback

The nonsecret archive is selected by explicit `archive-allowlist.json`, scanned for credential fields/key material, copied without overwriting historical archives, and destination hashes independently verified. It excludes databases, DPAPI files, configurations, enrollments, grants, session credentials, provider secrets and executables. `archive-verification.json` records the exact destination and results. Public raw regression result files are copied into `regression-evidence/`; historical campaign records into `prior-campaign/`.

Rollback requires no runtime, production or database change: stop using the new Stage 5 harness and retain the unchanged Stage 4 accepted snapshot/package. Preserve this campaign's failure and success evidence. Do not reset the working tree, revert unrelated files, delete evidence or restore stale TEST credentials. Any future removal of disposable TEST installations should separately verify no live identity/lock owner remains.

Acceptance commit: NOT CREATED. This campaign creates evidence and TEST harness changes only; it does not silently commit the repository's pre-existing working-tree changes.

Next gate: owner review of Stage 5 results and separately authorized later-stage scope. No later Core stage begun.
