import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parent;plan=json.loads((R/'workspace-plan.json').read_text());CODE=pathlib.Path(plan['live_code'])
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
x=read(R/'campaign-summary.json');runs=x['runs'];focused=x['focused'];failed=next(v for v in runs if v['status']=='FAIL');failroot=CODE/failed['run'];probe=read(failroot/'probe-timeout-reconciliation.json')['timedOut'][0]
qdir=next(CODE.glob('queue-tests-*'));q=read(qdir/'result.json')
old=R.parent/'stage6-eventdrain-resume-20260920';manifest=read(old/'archive-manifest.json');changed=[]
for row in manifest['files']:
 p=old/row['path']
 if not p.resolve().is_relative_to(old.resolve()):raise RuntimeError('Old archive path escape')
 if sha(p)!=row['sha256'] or p.stat().st_size!=row['size']:changed.append(row['path'])
receipt=read(old/'archive-verification.json')
if sha(old/'evidence.zip')!=receipt['zip_sha256']:changed.append('evidence.zip')
save(R/'previous-diagnostic-preservation.json',dict(files=len(manifest['files']),zipSha256=sha(old/'evidence.zip'),changed=changed,status='PASS' if not changed else 'FAIL'))
if changed:raise RuntimeError('Old evidence changed')
inventory=read(R/'live-path-inventory.json');inventory.append(dict(files='baseline-manifest-hash.json;acceptance-failure.json;acceptance.json;probe-timeout-reconciliation.json;probe-window.json',new_path=str(CODE/'<unique-run>'),new_volume='D',reader='offline acceptance/report tooling',writer='dry worker/acceptance verifier/post-failure reconciler',frequency='dry hashing or after collection freeze',synchronous_operations='hash/write/fsync',critical_path='baseline hash active; other evidence after monitor exit'))
save(R/'live-path-inventory-final.json',inventory)
modified=[p.name for p in (R/'before').iterdir() if sha(p)!=sha(R/'candidate'/p.name)]
added=[p.name for p in (R/'candidate').iterdir() if not (R/'before'/p.name).exists()]
def table(headers,rows):return '| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+''.join('| '+' | '.join(str(x) for x in row)+' |\n' for row in rows)
workloads=table(['Workload','Result','Expected / callback / enqueued / persisted START','Expected / callback / enqueued / persisted STOP','Heartbeat interval / age s','Longest drain s','Longest live D call'],[[v['mode'],v['status'],f"{v['expectedPairs']} / {v['startCallback']} / {v['startEnqueued']} / {v['starts']}",f"{v['expectedPairs']} / {v['stopCallback']} / {v['stopEnqueued']} / {v['stops']}",f"{v['heartbeatInterval']:.6f} / {v['heartbeatAge']:.6f}",f"{v['maxDrain']:.6f}",f"{v['longestLiveFileCall']['stage']} {v['longestLiveFileCall']['seconds']:.6f}s"] for v in sorted(runs,key=lambda v:{'idle':0,'disk':1,'sustained':2}[v['mode']])]+[['CPU-only','NOT RUN','—','—','—','—','—'],['D hashing','NOT RUN','—','—','—','—','—']])
failuremap=[['D workspace inaccessible','PASS, simulated EACCES plus actual restricted-context preparation denial','test_livepaths.test_workspace_access_denied; preparation-failure.json'],['Heartbeat write failure / simulated disk full','PASS, injected append ENOSPC/short write','test_journal.test_disk_full/test_short_write'],['Event write failure','PASS, actual invalid write target; entry retained and failure latched','queue regression failed_write_zero_removed_and_retry_refusal'],['Queue consumer failure','PASS, identity-verified disposable process termination','test_failure_campaigns.test_queue_consumer_death_is_explicit_campaign_failure'],['Monitor/publisher failure','PASS, retained-child termination and rejected liveness','test_processes.test_killed_publisher_immediate_failure; finalization crash tests'],['Durable finalization failure','PASS, fsync exception and interrupted finalizer','test_finalization.test_final_flush_failure/test_finalizer_process_crash'],['Archive copy failure','PASS, injected PermissionError','test_livepaths.test_archive_copy_denied_fails_closed'],['Evidence hash failure','PASS, intentionally corrupted copied evidence/tampering','test_finalization.test_copy_hash_failure/test_tamper_after_finalization'],['Process probe failure','PASS rejection test; REAL recurring timeout blocks campaign','test_livepaths.test_probe_nonzero_rejected; failed run evidence'],['EventIdentifier collisions','PASS, 222 assertions / 10,000 concurrent entries','queue result.json'],['Duplicate PID','PASS rejection','test_event_rejection.test_duplicate_pid_is_rejected'],['Identity ambiguity','PASS rejection','test_queue_finalization.test_identity_ambiguity_blocks_acceptance; test_livepaths.test_ambiguity_is_rejected']]
report=f'''# Stage 6 D: monitoring workspace correction — stopped acceptance

FINAL STATUS: MONITOR_STILL_DEFECTIVE

The infrastructure path correction is implemented in a new isolated candidate. Idle and C sustained-read runs passed. C sustained hashing failed on the unchanged five-second process-probe timeout, despite healthy heartbeat publication. The campaign stopped immediately; no retry, timeout increase, later stress workload, reproduction batch, full final campaign or dry run followed.

This status describes incomplete monitor acceptance. It does not mean the D event-drain path reproduced its old >10-second stall, nor that production JARVIS is defective.

## 1–6. Changes, hashes and live path boundary

All source changes are confined to new `docs/stage6-dlive-20260920` infrastructure plus `docs/prepare_stage6_dlive.py` and the copied D workspace. Existing monitors, collision-correction source, historical failures and production source remain unchanged.

Modified copies: {', '.join('`'+n+'`' for n in modified)}.

New candidate modules: {', '.join('`'+n+'`' for n in added)}.

The queue consumer crash fixture needs both the existing timing helper and queue source when copied; this is build wiring, not changed queue semantics. `finalize.py` adds D containment only. `collect.py` resolves one D root and records the existing successful live-collection status consumed by the existing finalizer; it does not grant acceptance. The verifier still separately checks health, process/event counts and durable receipts. No five-second or ten-second limit changed. The exact queue reference/removal implementation is byte-identical to its pre-change diagnostic source.

`pre-change-hashes.json` records 25 original source hashes, sizes and modification times; `before/` preserves those bytes. `final-source.diff` records the copied-file changes. `final-source-hashes.json` records final candidate hashes and D-copy equality. `candidate-hashes.json` preserves first-deployment hashes; `code/prelive-launch-refinement.json` records the later pre-live launcher refinement (D working directory and executable hashing before monitor start). Per-run source-hash comparisons found zero drift. No source was edited after the first live run began.

Previous critical C paths: heartbeat journal, event evidence, Test-Path/Get-Item checks, readiness/configuration, probe/phase records, stop/completion flags, collector and monitor error/status records, resource output, console output, active temporary files, queue/timing output and live dry-run manifest/hash files.

New bounded live code/workspace: `{CODE}`. Each run is a uniquely generated `<label>-<GUID>` child, created without overwrite. Live data, controls and temporary files use that D child. Script/probe executable copies and focused synthetic fixtures also reside on D. TEMP/TMP are set only for these processes; no permanent environment change occurs. Paths reject C/other roots, traversal, alternate-stream names and reparse escapes. Existing run IDs cannot be reused. `workspace.py`/`workspace.ps1` enforce the root before collection; no C evidence fallback remains in the implemented path.

`live-path-inventory.json` is the initial inventory; `live-path-inventory-final.json` adds new acceptance/dry/report artifacts. Each entry records old/new path and volume, reader/writer, frequency, synchronous operation and critical-path role. Actual run trees were checked for reparse/containment violations. `timing-state.json` records the D journal path; run configs require D journal/event/control volumes. Fixed source paths in `workload.py` are read-only sacrificial inputs, not live state.

Unavoidable external C dependencies: installed Python/PowerShell/.NET/Windows binaries and modules, OS-managed pagefile/logging/prefetch/security activity, and the deliberately stressed sacrificial C source. These can still affect process launch, paging or scheduling and are not proven latency-free. They do not store acceptance authority/heartbeat state. No DLL/runtime move, OS logging change or security setting change was attempted. Source/path evidence is not a system-wide kernel file-I/O trace.

The first restricted-context D root creation failed with WinError 5 before any monitor/workload started. It is preserved in `preparation-failure.json`; authorized host-context creation then succeeded without changing ACLs. This preparation failure is not a live acceptance pass or a Windows security correction.

## 7–9. Focused and collision regressions

Focused tests: {focused['executed']} executed, {focused['passed']} passed, {focused['failures']} failures, {focused['errors']} errors, {focused['skipped']} skipped. Twelve new containment/failure checks are included. Original heartbeat, stale identity, process lifecycle, retained handles, malformed/partial input, finalization and queue rejection regressions were rerun from D. `code/focused-result.txt` contains exact test names; `focused-result.json` records totals/elapsed time.

Queue regression: {q['results']['checks']} assertions PASS, real PSEventArgsCollection identity proof, 10,000-event concurrent stress, 9,993 external identifier collisions, zero internal collisions/losses/duplicates/sibling deletion. Evidence: `code/{qdir.name}/result.json`. Fifty retained-probe identity checks passed within the focused suite. Powershell syntax checks passed before execution, and the pre-live launcher refinement was separately parsed.

## 10–18. Workloads, repetitions, heartbeat, events and collisions

{workloads}

The dedicated three independent C-hashing reproduction runs: NOT RUN. The first D7 C-hashing stress case failed, activating the required D9 stop. It is not relabeled as a passing reproduction. The separate D11 five-workload final acceptance campaign: NOT RUN. D7 stress is incomplete (two PASS, one FAIL, two NOT RUN).

Across the three executed real runs: **253 expected/callback/enqueued/persisted STARTs and 253 confirmed/callback/enqueued/persisted STOPs**, five external EventIdentifier collisions, zero internal queue-ID collisions, no queue residue or lost/duplicate events. Overall maximum heartbeat interval 1.0634171 seconds; maximum successfully sampled age 1.0584257 seconds. Longest measured D file operation was journal Flush(false), 0.720630 seconds, in the hashing case. Longest event append in that case was 0.0005639 seconds; longest drain 0.0221988 seconds. Timing includes startup/live calls conservatively. No evidence-write error was recorded in these real runs. Per-case locks, queue depth, event writes and heartbeat operations are in `campaign-summary.json`.

### Exact recurring probe failure

Run: `{failed['run']}`. `collect.py:41` raised `subprocess.TimeoutExpired` from `p.wait(timeout=5)` for `{CODE / 'J6Probe.exe'}`. The executable was on D and its source hash was captured before launch. Timed-out PID **{probe['pid']}**, creation FILETIME **{probe['times'][0]}**, kernel exit FILETIME **{probe['times'][1]}**, kernel lifetime **{probe['kernelLifetimeSeconds']:.7f} seconds**. The cached return code is unavailable (null); it is not invented.

The normal successful-probe list contains 130 records; it excludes the failed wait because its append occurs afterward. Retained-handle evidence contains 131 unique processes with kernel exits and exactly one START and STOP each. `probe-timeout-reconciliation.json` preserves that distinction and never changes the failed run to PASS. Six heartbeat records fall within the kernel lifetime window, maximum adjacent interval 1.0280246 seconds (`probe-window.json`). The monitor remained responsive through this failure. Workload, monitor and resource sampler exited zero; no forced cleanup was used.

Classification: **PROBE_COMPLETION_TIMEOUT — ROOT CAUSE UNCONFIRMED**. This demonstrates recurrence without the earlier multi-second event-drain/heartbeat blockage. It does not prove complete independence from all storage/Windows behavior: C system dependencies and other mechanisms could still affect process lifetime. No loader, security-hook, scheduler or native wait cause is established. Do not increase the probe timeout or claim a flake.

## 19. Failure injection

{table(['Failure','Actual result / limitation','Evidence'],failuremap)}

These are the existing focused synthetic/process-injection paths plus the new containment checks, not claims that an actual D disk was filled or ACLs changed. Event persistence failure uses a real failing file target in the queue fixture; inaccessible workspace/ENOSPC/fsync/copy exceptions are deliberately simulated where stated. Full acceptance cannot be granted from these unit/fixture results after a real workload fails. No additional live failure-injection campaign was begun after the stop.

## 20–23. Dry runs, durability and archive

Dry Run #1: NOT RUN. Dry Run #2: NOT RUN. Protected hashing: NOT RUN / UNAUTHORIZED.

Idle and sustained-read runs froze collection, reconciled queues, completed Flush(true), exited, then fsynced their evidence and verified D-local manifest/archive receipts. Their `EVIDENCE-DURABLY-FINALIZED.json` and `acceptance.json` are preserved. The failed hashing monitor also closed with its final journal flush and all exits confirmed, but its acceptance finalizer correctly refused a receipt. That failure will be archived as failed evidence, never as an accepted baseline.

Final report/evidence archival occurs only now, after all live monitors/processes exited and acceptance is frozen as failed. The archive destination is `{plan['archive']}`. `archive-manifest.json` lists source/report and D-workspace artifacts with SHA-256/size; `archive-verification.json`, created after copying and independently hashing all ZIP members, supplies actual archive verification/counts/hashes. It is outside the sealed ZIP to avoid self-reference. An archive receipt proves preservation only, not monitor acceptance. Any final archival error remains a blocker.

## 24–29. Uncertainty, preservation, eligibility and disposition

Supported historical statement: “Synchronous filesystem operations on C: were repeatedly demonstrated to block the live Stage 6 monitoring path for multiple seconds, including intervals exceeding the 10-second health threshold.”

The underlying Windows/filesystem/driver problem is NOT identified. The original 13.7 / 14.084 / 14.565 second delays are NOT conclusively assigned a common cause. The new probe timeout is preserved separately. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

All 25 pre-change source files retain their original hashes/size/mtime. Prior diagnostic archive content ({len(manifest['files'])} original members) and its ZIP hash remain unchanged. No historical evidence was overwritten. `identity-reconciliation.json` performed 258 PID+creation-time queries for current campaign monitors/workloads/probes with zero unresolved/live matching identities and no source drift. Retained kernel exits and resource Popen completion independently confirm cleanup. Final host snapshot: no workspace processes, no J6Probe, no VirtualBox processes; VBoxSDS stopped. Tests that intentionally killed sacrificial fixtures retained their existing bounded cleanup.

Protected VM/configuration access: NONE. Production JARVIS changes: NONE. VirtualBox launch: NONE. Windows security changes: NONE. Runtime/application source changes: NONE. Acceptance commit: NONE.

Protected-baseline eligibility: **NOT JUSTIFIED**.

Final status: **MONITOR_STILL_DEFECTIVE**.

Next owner review: authorize a narrowly bounded probe lifetime/startup/exit diagnosis using this preserved run and targeted disposable probes if needed. The measured monitoring path improvement is preserved; no redesign or timeout change is proposed on current evidence. The requested full acceptance, three C repetitions and both dry runs must still pass later before any protected-baseline procedure is eligible. No protected-baseline capture command is issued as approved because MONITOR_VALIDATED was not reached.

Rollback: stop using this new D candidate and retain the prior immutable infrastructure/evidence. No production or protected-state rollback is required. Preserve the D run directories and archived failure; do not delete or overwrite them to reset acceptance.

Commands: installed Python `-B <D code>/run_focused.py`; PowerShell `-NoProfile -File <D code>/test_queue.ps1`; fresh UAC monitor launches through `launch.ps1 -Mode idle -Duration 30 -Label stress-idle`, `-Mode disk -Duration 100 -Label stress-reads`, and `-Mode sustained -Duration 150 -Label stress-hash`. Exact configurations, hashes, timing, call stacks and retained identities are in each run directory. No further workload was executed after the hash failure.
'''
with (R/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
print(json.dumps(dict(status='MONITOR_STILL_DEFECTIVE',modifiedCopies=modified,newFiles=added,oldEvidenceMembersPreserved=len(manifest['files']))))
