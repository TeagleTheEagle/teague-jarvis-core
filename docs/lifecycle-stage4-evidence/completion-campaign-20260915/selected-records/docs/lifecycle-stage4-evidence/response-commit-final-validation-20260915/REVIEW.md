# Response-commit gate — final frozen-source validation

2026-09-15. **Response-commit requirement: CLOSED. Stage 4 overall: INCOMPLETE. STOP FOR REVIEW.**

The three remaining validation items passed. This closes gate 1 in the remaining-requirements matrix, not Stage 4 as a whole. No response-commit implementation, Store interface, Electron behavior or production state changed. No paid provider call was made.

## Executed checks

Exact commands, working directory and exit results are in [commands.json](commands.json). All executions used the ordinary command context; no Electron invocation was needed in this checkpoint.

| Requirement / execution | Actual result | Evidence |
|---|---|---|
| Existing text-only fallback integration | 12/12 PASS | `fallback-integration.log`, `results/fallback-integration-results.json` |
| Existing fallback fresh-process history helper | 4/4 PASS | `fallback-restart.log`, `results/fallback-restart-results.json` |
| Existing dedicated Deep Review integration | 14/14 PASS | `deep-review-integration.log`, `results/astra-integration.json` |
| Existing Deep Review fresh-process helper | 4/4 PASS | `deep-review-restart.log` |
| Supplemental fallback and Deep Review fresh-process/restart validation | 4 sequential child processes; 88/88 checks; all exits 0; no live workers at exit | `fresh_process_validation.py`, `fresh-process-results.json`, `fresh-process.log` |
| Actual authenticated TEST pipe / Deep Review integration | 8/8 PASS; TEST Core exited 0 | `deep-review-pipe.log`, `results/astra-pipe-42693ba6c7254efe94316ad4cfd2cd07.json` |
| Directly affected offline provider regressions | 62/62 PASS | `provider-regressions.log` |
| Standalone Python syntax | 15/15 files PASS | `standalone-syntax.json` |
| Standalone JavaScript syntax | 5/5 files PASS | `standalone-syntax.json` |
| Independent post-exit SQLite inspection | 5 TEST databases PASS; no orphan assistant messages, orphan successful provenance or duplicate responses | `independent-sqlite-verification.json` |

The pipe probe's inherited console wording includes “Electron checks”; this invocation did **not** launch Electron or provide new UI evidence. Actual Electron acceptance was already closed by the prior approved 29-check host-context run.

Python syntax validation used `compile(source_bytes, filename, 'exec')` without importing or executing those files or creating bytecode. The 15 files comprise 14 existing affected/runtime/test files and the new validation driver. JavaScript used `node --check` on the five exact files listed in the syntax record. Syntax success is not runtime validation.

## Fresh-process and persistence evidence

The additional validation fills two limits of the existing helpers: a deterministic **last completed fallback** query after restart, and explicit old-token / old-request-authority rejection across a new TEST epoch. It imports the frozen TEST Context/App/Store and calls the existing trusted authenticated dispatcher seam. It adds no runtime route, authority or persistence behavior.

| Mode | Seed process PID / creation FILETIME | Fresh restart process PID / creation FILETIME | Canonical TEST data identity |
|---|---|---|---|
| Text-only fallback | 19816 / 134339213507482594 | 22000 / 134339213510957129 | Recorded unchanged in `fresh-process-results.json` |
| Deep Review | 22592 / 134339213513620787 | 17832 / 134339213517100487 | Recorded unchanged in `fresh-process-results.json` |

All four child processes reported the same expected executable SHA-256, `372c2eae555b344520bf147be0096e009069aeca4e7f78d6aecea6d53158056a`. Each held the real TEST lifetime lock, constructed one App/Store/VoiceEngine/WakeDetector, obtained new TEST sessions and exited before its successor started. PID plus creation identity establishes these were fresh processes; PID alone was not used. These are completed-run observations, not identifiers for future cleanup.

For each mode, validation established:

- Explicit mode admission and the expected owner/original session in the durable response record.
- One final event matching the committed answer; duplicate submission returned the original response without a new worker/generation.
- Completion before cancellation retained the historically truthful COMPLETED answer and provenance.
- Cancellation during generation was durably acknowledged before releasing the deterministic fixture transport. No final event, answer text or successful attribution appeared afterward; the cancelled request did not replace the last completed response.
- After a fresh process reopened the same TEST database, the exact completed record and deterministic last-provider result survived. Cancelled state survived too.
- Old TEST session tokens were denied. A fresh session could read its owner's history but could not cancel or inspect the old work item. Foreign-owner provenance queries were denied.
- General tool execution remained prohibited for these requests. Separately authorized TEST shutdown reached FINALIZING with no live worker, and every child exited 0.

The fallback provider call and OpenAI 429 were **simulated** by the existing offline router. Provenance truthfully identifies fixture Ollama / `qwen3:4b`, fallback reason `temporary_rate_limit`, and `simulated: true`. Deep Review used the existing deterministic fixture, explicit `DEEP_REVIEW`, medium effort, fixture OpenAI / `gpt-6-astra`, and `simulated: true`. These are not live-provider generation, latency, spend or quality claims. No credential was read or copied for this validation.

The stale TEST token was transferred only through private parent/child pipes for the rejection check. Neither raw token envelopes nor credentials are in the public evidence or archive.

