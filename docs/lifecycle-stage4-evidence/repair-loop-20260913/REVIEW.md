# Stage 4 TEST asyncio host — implementation and review checkpoint

Date: 2026-09-13. **Implementation validated in passing runs; final acceptance remains INCOMPLETE because a subsequent emergency rerun failed.** No acceptance commit. Production activation and Stage 5 remain blocked.

## Exact change

`stage4_runtime.py` now creates one `RepairLoopHost` only when the trusted parent explicitly enables the synthetic repair fixture. Bootstrap creates the Windows asyncio loop's internal wakeup socketpair before installing the permanent TEST audit guard. No provider, renderer or request callback runs in this bootstrap step. There is no added socket-connect exemption, global asyncio-policy change or arbitrary localhost allowance. The audit function's AST is unchanged.

Each registered repair worker borrows that idle loop under a nonblocking exclusive lock. It supplies a fresh single-thread executor and waits for that executor's cleanup inside the worker. Sequential requests may reuse the idle loop; concurrent borrowing and reuse after closure are denied. Unexpected pending async tasks are cancelled and joined, poison the host and return failure rather than being abandoned. If cleanup does not return, the existing tracked-worker deadline retains Core ownership; no forced thread cancellation or refund is inferred.

Core finalization closes the idle host before writing exit readiness. Close runs under a bounded observation: at most two seconds and no more than the remaining thirty-second shutdown allowance. Uncertain closure retains lifetime ownership with `REPAIR_LOOP_CLEANUP_UNCERTAIN`. Ordinary requests gain no shutdown authority. The host owns no Store, provider, voice engine or Core.

Worker exceptions now expose a bounded diagnostic containing phase, exception type, errno/WinError and traceback frame file/function/line identifiers. Exception locals, request contents and credentials are not recorded. The TEST driver checks a completed worker's diagnostic before reporting a timeout waiting for resource events.

Source files changed this continuation:

- `stage4_runtime.py`
- `tests/lifecycle_stage4/fixtures.py`
- `tests/lifecycle_stage4/test_stage4.py`

`docs/CANONICAL-CORE-STAGE-4.md` links this checkpoint. No further budget runner hook was needed. All 23 protected sources, including `budgeted_repair.py`, remain byte-identical to this continuation's baseline. The prior continuation's gated budget-runner change remains separately documented; it was not deployed here.

## Validation actually performed

| Suite/scenario | Result |
|---|---|
| Focused repair worker/accounting | 22 passed |
| No-Core asyncio host with exact extracted runtime audit | 16 checks passed |
| Authenticated TEST App repair cancellation | 44 passed, including final rerun |
| Authenticated TEST App repair detach/reattach | 45 passed, including final rerun |
| Authenticated TEST App repair emergency | Initial 45 passed; final rerun FAILED, retained below |
| Authenticated TEST App shutdown grace/cancellation/settlement | 46 passed; cancellation observed after 10.015 seconds |
| Existing real TEST App deadline/recovery | 36 passed; recovery observed after 30.031 seconds |
| Actual Electron TEST clients/lifecycle | 29 passed; both screenshots inspected |
| Stage 4 ownership / inspection | 27 / 13 passed |
| Native peer identity / bootstrap | 15 / 6 checks passed |
| Unchanged Stage 1 | 24 total: 23 passed, 1 existing skip |
| Unchanged Stage 2 | 36 total: 35 passed, 1 existing skip |
| Unchanged Stage 3 | 43 passed |
| Existing Python suite | 212 passed |
| Existing desktop JavaScript suite | 29 passed |
| Offline provider/router suite | 62 passed |
| Python compilation / protected hashes | 3 files passed / 23 unchanged |
| Permanent audit-guard AST comparison | unchanged |

The no-Core audit test rejects arbitrary loopback (including Ollama when disabled), LAN, remote and DNS calls before connection. It verifies sequential worker reuse, executor joining, concurrent-owner denial, refusal to close a busy loop, fail-closed cleanup of unexpected pending tasks and rejection of a closed loop. It uses the actual runtime audit function extracted from source, not a rewritten approximate policy. The real App runs separately validate that bootstrap ordering under the real hook works.

Actual Electron v44.2.0 screenshots visibly identify both clients as authenticated STAGE4_TEST. They truthfully state physical voice/capture unavailable. They are lifecycle regression evidence, not a manual physical media PASS or a new repair UI demonstration. The repair route was exercised through authenticated Python TEST clients. No real AI-generated repair, Podman execution, paid provider request or physical media use occurred.

