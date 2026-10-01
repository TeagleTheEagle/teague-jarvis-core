# Stage 6 workspace-binding v4 — offline implementation result

Status: WORKSPACE_BINDING_AMENDMENT_IMPLEMENTED_AND_TESTED, subject to the accompanying verified archive receipt.

Scope: prospective TEST successor only. No live diagnostic, UAC, collector, probe workload, medium/large validation, protected access, production change, or acceptance commit. Stage 6 remains incomplete. Relocated **live execution remains unproven**.

## Candidate and preservation

Candidate: `D:\JARVIS-STAGE6-LIVE\fb0bf86657a64aff85a1799db37e94c7\code`

Fresh failure-preservation destination: `D:\JARVIS-STAGE6-LIVE\fb0bf86657a64aff85a1799db37e94c7\preservation-v4`

229-file source manifest SHA-256: `d2f6738f5d7c3f22fe361f6cb1da174f630d8e150574009b59825d88321ed4d7`.

The 12 copied synthetic files total 786,432 bytes. Their original content hashes are retained; the allowlist, file identities and modification-time baseline bind the new destination. Protected roots are empty and realProtectedAccess is false. No links substitute for copied content.

DLL SHA-256 remains `ff2454390795bb302cdb68990b7f52fc02db7efedb55d2bbd3dd2cbd0e1da7ef`. Both Python and PowerShell loaded this exact candidate-local module and verified its loaded path. Neither invoked RunCollector. The DLL was not rebuilt.

## Changes

Exact absolute paths, predecessor/new hashes: `changes.json`. Complete text diff: `implementation.diff`.

New modules: workspace_binding_v4.py, evidence_format_v4.py, candidate_dll_v4.ps1, runtime_scope_v4.ps1, external_driver_v4.py, small_launch_v4.ps1, small_finalize_v4.py, failure_preserve_v4.py, one_run_v4.py, test_binding_v4.py.

New policies: shared-runtime-v4.json and preservation-policy-v4.json.

Only in the new copy: baseline-allowlist.json now names the local synthetic dataset; native_bridge.py uses the verified local DLL loader; timed_monitor.ps1 selects the declared runtime/module scope. Its event collection logic is unchanged. The successor source manifest was regenerated. The predecessor was not edited.

The existing small declaration schema, small_check_v3.py, completed_v3.py, coordination_v3.py, terminal_control_v3.ps1, native binaries, ETW code/configuration, queue logic and shutdown ordering remain unchanged. Frozen checker SHA-256 remains `e6fbefd3fd463c6c8e09d0e8273a81b46ee2806515cae05e7837ea905a3e69d6`.

## Binding and runtime boundary

Exactly four dependency classes are declared: RUN-LOCAL; CANDIDATE-LOCAL; APPROVED SHARED RUNTIME; FORBIDDEN OLD-WORKSPACE DEPENDENCY.

The separate workspace-binding-v4.json records run/root identity, candidate manifest, 12-file dataset content/metadata baseline, DLL, observers, probe, scripts, runtimes, preservation tool/policy/destination, unchanged declaration digest, entry points and environment policy. Exact recomputation is required before launch and before finalization/preservation. See BINDING-SCHEMA.json.

Runtime identities include four explicit executables and 1,055 supporting files. Python, pwsh, Windows PowerShell and logman use fixed paths. Python stdlib/native runtime and required PowerShell/.NET files are hashed; Windows system-component resolution is explicitly declared, not copied. This is dependency verification, not a claim that the host runtime cache or Windows is immutable. Site-packages are not used by the approved path. No whole environment dump is recorded. Child PATH, module roots, no-user-site and D: TEMP/TMP settings are process-local only; no machine environment is modified.

Old workspace references in relevant environment/CWD/import resolution fail preflight. Candidate paths reject traversal, reparse points and missing/mismatched local files. No old dataset or DLL fallback exists. Preflight and finalization rehash shared dependencies; this is not an OS-enforced lock over the whole Windows/runtime installation. Any detected drift fails closed.

