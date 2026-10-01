# Canonical JARVIS Core — Stage 4 ownership and drain design

Date: 11 September 2026. **DESIGN REVIEW COMPLETE; IMPLEMENTATION NOT AUTHORIZED.**

ONE JARVIS. ONE CORE. ONE IDENTITY. ONE CANONICAL MEMORY. Multiple clients with explicit interaction ownership.

This document proposes the minimum isolated integration contract. It does not activate it. Only this document was created during this review; no runtime source, configuration or database was changed, no Core/client was started, and no lifecycle, audio, provider or failure-injection test was run. No commit or broad records sync was performed.

Read as governing evidence: CANONICAL-CORE-OWNERSHIP-PROPOSAL.md, CANONICAL-CORE-STAGE-1.md, CANONICAL-CORE-STAGE-2.md, CANONICAL-CORE-STAGE-3.md, CANONICAL-CORE-STAGE-4-AUDIT.md and lifecycle-stage3-evidence/stage1-permission-investigation.json, all under this docs directory. Current source was inspected as text, without importing the App or opening a Store. Historical proposals are not deployed capabilities.

All file paths in the implementation map are relative to the exact repository root:
`C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis`.

## A. Current blocker evidence

**OBSERVED CURRENT BEHAVIOR** — source observations, not new live verification:

| Files/functions | Current owner, authorization and cancellation | Disconnect/shutdown and persistence |
|---|---|---|
| `desktop/main.cjs`: start, stop, quit, close and render-process-gone handlers; `desktop/backend.cjs`: startBackend, stop, quit | Electron starts its Python backend, generates a shared desktop token and sends global stop/quit through stdin. Local capture uses ScreenCapture and native permissions. | Close-to-tray and renderer failure invoke global stop. Quit ends stdin and can kill its child after four seconds. Preferences/descriptor are files; capture grants are transient. No scoped multi-client Core revocation. |
| `intelligence/main.cjs`: start | Reads desktop/.jarvis-session.json; injects shared token using URL-prefix matching. It creates a window, not App/Store/providers. | Window closure exits this UI; no authenticated per-client detach protocol. Local fallback is not proof of attachment. Descriptor survives according to desktop owner's lifecycle. |
| `server.py`: Handler.allowed, Run, App.start_run, App.approve, Handler.do_POST | One App cookie, optional environment desktop token, exact loopback Host/Origin and fetch-site checks. `/api/cancel` accepts a run ID, without authenticated owner binding. Approvals are in-memory, expiring, consumed once and linked to run IDs; existing execution checks remain essential. | One active Run is allowed globally. Daemon work thread is started without retaining its handle. Pending runs/approvals/session are in memory; messages and audit records use Store. No authenticated client expiry cleanup. |
| `server.py`: /api/shutdown, main, Server | Ordinary API authentication reaches shutdown. stdin EOF with desktop token set also cancels runs and shuts down. | Signals run cancellation and closes server; does not establish completion of all background/HTTP work. `daemon_threads=True`. No managed admission/drain contract. |
| `static/app.js`: speak, stopSpeech, stop, JarvisVoice callbacks, beforeunload; `static/voice.js`: start/stop/arm/finish/recover/drain; `wake.py`: WakeDetector.predict | Renderer owns capture, conversation/arming/recovery and playback. Core VoiceEngine performs provider synthesis. WakeDetector has one client/last/triggered state; microphone ID is request-supplied. Different recent client is rejected. | Renderer stop stops local audio and requests cancellation of its selected run; unload is best-effort. A fetch abort is not server completion. Browser speechSynthesis is a separate existing fallback. Audio queues, grants and model state are transient. |
| `voice_engine.py`: VoiceEngine.synthesize; `providers.py`: request/chat/speech/transcribe | One App VoiceEngine/cache/lock delegates to provider functions. Blocking synthesis has no cancellation argument. Some provider paths have internal retries; transcribe retries selected connection/timeout failures. | Cancellation cannot retroactively prove no provider consumption. No fresh multi-client or audio verification. |
| `inspection_jobs.py`: InspectionJobs.start/_work/cancel; module JOBS | In-process jobs have cancellation events and detached daemon workers. HTTP status/cancel is not bound to client ownership. | Archiving in `_work` finally may still run after status changes. Expiry timer is another transient owner; a displayed terminal status is not a joined worker. Reports can persist through archive callback. |
| `budgeted_repair.py`: dispatch/run; `project_budgets.py`: change/lifecycle/snapshot; `workspaces.py`: setup/change | Repair uses existing App/Store/service, stable project/operation key, explicit fixture confirmation, reservation/start/write-ahead consumption and conservative settlement. Repair has its own cancellation event. Workspace API exposes configure/reserve, not the internal lifecycle hook. | Budget rows persist; repair experiment runtime status is in App memory. Global Run cancellation does not cover every repair/inspection worker. Expired holds stay charged; snapshot flags them for recovery. |

