# Stage 4 event polling — reproduced late-write failure

2026-09-15 — **EVENT POLLING: FAIL. STOP FOR RESPONSE-COMMIT BOUNDARY REVIEW.**

Approvals: **DEFERRED — WORKFLOW NOT PRESENT IN CURRENT STAGE 4 PRODUCT SURFACE**.

Uploads: **DEFERRED — REQUIRES SEPARATE AUTHORITY / PERSISTENCE REVIEW**.

These explicit user-authorized deferrals are exclusions, not passed tests. They do not reduce the event-polling contract. No approval/upload routes, authority or persistence behavior were added.

## Exact executed test and result

Command, from the authoritative repository:

```powershell
.venv\Scripts\python.exe -B tests/lifecycle_stage4/fixtures.py --real-app-event-polling
```

One run, exit code **1**. **39 assertions passed, 1 assertion failed**, plus one successful authenticated failure-cleanup check. The JSON also contains a separate exception-summary record; that is not a second independently failed test. No rerun was used to erase the failure.

Original result: `docs/lifecycle-stage4-evidence/real-app-probe-1c9bce22f1d045d79e67926776ae2509.json`. Raw output: `real-polling-01.log`. TEST namespace: `TEST-STAGE4-ea4e9abf596b4021a4712646914cdb94`. TEST child launcher PID recorded as 6528; its Core exited normally, code 0. No forced termination or retained TEST controller was required.

The probe uses one actual isolated App/Store, the existing Stage 2 authenticated pipe client, current ownership/lifecycle modules and the existing deterministic provider. It first runs the standard 26 actual-App integration checks, then one uncancelled control and one cancelled commit-boundary scenario. No production credentials, paid calls, microphone, upload, real repair or production data were used.

### Scheduling injection and its limits

Only `tests/lifecycle_stage4/fixtures.py` changed. A distinct parent-selected `--polling-app-worker` entry wraps construction of the existing real TEST App. Its observer temporarily pauses the existing bound `Store.message` invocation for the next armed synthetic assistant response, immediately before invoking its actual implementation. It then calls that original implementation exactly once. It does not inject an INSERT, alter returned events, suppress cancellation, replace the database, modify Store code or weaken authentication. Immutable TEST latches release the pause; a five-second bound prevents an indefinite held worker. No remote operation can select that observer.

This deliberately widens a source-level scheduling window, not a claim about natural failure frequency. The uncancelled control validates the same observer and real write path. Parent cancellation acknowledgement precedes release by explicit test sequencing. The fixture does not invent a successful cancellation outcome.

## Observed behavior

| Check | Result |
|---|---|
| Owner can poll a real active request | PASS, control and cancelled scenario |
| Foreign owner cannot read its events or cancel it | PASS, both scenarios |
| No assistant write while paused | PASS |
| Uncancelled release commits exactly one answer and emits successful completion | PASS; assistant rows 2 → 3 |
| Owner cancellation acknowledged before release | PASS; CANCELLATION_REQUESTED |
| Cancellation is not immediately mislabeled worker completion | PASS; done remained false while held |
| Terminal event poll stable across repeated reads | PASS, both scenarios |
| Cancelled request cannot commit late assistant content | **FAIL; assistant rows 3 → 4 after cancellation acknowledgement** |
| Authenticated failure shutdown | PASS; Core exit 0 |

The cancelled request's terminal event types include `run.failed`, with no `assistant.completed` or `run.completed`. The assistant row nevertheless exists in the real TEST SQLite database. A subsequent independent read-only query after Core exit confirms four assistant rows. Aggregate response provenance contains three completed records; that aggregate is not used to invent per-operation attribution. Counts and event names are preserved without archiving conversation content or credentials.

## Exact mechanism supported by evidence

`server.py:App.work` checks `run.cancel.is_set()` and chooses the final-answer branch. It then emits answer evidence and invokes `Store.message` to persist the assistant answer. After that write, it emits `assistant.completed`.

`stage4_runtime.py:Context.start_request` wraps `assistant.completed` with `owners.next_step` before recording final-response provenance. Cancellation acknowledged in the interval before SQLite writing is therefore noticed **after** the assistant message is saved. The later ownership check rejects completion; the App reports failure, leaving persisted answer content inconsistent with the failed event outcome.

The reproduction demonstrates this race in the actual TEST integration. It does not diagnose any historical Stage 1 PermissionError, Windows application crash, API error or prior long-interruption incident.

## Why a runtime correction was not implemented

Moving the existing ownership/cancel check immediately before `Store.message` leaves a check/write race. Deleting the row afterward also violates the requested no-late-write contract and can expose content before deletion. Treating CANCELLATION_REQUESTED as permitting arbitrary new answer writes would weaken the acceptance criterion.

