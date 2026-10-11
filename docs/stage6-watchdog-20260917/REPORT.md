# Stage 6 watchdog review: current update path PASS; Stage 6 BLOCKED

Production untouched. Stage 7 NOT STARTED. No release, cutover or acceptance commit.

## Deadline correction

35-SECOND DEADLINE REVIEW: HARNESS DEFECT for the measured current operation. The preserved earlier normal campaign timed out at 35.031 seconds but its updater exited normally at 37.110 seconds. Independent late-timeout-state.json verified all 800 staged files, the manifest pin, stopped state, and absence of enrollment/activation. The old TEST wait rejected that correctly completed staging operation.

HISTORICAL UPDATE TIMEOUT CAUSE: UNRESOLVED. This budget finding does not identify the cause of the original historical event or explain the observed latency variation. Neither event is called a flake.

Only existing harness source changed: C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\TEST-STAGE6-SOURCE-03c76cdb24e84b58b715d4585163c3fc\tests\deployment_contract\fixtures.py
Before SHA256: c70603386d4be0f47e3bd282c3de2f7baf77877a5e68b6557d3a78aa2fb57da0
After SHA256: 1cb675a3a5e7985e1f699c7dccb84527df0ec082b5d675ded991479893d5de01

Added control_timeout(action), used by the fixture's communicate call: stage-update 35 -> 45 seconds; every other control stays at 35. Rationale: ceil(37.110 * 1.20) = 45, a finite empirical test budget with 20 percent headroom, not a claimed universal worst case. No retry, sleep, runtime/security change or weakened interruption criterion. Any future overrun remains a failure; no further increase was made. Exact source/diff: fixtures.before.py, fixtures.after.py, fixtures.diff and change.json.

New campaign.py and repeat_negative.py use this same helper in the existing diagnostic wrapper. They record PID/creation/executable identity before waiting. Their existing bounded post-timeout observation is for cleanup only and never changes FAIL to PASS or replays work.

## Measurements and validation

Prior per-function instrumentation remains in ../stage6-timing-campaign-20260917/timing-summary.json: package/bootstrap preparation, enumeration, hashing, security/path/native verification, staging/fsync, durable intent, native lock acquisition and launch/profile overhead. Inclusive times overlap. This updater stages a new immutable release and uses a separate durable activation commit; it does not overwrite the active release in place. No historical per-phase trace is invented.

Current successful stage-update elapsed seconds: [17.65700000000288, 9.75, 20.062000000001717, 20.25, 23.57800000000134, 25.625].

- full-normal-51d574da97514fb48f2de5e1af1f820e.json: 336/336 PASS. Genuine installed A-to-B, B-to-A, newer-data rollback refusal, six interruption boundaries, invalid package/authority/expiry tests, actual Electron/Core paths and cleanup.
- negative-repeat-59299b19652347588b762cf243bb3482.json: 25/25 PASS on a fresh TEST installation. The formerly-sensitive final preparation completed in 25.625 seconds; full campaign equivalent was 23.578 seconds.
- test_watchdog.py/watchdog-results.json: 8/8 PASS. Correct bound selection; unchanged controls; timeout propagation; no retry or false successful record; real inert child exceeds the 45-second wait and then exits naturally. Observed timeout 45.000000 seconds. This is a watchdog test, not claimed as Core execution.
- boundary_regression.py/security.log: 26/26 existing updater security checks PASS.
- frozen TEST tests/deployment_contract/test_contract.py/policy.log: 26/26 PASS. Policy evidence policy-625e72d5fdd04fa8bbf5724695a04f5a.json.

Total: 361 deployment + 8 watchdog + 52 security/policy = 421 passing checks, zero test failures in this corrected campaign. Counts include lifecycle/cleanup records, not distinct unique requirements. Historical failures remain separate and preserved.

Exact campaign commands: repository .venv/Scripts/python.exe -B docs/stage6-watchdog-20260917/campaign.py (or repeat_negative.py), followed by docs/stage6-separated-io-20260917/deployment-1c0ad3bad7964153a7cdf2ceee603ae2.json. See campaign-01.log and negative-repeat-01.log. The focused scripts/logs above preserve their commands and assertions.

CURRENT UPDATE PATH / A-to-B / BOTH COMMIT INTERRUPTIONS / B-to-A / SECURITY: PASS within tested local TEST scope. Finite repetition does not prove arbitrary-load or clean-machine performance.

## Hashes, preservation and cleanup

final-verification-recheck.json verifies all 61 accepted application files and five candidate runtime files unchanged. Each A/B package retains its original manifest and all 800 files. Only the separate deployment TEST fixture changed. Historical failure hashes match. Native checks found zero live matches among 143 recorded identities, with zero final inspection errors. process-census.json found zero matching TEST installation processes. No forced termination occurred.

Preserved reconciliation anomaly: final-verification.json initially returned OpenProcess WinError 5 for PID 24772. The campaign already recorded the exact child exiting with expected PACKAGE_COMPATIBILITY rejection. The independent pid-24772-recheck.json CIM query found no process, and a separately saved full native recheck passed. The initial failure is not erased; its transient access-denial cause is unconfirmed. No permissions changed and no connection to historical Stage 1 is asserted.

Documentation-only failure: the first report write failed due to the default cp1252 encoder rejecting an arrow character. Its empty artifact is preserved as REPORT-empty-encoding-failure.md; this report uses explicit UTF-8. Runtime/tests were unaffected.

## Remaining Stage 6 and Stage 7 gates

Fresh Windows recovery: ENVIRONMENT REQUIRED / NOT RUN. CLEAN-WINDOWS-QUICKSTART.md provides the owner setup procedure; the detailed earlier plan is linked. No qualifying VM exists, and no host installation/security setting was changed. The development Windows installation, macOS, copied development profile or developer VM image do not substitute.

The existing clean-machine contract also requires reviewed identity-bound owner recovery: current-user DPAPI enrollment cannot simply be copied across machines, and a new data identity is not restoration. This remains part of the open recovery gate, not an implemented or validated capability.

Clean-machine backup/restore, canonical production-path verification, verified pre-cutover production backup and remaining cutover prerequisites are unexecuted. Conditional cutover authority is acknowledged; its conditions have not passed. Stage 7 actual release install/update/uninstall/reinstall/regression and final installer verification remain NOT RUN. Unrun gates are not observed execution failures. No final release build, final release commit or installer hash is available.

## Rollback

After ending TEST runs, restore the single fixture from fixtures.before.py and verify its before hash to reverse this harness correction. Preserve all reports and failures. No application/production rollback is necessary; packages are unchanged. No schema, provider, authority, autonomy, feature or Stage 8 work occurred.

HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