Additional isolation prerequisite: server import calls load_env against the source .env; App has source-relative personality/model/development paths, and Store creates missing data/schema. An isolated data-dir argument alone is insufficient. Stage 4 must guard configuration/imports and open an explicitly provisioned TEST dataset under lifetime ownership. No production path fallback.

**EXISTING TEST EVIDENCE:** Stage 1 recorded 19 passed/1 skipped in its accepted run; the later Stage 3 regression had 18 passed/1 failed/1 skipped and then four unchanged passing reruns. Stage 2 recorded 35 passed/1 skipped. Stage 3 recorded 43 passed for synthetic migration. These are historical results, not tests performed here. Stage 2 is an isolated pinned-key authentication harness, not production authentication. Earlier Stage 4 AST/syntax checks establish syntax only.

**UNVERIFIED ASSUMPTIONS:** live production database provenance, live owner counts, actual multi-client voice, hardware permission revocation under all failures, other-user/cross-session and actual remote-host rejection. No assertion in this document closes those gates.

## B. Proposed client/session/request ownership

The Core owns one interaction registry in memory, not another database, memory, personality or assistant. Reuse the existing DeviceRegistry for presence; do not create a competing device service.

| Record | Proposed meaning |
|---|---|
| Client identity | An enrolled application instance/configuration, authenticated through reviewed bootstrap. A claimed name alone grants nothing. |
| Session | Random Core-issued session with enrolled client binding, scopes, protocol, monotonic expiry, revocation generation and instance/epoch. Token stays in native client memory; only a lookup hash is retained by Core. |
| Core identity | Existing installation_id/data_id plus fresh instance/epoch and authenticated process/runtime identity. Unchanged canonical JARVIS identity across restarts; TEST is never production. |
| Request identity | Core-issued run/work ID and immutable owner session family. Renewal rotates credentials within that family; a new attachment does not automatically inherit active execution/approval rights. |
| Operation identity | Stable existing project/operation idempotency key where wired. New unmetered work receives an operation ID for lifecycle evidence, not an invented budget allocation. |
| Media right | Expiring Core-issued lease for a specific session/epoch and capture or playback purpose; never accepted solely because a body contains client/admin/owner fields. |

Proposed ordinary session lifetime: 15 minutes, renewed only through authenticated bootstrap before expiry. Capture/playback leases: 10 seconds, renewed every three seconds while valid and explicitly active. TEST timers may be shortened for deterministic tests without changing ordering. These durations await approval and are not guarantees of instantaneous crash detection.

Request path: authenticate transport/session → derive immutable owner context on the server → validate operation scope → acquire admission gate → register operation and any write-ahead recovery record → apply existing action/approval/resource checks → dispatch. Caller ownership claims are rejected; an ID is only a lookup key. Do not hold the admission mutex while doing I/O or executing a tool.

Keep the existing single-active-chat limit. Multiple attached clients do not imply simultaneous AI execution. Contention returns BUSY without new queued work or provider calls. Do not build a scheduler as part of this change.

