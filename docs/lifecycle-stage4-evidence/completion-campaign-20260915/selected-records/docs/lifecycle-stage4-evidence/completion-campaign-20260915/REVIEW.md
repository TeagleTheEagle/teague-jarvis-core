# CANONICAL JARVIS CORE — COMPLETION AND CUTOVER REVIEW

2026-09-15 working-source checkpoint. **Stage 4 automated requirements PASS; required human lifecycle result OPEN. Stage 5 has not started. Production cutover and release are not complete.**

The [single completion checklist](../../CORE-COMPLETION-CHECKLIST.md) controls current programme status. The latest completion mission supersedes old stop-after-each-gate wording and conditionally authorizes Stage 5 after all required Stage 4 evidence. Approvals/uploads and physical media retain their explicit exclusions. They are not counted as passing.

## Stage 4 result

The bounded TEST coordinator now implements explicit start/restart. Ordinary startup refuses a retained stop latch. A separate authenticated native controller obtains a one-use grant bound to its live process, session, coordinator instance, TEST namespace/data identity, prior Core epoch and exact stop-state fingerprint. Grant validity is at most 30 seconds; launch validity is 15 seconds; the disposable coordinator session/server is bounded to 120 seconds. The Core holds its own lifetime lock and outlives the coordinator.

The coordinator obtains `supervisor.lock`, proves Core absence through the existing Windows lifetime lock and process creation identity, inspects prior journals and consumed intents, and exclusively creates/fsyncs an immutable intent before spawning. The child claims that intent under `core.lock` before App/Store construction. The coordinator then reconciles Stage 1 identity and verifies Stage 2 authenticated pipe identity before writing the durable verified record that opens ordinary admission. No file existence is substituted for lifetime ownership. No lock, stop latch or failed intent is deleted to force recovery.

Replacement coordinators may finish verification/adopt a surviving claimed Core. They cannot spawn a second Core for an ambiguous consumed intent. Interruption before intent leaves no consumed authority; after intent with no verified survivor fails closed. The stop marker is retained and reconciled only through the explicit transaction. Expired/replayed/foreign grants and changed configuration/stop state are rejected. A publication failure is not recorded as a successful claim. UNKNOWN journal work remains blocking; uncertain budget holds are neither refunded nor replayed.

The shared response-commit transaction is unchanged. [Method comparison](closed-boundary-method-verification.json) confirms only `Context.shared_state` and the reviewed outer `Authority._operation` dispatch changed among prior runtime methods. The approved startup composition changes are separate from cancellation/completion serialization. No Store, schema, provider, personality, VoiceEngine, WakeDetector, Stage 1–3 algorithm, launcher or production configuration change was made in this campaign.

The TEST shared-read response now uses existing Store/workspace/device readers for projects, tasks, conservative budget snapshots and fresh presence. It adds no write route or action authority. The TEST media reply includes relative remaining validity so Electron never compares unrelated clock origins.

Both actual Electron adapters use a client-local modeled-media watchdog. It bounds a grant by the request's start time plus Core-supplied remaining validity (at most ten seconds), renews after three seconds only while explicitly active, stops on expiry/denial/transport loss/close, and rejects stale callbacks by generation and deadline. Stop capture, stop playback and request cancellation remain separate. No automatic grant reacquisition, hardware capture, browser TTS, new provider or consequential operation was enabled. An unresponsive/malicious OS process is not claimed to be physically controllable by this software timer.

## Executed evidence

Exact commands, exit codes, PIDs, elapsed times and logs are in `regressions-175914.json` and `regressions-180332.json`. Source/executable hashes are in [final-source-hashes.json](final-source-hashes.json); function binding is recorded separately. HEAD remains `8f0b9bce181800f9339249c4024e396246e94208`; this dirty working-source checkpoint is not represented by HEAD alone and is not an acceptance commit.

