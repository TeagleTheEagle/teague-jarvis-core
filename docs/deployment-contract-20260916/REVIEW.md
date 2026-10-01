# DEPLOYMENT / BOOTSTRAP / ENROLLMENT CONTRACT REVIEW

16 September 2026, Australia/Sydney. **REVIEW REQUIRED before changing the deployment trust boundary.** Stage 4 remains CLOSED for TEST acceptance; Stage 5 isolated validation remains PASS. This document proposes a contract; it does not certify an installable release.

**Result:** 16 read-only preflight checks passed; all 31 accepted source/executable hashes still match. No relocated Core, package, installer, enrollment, update or clean-machine restore was executed. Existing source deliberately rejects an independently located TEST state root. Changing that binding and replacing fixture-owned credentials with durable enrollment require the review expressly required by the mission.

ONE JARVIS. ONE CORE. ONE IDENTITY. ONE CANONICAL MEMORY. A release, installer, coordinator or client is not another JARVIS.

## 1. Current architecture and evidence

The accepted architecture is an isolated, authenticated TEST runtime. It is not the legacy production launch path and is not yet a deployment system.

| Observed implementation | Deployment implication |
|---|---|
| `tests/lifecycle_stage1/harness.py:31–57` derives the allowed evidence root from its source location, checks TEST markers/reparse paths, and holds `supervisor.lock`/`core.lock` with Windows `CreateFileW`, zero sharing and non-inherited handles | Preserve the OS-held locks. A copied source tree has a different allowed lock namespace; release location must not determine canonical ownership |
| `stage4_runtime.py:33–68` restricts roots and binds a synthetic `data_id` to `STAGE4_TEST-data`; `Context` generates a fresh process epoch | Existing persistent TEST data identity and per-process epoch are useful foundations, but are not a completed installed identity/restore contract |
| `stage4_runtime.py:908` implements the reviewed authenticated, bounded, one-use start/restart transaction and durable grant/intent/claim records | Carry forward this transaction. A durable stop is never cleared merely because a launcher runs |
| `stage4_client.cjs:184–200` independently enforces a source-relative TEST root; trusted startup configuration supplies identity pins and credentials | Relocation must update both trusted bindings consistently; renderer-supplied paths or enrollment are not acceptable substitutes |
| `tests/lifecycle_stage2/bootstrap.py:84–96` checks live pipe peer, enrolled executable digest and client proof; native peer verification precedes reusable credential transmission | Retain executable, process-creation, Core identity, protocol and authentication checks. A PID or a discovered file is insufficient |
| TEST enrollment/configuration and secret keys are supplied by a disposable fixture parent; the TEST installation identifier is fixed to `STAGE4_TEST` | There is no reviewed, durable installed enrollment authority or credential recovery process to load instead |
| `stage4_runtime.py:818` uses the native base Python plus repository `.venv/Lib/site-packages`; the client fixture uses Node from the developer cache | Copying the venv or application directory alone does not produce an independent runtime |
| `stage4_client.cjs:258` loads the native addon from sibling `../stage4-toolchain/peer-build/Release/peer_identity.node` | The release must explicitly include and identity-check its matching native dependency |
| The non-TEST `desktop/main.cjs`/`desktop/backend.cjs` launch and stop a backend; non-TEST `intelligence/main.cjs` reads desktop-owned `.jarvis-session.json` | These legacy branches cannot be used as canonical deployment bootstrap. They were read only and remain unchanged |
| Both package manifests are preview `0.1.0`, with `start`/`test` scripts; `desktop/local-updates.cjs` watches development source | This is neither a signed release manifest nor an installation/update transaction |

[Inspected source hashes](inspected-source.json) identify the 18 source files read. [Dependency observations](dependencies.json) identify Python 3.12.14, Electron 44.2.0, the native addon and sample import origins. Several dependencies resolve from the developer's global runtime cache; the venv enables system site packages. This sample is not a complete dependency bill of materials.

Copying two complete trees could give contenders separate path-based locks: this is an architectural inference from source, **not an observed double-Core incident**. No launch was used to manufacture that condition.

## 2. Assumptions, security and risks

