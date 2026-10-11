# DEPLOYMENT TRUST-BOUNDARY IMPLEMENTATION REVIEW

2026-09-16. **Bounded TEST implementation and same-host relocation validated; production/release readiness remains PARTIAL.** No production database was opened, no production Core was launched/restarted, no production enrollment/configuration was changed, and no paid provider, installer installation, acceptance commit or publication occurred.

Authority: [exact current approval](APPROVED-SCOPE.txt), accepting the [deployment contract](../deployment-contract-20260916/REVIEW.md). Scope remains canonical root binding, packaged fixed-role bootstrap and persistent owner-authorized TEST enrollment. Stage 4 remains historically CLOSED in TEST; Stage 5 remains historically passed. This is a new deployment implementation version, not a claim that its three intentionally changed accepted files retain historical hashes.

## 1. Implementation and source boundary

[Full before/after SHA-256 values, syntax commands and AST comparison](source-final.json) identify all ten implementation/test files. The three prior source snapshots and unified diffs are retained here. Of 31 previously accepted source/executable paths, 28 still match; exactly the following three intentionally differ. No unexpected drift was found.

| File | Change | Prior acceptance boundary |
|---|---|---|
| `tests/lifecycle_stage1/harness.py` | Explicit installed TEST binding hook in root validation; original source-root branch remains | Yes; OS lock, IPC guard and identity algorithms unchanged |
| `stage4_runtime.py` | Configure packaged binding, report installation/package identity, load persistent revocations, select fixed packaged child command | Yes; only existing `serve` and `test_child_command` functions differ, plus new configuration hook |
| `stage4_client.cjs` | Trusted-main installed root/package/native mapping and separate installed profile root; original default branch retained | Yes; existing native peer verification, transport and renderer authority retained |
| `deployment_test/contract.py` | Explicit descriptor, TEST paths, private directory creation, DPAPI records, manifest/hash checks and held file handles | New |
| `deployment_test/package.py` | Explicit runtime/source inventory, NEW materialization, stopped synthetic backup/transfer, bounded uninstall and same-package reinstall | New |
| `deployment_test/bootstrap.py` | Fixed Core/coordinator/owner-control roles, owner proof, package-only code reads and module provenance | New |
| `deployment_test/enrollment.py` | Bound persistent enrollment generations, one-use owner intents, revocation and stopped client replacement | New |
| `tests/deployment_contract/test_contract.py` | Nonexecutable policy fixtures and rejection/interruption tests | New |
| `tests/deployment_contract/fixtures.py` | Real relocated process/client driver; private credentials, exact identity records and authenticated cleanup | New |
| `tests/deployment_contract/campaign.py` | Actual relocation, contention, enrollment, synthetic restore, retention and failure campaign | New |

The Store, schemas, response-commit code, lifecycle/ownership classes, Stage 2 authentication/native bridge, production launchers, personality, provider routing and voice engines were not edited. AST comparison confirms the existing `Context`, `Authority` and coordinator classes are unchanged. Existing TEST Electron GPU switches were not added or changed. There is no new renderer management API.

Repository HEAD is `8f0b9bce181800f9339249c4024e396246e94208`; it is the previous repository checkpoint, **not** a commit containing this implementation. Source/evidence hashes, not HEAD alone, identify this working version. Pre-existing unrelated working-tree files were not reset, committed or included automatically.

## 2. Canonical root and runtime design

An explicit current-user DPAPI `binding.dpapi` pins owner SID, synthetic installation/data identities, exact install/state/release roots, package manifest hash, protocol `[2,3]` and TEST data schema `1`. It is the only discovery input. Missing, relative, UNC, conflicting, reparse or copied bindings are refused; no search of arbitrary directories or activation of a production default occurs. The state path must be the bound `state/TEST-STAGE4-<id>` beneath `TEST-INSTALL-<id>`.

```text
TEST-INSTALL-<installation-id>/
  binding.dpapi, initial-owner.dpapi, installation.json
  releases/<build-id>/
    manifest.json
    app/                 explicit application and authenticated TEST client files
    python/              native Python, restricted ._pth, stdlib and native DLLs
    electron/            actual Electron distribution
    node/                fixed trusted TEST client launcher runtime
    native/              existing peer_identity.node
  state/TEST-STAGE4-<namespace>/
    TEST_ONLY, existing OS lock files, stop/start and recovery records
    STAGE4_TEST-data/     synthetic canonical database and artifacts
    enrollment/          protected owner record and immutable generations
    owner-intents/, backups/, maintenance records
  client-state/          disposable Electron profiles, separate from code/data
```

