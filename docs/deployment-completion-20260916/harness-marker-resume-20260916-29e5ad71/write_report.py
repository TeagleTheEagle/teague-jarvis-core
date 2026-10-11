"""Write the stopped validation disposition from preserved results; no tests or runtime calls."""
from pathlib import Path
import hashlib,json,time
D=Path(__file__).resolve().parent
read=lambda n:json.loads((D/n).read_text(encoding='utf-8-sig'))
s=read('stopped-validation.json');integrity=read('final-integrity.json');targeted=read('targeted-results.json');restart=read('restart-reconciliation.json')
census=read('process-reconciliation.json');snapshot=read('native-process-snapshot.json');resolved=[]
for row in census['rows']:
    if row['status']!='UNKNOWN':continue
    current=next((x for x in snapshot['rows'] if x['pid']==row['expected']['pid']),None)
    assert current and current['created_filetime']!=row['expected']['created']
    resolved.append({'expected':row['expected'],'original_query':'UNKNOWN / errno 5',
        'current_creation_filetime':current['created_filetime'],'current_name':current['name'],
        'disposition':'PID_REUSED_NOT_TOUCHED','reason':'CIM creation time differs from preserved TEST creation identity; executable access was not needed to exclude this identity.'})
assert not [x for x in census['rows'] if x['status']=='MATCHING_TEST_IDENTITY_LIVE']
assert not [x for x in snapshot['rows'] if x['native_command_match'] or x['pid']==19724 or x['parent_pid']==19724]
cleanup={'at':time.time(),'exact_recorded_identities':len(census['rows']),'absent':sum(x['status']=='ABSENT' for x in census['rows']),
    'pid_reuse_exclusions':resolved,'native_command_matches':0,'native_runner_matches':0,'no_termination_performed':True,
    'limitation':census['limitation'],'result':'No matching recorded TEST identity or matching native probe command remains in this observation.'}
assert not (D/'cleanup-reconciliation.json').exists();(D/'cleanup-reconciliation.json').write_text(json.dumps(cleanup,indent=2),encoding='utf8')
matrix={'marker':'PASS','targeted':'PASS','restart_lifecycle':'PASS','full_acceptance':'FAIL',
    'native_expected_success':'FAIL','remaining_19_command_groups':'NOT RUN - stopped on native failure',
    'actual_candidate_electron_rerun':'NOT RUN - stopped on native failure',
    'final_standalone_syntax':'NOT RUN - campaign stopped',
    'approvals':'DEFERRED - WORKFLOW NOT PRESENT IN CURRENT STAGE 4 PRODUCT SURFACE',
    'uploads':'DEFERRED - REQUIRES SEPARATE AUTHORITY / PERSISTENCE REVIEW',
    'physical_media':'DEFERRED - no new hardware/media authority',
    'response_commit':'PASS - 306 trials / 4748 assertions, direct SQLite integrity and linkage checks passed',
    'acceptance_commit':'NOT CREATED','production':'UNTOUCHED / NOT ACTIVATED','stage4':'INCOMPLETE','stage5':'NOT STARTED'}
