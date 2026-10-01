# Stage 4 TEST repair cleanup and reservation accounting — review checkpoint

Date: 2026-09-12. Status: **INCOMPLETE — authenticated TEST integration blocked**.
Production activation remains blocked. Stage 5 has not started. No acceptance commit.

## Implemented within the approved scope

- `budgeted_repair.py`: optional trusted lifecycle checkpoint before each resource attempt, and an optional synthetic workflow callback. Existing default repair workflow, confirmation, write-ahead accounting and settlement remain unchanged. Stage 4 dispatch cannot fall through to real repair execution.
- `stage4_runtime.py`: authenticated owner/session-bound TEST repair admission, cancellation and status; fixed synthetic project/task; one registered worker through nested cleanup and settlement; operation idempotency; persistent reservations do not confer execution authority after reattachment/restart. Each journal record carries its budget reference. The fixture is disabled unless the trusted TEST parent explicitly provisions it.
- `tests/lifecycle_stage4/fixtures.py`: synthetic outcomes, no model/patch/Podman execution; cancellation/detachment/emergency scenarios through the real authenticated TEST App path, with independent read-only ledger and journal checks.
- `tests/lifecycle_stage4/test_stage4.py`: 20 focused cleanup/accounting/ownership tests against the existing reservation runner, actual synthetic Store and lifecycle journal. Deadline tests inject a clock and do not start a Core.
- `docs/CANONICAL-CORE-STAGE-4.md`: checkpoint link only.

No change to Store/schema, project budget ledger implementation, real repair workflow/sandbox, provider routing, personality, VoiceEngine/WakeDetector, accepted Stage 1–3 semantics, launchers or production configuration. All 22 protected source hashes still match the pre-work baseline. The gated shared source file `budgeted_repair.py` has changed; the running production process was not restarted or activated with it. This is not a claim that zero production-used source files changed.

## Checks actually performed

| Check | Result |
|---|---|
| Focused TEST worker/reservation suite | 20/20 passed, run 03 |
| Existing `test_budgeted_repair` + `test_project_budgets` | 19/19 passed |
| Four modified Python files, AST and compilation without execution/bytecode writes | PASS |
| Protected source hashes | 22/22 unchanged |
| Authenticated real TEST App cancellation case | **FAILED**, 27 preceding checks passed |
| Real App detach/emergency repair cases | NOT RUN following blocker |
| Full Stage 1–4, Python/desktop/provider regressions | NOT RERUN following blocker; previous passes are historical |
| New physical voice/manual Electron/real repair execution | NOT RUN / not authorized for this gate |

The focused checks cover successful exact-unit settlement, partial consumption, duplicate/concurrent admission, owner isolation, confirmation distinct from budgets, cancellation and detach while cleanup waits, settlement still inside the registered worker, uncertain provider/checker outcome retaining allocation, deadline quarantine, cancellation before execution, closed admission, over-budget rejection, persisted reservation visibility to a separate read-only process, no restored execution authority, expiry/release refusal, corrupt reservation handling, emergency distinct from shutdown, and final journal failure without refunding consumed units.

These are fixed synthetic resource attempts, not monetary/token spend measurement, a real AI repair, or complete resource-budget enforcement. Ordinary chat/TTS/inspection remain outside these two resource counters. Cancellation and missing responses do not establish zero resource consumption.

## All development failures retained

1. Focused run 01: 20 setup errors because the no-App fixture had not initialized the existing workspace tables. No resource worker ran. Full log, machine-readable result and exact failed test source retained.
2. Focused run 02: 20 setup errors because the test passed a SQLite connection rather than a Store to `workspaces.setup`. Corrected only test setup; full log/result/failed test source retained.
3. Focused run 03: 20 tests passed. Later success does not erase either setup failure.
4. Real App probe `ac20f8d828964066bbd59701fa597556`: timeout waiting for the first synthetic repair resource event. Its repair journal records UNKNOWN; authenticated shutdown subsequently could not establish a known outcome. This failed run remains failed after cleanup.

## New integration blocker and evidence limits

The newly introduced Stage 4 worker uses `asyncio.run(...)`. On this installed Windows Python runtime, creating the default Proactor event loop calls `_make_self_pipe()` → `socket.socketpair()` → the Windows fallback `csock.connect(('127.0.0.1', ephemeral_port))`.

The isolated TEST App's existing socket audit gate denies that connection. A separate no-App/no-Core diagnostic reproduced the denial during loop construction, with the full traceback and exact attempted destination in `asyncio-audit-diagnostic.json`. No network connection was permitted. It also preserved the subsequent partial-loop destructor warning. No ACL, security setting, provider endpoint or audit rule was changed.

This **confirms the asyncio/TEST network-policy incompatibility in the isolated diagnostic** and is consistent with the real App's pre-resource failure. The original worker exception traceback/result was not captured by the failed probe; therefore that exact invocation's underlying exception is not independently recovered. Do not promote inference into a captured original traceback. A future approved test should preserve its bounded nonsecret exception evidence before reporting a resource-wait timeout.

