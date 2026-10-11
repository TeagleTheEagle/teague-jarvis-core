# Canonical JARVIS Core — Stage 3 isolated data preservation rehearsal

Date: 2026-09-11. Implementation and test evidence; NOT production migration.

Final Stage 3 result: **43 passed, zero failures/errors, 7.853 seconds**. Stage 2 unchanged: **35 passed, one skipped, 65.874 seconds**. Stage 1: initial 18 passed/one failed/one skipped; subsequent unchanged rerun and three further sequential runs each **19 passed/one skipped**. The additional runs took 28.377, 28.606 and 28.637 seconds. All failing evidence is retained; the issue remains **ROOT CAUSE UNCONFIRMED / FAIL-SAFE / REVIEW REQUIRED**. Nine Python files compiled/static-reviewed successfully. Staged whitespace checks pass after removing blank-line SQL trailing spaces only.

Stage 0 — architecture: PASS (approved direction). Stage 1 — ownership/exclusion: safety invariant retained; final reruns PASS with unresolved reliability review item. Stage 2 — isolated authentication: PASS within its previously documented limits. Stage 3 — data/migration rehearsal: PASS for the cooperative synthetic model; NOT a production cutover approval.

**ONE JARVIS. ONE CORE. ONE IDENTITY. ONE CANONICAL MEMORY.**

Production database moved: NO. Production database modified by this work: NO. Production Core restarted: NO. Production configuration changed: NO. Stage 4 started: NO.

## Audit and provenance

The read-only audit inspected `store.py`, `workspaces.py`, `project_budgets.py`, `recovery.py`, `server.py`, their schema declarations and data-directory entry names. It did not instantiate App/Store, open production SQLite, query conversation content, read secret files or contact a live Core. Source fingerprints and nonsecret findings are in `lifecycle-stage3-evidence/persistence-audit.json`.

Source normally selects ROOT/data/jarvis.sqlite3, but --data-dir and frozen APP_ROOT logic can override it. **Actual live Core database handle/provenance remains UNVERIFIED.** Source defaults and directory existence do not prove the running authority. This is a gate before any future production copy/cutover, not something inferred from synthetic tests.

Current persistence includes items (memory/tasks), messages, reminders, settings, audit, feedback, documents, task_meta, research, turn_evidence, workspaces, workspace_links, project_budget_limits and project_budget_reservations, plus SQLite's sequence table. Settings also carry structured state; user_version=1 is insufficient to establish the complete additive schema. Existing budget states include held, started, recovery_required, settled and released, with consumption, expiry, revision and evidence fields.

Observed external categories include provider-shadow.jsonl, inspection archives, generated content, development/update history and model caches. Existing recovery.py contains useful backup concepts, but imports were deliberately avoided: its production root selection and restore paths are outside this stage. No shared production module required modification. Source-audit findings are not a declaration that every observed directory is canonically approved to migrate.

## Implemented files and isolation

- `tests/lifecycle_stage3/fixture.sql`: frozen schema extracted by reading literal SQL from source ASTs, with budget additive columns mirrored explicitly. No production module execution.
- `fixtures.py`: creates fresh TEST namespaces containing entirely synthetic records and eight synthetic persistent artifacts. Holds a WAL connection open for realistic committed-but-uncheckpointed tests.
- `migration.py`: isolated lock, consistent SQLite backup, journal, staging, verification gate, atomic TEST mapping publication, explicit recovery and rollback.
- `verify.py`: separate read-only verifier with no migrator/production imports, database integrity/schema/table-content checks and artifact hashes.
- `test_stage3.py`: positive/negative, actual subprocess crash, concurrency, rollback and independent direct-SQL/byte-comparison tests.
- Local .gitignore: excludes disposable fixture directories, WAL files and runtime evidence from automatic staging. Only explicitly selected nonsecret evidence is exported.

