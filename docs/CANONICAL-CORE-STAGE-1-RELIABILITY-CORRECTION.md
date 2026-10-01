# Stage 1 reliability correction and diagnostic evidence

Historical root cause remains UNCONFIRMED. Production activation is blocked.

## Publication/read contention diagnostic — 2026-09-11

Status: **STOP FOR CORRECTION REVIEW**. Stage 4 runtime integration remains incomplete. This diagnostic is separately authorized by the additional investigation lead; it does not change accepted Stage 1 semantics.

### Source finding

The unchanged `tests/lifecycle_stage1/harness.py` Core loop reads challenge.json and calls write(response.json, ...) on every nonempty request, then sleeps 15ms. It does not remember the last answered challenge. Its coordinator polls at 20ms until a matching response is validated, then returns. Thus the Core continues publishing even after a successful reconciliation while the challenge remains present. This repeated-publication behavior is confirmed by source inspection; its role in the historical failure remains inferred.

### Experiment

`tests/lifecycle_stage4/fixtures.py` contains only disposable publisher/reader processes. It imports no JARVIS App, Store, providers or accepted harness. The instrumented writer preserves the temporary.write_text -> os.replace sequence, logs the exact Python operation on error, and stops on a publication error without retry. No lock, ACL, identity, provider or production change was made. No Core was started.

Each trial lasts 1.2 seconds with one unchanged synthetic challenge, separate TEST directory, one publisher and one reader (idle in the no-reader control). Mode order alternates across pairs. Per-challenge publication attempts/completions, all errors, process IDs, monotonic timestamps, source/destination paths and tracebacks are preserved. Every case and its leftover files is retained. The once-per-challenge comparator records a challenge only after successful publication and does not change Stage 1 code.

| Profile | Repeated failed/trials | Once failed/trials | Repeated successful publications |
|---|---:|---:|---:|
| Baseline 20ms reader / 15ms writer | 3/20 | 0/20 | 1,368 |
| Amplified reader, 0.5ms interval | 10/10 | 0/10 | 222 |
| Amplified reader holds open file for 10ms | 10/10 | 0/10 | 35 |
| No-reader control | 0/10 | 0/10 | 709 |

Total: **100 completed diagnostic trials**. The 23 publication failures are expected retained observations, not 23 accepted regression failures. All 23 captured `PermissionError`, `errno=13`, `winerror=5`, at `os.replace(temporary, response.json)`, with full traceback and paths. All 23 retained temporary files contain valid JSON for the unchanged challenge. Once mode published exactly once in each of 50 trials.

### Interpretation and limitations

Repeated publication materially increased observed per-trial failures under reader contention in this experiment. The no-reader control and amplified-reader profiles support a replace/read contention mechanism. This is a reproduced reliability defect/risk in the publication pattern, not proof of the exact historical failure or the identity of a blocking handle/filter.

The baseline retains Stage 1's sleep intervals but continues polling for the trial duration; real reconciliation stops when it succeeds. Therefore its failure percentage is not a production or Stage 1 incidence estimate. Fast/held-read profiles deliberately amplify overlap. Cases were run on one machine, with finite samples and alternating rather than randomized mode order; no process-wide native handle trace, antivirus attribution or power-loss testing was performed. Zero comparator failures does not prove that publishing once cannot fail, especially on a new challenge while a reader still has the prior response open. No unique-challenge transition safety acceptance is claimed by these single-challenge trials.

Historical classification remains **ROOT CAUSE UNCONFIRMED / FAIL-SAFE / REVIEW REQUIRED**. Historical os.replace remains inferred. New diagnostic failures establish the Python call and WinError for these runs only; they do not supply the missing historical traceback or WinError.

### Minimum proposed correction — NOT APPLIED

Subject to separate approval, change only the accepted Core fixture publication loop to remember the last successfully published challenge value within that Core instance and skip redundant publication for an identical value. Publish for a new challenge; update the remembered value only after write success. Keep lifetime/supervisor locks, fresh coordinator challenges, full identity comparison, timeouts and fail-closed write-error behavior unchanged. No retries, permissive sharing, ACL changes, file deletion, fabricated adoption or production changes.

