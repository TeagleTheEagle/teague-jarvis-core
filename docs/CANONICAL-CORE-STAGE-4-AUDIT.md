# Canonical Core Stage 4 — integration audit and review gate

Status: **BLOCKED FOR ARCHITECTURE REVIEW — NOT IMPLEMENTED, NOT PASSED**.

This is the first, read-only integration audit required by the approved Stage 4 brief. The stop decision follows its voice-ownership review requirement and its instruction to stop if real App integration requires a major ownership redesign. It is an engineering assessment of the cross-layer changes below, not a demonstrated impossibility of lifecycle independence.

No Core or client was launched. No production/shared runtime source was modified. Only this report and `lifecycle-stage4-evidence/integration-audit.json` were created. Existing unrelated working-tree changes were preserved. No commit or OneDrive archive was made.

## Evidence categories

- **OBSERVED:** Current source behavior described below, inspected as text without importing `server.py` or reading credentials.
- **VERIFIED:** 16 Python files parsed successfully with `ast.parse`; eight JavaScript/CommonJS files passed `node --check`. SHA-256 hashes of 25 audited source/launcher files match before and after these checks.
- **PROPOSED:** The ownership changes and test gates below. None is implemented.
- **IMPLEMENTED:** No Stage 4 runtime, adapter or test harness. Documentation/evidence only.

Source-hash verification covers this audit/check interval. It does not establish that the working tree matches a prior release. Source inspection does not prove live production ownership counts, active data provenance, or successful client behavior.

## Current ownership and integration map

| Boundary | Observed current source | Reuse and gap |
|---|---|---|
| Desktop startup/readiness | `desktop/main.cjs` calls `startBackend`; `desktop/backend.cjs` spawns source Python with `server.py --port 0`, inherited environment plus a fresh desktop token, piped stdin/stdout. Readiness is a stdout URL. | Preserve the legacy production branch. TEST attachment must not call this backend owner or treat its stdout as authenticated identity. |
| Desktop quit/renderer failure | `stop()` sends global backend stop. Close-to-tray and renderer failure call it. `quit()` calls backend quit and removes the desktop descriptor. Backend quit ends stdin and may kill its child after four seconds. | Window/capture code is reusable. Client revocation must be separated from global cancellation and explicit Core lifecycle authority. |
| Desktop backend failure/updates | Backend exit causes desktop quit. `local-updates.cjs` drives frontend reload or application relaunch; restart currently also quits its backend. | TEST clients need explicit disconnected/re-authentication state. Client reload must not restart Core or replay a request. |
| Intelligence | `intelligence/main.cjs` reads `desktop/.jarvis-session.json`, attaches its token using `startsWith(origin)`, and loads `/intelligence.html` with a local fallback. No App, Store or Python spawn appears in this entry. | Reuse its actual window/frontend. Replace TEST trust with canonical bootstrap and exact parsed-origin checks. A fallback page must not claim a connected Core. Production code has not been changed. |
| App and Store | `server.py:App.__init__` constructs one Store, DeviceRegistry, Controls, Archive, VoiceEngine, LocalSTT, Spotify and ShadowObserver, then WakeDetector. `workspaces.setup` uses that Store. | Reuse these actual implementations. There is no separate class called ProviderManager to duplicate. Module-level provider functions and App-owned provider state form the current provider boundary. |
| Data opening | `store.py:Store.__init__` makes a missing directory/database and applies schema setup. | Stage 4 must validate identity/schema/existence under the lifetime lock before opening real Store. Provisioning must be separate; `--data-dir` is not sufficient. |
| Configuration/source roots | Importing `server.py` calls `load_env()` against source `.env`. App uses `ROOT/data` for STT/wake models; development tools refer to `ROOT`. | Explicit TEST configuration and dependency isolation is required before importing/constructing App. Do not inherit production keys or expose real development actions through a TEST UI. |
| Authorization and sessions | `Handler.allowed` validates desktop token, localhost Host/Origin and one global App session cookie. Runs have no authenticated client principal. `/api/cancel` selects a run by ID. | Existing action authorization must remain authoritative, but TEST transport identity must be bound to request ownership and scopes. Authentication is not permission to execute tools. |
| Shutdown and stdin | Ordinary authenticated `/api/shutdown` cancels runs and calls server shutdown. With desktop token set, stdin EOF also cancels runs and shuts down. `Server.daemon_threads=True`; App work threads are daemon threads without retained join handles. | Existing main cannot serve as the independent entry unchanged. Explicit admission/drain/stop ownership must precede lock-last teardown. |
| Voice/wake/capture | One App VoiceEngine performs provider synthesis. Renderer `JarvisVoice` owns conversation/arming/recovery state and hardware capture. Core WakeDetector has one `client/last/triggered` state; the client ID comes from the request body. A different recent client is rejected. | Preserve one VoiceEngine and wake owner. Authenticated media ownership is missing. Do not infer Core-owned multi-client orchestration from a single TTS object. |
| Devices | App constructs an in-memory registry and registers PC capabilities. Runs are sourced as PC or wearable, not authenticated Electron client identity. | Reuse the registry; remote/client presence must be established by fresh attachment and removed per session. No new physical device work. |
| Workspace/budgets | `workspaces.py` and `project_budgets.py` operate on the supplied Store. | Reuse their persistence and conservative recovery semantics. A client session or available reservation must not grant execution authority. |
| Repair/inspection | Repair dispatch uses existing App/Store/service, explicit confirmation and budget state. It has its own cancellation event. Module-level inspection jobs have their own daemon workers. | Do not run repairs. A lifecycle drain must account for these owners instead of only iterating App.runs; preserve uncertain charges. |
| Discovery | Desktop writes `.jarvis-session.json`. Wearable `publish_connection` creates a Service on the same App and writes its descriptor only when Store root equals the source live-data directory. | Retain that existing TEST-data safeguard. Do not use either production descriptor for Stage 4 canonical trust. Stage 2 bootstrap remains isolated test machinery. |
| Shared versus visual state | Canonical settings/data use Store; desktop preferences and renderer navigation/capture state belong to clients. | Keep window/navigation state local. Do not reset shared data when a client disconnects. |

