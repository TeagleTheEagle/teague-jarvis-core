# Stage 4 harness correction — targeted validation stopped

16 September 2026. **STAGE 4 INCOMPLETE. STOP FOR REVIEW.**

The requested TEST-harness correction is applied but not accepted. The first targeted run executed 23 tests: **22 passed, 0 assertion failures, 1 test error**. The fail-fast runner stopped before the two real coordinator integration tests. No TEST coordinator or Core was launched by this run. No restart campaign, full acceptance campaign, acceptance commit, production operation or Stage 5 work followed the failure.

## Exact blocker

`test_23_primary_startup_exception_not_masked` failed before its intended injected readiness error:

```text
test_coordinator_readiness.py:164
  RestartCampaign.coordinator(...)
    stage4_runtime.test_child_command(...)
      validate_root(...)
        harness.validate(...):54
          ValueError: Missing test identity
```

The new test's `setUp()` wrote `SYNTHETIC HARNESS TEST ONLY` into its disposable root's `TEST_ONLY` marker. The existing guard requires exactly `NO PRODUCTION SERVICES`. The guard correctly rejected the fixture. Argument evaluation reached that guard before even the mocked `subprocess.Popen` invocation. The intended PermissionError injection and top-level startup diagnostic assertions were not reached.

This is **a defect in the newly added test setup**, not evidence of a new runtime regression, authentication failure or recurrence of the original readiness None result. The test code and failed evidence remain unchanged after the failure.

**Minimum next correction proposed, not implemented:** change only the new test's marker content to the existing required `NO PRODUCTION SERVICES` value. Use fresh disposable identities on a later authorized rerun; do not change the runtime guard, manufacture a readiness identity, alter preserved failed directories or weaken assertions. Test 23 still must prove original exception preservation, and tests 24–25 still must exercise real authenticated coordinator behavior.

The user's section 5 explicitly says: **“If any targeted test fails: STOP. Do not run the full restart campaign.”** This report honors that stop; no corrective test edit or targeted retry was made after the failure.

## Harness correction

**Source files changed:**

1. `tests/lifecycle_stage4/fixtures.py`
2. `tests/lifecycle_stage4/test_coordinator_readiness.py` (new focused tests)

No coordinator/Core runtime, authentication implementation, lifecycle policy, cancellation/response-commit code, blank-UI bootstrap, production configuration/data or Stage 5 source was changed. The existing packaged TEST driver file also remains unchanged.

Behavior implemented in the harness:

- Strict coordinator readiness UTF-8 read and JSON parse, avoiding the shared helper that discarded errors as None. One read attempt; no read-error retry loop.
- Preserve exception class/message, errno, WinError, traceback, operation/path, timestamp, elapsed time, wait polls and read attempts. Diagnostic records whitelist nonsecret metadata, excluding configuration, keys and session tokens.
- Validate object/required fields and complete readiness peer against the independently captured PID/creation-time/executable pin before dereference or authentication. Keep expected TEST namespace, data identity, endpoint, coordinator epoch and protocol checks.
- Retain the process item before private configuration is sent. Record startup failure separately; never turn cleanup success into startup PASS.
- Cleanup distinguishes `AUTHENTICATED_CLOSE_SUCCEEDED`, `PROCESS_ALREADY_EXITED`, `NOT_ATTEMPTED_IDENTITY_UNESTABLISHED`, `NOT_ATTEMPTED_SESSION_UNESTABLISHED`, authenticated close failure, and close acknowledgement with unconfirmed exit.
- For an incomplete, never-attached startup with an independently recorded live pin, a single cleanup-only readiness read can establish the existing bootstrap prerequisites and use the original authenticated close path. It cannot issue start/restart authorization. Unknown attachment outcome remains retained/fail-closed.
- Already-exited reporting does not index a missing readiness object. Unexpected exit status still fails explicitly rather than being relabelled successful cleanup.
- Preserve compatibility with the existing installed TEST fixture's independently recorded `initial_peer`; do not infer a trusted process pin from readiness contents.

The source diff for this turn is `harness-correction.patch`, relative to the exact pre-edit snapshot, not the much older Git baseline. `before/fixtures.py` and `after/` contain exact source snapshots.

## Targeted tests

Exact executed command, with approved host context, from the JARVIS repository:

```powershell
.\.venv\Scripts\python.exe -B docs\deployment-completion-20260916\harness-readiness-correction-20260916-40d2b891\run_gate.py targeted
```

The wrapper executed:

```powershell
.\.venv\Scripts\python.exe -B tests\lifecycle_stage4\test_coordinator_readiness.py docs\deployment-completion-20260916\harness-readiness-correction-20260916-40d2b891\targeted-results.json
```

| Result | Count |
|---|---:|
| Planned methods | 25 |
| Executed | 23 |
| Passed | 22 |
| Assertion failures | 0 |
| Errors | 1 |
| Skipped | 0 |
| Not run after fail-fast stop | 2 |

The 22 passed methods cover file-error details; JSON/null/non-object/missing fields; UTF-8 failure; publication timeout and early exit; normal modeled readiness/attach/close; incomplete cleanup; missing readiness without authentication; already-exited and abnormal exit reporting; absent/mismatched process pins; namespace/data/endpoint rejection; unknown attach state; authenticated denial; close acknowledgement without exit; and the installed driver's record shape.

Several methods contain subcases; 22 is a count of test methods, not a fabricated assertion count. Expected injected negative outcomes are preserved in `targeted-results.json` and are not independent unexpected campaign failures.