Ordinary clients may inspect their active requests and cancel those requests. Shared stored memory/conversation/project data may be read under existing same-owner application permissions; shared read access does not grant the right to cancel another session or approve its pending action. Unknown or foreign request IDs return a non-disclosing denial. List/stream/approval/upload endpoints require the same ownership checks, not only /api/cancel. Pending approval decisions must verify the owning session before consuming the existing one-use approval. An owner-wide approval interface would require separate review.

On detach, expiry or revocation: invalidate that session's permissions, remove only its presence, reject further execution/approval/media requests, and signal cancellation of its interactive operations. Cancel-not-started operations without dispatch. Allow a non-interruptible operation already authorized and started only to finish/record its current outcome; no next tool step, follow-up inference or background goal is thereby authorized. Preserve unknown outcomes. No new detached-work permission is introduced. Pending approvals expire/revoke and are never restored from historical records.

A cooperative close revokes immediately; missed heartbeat/session expiry handles crashes and partitions. Client-local lease expiry stops tracks/audio even when Core cannot be contacted. Core independently rejects expired media. A malicious or hung client cannot be guaranteed to surrender hardware by a network message; that limit remains explicit. Last-client departure does not shut down Core and does not start work.

## C. Voice and cancellation ownership

Preserve one actual VoiceEngine, one WakeDetector, existing synthesis configuration, personality, waveform/voice appearance and existing DSP/capture code. No per-client wake models or provider instances. Add permission/orchestration hooks rather than rewrite recognition or speech generation.

Core decides which session may listen, open a conversation, submit a voice request and play a response. Existing renderer endpoint detection, PCM framing, echo handling and local stop remain device mechanics. Renderer arming/recovery/idle prompts become requests subject to Core permission; stale callbacks cannot create speech or reopen capture after revocation. A shared settings toggle remains an explicit settings action; local mute must not write the shared voice preference.

| Control | Proposed scope and effect |
|---|---|
| Stop listening/capture | Always stop own local tracks immediately; release own Core lease. No effect on another client or Core lifetime. |
| Stop request playback | Stop own output and invalidate its pending delivery. Do not cancel another playback or assume synthesis stopped. |
| Cancel my request | Verify immutable owner, then signal that operation; report cancellation_requested until termination/outcome is known. |
| Global emergency stop | Separate human-owner-authorized control; Core cancels all active work and media, revokes pending approvals and suspends admission. Does not release lifetime ownership or imply shutdown. Explicit owner resume, no automatic replay. |
| Core shutdown/restart | Separate scoped lifecycle transaction described below. Never a generic model tool or consequence of window closure. |

Competing input: one active wake-input lease across the current PC surfaces, first valid explicit request wins; BUSY for competitors, no silent takeover or queued recording. Release/reset the existing model only when its active owner's lease ends; an inactive client leaving must not reset another owner's model. B can continue its other authorized activity while A loses capture.

Competing output: one automatic spoken delivery for each Core response, to the requesting session's leased output. Other clients observing shared history do not call TTS. Same request/playback ID is idempotent; explicit replay is a new user action. For this PC-only test, serialize output globally rather than assume two windows use different speakers. Contention is BUSY; no surprise delayed playback queue. Local barge-in may interrupt its own response, not another client's.

Existing browser-TTS fallback remains untouched on the legacy production branch. TEST clients must not independently synthesize when Core voice is unavailable: report unavailable, or play clearly identified deterministic Core-provided test audio. This avoids hiding missing ownership with a second synthesis authority. Live providers, browser fallback parity and actual audibility remain later explicit tests, not claims from synthetic media.

Authorized emergency stop remains a trusted native controller action, not a renderer-provided global flag. If its authority is unavailable, show that global stop is unavailable; local mute/stop still works. Test controller reachability even if a renderer crashes. No extra global hotkey may steal production's existing emergency shortcut during isolated tests.

## D. Lifecycle authorization

Four independent gates remain: authenticated identity, existing action authorization, explicit lifecycle permission and resource availability. Passing one never substitutes for another.

Ordinary TEST Teague/Intelligence enrollment permits attachment, approved shared reads, own request controls and explicitly granted media only. No start/stop/restart/maintenance/emergency authority is inherited. /api/shutdown must reject ordinary sessions even if they hold a valid cookie. The legacy production route is unchanged until separately approved cutover.

