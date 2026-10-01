# Canonical JARVIS Core ownership and client attachment

11 September 2026 — COMPLETE PROPOSAL / REVIEW REQUIRED — lifecycle direction approved

No runtime implementation, installation, data migration, provider change or production restart was performed. The only changes in this milestone are this document and its records copy. Existing dirty source changes predate this audit and were not reverted or included as completed work.

## Evidence and confidence

OBSERVED means read from the current working tree; VERIFIED means a specific live read-only observation. PROPOSED is not implemented. ASSUMED items require validation before activation. No secret values, conversation contents or database rows were printed.

The source root below means C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis.

### Current lifecycle map — OBSERVED

Start-Desktop.ps1 -> desktop Electron -> application-specific single-instance lock -> desktop/backend.cjs -> .venv/Scripts/python.exe server.py --port 0 -> server.App -> canonical Store, providers, voice, wake, device registry, authorization and workspaces.

desktop/main.cjs always calls startBackend; it does not start-or-attach to an independently owned Core. backend.cjs generates a random desktop token and supplies it through the child's environment. It parses localhost readiness from stdout. Port 0 requests an OS-selected port; server.main otherwise defaults to JARVIS_PORT or 8765, and always binds 127.0.0.1.

Close-window hides to tray and stops activity. Quit closes watchers, stops activity, sends quit through child stdin, waits up to four seconds and kills its owned child if needed; session metadata is removed. Server stdin EOF also initiates shutdown. Renderer failure stops activity and displays an error. Backend exit quits the client. Startup readiness has a 90-second timeout. Source updates can relaunch the entire owning desktop/backend. These semantics bind Core lifetime to one client, even if other clients still need it.

VERIFIED process observation: Electron PID 22272 was the parent of venv Python PID 21712, itself parent of runtime Python PID 22540. Multiple Electron child processes were also present. This is a single observed launch tree; a Python launcher/runtime chain is not proof of two Core instances. No process was terminated. Listener ownership and live in-process App count were not independently verified. Initial restricted process inspection was denied; an approved read-only inspection succeeded without exposing command lines.

### Current storage and ownership map — OBSERVED unless stated

| Concern | Current owner/location | Limitation |
|---|---|---|
| SQLite, memory, conversations, tasks, settings | App.store; source data/jarvis.sqlite3 through Store | Store creates missing directory/database; no missing-canonical-data refusal |
| Projects, task links, budgets | Same Store, workspaces.py and project_budgets.py | No separate client ledger; budget availability is not execution authorization |
| Database presence | VERIFIED source data/jarvis.sqlite3 exists, 688128 bytes at inspection | File size is not data identity/integrity verification; active --data-dir was not independently established |
| Frozen data | server.py can use executable APP_ROOT/data | Can silently diverge from source data |
| Personality | Core reads source personality.txt; user settings/memory in Store | User-modified personality must be inventoried and preserved, not replaced with a package default |
| Provider configuration/secrets | Core process environment; server.load_env reads APP_ROOT/.env | Existing environment takes precedence; installed resources must not contain production secrets |
| Desktop preferences | desktop/preferences.json | Mixes microphone/capture policy with UI settings; requires deliberate ownership split |
| Desktop discovery | desktop/.jarvis-session.json with origin, bearer token, timestamp | No canonical epoch/protocol validation or independently reviewed per-client expiry |
| Wearable bridge | Core-owned Service, .env.wearable-connection.json for source data only | Shared bridge token; file is not a process-exclusion mechanism; cleanup checks its own token |
| Device/capability presence | App.devices, in-memory dictionaries and TTLs | Ephemeral presence must be re-established, not migrated as live connectivity |
| Runs, approvals, captures | App memory / desktop capture session | Active execution and permission grants must not be resurrected after restart |
| Shadow telemetry | Store root/provider-shadow.jsonl and rotated sibling | Preserve Phase 1 shadow-only behavior and appropriate telemetry |
| Generated files, recovery/history | Store root/generated; recovery uses source and data paths, source sibling jarvis-backups | Inventory approved artifacts outside SQLite; SQLite export alone is insufficient |
| Repair records | Budget rows plus existing report artifacts; current experiment runtime state can be ephemeral | Do not promise persistence for records currently only held in memory |