### What “assistant response commit” means in these existing paths

The reviewed text-only and Deep Review implementation stores answer text and final provenance in the **same `stage4_response_provenance` row**, through the shared response boundary. It does not also insert a separate conversation `messages` row for those modes. Normal chat uses the reviewed Store transaction interface to commit its assistant message and linked provenance together.

Independent read-only SQLite queries after process exit verified that representation: each successful record has answer text, owner/session and provider/model attribution; cancelled records have no durable answer or successful provider; every normal assistant-message link agrees with the stored content; there are no unlinked assistant messages or duplicate response/operation identities. `PRAGMA quick_check` passed and the isolated TEST application identity was verified for all five databases. No separate assistant-message row was invented to satisfy the test.

### Restart scope limitation

These fresh-process tests use the already approved integration/helper composition: a new TEST Context/App opens the existing TEST database under its lifetime lock and establishes a new epoch and sessions. They do **not** exercise a coordinator's authorized start-after-stop policy, repeated startup contenders, crash recovery or actual client authentication across Core epochs. The existing stop latch was not deleted or modified to manufacture a startup pass. Thus these results close response/provenance restart persistence, not the separate full lifecycle restart matrix (gate 2).

## Retained evidence and source binding

[source-after.json](source-after.json) verifies all 19 prior reviewed source/executable reference paths and seven additional affected paths unchanged. [retained-evidence.json](retained-evidence.json) records hashes and locations of the prior evidence. The following are **retained final-source results, not reruns in this checkpoint**:

- Shared transaction correction: 918 trials / 14,244 assertions across normal chat, text-only fallback and Deep Review. Ordered controls exercised both legal outcomes; all simultaneous-release trials chose cancellation. No claim is made about a natural outcome distribution.
- Two actual authenticated polling probes: 43 checks each, independently verified against durable SQLite state.
- Stage 1: 23 pass / 1 skip; Stage 2: 35 pass / 1 skip; Stage 3: 43 pass; Python: 212 final passes with isolated development-history fixture; desktop/intelligence units: 29; native peer: 15; bootstrap: 6; recorded actual Core lifecycle and worker-cleanup checks. Prior failures remain in their original packages.
- Actual Electron: 29/29 host-context checks, both actual clients, previously inspected screenshots and normal exits, against the same frozen source.

Only directly affected provider regressions and the dedicated integration paths were refreshed here. No changed runtime source or unresolved issue warranted repeating the broader passing suite.

The restricted-context **Electron 44.2.0 GPU process failure** remains a disclosed execution-environment limitation. The observed exit status is consistent with STATUS_DLL_NOT_FOUND; the exact missing/inaccessible DLL and root cause remain **UNCONFIRMED**. The same frozen source passes host-context Electron validation. No GPU flag, DLL, security, cache/profile or runtime change was made. The historical Stage 1 PermissionError also retains its separate unconfirmed classification; this validation supplies no new evidence about its cause.

## Preserved failure

All runtime validations in this checkpoint passed. One independent post-exit audit command had a missing closing bracket and failed Python parsing before executing any statement. The failure is retained in `audit-command-01-failure.json`. Only the inspection command was corrected; no runtime source was changed or runtime test retried. The successful independent inspection is recorded separately. Earlier runtime failures and screenshots were not removed or reclassified as passing.

## Reconciliation, changes and rollback

| Response-commit acceptance item | Status |
|---|---|
| Fresh-process fallback provenance / restart | **CLOSED** |
| Dedicated Deep Review integration / restart | **CLOSED** |
| Final standalone Python / JavaScript syntax | **CLOSED** |
| Shared cancellation/completion invariant and authenticated polling | **CLOSED — retained frozen-source evidence** |
| Actual Electron dependency | **CLOSED — prior host-context evidence retained** |
| Overall response-commit / event-polling gate 1 | **CLOSED** |

Changed authored files are the evidence-only validation driver, this package's reports/records, `docs/CANONICAL-CORE-STAGE-4.md` and `docs/STAGE4-REMAINING-REQUIREMENTS-20260915.md`. Existing probes also wrote the recorded isolated TEST outputs. No frozen runtime source was edited. `before/`, `current/` and `documentation.diff` preserve the exact documentation delta. `files-changed.json` inventories the authored/collected package.

Rollback needs no runtime, schema or production data action. After checking for later edits, reverse only `documentation.diff` to undo the status update; preserve this evidence and the validation driver as historical records. TEST databases, private handshake/session material and profiles remain in the isolated workspace and are excluded from the archive. The selected nonsecret package is SHA-256 inventoried and its TEAGUE INDUSTRIES DATABASE copy is verified separately.

**Next unresolved gate only:** gate 2 — full real-Core stop/start, crash/restart and repeated startup-race matrix. Its status remains PARTIAL. It was not started. Approvals and uploads remain DEFERRED, not PASS; other Stage 4 gates are unchanged.

PRODUCTION SOURCE / DATA / CONFIGURATION CHANGED: NO  
PRODUCTION CORE RESTARTED: NO  
FROZEN RESPONSE-COMMIT / ELECTRON SOURCE CHANGED: NO  
PAID PROVIDER CALLS: NONE  
STAGE 4 ACCEPTANCE COMMIT: NONE  
STAGE 5 STARTED: NO

**STOP FOR REVIEW.**