| Validation | Actual result / evidence |
|---|---|
| Real restart campaign | **636 checks PASS**: [per-case identities and outcomes](../restart-campaign-5a9ac2730cbe4c1da318e710793af901.json). Four rounds of eight actual contenders, three coordinator-loss/adoption rounds, three Core-crash/recovery rounds, additional interrupted boundaries, explicit stop/restart, stale session/enrollment rejection, no restored grants/presence, conservative budget preservation. |
| Focused durable start negatives | **10/10 PASS**, [log](../restart-transaction-20260915/transaction-negative-01.log): claim once, failed/partial publication, expiry, wrong data/nonce/configuration, changed stop state, path escape, unverified intent and wrong verified peer. No App is constructed by these focused record tests. |
| Actual Electron state/media/restart | Final **74 checks PASS**, [result](../client-state-media-a9cbccc28f354831aee61a48f2d2727d.json). Both clients read same canonical projects/tasks/budgets, completed work remains historical, local controls preserve shared settings, disconnect removes only its presence, renderer crash retains Core, explicit fresh-epoch reattachment has no stale work/media, owner emergency revokes modeled media. Earlier 68-check passing run retained, not added to final total. |
| Actual Electron existing lifecycle regression | **29/29 PASS**, [result](../electron-app-probe-6425a1f8fb814e4b83ed6c48250ec55a.json), approved host context, Electron **44.2.0**. Both applications attach, close/reopen/crash correctly; ordinary renderer/native/network boundaries checked. |
| Client watchdog focused tests | **19/19** in its desktop file (includes six new watchdog cases); complete desktop + Intelligence suite **35/35 PASS**. These are overlapping suites, not 54 independent tests. |
| Stage 1 / Stage 2 / Stage 3 | **23 pass + 1 existing skip / 35 pass + 1 existing skip / 43 pass**. Accepted source unchanged. |
| Stage 4 ownership / controller recovery | **27 / 52 PASS**. |
| Inspection workers / repair workers / loop audit | **13 / 22 / 16 PASS**. Synthetic repair; no real repair execution. |
| Shared response-commit regression | **306 trials / 4,748 assertions**, no failures or live workers. Ordered controls exercise both legal orderings; repeated simultaneous schedules exercised cancellation/commit serialization. Earlier 918-trial acceptance remains preserved; do not add it to this run's count. |
| Broad Python / offline providers | **212 / 62 PASS**. Disposable guard blocks production files/credentials and permits only loopback sockets bound by that same test process. No paid calls. |
| Native identity / bootstrap | **15 / 6 PASS**. |
| Actual normal / emergency / deadline / controller-expiry | **29 / 32 / 36 / 45 PASS**. Deadline scenario retains ownership for UNKNOWN work; no guessed completion. |
| Actual inspection cancel / detach / emergency | **43 / 43 / 44 PASS**. |
| Actual synthetic repair cancel / detach / emergency / drain | **44 / 45 / 45 / 46 PASS**. |
| Actual event polling | **43 PASS**; persistence checked independently. |
| Fallback / Deep Review integration / authenticated Deep Review pipe | **12 / 14 / 8 PASS** using existing offline mechanisms. No paid or live-model performance claim. |
| Standalone syntax | **13 Python + 6 JavaScript files PASS**; exact files/commands in [syntax record](standalone-syntax.json). Parsing is not runtime validation. |

The final client-state/media screenshots were inspected: both visibly identify authenticated STAGE4_TEST attachment and physical media as unavailable. Intelligence's lower controls extend beyond the viewport; the existing scrollable layout is unchanged and is not relabeled a physical-media PASS. No GPU flag or Electron runtime correction was introduced. The existing TEST launch settings were preserved.

The [47 original requirements plus later scope decisions](requirement-to-evidence.json) have individual dispositions and evidence references. Supported request/event workflows remain in scope. Approval and upload workflows are explicitly DEFERRED, never inferred from unsupported-operation denial.

## Independent state and cleanup verification