Current desktop API requires its environment token when configured, exact Host, acceptable Origin/fetch-site, and an App session cookie for API routes. Bare server mode can issue a browser session without the desktop-token requirement. Preserve existing behavior now; the proposed canonical production entry point must refuse tokenless production startup rather than silently inheriting bare-server mode. Wearable authentication is a separate bounded interface, not a general client/admin credential.

### JARVIS Intelligence — OBSERVED

intelligence/main.cjs reads desktop/.jarvis-session.json, injects the desktop bearer header, and loads /intelligence.html; it falls back to its local page. No Python spawn, Store creation, direct provider client or TTS service appears in this entry point. It shares the current desktop's credential and has no authenticated canonical handshake. Its URL prefix comparison is weaker than desktop/policy.cjs exact parsed-origin comparison. Its navigation/redirect and fallback behavior need security tests before being treated as a trusted production attachment. This audit does not certify every renderer action as safe. No Intelligence code was changed or launched.

Existing tests include desktop/test/backend.test.cjs (owned isolated backend auth/readiness/shutdown), policy.test.cjs, local-updates.test.cjs, capture.test.cjs and inspection-job.test.cjs, plus Python Store, wearable, registry, budget, repair, authorization-related and shadow tests. None establish a cross-application canonical startup lock, shared shutdown ownership or source/installed coexistence. No regression suite was run for this documentation-only milestone; past totals are not fresh evidence.

## Exact duplication risks

1. Different Electron application identities can each pass their own UI lock and spawn a backend on different ephemeral ports.
2. Multiple backends pointed at one SQLite file still duplicate voice, providers, approvals, registry and lifecycle ownership. SQLite locking is not a Core lock.
3. Copied/frozen source defaults can initialize a second empty database; relative .env/personality paths can create inconsistent configuration.
4. Shared discovery files can be overwritten; stale tokens/ports do not prove identity. A health response or PID alone is insufficient.
5. Closing the original desktop currently shuts down a backend on which another client depends.
6. A legacy launcher can bypass a newly introduced client-only protocol. All production startup paths must be gated before coexistence is enabled.

## Ownership options — PROPOSED

| Option | Benefits | Risks/privileges | Upgrade and development | Recovery and shutdown | Installer impact |
|---|---|---|---|---|---|
| Retain desktop as owner, attach other clients | Smallest change | No admin; owner UI remains a dependency | Owner must coordinate restart | Owner crash/quit affects everyone | Cannot meet requested independent lifetime fully |
| Per-user Core host independent of UIs (recommended) | One runtime owner; existing Core internals retained; no always-on system service | No intended elevation; new local IPC, lifetime lock and stop controls require review | One selected runtime, clients attach; explicit maintenance restart | Host owns bounded recovery and explicit shutdown | Separate runtime/client packaging later; user data outside binaries |
| Windows Service owning Core | OS-managed start/recovery | Service registration/admin; session/audio/desktop interactions become more complex | Coordinated service upgrade | SCM controls lifetime; interactive device bridge needed | Highest complexity and privilege requirements; not recommended now |

Recommend ONE per-user lifecycle coordinator/supervisor and ONE canonical Core for the approved Windows account. The supervisor is only a process/lifecycle controller: no App, Store, AI, personality, voice, device registry or budget ledger. The Core remains the sole owner of those systems. Start on explicit client launch; no logon task or Windows Service is introduced in this milestone. The approved direction makes Core lifetime independent of every UI.

## Start-or-attach protocol — PROPOSED

1. Read a protected canonical configuration identifying this user's installation/data identity and selected runtime. Never choose a runtime based on which client launched first, cwd or newest timestamp.
2. Contact a protected local bootstrap endpoint. Validate its OS process identity, current user, approved runtime provenance and protocol, then obtain a client-scoped session. Discovery JSON is a hint only, not authentication.
3. If a healthy, compatible production Core exists, attach to that same instance; no App constructor in any client.
4. If discovery is absent/unavailable, clients invoke the approved coordinator bootstrap. Coordinator contenders acquire one OS-enforced supervisor lifetime lock before any Core startup decision. The winner examines the independent Core lifetime lock and authenticated process identity. It may spawn one selected Core only after verified absence; losers wait for authenticated coordinator readiness and never spawn Core. The Core acquires its own lifetime lock BEFORE binding or creating Store/voice/providers. This second lock prevents replacement coordinators from duplicating a surviving Core.
5. The host holds that lock for its entire life. A second lock owned only by the UI or a timestamp lease is insufficient. Handle ownership, no accidental inheritance, directory/reparse-point validation and cross-session behavior must be tested. Never remove a lock file to break an active lock.
6. Wait boundedly (proposed 90-second readiness deadline with bounded backoff). Publish an atomic, credential-free descriptor only after identity/data checks and required readiness succeed. Healthy means database identity/schema and auth available; optional voice/provider failure is separately reported as degraded.
7. Host presents persistent installation/data identity, random per-start core_instance_id, startup_epoch, PID plus process creation time, runtime/build identity, production/test mode and protocol compatibility. Client checks the complete authenticated handshake, not only PID or port.
8. If startup is blocked, incompatible, ambiguous or an unknown listener owns the endpoint, fail closed and report diagnostics. Do not fall back to a different port/data location/Core. No automatic takeover of the legacy desktop-owned runtime.

