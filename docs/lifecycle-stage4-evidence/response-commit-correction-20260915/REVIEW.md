# Shared TEST response commit boundary — implementation / validation review

2026-09-15. **PARTIAL — STOPPED FOR REVIEW.**

The approved correction is implemented. Targeted persistence and cancellation validation passed, including 918 final race trials and two actual authenticated event-polling probes. The wider regression run then failed at Electron startup, before client attachment. The user's Stage4 acceptance-failure stop condition was observed: no further runtime edits or tests followed that failure. No acceptance commit, production activation or Stage5 occurred.

The narrow invariant is demonstrated by the recorded tests. **The correction's overall acceptance remains PARTIAL**, pending review of the Electron failure and completion of the remaining final-source regression steps. This is not a declaration that Stage4 is complete.

## Root cause and implemented boundary

The original actual-App probe acknowledged cancellation between `App.work`'s in-memory check and `Store.message`'s separate INSERT transaction. The message then committed; only afterward did the Stage4 completion/provenance hook reject ownership. An assistant row survived despite failed polling state. The original failure package remains unchanged at `docs/lifecycle-stage4-evidence/event-polling-20260915/`.

The correction reserves normal-chat response provenance before dispatch and routes **normal chat, explicit text-only fallback and deep review** through `Context.finish_response` / `Context.settle_response` and `History.finish`. All finalization and cancellation decisions now use `BEGIN IMMEDIATE` in the existing canonical TEST SQLite database. The existing provenance table is reused; no table/column or production schema migration was added.

Within that transaction, History checks the response owner and original session family and reads the durable status. Only PENDING can become a new final result. For normal completion, the real Store message INSERT participates in this same transaction and its row ID is recorded in provenance alongside immutable run/work IDs. Any exception rolls back both writes. Final events are emitted only after the transaction returns successfully.

- **Cancellation wins:** PENDING becomes CANCELLED, with no final answer text or successful provider/model attribution. A later completion reads CANCELLED and cannot insert an assistant row or change that terminal record.
- **Completion wins:** the answer and provenance remain COMPLETED. Later cancellation cannot overwrite them. The original worker result is retained separately; RPC cancellation now adds `response_status`, and polling adds `response_status` and `worker_outcome`. A response may already be committed while its worker is still active.
- **Repeated/late callbacks:** terminal provenance is immutable. Publishing is idempotent per run; repeated cancellation or completion cannot create another response or contradictory response terminal event.

Owner loss through detach/revocation and cancellation through emergency/drain flush response cancellations outside the owners mutex before successful acknowledgement. Expiry detected during authenticated dispatch is also flushed in the dispatcher boundary; the lifecycle tick flushes cancellation state. These are trusted callbacks, not renderer-supplied authority. Reattachment cannot acquire the old Work/session family.

SQLite waits use at most the existing one-second History timeout, capped by the remaining lifecycle deadline. There are no added retries or sleeps in runtime. No response seal can execute while the global owners mutex is held; a fail-closed lock-order check enforces that rule. Completion holds the SQLite transaction while briefly checking existing Work authority, never the global mutex while waiting for SQLite. Cancellation signals under the mutex, releases it, then enters SQLite. This avoids the opposing lock order. Providers/tools/worker joins are outside this transaction.

A persistence exception marks `RESPONSE_PERSISTENCE_UNCERTAIN` and invokes existing retained-ownership recovery. Cancellation does not change UNKNOWN work to a known outcome, imply worker cleanup, or refund resources. The file-based operation journal remains separate from SQLite: this correction does not claim an atomic database-plus-journal commit. Fresh-process recovery of a committed response with an interrupted journal still requires the existing conservative recovery rules; final-source restart reruns remain outstanding at this stop.

## Exact Store interface change

`Store.message(conversation, role, content, *, transaction=None)` gains one opt-in argument. With a transaction, it requires an active SQLite connection, the TEST application ID and the same database path as the Store, executes its existing INSERT, returns the inserted row ID, and leaves commit/rollback to the caller. Without the argument, the pre-existing production call behavior remains unchanged, including its separate connection and return behavior.