[Independent SQLite inspection](independent-sqlite-final.json) opened **36 selected TEST databases read-only** after their fixture exits. Initialized response stores had no orphan assistant messages, orphan successful provenance, contradictory failed/cancelled success attribution or duplicate message references. Databases provisioned before failed startup are identified separately rather than counted as response-path executions. Integrity/application identity checks and canonical table hashes are retained. The full restart campaign compared every application table, including settings, project/task links, reservations and recovery outcomes before/after restart.

[Cleanup verification](process-cleanup-final.json) checked **170 recorded process identities**, including PID/creation/executable evidence where supplied: none remained the same live process. PID reuse was not treated as termination authority. All actual client/Core scenarios exited through their approved fixture crash or authenticated graceful cleanup. No forced termination or historical-PID cleanup was performed. This is recorded finite-run coverage, not a claim about every unrelated process on Windows.

[Source verification](final-source-hashes.json) confirms **22 protected source/executable paths unchanged** from the preceding response-commit checkpoint. Existing response-commit, Core identity/authentication primitives, production source/configuration/launcher branches remain intact. The production database was not opened or hashed; a running production database is not claimed byte-for-byte quiescent. No production Core was started, restarted, stopped or migrated.

## Preserved failures and limitations

- Restart smoke 1 stopped before a Core spawn because the Windows venv redirector PID differed from the actual native interpreter identity. The exact-identity test was preserved. The TEST child launcher now directly starts the known native interpreter with only fixed venv import paths; identity checking was not weakened. The discarded coordinator exited on its own bounded lifecycle.
- Restart smoke 2 consumed its grant but failed before App construction: configuration fingerprinting encountered enrollment bytes after the existing key-decoding step. The traceback and source remain retained. A JSON clone before decoding now binds the same original trusted configuration. The child exited, the coordinator reported RECOVERY_REQUIRED, and its intent was not silently cleared. Smoke 3 and the full campaign are separate passing records.
- Broad Python attempt 1: **212 executed / 38 errors** because the new evidence guard blocked asyncio's Windows loopback socket pair and own-process HTTP fixtures. The guard alone was corrected to recognize live sockets bound by that process; all remote/unowned connections stay denied. Attempt 2 passed 212. No runtime or test assertions were changed to accommodate failure.
- Matrix-generation command 1 failed decoding the UTF-8 mission using Windows cp1252 before writing the matrix or running syntax checks. Its record remains; the evidence script now explicitly reads UTF-8.
- Documentary package preparation rejected the newly created `.ps1` copy helper because that extension was absent from its allowlist. It stopped before OneDrive writes; the preserved record identifies the correction to the package-only allowlist. No runtime or tests changed.
- All older failed/transitional runs remain in their original locations. Original Stage 1 PermissionError remains **ROOT CAUSE UNCONFIRMED / FAIL-SAFE / REVIEW REQUIRED**. Later response-publication and challenge/response contention mechanisms remain separate. No historical cause is retrospectively proven.
- Restricted-context Electron GPU failure remains an environment limitation: **44.2.0**, exit consistent with STATUS_DLL_NOT_FOUND; exact missing/inaccessible DLL and root cause **UNCONFIRMED**. Host-context success does not erase it.
- Other-user/cross-session/actual-remote-host skips, physical voice, live-provider cancellation/parity, production enrollment and clean-machine deployment remain unverified where previously disclosed. No new hardware, security or provider authority was assumed.

## Stages 5–7 preparation and remaining dependency

**Stage 5: NOT STARTED.** Its conditional authorization requires the human Stage 4 lifecycle criterion to be satisfied first. The [human check](../../STAGE4-HUMAN-LIFECYCLE-CHECK.md) is prepared and the user has said they will run it. No resulting PASS or completed operator record has yet been received. An automated script invocation cannot replace that result. After it passes, use the frozen baseline for the existing integrated reliability matrix; no further permission is required merely to progress.

