# Stage 4 inspection cleanup checkpoint — 12 September 2026

Status: INCOMPLETE / FAILED REAL-APP ACCEPTANCE / TEST CLEANUP REVIEW REQUIRED.
Production activation remains blocked. No Stage 5 or acceptance commit.

## Scope and implementation

This advances the approved inspection ownership/cleanup gate in
CANONICAL-CORE-STAGE-4-OWNERSHIP-DRAIN-DESIGN.md sections G and I. Ollama
Independence and the validated provider experiments remain preserved future work.

Changed source:

- inspection_jobs.py: optional synchronous registered-worker entry using the
  existing JOBS singleton and existing inspection/archive implementation. The
  trusted caller supplies cancellation and a per-step admission check. The TEST
  path creates no nested worker or expiry timer. Completed TEST results expire
  lazily on get/start; active archive work cannot be evicted as expired. Legacy
  background start/timer behavior remains the default.
- stage4_runtime.py: authenticated TEST inspection start/status, lifecycle
  ownership, existing cancellation and trusted synthetic runner binding. Archive
  failure is UNKNOWN because partial writes must not be assumed absent.
- tests/lifecycle_stage4/test_stage4.py: 13 focused inspection/lifecycle tests.
- tests/lifecycle_stage4/fixtures.py: actual TEST App/archive probes for cancel,
  detach/reconnect and emergency. Only the cancel variant ran.
- docs/CANONICAL-CORE-STAGE-4.md: checkpoint link/status.

The common inspection source file has an optional TEST hook; the running
production process, production database/configuration/authentication, launchers,
providers, personality and voice were not changed or restarted by this work.
No physical media capture or provider calls were performed.

## Checks actually performed

13/13 focused tests PASS. These use actual inspection job code and real tracked
threads, synthetic panel/archive callbacks, and an injected deadline clock.
Coverage includes foreign status/cancel rejection, archive completion before
drain, detach/reattach isolation, archive failure retaining UNKNOWN, deadline
quarantine, safe expiry, closed admission, cancelled-before-start, no subsequent
panel/summary after admission closes, emergency suspension, singleton contention,
and legacy background/timer compatibility. They are not physical/Electron tests.

First real-App inspection-cleanup probe: 35 checks passed before process exit
timed out; cleanup also timed out. This run FAILED and has not been retried.
Original evidence: ../real-app-probe-b2d796cec9c44e36a79aa55f8b1924a2.json.
It verified authenticated client isolation, actual local-time/silent synthetic
voice paths, cancellation reaching the archive, pending archive counted as
active work, new inspection admission denied during drain, and lifetime lock
retained while the archive was held. Successful archive and exit were NOT proven.

Stage 1–3/full Python/desktop regressions were NOT rerun in this checkpoint;
they remain required after the fixture issue and cleanup are addressed. Previous
passes do not erase this failure. The detach/emergency inspection variants and
physical/manual checks remain NOT RUN.

## Failure diagnosis and retained TEST process

Namespace: TEST-STAGE4-ac2fbc49c91c47f38a5e7917c9fbd5e8.
Actual TEST Core PID: 18372. Virtualenv child launcher PID: 14176.
Recorded/live Core creation value: 134336887101684158.
Recorded/live executable SHA-256:
372c2eae555b344520bf147be0096e009069aeca4e7f78d6aecea6d53158056a.

Read-only checks found zero TEST workspaces, zero inspection_records and no
archived files. Existing Archive.save requires linked project
0383e8c2e67346b59c484a5766b581f4 and refuses its absence before archive writes.
The synthetic fixture never provisioned this prerequisite. The existing job
handler masks archive exceptions, so an original traceback was not captured;
the source/database diagnosis is not a captured exception traceback.

The inspection journal records UNKNOWN. Automatic cleanup did not bypass that
outcome. The Core remains quarantined with lifetime ownership and the existing
TEST controller retained. No forced termination, guessed settlement, journal
rewrite, deletion or replacement Core was attempted. Identity checks and
read-only counts are in failed-run-diagnosis.json and failed-run-processes.json.
Recheck native identity immediately before authorized cleanup; PID is not enough.

This TEST fixture prerequisite failure is separate from the historical Stage 1
PermissionError (root cause still UNCONFIRMED), corrected repeated-response
publication defect and separately validated IPC contention guard.

## Minimum next step and approval boundary

1. Obtain approval for identity-reverified cleanup of disposable TEST Core PID
   18372. Prefer a supported authenticated graceful path; the existing path
   refused uncertain completion. Let launcher/controller exit naturally and
   preserve evidence. Uncertain identity means stop.
2. In the already approved fixture file, seed the required synthetic inspection
   project in fresh TEST storage using the existing workspace API, and check it
   before dispatch. Do not change the failed database or weaken UNKNOWN behavior.
3. Preserve a nonsecret diagnostic failure record for the TEST archive callback.
4. Rerun focused tests, real cancel/detach/emergency probes and required Stage 1–4
   and Python/desktop regressions. No production run or physical media.

Earlier forced-cleanup authorizations named other PIDs and do not authorize this
newly identified Core. No broader architecture change is proposed.

## Rollback and evidence

before/ preserves exact pre-edit bytes for affected source and the Stage 4
report. source/ and diffs describe this checkpoint only. After verified TEST
process exit, revert only these hunks; never reset the unrelated dirty tree.
Retain failed namespace/journal/data/evidence. Never restore an older database
or reset the live process to make a failed result disappear.

The package includes explicit source/evidence hashes. No credentials or
production database are included. No acceptance commit was created.