The actual failed TEST database has **zero reservation rows**, and no synthetic checker/provider-attempt event was published. Its worker journal is UNKNOWN, its registered workers have unwound (`active_work=0`), and authenticated lifecycle status is RECOVERY_REQUIRED / SHUTDOWN_DEADLINE_OR_UNKNOWN_OUTCOME. No replacement Core was started. No production Core was touched. The lifetime ownership quarantine was not bypassed.

## Approved cleanup completed

User separately approved identity-verified cleanup of only TEST Core PID 16580. Before termination, a held Windows process handle verified creation FILETIME `134336921937816844`, executable SHA-256 `372c2eae555b344520bf147be0096e009069aeca4e7f78d6aecea6d53158056a`, and preserved TEST namespace/instance metadata.

Namespace: `TEST-STAGE4-501064214671471ab3ad2c6445aa8613`.
Instance: `d1725c46e513483a97923d30f4706946`.

Termination used that verified Core handle only. The Core exited 1; its venv launcher PID 21240 exited naturally with 1 and was not terminated. The retained controller then exited with the original failed-probe assertion. A STATUS command that unblocked its input after cleanup received FileNotFoundError because the pipe was gone; it did not launch anything or retry shutdown. Identity/journal/event files were hash-verified unchanged. See `approved-test-cleanup.json`. This operator cleanup is not a successful lifecycle-drain acceptance result.

## Minimum proposed next correction — NOT IMPLEMENTED

Review a narrowly bounded **TEST-owned asyncio loop host** for this synthetic repair integration:

1. Construct only the loop's internal wakeup resources during trusted TEST bootstrap, before installing the request/network audit gate, and retain them as explicit TEST-owned resources. Do not make arbitrary loopback connections available to requests, providers, renderers, or callbacks.
2. Supply the resulting single-owner loop to the registered TEST repair worker instead of calling `asyncio.run`, which creates another loop after admission. Include coroutine completion, executor cleanup and loop closure in the worker/lifecycle cleanup accounting. Do not share a running loop between repair requests or re-use a closed loop.
3. Define bounded preflight/cleanup behavior and preserve UNKNOWN if loop/worker cleanup cannot be established. No inferred refund, force kill, retry or change to lifecycle authority.
4. Capture the fixed synthetic worker exception and phase in the TEST probe before waiting for nonexistent resource events; exclude credentials and response contents.

Exact proposed files: `stage4_runtime.py`, and the already-approved integration tests `tests/lifecycle_stage4/fixtures.py` / `tests/lifecycle_stage4/test_stage4.py`. If an additional budget runner hook is needed, review its precise delta to `budgeted_repair.py` first. No change to global asyncio policy, Stage 1–3, the budget ledger, production network policy or standard repair workflow is proposed.

This design is a proposal, not a validated implementation. Trusted-bootstrap allocation of internal socket resources extends the reviewed TEST runtime boundary, so **new explicit scope approval is required** before implementing it. Broad localhost permission and an audit bypass around arbitrary request code are not proposed.

Focused validation after approval: real TEST loop initialization with normal network denial intact; rejected remote/LAN/DNS/arbitrary-port requests; clean loop/executor shutdown; two sequential repair requests with no loop ownership leak; cancellation during each stage; no refund for unknown consumption; authenticated cancel, detach/reattach, emergency, deadline, known settlement and process exit. Then rerun all required Stage 1–4 and Python/desktop/provider regressions. Preserve every failure. No paid provider call, physical voice, real repair or deployment.

Rollback: restore only this checkpoint's exact pre-edit files from `before/` after checking for later changes; retain all evidence, synthetic data and incident files. Do not reset unrelated working-tree changes, roll back production data, or restart production. Any later async-host implementation must receive its own pre-edit snapshot and can be reversed independently.

## Historical findings and remaining acceptance gates

This is a new async-runtime integration failure, not evidence that the original Stage 1 PermissionError, corrected response publication contention, corrected IPC guard contention, or historical Windows application memory crash shared a cause. Original historical root cause remains UNCONFIRMED. Existing cross-session skips are unchanged and were not rerun here.

Repair-worker cleanup/accounting acceptance remains open until the real TEST App path passes. Broader Stage 4 gates (including remaining approvals/stream/upload cleanup, lifecycle/race coverage and authorized manual/media review) remain open per the approved matrix. There is no Stage 4 acceptance commit or progression to Stage 5.

PRODUCTION DATABASE MOVED: NO  
PRODUCTION DATABASE MODIFIED: NO  
PRODUCTION CORE RESTARTED: NO  
PRODUCTION CONFIGURATION CHANGED: NO  
PRODUCTION ACTIVATED: NO  
STAGE 5 STARTED: NO

**Review requested:** approve only the bounded TEST asyncio loop-host/diagnostic integration described above, followed by its focused acceptance tests and required regressions. Cleanup of PID 16580 has already been separately approved and completed.
