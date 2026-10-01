# Remaining Core completion path after accepted Stage 5

Read-only architecture/evidence review, 2026-09-17. No Core, installer, migration, update or provider was run during this review. This maps the existing programme; it does not define additional stages or authorize production.

Stage 5 acceptance commit: `9460dbc44f63c95d1128c1a27f124f87d99b530b`.
Immutable Stage 4 parent: `d6199756f1e1f4495ad6c3de457660cbf1f03e84`.
The exact 283-file Stage 5 allowlist was verified against the commit. The index is empty. All 16 previously modified tracked-file contents remain unchanged; unrelated untracked work was not selected. The repository is intentionally still dirty, not a clean production release tree. See `commit-receipt.json`.

## Existing stage definitions and current status

Authority: [ownership proposal, ordered stages](../CANONICAL-CORE-OWNERSHIP-PROPOSAL.md), [canonical checklist](../CORE-COMPLETION-CHECKLIST.md), the approved completion campaign (`bd4e5dd4-05df-4389-b181-b8e74261caa6/pasted-text.txt`, Stage 6/7 sections), [deployment contract](../deployment-contract-20260916/REVIEW.md), and [later deployment-completion approval](../deployment-completion-20260916/APPROVED-SCOPE.txt).

The original Stage 6 production-cutover and Stage 7 installer/release stages were refined into Stage 6 cutover readiness and Stage 7 release preparation, with actual production cutover/release still separately approved. Some Stage 7 TEST prerequisites were implemented early. This does not create a new Stage 8 or make the production stages complete.

| Existing stage / checklist IDs | Current status | Remaining work |
|---|---|---|
| 0 architecture; 1 exclusion; 2 authentication; 3 migration rehearsal | Completed within reviewed isolated scope | Preserve original platform/security limitations; not proof of live deployment |
| 4 lifecycle-independent TEST Core and clients | Accepted immutable baseline | No reopening without regression evidence |
| 5 / S5-01 reliability campaign | Accepted at the commit above | No additional Stage 5 work required by this review |
| 6 / S6-01 cutover readiness and rehearsal | PARTIAL | Final approved production source/destination identity, complete current-state backup/recovery inventory, production bootstrap mapping and rollback/cutover rehearsal |
| 6 / S6-02 live cutover | OPEN, separately authorized operation | Approved controlled migration/activation, legacy-start fencing, one live Core and post-cutover owner acceptance |
| 7 / S7-01 deployment/release preparation | PARTIAL | Native dependency closure, actual changed-build upgrade evidence, clean-machine recovery, final release packaging/operations acceptance |
| 7 / S7-02 production release | OPEN, separately authorized operation | Approved install/release/signing/update/distribution policy and actual final Windows release validation |

Older September 15/16 checklist text saying Stage 5 passed refers to historical evidence. It is superseded for Stage 5 acceptance by the new commit, not reused as fresh evidence. Older descriptions of native packaging and upgrades as wholly unimplemented are also stale: code and partial validation now exist, but complete passing acceptance was not found.

## Required remaining gates, in dependency order

These are work packages under existing S6/S7, not new numbered stages.

