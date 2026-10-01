# Stage 6 bounded updater separation — result

**Overall acceptance: INCOMPLETE.** The focused security boundary and normal A→B/B→A sequence passed. Extended interruption validation encountered a preserved 35-second updater timeout; its cause is unconfirmed. Fresh-Windows recovery remains required and unavailable. No production cutover, Stage 7 work or acceptance commit occurred.

## Security result

UPDATER SECURITY CORRECTION: PASS within the fixed authenticated updater model, 26/26 final focused checks. This is not an OS-wide non-execution guarantee against an arbitrary same-user process. See DESIGN.md for the boundary and explicit limitations.

Incoming bytes are readable only within a manifest-bounded verification phase. Staging uses exclusive new-file creation into the protected pending target, hashes copied bytes and revokes each per-file scope. New compile/exec/function construction, child-process execution and non-allowlisted native loading remain denied throughout updater-command execution, including after verification. Core/coordinator and unrelated commands retain the original guard. Owner-only DACL, DPAPI, owner proof, durable intent, enrollment and activation remain unchanged.

The initial adversarial retained-bytes test FAILED. The final execution freeze rejects it, including fabricated filenames and later function construction/native loading. Earlier failures are preserved, not erased.

## Actual update and rollback

Evidence: deployment-2a326813d3394c2781dd2b887bfebb54.json, records 0–104: **105/105 PASS** for package prerequisites and complete normal update/rollback sequence. Later records belong to an interruption case which failed in a source-driver lock helper, not to the completed sequence.

- A→B: PASS. Actual changed Electron/package identities, hash validation, new Core epoch, same canonical data identity, persistent snapshot equality, revoked-client policy retention, stale controller denial, authenticated actual Electron attachment and native loading.
- B→A: PASS. Previous package and data restored through authenticated enrollment/commit/restart; revoked authority remains revoked; no mixed inventory accepted.
- Subsequent A→B plus a real deterministic TEST response: PASS; response rendered and provenance persisted. Naive rollback over newer canonical data was refused.

A package manifest SHA-256: f11d6d52c99045dfdf81a843f01fc50462ddb890011dedc6be537798d10cf8a8

B package manifest SHA-256: 11c26898af666f0cf6201b545c6ca2a5a9b87d97a28effdab0aa1e5111135430

Packages were reused only after matching every application input to the final candidate. These are TEST candidate packages, not production releases or the immutable accepted baseline.

## Extended interruption campaign: incomplete

deployment-2ed83e2ef96d4665a6afd39439f5c56a.json: 150 recorded checks, 149 pass, 1 exception. During preparation of the before-commit case, the existing control communicate deadline expired after 35 seconds. No timeout increase or blind transaction replay was made.

Read-only follow-up found zero processes belonging to that exact TEST installation. Its staged target and expected manifest pin were present. This is not proof of all file hashes, reply delivery, or the timeout mechanism. timeout-readback.json explicitly retains that distinction. The last two commit-interruption cases and later negative-package cases did not finish; do not count them as passed.

## Regressions and integrity

- Deployment policy: 26 tests PASS.
- Response commit: 306 trials / 4,748 assertions PASS, zero live workers.
- Actual Core event polling: 43 checks PASS.
- Final syntax: five modified/new candidate Python files compile successfully.
- Immutable accepted snapshot: 61/61 hashes unchanged.
- Final census: 116 recorded process identities checked; zero remained live. Separate exact-installation process query found zero processes for the timed-out worker's installation. No forced process cleanup was performed.
- The normal update sequence and interruption runs perform authenticated Core/client cleanup. Durable stopped TEST states, partial stages, intent records and synthetic databases remain preserved as evidence; they are not production data and must not be copied with credentials to the project archive.

Do not sum overlapping/repeated runs into a unique acceptance-test total. Full preserved deployment attempts: 5 records/1 failure; 50 records/2 failures; 127 records/1 failure; 150 records/1 failure. All are retained with their original logs.

## Exact candidate changes

Isolated source: C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\TEST-STAGE6-SOURCE-03c76cdb24e84b58b715d4585163c3fc

- deployment_test/update_io.py — new bounded data phases and updater execution freeze.
- deployment_test/bootstrap.py — preload verified control modules; install updater freeze only for five update commands.
- deployment_test/upgrade.py — existing authentication wrapped with scoped authority; use bounded verification and exclusive staging.
- deployment_test/package.py — include the new module in the explicit manifest.
- tests/deployment_contract/completion.py — negative authentication test inspects DENIED directly; lock inspection uses the bound installed helper.
- Evidence-owned run_deployment.py and test_boundary.py — focused adversarial tests, explicit installed helpers and hash-checked package reuse. Regression-input.json identifies the unchanged Stage 5 test source used for the response-commit regression.

final-source/, *.final.diff and final-reconciliation.json contain final source, diffs and hashes. Earlier candidate snapshots/changes.json remain preserved as intermediate evidence. Repository production/runtime files and immutable baselines were not edited.

## Preserved failures and corrections

1. Null executable in Windows subprocess audit event: explicit updater subprocess denial replaced the erroneous Path(None) branch.
2. Replay test expected ValueError; existing exclusive nonce record correctly raised FileExistsError. Test now checks that specific denial.
3. Retained bytes executed under a fabricated filename: demonstrated genuine candidate weakness; fixed with updater-lifetime execution freeze.
4. Freeze initially affected initialization: actual package rejected its lazy Store import before Core creation. Narrowed freeze to update commands.
5. Negative stale-auth test called a success-asserting helper: corrected test to require the raw DENIED result.
6. Source-side installed Core-lock inspection lacked binding: moved read-only check into an explicitly bound installed interpreter. Lock semantics unchanged.
7. Later 35-second control timeout: UNCONFIRMED, unresolved, no retry/timeout padding. It is not classified as an established runtime defect.

## Rollback and next gate

Do not activate these candidates. To abandon them, return to the unchanged accepted snapshot; retain the separate TEST source/packages and evidence for review. No production state needs rollback. Further work should diagnose the recorded updater deadline without weakening guards or replaying uncertain authority, complete the remaining interruption/negative tests, and then perform mandatory fresh-Windows recovery when a qualifying environment exists.

Stage 6 remains INCOMPLETE. Production untouched. Deferred capabilities remain approvals, uploads and physical media. No paid/live provider calls occurred.

HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Original Stage 5 timeout cause: UNCONFIRMED; this new Stage 6 timeout is a separate event.