The final package has **785 manifest entries, 517,309,374 bytes**. Manifest SHA-256: `4c07cf1d46544d248db711bfb3249bfe4f933a3f8f9241b4a182dddce00d9d04`. The package lives outside the JARVIS repository under `outputs/deployment-test-releases/TEST-PACKAGE-8448f8961aeb4567956d4749fdac3471`. Heavy binaries, profiles, private runtime state and credential records remain local and are excluded from the project-record archive.

Installed Python executes only a fixed bootstrap role, with `-I -S -B`, explicit package paths and no PATH/PYTHONPATH reliance. Before importing the runtime it verifies the complete inventory, including no unexpected files, and holds read-only non-delete-sharing handles on manifest files. A code-read audit refuses external `.py`, `.pyc` and `.pyd` paths. Actual Core module origins and import paths were recorded entirely within the release while the working directory was unrelated. The original repository was not renamed or disabled; the source-independent claim applies to the installed processes, not the source-owned acceptance driver.

The existing Core holds the lifetime lock; the bootstrapper is not a second Core. Existing startup exclusion, stop latch and one-use restart transactions remain authoritative. Losing the coordinator permits authenticated adoption of the surviving owner; it does not authorize a replacement. Interrupted consumed startup intent remains recovery-required. Fixed diagnostic self-exit at the existing before-intent/intent/spawned observer boundaries is separately included in the signed TEST owner request; it accepts no process ID, command or arbitrary executable.

## 3. Dependency contract and its limit

Bundled: native Python 3.12.14 and its stdlib/native extensions; Electron 44.2.0; a pinned Node binary; the unchanged native bridge; fixed authenticated HTML/CSS/branding assets; TEST protocol and package manifests. No venv, site-packages or npm resolution is used by the installed process. Optional Python/document/ML/speech dependencies and local model services are not part of the active deterministic TEST surface. Physical media, actual repair execution, paid providers and live Ollama/Astra are disabled/unavailable here; earlier provider work is not represented as newly validated live functionality.

[PE import inventory](independent-final.json) covers **53 binaries**. Windows system DLLs/API sets remain platform dependencies. The native bridge also imports MSVC runtime libraries, notably **MSVCP140.dll**, which is not bundled. VCRUNTIME files are bundled for Python, but this does not prove Electron resolves the bridge's VCRUNTIME imports from that directory. No module-resolution trace or clean-machine proof was performed. This is a disclosed **host-runtime packaging prerequisite**, not a fully self-sufficient Windows distribution. No DLL, redistributable, driver or system setting was installed/changed to obtain a pass. See the [clean-machine plan](CLEAN-MACHINE-REHEARSAL.md) before deciding app-local redistribution versus an approved prerequisite.

## 4. Persistent enrollment and authority

Owner operations require an HMAC-authenticated intent bound to the descriptor digest and intended installation, with an explicit action/arguments, random nonce, 30-second expiry and exclusive one-use receipt. Secrets reside in current-user DPAPI records inside new owner-only TEST directories; keys travel only through the private trusted-process configuration boundary, never renderer APIs, command arguments or evidence.

Enrollment binds installation/data identity, owner SID, approved package/protocol, client ID, executable digest, scopes, enabled state and monotonic version. Immutable protected generations avoid readers observing partial publication. Teague and Intelligence keep separate ordinary credentials; the controller keeps separate lifecycle/emergency scope. A Python caller cannot impersonate an Electron enrollment. The existing Stage 2 peer PID/creation-time/executable and peer-before-proof rules still perform authentication.

Revocation is persisted, applied by the existing Core revoke-client path and checked before subsequent authenticated operations; another client's authority remains intact. Replacement requires owner intent, expected version, stopped Core and existing supervisor/lifetime lock exclusion. It issues a fresh credential and advances the version for the currently approved package's actual Electron identity. Old credentials remain rejected across restart. Completed same-package reinstall preserves owner enrollment management.

**Bounded replacement limitation:** same-approved-package re-enrollment/replacement is implemented and tested. A different Electron executable/new release manifest cannot be learned or trusted automatically. Cross-build atomic activation/re-enrollment and recovery are not implemented here; they require a concrete next release transition review. Do not call the tested replacement a validated new-binary upgrade.

This per-user TEST boundary is not a security boundary against an administrator or arbitrary malicious code already running as that Windows user. DPAPI is not a signing infrastructure, a portable machine-independent backup key or an anti-rollback counter. Cross-user/session and copied-machine attacks need their own environment evidence. No broad shell, generic Python/process broker, destructive-data API, network destination or production registration route was added.

## 5. NEW, restore, retention and recovery