Writable roots must be immediate TEST-UUID children of this harness's evidence directory, with a matching marker. Fixed source/backup/staging/canonical paths prevent arbitrary production destinations. Ancestors and nested entries reject reparse points; hardlinked files are rejected. The migration lock is a non-inheritable Windows CreateFileW handle with share mode zero, OPEN_ALWAYS and open-reparse-point semantics. File existence is not ownership, and active lock files are never deleted to break a lock.

These controls protect the cooperative isolated test model. They are not a hostile same-user filesystem security boundary: path checking is not handle-relative traversal, and test policy/journal files are not authenticated. A malicious same-user actor could alter fixture policy or race path checks. No production-grade claim is made.

## Persistent state contract

Every row in all 15 tables (14 application tables plus sqlite_sequence) is preserved without transformation or duplicate insertion. Table checks use type-tagged cell representations and order-independent row hashes; schema objects and user_version are compared separately. Memory, conversations, tasks, project links, approval history, provider configuration, shadow-only status and review-only repair status are represented synthetically. Budget/reservation consumption, expiry, revision and uncertain recovery states are retained exactly; migration neither refunds nor spends reservations and never replays work.

Synthetic external records separately represent personality text, provider telemetry, repair verification, device configuration, evaluation, UI state, recovery and a binary artifact. They are explicitly enumerated by the fixture's approved artifact policy. Missing or unclassified persistent artifacts fail closed. Top-level runtime, secrets and cache fixtures remain in source and are excluded from backup/publication. Unknown top-level entries fail classification rather than being silently omitted. Persistent approval/history is preserved as history, not activated authority.

The fixture has no interpreter of saved goals, reminders, approvals, online presence, repair candidates or device readiness. There is no start, tool execution, provider call, deployment or scheduling API. Persistent data is not authority. The Stage 3 future-compatibility addendum and governing principle are included as design constraints, not implementation of future autonomy.

## Backup, staging and journal

1. Validate isolated paths, TEST identities, mapping identity, operation ID and empty destination. Acquire exclusive migration ownership.
2. Write an operation-bound PREPARED journal atomically using a flushed sibling file and os.replace. All existing journal states are reconciled explicitly; conflicting operation IDs are refused.
3. Open existing TEST source only (`mode=rw`, never create-if-missing), take SQLite BEGIN IMMEDIATE as a write reservation, and record an independently computed expected dataset. Back up with sqlite3.Connection.backup from a separate read-only source connection. A progress callback limits backup time and supports explicit fault injection.
4. Copy approved artifacts and identity. Compare the source again and independently verify backup before recording BACKED_UP. Commit no source SQL mutations; release the reservation by rollback/close.
5. Copy backup into staging, independently verify it, record VERIFIED, then rename staging to canonical on the same volume. Record PUBLISHED. Recheck source and destination identity/content before atomic TEST mapping change. Record ACTIVE only after mapping publication.

The journal is separate from the dataset, with no credentials. It records namespace, operation, phase, expected hashes/counts and conservative raw rollback stamps. PREPARED/BACKED_UP interruption is retained and requires cancellation/review; it is not automatically retried. Explicit recovery can complete a VERIFIED/PUBLISHED operation after rechecking source/candidate, including rename-to-journal and mapping-to-journal crash gaps. If candidate/source changed, recovery refuses. Same-operation ACTIVE replay verifies and returns idempotently; another operation ID cannot reuse its journal.

SQLite write reservation protects the database snapshot while backup occurs. Artifact comparison detects the exercised concurrent mutation, but artifacts do not participate in SQLite transactions. This model requires cooperative artifact quiescence and no writers across final TEST cutover/rollback. It does **not** prove atomicity against arbitrary noncooperating writers after the final check; a production maintenance gate remains mandatory. Likewise atomic rename is tested against process interruption, not sudden power loss or storage-controller durability. Directory flush/power-failure guarantees and cross-volume cutover are not established.

## Independent verification