An exclusive user-profile file is a candidate cross-session mechanism; Windows implementation semantics and crash release must be proven before adoption. Microsoft explicitly documents profile-file locking as a per-user alternative and warns against relying on an unprotected predictable named mutex. [CreateMutexW](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-createmutexw).

## Authentication and local transport — PROPOSED

Keep data APIs on 127.0.0.1 only. Bootstrap through a local named pipe with explicit current-user access controls, remote access rejected, bounded messages, peer process verification and a reviewed client-enrollment policy. Do not grant every same-user process authority just because it supplies a client name. Registered executable/build identity and explicit enrollment approve client scopes; source builds require a deliberately approved development identity. Same-user malware/admin compromise is outside a perfect application isolation guarantee and must not be disguised as solved by an ACL.

Clients must authenticate the pipe server before sending credentials. Bootstrap creates short-lived per-client bearer tokens in native client memory (proposed 15-minute expiry, renewal over authenticated bootstrap), scoped to instance, epoch and permissions. Do not put tokens in descriptor files, renderer storage, logs or bundles. Issue a separate Core-stop/admin scope only to an explicit user control; ordinary clients cannot stop Core. Revoke on client detach where applicable, instance restart and user revocation. Protocol changes retain existing Host/Origin/CSRF protections, bounded requests and approval checks. Check exact parsed origins before attaching headers, including redirects.

Default pipe ACLs are not enough: Microsoft documents broader default read access and provides explicit access-control guidance. No IPC ACL or security policy was modified here. [Named pipe security](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-security-and-access-rights).

## Canonical data proposal — PROPOSED, approval required

Target base: %LOCALAPPDATA%\Teague Industries\JARVIS (resolve the Windows known folder, not a hard-coded username).

- data/: ONE jarvis.sqlite3 plus approved persistent artifacts.
- config/: canonical runtime selection, installation/data identity and nonsecret Core configuration; approved personality configuration/reference preserving current content.
- secrets/: explicitly protected, user-bound secret storage; evaluate Windows-protected storage before implementation. Never packaged or copied into source-record exports.
- runtime/: lock and credential-free discovery metadata; ephemeral, not backed up as active sessions.
- logs/ and cache/: separated with retention limits; no tokens/raw provider credentials.
- clients/<client-id>/: UI-only state. Core owns permissions, voice configuration and shared preferences; retain per-client presentation settings only.

Source and installed clients resolve the same approved configuration. Before migration, the design may explicitly pin the current verified data location rather than move it, but only after live path/identity verification. This audit confirms the source default/file exists, not that an arbitrary matching file is authoritative. No production bootstrap or migration is permitted until the actual live path and identity are positively verified. Missing or conflicting canonical data means an error, never silent empty creation. First-ever provisioning must be a separate explicit flow.

## Migration and rollback plan — PROPOSED

