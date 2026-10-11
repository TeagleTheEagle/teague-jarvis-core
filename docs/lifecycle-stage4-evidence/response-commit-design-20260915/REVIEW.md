# Stage 4 response commit / cancellation — design review

2026-09-15. **DESIGN COMPLETE FOR REVIEW; RUNTIME CORRECTION NOT IMPLEMENTED.**

The mandatory pre-edit trace identified response persistence outside the normal chat Store path. The user's stop condition, **“another persistence path can bypass the proposed boundary,”** applies to a correction confined to `Store.message` / normal chat. This record proposes a common boundary covering all existing TEST response modes and identifies the narrow Store transaction-interface dependency. It does not grant new provider or lifecycle authority.

Production is unchanged. No source/runtime edits, test execution, Core/client launches, provider calls, production database reads, acceptance commit or Stage 5 occurred in this review. Documentation and evidence bookkeeping are the only writes. Earlier dirty source files were not reset or committed.

## Confirmed failure and limits

Preserved original probe: `docs/lifecycle-stage4-evidence/real-app-probe-1c9bce22f1d045d79e67926776ae2509.json`.

Preserved failure package: `docs/lifecycle-stage4-evidence/event-polling-20260915/`.

That authenticated actual-App probe passed 39 assertions and failed one late-write assertion; its additional authenticated failure-cleanup check passed and the Core exited normally with code 0. Its separate exception-summary entry is not another independently failed test. The uncancelled control increased assistant rows from 2 to 3. In the cancelled case, `CANCELLATION_REQUESTED` returned before the observer released the actual Store call, yet assistant rows increased from 3 to 4. Polling showed `run.failed`, with no `assistant.completed` or `run.completed`. The independent post-exit read-only SQLite observation confirmed four assistant rows.

This establishes the normal-chat check/write race. No new execution took place in this design review. In particular, this review does **not** claim a reproduced cancellation failure in fallback or deep review: those paths currently hold the owners mutex around their final history write. They are additional persistence entry points that a normal-chat-only guard would not cover.

This finding does not establish the cause of the historical Stage 1 PermissionError, earlier Windows memory-access crash or any provider error.

## Complete lifecycle trace and existing boundaries

Line references describe the source hashes captured in `source-inventory.json`; relevant code is preserved as line-numbered text in `source-excerpts.txt`.

| Phase | Current implementation | Persistence / visibility boundary |
|---|---|---|
| Run creation | `stage4_runtime.py:202–237` creates `server.Run`, captures authenticated owner, dispatches one Work and binds the run to that Work. | Normal response provenance is not reserved at admission. The immutable worker/run mapping is established before releasing the worker. |
| Admission and execution | `stage4_lifecycle.py:88–122` registers Work, writes ADMITTED, starts the worker, writes RUNNING and calls the owner-checked function. | ADMITTED and RUNNING are separate atomic JSON journal replacements, outside SQLite. They do not commit an assistant answer. |
| Response generation | `server.py:App.work` writes the user message, executes the existing authorized request and generates an answer. | User message/tool evidence writes are separate transactions. They are not new final assistant responses and must not be deleted by cancellation. External effects and resource use remain conservatively accounted for. |
| Cancellation request | `stage4_runtime.py:559–561` invokes `stage4_sessions.py:183–187`. | Ownership is checked under the owners lock and the Work cancellation event is set. |
| Cancellation acknowledgement | `cancel_request` returns COMPLETED if the worker is already done, otherwise CANCELLATION_REQUESTED. | No database cancellation state is committed before acknowledgement. Worker cleanup is not implied by that acknowledgement. |
| Assistant persistence | `server.py:552–560` checks cancellation, emits answer evidence, calls `Store.message`, then emits completion. `store.py:123–125` opens its own connection. | The assistant INSERT commits when `Store.connect` exits (`store.py:56–64`), before the next completion hook. This is the reproduced race window. |
| Response provenance | The normal `assistant.completed` wrapper at `stage4_runtime.py:209–220` checks ownership again, reserves provenance, then finishes it. | Reserve and finish use their own SQLite transactions. A rejection here cannot undo the already committed assistant row. |
| Terminal worker state | App marks `run.done`; the wrapper derives a worker outcome from events. Lifecycle writes that outcome to the file journal and only then calls `owners.complete`. | File-journal terminal state and SQLite response state are not one transaction. Unknown outcome/persistence failure invokes existing recovery; Core ownership must remain retained. |
| Polling visibility | `stage4_runtime.py:555–558` checks owner and returns Work.done plus the run's in-memory events. | A successful poll or stable event list is not proof of durable assistant state. Final response events must follow the durable response decision. |