The two unexecuted methods are:

- `test_24_real_authenticated_owner_and_close`
- `test_25_real_partial_startup_cleanup_existing_auth`

The failing method is `test_23_primary_startup_exception_not_masked`. Its guard rejection leaves that end-to-end diagnostic requirement unverified even though helper-level exception-preservation tests passed.

Evidence: `targeted-3709b50d92c640aabdd126593bce6c61.log`, `targeted-command.json`, `targeted-results.json`. Every observed test record has an empty real-coordinator list. No Core-start path was executed. Only the test runner and its wrapper processes were launched; their command completed with exit 1. No force termination or runtime cleanup was needed or performed.

## Readiness / cleanup disposition

| Requirement | Disposition and limit |
|---|---|
| Original exception preservation | **PASS at helper level; PARTIAL overall.** File/UTF-8/JSON/deadline diagnostics passed. Test 23 did not reach the coordinator startup wrapper's preservation assertion. |
| Result validation | **PASS in focused unit tests.** Null/non-object/missing peer/identity cases fail explicitly. |
| Peer dereference protection | **PASS in focused unit tests.** No secondary None/KeyError masks those injected readiness failures. Real workflow remains unrun. |
| Incomplete-startup cleanup | **PASS in modeled tests; PARTIAL overall.** Real partial-start integration test not run. |
| Already-exited process handling | **PASS in modeled tests.** No readiness dereference and no authentication attempt. |
| Authentication semantics preserved | **YES in source scope.** The implementation still invokes existing authenticated bootstrap/close; malformed or uncertain identity/session blocks calls. Actual authenticated negative/cleanup regression is pending. |
| Targeted gate overall | **FAIL — one test setup error.** It is not acceptable to claim this gate passed based on the earlier 22 results. |

## Restart/lifecycle gate

**NOT RUN / BLOCKED BY TARGETED FAILURE.** Coordinator readiness, peer identity, restart authorization, lifecycle transition, actual authenticated shutdown, cleanup and process absence for a fresh restart campaign have not been revalidated against this correction. The prior failed campaign is preserved unchanged.

## Full Stage 4 acceptance

- New full-acceptance groups executed: **0**.
- New groups passed: **0**.
- New full-acceptance group failures: **0, because not run**; this is not a PASS.
- Earlier 31-group run remains **30 passed / 1 failed**, unmodified and not erased.
- Approvals: **DEFERRED**.
- Uploads: **DEFERRED**.
- Physical media: **DEFERRED**.
- No new disposition is claimed for the preserved positive blank-UI, response-commit, event-polling or other acceptance evidence.

## Integrity / rollback

| Source | Before SHA-256 | After SHA-256 |
|---|---|---|
| `tests/lifecycle_stage4/fixtures.py` | `cf38dbb10f91da7b3b01608c425b3ec3d50c9fb54582e507c1c1c7dd23c064f9` | `792d96f09da1b37301d217f817ec1500bfc7821392e5b89a64213242d818d68a` |
| `tests/lifecycle_stage4/test_coordinator_readiness.py` | New file | `69f8b175ae4fac6decd7dfd5edc50028f7a3e97094f69ed8d9a9f28426da0b5d` |

`final-integrity.json` records every comparison. Only `fixtures.py` changed among the prior 101 recorded source entries and 297 tracked-file snapshots. Those source-entry counts can include duplicate paths; they are not unique-file claims. All other recorded files remain hash-identical, including runtime and Stage 5 files covered by the snapshots.

The frozen candidate remains **796/796 payloads unchanged**, manifest SHA-256 `fcbd0381f3b4d2b0acd89c15e373418dc27172a60456e3e1698a1963fec091e3`. The original failed-acceptance archive and prior diagnostic archive were reverified: **133 files including both receipts unchanged**.

Git HEAD remains `8f0b9bce181800f9339249c4024e396246e94208`; HEAD tree `e61f7d1df443826556c306ed0359b815c1ca19ed`; index empty. This task made no acceptance commit and did not reset or stage the unrelated dirty working tree.

Rollback reference: the exact pre-edit `before/fixtures.py` snapshot and `harness-correction.patch`. A reviewed rollback should reverse only this task's patch and new test file, preserving all older uncommitted work. No rollback was applied. The candidate package needs no rollback because it was not changed.

The first evidence collector asserted because it compared a Windows-backslash manifest path with a forward-slash literal. Its initial script and `collection-error.json` are preserved; only collection path normalization was corrected. It was not a test rerun or source correction. Existing snapshots were verified, not overwritten.

New nonsecret source snapshots, diff, failed log, structured results, hashes and this report are archived in TEAGUE INDUSTRIES DATABASE with copy verification. The broad sync script is not used because it would copy unrelated working-tree material. Synthetic runtime directories, databases, keys/configuration and provider/session secrets are not archived.

## Final decision

HARNESS CORRECTION: **APPLIED + NOT FULLY VALIDATED**.

ACCEPTANCE COMMIT CREATED: **NO**. Commit/hash: **none**.

PRODUCTION TOUCHED: **NO**. PRODUCTION ACTIVATED: **NO**. PAID CALLS: **0**. STAGE 5 STARTED: **NO**.

STAGE 4: **INCOMPLETE — the new focused test fixture uses an invalid TEST_ONLY marker; the targeted gate has one error and later validation is blocked.**

The original readiness-read trigger remains unconfirmed. No historical failure was relabelled resolved. **STOP FOR REVIEW of the one-line test-fixture correction before any rerun.**