Propose a separate native TEST management controller with a distinct enrollment key supplied by the trusted test parent, not stored in a desktop descriptor, renderer or production key file. The human explicitly chooses stop/restart/emergency-stop and the target TEST identity. Controller requests a one-use capability bound to action, exact namespace/instance/epoch, operation ID and 30-second expiry. Core validates the scoped management credential and consumes it atomically. Repeated same operation returns existing status; it never restarts the drain timer or repeats execution. Revocation/expiry prevent new commands, not reversal of an accepted stop intent.

Coordinator serializes start/stop/maintenance under supervisor.lock, holds no Store/provider/voice, and delivers authenticated management intent to Core. Core validates authority and owns admission/work/state transitions. Coordinator is not a second execution-authorization service. A dead coordinator cannot clear a live Core's stop state; replacement reconciles identity and accepted intent before proceeding.

Core stop intent is acknowledged only after admission is closed and a durable TEST stop record is written. Crash before acknowledgement is uncertain; reconnect/status must not retry execution. Start after stop requires a separately authorized start transaction under supervisor exclusion, verified absence and acceptable recovery state. A caller's application name, admin boolean or operation string cannot establish authority.

Unauthorized calls are denied and recorded with bounded reason codes, timestamp, authenticated identity if available and opaque operation reference. Never log tokens, request bodies, proof material or conversation content. Logging failure does not turn denial into permission. Rate-limit unauthenticated denial logs to avoid disk exhaustion. Keep loopback Host/Origin/fetch-site protections and exact native origin matching, including redirects. Do not claim Stage 2 already implements human enrollment or management actions: those harness responses explicitly say lifecycle_executed=false.

## E. Shutdown/drain state machine

Proposed lifecycle: RUNNING → DRAINING → CANCELLING → FINALIZING → EXITED. DRAINING/CANCELLING/FINALIZING can enter RECOVERY_REQUIRED. No automatic transition from RECOVERY_REQUIRED back to RUNNING. Emergency stop enters SUSPENDED and remains distinct from shutdown.

Proposed total deadline: **30 seconds from accepted shutdown**, with up to 10 seconds for suitable completions and the remaining time for cancellation/cleanup. All persistence, lock acquisition, provider waits and joins must fit the remaining deadline; a Python timeout does not cancel a worker. A hard bound requires the uncooperative-worker test, not just a timer assertion.

1. Validate management capability. Under the same admission gate used by request dispatch, close new admission, identify registered operations and record shutdown intent. Failure to persist intent yields RECOVERY_REQUIRED, not successful stop; coordinator also retains transaction intent and must not clear it blindly.
2. Deny new chat, tools, synthesis, inspections, repairs, approvals, settings writes and state refresh side effects. App.state is not a drain-safe status API: it can fire reminders and update history. Supply a separate memory-only lifecycle status surface. Close general client admission; retain bounded authenticated management status while needed.
3. Register accepted work before releasing admission, including nested operations. Accepted-but-not-started work is cancelled without dispatch. Already-running short local commits may finish. Interactive streaming work can receive cancellation immediately. No new external/tool stage starts just because its parent request was admitted earlier.
4. At most ten seconds later request cancellation of all remaining cancellable work. Track actual worker completion including inspection archive callbacks, HTTP handlers, synthesis, approval-triggered actions and repair cleanup. Timers/callbacks that could write must be tracked or prevented from firing. Displayed done/status and cancellation events are not sufficient evidence.
5. Record known outcomes, recorded usage and unresolved operations. Preserve budget holds/consumption and idempotency identity. Missing persistence or unknown active writers prevents FINALIZING. Do not block while holding the admission/ownership mutex, and do not let worker and drain paths race two settlements.
6. Revoke ordinary sessions and all transient media grants; stop general listeners and event streams. Once tracked work and callbacks are finished, close remaining resources and management listener in bounded order. Store uses per-operation connections; prove they are closed rather than invent a Store.close call.
7. Retain core.lock until process exit; no window, listener or coordinator callback releases it early. OS process termination releases the lifetime handle. Coordinator must verify process exit and ownership absence before any next start, not trust a final response alone.