## Blockers and minimum proposed changes

### B1 — authenticated client and voice ownership

**Exact issue:** Core Run has no authenticated principal; the microphone ID is caller-supplied; renderer voice control and desktop global stop assume a single desktop owner. Closing client A currently has a path to cancel unrelated Core work. Merely retaining the Python process or changing the transport would leave that ownership mismatch.

**Affected boundary:** renderer capture/output, Core voice orchestration, session revocation and request cancellation.

**Proposed minimum for review:** Introduce one Core-owned authenticated client context with epoch-bound media leases and run ownership, used by both TEST adapters. Keep existing VoiceEngine and WakeDetector; define single active wake-stream arbitration explicitly. Scope client close/crash to that client's grants/work. Model A/B media leases without enabling hardware, as the brief allows; do not claim a modeled lease proves real concurrent microphone behavior. Define which existing renderer conversation decisions must move to Core versus remain local presentation/capture behavior before implementing that change.

**Risk:** Partial migration can leave two orchestration authorities, cross-client cancellation, stale grants after restart, or a new route around existing tool authorization. This requires a reviewed cross-layer contract, not an additional voice implementation.

### B2 — lifecycle shutdown is not yet a managed drain

**Exact issue:** App exposes no lifecycle admission/drain contract covering runs, inspection, repair and synthesis. Ordinary session authentication reaches `/api/shutdown`; current shutdown signals Run events and closes the server. That is not evidence that in-flight owners have finished before lifetime-lock release.

**Affected boundary:** management authority versus ordinary clients; asynchronous work versus Store/lifetime-lock ownership.

**Proposed minimum for review:** Add a TEST lifecycle host with separately authorized management operations, stop intent, admission closure and tracked draining. On uncertainty preserve charged/recovery-required state and fail closed. Revoke epoch sessions, close listeners and release the lifetime lock only after managed teardown. Keep the production legacy startup/shutdown path intact. Do not treat Stage 2's authorization-only `lifecycle_executed:false` fixture response as a real shutdown implementation.

**Risk:** Releasing ownership while work can still write permits overlapping writers; global cancellation or guessed refunds can destroy the economic/recovery boundary.

### B3 — isolation prerequisite