The separate verifier opens only an existing database with mode=ro, trusted_schema=OFF and a read transaction. It checks integrity_check, foreign_key_check, all schema objects, version, every table's row count/content hash and every approved artifact hash. It also checks fixture budget state/consumption consistency and exact identity. The audited production schemas do not declare foreign keys, so foreign_key_check is not proof of every application-level relationship. Exact data preservation and synthetic linked-record comparisons are tested; no broader production semantic reconciliation is claimed.

Test 39 supplies a second oracle independent of the inventory/manifest functions: direct SQL rows for every table and direct bytes for every artifact, captured before migration and compared after it. Corrupting staging SQLite or omitting an artifact blocks publication; subsequent database tampering is detected. All expected data and exported identities refer to synthetic fixtures only.

## Rollback boundaries

| Boundary | Tested behavior |
|---|---|
| Before cutover | Keep source mapping; mark cancellation; retain backup/partial staging/journal for review. Delete nothing |
| After cutover, no new writes | Verify original and canonical state/stamps, atomically return TEST mapping to source, retain both copies. Repeat rollback returns the same terminal state |
| After new writes | Refuse naive rollback. Keep canonical mapping and new records. New database rows, changed external artifacts, old-source writes and post-crash candidate changes are exercised |

Raw SQLite/WAL and artifact stamps make rollback conservative: harmless checkpoint/file changes can also cause refusal. This stage does not implement reverse migration or merging after new writes. Refusal plus retention is the safe tested outcome; a separately reviewed compatible runtime/reverse-migration path would be required to proceed. User-visible persistent state is never silently rolled back merely to restore an older runtime.

## Test matrix

| Tests | Evidence |
|---|---|
| 01–04 | All tables/artifacts; committed WAL inclusion; uncommitted writer rejection; concurrent SQL write blocked during backup |
| 05–10 | Runtime/secrets exclusion, corrupt database, full-schema mismatch, source identity, nonempty destination and outside-root rejection |
| 11–14 | Actual hardlink and junction rejection, injected ENOSPC, actual Windows read-only mapping PermissionError |
| 15–18 | Corrupt/omitted candidate material, source artifact mutation, independent database-tamper rejection |
| 19–20 | Same-operation idempotency/conflict; three fresh four-process migration races, one publishing owner per namespace |
| 21–25 | Three rollback boundaries, including refusing new canonical database/artifact data or changed legacy source |
| 26 | Real os._exit(83) subprocess crashes at prepared, backup-copy, backed-up, verified, renamed, published and mapped boundaries; OS lock reacquisition; explicit safe recovery or refusal |
| 27–32 | Corrupt journal/reservation, stale reservation preservation, missing source without empty creation, unknown class, refusal to recover over post-crash new writes |
| 33–38 | Destination/mapping identity, schema version, unclassified nested secret, missing verification artifact and budget overspend refusal |
| 39–43 | Direct SQL/byte oracle, ENOSPC during backup, no child lock inheritance, source change before explicit recovery, concurrent idempotent rollback |

ENOSPC is deliberately injected at two write boundaries; the physical disk is never filled. Permission and link failures use real Windows semantics within disposable test paths. Process crashes are real; power-off, hardware faults, antivirus behavior, production-scale data and cross-volume migration are unverified.

## Development and regression findings

The first 32-test development run recorded ten failures and one error (including crash-boundary subtest failures): isolated-mode CLI imports could not find verify.py, and the junction command was overquoted. Both test-launch issues were corrected within Stage 3. The second 32-test run passed. An expanded 43-test run passed. Review then improved rollback idempotency so repeated rollback preserves the original terminal phase rather than relabeling it; final validation follows that change. Every selected failed/passing run is retained separately.