| Gate | Kind / objective | Prerequisites and acceptance evidence | Production / environment | Authorization |
|---|---|---|---|---|
| Reconcile deployable candidate to accepted baseline | Read-only review, then bounded TEST corrections if needed | Review the three excluded working files `deployment_test/contract.py`, `native.py`, `package.py` against the frozen package; choose explicit intended changes, exact new source/package hashes and affected regressions. Never package the whole dirty tree | TEST only; existing Windows host | Inspection already authorized. Existing narrow TEST packaging correction scope can continue; new trust/runtime authority requires review |
| Native dependency closure | Implementation reconciliation + actual validation | Prove required native binaries load from declared package/Windows sources; omitted, modified and wrong dependencies fail closed; relocated launch does not rely on development paths. Resolve observed path/module-classification failures using evidence, not bypasses | TEST only; then confirm on clean Windows | Bounded TEST packaging work already approved; installing prerequisites/system changes needs approval |
| Changed-build A → B update | Primarily validation of existing implementation; minimal fixes only if evidenced | Different approved build/executable; owner-authorized staging/enrollment; data identity unchanged; exactly one Core; invalid/partial/incompatible builds denied; interruption recovery; stale bootstrap and revoked credentials denied; rollback preserves newer state and refuses unsafe downgrade; authenticated cleanup and final regressions | TEST only; existing Windows host initially | Already approved bounded TEST scope; no production update or broader schema/authority change |
| Clean-machine owner recovery | Missing recovery-contract work + actual environment validation | Reviewed identity-bound transfer/re-enrollment and old-host fence; recover synthetic existing identity/data from a coherent backup, fresh credentials/sessions, one Core, both clients, lifecycle/reliability and no undeclared dependencies. Same-host reinstall cannot close this | Fresh Windows environment required. VM may qualify only after definition/owner confirmation; second physical Windows PC is an alternative | Environment selection/creation/prerequisites require approval; cross-machine trust/credential recovery design requires separate review before implementation |
| Stage 6 final rehearsal and cutover plan | Read-only inventory + isolated rehearsal | Identify actual live Core/data provenance via a reviewed read-only diagnostic before copying anything; approve canonical local destination; preserve all records/artifacts/configuration/accounting/UNKNOWN state; exclude transient authority; verify coherent WAL backup plus artifacts; restore and independently compare; rehearse three rollback boundaries and new-write refusal; account for secrets separately | TEST rehearsal first; eventual live source inspection/migration explicitly scoped | Planning/synthetic rehearsal already approved. Live data access/copy, secret recovery and live operations require the consolidated approval |
| Production bootstrap and legacy-entry convergence | Reviewed implementation, then validation | Source/installed/legacy launchers discover the same approved canonical descriptor/Core; approved account and path/ACL/protocol boundaries; ordinary clients cannot own lifecycle; stopped stays stopped; ambiguous identity starts nothing; preserve existing approved capabilities and truthfully expose deferred ones | Changes would affect production paths even if first tested in isolation | Exact production file/authority design must be reviewed. TEST flags are not production authorization |
| Stage 6 live cutover and owner acceptance | Deployment + validation | Verified backup, explicit stop/drain, no UNKNOWN unsafe shutdown, old entry points fenced, one Core at approved canonical data, fresh authentication/presence, correct persistent identity/records, both interfaces, restart/close behavior, rollback readiness and owner checks | YES, production | Explicit consolidated owner approval immediately before execution; no automatic cutover from TEST PASS |
| Stage 7 final Windows release | Packaging + validation + deployment/release decision | Reviewed installer/bootstrap, version/compatibility manifests, install/launch, duplicate-launch behavior, update/failure recovery, uninstall retains canonical data, reinstall attaches correctly, client independence, operations/recovery documentation, final intended source hashes and regressions | Disposable installer tests first; production install/publication later | TEST packaging preparation remains approved. Production install, signing purchases, release publication/push and automatic updates need explicit approval |

## Evidence that prevents premature completion