Resource accounting still means the existing `core_requests` and `container_checks` attempt units. It is not comprehensive monetary/token accounting: ordinary chat, TTS and inspection remain unmetered by this ledger. Cancellation/disappearance does not prove zero consumption; unknown attempts retain their reservation. The fixed repair callbacks used synthetic outcomes only.

## Subsequent failed run — not erased by prior passes

`real-app-probe-db65476c022c49e28741116b478c9e03.json` failed on the final emergency rerun after 26 preceding checks. The reported error was `OSError [Errno 109] Windows test pipe operation failed`, before the driver received the repair-start response. The tool reported 14920.4601751 seconds of elapsed time for that command.

Preserved readiness was last written at 2026-09-13 04:26:44 UTC; the repair journal was written as NEVER_STARTED around 08:35:23 UTC. The database contains zero reservations and no repair-resource-attempt events were published. This is **not** the previous UNKNOWN/asyncio initialization failure. The retained controller's STATUS returned DENIED. Existing sessions expire after at most 900 seconds, so the long interval is consistent with expired authority. The exact cause of the interruption/broken pipe is unconfirmed; no power/suspend trace or contemporaneous scheduling trace was captured. Do not claim a proven machine-sleep cause, a new production fault, or a successful emergency test from this run.

No automatic rerun or correction followed this failure. All earlier passing records remain intact. The failed test remains a review item preventing this checkpoint from being called an unconditional acceptance PASS.

## Separately approved cleanup

User approved cleanup of only this retained TEST Core PID 17320. Before termination through a held Windows process handle, creation FILETIME `134337472037033242`, executable SHA-256 `372c2eae555b344520bf147be0096e009069aeca4e7f78d6aecea6d53158056a`, TEST namespace `TEST-STAGE4-97ba16ed03404c35b7ea6a4423a9fa5e` and instance `46a83de66b7a4419bd45c62ef2291a9c` matched the preserved evidence.

Only that Core was terminated. Verified venv launcher PID 21584 exited naturally and was not terminated. The retained test controller then exited with the original failed-probe assertion. A post-cleanup STATUS wakeup received FileNotFoundError because the endpoint was gone; it did not launch anything or retry a request. Existing identity/journal/event files remained hash-identical. See `approved-final-test-cleanup.json`.

All other new real TEST App and Electron scenarios reported normal Core exits. No production process was terminated or restarted. Prior cleanup of PID 16580 remains a separate record in the previous checkpoint.

## Rollback and residual limits

Restore only the exact pre-continuation files in `before/`, after checking for subsequent edits. Preserve all current source snapshots, diffs, failed/passing evidence and synthetic TEST roots. Do not reset unrelated working-tree changes, restore/migrate production databases or restart production. This rolls back only the new loop-host integration, not the prior reviewed reservation/worker work or accepted Stage 1–3 logic.

Host creation is trusted TEST bootstrap only. Process-level hangs cannot be made safe by a Python cancellation flag; if a worker or host closer cannot establish cleanup, the existing quarantine intentionally retains ownership. No production lifecycle guarantee is asserted from this synthetic milestone.

Historical Stage 1 PermissionError root cause remains UNCONFIRMED. Its later reproduced response-publication defect, corrected IPC guard contention, the earlier Windows application memory crash and this long-interruption pipe failure are separate findings. Existing Stage 1 cross-session and Stage 2 other-user/cross-session/actual-remote-host skips remain unchanged.

## Review / next gate

Review the final interrupted emergency run and the retained TEST controller's inability to reauthenticate after its session expires. A minimum follow-up should diagnose that controller path under controlled TEST expiry and preserve exact state/exception evidence. Do not lengthen session validity, bypass authentication, replay repair requests or infer restored authority from a prior token. Any correction to the controller's reviewed authority semantics requires review first. No such correction was implemented here.

The broader Stage 4 matrix still has remaining approvals/stream/upload cleanup, lifecycle/race and separately authorized manual/media acceptance work. No Stage 4 acceptance commit is created, and Stage 5 is not started.

PRODUCTION DATABASE MODIFIED: NO  
PRODUCTION CORE RESTARTED: NO  
PRODUCTION CONFIGURATION CHANGED: NO  
PRODUCTION ACTIVATED: NO  
REAL REPAIR EXECUTED: NO  
PAID PROVIDER CALLS: NO  
STAGE 5 STARTED: NO
