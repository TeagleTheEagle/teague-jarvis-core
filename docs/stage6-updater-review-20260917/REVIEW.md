# Stage 6 updater security review

STATUS: BLOCKED

SECURITY CONCERN: An exact-file read-only audit exception is insufficient to preserve the current external-code execution restriction. The same update also requires staging writes currently rejected by that guard. No deployment/runtime source correction was applied.

## Exact current path and authorization

Inspected the preserved Stage 6 candidate, not unrelated working-tree application changes. bootstrap.py lines 32–38 installs no_external_code: an `open` event for .py/.pyc/.pyd is rejected unless its resolved path lies inside the currently executing release. It ignores read versus write and does not independently handle compile/exec. The guard is process-local, not a Windows ACL or cross-process security boundary.

upgrade.operate first calls enrollment.authorize (line 46). That validates request shape, installation/binding, expiry, nonce, owner HMAC and creates an exclusive one-use receipt (enrollment.py lines 31–45). It then acquires supervisor/core locks, checks durable stop, update/fence state, expected package/enrollment and validates the source path before verify_release. Therefore the preserved stage-update rejection happened AFTER owner authentication and transaction admission. No renderer read route or unauthenticated verifier route was identified.

Hash path: upgrade.operate → verify_release → Binding.verify_package → contract.digest → Path.open('rb') → no_external_code. The original full traceback remains in docs/stage6-20260917/deployment-run-03.log. This is established evidence, distinct from the historical PermissionError and unexplained Stage 5 timeout.

## Access actually required

The incoming package manifest and native manifest, every manifest-listed file, and corresponding staged release files must be read to validate hashes, size, inventory and native identity. Only .py/.pyc/.pyd opens currently trigger this particular guard. access-inventory.json records exact package locations and code-file lists from the preserved A/B artifacts.

The staging destination is binding.install/releases/<manifest build>. upgrade.py lines 88–97 copies files and verifies that destination. package._copy checks source safety/nonexistence then uses shutil.copyfile, which opens destination code files for writing. A read-only exception alone therefore cannot complete the existing update. No new destination write exception was granted.

## Disposable probe evidence

probe.py extracts the exact existing audit function using AST and runs it in separate disposable Python processes against harmless synthetic files. It does not launch a Core, use enrollment credentials or change a packaged guard. probe-results.json preserves stdout, errors, source hash and fixture paths.

1. Existing guard: incoming .py read denied; new staging .py write denied.
2. Experimental exact-path, read-only exception: read allowed; `compile`/`exec` of that inert file succeeded; staging write remained denied.
3. Process without the audit hook: synthetic file read/write allowed under the same user. This demonstrates only the hook's process-local scope. It is not an unauthorized authenticated-bootstrap test and does not establish access to production/protected files.

The experiment intentionally evaluates the exception ALONE. It does not prove that a complete narrow verifier/copy design is impossible, nor that untrusted input can currently obtain Python execution. No exploit through an existing JARVIS route was demonstrated. Do not treat successful probe exits as updater acceptance tests passing.

## Narrower design needed before claiming safety

Prefer trusted operations returning verification results rather than a general readable-directory grant:

- After existing owner authorization, pin the exact incoming manifest and file handles; validate exact entries, hashes and non-reparse paths before granting any operation.
- A bounded verifier returns hashes/results, never reusable read handles or source bytes to clients. No callbacks into incoming code. Its scope must be thread/process-local and revoked in finally/on failure; process exit must not persist authority.
- Preserve independent external import/compile/exec/native-loading denial. An open-event exception must not be treated as execution control. Assess this against the actual accepted threat model; an arbitrary same-user Windows process is not constrained by a Python hook installed in another process.
- Keep staging separate: only the already-authorized, exact manifest-relative destination, exclusive creation, no overwriting the active release or unrelated Core state, followed by hash verification. Do not exempt a directory from write checks. Preserve the existing durable update/enrollment/commit sequencing and stop state.
- Reject traversal, reparse/substitution, stale binding/intent, unauthorized requests and unrelated file access. Verify teardown, concurrent access and negative execution cases, then actual A→B/B→A and deployment/Core regressions.

Likely affected files if this design is subsequently implemented: deployment_test/bootstrap.py (guard integration), deployment_test/contract.py (bounded verification interface), deployment_test/upgrade.py (operation lifetime), potentially deployment_test/package.py for an exclusive validated staging-copy operation, and focused tests. Exact-file before hashes are in source-hashes.json. No source diff exists because none were modified.

I cannot certify the proposed read exception as safe on the current evidence. Per the owner's conditional authorization, implementation and real deployment reruns are stopped. No global bypass, security change, additional route or copied credential was introduced.

## Status

UPDATER SECURITY CORRECTION: NOT IMPLEMENTED / NOT VALIDATED

A→B: prior failure preserved; NOT RERUN

ROLLBACK: NOT RUN

FRESH WINDOWS: REQUIRED; owner confirmed unavailable

STAGE 6: INCOMPLETE. Production untouched. No cutover, Stage 7, acceptance commit or baseline modification. Probe child processes all exited with status zero; no Core was launched. Prior Stage 6 cleanup census remains separately recorded, not newly reclassified.

HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Original Stage 5 timeout cause: UNCONFIRMED.