### Other persistent response paths

| Path | Existing commit | Consequence for correction scope |
|---|---|---|
| Normal chat | Assistant INSERT, then provenance reserve, then provenance finish: three transactions | Must combine final message and final provenance decision. An extra in-memory check does not close the gap. |
| Explicit text-only fallback (`stage4_runtime.py:239–284`) | Early PENDING reservation; `History.finish(COMPLETED, text, provenance)` under owners lock | Stores the final answer in the provenance table without calling Store.message. Must use the same finalization rule. No provider-routing change is proposed. |
| Explicit deep review (`stage4_deep_review.py:144–175`) | Early PENDING reservation; `History.finish(COMPLETED, text, record)` under owners lock | Also bypasses Store.message. Must use the same finalization rule. No live Astra request or new authority is proposed. |
| Legacy approval result (`server.py:App.approve`) | Writes an assistant result through Store.message | Authenticated TEST approval routes are absent and explicitly DEFERRED. Keep unreachable; do not enable or alter this legacy workflow to satisfy Stage 4. |

`stage4_response_history.py:39–45` already conditionally updates a PENDING row, but it opens its own transaction and is not presently the cancellation acknowledgement boundary. `Context` points it at the same TEST `jarvis.sqlite3`; no second database or Store is necessary.

Cancellation can also originate from detach, expiry, enrollment revocation, emergency stop and drain (`stage4_sessions.py:106–157`; `stage4_lifecycle.py:124–182`). An explicit-cancel-only fix would be insufficient for the previously approved ownership-loss requirements. These entry points must participate in the shared finalization decision without restoring request authority.

## Minimum proposed shared transaction rule — not implemented

1. Reserve an owner/run-bound PENDING response in the existing TEST provenance table before any normal-chat worker can generate or commit a final answer, as already done for the other response modes. Preserve operation idempotency. Failed admission must not leave a record falsely labelled completed.
2. Use one conditional finalization transaction on the existing TEST SQLite database for all three response modes. For normal chat, its assistant-message INSERT and PENDING-to-COMPLETED provenance update must commit together or roll back together. The existing Store should participate in that caller-owned transaction; do not introduce another writer that duplicates its SQL outside Store.
3. Cancellation must durably settle PENDING-to-CANCELLED before returning a successful cancellation acknowledgement that promises no later final answer. The same response decision must govern owner-loss and lifecycle cancellation acknowledgements. No raw renderer flag may determine the owner or decision.
4. SQLite write serialization and a conditional terminal-state transition decide the winner. If cancellation commits first, a later completion cannot change CANCELLED and its assistant INSERT is rejected/rolled back. If completion commits first, cancellation reads COMPLETED, preserves that answer and reports the already-committed response accurately. It cannot rewrite completed provenance as CANCELLED.
5. Preserve the distinction between **response committed** and **worker cleanup completed**. Existing `COMPLETED` in cancellation's result means Work.done; it must not silently be reused for an unfinished worker merely because its response was committed. Proposed minimal result addition: owner-scoped `response_status` (PENDING / COMPLETED / CANCELLED / FAILED), while retaining the worker result. An already committed response may coexist with a subsequent request to stop residual work; the response is never represented as withdrawn. Review this exact acknowledgement contract before implementation.
6. Emit one assistant completion and one response terminal decision only after successful database commit. A failed or ambiguous commit cannot produce success events. Repeated cancellation reads the same durable decision; it does not republish or erase a response. Polling must distinguish response outcome from worker cleanup outcome rather than manufacture two contradictory response terminals.
7. Carry immutable run/work/response association in the existing provenance data, with the inserted message row ID where applicable, so independent verification can attribute rows to a specific run. No schema expansion is proposed. If existing columns/JSON cannot meet the association and recovery requirement, stop again for schema review.

### Locking, deadlines and crash limits to preserve