A reliable correction needs an explicit final-response commit/cancellation linearization rule: persistence and final events must be consistent with whether cancellation/ownership loss was acknowledged before that commit. It must cover cancel, detach, expiry, revocation and drain without granting renewed authority. Already-started external work may still record legitimate cleanup/settlement; that is distinct from accepting new assistant answer content after cancellation.

The reviewed ownership design says not to hold the admission mutex while doing I/O. Holding `owners.lock` around all SQLite work would conflict with that policy and could obstruct bounded lifecycle handling. Alternatively introducing a commit reservation/barrier, changing cancellation acknowledgement ordering, or placing owner-aware checks at the Store transaction boundary changes the reviewed ownership/persistence contract; Store changes are outside this correction's permitted scope. No such change was silently made.

**Minimum proposed review:** define a TEST-only response commit boundary in the existing gated App/Stage 4 ownership runtime. Specify cancellation-before-commit refusal, commit-already-in-progress acknowledgement/outcome, bounded waiting, no new tool step, atomic event/persistence outcome and behavior under database failure. Prefer no Store/schema change. Review the exact locking/deadline contract before implementing it. Likely existing file scope: gated `server.py`, `stage4_runtime.py`, `stage4_sessions.py` and existing Stage 4 fixtures/tests; any `stage4_lifecycle.py`, Store or schema change needs its own explicit justification. No new route, provider or approval/upload functionality is necessary or proposed.

## Acceptance status at this stop

| Gate / requirement | Evidence status |
|---|---|
| Event polling | **FAIL**, one reproduced in-scope late-write violation; other unexecuted polling races remain incomplete |
| Authenticated TEST approvals | **DEFERRED**, exact user-approved exclusion above; not PASS |
| Authenticated TEST uploads | **DEFERRED**, exact user-approved exclusion above; not PASS |
| Controller reauth/lifecycle-only recovery | Prior **PASS**, runtime/session sources unchanged; this fixture-only addition is not a new recovery implementation |
| Inspection/archive cleanup | Prior **PASS**, no related implementation changed |
| Synthetic repair cleanup/accounting | Prior **PASS**, no related implementation changed |
| Demonstrated Electron attach/close/reopen and known-work deadline/emergency paths | Prior **PASS** only for their documented scope; not rerun in this failing checkpoint |
| Full real-Core restart/crash/race gate | Still OPEN/PARTIAL, **not run here**; no fabricated functional FAIL or PASS |
| Full shared-state/restart/presence gate | Still OPEN/PARTIAL, **not run here** |
| Adapter media/watchdog gate | Still OPEN/PARTIAL, **not run here**; physical media separately deferred |
| Human-operated isolated lifecycle review | Still OPEN/PARTIAL, **not performed here** |
| Overall Stage 4 acceptance | **FAIL / INCOMPLETE**, event polling violates the contract and other in-scope evidence remains outstanding |

PASS/FAIL/DEFERRED are not interchangeable with NOT RUN. Unexecuted gates cannot honestly receive a new test verdict. The full Stage 4 acceptance suite and Stage 1–3/Python/desktop regressions were **not rerun** after this conflict: the explicit instruction to STOP before broadening the architecture takes precedence over continuing a suite toward acceptance. No acceptance commit was created.

## Correction validation and rollback plan

After review, retain this original failed source/result and rerun the control plus the same cancelled boundary. Add deterministic cancellation on both sides of the agreed commit point; detach/expiry/drain variants; foreign read/control denial; terminal event/provenance/database consistency; duplicate/pending polls; no old authority on reconnect; database failure/deadline cleanup. Then execute the complete required Stage 4 suite and directly affected regressions, reporting each gate against final hashes. Do not call a finite interleaving test proof of all possible schedules.

Current rollback needs only restoration of `tests/lifecycle_stage4/fixtures.py` from `before/` after checking for subsequent edits, or reversing `fixture.diff`. Do not restore any database or remove the failure artifacts. This removes the observation fixture, not a runtime fix; runtime source remained unchanged. Python compilation of the changed fixture passed. Source snapshots, exact diff, independent counts, raw failure output and selected nonsecret runtime metadata/journals are retained and hashed. Runtime TEST data stays local and is excluded from the record copy.

PRODUCTION BEHAVIOR CHANGED: NO  
PRODUCTION DATABASE MODIFIED: NO  
PRODUCTION CORE RESTARTED: NO  
RUNTIME CORRECTION IMPLEMENTED: NO  
ACCEPTANCE COMMIT CREATED: NO  
STAGE 5 STARTED: NO

**STOP FOR REVIEW.**