1. [Stage 4 final accepted source comparison](../deployment-completion-20260917/final-blockers/package-source-comparison.json) excludes three pending deployment files. [Stage 4 report](../deployment-completion-20260917/final-blockers/REPORT.md) explicitly says they were not accepted. They cannot silently become the next production source.
2. `deployment_test/upgrade.py` and `tests/deployment_contract/completion.py` exist, including A/B, interruption and newer-data rollback assertions. However, all three preserved `completion-*.json` runs in `docs/deployment-completion-20260916` stopped at 27 records with one failure, before complete A/B acceptance. The observed failures were `EXTERNAL_PACKAGED_NATIVE` for system MSVCP140.dll, an extended-path native module classification, and `UNDECLARED_LOADED_NATIVE` for packaged python.exe. Those messages establish the failures, not their final root cause. No later complete passing A/B record was found in the inspected repository evidence. Ordinary later client/Stage 5 PASS is not a substitute.
3. Native manifests exist and passed inventory checks, but all-file hash verification does not prove clean-machine dependency resolution. The [clean-machine plan](../deployment-implementation-20260916/CLEAN-MACHINE-REHEARSAL.md) and later approval explicitly retain NOT RUN until a genuinely qualifying Windows environment is used.
4. The clean-machine plan identifies current-user DPAPI recovery as a separate trust issue. Copying its blobs, generating a replacement canonical identity, or turning RESTORE into NEW would not satisfy acceptance. The same-host synthetic restore already passed; it is not cross-machine recovery.
5. [Current-schema rehearsal evidence](../lifecycle-stage4-evidence/completion-campaign-20260915/cutover-rehearsal-2d3eb60e240c4ca6949b7819274132eb.json) covers 13 checks / 19 application tables plus artifacts and rollback. It does not verify the present production data location, current production schema/content, complete production secret recovery or a live cutover.
6. The accepted `deployment_test/contract.py` explicitly supports STAGE4_TEST_DEPLOYMENT and TEST installation identities. Production discovery/defaults are absent. Removing TEST checks or reusing legacy desktop-owned bootstrap is not an approved production design.

## Continuous work versus real owner boundaries

No new approval is needed merely to read code/evidence, reconcile the candidate, prepare manifests/runbooks, or perform previously approved synthetic rehearsals and narrow TEST deployment validation. These can form one continuous campaign under the existing scope when resumed. This turn stops after review as requested.

Actual owner boundaries are: new production discovery/enrollment authority, machine-independent recovery/security design, choosing/creating a clean Windows VM or other host and installing prerequisites, any live source-data access/copy beyond authorization, production stop/migration/activation, and signing/publishing/automatic updates. Required cross-session/security gaps need actual evidence or an explicit approved deployment limitation; they must not be silently converted to PASS.

The most useful next action is Stage 6 cutover-readiness preparation while closing its Stage 7 TEST deployment prerequisites, beginning with the three excluded deployment files and the preserved native/A→B failures. Do not restart the accepted Stage 5 campaign without a relevant source change/regression need.

## Mac and timing

No Mac is required by this Core roadmap. The reviewed package is Windows-specific: native Windows locks/named-pipe peer checks, executable/process identity and DPAPI enrollment. A native macOS port would be a separate design and authorization, not a shortcut to completing these Windows gates. A Mac hosting a compatible Windows VM is only a possible separately reviewed environment, not an assumed compatible target.

Estimated remaining technical work: four substantial packages—deployment dependency/update closure, clean-machine recovery, production cutover/bootstrap readiness, and final installer/release acceptance. Overall medium-to-high deployment/integration effort; this is not a new Core architecture rewrite. A defensible calendar estimate is not available until native/A→B diagnostics and the clean-machine recovery/environment decision are closed. Environment/owner waiting time is separate from engineering work. Do not promise that only one test or a few minutes remain.

## Deliberately outside Core completion

Approvals, uploads and physical media remain owner-deferred; no later reviewed gate found here silently enables them. General autonomous goal-setting, recursive self-improvement, resource acquisition, broader providers/Ollama Independence, paid Astra comparisons, devices/wearables, native macOS support, remote-host multi-Core deployments and optional UI improvements are outside this finite completion campaign. Preserve compatibility for future work without implementing it now.

The unexplained Stage 5 timeout delays and restricted-context Electron exact DLL finding remain limitations. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Conclusion: the isolated Core foundation through Stage 5 is accepted. Official deployed Windows Core completion remains incomplete until the required Stage 6/7 gates and their explicit production/release decisions are satisfied. No production operation has begun.