The approved design prohibits I/O under the admission/owners mutex. A blanket `owners.lock` around Store persistence is therefore not the selected correction. A narrowly scoped per-response finalization guard may order ownership validation, cancellation sealing and the SQLite transaction without holding the global admission mutex while SQLite waits. All entry points must use one lock order; no path may wait for the response guard while holding the owners mutex, and no guard may span provider work, tool work, worker joins or shutdown waits. A database transaction alone does not substitute for owner authorization.

Proposed database lock-wait bound: at most the existing History one-second limit, further capped by the remaining lifecycle deadline, with no retry loop. This is a proposed bound requiring validation, not a claim that OS scheduling can provide a hard one-second completion guarantee. On busy/I/O/commit uncertainty, do not return successful cancellation, do not infer rollback and do not pretend the response is completed. Preserve existing RECOVERY_REQUIRED / retained Core ownership and the 30-second shutdown policy. There is no forced worker termination or refund.

The operation journal remains a separate filesystem artifact. This proposal does **not** claim atomicity between SQLite and the JSON journal. If a crash occurs after response commit but before worker outcome recording, retain the completed response and the unresolved worker outcome; reconcile in recovery without replaying the request or deleting the response. Interrupted cancellation likewise cannot restore authority after restart. Tests must prove this behavior rather than assume an acknowledgement or absence of an event establishes it.

## Exact proposed file scope

No runtime file in this table was changed by this review.

| File | Minimum proposed responsibility |
|---|---|
| `store.py` | Narrow opt-in transaction participation for the existing message INSERT, preserving the existing default production call behavior. This protected shared interface is the additional dependency requiring review; no schema or data migration. |
| `server.py` | Existing gated Stage4 final-response hook uses that shared finalization; normal production path remains unchanged. Avoid a second unconditional Store write. |
| `stage4_response_history.py` | Shared conditional response finalization / cancellation decision and optional transaction participation; owner checks, idempotency, actual provenance and terminal-state immutability retained. |
| `stage4_runtime.py` | Early normal reservation; bind run/work/response; route normal and text-only finalization, polling and authenticated cancellation/detach through the common decision. |
| `stage4_deep_review.py` | Minimal use of that same finalization interface, including failure handling; no provider/model/budget/tool changes. |
| `stage4_sessions.py` | Owner-validated cancellation/owner-loss coordination, without DB I/O under the global lock; retain worker completion and recovery semantics. |
| `stage4_lifecycle.py` | Drain/emergency response-seal acknowledgement integration only, retaining management authorization, deadline, conservative outcome tracking and lifetime locks. |
| `tests/lifecycle_stage4/fixtures.py`, `tests/lifecycle_stage4/test_stage4.py` | Extend the authenticated real-App probe for both transaction orderings and direct TEST SQLite verification; retain the original failing probe and assertions. |
| `tests/provider_fallback_integration.py`, `tests/test_stage4_deep_review.py`, `tests/astra_deep_review_integration.py` | Focused offline regression of existing alternate finalization paths as needed; no paid/provider or physical-media validation. |

The Store interface and coverage across independent History writers are why this review returns before implementation. No new route, approval, upload, provider authority or general lifecycle redesign is requested.

## Validation plan after scope/contract review — NOT RUN

1. Rerun the exact existing authenticated probe: `.venv\Scripts\python.exe -B tests/lifecycle_stage4/fixtures.py --real-app-event-polling`. Keep its original paused-write test and persistence assertion. Do not change the expected invariant to fit the runtime.
2. In isolated actual-App runs, execute at least 100 cancellation-first and 100 commit-first trials, plus 100 unscripted concurrent attempts distributed across repeated TEST process runs. Use bounded barriers immediately around the real transaction boundaries to force both orderings, not sleeps in production or a test-only response implementation. Record every trial and failure; no automatic pass-seeking reruns. Stop on a validation failure and preserve normal authenticated cleanup evidence.
3. Exercise cancellation during generation, duplicate cancellation, a late generation return after acknowledged cancellation, and a completion attempting to overwrite CANCELLED. Repeat with offline text-only and deep-review providers; verify ordinary final content is retained only for the committed winner.
4. Independently query TEST SQLite in read-only mode, including after normal TEST Core exit: match run/work/response/message IDs, owner, final status and row counts. Cancellation-first must have zero new assistant rows for that run and no completed final-response text. Commit-first must have exactly one committed answer and one completed provenance record. Count aggregate rows only as supporting evidence, never as per-run proof.
5. Compare authenticated polling against persistence: one response terminal outcome, stable repeated polls, no duplicate completion, no orphan assistant row, failed/cancelled generations not labelled successful. Worker cleanup may finish later but must not contradict the durable response decision.
6. Validate foreign read/cancel denial, old-family denial after reconnect, detach/expiry/revoke/drain/emergency, admission closed during drain, bounded DB contention and commit failure. Preserve UNKNOWN resource consumption/worker cleanup where applicable. Exercise crash between SQLite commit and file-journal completion without replay or authority restoration, subject to the established identity-verified TEST process cleanup rules.
7. Only if targeted tests pass, rerun the complete approved in-scope Stage4 suite, unchanged Stage1–3 regressions, Python and desktop suites, existing offline provider/history/restart/integration tests, and relevant compilation/JavaScript validation. Preserve every failure; stop on any Stage4 acceptance failure. Broader unresolved matrix gates remain separate and must not be silently marked passed.

