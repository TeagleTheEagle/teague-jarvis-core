# REMAINING REQUIREMENTS TO DECLARE STAGE 4 COMPLETE

## Human denial-driver correction — fresh human run required

2026-09-15. The original human run reached correct SELECT and DENIAL inputs but failed in the driver before the intended authority-policy test. Its evidence remains unchanged. The [approved narrow correction](lifecycle-stage4-evidence/human-denial-correction-20260915/REVIEW.md) now sends the denial probe through the actual authenticated Electron client and requires a matching Core-side `SCOPE` receipt. Focused actual-Electron validation passed **38 checks**, existing Electron lifecycle **29**, desktop **35**, authentication **35 + one existing skip**, ownership **27**, controller recovery **52**. These are automated results, not human acceptance.

**Gate 5 remains PARTIAL; human acceptance remains OPEN.** Complete a fresh SELECT → DENIAL → CRASH → EMERGENCY → SHUTDOWN session using the updated [checklist](STAGE4-HUMAN-LIFECYCLE-CHECK.md). Gate 6 still depends on that evidence. Stage 5 has not started. The [new source baseline](lifecycle-stage4-evidence/human-denial-correction-20260915/source-after.json) changes only the TEST client and fixture; 25 other validated paths remain unchanged. Earlier closed gates and deferred/limited dispositions remain as recorded below.

## Current completion campaign reconciliation — automated gates closed; human result pending

2026-09-15. This section supersedes the historical status statements below. The [single programme checklist](CORE-COMPLETION-CHECKLIST.md) is the current working authority; the [completion review](lifecycle-stage4-evidence/completion-campaign-20260915/REVIEW.md) and [requirement-to-evidence matrix](lifecycle-stage4-evidence/completion-campaign-20260915/requirement-to-evidence.json) contain exact results and retained limitations.

| Gate | Current status | Evidence changing or confirming its status |
|---|---|---|
| 1. Shared response commit / event ownership | CLOSED | Frozen boundary retained; final 306 race trials / 4,748 assertions, authenticated polling 43, fallback 12, Deep Review 14 + 8, independent SQLite inspection; prior fresh-process restart evidence retained |
| 2. Full Core stop/start, crash/restart and startup races | CLOSED | Reviewed bounded restart transaction; 636 real-process checks, four rounds of eight contenders, three coordinator-loss/adoption and three Core-crash/recovery rounds; 74 actual-client state/media/restart checks |
| 3. Persistent projects/tasks/budgets and fresh presence | CLOSED | Both authenticated Electron clients read the same synthetic records, persistent table hashes survive a new epoch, old grants/sessions/presence are not restored; 36 TEST database inspections |
| 4. Client media watchdog / lease ownership | CLOSED for modeled TEST scope | Six new watchdog cases in the 19-check file; full desktop/Intelligence 35; actual-client 74-check campaign includes partition/expiry, stale callback, cross-owner denial, renderer loss and reattachment |
| 5. Human-operated lifecycle controls | PARTIAL — blocking | Automated controls passed; [human checklist](STAGE4-HUMAN-LIFECYCLE-CHECK.md) prepared. User intends to run it; completed human evidence has not yet been received. Requires exact TEST selection, denial, renderer crash, emergency, shutdown and cleanup |
| 6. Final evidence/source reconciliation | PARTIAL — depends only on human evidence | Automated regressions passed, 170 recorded process identities exited, 22 protected paths unchanged; exact modified hashes and syntax recorded. Incorporate human result before acceptance baseline |

Approvals remain **DEFERRED — WORKFLOW NOT PRESENT IN CURRENT STAGE 4 PRODUCT SURFACE**. Uploads remain **DEFERRED — REQUIRES SEPARATE AUTHORITY / PERSISTENCE REVIEW**. Physical media remains deferred. None is counted as PASS. Historical PermissionError and restricted-context Electron GPU findings retain their previous classifications. All failed/transitional runs remain preserved.

Stage 5 is conditionally authorized by the completion campaign, but **has not started because the required human Stage 4 result remains pending**. No acceptance commit or production operation has occurred.

