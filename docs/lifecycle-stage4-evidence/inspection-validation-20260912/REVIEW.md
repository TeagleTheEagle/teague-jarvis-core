# Stage 4 inspection cleanup validation — 12 September 2026

AUTOMATED INSPECTION WORKER / ARCHIVE CLEANUP GATE: PASS FOR REVIEW.
OVERALL STAGE 4: INCOMPLETE. PRODUCTION ACTIVATION: BLOCKED. STAGE 5: NOT STARTED.
No acceptance commit was created.

## Authorized cleanup

The user approved termination only of disposable TEST Core PID 18372 after
creation-time/executable/namespace verification. The preserved and fresh native
identity matched: creation value 134336887101684158, executable SHA-256
372c2eae555b344520bf147be0096e009069aeca4e7f78d6aecea6d53158056a,
namespace TEST-STAGE4-ac2fbc49c91c47f38a5e7917c9fbd5e8.

One native process handle was retained for both verification and TerminateProcess,
preventing PID reuse from redirecting termination. Exit was observed with code 1.
Launcher PID 14176 exited naturally; no launcher or unrelated process was killed.
The lifetime lock became available. Hashes of the preserved identity/journal
files remained identical. The failed TEST database was not repaired or reset.
See cleanup-verified-intent.json, cleanup-result.json, cleanup-lock-verification.json
and final-process-observation.json.

## Minimum fixture correction

Only tests/lifecycle_stage4/fixtures.py changed in this continuation, plus this
evidence/report and the Stage 4 report checkpoint. The previous inspection hook
remains in inspection_jobs.py and stage4_runtime.py; neither required a further
runtime change here.

The fresh synthetic Store originally contained no project. The actual Archive.save
requires an existing linked project and refused archiving. Before exposing the
TEST runtime, the fixture now verifies fresh storage, creates one synthetic
project using workspaces.change, binds the existing TEST archive instance to that
project, and verifies it exists. No Store/schema/workspace API/Archive code or
production project is changed. This creates a project record, not another Core,
Store or identity. The original failed namespace remains untouched.

The TEST archive callback now records operation, errno/WinError and traceback on
failure before rethrowing. Release-wait failures are distinguished from Archive.save
failures. This is synthetic-data-only diagnostic logging. It does not retry,
weaken permissions, hide UNKNOWN, or infer successful cleanup from cancellation.

The existing singleton job, trusted owner mapping and tracked worker remain
responsible for the entire panel/archive sequence. The TEST path has no nested
untracked worker or expiry timer; completed TEST results expire lazily. Legacy
background/timer behavior remains the default and has focused compatibility coverage.

## Results actually obtained

| Suite / scenario | Result |
|---|---|
| Focused inspection worker/ownership tests | 13 passed |
| Real TEST App: request cancellation + archive/drain | 43 checks passed |
| Real TEST App: owner detach/reconnect + archive/drain | 43 checks passed |
| Real TEST App: emergency cancellation + archive/drain | 44 checks passed |
| Stage 4 ownership/lifecycle model | 27 tests passed |
| Existing real shutdown deadline | 36 checks passed; recovery at 30.046 seconds |
| Actual Teague/Intelligence Electron lifecycle | 29 checks passed |
| Native identity / bootstrap | 15 / 6 checks passed |
| Unchanged Stage 1 | 24 total: 23 passed, 1 existing skip |
| Unchanged Stage 2 | 36 total: 35 passed, 1 existing skip |
| Unchanged Stage 3 | 43 passed |
| Existing Python regression | 212 passed |
| Existing desktop/Intelligence regression | 29 passed |
| Offline TEST provider regressions | 62 passed; no live provider calls |
| Static checks | 4 Python files compiled in memory; 5 JS files passed syntax validation |

These are separate suites with overlapping checks, not a sum of unique scenarios.
The focused deadline clock is injected; the 30.046-second measurement comes from
the separate real-process deadline test. After each successful archive run, a
read-only SQLite join independently verified one real archive record, its
document and its project link in the same canonical TEST database. One panel and
one archive were recorded; further panel work stopped after cancellation.

Both Electron screenshots were inspected. They show authenticated STAGE4_TEST
interfaces and truthful physical-voice/capture unavailability. This is automated
real Electron verification, not manual microphone/headset/audibility acceptance.

All five actual-App TEST runs reported exit 0. Final read-only process checks
found their recorded Core PIDs absent; both approved cleanup PIDs were also absent.
The Electron report records normal exits for its clients. No TEST Core was left
running by this validation. The earlier forced cleanup is separately recorded
as exit 1 and is not described as successful graceful shutdown.

20 protected source files, including Stage 1–3, server, Store, providers,
ownership/lifecycle, VoiceEngine and launchers, hash-match the regression baseline.
Production data/configuration/authentication and the running production Core were
not changed or restarted. No paid API call, physical capture, actual repair
execution, provider expansion, installer or Stage 5 work occurred.

## Preserved failure and limitations

The first inspection run remains FAILED: 35 preceding checks passed, then archive
and cleanup acceptance timed out. Its journal retained UNKNOWN. The original
archive exception was masked by the existing handler, so its exact traceback was
not captured. Missing synthetic project was established from read-only database
contents and source; supplying that prerequisite made the actual archive path
pass. Do not replace this historical record with the subsequent passes.

The original Stage 1 PermissionError remains HISTORICAL ROOT CAUSE UNCONFIRMED.
The independently reproduced response-publication and IPC guard mechanisms remain
separate findings. This fixture failure supplies no evidence of a common cause.

Stage 1's second-session/fast-user-switching test and Stage 2's other-user/
cross-session/actual-remote-host test retain their existing skips. Physical voice
remains deferred. Ordinary chat/TTS/inspection are not universally budget-metered;
cancellation never proves zero spend or authorizes refunds.

## Remaining Stage 4 path

This closes the automated inspection cancellation/archive-worker requirement only.
The remaining approved work includes repair worker/cleanup registration with
synthetic outcomes and conservative reservation accounting (no actual repair),
pending-approval revocation and stream/upload ownership coverage, the outstanding
Stage 4 process-race/crash breadth, lease-watchdog/media integration, human lifecycle
control validation and separately authorized physical/manual verification.
Disabled routes are not certified merely because they fail closed. Overall
Stage 4 acceptance and its commit remain pending; production and Stage 5 stay blocked.

Next priority: bounded repair-worker/cleanup and reservation-outcome validation
inside the already reviewed TEST scope. This checkpoint does not implement it.

## Rollback / evidence

before/tests/lifecycle_stage4/fixtures.py is the exact pre-correction fixture.
diffs/ records the current continuation; source/ includes the four existing
inspection-related files for reproducibility. A rollback must use only these
hunks after verifying TEST process exit, preserving unrelated dirty source and
all failed/successful evidence. Reverting the fixture alone reintroduces the
missing-prerequisite test failure; do not run that as a supposedly valid fixture.
The earlier inspection-cleanup-20260912 package preserves pre-hook bytes if a
broader reviewed rollback is later needed. Never restore/reset any database as a
code rollback. Machine-readable validation, source hashes and a copy manifest
accompany this report; credentials and databases are excluded from the package.
