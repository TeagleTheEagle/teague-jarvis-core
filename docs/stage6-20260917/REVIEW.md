# Stage 6 deployment review — 2026-09-17

STATUS: BLOCKED. JARVIS CORE: INCOMPLETE. No production cutover or Stage 7 work performed.

## Verified work

The accepted application snapshot (61 files) remains unchanged. A separate TEST source copy contains only the three reconciled deployment differences listed in source.json. The repository runtime and production configuration were not edited by this work. Existing unrelated working-tree modifications were not included.

- contract.py: retains the pending orphan-update-record rejection.
- package.py: retains the pending app-local CRT copies in the native directory.
- native.py: retains the pending dependency inventory and drive-prefix normalization; corrects the branch that wrongly classified an in-package executable as an undeclared external module. External packaged-name DLLs and unknown non-Windows modules remain rejected.
- Seven focused tests passed, including reproduction of the original branch defect and negative external-module cases.
- Three actual packaged runs each recorded 29 checks, 28 passing and one failure. These are separate attempts, not a combined acceptance PASS.
- Actual Python, Electron and Node module observations passed; the Electron bridge and required MSVC modules were observed app-local. A and B have different package and executable identities.
- All runs completed authenticated cleanup. Final census checked 37 recorded process identities; none remained live.

## Preserved failures

1. deployment-728c2f7b18544d31b743225ae046918a.json: source-side upgrade.snapshot called from an unbound driver; TEST namespace required. No update occurred.
2. deployment-869f3489414d45ab91b3f23d50db4d0a.json: explicit binding in the development interpreter was correctly rejected with INSTALLED_RUNTIME_REQUIRED. No update occurred.
3. deployment-20066a8db5d54c1ca2f5b04a54b3ee58.json: the corrected driver used the installed interpreter/application and passed snapshot validation. The authenticated stage-update then failed during incoming package verification with SOURCE_TREE_EXECUTION_DENIED.

The driver-only snapshot correction uses a fresh installed Python process, exact installed app and explicit existing Binding. It does not rebind a shared runtime, alter namespace checks or add a product route. The first census invocation encountered the expected invalid-PID Windows errno 87 for an exited process; the final census records that as absent and fails on other errors. The original invocation remains in tool history.

## Current confirmed update conflict and proposed review

Trace: completion.changed_build → prepared → authenticated stage-update → upgrade.operate line 66 → verify_release → Binding.verify_package → digest/open(rb) → bootstrap.no_external_code line 37.

The bootstrap audit hook rejects *all opens* of .py/.pyc/.pyd outside the active release, including read-only hashing of the incoming package. Therefore the legitimate hash-verification step cannot complete. This is distinct from the historical Stage 1 failure and Stage 5 timeout.

Minimum proposed correction, NOT IMPLEMENTED: provide a narrowly bounded data-verification operation for the explicitly authenticated, hash-pinned incoming TEST package, while retaining independent enforcement against importing/executing its code. Do not simply exempt every external code-file read or disable the audit hook. Review how verification handles remain pinned, how expiry/failure revokes the bounded operation, and how update-copy reads are covered. Exact implementation requires review because the existing code-read trust boundary is affected.

Likely files: deployment_test/bootstrap.py, deployment_test/contract.py and deployment_test/upgrade.py only as needed for the bounded verification interface, plus focused deployment tests. No schema, provider, Core lifecycle or production changes proposed.

Validation: valid authenticated A→B; unauthorized target/read denial; path substitution/reparse rejection; incoming code import/exec denied; modified package rejected; bounded verification teardown on error; interruption; B→A; newer-data rollback refusal; native dependency and existing deployment/authentication regressions. Rollback: discard the isolated candidate and retain immutable accepted package/source; do not overwrite accepted evidence. No correction to this boundary has been implemented.

## External prerequisite

Owner confirmed no fresh Windows environment is available. Mandatory fresh-Windows recovery cannot be performed here. Same-host relocation/native-load results are not clean-machine evidence. Current-user DPAPI blobs are not portable enrollment; the existing clean-machine recovery design also requires an explicitly reviewed recovery/trust-transfer mechanism. No machine, security installation, credential transfer or fresh identity substitution was attempted.

## Disposition

- Stage 6: incomplete; source reconciliation and positive native validation progressed, full negative/native closure is not complete.
- A→B: FAIL at incoming-package verification before activation.
- B→A rollback and remaining interruption/negative campaign: NOT RUN.
- Fresh Windows recovery: NOT RUN / environment unavailable.
- Production backup/restore/cutover: NOT PERFORMED in this campaign.
- Stage 7 installer/install/update/uninstall/reinstall acceptance: NOT RUN.
- Last passing checks: Build A authenticated clients, app-local native module observations, data snapshot and authenticated shutdown.
- No final release or installer hash; no acceptance commit created. Existing accepted Stage 5 commit: 9460dbc44f63c95d1128c1a27f124f87d99b530b.
- Production unchanged. Deferred: approvals, uploads, physical media, new capabilities, native macOS.
- HISTORICAL STAGE 1 CAUSE: UNCONFIRMED. Original Stage 5 timeout cause: UNCONFIRMED.

Next required actions: review the bounded incoming-package verification correction; provide a qualifying fresh Windows recovery environment before mandatory recovery/cutover. No production activation is permitted by these results.

## Evidence

source.json records before/pending/candidate hashes. accepted/, pending/ and candidate/ preserve the three files; *.diff records changes. Native focused log, all three deployment logs/JSON files and reconciliation.json retain results and final identity/hash checks. Full synthetic TEST installations remain local, including their protected records; they must not be copied to the public project archive. Archive only the explicitly reviewed nonsecret files in this evidence folder.