1. Inventory active Core, actual open database path, runtime arguments, schema/tables, external artifacts, personality edits, preferences and secret references without printing secrets. Resolve any competing data folders manually; do not merge by recency.
2. Approve source and destination identities. Create a consistent SQLite backup using the SQLite backup mechanism with a controlled snapshot boundary; never copy only the main file while WAL writes continue. Back up external mutable records at a matching quiescent boundary. Keep secrets separately protected, outside general records snapshots.
3. Test using explicitly labelled isolated copies first: integrity_check, foreign_key_check where applicable, schema inventory and logical row/content checksums/counts. Include all tables: memory, conversations, settings, projects/tasks, budgets and recovery records. user_version=1 alone is insufficient because Store currently sets it while creating additive tables.
4. Rehearse copy into a new staging directory, verify artifacts/preferences/personality and schema compatibility, then approved atomic configuration cutover on the destination volume. Never expose a partly copied canonical folder. Use an explicit migration journal.
5. During real cutover: stop new work, drain/cancel safely, reconcile uncertain reservations without refunds or retries, shut down the legacy owner, verify it exited, and activate exactly one new host. Legacy launchers must no longer create their own App before they can be used again. This is a coordinated maintenance change, not part of this audit.
6. Retain original files and verified backup; no automatic cleanup. If startup fails before new writes, stop the new host and atomically restore the prior runtime/data mapping, ensuring only one owner. After new writes, do not restore an old snapshot blindly: preserve new evidence and require a tested backward-compatible runtime or explicit reverse migration. Never roll back to an unsupported schema or silently lose new conversations.

## Lifecycle and recovery policy — PROPOSED

| Event | Required result |
|---|---|
| Window close | Detach/hide UI; revoke its capture/microphone session and cancel only its owned work as policy requires; no global Core quit |
| One client quits/crashes | Its session expires, its device presence becomes unavailable; other clients retain same Core |
| Last client quits | Core remains under explicit supervisor lifecycle control. No automatic shutdown merely because client count reaches zero; capture permissions still expire. No new background work is authorized by keeping the process alive. |
| Manual Core shutdown | User-authorized lifecycle control not a generic model tool; stop new requests, drain/cancel, preserve uncertain reservations, revoke tokens, close listeners, release lock last |
| Logout/Windows shutdown | Bounded graceful stop; crash-consistent persistent state if deadline exceeded; transient grants never resumed |
| Core crash | OS releases lifetime lock; new explicit client attempt may start selected runtime only after absence is proven; bounded recovery, proposed max 3 failures/5 minutes then intervention |
| Startup client dies | Host lock ownership survives if host is alive; other clients wait/attach. If host dies, startup can be retried after identity/absence checks |
| Stale metadata/token or port reuse | Reject attachment; cleanup only metadata proven to belong to dead instance; never kill unknown listener |
| Partial startup | No healthy descriptor; retain exclusion while alive; timeout reports failure rather than launching alternate Core |
| Upgrade/development restart | Explicit maintenance, notify all clients, block new work, verify candidate, drain, stop old host, select approved runtime, start/reattach; new instance ID, same data ID |

No automatic replay of tool calls, paid requests, purchases or repairs after crashes. Durable operation identities and existing budget recovery_required states survive; no refund solely because time passed. Current single-user request limits and permission semantics remain until separately reviewed. Moving microphones to shared clients also requires exclusive capture ownership and request-scoped stop/voice arbitration; simply leaving today's global stop behavior would break other clients.

## Source, installed and test coexistence — PROPOSED

Both production clients attach to the selected canonical runtime regardless of their own source location/version. Protocol mismatch displays an actionable compatibility error; it never starts an alternate Core. A development client edit must not silently hot-reload canonical backend code. Core code changes require an explicit reviewed runtime switch/restart. Old builds and launchers are retained for rollback but must be fenced from production starts during cutover; unknown legacy runtime detected means stop, not takeover.

Tests require explicit test mode AND isolated data AND random test namespace AND no production credentials by default. Test ports, identities, bootstrap scope and discovery are separate; production clients reject test mode even when protocol-compatible. Test helpers must not overwrite either existing discovery file. Require explicit opt-in for any live provider test. Disposable repair containers retain no Core, memory, credentials or provider manager.

## Release manifest — PROPOSED

Fields: application_id, client_version, core_version, build_id, git_commit, dirty_worktree, source_manifest_sha256, core_protocol_min/max, client_protocol_min/max, data_schema_current/min/max, runtime_mode, runtime_artifact_sha256, platform/architecture. Runtime status separately reports core_instance_id, startup_epoch, opaque data identity and negotiated protocol. Never claim a clean Git build while uncommitted changes exist. No secrets, DB contents or tokens. Installation manifest and authenticated runtime identity must agree. Exposing this in Teague System is future UI work.

## Files likely to change after approval