NEW explicitly creates a distinct synthetic data identity and refuses to adopt supplied existing data. RESTORE requires a stopped source, explicit owner target, compatible coherent SQLite backup/artifact inventory, old-installation fence and one-use bounded transfer intent. It preserves the existing synthetic data identity and canonical rows, creates a new installation binding and fresh enrollment keys, carries revocation policy forward and excludes old sessions/ready/start authority. A corrupt backup was rejected before any destination identity was materialized. No replacement identity was generated.

Normal TEST uninstall is allowed only after authenticated stop and a maintenance fence. It deletes only individually manifest-verified application files; no recursive data deletion, forced process termination, lock deletion or ACL mutation is used. Mutable database, identity, protected enrollment and evidence remain. Reinstall accepts only the same pinned package, completes the maintenance fence durably, keeps the stop state and requires a fresh authorized restart. This is a bounded single maintenance cycle, not a general upgrade/uninstall history manager.

Interrupted initialization or incomplete enrollment remains fail-closed; recovery is not a silent NEW or speculative retry. After a consumed restart intent is interrupted before a Core owns it, later start authority is refused pending review. A surviving Core after coordinator interruption is adopted instead of duplicated. No rollback of canonical data over newer writes occurs.

## 6. Executed validation and dispositions

Primary evidence: [26 policy tests](policy-47a545baaacc4421b92356cd1a797080.json), [347-check relocated campaign](installed-0630e4345f8f4975bf5bab5a6ab07c23.json), [29 exact regression commands/log paths](regressions-1d930927d3984283bac10f8527a675e0.json), [independent hashes/process/dependency audit](independent-final.json). Counts include individual assertions and cleanup checks; they are not 347 independent race trials.

| Required validation | Disposition and exact coverage |
|---|---|
| 1–3 Canonical, invalid and ambiguous roots | PASS — explicit binding, missing/relative/UNC/conflicting/copied configuration and duplicate JSON keys rejected in policy fixtures |
| 4–5 Relocated launch; no source-code dependency | PASS on this host — actual packaged Core and both Electron clients; package-only recorded imports, unrelated cwd and no PATH |
| 6 Exactly one Core | PASS in exercised TEST namespaces — three rounds of four concurrent authorized contenders; one start winner each, all others adopt; real OS lock code unchanged |
| 7 Interrupted bootstrap | PASS fail-closed — actual coordinator self-exit before intent, after intent and after spawn; stop and old-grant rejection verified, consumed unresolved intent refuses replacement; surviving Core adopted |
| 8 Stale bootstrap state | PASS — stop latch blocks ordinary startup; old grants/controller authority rejected, interrupted intent not replayed |
| 9 Package/data incompatibility | PASS for exercised pins and identity/schema contracts — modified package/runtime refused; actual mismatched canonical TEST data rejected before spawn. Exhaustive ABI/Windows-version compatibility is NOT RUN |
| 10–13 Valid, wrong/stale/revoked enrollment | PASS — actual Electron enrollment, Python impersonation denial, live revocation, foreign-client continuity, fresh replacement and old-key rejection; modified runtime pin tested with nonexecutable policy fixtures |
| 14 Copied enrollment | PASS same host — copied binding/policy rejected; actual unrelated installation rejects copied protected owner record. Other-machine/account execution NOT RUN |
| 15 Approved client replacement/update | PARTIAL overall — same-package owner replacement/re-enrollment PASS; changed-executable/new-build update NOT IMPLEMENTED/NOT RUN |
| 16 Reinstall | PASS bounded same-package cycle — data identity retained, stop retained, explicit fresh restart, enrollment management retained |
| 17–19 Synthetic restore, distinct NEW, restore failure | PASS same host — complete table comparison, fresh transient authority, distinct NEW identities, corrupt restore creates no destination |
| 20–21 Uninstall retention; separate destruction | PASS — named application files removed, database/enrollment retained; destructive-data action refused |
| 22 Stage 4 lifecycle/security regression | PASS — 29 commands, including Stage 1–3, 306 response races/4,748 checks and actual Core lifecycle/cleanup, plus 74 actual Electron client checks |
| 23 Stage 5 integration regression | PASS — 1,152 existing isolated combined-fault checks on final deployment source |
| Standalone syntax | PASS — nine Python AST parses, client CJS and two generated JS entry strings; 12 checks. Syntax is not runtime evidence |
| Clean-machine restore | NOT RUN — owner recovery and native runtime prerequisites need review |
| Production/release | NOT AUTHORIZED — no cutover, production install or commit |