Before accepting that delta, separately test unchanged challenge suppression, new challenge response, process/epoch reset, stale/malformed challenges, publication failure, missing response behavior, concurrent coordinators and the complete Stage 1 exclusion/crash suite plus Stage 2/3 regressions. Missing-response behavior must be reviewed explicitly; do not silently recreate or reuse stale responses. If once-per-challenge is insufficient, return for review rather than broaden the correction.

The defect concern triggers the user's STOP-and-propose gate. No Stage 1 correction or further client integration was performed after the experiment.

### Evidence and boundaries

- `docs/lifecycle-stage4-evidence/publication-diagnostic-review.json`: machine-readable summary, unchanged baseline verification and SHA256 manifest.
- `docs/lifecycle-stage4-evidence/publication-diagnostic-b41e867c8ffa4a7b9956caeb3d181f79/`: all 80 comparative cases, summaries, successful and failed publications.
- `docs/lifecycle-stage4-evidence/publication-diagnostic-b5c369042899488f8a68d99b403f8a34/`: 20 no-reader controls.
- `tests/lifecycle_stage4/fixtures.py`: isolated diagnostic source. No accepted Stage 1 import or monkeypatch.

All 25 preflight baseline file hashes still match, including accepted Stage 1–3 source and production modules. No Stage 1–3 regression was rerun by this diagnostic task. Earlier runs remain separate evidence.

PRODUCTION DATABASE MODIFIED: NO. PRODUCTION CORE RESTARTED: NO. PRODUCTION CONFIGURATION CHANGED: NO. STAGE 1 CODE CHANGED: NO. STAGE 5 STARTED: NO. FIX APPLIED: NO.

No commit or broad source-record sync performed. STOP FOR REVIEW of the narrow Stage 1 correction above.

## Approved isolated Stage 1 correction — validation complete

Status: **ISOLATED CORRECTION VALIDATED / STOP FOR REVIEW**. This section supersedes the earlier unimplemented-correction proposal, not its historical evidence.

### Exact change

Only `tests/lifecycle_stage1/harness.py` accepted logic changed: initialize a per-instance unanswered sentinel, compare the incoming challenge to last_answered, publish when different, then assign last_answered only after successful write returns. An unchanged challenge does not republish. No changes to lifetime locking, startup exclusion, coordinator reconciliation, identity/PID/creation checks, freshness generation, stop latch or fail-closed behavior. No retries. The accepted Stage 1 regression test file and all Stage 2 source remain byte-identical to baseline.

### Actual corrected implementation tests

`tests/lifecycle_stage4/test_stage4.py` invokes the actual corrected Stage 1 core() in disposable credential-free fixture processes. Diagnostic wrappers record calls to the actual write helper, preserve its exceptions, and observe last_answered on an exception without changing its value. This is not another production JARVIS/App/Store. Each trial uses a separate TEST namespace under the accepted harness evidence directory, real Core lifetime locking and an unchanged challenge for 1.2 seconds. The reader profiles match the preceding controlled experiment; all successful/failed artifacts remain retained.

| Profile | BEFORE repeated failures | AFTER corrected failures | AFTER successful publications |
|---|---:|---:|---:|
| Normal polling intervals | 3/20 | 0/20 | 20 |
| Faster polling | 10/10 | 0/10 | 10 |
| Reader holds response briefly | 10/10 | 0/10 | 10 |
| No reader | 0/10 | 0/10 | 10 |

Two additional actual-fixture semantic checks passed:

1. A receives a response with the actual live Core identity; fresh B receives a fresh matching response; repeated B produces no third publication; B's response does not satisfy a C challenge.
2. After successful A, a deliberately held read handle prevents publication of fail-B. The actual write raises WinError 5; its traceback is preserved; Core exception-frame inspection shows last_answered is still A. The old response remains A, the failure is recorded FAILED_CLOSED, and this fixture starts no replacement. This injected failure is a successful fail-closed test, not counted as an ordinary comparison failure. Test-local handle sharing was used solely to create the approved failure injection; accepted lock code, filesystem ACLs and Windows security settings were unchanged.

### Regressions and limits