## Historical checkpoints (retained)

## Latest superseding reconciliation — response-commit gate CLOSED

2026-09-15. The three remaining checks passed against **unchanged frozen source**:
fallback integration/restart **12 + 4**, Deep Review integration/restart **14 + 4**,
actual authenticated Deep Review pipe **8**, and supplemental fresh-process
validation **88 checks in four sequential TEST processes**. Standalone syntax
passed for **15 Python and five JavaScript files**; **62** affected provider
regressions passed. Independent post-exit read-only inspection of five TEST
SQLite databases found no orphan assistant messages, orphan successful
provenance or duplicate responses. All 26 source/executable paths stayed unchanged.

**Gate 1: CLOSED.** See [final validation, exact commands, hashes and limits](lifecycle-stage4-evidence/response-commit-final-validation-20260915/REVIEW.md)
and [machine-readable results](lifecycle-stage4-evidence/response-commit-final-validation-20260915/validation-summary.json).
The prior **29-check actual Electron** dependency remains CLOSED and was not
rerun. The shared boundary's **918 trials / 14,244 assertions** and two
**43-check** authenticated polling probes remain retained final-source evidence.

Fresh-process answer/provenance persistence, new TEST epochs, owner-scoped
queries and stale-authority rejection are established. These existing TEST
composition/helper checks do not validate the coordinator's start-after-stop
policy or full crash/restart matrix. **Next unresolved gate: gate 2**, still
PARTIAL and not started. Other gates retain their existing status. Approvals
and uploads remain DEFERRED, not PASS.

The restricted-context Electron 44.2.0 GPU failure remains an execution-environment
limitation: observed STATUS_DLL_NOT_FOUND-compatible status; exact DLL/root cause
UNCONFIRMED. No GPU flags or runtime changes were made. A parse-only typo in an
independent audit command is preserved separately; it caused no runtime execution.
All previous failures remain retained. Production is unchanged and blocked;
no Stage 4 acceptance commit or Stage 5. Stage 4 remains incomplete and paused
for review. Earlier checkpoint statements below describe their historical state;
this section and the CLOSED/backlog tables control the present status.

2026-09-15. **REVIEW ONLY â€” Stage 4 remains paused.** This reconciliation records the user's acceptance of the controller reauthentication/lifecycle-only recovery requirement as validated against the final reviewed source. It does not accept Stage 4 as a whole or authorize further work.

No runtime code changed, tests rerun, Core/client launched, production accessed, acceptance commit created or Stage 5 started by this reconciliation. Only documentation and hash/evidence bookkeeping were written.

Historical gate-1 inspection (superseded by the explicit deferrals below): [approval/stream/upload scope review](STAGE4-APPROVAL-STREAM-UPLOAD-REVIEW-20260915.md). Gate 1 remains **PARTIAL**. Owner-bound event polling exists; approval/upload workflows are absent from the authenticated TEST surface. Adding their routes/action or indexing authority triggers the explicit scope-review condition. No runtime implementation or tests were performed in that inspection, and no acceptance exclusion was assumed.

## Historical event-polling decision and failure (superseded above)

**Historical correction checkpoint:** the reviewed shared response boundary is now
implemented and its targeted invariant passes: 918 final trials, 14,244
assertions, two 43-check authenticated probes, plus independent SQLite checks.
The final-source actual Electron regression failed at startup before attachment;
the TEST Core exited normally. Correction acceptance is PARTIAL, not CLOSED.
Fresh-process provenance/restart reruns and final standalone syntax checks were
not executed after the mandatory stop. See [the correction report](lifecycle-stage4-evidence/response-commit-correction-20260915/REVIEW.md).
Prior CLOSED checkpoint entries below retain their historical scope and are not
a claim that every final-source regression passes. Production remains blocked.

Approvals and uploads are now explicitly DEFERRED, not counted as passed. Event polling remains in scope and has a reproduced late-write FAIL. See [the actual integration evidence and scope stop](lifecycle-stage4-evidence/event-polling-20260915/REVIEW.md). Only the test fixture changed; no runtime correction, full-suite rerun, production change or acceptance commit followed the failure. Earlier source hashes below describe the prior reviewed checkpoint; the new fixture hash is recorded in the event-polling evidence.