At deadline, if anything remains active or uncertain, return a terminal **shutdown-attempt** result RECOVERY_REQUIRED and keep the stop latch and Core ownership. No indefinite join, automatic repeated drain, automatic resume, replacement spawn or blanket process kill. The quarantined process may retain unresolved workers and a restricted management status channel; this is explicitly incomplete shutdown. Late completion records evidence but does not resume execution. A later owner-authorized re-evaluation can finalize once every writer is accounted for.

Separately authorized forced termination is **not included** in Stage 4 implementation scope. External Windows/process death is treated as crash recovery, not graceful success. A future force policy would need bounded process targeting, uncertain-write handling and explicit review. Runtime deadlines cannot guarantee completion of unknown external operations.

## F. Failure, budgets and recovery

### Coverage actually wired today

`budgeted_repair.run` reserves one core_requests unit and two container_checks, starts with revision checks and charges before attempts. It marks uncertain failures/cleanup conservatively; settlement requires outcome evidence. The duplicate operation path returns REPLAY_NOT_EXECUTED. `workspaces.change` also exposes configure/reserve; reserving does not execute anything. `project_budgets.lifecycle` is an internal Core hook, not an HTTP/model action.

Ordinary chat, standalone TTS/transcription, searches and inspections are **not universally metered by this ledger**. Inspection's time limit named budget is not a monetary/resource reservation. No USD accounting, new universal budget enforcement or routing redesign is proposed here.

For tracked reservations, preserve consumption, full held capacity for unresolved work, revision, expiry, project/task/operation identity and evidence. Cancellation of proven never-started work may use the existing release rule; disappearance/timeout alone cannot prove that condition. Started/unknown work remains charged/recovery_required; settlement uses the existing trusted hook only after evidence. Expiry marks recovery concerns; it never frees capacity by itself.

For unmetered operations, record attempted/completed/unknown status without inventing a zero charge or reservation. Stage 4 uses deterministic provider fixtures and denies live provider entry points, including existing retrying transcription paths. No lifecycle retry/replay is added. Existing production provider retry behavior is neither silently changed nor certified compatible with future live draining; it remains an explicit later live-integration gate.

Propose a bounded, content-free persistent TEST operation journal in the same approved TEST data namespace, not another Store/ledger: operation ID, original session reference/epoch, type, phase, budget reference if any, attempt/outcome evidence and cleanup state. Write acceptance before starting effects. It contains no memory, prompts, audio, tokens or renewed permissions. A journal failure refuses new work or puts active work into recovery; it cannot authorize resumption. Active sessions/media/presence themselves stay in memory only.

On restart, new instance/epoch invalidates all old credentials/grants. Journal records are recovery history, never runnable jobs. Existing uncertain/started reservations stay conservative; hold expiry or startup does not refund. Reconciliation must preserve references and account for interrupted journal/database updates; contradiction or corruption blocks further conflicting work. This journal is an explicit new persistent artifact to classify in Stage 4 synthetic fixtures, not an assertion that Stage 3 already verified it. No production schema migration or new approval restoration.

### Retained Stage 1 PermissionError

**ROOT CAUSE UNCONFIRMED / FAIL-SAFE / REVIEW REQUIRED.** Recorded errno 13; exact winerror/traceback absent. Inferred operation: os.replace of a complete temporary response.json beside the target in TEST-02363806196549c7ba7c0067af9fad43. Concurrent reader/filter interference is plausible, not proven. No matching event in the prior narrow Defender query does not exclude antivirus. Do not classify it as merely environmental.

Preserved evidence: one Core acquisition/spawn, RECOVERY_REQUIRED, no replacement spawn. Passing reruns do not erase it.