Source `.env` loading at import, hardcoded source/model roots and Store's create-if-missing constructor require an explicit isolated runtime boundary. This is not independently evidence that isolation is impossible. Validate a pre-provisioned TEST identity before App/Store construction, supply sanitized fixture dependencies, and prevent source-root actions/provider calls. A copied or substitute Core must not be used to conceal missing ownership integration.

## Review decision requested

Review B1/B2's explicit client-ownership and lifecycle-drain contracts before implementation. The existing authorization already covers isolated Stage 4 work; the reason for this pause is the brief's additional review gate for a change to the real voice/ownership architecture. No production cutover or future-feature authorization is being requested.

After review, implement these contracts only in the isolated Stage 4 path, compose unchanged Stage 1 exclusion and Stage 2 authenticated identity, reuse real App/Store components, then attach the actual Electron clients. Avoid changing accepted Stage 1 semantics to obtain a pass.

## Required proof after review — not run

All 47 Stage 4 matrix cases remain **NOT RUN**. In particular:

1. Lifetime lock precedes App/Store; missing/wrong TEST identity fails without creating data; concurrent starts have one owner.
2. Both real clients attach to the same instance/data/App; closing/crashing either or both and stdin EOF do not stop Core.
3. A cannot cancel B or revoke B's media lease; no duplicated voice/provider owner or observation-triggered provider call; no hardware capture enabled for a model-only test.
4. Ordinary sessions cannot stop Core; authorized stop closes admission, drains, preserves uncertain budget state and releases ownership last.
5. Coordinator loss preserves Core; Core crash releases the OS lock; replacement has a new epoch with the same TEST Store; old sessions/grants fail, no request replay/refund.
6. Shared synthetic conversation/project/task/budget state is visible through both clients; remote presence is empty after restart.
7. Failure injection covers drain boundaries and permission/identity uncertainty. Repeat races; retain every failure.
8. Rerun unchanged Stages 1–3, Stage 4 suite, affected production/desktop/Intelligence tests and syntax checks. Manual TEST Electron verification must be reported separately.

No runtime regressions were run in this audit because implementation stopped at the review gate. Prior accepted counts are historical, not new results.

## Retained Stage 1 finding

Classification remains **ROOT CAUSE UNCONFIRMED / FAIL-SAFE / REVIEW REQUIRED**.

The Stage 3 record identifies Core PID 7184, replacement coordinator PID 6844 and namespace `TEST-02363806196549c7ba7c0067af9fad43`. The recorded exception is PermissionError, errno 13; an exact Windows error code was not recorded. Replacement of a temporary `response.json` file is an inference from the remaining complete temporary file, not a proven stack trace. Concurrent reader/filter interference remains plausible; antivirus causation is not established.

The retained evidence records uncertain identity → RECOVERY_REQUIRED → no replacement spawn/no second ownership. Later passing runs do not erase the failure. No Stage 1 code or evidence was modified here. It was not reproduced or newly verified during this audit. Review `docs/lifecycle-stage3-evidence/stage1-permission-investigation.json` and the retained failed-run records.

## Production boundary and final status

The source-default database candidate was examined by file metadata only. No SQLite connection was opened. Live production database provenance and before/after database content integrity are **UNVERIFIED**. The process inventory attempt using `Get-CimInstance Win32_Process` returned **Access denied**; no elevation, process termination or restart was attempted. No credential/configuration contents were read. No claim is made that an independently running application could not write its own data during this audit.

| Stage | Status |
|---|---|
| 0 — Architecture | Previously approved; unchanged |
| 1 — Ownership/exclusion | Prior accepted tested scope; unresolved fail-safe review item retained |
| 2 — Isolated authentication | Prior 35 passed / 1 skipped; not rerun |
| 3 — Data/migration rehearsal | Prior 43 passed; commit efad41c and verified archive unchanged; not rerun |
| 4 — Real isolated integration | BLOCKED FOR REVIEW; not implemented or accepted |

Actions performed by this task:

- PRODUCTION DATABASE MOVED: NO
- PRODUCTION DATABASE MODIFIED: NO
- PRODUCTION CORE RESTARTED: NO
- PRODUCTION CONFIGURATION CHANGED: NO
- PRODUCTION AUTHENTICATION/LIFECYCLE CHANGED: NO
- STAGE 5 STARTED: NO
- ADDITIONAL CORE STARTED: NO

Stopped for review. ONE JARVIS remains the governing architecture.