No broader Store refactoring, schema migration, new Store or alternate Core was introduced. Shared source files `server.py` and `store.py` changed within the approved interface/gating scope; production processes, data, configuration and default behavior were not changed or activated by this work.

## Files changed

Source and test changes are exactly:

1. `store.py` — opt-in TEST transaction participation.
2. `server.py` — existing Stage4 gate delegates final persistence/events to the shared boundary; ordinary production branch retained.
3. `stage4_response_history.py` — single conditional SQLite finalization transaction, immutable terminal records, optional Store INSERT/owner validation.
4. `stage4_runtime.py` — early normal reservation, immutable bindings, shared finalization/cancellation flush, truthful response-versus-worker status.
5. `stage4_sessions.py` — trusted cancellation flush after releasing the ownership lock and before acknowledgement.
6. `stage4_lifecycle.py` — cancellation sealing at worker/lifecycle boundaries without changing work outcome or shutdown ownership.
7. `stage4_deep_review.py` — use the same finalization path; provider/model/tools/budgets unchanged.
8. `tests/lifecycle_stage4/fixtures.py` — retain the original authenticated persistence assertions, placing its observer before the newly introduced transaction.
9. `tests/lifecycle_stage4/test_stage4.py` — repeated actual-App/Store transaction tests and direct SQLite checks.

Before/current snapshots, exact hunks and SHA-256 values are in `before/`, `current/`, `source-changes.diff` and `source-hashes.json`. Three other reviewed integration/test files are unchanged and recorded by hash. The two Stage4 status documents have documentation-only pointers to this report. Nothing was committed.

## Targeted validation and scheduling evidence

Final-source driver runs `response-races-04`, `05`, `06` each executed 306 trials and 4,748 assertions successfully, with zero remaining worker threads. Combined: **918 trials, 14,244 assertions**.

| Mode | Cancellation-first | Commit-first | Concurrent release |
|---|---:|---:|---:|
| Normal chat | 102 CANCELLED | 102 COMPLETED | 102 CANCELLED |
| Text-only fallback | 102 CANCELLED | 102 COMPLETED | 102 CANCELLED |
| Deep review | 102 CANCELLED | 102 COMPLETED | 102 CANCELLED |

Both legal outcomes were exercised with bounded observers around the actual transaction. The concurrent-release trials all selected cancellation on this host; this is reported as measured and is **not** evidence of a natural timing distribution or a claim that completion cannot win under concurrency. No runtime scheduling delay or provider behavior was added to force success.

These tests use one actual isolated App/Store and the trusted authenticated dispatcher seam in each separate test process, with offline providers. They are not substitutes for named-pipe authentication or Electron evidence. The actual pipe probe below supplies that complementary proof.

Each final trial checked acknowledged status against direct read-only SQLite queries and owner polling, per-run/work/response association, exactly zero or one assistant rows/events as appropriate, one terminal response event, retained provider attribution for completed answers, repeated cancellation, and a subsequent late/duplicate completion callback. Commit-first cases paused after the actual commit while the worker remained active and verified separate cleanup status. All normal-chat completed rows matched their provenance text and message ID.

Additional checks covered a deliberately injected exception after the real Store INSERT but before transaction completion (both message and provenance rolled back), wrong owner/family transaction denial, disconnect during the actual provider-generation call, stale/fresh family denial of the disconnected Work, history-object reopen, drain racing a pending final response and admission denial during drain. The injected transaction exception is an expected negative-test result, not an erased failed acceptance run.

The original authenticated command was rerun twice:

```
.venv\Scripts\python.exe -B tests/lifecycle_stage4/fixtures.py --real-app-event-polling
```