- New lifecycle/bootstrap module and test harness; canonical config/identity and migration tooling, protocol schemas and release manifest generator.
- server.py: canonical startup before App/Store; mandatory production auth, readiness/identity, lifecycle and request/client ownership integration.
- store.py: explicit canonical open-vs-provision distinction and real schema validation; preserve memory semantics.
- desktop/backend.cjs and main.cjs: attach/start coordination, no direct per-client backend ownership, client-specific shutdown/auth/preferences/update behavior.
- intelligence/main.cjs: canonical attachment, exact-origin credential protection, navigation restrictions and compatibility handling.
- wearables/service.py and real_core.py: canonical discovery/identity while keeping existing bounded media/tool contracts.
- Start-Desktop.ps1, desktop_launcher.py and build entry points: eventually participate in approved launch protocol; unchanged now.
- local-updates.cjs, recovery.py and source-relative resource/config consumers: distinguish client updates, canonical runtime updates and user data.
- Documentation/tests for each boundary. No provider-routing, Ollama Phase 2, personality redesign, alternate budget ledger or production repair activation.

## Test matrix and installer gate

All following are REQUIRED / NOT RUN for the proposed architecture:

1. A starts, B attaches: same instance/data identity; one App initialization and one listener owner.
2. Many simultaneous processes across source/installed clients: one initialization; losers only attach. Test process crashes at every startup boundary, not merely threads.
3. Close/quit/crash A while B continues; validate scoped cancellation, microphone release and unchanged Core identity.
4. All clients detach: grace/background-obligation policy; explicit authorized shutdown; unauthorized stop rejected.
5. Kill Core/startup owner, reuse PID/port, stale/partial descriptor, lock held/abandoned, access-denied lock, reparse path, unknown listener: fail closed; no duplicated Core, blind refund or replay.
6. Invalid/expired/revoked/wrong-instance tokens, wrong origin, redirects, unregistered client, wrong pipe peer, other user/remote connection: denied; secrets absent from logs/renderer/distribution.
7. Source and installed clients in either launch order attach to selected runtime; incompatible versions and old launchers cannot silently spawn alternatives.
8. Test mode cannot attach to production or publish production discovery; tests use isolated data and credential-free fixtures.
9. Migration/upgrade/rollback using copies: preserve all rows/artifacts/preferences/personality, schema compatibility, interrupted copy and post-cutover writes; missing/ambiguous source aborts.
10. Simulate Windows-session termination and restart where possible; later real logout/reboot validation separately labelled.
11. Full current Python and desktop regressions plus targeted authorization, voice, memory, provider shadow, budgets, repair isolation and client ownership tests. Real audio/device checks distinguished from deterministic tests.
12. Ollama remains shadow-only, providers stay Core-owned, reservations remain canonical and uncertain after crashes, repair containers remain disposable with no production deployment.

Installer gate: approved ownership design; approved data location; implemented/tested start-or-attach, concurrent exclusion, authentication, crash recovery, source/installed coexistence; isolated migration and rollback verified; existing regressions passed; Ollama shadow, shared budgets and repair isolation preserved. Every item must have evidence before building any installer. Signing/distribution purchases, firewall changes and update servers remain outside this milestone.

## Review decision

## Detailed coordinator contract following the approved direction

```
Teague client / Intelligence client / future client
                 |
        validated local bootstrap
                 |
   ONE lifecycle coordinator (no intelligence)
                 |
          ONE JARVIS Core
                 |
       ONE canonical Store/config
```

### Startup exclusion and system scope

Use two separate lifetime locks in a stable protected location under the approved Windows user's LocalAppData, outside versioned runtime and data migration directories: supervisor.lock and core.lock. Both are OS-held exclusive handles, not existence checks or expiring leases. All source, installed and legacy production entry points must use the same locations. Locks survive client termination and are released by owner termination; the Core holds its lock independently of the supervisor. Never inherit lock handles into subprocesses.

This provides exclusion across applications and sessions for the approved Windows account on this PC. It does NOT silently create a Core for each other account. Production bootstrap from an unconfigured/different account must refuse activation. Machine-wide multi-user access would require a separately approved broker/service and access model; it is not solved by using a Global mutex name. Fast-user-switching and same-user multiple-session tests are mandatory. Namespace, file identity and ACL failures are fatal, never reasons to choose an alternate lock.

Coordinator state machine: STOPPED -> STARTING -> READY/DEGRADED -> DRAINING -> STOPPED, with explicit FAILED and RECOVERY_REQUIRED states. A lifecycle operation has a stable operation ID and requested runtime identity. Persist a small atomic lifecycle journal with intent and outcome, without copying the business database or budget ledger. Repeated operation IDs return existing outcomes, not repeated restart/upgrade actions. An explicit Core shutdown records a stop latch; background reconnect cannot undo it. A fresh explicit user launch/start may clear it under the approved lifecycle policy.