**Proposed choice:** reuse the accepted Stage 1 exclusion and cooperative reconciliation as a prerequisite, then require Stage 2 authenticated identity as an additional gate. Do not silently replace file reconciliation with pipe authentication or let a valid pipe response override a failed ownership/reconciliation result. Do not edit Stage 1 here. Stage 4 boundary diagnostics should capture available operation, TEST path, PID/time, errno/winerror and cleanup state without secrets. If the unchanged helper loses diagnostic detail, report that limit; do not manufacture it or monkeypatch accepted semantics.

This does not block documentation or, after separate approval, bounded isolated implementation intended to gather evidence. It does block unconditional acceptance/production activation. Run unchanged Stage 1 before real client integration; if recurrence undermines reliable attachment, preserve evidence and STOP that integration. A mechanism change needs its own reviewed delta and repeated exclusion/authentication regressions. Other-user, cross-session, actual remote-host rejection, same-user code trust and production enrollment remain open production gates.

## G. Exact affected-file map for later approval

Proposed new symbols below are interface contracts, not claims that they exist. Changes must be behind explicit validated STAGE4_TEST construction, never selected by a renderer header or ordinary request. Legacy behavior remains default. No silent fallback to production on TEST errors.

| File | Minimum change and reason | Failure, tests and rollback |
|---|---|---|
| `server.py` | Explicit pre-import TEST configuration guard; App dependency/root hooks; Run owner/work handle; App.start_run/tool/approve and Handler admission/owner checks; status/voice routes; optional lifecycle context. Reuse actual App. | Missing identity/config fails before Store; foreign owner denied; admission/drain tests. Restore only Stage 4 hunks on rollback. |
| `desktop/main.cjs` | TEST branch bypasses startBackend; isolated Electron profile/partition before singleton/window setup; per-client close/crash/stop and update behavior; native TEST controller entry with narrow human controls. | No backend kill/spawn or production descriptor/preference writes; actual Electron tests. Keep legacy branch and restore delta. |
| `desktop/preload.cjs` | Narrow TEST media/session notifications and own controls; no management tokens in renderer, no arbitrary scope requests. | Spoofed IPC sender/frames denied; bridge tests; restore delta. |
| `intelligence/main.cjs` | TEST canonical attach, exact origin/redirect restrictions, isolated profile and truthful disconnected state; no desktop descriptor fallback. | Wrong peer/epoch/mode fails with no startup; actual client tests; restore delta. |
| `static/app.js` | TEST owner-bound request/cancel/approval/speech calls and lease events; no observation-triggered TTS or browser fallback; shared preferences distinct from local mute. | Session loss stops own output, no replay; renderer tests; restore delta. |
| `static/voice.js` | Optional permission hooks on start/arm/finish/recover; local hard stop on grant loss. Keep PCM/DSP/endpointing and legacy callbacks. | Stale callbacks cannot reacquire; media model tests, later audio parity; restore delta. |
| `inspection_jobs.py` | Optional work/owner registration in start/_work/cancel including on_finish and expiry timer; completion event reflects actual worker exit. | Drain cannot finish before archive callback; fixture tests; restore delta. |
| `budgeted_repair.py` | Optional owner/lifecycle registration around dispatch/run, expose cancellation/completion to host without changing confirmation/accounting. | Simulated cleanup/outcome tests, no real repair; restore delta. |
| NEW `stage4_runtime.py` | Explicit fixture provisioning versus open-existing startup; coordinator/control entry, namespace guard, sanitized config, accepted lock/auth composition, real App once. | Fail closed at every boundary; Windows tests; retain evidence, remove code only after TEST exit. |
| NEW `stage4_sessions.py` | Core-owned auth-context/lease/operation ownership and scoped management capability validation; mapped to existing authorization. | Expiry/renewal/revocation/foreign ownership tests; remove with dependent TEST code. |
| NEW `stage4_lifecycle.py` | Admission registry, work handles, intent/journal, bounded drain and recovery status. No second database or provider. | Deadline/fault/accounting tests; journal retained for review. |
| NEW `stage4_client.cjs` | Shared native bootstrap/attachment and lease watchdog for both Electron clients, TEST-only credentials in native memory. | Origin/redirect/expiry tests; remove adapter with gated callers. |
| NEW `tests/lifecycle_stage4/fixtures.py`, `tests/lifecycle_stage4/test_stage4.py`, `tests/lifecycle_stage4/.gitignore` | Synthetic data/journal/provider/media fixtures and isolated real-process test matrix; exclude raw secrets/runtime artifacts from staging. | Evidence includes failed runs; retain nonsecret records on rollback. |
| NEW `desktop/test/stage4-client.test.cjs`, `intelligence/test/stage4-client.test.cjs` | Unit and actual-adapter ownership tests; Intelligence currently has a test script but no test directory observed. | No claim of pre-existing Intelligence coverage. |
| NEW `docs/CANONICAL-CORE-STAGE-4.md`, `docs/lifecycle-stage4-evidence/` | Later implementation report and explicitly selected nonsecret case records. | Never overwrite this design or failed evidence to imply a pass. |