Both runs passed **43 checks**, exited normally and released their TEST lifetime lock only after exit. Result IDs: `57fb045aacf346118d593ef393ae1ae2` and `db7b935423e24f5bad2d40c8faa04ae5`. Independent read-only SQLite inspection after each Core exited found three completed assistant rows, one cancelled response with no answer, zero orphan rows and zero duplicate message links. In both cancelled scenarios the count stayed **3 → 3**, replacing the old failed observation **3 → 4**. See `independent-sqlite-verification.json`.

The old observer paused inside `Store.message` before it opened its own transaction. The new caller now owns that transaction; pausing inside Store would instead hold an already-acquired SQLite writer lock. The observer therefore now pauses before the common transaction entry, preserving the same cancel-before-write ordering and original assertion. Separate commit-first tests exercise the other ordering. The original driver/source/failure are retained for comparison.

## Regressions executed

All commands ran against the current corrected source. Exact output and evidence paths are preserved in the named logs and `evidence-references.json`.

| Suite / scenario | Result |
|---|---|
| Stage1 unchanged | 23 passed, 1 existing skip |
| Stage2 unchanged | 35 passed, 1 existing skip |
| Stage3 unchanged | 43 passed |
| Stage4 ownership / controller recovery | 27 / 52 passed |
| Inspection workers / repair workers / loop audit | 13 / 22 / 16 passed |
| Existing Python suite | Final 212 passed with isolated history fixture; earlier guarded run: 211 passed, 1 error retained |
| Desktop + Intelligence unit tests | 29 passed |
| Offline provider/router/transport/deep-review unit tests | 62 passed |
| Actual fallback App integration | 12 passed |
| Native identity / bootstrap | 15 / 6 passed |
| Actual normal / emergency / deadline / controller expiry | 29 / 32 / 36 / 45 passed |
| Actual inspection cancel / detach / emergency | 43 / 43 / 44 passed |
| Actual synthetic repair cancel / detach / emergency / drain | 44 / 45 / 45 / 46 passed |
| Actual authenticated event polling | 43 passed twice |
| Actual Electron lifecycle | **FAIL at startup:** one reconciliation check passed; client exited before attachment; no screenshots |

The actual deadline run retained an active/unknown worker under Core ownership until safe completion; response cancellation did not clear UNKNOWN or bypass the deadline/recovery contract. All actual-Core fixture processes, including the failed Electron run's Core, exited normally. No forced termination was performed.

Stage1–3 commands were `python -B tests/lifecycle_stageN/test_stageN.py`. Focused Stage4 commands used `test_stage4.py` with `--ownership-tests`, `--controller-recovery-tests`, `--inspection-tests`, `--repair-tests`, `--repair-loop-audit` and `--response-commit-tests --response-rounds 34`. Actual scenarios used the matching `fixtures.py --real-app-*` switches named by each log; native/bootstrap/Electron used `--native-probe`, `--bootstrap-probe`, `--electron-app-probe`. Offline provider unit command: `python -B -m unittest discover -s tests -p 'test_stage4*.py'`. Desktop used Node `--test` with the enumerated `desktop/test/*.test.cjs` and `intelligence/test/*.test.cjs` files.

The Python 212-test suite used `unittest` discovery of root `test_*.py` with a disposable-process guard: the real `.env` read returns empty without opening it, inherited secret environment entries are removed, production data/source writes and remote socket calls are denied. One legacy test calls `development.history(ROOT)` even though its App is temporary. The guard blocked the production metadata read. The final rerun redirected only that canonical-root history call to an empty temporary `data/development` fixture, still executing the real `development.history` implementation and unchanged assertions. Other callers retain their supplied fixture root. No test file or production history was altered to get that pass.

## Electron failure and stop

Preserved result: `results/electron-app-probe-2f8a9d94206e48b4a59082b328539567.json`; stderr: `results/electron-failed-stderr.txt`.

Electron's launcher reported exit **2147483651 / 0x80000003**. Stderr records an encryption warning, then six GPU-process exits with code **-1073741515**, followed by **“GPU process isn't usable. Goodbye.”** The first client never completed attachment; the second client was not started and no screenshots were captured. The disposable Core exited with code 0.