Coordinator serializes startup, shutdown, maintenance and upgrade. Client attachment is not permission to install/select a new runtime. STARTING waits are bounded; optional provider or audio unavailability gives DEGRADED, not replacement-Core startup. Current public readiness must be extended to distinguish authenticated lifecycle readiness from capability readiness.

### Supervisor loss, adoption and split-brain prevention

The Core must no longer shut down on UI stdin EOF. Its future control channel belongs to the lifecycle protocol, not any client. Supervisor loss leaves a healthy Core alive with its lifetime lock held. It does not leave unrestricted recording running: client capture leases remain independent and expire.

A replacement coordinator acquires supervisor.lock, then authenticates the surviving Core using the protected control endpoint, installation/data identity, instance epoch, expected executable/build and OS process creation identity. If all agree, adopt supervision without constructing App or reopening Store. If Core identity is uncertain, report RECOVERY_REQUIRED and start nothing. Failure to contact an existing locked Core is not proof that it is dead. Hung Core termination must target a verified process handle through an explicit recovery operation; never kill a PID from stale JSON.

If no Core exists and core.lock can be obtained as an absence check, the coordinator releases that check handle and launches the configured runtime; only this single coordinator may initiate launch, and the new Core must independently acquire core.lock before initialization. Any unexpected contender winning in that interval blocks startup and triggers identity reconciliation. The release/launch interval therefore cannot authorize two App initializations.

Proposed automatic recovery is bounded to three verified crash restarts within five minutes while supervision is active, then FAILED requiring user action. Each restart gets a new epoch and requires clients to renew authentication. Never replay commands, restore capture grants, approve tools or settle uncertain reservations during recovery. An explicit shutdown, upgrade or logout suppresses crash-restart policy. Coordinator crash recovery begins on an explicit client reconnect/start; no extra watchdog process or scheduled task is installed in this stage.

### Identity, bootstrap and client scopes

Persistent installation_id and data_id are opaque identifiers established only after positive canonical source verification. Neither is an API secret or a substitute for authentication. A Core instance adds random core_instance_id, startup_epoch, process creation time and selected runtime digest. Health responses include negotiated protocol and schema compatibility and are only trusted after bootstrap authentication.

The local pipe/control channel is a narrowly scoped lifecycle interface, not a shell or arbitrary process launcher. It permits fixed operations: discover, attach/renew/revoke own session, status, and separately authorized start/stop/restart/maintenance. Clients cannot supply arbitrary Python paths, data directories or environment variables. Runtime selection comes from the approved configuration. Verify both client and server OS identities, restrict pipe access, prohibit remote access and constrain impersonation to identity inspection. Implementation must have tests against pipe spoofing before transmitting session credentials.

Proposed scopes separate normal application attachment, device media, lifecycle management and explicitly labelled test access. Per-client credentials do not grant tool authority: existing Core authorization remains decisive. Desktop/Intelligence renderers receive no provider secrets, supervisor tokens or unrestricted lifecycle bridge. Enrolling an unsigned development executable is explicit and hash/version-bound; a claimed application_id alone is never trusted. Changes to approved executable hashes need review/reenrollment. User-writable source and same-user malware remain material trust limitations, not cryptographically trustworthy software identity.

### Persistent and ephemeral devices

After every Core startup the live registry begins with NO authenticated remote/client device ONLINE status. Any local PC capabilities must be probed before marked ready. Clients reconnect, authenticate to the new epoch, register allowed capabilities and renew heartbeat leases. Only fresh validation sets readiness. Previously stored identity, user preferences and approved device configuration may be reused; recording grants, connected flags and in-flight capability leases may not.

Device ID is stable; connection/session ID changes. Duplicate sessions for the same device need an explicit replacement policy; the old session cannot publish stale readiness into the new epoch. Disconnect removes readiness and the device's request association without taking the Core offline. Microphone/speaker selection is Core-orchestrated; clients implement hardware access, not additional voice engines or provider managers. Loss of one UI cancels/revokes its capture, not another client's authorized request.

### Upgrade and source development rules

