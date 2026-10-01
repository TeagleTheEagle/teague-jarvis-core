# CANONICAL CORE STAGE 4 — FINAL ACCEPTANCE

Disposition: **COMPLETE for the identified TEST candidate. Production activation is not authorized. Stage 5 was not started.**

## Acceptance matrix

| Requirement | Disposition | Evidence |
|---|---|---|
| Instance-bound readiness publication | PASS | Prior readiness-publication-fix stress 500/500, focused 8/8, coordinator 25/25; final native/bootstrap/restart groups; frozen runtime hash below |
| Corrected fallback restart invocation | PASS | fallback-result.json; final-suite/fallback-integration.log and fallback-restart.log: 12 + 4 checks |
| Crash-readiness cleanup | PASS | retired-readiness.json (10 files archived/hash-verified before unlink); cleanup-crash-tests.json (115 checks); final-cleanup.json |
| Matching actual packaged clients | PASS | actual-client-6c0b6e1fdb344582b0aa66f24bff9b4f.json: 101 checks; teague.png / intelligence.png |
| Authentication, peer/executable identity, shared Core | PASS | packaged-client evidence, final native/bootstrap, Stage 1/2 and ownership groups |
| Explicit stop/restart, crash recovery, epoch, startup races | PASS | final-suite/full-start-crash-restart.log: 641 checks; referenced raw restart evidence |
| Controller recovery, stale authority and owner isolation | PASS | final controller-recovery: 52 checks; ownership: 27 tests; actual packaged reattachment |
| Cancellation, response commit, event polling | PASS | final response-commit: 306 trials / 4,748 assertions / 0 failures; event-polling: 43 checks |
| Inspection/repair cleanup and accounting | PASS | final inspection, repair, loop, cancel/detach/emergency/drain groups |
| Deep Review integration and fresh process persistence | PASS | final deep-integration, deep-pipe and deep-restart groups; simulated/offline provider only |
| Shared persistent vs transient state | PASS | final lifecycle/restart records, Stage 3 regression, restart helpers; SQLite read-only integrity check: 49 synthetic databases OK |
| Desktop visibility/profile isolation/window lifecycle | PASS | actual package 101 checks; 35 desktop tests; real screenshots |
| Required regression inventory | PASS | final-suite/commands.json: all 33 groups exit 0; 2 pre-existing cross-session-related test skips remain disclosed limitations |
| Final cleanup and integrity | PASS | 202 recorded identities: 0 live, 0 uncertain; 49 namespaces: 0 readiness/temp artifacts; final process sweep: 0 matching TEST processes; 796 package files hash-verified |
| Approvals | DEFERRED | Authenticated workflow not present in approved Stage 4 surface; not counted as PASS |
| Uploads | DEFERRED | Separate authority/persistence review required; not counted as PASS |
| Physical media | DEFERRED | Physical capture/voice unavailable; modeled ownership checks do not prove hardware behavior |

## Exact changes and defect disposition

The fallback helper error was an invocation defect: the required TEST namespace argv was omitted before Core construction. The helper/runtime was unchanged. The final inventory pairs each restart helper with its own immediately preceding integration's fresh TEST root and validates its location and marker.

The fallback helper proves a fresh process/Context/App, lifetime locking and owner-scoped persisted history. It does not itself exercise a named pipe or Electron. Actual readiness, authenticated attachment and full restart are independently covered by the packaged and lifecycle probes. Its final last-response record is explicitly simulated; no paid provider event is claimed.

Ten coordinator readiness records were leaked by the intentional coordinator-crash fixture: fault_case waited for the expected crash but did not call the existing close/metadata cleanup routine. The only new test-source correction in this phase is `self.close(c)` after the expected exit assertion in tests/lifecycle_stage4/fixtures.py. Lifetime-lock/security/runtime behavior was unchanged. Old metadata was copied and hash-verified before exact-path removal, after identity verification. Diagnostic namespace data, synthetic databases and historical failures remain intentionally preserved; these are evidence, not active sessions or stale readiness authority.

The readiness runtime itself remains frozen at SHA-256 `1e1bd911fe49a261d0e852e6901c4c80a2a6312b5b3330aff062b07a523af1a4`.

## Candidate and source identity

Package: `outputs/deployment-test-releases/TEST-PACKAGE-67ec63aa1f1e4b0c845b289a1be09b53` (relative to cr).

Manifest SHA-256: `a4aa4f75aa24608dcc22305af8344a3c04f2305592969d3b95b8c4019d76a625`.

The new immutable candidate uses the previous validated package/build policy, replacing only app/stage4_runtime.py; native-manifest.json also changes source provenance paths. Native binaries remain unchanged. The original package is preserved. No installer or production installation was made.

`accepted-app/` preserves all 61 exact packaged application files, and accepted-package-manifest.json identifies all 796 payload files. `final-integrity.json` and `package-source-comparison.json` distinguish this accepted snapshot from pending repository work. Three pre-existing deployment_test files (contract.py, native.py, package.py) differ in the working tree and are **not** accepted by this campaign; frozen packaged versions are preserved in accepted-app. Generated packaged entry/launcher files are also preserved. The acceptance commit is scoped to this evidence/snapshot and reviewed Stage 4 correction files, not a blanket endorsement of the dirty working tree.

All 33 exact final commands, timings, exit codes and log hashes are in final-suite/commands.json. The full inventory ran once after the three blocker validations. No failed acceptance run was retried away.

## Preserved failures and limitations

- Original missing namespace invocation and earlier readiness failures remain in readiness-publication-fix; previous historical evidence remains unchanged.
- Original historical Stage 1 PermissionError root cause remains **UNCONFIRMED**. Later isolated response replacement and challenge contention findings do not establish that historical cause.
- Restricted-context Electron GPU failure remains an environment limitation; exact DLL/root cause unconfirmed. Actual Electron acceptance used the approved host context without speculative flags.
- The read-only final integrity collector initially received WinError 5 while stat-ing the host-owned packaged TEST namespace under restricted context. The same unchanged collector passed in host context; no ACL/runtime change. Recorded separately in integrity-restricted-failure.txt and integrity-host.log.
- Initial broad process sweep matched only its own pwsh inspector. process-sweep.json is retained; process-sweep-final.json restricts executable names and finds zero TEST processes.
- Two existing cross-session coverage skips remain limitations, not PASS results.
- No real paid providers, physical voice/media, production enrollment or deployment were validated here. TEST provider provenance is truthful about simulation.

## Production and rollback

Production was NOT TOUCHED or activated. No production Core restart, database operation, configuration/authentication change, provider call, key transfer or forced process termination occurred in this phase. All generated state is under explicitly isolated TEST paths. Cleanup uses existing authenticated paths and exact exited TEST identities. The 49 SQLite checks were read-only against synthetic TEST databases only.

Rollback: preserve all evidence and immutable packages. Restore only the cleanup line using fixtures-before.py for this phase, or the five readiness correction files using readiness-publication-fix/before for the preceding correction. Writer/reader protocol versions must remain paired. Do not reset the whole repository or overwrite unrelated pending work. Keep the original immutable package as rollback material; no production rollback is required.

Acceptance commit is permitted only after the evidence archive is hash-verified. Commit receipt will identify the exact commit. **STOP after acceptance. Stage 5 and production activation are not started.**
