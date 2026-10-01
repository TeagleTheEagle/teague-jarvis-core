# JARVIS Stage 4 — marker correction and stopped acceptance

Full acceptance is **INCOMPLETE**. The only source change in this turn is the approved TEST marker. All 25 targeted tests and the separate 636-check restart/lifecycle gate passed. The full campaign then stopped at its native peer-identity probe: 14 native checks passed and the expected-success check failed. No acceptance commit was created.

## TEST MARKER CORRECTION

- Changed: YES — `tests/lifecycle_stage4/test_coordinator_readiness.py:21`.
- Exact replacement: `SYNTHETIC HARNESS TEST ONLY` → `NO PRODUCTION SERVICES`.
- Runtime files changed: NO. Coordinator/Core/authentication/response-commit/blank-UI behavior unchanged.
- Before SHA-256: `69f8b175ae4fac6decd7dfd5edc50028f7a3e97094f69ed8d9a9f28426da0b5d`.
- After SHA-256: `abb75b247c5e4d9b356c0f1ff64645160eb3f0c3e36f83a6cb804501eeb5b997`.
- Reviewed harness remains `792d96f09da1b37301d217f817ec1500bfc7821392e5b89a64213242d818d68a`.
- See `marker-only.patch`, `before/`, `after/`, and `final-integrity.json`.

## TARGETED TESTS

Executed **25**, passed **25**, failed **0**, errored **0**, skipped **0**, not run **0**. The previously stopped run (23 executed / 22 passed / 1 error / 2 not run) remains unchanged and separately archived. Expected injected negative outcomes in the new test observations are not unexpected test failures.

Exact command: `.\.venv\Scripts\python.exe -B docs\deployment-completion-20260916\harness-marker-resume-20260916-29e5ad71\run_gate.py targeted`.
Commands, outputs, and actual coordinator identities are in `targeted-command.json`, its hash-pinned log and `targeted-results.json`.

## RESTART / LIFECYCLE

**PASS — 636 recorded checks, zero failures.** Coordinator readiness, peer identity, authenticated attachment, restart authorization, shutdown and cleanup passed. This was an actual isolated Core/process campaign, including repeated startup contenders, stop/restart, crash/adoption, epochs and stale-authority checks.

Exact underlying command: `.\.venv\Scripts\python.exe -B tests\lifecycle_stage4\fixtures.py --restart-campaign`, invoked through `run_gate.py restart`.
Evidence: `restart-command.json`, its log, `raw-evidence/restart-campaign-9af593dca2a44fa4af3238520459d011.json`, and `restart-reconciliation.json`.
The post-gate identity check found no surviving matching identity among **95** recorded PID/creation/executable identities before advancing to full acceptance. No additional termination was performed by the reconciliation.

## FULL STAGE 4 ACCEPTANCE

**33 command groups planned; 14 executed; 13 passed; 1 failed; 19 not run after the failure.**
The executed unit/regression suites reported **474 tests, 472 passed and 2 existing skips**. These totals exclude the separately reported targeted tests, native cases, response-commit assertions and restart checks; unlike counting units are not combined.

| Group | Result | Unit-count detail |
|---|---|---|
| response-commit | PASS | Case/assertion evidence; see log and raw report |
| event-polling | PASS | Case/assertion evidence; see log and raw report |
| stage1 | PASS | 24 unit tests; 1 skipped |
| stage2 | PASS | 36 unit tests; 1 skipped |
| stage3 | PASS | 43 unit tests; 0 skipped |
| ownership | PASS | 27 unit tests; 0 skipped |
| controller-recovery | PASS | Case/assertion evidence; see log and raw report |
| inspection | PASS | 13 unit tests; 0 skipped |
| repair | PASS | 22 unit tests; 0 skipped |
| repair-loop | PASS | Case/assertion evidence; see log and raw report |
| python | PASS | 212 unit tests; 0 skipped |
| providers | PASS | 62 unit tests; 0 skipped |
| desktop | PASS | 35 unit tests; 0 skipped |
| native | FAIL | Case/assertion evidence; see log and raw report |

Approvals, uploads and physical media remain **three DEFERRED capabilities**, not passed tests. Their deferral did not excuse the native failure. Actual candidate Electron acceptance, later integration/restart groups and final standalone syntax validation were not run after the required stop. Earlier evidence is preserved but does not substitute for this incomplete campaign.

### Exact blocker

Command: `.\.venv\Scripts\python.exe -B tests\lifecycle_stage4\fixtures.py --native-probe`.
Log: `native-2f1094e39f5941d38e8fe09cfc2d8982.log`.
Structured evidence: `raw-evidence/native-native-probe-66e3b69575ac4f02bc8127e0dad2ab4c.json`.