(D/'acceptance-disposition.json').write_text(json.dumps(matrix,indent=2),encoding='utf8')
rows='\n'.join(f"| {x['group']} | {'PASS' if x['exit']==0 else 'FAIL'} | {str(x['unit_tests'])+' unit tests; '+str(x['skipped'])+' skipped' if x['unit_tests'] is not None else 'Case/assertion evidence; see log and raw report'} |" for x in s['totals'])
report=f'''# JARVIS Stage 4 — marker correction and stopped acceptance

Full acceptance is **INCOMPLETE**. The only source change in this turn is the approved TEST marker. All 25 targeted tests and the separate 636-check restart/lifecycle gate passed. The full campaign then stopped at its native peer-identity probe: 14 native checks passed and the expected-success check failed. No acceptance commit was created.

## TEST MARKER CORRECTION

- Changed: YES — `tests/lifecycle_stage4/test_coordinator_readiness.py:21`.
- Exact replacement: `SYNTHETIC HARNESS TEST ONLY` → `NO PRODUCTION SERVICES`.
- Runtime files changed: NO. Coordinator/Core/authentication/response-commit/blank-UI behavior unchanged.
- Before SHA-256: `{integrity['marker_before']}`.
- After SHA-256: `{integrity['marker_after']}`.
- Reviewed harness remains `{next(x['actual'] for x in integrity['source_checks'] if Path(x['path']).as_posix()=='tests/lifecycle_stage4/fixtures.py')}`.
- See `marker-only.patch`, `before/`, `after/`, and `final-integrity.json`.

## TARGETED TESTS

Executed **25**, passed **25**, failed **0**, errored **0**, skipped **0**, not run **0**. The previously stopped run (23 executed / 22 passed / 1 error / 2 not run) remains unchanged and separately archived. Expected injected negative outcomes in the new test observations are not unexpected test failures.

Exact command: `.\\.venv\\Scripts\\python.exe -B docs\\deployment-completion-20260916\\{D.name}\\run_gate.py targeted`.
Commands, outputs, and actual coordinator identities are in `targeted-command.json`, its hash-pinned log and `targeted-results.json`.

## RESTART / LIFECYCLE

**PASS — 636 recorded checks, zero failures.** Coordinator readiness, peer identity, authenticated attachment, restart authorization, shutdown and cleanup passed. This was an actual isolated Core/process campaign, including repeated startup contenders, stop/restart, crash/adoption, epochs and stale-authority checks.

Exact underlying command: `.\\.venv\\Scripts\\python.exe -B tests\\lifecycle_stage4\\fixtures.py --restart-campaign`, invoked through `run_gate.py restart`.
Evidence: `restart-command.json`, its log, `raw-evidence/restart-campaign-9af593dca2a44fa4af3238520459d011.json`, and `restart-reconciliation.json`.
The post-gate identity check found no surviving matching identity among **95** recorded PID/creation/executable identities before advancing to full acceptance. No additional termination was performed by the reconciliation.

## FULL STAGE 4 ACCEPTANCE

**33 command groups planned; 14 executed; 13 passed; 1 failed; 19 not run after the failure.**
The executed unit/regression suites reported **474 tests, 472 passed and 2 existing skips**. These totals exclude the separately reported targeted tests, native cases, response-commit assertions and restart checks; unlike counting units are not combined.

| Group | Result | Unit-count detail |
|---|---|---|
{rows}

Approvals, uploads and physical media remain **three DEFERRED capabilities**, not passed tests. Their deferral did not excuse the native failure. Actual candidate Electron acceptance, later integration/restart groups and final standalone syntax validation were not run after the required stop. Earlier evidence is preserved but does not substitute for this incomplete campaign.

### Exact blocker

Command: `.\\.venv\\Scripts\\python.exe -B tests\\lifecycle_stage4\\fixtures.py --native-probe`.
Log: `native-2f1094e39f5941d38e8fe09cfc2d8982.log`.
Structured evidence: `raw-evidence/native-native-probe-66e3b69575ac4f02bc8127e0dad2ab4c.json`.

The `correct` case returned `passed=false`, `error=PIPE_CONNECT:2`, child exit code 0, zero received frames and server exception class `Rejected`. The remaining 14 cases passed. The group exited 1 at `fixtures.py:200` with `AssertionError: Native checks failed; see retained evidence`.

`fixtures.py:199` prints `native checks 15 PASS` unconditionally before checking its results. That console line is misleading and is NOT accepted as evidence of success. The JSON results and nonzero exit establish the failure. No source was changed to address this reporting problem.

The exact connection failure mechanism remains **UNCONFIRMED**. The saved evidence does not include the underlying server exception reason, native-operation timeline or individual native child creation identities. No retry, new reproduction, security relaxation, timeout adjustment or runtime correction was attempted. This failure is not attributed to the marker change or to the historical Stage 1 incidents without evidence. The native fixture uses an isolated pipe, Electron-as-Node clients and disposable idle-process identity targets; it does not launch another JARVIS App/Core.

## Previous failure regressions

- Cancellation/response commit: **PASS**, 306 trials and 4,748 assertions, zero failures/live workers. Direct read-only inspection of the same isolated SQLite database returned integrity `ok` and no answer/provenance/orphan-link issues. Both reviewed legal orderings remain represented in the test evidence; no claim is made that uncontrolled scheduling produced a particular mix. See `response-persistence-inspection.json` and raw race results.
- Event polling: **43 checks PASS**.
- Restart/lifecycle: **636 checks PASS** in the prerequisite gate.
- Cleanup: no matching recorded TEST identities remained in the final observation. Of 133 identities, 131 were absent. Two access-denied PID queries were retained, then read-only CIM creation-time checks proved those PIDs now belong to later `svchost.exe` instances. They were not touched. No native-probe command or runner remained in the current snapshot. Native child identity records were not persisted by this probe, so the cleanup statement is limited to its recorded child completion/wait behavior and the supplemental current snapshot.

## Integrity, preservation and limitations

- All **101** preflight source-hash entries remained unchanged after the marker preflight; the only turn edit is the exact marker diff recorded above.
- Candidate package: `{integrity['candidate']}`.
- Package manifest SHA-256: `{integrity['candidate_manifest_sha256']}`; all **796 payload hashes match**. No rebuild, installation or package modification.
- Source HEAD: `{integrity['head']}`; HEAD tree: `{integrity['tree']}`. The pre-existing working tree is not represented as a clean accepted baseline. Index remains empty.
- The previous marker-error archive and its receipt still match: **17 files**, no overwrite. Original blank-UI/readiness/native and historical failure records remain preserved.
- Historical Stage 1 PermissionError root cause remains UNCONFIRMED. The separately demonstrated response-publication and guarded IPC findings are not retroactively used to establish that historical cause.
- Restricted-context Electron GPU failure remains a disclosed environment limitation; exact missing/inaccessible DLL remains unconfirmed. No GPU flags, runtime changes, driver changes or Windows security changes.
- Existing Stage 1/2 cross-session coverage skips remain skips. No new cross-session proof is claimed.
- Production data was not opened for this collection, copied, moved or intentionally hashed while live. No production Core/configuration/authentication operation or paid provider call was performed. Production-preservation claims refer to this bounded TEST campaign and unchanged monitored source/package hashes, not a claim that the user's independently running production database is static.

## Rollback / review

No runtime rollback was applied. To reverse only this turn's marker change, review `marker-only.patch` or restore this single test file from `before/test_coordinator_readiness.py` after checking its current hash. This intentionally restores the incorrect marker and its isolation rejection; it is not an operational fix. The reviewed prior harness correction and the blank-UI candidate must not be reverted as a side effect. All TEST evidence stays preserved. No production restoration or process termination is required by this report.

Next review item: authorize narrowly scoped diagnosis of the native expected-success connection failure, using the retained report and exact frozen source. Do not change authentication, native bridge behavior or deadlines speculatively. Full acceptance remains blocked until that required case and the remaining campaign pass.

The archive uses an explicit nonsecret allowlist from this evidence directory, rather than the broad database-sync workflow, to exclude unrelated source, live TEST runtime files, credentials, private configs, databases and heavy packages. See `SHA256.json` and `archive-verification.json` for exact copy hashes and destination.

## Final disposition

- Acceptance commit created: **NO**; commit/hash: **none**.
- Production touched: **NO**; activated: **NO**.
- Stage 4: **INCOMPLETE** — native expected-success failure; full campaign stopped.
- Stage 5: **NOT STARTED**.

**STOP FOR REVIEW.**
'''
assert not (D/'REPORT.md').exists();(D/'REPORT.md').write_text(report,encoding='utf8')
print(json.dumps({'report':str(D/'REPORT.md'),'stage4':'INCOMPLETE','native_failed':1,'cleanup_identity_exclusions':len(resolved),'acceptance_commit':False}))