Installed UI upgrades can attach without restarting a compatible Core. Core upgrades require a serialized maintenance operation: verify artifact and compatibility, announce downtime, block new execution, settle known operations, retain uncertain ones, make verified backup, stop old Core, confirm lifetime-lock release, select new runtime, start one Core and verify the same data identity. No blue/green parallel production Core. Unknown shutdown outcome prevents starting the replacement.

Source-mode production clients use the selected canonical runtime just like installed clients. Editing source does not change running canonical backend authority. A reviewed development runtime can be selected explicitly for the one production Core only during maintenance. Ordinary test development uses isolated fixtures with distinct identities, credentials and directories; it cannot register as production even if the UI looks identical. No automatic source-to-installed data copying on launch.

Rollback covers three boundaries: before data cutover (discard only staging after review), after cutover with no new writes (restore verified mapping), and after new writes/schema changes (retain current data and use tested compatible downgrade or explicit reverse migration). Never silently restore an older backup over newer memory/budget state. Existing source/shortcut rollback is safe only after the new host has fully stopped and the older startup path is deliberately selected again. Backup presence alone is not rollback verification.

### Ordered implementation stages — all future, none started

| Stage | Deliverable | Exit evidence |
|---|---|---|
| 0 | Approve this protocol, account scope, data destination and lifecycle controls | Reviewed decisions; no runtime changes |
| 1 | Credential-free test harness for coordinator/Core locks and identity | Multi-process races, crash injection and cross-session exclusion pass; no production App |
| 2 | Bootstrap authentication, scopes, revocation and manifests in isolated tests | Wrong listener, spoofed pipe, expired token, protocol mismatch and redirect tests pass |
| 3 | Canonical configuration/open-existing guard plus migration rehearsal tooling | Missing data refuses startup; consistent backup, full schema/record/artifact checks and all rollback boundaries tested using temporary copies |
| 4 | Lifecycle-independent Core entry and both client adapters in isolated mode | One App/Store/provider/voice/registry owner; closing clients preserves Core; stop controls and fresh presence pass |
| 5 | Full regression and fault matrix, source/installed-layout simulations | Deterministic unit/integration tests separated from opt-in live provider/audio tests; no installer required for layout simulation |
| 6 | Separately approved production cutover | Verified canonical path, backup, fenced legacy launchers, one live Core and post-cutover user checks |
| 7 | Re-evaluate installer gate | Every gate evidenced before packaging begins |

Stage 3 must include interrupted backup/copy, WAL consistency, disk-full, destination identity mismatch, schema mismatch, invalid permissions, existing nonempty destination, new-write rollback and corrupt budget reservation fixtures. Compare all tables and external artifacts, not only messages/items. Tests must never call Store against production merely to discover its location. Before any production copy, obtain active data identity via a reviewed read-only runtime diagnostic and match it to on-disk provenance.

Fault tests inject coordinator death before/after lock acquisition, after spawn/before handshake and after descriptor publication; Core death before/after Store initialization; client death during authentication; stale PID/port reuse; simultaneous restart and stop; Windows shutdown intent versus crash policy; descriptor truncation; concurrent version mismatch; detached-device reconnect with stale epoch. Assert one Core initialization, no duplicate provider calls, no unauthorized refund/replay and no live device restored without a new lease.

### Remaining risks and present verification limits

No migration or rollback test was executed in this design-only phase. This is the concrete plan for producing that evidence, not a claim that migration is already safe. No new architectural regression suite was executed because the architecture is not implemented. Existing user-reported desktop keyboard PASS remains separate UI evidence.

Key unresolved engineering risks: secure local enrollment for unsigned source applications; same-user process trust; Windows handle inheritance and process-tree shutdown; legacy launch paths bypassing exclusion; canonical data provenance; additive schema tracking; source-relative personality/assets/recovery paths; global stop behavior becoming incorrectly shared; microphone ownership across clients; crash reconciliation of paid/repair operations; preserving reminders without implicitly enabling autonomy; and data-safe downgrade after new writes. Each has a corresponding gate above rather than an assumed solution.

The proposal is ready for review. No installer, runtime code, production data, Windows Service/task, firewall rule, additional provider or alternate JARVIS has been created.

The user approved lifecycle independence, client attachment, ephemeral device presence, canonical data design without migration, canonical authentication and source/installed identity separation. The following detailed design completes that direction and awaits review. No runtime implementation is authorized by this deliverable. Production migration requires separately reviewed test evidence and cutover approval.

