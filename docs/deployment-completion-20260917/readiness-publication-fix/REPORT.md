# Stage 4 readiness publication correction — INCOMPLETE acceptance

## Correction

The Windows file-only experiment established that observing a renamed destination does not prove the publisher has returned from replacement. Overlap failed 490/500 times with UCRT error 32; writer-completed controls passed 500/500. This supports a readiness synchronization defect. It does not retroactively confirm the historical Stage 1 failure's cause, which remains UNCONFIRMED.

The TEST coordinator now sends PUBLISHING then COMPLETE over its existing inherited stdout pipe, with its unique coordinator name. COMPLETE is sent after temporary write/close and os.replace return. FAILED carries the original exception type, errno, winerror and traceback; the writer rethrows the original error instead of swallowing/retrying it in its connection loop. The reader enforces ordered, matching-instance notification, bounded by the original 8-second startup deadline (25 seconds for installed TEST startup), then performs one strict payload read and unchanged independent process, namespace, epoch, peer and authentication checks. Publication notification is sequencing only, never authority.

No marker files or new credentials are created. A failed writer removes its own temporary file. Normal authenticated coordinator cleanup removes the exited child's readiness file and records its hash. Ten crash-path metadata files remain: see cleanup-reconciliation.json. This is an OPEN artifact-cleanup item, not a full cleanup PASS.

## Exact source changes

- stage4_runtime.py: publish_coordinator_readiness and TEST coordinator publication call/error handling.
- tests/lifecycle_stage4/fixtures.py: bounded notification consumption, strict read sequencing, exited coordinator readiness cleanup.
- tests/deployment_contract/fixtures.py: installed TEST driver uses the same consumer; no existing package rebuilt.
- tests/lifecycle_stage4/test_coordinator_readiness.py: model fixtures explicitly represent completed publication; timeout/exit tests provide notification states.
- tests/lifecycle_stage4/test_readiness_publication.py: eight focused sequencing/failure tests.

Before/after snapshots, correction.patch, source-hashes.json and scope-comparison.json preserve exact scope. The response-commit functions did not change. Diagnostic runners and reports are also in this folder.

## Validation

| Gate | Result |
|---|---|
| New focused publication tests | 8/8 PASS |
| Actual publisher/consumer file stress | 500/500 PASS, zero read failures, zero temporary/remaining files; identity is validated separately, not simulated by these file trials |
| Final coordinator readiness/cleanup tests | 25/25 PASS, including previously failing real coordinator case |
| Full restart/crash/lifecycle | 636 checks PASS, then 636 PASS again in full inventory |
| Native | 15/15 PASS; repeated in full inventory |
| Native readiness unit | 9/9 PASS |
| Desktop/Intelligence tests | 35/35 PASS; repeated in full inventory |
| Event polling | 43 PASS; repeated in full inventory |
| Response commit | 306 trials / 4,748 assertions PASS; repeated in full inventory; zero live workers reported |
| Stage 1 | 24 tests, existing 1 skip, no failure |
| Stage 2 | 36 tests, existing 1 skip, no failure |
| Stage 3 | 43/43 PASS |
| General Python | 212/212 PASS |
| Provider regressions | 62/62 PASS |
| Full 33-group inventory | 32 executed: 31 PASS, 1 FAIL, 1 NOT RUN |
| Changed Python syntax | 5/5 PASS |

Exact commands, exit codes, timing and hashes: validation.json. Raw referenced results: raw/. Full standalone restart result is cited in restart.log.

## Stop reason

The saved inventory launches tests/provider_history_restart.py without its mandatory TEST namespace argument. It exits at line 9 (`sys.argv[1]`) with IndexError before constructing a TEST Core. The following tests/astra_restart_probe.py entry also lacks its required argument and was NOT RUN. The earlier successful command record at docs/lifecycle-stage4-evidence/response-commit-final-validation-20260915/commands.json supplied validated synthetic namespace arguments. Do not reuse historical namespaces blindly: pair each restart helper with the fresh matching integration result and verify process shutdown first. No restart helper or inventory was changed to hide this failure.

## Preserved development failures

- coordinator-cleanup-final.json/log: 10 executed, 9 passed, 1 error. Adding a separate cleanup record displaced the existing terminal result and caused KeyError cleanup_result in test 10. Corrected by attaching artifact details to the existing terminal record; coordinator-cleanup-corrected.json/log is 25/25 PASS. Original failure retained.
- acceptance-fallback-restart.log: required missing-argument failure described above; campaign stopped.
- Evidence collector first invocation failed with AttributeError because one evidence document is a list, not a dict. Its read-only collector was corrected to handle both document shapes; no runtime changes or acceptance rerun. This diagnostic failure is retained here.
- One attempted live progress read during the first restart campaign encountered incomplete JSON while the evidence writer was updating its file. It was not used as acceptance evidence; completed results were read after exit.
- All preceding historical failure folders remain unchanged.

## Cleanup, limitations and remaining gates

cleanup-reconciliation.json covers 262 recorded identities: 260 absent/exited, two reused/different PIDs, zero matching live processes, zero uncertain lookups. No forced termination occurred. Ten coordinator readiness JSON files remain in crash-test namespaces; preserve their identity/hash evidence before reviewed cleanup completion. Historical databases and diagnostic artifacts are retained intentionally; do not confuse them with active authority.

The preserved relocated package TEST-PACKAGE-2966f064bb014c14a13e260937ea4074 still contains the old writer (scope-comparison.json). It is not compatible evidence for the updated installed driver. It was not rebuilt, modified or launched. Matching package/actual Electron acceptance remains unvalidated for this correction.

Approvals, uploads and physical media remain DEFERRED, not passed. The two existing cross-session-related skips remain limitations. The historical Stage 1 cause and exact restricted-context Electron DLL cause remain unconfirmed.

Next: correct the validation invocation to supply each fresh integration namespace; complete both restart helpers, crash-artifact cleanup validation and matching packaged/actual-client acceptance, then reconcile final source hashes and all required evidence. Stage 4 acceptance commit NOT CREATED. Stage 5 NOT STARTED. Production NOT TOUCHED or activated; no paid calls, production configuration or authentication changes.

## Rollback

Restore only the five changed source/test files from the before snapshots (the new test file had no previous version). Do not use repository-wide reset/checkout: unrelated pending work predates this correction. The installed driver and runtime notification writer must move together. Keep all evidence and the original package immutable. No production rollback is needed because production was not activated or modified.
