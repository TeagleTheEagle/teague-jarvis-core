# Canonical Core Stage 4 — final campaign review boundary

2026-09-15. **Campaign stopped at a genuine new review boundary. Gate 2: PARTIAL. Stage 4: NOT READY FOR OWNER ACCEPTANCE.**

The approved campaign was resumed with read-only inspection of the current acceptance matrix, ownership/drain design and actual TEST startup/control implementations. No Core/client was launched, no runtime test or regression was run, and no process was terminated. The previous interrupted turn consisted of completed read-only commands; it launched no TEST runtime requiring cleanup.

## Exact blocker

The required **authorized restart of a stopped Core is not implemented in the current Stage 4 TEST composition**. This is a source-established integration gap, not an observed runtime crash, race failure or regression of the closed response-commit boundary.

The approved design requires a separately authorized start transaction under supervisor exclusion, verified Core absence and acceptable recovery state (`CANONICAL-CORE-STAGE-4-OWNERSHIP-DRAIN-DESIGN.md:88–92`). Current code correctly leaves a stop latch and refuses ordinary startup, but provides no transaction to authorize and reconcile the transition from that stopped state to a new Core.

| Evidence in current source | What it establishes |
|---|---|
| `stage4_runtime.py:662–674`, `Authority._operation` | Authenticated shutdown/emergency writes and flushes the TEST `stop` latch. Only those lifecycle actions are dispatched; unsupported operations are denied. |
| `stage4_runtime.py:678–694`, `serve` | Startup requires absence of `stop` before acquiring the Core lifetime lock or constructing the App. A direct relaunch of a stopped namespace is rejected as `STOP_LATCH`. This is source behavior, not a new executed relaunch test. |
| `stage4_sessions.py:255–266`, `management_capability` | Existing Core-issued management capabilities accept only `shutdown` and `emergency-stop`. They are not an offline start/restart authorization mechanism. |
| `tests/lifecycle_stage4/fixtures.py:351–364`, `controller_action` | The existing explicit controller surface supports REAUTH, RECOVER, STATUS and SHUTDOWN. RECOVER reattaches to the same surviving Core; it does not start a stopped/dead Core. |
| `tests/lifecycle_stage4/fixtures.py:406–454` and `:492–493` | The real App probe provisions a fresh namespace, takes supervisor exclusion, checks Core-lock absence and starts the child. Later it reconciles a surviving Core. It does not implement authorized start-after-stop or recover a dead Core's retained startup intent. |
| `tests/lifecycle_stage1/harness.py:188–226` | Stage 1's coordinator returns STOPPED for a stop latch and RECOVERY_REQUIRED for retained intent without a live owner. Its spawn target is the Stage 1 no-App test Core, not the real Stage 4 App. Substituting its passing races would not prove the composed Stage 4 requirement. |
| `tests/lifecycle_stage2/bootstrap.py:50–80` | Stage 2 recognizes lifecycle operation names for authentication testing but explicitly returns `lifecycle_executed: false`. That is not an implemented Stage 4 restart route. |
| `stage4_runtime.py:163–170`, `stage4_lifecycle.py:48–65` | Prior unresolved journal records block open-existing startup. This preserves fail-closed recovery; no authority to replay, refund, clear UNKNOWN or repair journal records is implied. |

Exact numbered source excerpts and SHA-256 hashes are in [source-evidence.json](source-evidence.json). [static-inspection.json](static-inspection.json) records an AST-only enumeration of the actual Stage 4 dispatcher: 23 explicit operation names, no start/restart branch. The source search also located the real fixture controller; a guessed `stage4_controller.py` path did not exist. No module was imported by the static inspection.

This does **not** prove an unsafe automatic restart or duplicate Core occurred. It establishes that the positive authorized stop/start requirement cannot currently be exercised through the reviewed actual lifecycle path. Crash/restart and repeated real-App startup-contender evidence also cannot be replaced by direct Context constructors, by deleting a latch, or by the Stage 1 no-App harness.

## Why this requires review

The latest authorization permits continuous validation and previously reviewed corrections, but requires an immediate stop for a new architectural design or broader authority. Implementing a stopped-Core start transaction introduces a lifecycle authorization consumer outside the live Core, a durable stop/start transition and recovery handling for a launch whose outcome may be uncertain. None of the already reviewed response-commit, controller reauthentication or IPC guard corrections implements that missing transaction.

The general architectural direction already approves a coordinator. The **specific implementation/authority transition needed here has not been reviewed as a correction**. This is not a request to reapprove routine tests or to reopen a closed gate.

## Minimum proposed addition — not implemented

Add one bounded **TEST-only coordinator start/restart transaction**, using the existing trusted TEST parent/controller credential boundary and Stage 1/2 verification primitives. The coordinator must not construct App/Store, own providers/voice, or grant ordinary clients lifecycle authority.

1. Require a fresh explicit owner action for start/restart, bound to the exact TEST namespace/data identity, prior Core epoch where applicable, operation ID and short expiry. Consume its one-use authorization durably; repeated invocation returns the existing operation outcome. A historic Core session token cannot authorize a new epoch.
2. Under `supervisor.lock`, verify Core absence using the real lifetime lock and live process identity. If a valid Core survives, reconcile and authenticate/adopt it. Uncertain identity or uncertain launch outcome yields RECOVERY_REQUIRED with no replacement spawn.
3. Inspect the durable stop/start intent and existing journal/data identity. UNKNOWN/interrupted/corrupt state remains blocked where the accepted contract requires it. Do not replay work, refund uncertain reservations or treat journal history as executable authority.
4. Record the explicit start intent before transitioning the stop latch. Retire a previous stop latch **only within the reviewed authorized transaction**, retaining its history. Define crash behavior for every partial transition; no opportunistic deletion or retry loop. An ambiguous partial transition must not permit another spawn.
5. Start one existing Stage 4 Core child under supervisor exclusion. Verify the new process creation/executable identity, new epoch, same canonical TEST data, Stage 1 reconciliation and Stage 2 authenticated identity before recording success or admitting clients. Keep lifetime ownership in the Core until OS exit.
6. Give clients fresh authentication according to the reviewed TEST enrollment policy. Do not restore old sessions, request authority, leases or live presence. Do not give renderer code management credentials or a restart API.