- Full unchanged Stage 1 test suite: **20 discovered; 19 passed; 1 skipped; 0 failed/errors; 28.634 seconds**. Includes independent Core ownership, crash/recovery, coordinator loss/adoption, repeated concurrent starts, stop/start races, stale metadata, PID creation mismatch and uncertainty/fail-closed cases.
- Full unchanged Stage 2 test suite: **36 discovered; 35 passed; 1 skipped; 0 failed/errors; 67.335 seconds**. Includes composed coordinator startup races, identities, session/token validation and fake-listener credential protection.
- Stage 4 diagnostic dependency checks: **50 comparisons and 2 semantic scenarios passed**. No native bridge or real-client Stage 4 acceptance suite exists yet; no Stage 4 completion claimed.
- Python syntax parsing passed for the changed harness, unchanged Stage 1 tests and both Stage 4 diagnostic files. Stage 3 was not rerun in this correction task.
- Cross-session/other-user/actual remote-host coverage remains skipped/unverified. No production or physical-media verification was performed.

The correction removes the demonstrated redundant-publication exposure in these tests. New challenge publication can still fail; that path remains fail-closed. Finite zero-failure samples do not prove universal absence of errors. Real coordinator polling stops after success, unlike sustained diagnostic polling; percentages are experiment-specific. No missing-file recovery, production retry or speculative protocol change was introduced.

### Separate historical and new findings

HISTORICAL ROOT CAUSE: **UNCONFIRMED**. Historical classification stays **ROOT CAUSE UNCONFIRMED / FAIL-SAFE / REVIEW REQUIRED**. Its absent traceback/WinError cannot be retroactively supplied.

NEW EXPERIMENTAL FINDING: **reproducible os.replace/read-contention mechanism confirmed in isolated file-IPC tests**, with WinError 5 and exact Python traceback; corrected actual Stage 1 fixture eliminates redundant publications and had 0/50 ordinary comparison failures. No native handle/filter attribution is claimed.

Proposed reviewed reliability disposition: **reproduced redundant-publication defect corrected and validated in isolation; historical cause unconfirmed; review still required**. Production gate is NOT automatically cleared. Recommend reviewing this narrow delta and retained evidence before considering the Stage 1 reliability gate disposition; production activation and the remaining lifecycle/auth/data/client gates require separate review.

### Shortcut read-only finding

Both JARVIS INDUSTRIES.lnk and TEAGUE INDUSTRIES.lnk currently point to the same PowerShell executable, Start-Desktop.ps1 and project working directory. Both currently include `-ExecutionPolicy Bypass`; this was observed, not added or executed. The script starts Electron on the same desktop directory. desktop/main.cjs acquires requestSingleInstanceLock before startBackend; a losing instance quits and the winning instance handles second-instance by showing its window.

Consequently shortcut launches can cause competing Electron startup attempts, but do not invoke the isolated Stage 1 harness/coordinator or its TEST response files. They are unrelated to the historical isolated failure and relevant to future production startup validation. This is a source-path assessment, not a live simultaneous-launch test or a system-wide exclusion guarantee across users/profiles/direct backend starts. Neither shortcut nor production runtime was modified or launched.

### Evidence, changed files and stop

- Changed accepted file: tests/lifecycle_stage1/harness.py (only publication suppression).
- Added: tests/lifecycle_stage4/test_stage4.py (diagnostic runner, NOT full Stage 4 acceptance suite).
- Updated: docs/CANONICAL-CORE-STAGE-4.md (this report).
- Added selected evidence: docs/lifecycle-stage4-evidence/correction-TEST-54b75d4077704d88a9fd56e17eb975ed/ including comparison.json, semantics.json, summary.json, stage1-regression.json, stage2-regression.json, review.json.
- Raw corrected fixtures: tests/lifecycle_stage1/evidence/TEST-54b75d4077704d88a9fd56e17eb975ed/.
- Raw Stage 1 regression: tests/lifecycle_stage1/evidence/TEST-041ef70285514917a7b3a9c9df5751f1/results.json.
- Raw Stage 2 regression: tests/lifecycle_stage2/evidence/b4507f606d4a4e81b0e2bb08779b4a5e.json.

Of the 25 baseline files, only the explicitly approved tests/lifecycle_stage1/harness.py differs. Production modules/data/configuration/launchers/shortcuts were untouched. No production Core restart, Stage 5, production activation, repair deployment or provider changes occurred. Prior diagnostic fixtures and all prior failure evidence remain intact.

The user approved a clean correction/evidence commit after this validation. Production activation remains blocked. Subsequent Stage 4 implementation is separate from this commit.