The subsequently authorized pre-edit design trace is complete: [response-commit design review](lifecycle-stage4-evidence/response-commit-design-20260915/REVIEW.md). It identifies separate text-only/deep-review persistence paths outside a normal-chat-only guard and the narrow Store transaction-interface dependency. The explicit bypass stop condition was reached before runtime edits. Gate 1 remains FAIL pending review of the shared boundary; no tests were rerun and no other gate status changed.

## Evidence basis and source binding

The governing baseline is the original Stage 4 47-case matrix in the supplied mission (`9a816a6e-52a1-4933-97f8-d89a8c461105/pasted-text.txt`), expanded by [ownership/drain design sections Bâ€“I](CANONICAL-CORE-STAGE-4-OWNERSHIP-DRAIN-DESIGN.md), with later explicit TEST-only approvals controlling scope. Old NOT RUN/blocked entries in the chronological report are historical, not the latest acceptance state.

Evidence abbreviations below:

- **R:** [controller recovery report](lifecycle-stage4-evidence/controller-recovery-20260915/REVIEW.md), [validation summary](lifecycle-stage4-evidence/controller-recovery-20260915/validation-summary.json), [manifest](lifecycle-stage4-evidence/controller-recovery-20260915/manifest.json).
- **X:** [actual authenticated expiry/recovery: 45 checks](lifecycle-stage4-evidence/real-app-probe-34049809379e42c8ae55903a0363fd22.json).
- **E:** [actual Electron lifecycle: 29 checks](lifecycle-stage4-evidence/electron-app-probe-ba76c336d41c454ba35934626c336b80.json).
- **D:** [real deadline: 36 checks, 30.047 seconds](lifecycle-stage4-evidence/real-app-probe-0d6374a307bd449592a4b184a3584d55.json).
- **I:** [inspection/archive cleanup report](lifecycle-stage4-evidence/inspection-validation-20260912/REVIEW.md): real cancellation/detach/emergency 43/43/44 checks; independent archive verification.
- **W:** [repair loop/cleanup report](lifecycle-stage4-evidence/repair-loop-20260913/REVIEW.md): real cancellation 44, detach 45, drain 46, focused 22 and loop audit 16. Its later failed emergency run remains retained.
- **F:** [later successful repair emergency: 45 checks](lifecycle-stage4-evidence/real-app-probe-711ed793ec2349aca525352f9ebeeb98.json).

Read-only SHA-256 comparison in this reconciliation confirms the current four corrected files match R's tested `current/` snapshots:

| Source | SHA-256 |
|---|---|
| stage4_sessions.py | 6918ec049b7b8d0f34a917c276996e9df026331a4eafa164f6d6cb6363f47b81 |
| stage4_runtime.py | eec3dcb54db00b795f687c1316b7fb3f83a581a3ba1b132742d62e35cf44b3ec |
| tests/lifecycle_stage4/fixtures.py | e2f04efa438c6b0d02fef80d74994c43dd2ba224a3bfdeceaef0a9c0ed591558 |
| tests/lifecycle_stage4/test_stage4.py | 9c6b8818ceb2c75ba9cc0bf95e7549c4bf10bdcd202ce67f28135111549e3c8c |

All 22 protected hashes also still match. These are comparisons with the validated checkpoint, not new test execution or certification of every unrelated working-tree change.

## CLOSED â€” removed from the blocking backlog