The exact durable intent format and interrupted latch-transition ordering need review before implementation. The proposal uses isolated TEST artifacts, not a production Store/schema migration, service or production credential change. If implementing it requires further authority or modules, return for review again.

### Proposed file scope

| File | Proposed delta |
|---|---|
| `stage4_runtime.py` | Narrow TEST coordinator/control entry and startup-transaction validation around the existing `serve` composition. No change to response-commit methods, providers or ordinary request authority. |
| `tests/lifecycle_stage4/fixtures.py` | Trusted TEST owner/controller invocation and actual multi-process coordinator/start/restart/crash fixtures; private bootstrap material stays outside evidence. |
| `tests/lifecycle_stage4/test_stage4.py` | Focused transaction/denial/recovery tests and repeated real-process campaign assertions. |
| `docs/CANONICAL-CORE-STAGE-4.md`, `docs/lifecycle-stage4-evidence/`, `docs/STAGE4-REMAINING-REQUIREMENTS-20260915.md` | Reviewed design delta, exact test/evidence records, hashes and status reconciliation. |

No Stage 1/2/3 semantics, production launchers, Electron behavior, Store/schema, response-commit logic or hardware/provider authority is proposed for change. Existing unresolved-journal refusal should be reused, not weakened.

## Validation after review — NOT RUN

- Actual authorized stop: persistent stop intent, verified Core exit/lock release and no automatic restart. Ordinary/stale/expired/duplicate start authorization denial must be demonstrated separately.
- Explicit restart: same TEST data identity, new process/epoch, immutable persistent records, old sessions/grants/work authority denied, fresh client authentication and fresh presence.
- At least **four rounds of eight simultaneous actual startup contenders**; record all process identities, winners/losers, lifetime-lock observations, adoption/authentication and clean exit. No Stage 1-only substitute.
- At least **three coordinator-loss/adoption rounds** and **three Core-crash/recovery rounds** using reviewed disposable crash fixtures. Reverify process identity before any targeted action. Do not terminate unrelated processes or improvise forced cleanup.
- Interrupt the start/stop intent transition at the reviewed boundaries. Prove either one authenticated Core or a fail-closed recovery state; never an unaccounted second owner. Unknown work/charges remain conservative and non-runnable.
- Compare actual SQLite integrity and canonical records before/after; distinguish durable history from invalidated transient authority. Verify both actual clients across Core epochs where required, not only direct Context construction.
- Run affected lifecycle/startup/authentication tests, then the required final Stage 1–4/Python/desktop checks against the reviewed final source. Preserve every failure. Closed response-commit tests are not changed merely to accommodate startup work.

Remaining media/manual/shared-state acceptance work can continue after this review boundary is resolved. Approvals remain DEFERRED — workflow absent; uploads remain DEFERRED — separate authority/persistence review. The campaign wording “where still applicable” does not silently implement or count those excluded capabilities as passed.

## Evidence, limitations and rollback

[frozen-source-verification.json](frozen-source-verification.json) confirms all **26** source/executable paths still match the final reviewed response-commit checkpoint. [source-revision.json](source-revision.json) records HEAD `8f0b9bce181800f9339249c4024e396246e94208` plus working-source hashes; HEAD alone does not represent the existing uncommitted Stage 4 implementation. Current matrix and chronological report hashes are recorded without editing them.

This campaign performed **read-only source/design inspection only**. No runtime tests, crash injections, startup races or regressions were executed after the boundary was identified. There are no new process identities/epochs or cleanup results to claim. No new race/runtime failure was produced. Search-path errors were not runtime failures. All prior failed runs and classifications remain untouched, including the historical Stage 1 PermissionError and restricted-context Electron GPU finding (exact DLL/root cause still unconfirmed).

Production preservation rests on the bounded operations actually performed: no production database was opened, no runtime configuration changed, no production process launched/restarted/terminated, and no frozen source edited. This is not a new claim of byte-for-byte quiescence of a concurrently running production database. No live process inventory or provider call was needed.

Only this new nonsecret diagnostic package was written. It contains source excerpts, read-only inspection results, source hashes, this review and a manifest. No DB, session token, private challenge, profile, key or provider secret is copied. Archive copies are hash-verified separately.

There is no runtime/data rollback needed for this checkpoint. Preserve the evidence. For the proposed implementation, snapshot affected source first, retain all TEST state and failed intents, and reverse only reviewed source hunks after verified TEST exit; never restore older databases or remove recovery records to make startup pass.

**Requested review scope:** approve the bounded TEST-only coordinator start/restart transaction and its one-use owner authorization, durable stop/intent transition and fail-closed recovery behavior, limited to the files above, followed by the actual process matrix and remaining already approved Stage 4 campaign. No implementation has begun.

RESPONSE-COMMIT GATE: CLOSED, UNCHANGED  
STOP/START/CRASH/RACE GATE: PARTIAL  
STAGE 4 READY FOR OWNER ACCEPTANCE: NO  
PRODUCTION CHANGED / RESTARTED: NO  
ACCEPTANCE COMMIT: NONE  
STAGE 5: NOT STARTED