**Stage 6: isolated rehearsal PARTIAL.** The initial unchanged Stage 3 fixture rehearsal passed 11 recorded checks. A subsequent synthetic fixture reflecting the current **19 application tables** passed **13 checks** using the unchanged Stage 3 migration/verifier: real SQLite backup/restoration, committed WAL record recovery, complete artifact comparison, linked assistant/provenance preservation, inspection finding/source/event linkage, rollback without newer writes, and refusal to overwrite newer state. See `cutover-rehearsal-2d3eb60e240c4ca6949b7819274132eb.json`. Table definitions alone were read from already-authorized TEST data; no historical user records or production data were copied. The known synthetic fixture policy was updated for that new fixture, not the accepted migration algorithm or production schema.

This proves backup/restore of the synthetic current schema; it does **not** prove switching a live Stage 4 runtime between deployment locations, Windows enrollment recovery, secrets restoration or clean-machine boot. The exact live database identity/source and final approved canonical destination must be verified under the eventual live-cutover authority; the original proposed destination is the resolved user known folder `%LOCALAPPDATA%\Teague Industries\JARVIS`, not an authorized move today. Stage 3's no-naive-rollback-after-writes contract remains mandatory.

**Stage 7: preparation only; installer/update/uninstall NOT RUN.** Read-only repository inspection finds two private 0.1.0 Electron 44.2.0 package manifests with start/test scripts, no reviewed Windows installer/update package contract. `desktop/local-updates.cjs` watches the development source tree; it is not a distribution updater. The TEST adapter/runtime deliberately pin source-relative TEST roots, a separately built native addon and a trusted test-parent enrollment. Copying files into an arbitrary install directory cannot safely be represented as a working installed production client.

A concrete release dependency therefore remains: review a relocatable, allowlisted TEST release layout/bootstrap and its Core/client enrollment and protocol manifest, then select the per-user Windows installer/update/uninstall mechanism and permitted install/data roots. That changes the deployment trust/configuration boundary; no production-mode fallback, relaxed TEST-root check, speculative packaging tool installation or source-watcher reuse was implemented. [Readiness source/schema hashes](cutover-packaging-readiness-audit.json) support this finding. Ordinary packaging preparation cannot silently become production enrollment design.

Clean-machine procedure to validate after that contract exists: provision the approved signed/pinned runtime dependencies and enrolled identity; restore the verified DB and classified artifacts to an empty approved destination; verify full logical state and artifact links; freshly enroll/authenticate clients; establish a new runtime epoch with no restored presence/grants; exercise one safe request and explicit shutdown; retain the original and newer state. If startup fails or new writes exist, preserve them and use the reviewed compatible-runtime/reconciliation procedure. This sequence is documented, **not executed on a clean machine**.

## Scope, rollback and final disposition

Five reviewed source/test files changed in this campaign: `stage4_runtime.py`, `stage4_client.cjs`, `tests/lifecycle_stage4/fixtures.py`, `tests/lifecycle_stage4/test_stage4.py`, and `desktop/test/stage4-client.test.cjs`. Exact prior bytes, source snapshots, focused diffs and hashes are in this package and the restart/client-state-media packages. The new human controller is a fixed TEST console driver in the existing fixture file; management credentials never enter the renderer or evidence.

Rollback: verify the specific campaign TEST identities have exited, retain all failed intents/journals/databases/evidence, then reverse only the recorded source hunks against matching before/after bytes. Do not reset the dirty tree, delete the stop latch, erase failed startup records, restore an old database over new writes, or roll back production. Source rollback does not authorize ambiguous consumed start intents to run again.

Nonsecret source, reports, logs, hashes and selected screenshots are copied to TEAGUE INDUSTRIES DATABASE with a separate copy-verification record. Raw datasets, profiles, enrollment/management material, grants, private handshakes and keys stay excluded. No broad folder sync is used.

Proposed live actions today: **none**. Eventual cutover needs one consolidated owner approval after Stage 4 human acceptance, Stage 5 reliability, deployment/enrollment review, actual source/destination verification and rehearsed rollback/release readiness. No final acceptance/release commit, push, production installation, activation or migration was performed.

**BLOCKED — required human Stage 4 lifecycle evidence is pending; Stage 5 cannot begin yet. Release/bootstrap contract review is also required before Stage 7 installation testing or any production cutover.**