No changes proposed to accepted Stage 1–3 code, Store/schema, personality, memory, provider routing, VoiceEngine/WakeDetector algorithms, DeviceRegistry architecture, workspace/budget ledger, repair sandbox/workflow, desktop/backend.cjs, launchers, shortcuts, production preferences or discovery. If exact implementation needs another file or a deeper voice change, report that dependency before expanding scope. Existing module singleton JOBS is tracked, not duplicated. Fixture provider substitution is only inside the test Core, not another provider authority.

## H. Isolated implementation sequence — NOT RUN

1. Obtain separate explicit implementation approval. Snapshot the existing dirty working tree/affected files and record nonsecret hashes; confirm production safeguards without opening a mutable Store. No source rollback to HEAD.
2. Build pure ownership/admission/deadline tests and TEST fixture provisioning. Validate existing data before real App initialization; sanitized TEST startup must not read production .env/personality/data or expose source actions. Synthetic personality preserves production by leaving it untouched.
3. Rerun unchanged Stage 1 and assess retained anomaly. Compose Stage 1/2 in isolated namespace; no auth-to-start shortcut. Collect diagnostic evidence before actual Electron integration.
4. Add gated real App ownership/drain hooks, deterministic providers and synthetic media. Exercise crash, state and budget persistence. No repair execution/live provider/capture.
5. Adapt both actual Electron clients in distinct TEST profiles to the same TEST Core. Test close/crash and request scoping. Production legacy branch retains normal behavior; no auto-update/relaunch of production.
6. Run full 47-case Stage 4 matrix, unchanged Stage 1–3 and affected existing regressions. Produce nonsecret evidence with measured timings and explicit modeled/unverified cases. Stop for acceptance review; no cutover or Stage 5.

## I. Acceptance tests — all pending, not executed in this review

| Class | Required cases |
|---|---|
| Unit/pure model | Auth-derived owner ignores spoofed IDs; A cancels A, denied B; shared reads do not grant foreign approval; token renewal/expiry/revocation; old epoch rejection; separate local stop/playback/request/global/shutdown scopes; 10-second lease expiry; no automatic wake takeover/TTS duplication; admission versus shutdown barrier; all work states and exact 30-second deadline; journal corruption/write failure; budget revision conflicts and no guessed refunds/replay. |
| Deterministic real App integration with synthetic data/providers | One App/Store/VoiceEngine/registry/provider boundary; missing/wrong data fails before construction; A writes approved TEST state and B reads same Store; projects/tasks/budget holds/usage preserved; timeout records unknown unmetered outcome; tracked reservation remains charged; cancelled inspection includes archive completion; pending approvals revoked; no actual repair; shared settings untouched by local mute; disabled routes fail closed. |
| Real Windows processes — isolated only | Concurrent starts (at least four rounds of eight contenders), coordinator loss/adoption and Core crash (at least three rounds each), lock-before-Store and lock-until-exit, child-handle inheritance, stop latch/reconnect, interrupted intent/journal, failed drain while worker remains alive, no replacement during recovery, new epoch/same data, old credentials rejected. Stop on meaningful PermissionError recurrence; preserve every failure. |
| Actual Electron clients — isolated only | Both actual applications same Core; A closes/crashes during request and modeled capture, B continues; last client closes Core survives; stdin EOF harmless; unauthorized shutdown rejected; human TEST controller stop/emergency works; reconnect has no replay/media grant; origin redirects never receive credentials; independent TEST profiles; no production descriptor/preferences modification. |
| Existing regressions | Unchanged Stage 1/2/3 suites; current Python tests covering voice, approvals, Store, budgets, repair isolation and shadow mode; desktop tests, new Intelligence tests; JS/Python static checks reported separately. Legacy startup integration only with synthetic data and provider/mic suppression, never restart production for regression. |
| Manual, separately authorized later | Real microphone permissions, headset interruption, unchanged usual voice/audibility, competing hardware output, capture revocation under suspend/disconnect and emergency control reachability. No manual audio PASS from simulated leases or synthetic bytes. |