| Requirement | Status | Evidence changing the status |
|---|---|---|
| Event-polling ownership/cancellation/late-write gate, including shared response-commit acceptance | **CLOSED** | [Final validation](lifecycle-stage4-evidence/response-commit-final-validation-20260915/REVIEW.md): fallback 12+4, Deep Review 14+4 and authenticated pipe 8, four fresh processes / 88 checks, 62 provider regressions, syntax 15 Python / 5 JS, five independent TEST DB checks. Retained frozen-source 918 trials / 14,244 assertions, authenticated polling 43+43 and host-context Electron 29. No orphan/duplicate records; stale authority denied. This does not close the broader restart matrix below. |
| Explicit TEST controller reauthentication and lifecycle-only recovery after expiry | **CLOSED** | User-directed recording against the matching final source; R's 52 focused checks and X's 45 actual authenticated checks. Fresh family, same surviving Core, old authority denied, no replay; recovery cannot clear UNKNOWN, restart deadlines or obtain ordinary work/media authority. Expiry used a trusted TEST clock, not an idle/sleep endurance trial. |
| Automated inspection worker cancellation, archive completion and cleanup | **CLOSED** | I supersedes the missing synthetic archive-project blocker. Its original failure is retained. R later reran the 13 focused inspection checks successfully; relevant protected worker code is unchanged. |
| Synthetic repair worker/loop cleanup and conservative reservation accounting | **CLOSED** | W established cancellation/detach/drain and accounting; F closes the previously outstanding successful emergency rerun, and R/X close the controller-expiry recovery deficiency. The earlier interrupted run remains failed and its interruption cause unconfirmed. No real repair execution or comprehensive monetary metering is claimed. |
| Both actual Electron clients attach to one Core, close/reopen without killing it, foreign cancellation denied | **CLOSED** for the demonstrated automated client lifecycle scope | E's 29 checks, same Core identity/shared conversations, independent profiles, renderer-crash survival, no replay and normal exits. Its inspected screenshots supersede the earlier startup/show/capture blocker. This is not physical-media or across-Core-restart proof. |
| Existing authenticated shutdown/emergency/deadline path | **CLOSED** for known-work drain and UNKNOWN quarantine | D, F and X establish actual process exits after authorized shutdown and retained ownership before safe completion. Old NOT PASS deadline/emergency statements no longer block this tested path. Broader crash-boundary matrix below is distinct. |
| Current checkpoint regression and static-validation requirement | **CLOSED** at this source checkpoint | R: Stage 1 23 pass/1 skip, Stage 2 35 pass/1 skip, Stage 3 43 pass; Python 212, desktop 29, provider 62, native 15, bootstrap 6; four Python compilations and unchanged audit guard. No repeat is needed merely to update this checklist. Future source changes require their relevant final regressions. |

## Still-open blocking gates only

Each FAIL/PARTIAL/OPEN in-scope row blocks formal Stage 4 completion and its acceptance commit. None authorizes implementation now. Stage 5 remains separately unauthorized even after these gates close.