Propose one canonical installation for the designated Windows owner. Resolve `FOLDERID_LocalAppData` through the Windows Known Folder API and validate its actual local path; do not accept arbitrary environment variables, cwd, OneDrive paths, UNC paths or renderer input as authority. Microsoft defines LocalAppData as per-user storage. [Known Folder reference](https://learn.microsoft.com/en-us/windows/win32/shell/knownfolderid)

The intended root is `%LOCALAPPDATA%\Teague Industries\JARVIS`. The proposed TEST equivalent must be an independently approved, explicitly synthetic root, never this production destination. A marker by itself cannot authorize a root. Bind the authorized root, owner SID, installation identity and data identity through a trusted descriptor; reject missing, conflicting, reparse or substituted ancestors. Retain the path/handle protections already validated and test replacement races rather than trusting a single string normalization.

Use an explicit owner-restricted DACL for state, secrets, control endpoints and enrollment. Do not grant Everyone access or modify security settings to recover. The current TEST pipe already supplies an explicit SID DACL; Microsoft's default pipe permissions are broader, so deployment must not substitute defaults. [Named-pipe security](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-security-and-access-rights)

The same owner across Windows sessions must resolve the same canonical state and locks. Global named-object scope does not unify different filesystem roots. Other-user and fast-user-switching coverage remains unverified. A per-user installation alone cannot establish a machine-wide singleton across unrelated user accounts. If that stronger guarantee is required, review a machine-wide ownership anchor separately; do not silently introduce an elevated service. [Windows object namespaces](https://learn.microsoft.com/en-us/windows/win32/termserv/kernel-object-namespaces)

Propose Windows current-user DPAPI for local encrypted credential blobs, with restrictive file access; do not use machine-wide DPAPI for client-management secrets. This protects local storage but is not application-level isolation from malicious code running as the same user. Microsoft documents same-user/same-computer behavior and a roaming-profile exception: it is not a universal anti-cloning or portable-backup guarantee. [CryptProtectData](https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata)

An Electron executable hash proves the binary, not the JavaScript it loads. Both clients can use the same Electron binary with different client credentials. A release therefore needs a verified manifest covering entry points, scripts, native modules, dependencies and relevant configuration. A hash manifest needs an independently trusted signature or explicitly owner-approved digest; self-hashing untrusted files is not authentication. Signing purchases, system hardening and a new security service are not authorized here.

Per-user writable releases are immutable by deployment policy, not OS-proof against the owner or administrator. Same-user malware, administrative takeover, complete disk clones and running two restored machines need explicit threat-model treatment. Do not claim that a plaintext installation ID or copied enrollment metadata solves them.

## 3. Proposed canonical layout and release contents

All paths below are proposed, not created. Release directories are versioned; state paths remain stable across release changes.

```text
JARVIS/
  releases/<build-id>/       # verified application, Python, Electron, native addon,
                            # explicit dependencies/assets/licenses and manifest
  deployment/               # active/previous/pending descriptors; install/update journal
  identity/                 # persistent JARVIS/data identity; owner/install binding
  data/jarvis.sqlite3        # sole canonical database, with its SQLite-managed WAL/SHM
  data/artifacts/           # classified canonical artifacts referenced by records
  config/                   # nonsecret validated settings/policy
  enrollment/               # approved client identities, scopes, revisions, revocations
  secrets/                  # separately protected credential blobs; never evidence
  runtime/                  # stable ownership locks, durable stop/start intent records
  runtime/transient/        # ephemeral discovery/presence; never proof of authority
  client-state/             # bounded mutable Electron profiles/cache, no management keys
  logs/                     # redacted operational records
  evidence/                 # nonsecret audit records and manifests
  backups/                  # verified recovery sets, with explicit retention policy
  staging/                  # same-volume bounded install/update/restore staging
  temporary/                # bounded scratch files; not canonical state
```

Mutable files must not live in `releases/`; runtime updates must not rewrite `data/`. Keep durable restart/stop and recovery records out of purgeable temporary storage. Backups on the same drive are useful rehearsal/rollback material, not sufficient disaster protection.

The release manifest must include build ID, source manifest hash, architecture, Python/Electron/native ABI, supported protocol and schema range, exact dependency versions/hashes and every executable or loaded code file. Include required DLLs, Python standard library/native extensions, site packages and assets. Include Node only if the reviewed bootstrap actually requires it; do not rely on a developer cache or ambient PATH. The runtime must work from an unrelated cwd with no source directory, global site packages or shell-specific environment. Optional provider/media dependencies must be explicitly packaged or truthfully unavailable; this contract grants no new media/provider access.

The installer stages and registers verified files. It has no independent Core, Store, memory, provider, enrollment or lifecycle authority. Source and installed production clients must eventually discover the same approved descriptor and Core. TEST remains a distinct, visibly labeled synthetic namespace.

## 4. Bootstrap, ownership and identity lifecycle

1. Resolve the trusted installation descriptor; verify owner, root, approved release manifest, runtime and configuration identity. Ambiguity enters `RECOVERY_REQUIRED` before App construction.
2. Discover the canonical endpoint and revalidate the live peer PID, creation time, executable identity, protocol and Core/data/epoch identity before sending reusable authentication material.
3. If a healthy verified Core exists, authenticate and attach. Do not spawn a Core just because a client is new or its local cache is stale.
4. Otherwise the coordinator obtains existing exclusive startup ownership. A held lifetime lock with unprovable identity means `RECOVERY_REQUIRED`, not replacement startup.
5. Inspect durable lifecycle history. A deliberately stopped Core stays stopped; ordinary startup is denied. Explicit authenticated start/restart must use the existing bounded, one-use, identity-bound transaction, including interruption recovery. Installation itself is not restart authorization.
6. Launch only the manifest-approved runtime under the same user and bounded configuration. The Core independently acquires the lifetime lock before creating the existing App/Store. No client or installer keeps a duplicate lock on its behalf.
7. Verify readiness, identity, new epoch and authenticated health before reporting successful start. A missing handshake cannot be relabeled success. Unknown outcomes retain the existing fail-closed recovery behavior.
8. Client exit/crash only revokes that client's current session/media/request authority. Coordinator loss permits verified adoption of the surviving Core; it does not kill or replace it. Shutdown/drain/emergency remain separately authenticated controls.

Never delete a lock file or stop latch to recover. Never reuse expired grants, restore old sessions, or transfer controller authority through a renderer. Secrets must not appear in command-line arguments, screenshots, evidence or archives. Trusted credential loading replaces the test-parent supply only after its review; a generic shell/process broker is not proposed.

**NEW versus RESTORE:** initialization must be an explicit owner decision. Missing database/identity/config is an incomplete installation, not permission to create a blank replacement JARVIS. NEW creates a deliberately named synthetic identity in TEST; an eventual production NEW requires separate authority. RESTORE verifies the expected existing JARVIS/data identity and coherent backup before adoption. An unrelated or partially restored dataset is rejected.

Keep persistent JARVIS/data identity separate from host installation binding and process epoch. A normal restart changes the epoch, not canonical memory identity. Moving an existing JARVIS to another machine must preserve canonical identity while renewing host binding and enrollment under reviewed recovery authority. The previous host must be stopped/fenced before activation. Offline restored software cannot prove that every cloned old host is off; that limitation must remain an explicit cutover prerequisite, not a false global singleton claim.

## 5. Enrollment and authority contract

Propose a separately authenticated owner enrollment action through the trusted lifecycle/control boundary. The installer may prepare a pending enrollment description but cannot authorize it. An ordinary client cannot enroll itself or inherit controller authority. The first owner bootstrap must use an explicit local provisioning ceremony, produce a one-use, expiring enrollment intent bound to the installation/data identity, and commit an auditable result. This authority does not currently exist as a persistent installed workflow; its implementation needs review.

Each durable enrollment record should bind client ID, owner SID, installation/data identity, approved executable digest, approved release-manifest digest, protocol range, scopes, revision/generation and enabled/revoked state. Store protected secret references separately. Do not log secrets or treat these nonsecret fields alone as credentials.

| Actor / event | Required behavior |
|---|---|
| Teague desktop / JARVIS Intelligence | Separate client identities and credentials; only existing ordinary request, state, ownership and modeled-media scopes. Neither can shut down/restart Core, enroll clients or install updates |
| Owner controller | Existing lifecycle authority stays distinct. Enrollment/update/restore actions require reviewed explicit scope; an installer button or authenticated chat session alone is insufficient |
| Future clients | Denied until specifically enrolled with reviewed capabilities and scopes. No automatic wildcard enrollment |
| Revocation | Invalidate that enrollment and active grants/sessions; reject stale callbacks and subsequent proofs; do not undo already committed response history. Preserve UNKNOWN work and conservative resource accounting |
| Client replacement/update | Validate the whole new release, explicitly authorize the new executable/manifest binding and advance enrollment generation atomically with activation. Do not automatically learn and trust an arbitrary changed executable |
| Same-version reinstall | Detect existing identity/enrollment and require verified reattachment/recovery; never silently initialize new memory. Changed trust material requires controlled re-enrollment |
| Copied credentials or clone | Reject wrong owner/installation/data/generation and unusable protected blobs. A same-user copy with identical credentials and runtime may be indistinguishable under current checks; reliable rejection is not yet proven and cannot be claimed from DPAPI alone |
| Restore on another machine | No automatic adoption of copied active credentials or sessions. Preserve revocation history, renew host binding and enroll clients through explicit recovery. Keep the restored Core stopped until verification and old-host fencing complete |

Retain Stage 2's peer-before-proof ordering, nonce/protocol checks and executable verification. Loading durable policy is not permission to weaken the wire protocol. Persistent enrollment/update revocation semantics are an added authority boundary, even if existing authentication messages are reused unchanged.

## 6. Data, backup and restore contract

A recovery set must identify the canonical identity, schema, release compatibility, backup sequence/time, artifact inventory and hashes. Verify the set independently before publishing it as usable. A hash match alone does not prove logical consistency, authenticity or successful restore.

Use SQLite's consistent backup mechanism and the reviewed migration/verification approach. Never copy only the active main database while ignoring committed WAL data, nor opportunistically combine database/WAL files from different times. For a coherent database-plus-artifact-plus-configuration snapshot, establish an authorized write fence or controlled stop, resolve/record in-flight work, snapshot, independently verify, then resume only through approved lifecycle authority. Current synthetic tests do not establish a live production backup mechanism.

| State category | Restore treatment |
|---|---|
| Memory, personality records, conversations, projects, tasks, settings, provenance, canonical artifacts and their links | Preserve content, relationships, identity, schema and applicable sequence/history. No new personality or provider default during restore |
| Budgets, reservations, recovery journals and UNKNOWN outcomes | Preserve conservative accounting and uncertainty; reconcile instead of pretending interruption consumed nothing |
| Stop state, consumed start intents and lifecycle audit | Preserve the conservative stopped/recovery disposition and audit history; old tokens/grants must not become executable restart authority |
| Enrollment policy/revocations | Preserve policy history, but reconcile the destination host and explicitly renew credentials/generation where required |
| Sessions, presence/readiness, ephemeral leases/grants, pipe discovery, caches and old epoch authority | Do not restore as live authority; reconnect and authenticate afresh |
| Provider/client/management secrets | Separate protected recovery process. Never copy plaintext credentials into a recovery evidence package or TEAGUE INDUSTRIES DATABASE. Existing provider-key reuse approval is not permission to duplicate it |
| Logs/evidence | Preserve selected redacted audit evidence and referential integrity; exclude sensitive payloads, caches and secret-bearing runtime configuration |

DPAPI blobs alone do not make a usable clean-machine restore. The owner must have a separately reviewed recovery or credential re-provisioning method; lack of it blocks restoration, rather than inviting weaker checks. No such secrets were read in this review.

Existing [synthetic rehearsal](../lifecycle-stage4-evidence/completion-campaign-20260915/cutover-rehearsal-2d3eb60e240c4ca6949b7819274132eb.json) retains 13 passing records, covering the current 19 application-table model, WAL, nine artifacts, provenance links and refusal of naive rollback after new writes. Its verifier includes an additional metadata table. That is prior isolated data evidence, not installed Core/enrollment recovery or a clean-machine PASS.

## 7. Update, interruption and rollback

Use verified versioned directories and a durable deployment journal, not the development watcher. Proposed states are `STAGED -> VERIFIED -> QUIESCED -> SWITCH_INTENT -> ACTIVE -> HEALTH_VERIFIED`, with explicit failure/recovery records. Journal states describe actual completed work, not intentions represented as success.

Validate all files, architecture/ABI, protocol, schema compatibility and enrollment transitions before authorized activation. Stage on the same volume. Preserve the previous release and active descriptor until the new mapping is durable. Multi-file replacement is not inherently atomic: use the reviewed journal and recovery rules, durable writes and bounded exclusive coordination. No observer may authenticate a mixture of old executable policy and new code.

Only an owner-authorized lifecycle transaction may drain/stop the existing Core. An authorized update must bind any required start/restart permission to the exact release/data/config identity; it is not a reusable auto-restart exemption. UNKNOWN work blocks the operation under the existing contract. An interrupted transaction must either retain a fully verified prior mapping or stop in recovery; never silently remove durable stop state, replay an enrollment grant or report a start that did not happen.

Rollback is binary/config rollback only where the data remains proven compatible. If the new release wrote data, do not replace it with an older snapshot. Preserve all newer records; an incompatible schema or reverse migration needs a separately reviewed plan and independent proof. No schema migration is proposed here. Enrollment revisions must not roll back to revive revoked credentials merely because a prior executable is selected.

Required fault points include before/after each journal commit, partial copy, wrong digest/ABI, disk-full/denied write, interrupted descriptor switch, failed health check, consumed/expired restart grant, and concurrent installer/coordinator/client attempts. They remain NOT RUN for a packaged deployment.

## 8. Uninstall and retention

Normal uninstall removes only manifest-owned application versions, launch registration/shortcuts and explicitly disposable deployment staging, after authorized lifecycle coordination. It must preserve identity, canonical data, artifacts, nonsecret configuration, enrollment history, protected recovery material, backups and audit evidence by default. It must not kill an unidentified process, recursively delete the canonical root or reset permissions to force removal.

If the Core is still running or its state is uncertain, removal is deferred or refused until separate authorized shutdown establishes a safe state. Uninstall cannot revoke the Core's ownership by deleting binaries beneath it. Reinstall discovers retained state and offers verified reattachment/restore; it does not create a second identity. Destruction of data/backups/identity requires a separate explicit, identity-bound owner authorization and deletion inventory, outside this implementation scope.

## 9. Clean-machine restore procedure — NOT RUN

1. Prepare an authorized fresh Windows TEST account/machine with no source checkout or developer runtimes; record OS, architecture and trust assumptions.
2. Install only a verified synthetic TEST release; record manifest, signatures/digest approval, dependencies and resolved local root. Start no Core automatically.
3. Select RESTORE, not NEW; supply a verified synthetic recovery set and its expected identity. Reject mismatch, partial set and incompatible schema.
4. Confirm the previous TEST host is stopped/fenced. Record this prerequisite separately from local lock verification.
5. Stage and independently verify SQLite, committed WAL content, canonical artifacts, references, settings, budgets, provenance and conservative recovery state.
6. Recover/provision authorized secret material through the separately reviewed private mechanism. Rebind the host installation and enrollment generation; preserve canonical JARVIS/data identity. Old sessions remain invalid.
7. Enroll the two approved clients and a separate lifecycle controller under real executable identities. Demonstrate wrong executable, wrong owner, revoked and copied/stale material behavior honestly.
8. Explicitly authorize start through the reviewed coordinator; race independent contenders; verify one lifetime-lock owner, new epoch and live peer identity.
9. Authenticate both clients to that same Core, verify shared persistent state, fresh presence and denied old authority. Exercise close/reopen and authorized stop/restart without automatic resurrection.
10. Verify clean shutdown, then interrupted update recovery and uninstall retention in separate disposable runs. Preserve failures and independent hashes.

A same-machine staged directory is not a clean Windows machine. No second-machine result, production restore or automatic activation is claimed.

## 10. Validation performed and remaining matrix

Exact command, run from the repository:

```powershell
.\.venv\Scripts\python.exe -B docs\deployment-contract-20260916\preflight.py
```

[Summary](summary.json), [all 16 checks](preflight-results.json), [31 accepted hashes](accepted-source-verification.json), [dependency observations](dependencies.json). The validator imports existing path/endpoint helpers without constructing App/Store, opening a pipe/database or starting a Core. It invokes root rejection and endpoint validation directly; other checks are source/metadata assertions, not runtime installation tests. The initial check label “Python client source” refers to the JavaScript client; its executable-binding source check proves the digest comparison is present, not that absence of a complete enrollment system was dynamically tested.

| Required deployment validation | Disposition / evidence |
|---|---|
| Frozen Stage 4/5 source consistency | PASS — 31/31 hashes match this turn |
| Current root and endpoint restrictions | PASS — relocated candidate rejected with `TEST namespace required`, production/remote endpoint names rejected, valid TEST name resolved without connection |
| Source/runtime dependency audit | PASS as inspection — source-bound paths, external Python/Node/native dependency and incomplete release manifest identified; portability itself is NOT PASS |
| Relocated startup, unrelated cwd and no repository/global dependencies | BLOCKED FOR REVIEW — trusted root/runtime binding changes required; no package built |
| Exactly one Core across source/installed releases; restart after relocation | NOT RUN — previous actual-process evidence applies to its original TEST namespace, not the new installation binding |
| Valid enrollment / invalid executable rejection | REUSED SOURCE-TEST evidence from Stage 4/5; installed persistent enrollment NOT RUN |
| Stale/revoked enrollment, same-user copied material, cloned-host behavior | NOT RUN — installed binding/recovery contract requires review; same-user clone limitation explicit |
| Interrupted bootstrap | REUSED source TEST start/restart fault evidence; packaged credential loading and relocation interruption NOT RUN |
| Interrupted installation/staging/update; failed-update recovery | NOT RUN — no installation/update transaction implemented |
| Synthetic data backup/restore | REUSED 13-check rehearsal; actual relocated runtime/enrollment and clean-machine restore NOT RUN |
| Ordinary uninstall retains data; destructive removal needs separate authority | PROPOSED CONTRACT ONLY — no uninstall/destruction executed |
| Package integrity/version/ABI mismatch | NOT RUN — sample hashes/version audit is not an installed manifest verifier |
| Production preservation | No production DB opened, source/config/enrollment changed, Core restarted or provider called by this work. No package/installer launched |

The [Stage 5 report](../lifecycle-stage5-evidence/REVIEW.md) retains 1,152 integrated checks, 74 actual Electron checks, 29 successful regression commands, 45 verified TEST databases and 194 exited recorded identities. Those were **not rerun or relabeled as deployment acceptance**. The [Stage 4 human closure](../lifecycle-stage4-evidence/stage4-acceptance-20260916/REVIEW.md) also remains intact. No runtime changed, so no new runtime regression run was justified before the review boundary.

## 11. Failures, skips and limitations

No preflight assertion failed. The deliberate relocated-path rejection is successful evidence of an existing restriction and evidence that relocation is not currently admitted; it is not a new runtime defect. All earlier failed runs are retained.

The initial archive-preparation helper stopped before copying files because its substring secret scan matched the literal private-key header in its own scanner source. [The exact failure](archive-preparation-failure.json), `prepare_evidence-initial.py` and the initial successful source-hash reconciliation remain preserved. Only that evidence helper was corrected to recognize actual header lines rather than quoted scanner code. This was a review-package preparation defect, not a recovered credential or JARVIS runtime failure. Final preparation and archive verification are recorded separately; no earlier result is erased.

- Original historical Stage 1 PermissionError remains ROOT CAUSE UNCONFIRMED / FAIL-SAFE / REVIEW REQUIRED. Later response-publication and challenge/response contention findings remain separate. The earlier Windows memory-read crash is also separate.
- Restricted-context Electron 44.2.0 GPU failure remains an execution-environment limitation, with observed exit consistent with STATUS_DLL_NOT_FOUND and exact missing/inaccessible DLL unconfirmed. Host-context TEST acceptance passed. This review adds no GPU flags or runtime/security changes; packaged clean-machine behavior remains untested.
- Cross-session/other-user/actual-remote-host skips, finite race coverage and same-user tampering limitations remain disclosed. They do not retroactively reopen Stage 4, but need a deployment security disposition.
- Physical media, authenticated approvals and uploads remain deferred as previously approved, not passed. No additional provider/capability authority is included; ordinary chat/TTS/inspection are not universally budget-metered. Cancellation does not establish zero consumption.
- No complete packaged dependency closure, trusted release-signing distribution, portable secret recovery or multi-machine fencing implementation is proved. Offline clones cannot establish global exclusive ownership merely by sharing a UUID.

## 12. Exact next review boundary, file scope and production cutover

Three linked changes require review before a relocatable TEST acceptance run: **(a)** trusted canonical root/identity binding independent of code location, **(b)** an explicit self-contained runtime/bootstrap descriptor, and **(c)** durable owner-authorized enrollment/credential loading with update/recovery semantics. These affect what location and authority the Core trusts. The mission explicitly requires review at that point; they have not been implemented.

Proposed next milestone is TEST only, using synthetic state and private synthetic credentials. It would preserve the accepted lock, IPC, wire authentication and response-commit algorithms, while adding the narrowly bounded deployment binding. Suggested implementation allowlist, subject to approval:

| Proposed file(s) | Bounded purpose |
|---|---|
| New `deployment_test/contract.py`, `deployment_test/package.py` | Validate trusted TEST descriptors/manifests; produce explicit runtime layout and dependency inventory without production paths |
| New `deployment_test/bootstrap.py`, `deployment_test/enrollment.py` | Trusted installed TEST credential/policy loading, separate local owner provisioning and lifecycle intent; no renderer authority or general command execution |
| `tests/lifecycle_stage1/harness.py` | Review the narrow root-policy input/factoring needed to apply the existing locks/IPC guard at the independently authorized TEST root; preserve default Stage 1 validation and OS-lock semantics |
| `stage4_runtime.py` | Bind approved descriptor/root/data/runtime paths and load reviewed TEST enrollment; keep response transactions, Store schema, provider behavior and lifecycle invariants unchanged |
| `stage4_client.cjs` | Resolve verified TEST descriptor/native module/runtime paths and trusted client configuration; retain existing peer verification and renderer boundary |
| New `tests/deployment_contract/test_contract.py`, `tests/deployment_contract/fixtures.py`, `tests/deployment_contract/campaign.py` | Negative descriptor/enrollment tests and actual relocated Core/client/install-update-uninstall fault campaigns |

If implementation needs native peer API expansion, Stage 2 protocol changes, production launchers, new Store/schema behavior or broader management authority, return for another review. Native bridge code, legacy `desktop`/`intelligence` production branches, personality, voice, provider routing and response-commit code are not authorized for change by this proposal. New scope must not silently turn fixture flags into production routes.

The proposed validation sequence is descriptor/package rejection tests, actual relocation with developer paths unavailable, persistent enrollment and copy/revocation tests, repeated one-Core/restart/interruption tests, synthetic backup/restore, recoverable update and uninstall retention, then affected Stage 1–5 regressions against final hashes. Preserve every failed case. Where cross-user or cloned-machine behavior needs an actual separate environment, retain NOT RUN until performed; do not substitute a mock PASS.

Rollback of this review requires no runtime action: retain its evidence and supersede only the proposed documentation disposition. A later TEST implementation must retain the accepted source hashes and immutable TEST backup, withdraw only its explicit TEST entry points, and never roll back canonical state across new writes. Do not reset the existing dirty worktree, delete failures, remove stop latches or affect production.

**Production cutover remains separately blocked** until the installed binding/enrollment contract is approved and passes actual deployment tests; backup, secret recovery, destination identity, old-host fencing, security/skip disposition and data compatibility are verified; and a concrete production operation/backup/rollback inventory receives explicit owner approval. No rehearsal authorizes opening production SQLite, moving data, enrolling production clients, installing over JARVIS, changing its identity or activating a release.

Changed authored paths this turn are this review/evidence directory and the current completion checklist only. Source hashes and the selected archive manifest identify them; no runtime source was changed. The repository HEAD remains the earlier checkpoint, not an acceptance/release commit and not a substitute for the frozen working-source hashes.

**Approval requested:** the TEST-only root/runtime/enrollment milestone and exact allowlist above, with preserved Stage 1–5 behavior and a further stop before any broader authority or production integration. Clean-machine enrollment security limitations require explicit review; this document does not declare them solved.

PRODUCTION DATABASE OPENED / MOVED / MODIFIED: NO  
PRODUCTION CONFIGURATION / ENROLLMENT MODIFIED: NO  
PRODUCTION CORE RESTARTED: NO  
NEW CORE OR CLIENT LAUNCHES THIS REVIEW: ZERO  
PACKAGED RELEASE / INSTALLER BUILT: NO  
PAID PROVIDER CALLS / ACCEPTANCE COMMIT / PRODUCTION ACTIVATION: NO