The original Stage 4 47-case matrix remains mandatory; the cases above expand its ownership/drain detail, not replace it. Record test identity, epoch, operation type/status, ownership counts, timings and reason codes only. No conversation/memory/audio/token/proof data. Distinguish failed, skipped, modeled and manually verified outcomes. Cross-session/other-user/remote-host tests remain unverified until specifically authorized and performed; no security-policy change in this scope.

## J. Remaining decisions and gates

Approval is requested for the concrete recommended defaults: 15-minute sessions, three-second heartbeat/10-second media leases; one wake stream and one PC output at a time; single-active-chat retained; no newly authorized detached work; 30-second drain with 10-second grace; recovery quarantine rather than forced kill; native separately enrolled TEST human control. No implementation approval is inferred from this design review.

Outstanding evidence-dependent decisions: exact Stage 1 failing operation/winerror and whether a separately reviewed IPC change is needed; trustworthy production enrollment/key storage and same-user code identity; live provider retry/cancellation contracts; physical audio parity; production data provenance; durable journal/SQLite reconciliation under power loss; Windows logout/forced shutdown policy. These do not prevent this design deliverable, but cannot be called solved by it. Protected TEST setup is a cooperative integration boundary, not protection against arbitrary same-user malware or administrator access.

## K. Rollback and production-cutover boundaries

No rollback execution occurs now. Before later implementation, retain pre-edit bytes and existing Git diff so unrelated uncommitted work survives. Gated legacy defaults must remain unchanged. A rollback removes only Stage 4 hunks/new runtime files after verified TEST process exit; do not blanket checkout/reset the working tree. If the TEST Core cannot drain, keep its namespace/ownership and evidence for explicit review rather than delete files or kill unknown processes.

Keep new TEST data/journal, failed evidence and any new writes. Never restore an older database to make code rollback succeed; an incompatible TEST runtime/data pair fails closed until reviewed. Stage 3's no-naive-rollback-after-writes principle remains. Production databases, configuration and launchers are not part of this rollback because no production cutover occurs.

Future production activation still requires separate approval, verified live provenance, backups/rollback, legacy launcher fencing, resolved/dispositioned Stage 1 reliability and Stage 2 security gates, live voice/client evidence and reviewed provider/drain behavior. No service, installer, firewall/LAN, physical device, Ollama Phase 2 or autonomous deployment work is included.

## Recommendation and status

Next approval should authorize only the file scope in G and sequence/tests in H–I for isolated Stage 4: one real TEST Core, both actual TEST clients, authenticated ownership/voice leases, human-scoped management and bounded drain with preserved uncertain state. It should explicitly retain the Stage 1 stop-on-impact gate and exclude forced termination, live audio/providers, actual repair execution and production cutover.

DESIGN REVIEW: COMPLETE

RUNTIME CODE CHANGED: NO

PRODUCTION DATA MODIFIED BY THIS TASK: NO

PRODUCTION CORE RESTARTED: NO

NEW CORE STARTED: NO

STAGE 4 IMPLEMENTATION STARTED: NO

STAGE 4 ACCEPTANCE: NOT CLAIMED

STOP FOR REVIEW. Design completion is not implementation approval.