This establishes the observed startup failure stage, not its underlying cause. No missing library, security setting, GPU configuration, response-commit regression or connection to a historical crash is established by this record. No flags, security settings, desktop code or production behavior were changed to bypass it. No rerun followed the failure.

Fresh-process fallback provenance/restart, the dedicated deep-review integration/restart rerun, and standalone final JS/Python syntax-validation commands were not run after this stop. Earlier syntax parsing and actual execution are recorded, but are not substituted for those unexecuted final checks. Existing broader Stage4 restart/shared-state/media/manual gates remain governed by the acceptance matrix.

## Preserved transitional / failed evidence

- Original pre-correction late-write failure remains intact in its own package.
- `response-races-01.log`: missing repository import path in the new driver; failed before App construction.
- `response-races-02.log` and its JSON: 34 cancellation-first trials passed, then the test observer accidentally held publication of an older terminal run. Zero remaining workers. The observer was restricted to the active, not-yet-published completion; no invariant/assertion was weakened.
- `response-races-03`: 306 passing transitional trials before the driver was strengthened to hold actual provider generation for the disconnect check. Final counts use only runs 04–06.
- `python-regression.log`: the blocked production-history read described above; final passing rerun does not erase it.
- `electron-app-probe.log`, result JSON and stderr: current failed acceptance evidence; still unresolved.
- A development editing-script assertion before writing the deep-review edit is recorded in `pretest-static.json`; it did not execute runtime code.

## Acceptance disposition and limits

| Requirement | Status |
|---|---|
| Shared cancellation/completion transaction invariant, normal message/provenance atomicity | **PASS — targeted evidence** |
| Owner/session denial, late/duplicate finalization, truthful commit-first history | **PASS — targeted evidence** |
| Disconnect/reconnect, admission/drain, UNKNOWN retention within recorded scenarios | **PASS — recorded scope** |
| Final-source provenance recovery across a fresh process | **PARTIAL — history reopen passed; planned restart reruns not completed** |
| Actual Electron final-source lifecycle regression | **FAIL — startup blocked before attachment** |
| Correction acceptance / event-polling gate closure | **PARTIAL — do not close until failed/pending acceptance evidence is reviewed** |
| Authenticated TEST approvals | **DEFERRED — WORKFLOW NOT PRESENT IN CURRENT STAGE 4 PRODUCT SURFACE** |
| Authenticated TEST uploads | **DEFERRED — REQUIRES SEPARATE AUTHORITY / PERSISTENCE REVIEW** |
| Overall Stage4 | **INCOMPLETE / STOPPED FOR REVIEW** |

The historical Stage1 PermissionError remains ROOT CAUSE UNCONFIRMED / FAIL-SAFE / REVIEW REQUIRED. Its later reproduced mechanisms remain separate. Existing cross-session skips and physical-media limitations were not silently converted into passes. Cancellation/timeout remains potentially resource-consuming; universal monetary enforcement is not claimed.

## Rollback and boundaries

Rollback is source-only and TEST-only: verify affected current files still match `source-hashes.json`, then restore only the nine changed files from this package's captured `before/` versions, or reverse only `source-changes.diff` after review. Those versions include pre-existing unrelated working-tree changes. If hashes differ, reconcile the new changes rather than overwrite them. Never reset the repository to HEAD.

Rolling back restores the known TEST late-write defect, so keep that runtime paused. Retain all TEST databases, journals and failed evidence; do not erase committed rows to make a comparison pass. No schema/data rollback or production migration is required or authorized.

**Production database moved/modified: NO. Production Core restarted: NO. Production configuration changed: NO. Production activation: NO. Acceptance commit: NONE. Stage5: NOT STARTED.** Shared TEST-gated source/interface edits are explicitly listed above, not concealed as “no files changed.”

Next review concerns the preserved Electron startup failure and authorization to resume the remaining final-source validation after its disposition. No additional implementation is proposed or performed in this stop.