The `correct` case returned `passed=false`, `error=PIPE_CONNECT:2`, child exit code 0, zero received frames and server exception class `Rejected`. The remaining 14 cases passed. The group exited 1 at `fixtures.py:200` with `AssertionError: Native checks failed; see retained evidence`.

`fixtures.py:199` prints `native checks 15 PASS` unconditionally before checking its results. That console line is misleading and is NOT accepted as evidence of success. The JSON results and nonzero exit establish the failure. No source was changed to address this reporting problem.

The exact connection failure mechanism remains **UNCONFIRMED**. The saved evidence does not include the underlying server exception reason, native-operation timeline or individual native child creation identities. No retry, new reproduction, security relaxation, timeout adjustment or runtime correction was attempted. This failure is not attributed to the marker change or to the historical Stage 1 incidents without evidence. The native fixture uses an isolated pipe, Electron-as-Node clients and disposable idle-process identity targets; it does not launch another JARVIS App/Core.

## Previous failure regressions

- Cancellation/response commit: **PASS**, 306 trials and 4,748 assertions, zero failures/live workers. Direct read-only inspection of the same isolated SQLite database returned integrity `ok` and no answer/provenance/orphan-link issues. Both reviewed legal orderings remain represented in the test evidence; no claim is made that uncontrolled scheduling produced a particular mix. See `response-persistence-inspection.json` and raw race results.
- Event polling: **43 checks PASS**.
- Restart/lifecycle: **636 checks PASS** in the prerequisite gate.
- Cleanup: no matching recorded TEST identities remained in the final observation. Of 133 identities, 131 were absent. Two access-denied PID queries were retained, then read-only CIM creation-time checks proved those PIDs now belong to later `svchost.exe` instances. They were not touched. No native-probe command or runner remained in the current snapshot. Native child identity records were not persisted by this probe, so the cleanup statement is limited to its recorded child completion/wait behavior and the supplemental current snapshot.

## Integrity, preservation and limitations

- All **101** preflight source-hash entries remained unchanged after the marker preflight; the only turn edit is the exact marker diff recorded above.
- Candidate package: `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\deployment-test-releases\TEST-PACKAGE-2966f064bb014c14a13e260937ea4074`.
- Package manifest SHA-256: `fcbd0381f3b4d2b0acd89c15e373418dc27172a60456e3e1698a1963fec091e3`; all **796 payload hashes match**. No rebuild, installation or package modification.
- Source HEAD: `8f0b9bce181800f9339249c4024e396246e94208`; HEAD tree: `e61f7d1df443826556c306ed0359b815c1ca19ed`. The pre-existing working tree is not represented as a clean accepted baseline. Index remains empty.
- The previous marker-error archive and its receipt still match: **17 files**, no overwrite. Original blank-UI/readiness/native and historical failure records remain preserved.
- Historical Stage 1 PermissionError root cause remains UNCONFIRMED. The separately demonstrated response-publication and guarded IPC findings are not retroactively used to establish that historical cause.
- Restricted-context Electron GPU failure remains a disclosed environment limitation; exact missing/inaccessible DLL remains unconfirmed. No GPU flags, runtime changes, driver changes or Windows security changes.
- Existing Stage 1/2 cross-session coverage skips remain skips. No new cross-session proof is claimed.
- Production data was not opened for this collection, copied, moved or intentionally hashed while live. No production Core/configuration/authentication operation or paid provider call was performed. Production-preservation claims refer to this bounded TEST campaign and unchanged monitored source/package hashes, not a claim that the user's independently running production database is static.

## Rollback / review

No runtime rollback was applied. To reverse only this turn's marker change, review `marker-only.patch` or restore this single test file from `before/test_coordinator_readiness.py` after checking its current hash. This intentionally restores the incorrect marker and its isolation rejection; it is not an operational fix. The reviewed prior harness correction and the blank-UI candidate must not be reverted as a side effect. All TEST evidence stays preserved. No production restoration or process termination is required by this report.

Next review item: authorize narrowly scoped diagnosis of the native expected-success connection failure, using the retained report and exact frozen source. Do not change authentication, native bridge behavior or deadlines speculatively. Full acceptance remains blocked until that required case and the remaining campaign pass.

The archive uses an explicit nonsecret allowlist from this evidence directory, rather than the broad database-sync workflow, to exclude unrelated source, live TEST runtime files, credentials, private configs, databases and heavy packages. See `SHA256.json` and `archive-verification.json` for exact copy hashes and destination.

## Final disposition

- Acceptance commit created: **NO**; commit/hash: **none**.
- Production touched: **NO**; activated: **NO**.
- Stage 4: **INCOMPLETE** — native expected-success failure; full campaign stopped.
- Stage 5: **NOT STARTED**.

**STOP FOR REVIEW.**