## Current acceptance matrix (no new test claims)

| Requirement | Status | Evidence / limit |
|---|---|---|
| Pre-edit lifecycle and transaction trace | PASS — documentation task only | Source excerpts/hashes in this review; not a runtime acceptance result. |
| Event polling: acknowledged cancellation forbids later durable assistant answer | **FAIL** | Original 39-pass / 1-fail actual-App probe; correction and new trials NOT RUN. |
| Owner polling/foreign control denial and uncancelled control | Prior PASS | Original probe; not enough to close the late-write requirement. |
| Controller reauth/lifecycle-only recovery, inspection cleanup, synthetic repair cleanup | Prior PASS for recorded scope | Existing `STAGE4-REMAINING-REQUIREMENTS-20260915.md` evidence; no source changed or rerun here. |
| Demonstrated automated Electron attach/close/reopen and known-work emergency/deadline | Prior PASS for recorded scope | Existing 29-check Electron and recorded actual-Core lifecycle results, not full restart/media acceptance. |
| Full composed real-Core restart/race matrix | PARTIAL — acceptance not satisfied | Remaining-requirements gate 2; not DEFERRED and not newly tested. |
| Full shared persistent TEST state / fresh presence | PARTIAL — acceptance not satisfied | Gate 3; not DEFERRED and not newly tested. |
| Client media watchdog / adapter ownership | PARTIAL — acceptance not satisfied | Gate 4; synthetic evidence still required, physical media separate. |
| Human TEST lifecycle / final client review | PARTIAL — acceptance not satisfied | Gate 5; no manual PASS invented. |
| Final source/evidence reconciliation and acceptance | OPEN — acceptance not satisfied | Gate 6. No acceptance commit. |
| Authenticated TEST approvals | **DEFERRED — WORKFLOW NOT PRESENT IN CURRENT STAGE 4 PRODUCT SURFACE** | User exclusion; not PASS. |
| Authenticated TEST uploads | **DEFERRED — REQUIRES SEPARATE AUTHORITY / PERSISTENCE REVIEW** | User exclusion; not PASS. |

PARTIAL/OPEN identify incomplete in-scope gates and block overall PASS; they are not alternative names for DEFERRED. Full acceptance has not been rerun at this design stop.

## Preservation and rollback

This review changes only its report/evidence and two documentation pointers. Reversing it requires removing only the new pointer paragraphs and this review package; retain the original failure package and all historical records. No runtime rollback is needed.

For the proposed future correction: first snapshot/hash the exact current affected files, including existing uncommitted work, then revert only the new reviewed hunks if needed. Never reset to HEAD or overwrite unrelated changes. Use disposable TEST databases only; preserve failed TEST datasets/evidence, never delete a committed response to conceal the race. Source rollback must not be used to activate an old runtime against a changed production dataset. No production migration or activation is part of this proposal.

## Requested review scope

Approve the shared TEST-only response finalization/cancellation contract across normal chat, text-only fallback and deep review, the narrow opt-in Store transaction interface, and the exact file/test scope above. Approve explicit reporting of an already committed response separately from worker cleanup, without weakening cancellation-first rejection. No schema change, provider routing change, new authority, production activation or Stage5 is included. If implementation reveals a further bypass or requires a broader contract, stop again for review.