| Gate | Status | Exact remaining proof / why existing evidence does not close it | Closure evidence and authorization |
|---|---|---|---|
| Authenticated TEST approvals | **DEFERRED** | **WORKFLOW NOT PRESENT IN CURRENT STAGE 4 PRODUCT SURFACE** — explicit subsequent user decision. | Excluded from Stage 4, not PASS. No routes/actions were added. |
| Authenticated TEST uploads | **DEFERRED** | **REQUIRES SEPARATE AUTHORITY / PERSISTENCE REVIEW** — explicit subsequent user decision. | Excluded from Stage 4, not PASS. Legacy extraction/indexing remains unexposed. |
| **2. Full real-Core stop/start, crash/restart and repeated race matrix** | **PARTIAL** | Original cases 20â€“28, 32â€“33 and 43 plus design I require more than same-Core reattachment. X/E prove survival/reattachment; Stage 1/2 prove their harness semantics. They do not prove the entire composed real App/Store/clients restart matrix. Explicit authorized start after a stop latch, new epoch/same data, old grant rejection, clients reauthenticating across epochs, and interrupted intent/journal/accounting reconciliation remain without complete integrated evidence. | At least four rounds of eight startup contenders and three rounds each of coordinator-loss/adoption and Core-crash scenarios, per design I; lock before Store/until exit, no replacement in recovery, new epoch/same canonical TEST state, no replay/refund or restored presence. Preserve every failure. No opportunistic latch deletion or unapproved termination; any missing start-policy implementation must be reviewed within scope. |
| **3. Full shared persistent TEST state and fresh presence evidence** | **PARTIAL** | Original cases 29â€“34. E/X show shared conversations/memory and identity. W proves actual repair accounting plus a focused subprocess persistence check. Current `shared_state` exposes memory/conversations/ownership, not a complete project/task/budget comparison through both actual clients. These are not full proof of all shared categories, their preservation across a real Core restart, or fresh device presence afterward. | Independent comparison of approved synthetic memory/conversation/project/task/budget/recovery records before/after, both authenticated clients tied to that data identity, no refund or authority restoration, disconnect removes only its presence, restart starts offline until fresh authenticated attachment. Combine with gate 2 to avoid duplicate tests. TEST-only; any Store/schema or device-architecture expansion needs review. |
| **4. Client-side lease watchdog and integrated media-control ownership** | **PARTIAL** | Core lease arbitration/idempotency/foreign-result rejection and silent existing-VoiceEngine delivery have model/actual-App coverage in R/X. The clients truthfully deny physical media. That does not demonstrate local watchdog expiry, stale callback rejection, partition/reconnect behavior or modeled capture/output stopping in the actual adapters while another client continues. | TEST-only deterministic adapter/renderer traces for capture/playback/request controls, lease expiry/heartbeat loss, no duplicate delivery/takeover, no auto-reacquisition after reopen, local mute preserving shared settings, and owner emergency revoking all relevant work/grants. No browser-TTS fallback. Physical microphone/headset/voice parity remains separately deferred; do not enable hardware as part of this gate without approval. |
| **5. Human-operated isolated acceptance of lifecycle controls / final client review** | **PARTIAL** | Automated authenticated management, inspected Electron images and explicit retained-controller commands are validated. No new user-performed native-controller exercise is evidenced by those automated results. Earlier production UI keyboard/time tests are not this isolated acceptance. | Record an explicit human TEST identity selection and separately authorized emergency/shutdown actions, ordinary-client denial, controller reachability after renderer failure, and matching lifecycle events. Review may explicitly accept existing evidence for a narrower criterion; do not silently mark manual PASS. Physical/manual media remains separately authorized/deferred. No new UI implementation is assumed necessary without review. |
| **6. Final acceptance reconciliation and source/evidence sign-off** | **OPEN** | The current checkpoint is validated, but gates 2–5 are not all closed. A full 47-case cross-reference and final acceptance source set do not yet establish overall PASS. This row is review/packaging, not a new feature or demand to rerun passing tests today. | Close remaining cases against exact final source, identify accepted deferrals versus blockers, preserve all failed evidence, retain rollback/source hashes and nonsecret record copies, and review scope-isolated staging before any acceptance commit. This request explicitly forbids that commit. Production activation and Stage 5 need their own authorization. |

## Not additional Stage 4 blockers

- Historical Stage 1 PermissionError remains **ROOT CAUSE UNCONFIRMED / FAIL-SAFE / REVIEW REQUIRED**. Its required assessment is recorded; historical root-cause proof is not a new prerequisite to this isolated checkpoint. Later reproduced response-publication and IPC guard mechanisms/corrections remain separate. Production disposition is not silently cleared.
- The preserved September 13 multi-hour interruption is not newly explained. F and X close the current emergency/recovery test requirements, not the historical causal question. A sleep/resume endurance test is not invented as a new requirement here.
- Existing Stage 1 cross-session and Stage 2 other-user/cross-session/actual-remote-host skips remain explicitly unverified. They are not fresh failures or an instruction to alter Windows security. Their production/security review remains separate.
- Physical microphone/headset/audibility, live-provider cancellation/parity and provider credits are deferred under the TEST-only boundary. Hardware-unavailable screenshots are truthful, not failed voice output. Gate 4's missing synthetic adapter ownership proof is distinct; any decision to require physical acceptance before isolated completion must be explicit.
- Universal token/monetary metering, Ollama Independence, Astra comparison, autonomous development, installer/suite conversion and production cutover are not Stage 4 closure work. Later explicitly approved TEST provider work supersedes the original shadow-only restriction only in its bounded TEST scope; it does not authorize production routing or add these projects to the critical path.

**Stage 4 remains paused for review. Production remains unchanged and blocked. No acceptance commit. No Stage 5.**