The first unchanged Stage 1 rerun failed test_15_more_crash_boundaries: the fixture Core emitted FAILED_CLOSED/PermissionError (errno 13) during its file-based handshake; replacement returned RECOVERY_REQUIRED instead of adopted. The source writes response.json via os.replace while another process reads it; Windows sharing contention is a plausible cause, not conclusively proven by the exception-class-only trace. No second lifetime-lock owner was observed. This is a pre-existing Stage 1 reliability finding, not something fixed or hidden in Stage 3. Stage 1 code remains unchanged; the failed trace remains a review/production gate even if a fresh rerun passes. Final counts and all rerun paths are in closure.json.

## Commands, evidence and limits

### Stage 1 anomaly classification

**ROOT CAUSE UNCONFIRMED / FAIL-SAFE / REVIEW REQUIRED**

Read-only inspection found a complete, parseable `response.json.db463a5ae52e4a8f855c1bbaf8375562.tmp` next to response.json in the failed TEST namespace. Its identity and challenge match the current fixture metadata. The likely failing operation is `os.replace(temporary, response.json)` in Stage 1's write helper; the preserved trace has no traceback or filename, so that exact operation is an inference. `PermissionError` and Python errno 13 are recorded. A Win32 `winerror` value was not recorded and cannot be reconstructed reliably.

The current target also matches the challenge, consistent with the Core repeatedly publishing a response while the coordinator checks it. A concurrent reader preventing replacement is plausible on Windows. Existing read-only attributes were not set on target or temporary file. The narrow Windows Defender Operational query over the failure window returned NoMatchingEventsFound; this neither proves nor excludes antivirus/indexer activity, including third-party software. No security setting was changed and no monitoring service was installed. Cleanup creates a stop latch after the failed assertion and does not delete response files; available timing does not establish cleanup as the cause. Full access/handle tracing was not available in the original run.

Thus a Stage 1 file-transport liveness/design issue is plausible; it is not justified to call this merely environmental or non-blocking. The existing exception handler demonstrably fails closed. In the affected namespace there was exactly one spawn, one successful Core-lock acquisition and one RECOVERY_REQUIRED; no replacement spawn followed the failure. Every recorded namespace in that failed run had at most one Core acquisition. A matching metadata response did not override inability to prove live lock ownership.

Three additional sequential unchanged complete Stage 1 runs were requested for repeatability. Their raw results and aggregate observations are retained separately. A later PASS does not erase the earlier failure or statistically establish a failure rate. No Stage 1 source, timeouts, error handling or test expectations were changed. Any fix to its file-response publication/reconciliation semantics must be a separate reviewed change. Proposed future review: first capture exact operation/filename/winerror and handle-sharing evidence; then assess an appropriate bounded IPC/publication change while preserving lifetime-lock ownership and fail-closed behavior. That work is not implemented here.

Commands run from `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis`:

```powershell
& .\.venv\Scripts\python.exe -I tests/lifecycle_stage3/test_stage3.py
& .\.venv\Scripts\python.exe -I tests/lifecycle_stage1/test_stage1.py
& .\.venv\Scripts\python.exe -I tests/lifecycle_stage2/test_stage2.py
git diff -- tests/lifecycle_stage1 tests/lifecycle_stage2
git diff --cached --check
```

Python AST/import review and py_compile cover all nine Stage 1/2/3 Python files. Only standard library and local fixture modules are imported. Stage 1/2 source diffs must remain empty. Machine-readable `closure.json`, `persistence-audit.json`, source hash/validation records and selected test JSON files accompany this report. They contain no production content, tokens or fixture secrets. Raw disposable namespace trees (including junctions and fake secrets) are not exported.

No production regression suite, production backup, live provider call, repair workflow, Core restart or installer run occurred. Production provenance, complete real-data classification, secret migration policy, filesystem quiescence, durable commit semantics, signed policy protection and unresolved Stage 1/2 reliability/security gates require review before production adoption. Stage 2's other-user, cross-session and actual remote-host cases remain explicitly unverified.

This commit contains Stage 3 implementation/tests/evidence/documentation only, including its approved compatibility addendum. Existing unrelated working-tree changes are excluded. Stage 4 is not authorized by completing this rehearsal. STOP FOR REVIEW.