## Evidence-format amendment

Only loss-diagnostic-v2.json and detail/loss-diagnostic-v2.json are added to successor admission. Their exact schema, fresh run, channel, observer-ready/final session identity, frequency, diagnostic-only flags and content hash are checked. Unknown artifacts remain rejected. These sidecars confer no lifecycle, identity, cleanup or acceptance authority. The unchanged checker still determines trace loss, identity, deadlines and lifecycle correctness.

Successor success finalization refuses preserved failures and requires completed terminal evidence first. Failure preservation stays NON-ACCEPTANCE with acceptance_seal=false, preserves the first failure, reports missing/invalid binding or diagnostics explicitly, and never turns later cleanup into PASS.

## Validation

Final offline total: **173 tests passed**: 41 new binding/evidence tests; 54 coordination tests; 30 telemetry tests; 48 original preservation/wrapper regressions. Original-suite runs validate retained logic and historical disposition; they are not claimed as live successor acceptance.

All 27 requested negative categories are represented by numbered tests 01–27 in test_binding_v4.py. Additional cases cover wrong session, import escape, runtime tampering, unchanged declaration, global-environment preservation, and an actual disposable NTFS junction rejection.

Positive PASS/FAIL archive integration exercised real archive creation/readback with mocked lifecycle/census dependencies. These are clearly **OFFLINE FIXTURES**, not proof that real observers or a collector completed. Existing historical failed evidence remains failed.

Syntax: AST parse of all 124 candidate Python files; PowerShell parser checks of four affected scripts. PowerShell Add-Type compiled the new loader helper during the load-only check. No native C++ source changed and no native binaries were rebuilt.

Exact commands/stdout/stderr: offline-*/ and verification-5b9bb343a0f44c4db35b1fe1feb4f004/. Final successful focused run: offline-8ea3aa308e0648cd958cbe44d00073ec/.

## Preserved transitional failures

The initial read-only PowerShell expression had a parser error; no body ran. The first new-test syntax check found a trailing-backslash string error; no tests ran. Both were corrected only in new action material. A subsequent 40-test run recorded 39 passes and one failed fixture assertion: its synthetic census omitted evidenceRoot, so fail-closed preservation correctly withheld uncertain evidence. The fixture was corrected; preservation logic was not weakened. Original output, failed fixtures and later successful results are retained separately.

## Integrity, cleanup and limits

Final preservation verification: 217 predecessor files, 223 recorded inputs, 482 earlier inputs, the 83-file failed live run, 216-file earlier candidate and four original preservation-tool files unchanged. Historical archives reopened and hash-verified: 105, 299 and 10 members. Exact before/after records: before.json and final-verification.json.

Read-only host census: zero matching diagnostic processes, zero trace sessions, zero VirtualBox processes, no unknown census entries. No diagnostic observer, worker or trace session was launched in this action. Ordinary offline test/syntax subprocesses exited. Test directories, deliberate malformed fixture files and a sacrificial junction remain preserved; they are not live processes or acceptance runs. Archive traversal never follows the junction and excludes .env fixture files.

Production and protected VM/configuration were not accessed or modified by this action. This claim is based on the bounded operations performed; it does not rely on hashing the forbidden protected paths.

Historical 21 AMBIGUOUS / 1 UNMATCHED remain unchanged. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED. Historical trace-loss cause: UNCONFIRMED. No evidence establishes that prior ambient resolution actually selected a stale binary.

## Rollback and next action

Rollback is to decline use of this unactivated successor and retain its evidence. All predecessor bytes and policies remain available unchanged. No source restoration, production rollback, VM operation or deletion is needed.

The corrected prospective procedure is ONE-RUN-OWNER-REVIEW.md. It requires a new explicit one-run/three-UAC authorization. Do not run it under this offline authorization. No automatic retry, medium/large validation, protected hashing, or next gate is authorized.