Stage 1: 24 discovered, **23 passed / 1 existing skip**. Stage 2: 36 discovered, **35 passed / 1 existing skip**. Stage 3: **43 passed**. Python: **212 passed**. Provider regressions: **62 passed**. Desktop: **35 passed**. Response commit: **306 trials / 4,748 checks**, no failures/live workers. Actual Electron source-root lifecycle: [74 checks](../lifecycle-stage4-evidence/client-state-media-ce4907b46aae4827a8d698a18b074a5b.json). Stage 5: [1,152 checks](../lifecycle-stage5-evidence/integrated-2dc1a02126b1480db0d1b07fc1ffc4e2.json). Existing skips remain unverified, not passed. The earlier human lifecycle pass is preserved; this work did not invent a new human result.

Both new source-root screenshots were inspected: each shows STAGE4_TEST/authenticated; physical voice/capture is truthfully unavailable. The relocated fallback check separately verified the actual visible response container/frame and persisted deterministic provider provenance. It was simulated provider output, not a paid OpenAI or real Qwen call.

## 7. Preserved failures, limitations and cleanup

- Restricted-context DPAPI probe failed with errno 2; host roundtrip passed. Exact environment mechanism is unconfirmed. No plaintext fallback or permission changes were added.
- `installed-253ef1805a7f4e9a909b32ade35a953c.json`: build input was a development npm junction; failed before Core launch. The driver now explicitly resolves and hashes that known build dependency; installed reparse protection is unchanged.
- `installed-1875fad8135c433e8daab90b8a7f0c45.json`: response-frame timeout after authenticated attachment. Preserved stderr also contains long-profile cache path errors. The TEST installed profile moved to the approved separate `client-state` root, and the driver used the actually visible last-opened client for its frame check. These observations are not claimed to establish one common cause. Cleanup passed. The later 54-check smoke and 246-check campaign remain separate earlier-source evidence.
- Additional review caught enrollment mutation being refused even after completed reinstall; the mutation path now requires the normal verified operational binding, preserving rejection of unfinished maintenance. The final campaign verifies post-reinstall owner replacement.
- Early cleanup-audit direct PID opens encountered access denied. These are read-only audit findings, not evidence of another Core or the historical identity-file race. The final census covers **232 distinct recorded identities**: 230 absent, two older identities share PID 10960 with a later process whose creation time differs. No unrelated process was terminated or granted access. Recorded parent exit waits and the census corroborate cleanup. The original exceptions and audit helper revisions remain disclosed; a later census does not explain every earlier native query failure.
- Automatic approval review initially rejected the Stage 5 command based on older restrictions. After the owner explicitly reconfirmed the exact regression, the same command ran and passed. No workaround or alternate invocation bypassed that rejection.
- Original historical Stage 1 PermissionError remains ROOT CAUSE UNCONFIRMED / FAIL-SAFE / REVIEW REQUIRED. The later response-publication and IPC contention reproductions remain separate. Historical Windows memory-access crashes remain separate. Restricted-context Electron GPU failure remains an environment limitation; exact DLL/root cause unconfirmed. This package dependency inventory does not retroactively diagnose it.

## 8. Rollback and next review boundary

Rollback this unactivated TEST implementation by withdrawing its explicit TEST entry points and retaining all package/state/evidence directories. Existing running production is untouched. The three pre-change source snapshots identify the previous accepted source; any restoration must check current hashes and preserve subsequent owner edits, never reset the whole worktree. Remove no lock/stop/identity records to force startup. Use authenticated TEST shutdown for any future active fixture; no blanket PID cleanup is authorized. Uninstall is optional and bounded to verified package files; data destruction remains outside scope. Do not roll database backups over new writes.

Appropriate nonsecret source snapshots, reports, selected test evidence, screenshots and manifests are copied to TEAGUE INDUSTRIES DATABASE with SHA-256 comparison; the archive receipt is separate. Private DPAPI records, keys, profiles, model/runtime files and databases are excluded. The archive is project evidence, not an executable installation or a portable credential backup.

**Next review:** resolve the native-runtime packaging prerequisite, define the concrete changed-build activation/enrollment transaction, and approve the clean-machine owner recovery/old-host fencing procedure and environment. The same-package relocated TEST milestone is evidenced; new-build upgrade and clean-machine readiness remain partial. No production cutover, production restore/enrollment, installer execution, acceptance/release commit or publication follows from these TEST results.

PRODUCTION DATABASE OPENED / MODIFIED / MOVED: NO  
PRODUCTION CORE LAUNCHED / RESTARTED: NO  
PRODUCTION ROOT / CONFIGURATION / ENROLLMENT CHANGED: NO  
PAID PROVIDER CALLS: ZERO  
ACCEPTANCE / RELEASE COMMIT / PUSH: NO
