"""Summarize frozen evidence after collection; archive receipt is separate."""
import pathlib,json,hashlib,ast
R=pathlib.Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(n,v):
 with (R/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
plan=read(R/'plan.json');C=pathlib.Path(plan['live_code']);runs=read(R/'workload-summary.json');ids=read(R/'identity-reconciliation.json');changes=read(R/'changes.json')
focused=read(C/'focused-result.json');policy=[dict(path=str(p),result=read(p)) for p in C.glob('probe-policy-*/result.json')];queues=[dict(path=str(p),result=read(p)) for p in C.glob('queue-tests-*/result.json')];gates=[dict(path=str(p),result=read(p)) for p in C.glob('finalization-tests-*/result.json')]
syntax=[]
for p in sorted((R/'candidate').glob('*.py')):ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p));syntax.append(str(p))
summary=dict(focused=focused,probePolicy=policy,queue=queues,finalization=gates,pythonAST=dict(passed=len(syntax),files=syntax),powershellSyntax=read(R/'powershell-syntax.json'),failureInjection='Deterministic fault-injection tests plus existing actual subprocess consumer/finalizer crash tests. No intentionally hung real 13.6-second process was launched.')
save('test-summary.json',summary)
expected={'hash1','hash2','hash3','idle','reads','campaign-hash','cpu','dhash','dry1','dry2'}
actual={x['run'].rsplit('-',1)[0] for x in runs}
ok=actual==expected and all(x['status']=='PASS' for x in runs) and not ids['unresolved'] and not ids['sourceDrift'] and focused['passed']==69 and policy[0]['result']['passed']==26
ok=ok and all(x['unchanged'] for x in read(R/'source-preservation.json')) and all(x['unchanged'] for x in read(R/'final-source-hashes.json'))
ok=ok and all(x['unchanged'] for x in read(R/'historical-preservation.json')) and all(x['passed'] for x in summary['powershellSyntax'])
ok=ok and all(x['result']['status']=='PASS' for x in queues+gates)
host=read(R/'final-host-state.json');ok=ok and not any(host[k] for k in ('virtualbox','probes','workspaceProcesses'))
state='MONITOR_VALIDATED' if ok else 'MONITOR_STILL_DEFECTIVE'
save('disposition.json',dict(status=state,archiveVerificationRequired=True,protectedBaselineAuthorized=False,missing=sorted(expected-actual),failedRuns=[x['run'] for x in runs if x['status']!='PASS']))
total=sum(x['probes'] for x in runs);warn=sum(x['slowWarnings'] for x in runs);hard=sum(x['hardFailures'] for x in runs)
mx=max((x['maxProbeLifetime'] or 0 for x in runs),default=0);hb=max((x['heartbeatMax'] or 0 for x in runs),default=0)
tables=['| Run | Probes / START / STOP | >5 s warnings | Max lifetime s | Hard failures | Max heartbeat s | Result |','|---|---:|---:|---:|---:|---:|---|']
for x in runs:tables.append(f"| {x['run']} | {x['probes']} / {x['starts']} / {x['stops']} | {x['slowWarnings']} | {x['maxProbeLifetime']} | {x['hardFailures']} | {x['heartbeatMax']} | {x['status']} |")
files='\n'.join(f"- `{C/x['name']}` — before `{x['beforeSHA256'] or 'NEW'}`; after `{x['afterSHA256']}`" for x in changes)
text=f'''# Revised Stage 6 probe acceptance — sacrificial validation

Decision: **{state}**, with canonical archival success established separately by the required `archive-verification.json` receipt. No protected baseline capture is authorized or performed. This is validation infrastructure acceptance, not Stage 6 completion.

## Blocking result — Dry Run #1

Dry Run #1 FAILED. Probe PID 9240 / creation FILETIME 134343506525182730 generated a slow warning at 5.008060 seconds. At 13.603420 seconds after launch request the retained handle was still nonsignaled (258), so the fixed 13.6-second policy failed closed. Its independent observer returned WAIT_TIMEOUT after 15.014988 seconds (15.017654 seconds since launch). A STOP callback was later recorded at launch +23.643717 seconds. This is callback timing, not a captured kernel exit time. Exact final lifetime and the underlying Windows cause remain UNCONFIRMED.

The monitor's largest recorded heartbeat gap was 9.574968 seconds; collector-observed maximum heartbeat age was 1.067545 seconds. Neither proves continuous sub-second health during finalization. The longest instrumented filesystem call in this failed run was journal.write 0.020536 seconds; uninstrumented delays must not be assigned a cause from that metric.

17 STARTs and 17 STOPs were preserved, but retained-handle closure did not satisfy acceptance. The monitor rejected the failed producer proof and exited 1. Finalization stopped at WAITING_FOR_PROCESS_EXITS; no SEALED/durable receipt, baseline manifest or manifest hash was created. The cancelled hash worker exited 1. Dry Run #2 was NOT RUN, as required. No retry or deadline increase was made.

The original hard-deadline error remains in probe-timings.json; cleanup overwrote the collector failure summary with an observer-timeout exception. The dry worker's cleanup stderr was not persisted. These reporting limitations are disclosed, not repaired in this stopped campaign. Full derived timeline: dry1-failure-timeline.json. Later zero-live-process checks do not retroactively cure failed retained-handle acceptance.

## 1. Exact files changed

Only a new validation candidate was created. Previous candidate/history files were not edited. Full before/after hashes and exact unified diff are in `changes.json`, `source-before.json`, `final-source-hashes.json`, and `source.diff`.

{files}

Report-only additions under `{R}`: plan/manifests, edit_candidate.py, summarize.py, make_report.py, archive.py, report/evidence JSON, source.diff, and PROTECTED-BASELINE-PROPOSAL.md. These are outside production code. No application runtime or Git acceptance commit changed.

## 2–5. Previous and revised rules; implementation

Previously the main probe wait used a locally selected five-second hard diagnostic limit. New runs use a five-second SLOW_PROBE_WARNING and a fixed 13.6-second launch-to-exit bound. The heartbeat remains strictly below ten seconds.

`Probe` records monotonic launch-request time before CreateProcess. `wait_tracked` uses the earlier of that time +13.6 seconds and the enclosing campaign deadline. Retained-handle waits use at most 50 ms slices with repeated publisher/subscriber/queue health and process-creation identity checks. Deadline checks do not reset after warnings, filesystem work, or waits. Delayed confirmation beyond the bound fails conservatively even if later evidence says the process exited earlier. A blocked API cannot be preempted by this Python loop; the separately running monitor and subsequent deadline check must still reject late confirmation.

Warning records include PID, creation time, monotonic timestamp, observed elapsed time, threshold and reason in D:-resident slow-probe-warnings.jsonl and probe-timings.json. Kernel FILETIME-to-QPC mapping is an estimate, not direct instruction/exit-initiation tracing. Exact kernel lifetime, monotonic launch/confirmation and bridge evidence are retained separately.

Warnings grant only ELIGIBLE_PENDING_LIFECYCLE. The unchanged finalization barrier plus validate_lifecycle require unique retained identities, normal exits, exact START/STOP, no residue, successful subscriber closure, durable flush, archive/hash verification. There is no retry or dynamic timeout extension.

## 6–7. Focused tests and regressions

- Revised policy: 26/26 tests PASS (boundary times, health, identity, handle, lifecycle, cleanup, archive/flush failure).
- Existing Python monitor regression suite: {focused['passed']}/{focused['executed']} PASS; errors {focused['errors']}, failures {focused['failures']}, skips {focused['skipped']}.
- Exact EventIdentifier/queue regression: 222 assertions PASS; all 10,000 stress events enqueued, persisted and removed; zero loss/duplicates/internal collisions, 9,993 external-ID collisions handled.
- Late-event finalization gate: see exact assertion count and 21 group results in test-summary.json. Assertion count includes scheduling-dependent polling; group coverage is unchanged.
- Python AST: {len(syntax)} files PASS. PowerShell parse results in powershell-syntax.json. Syntax is not runtime acceptance.

## 8–18. Real-run results, lifecycles, collisions and finalization

'''+ '\n'.join(tables)+f'''

Real probes: {total}; warnings: {warn}; hard-deadline failures: {hard}; maximum fully captured kernel lifetime among analyzed passing runs: {mx:.7f} seconds; maximum heartbeat interval across all runs: {hb:.7f} seconds. The failed probe exceeds the independent 15-second observer bound, but its exact kernel lifetime was not captured; {mx:.7f} is NOT the overall lifetime maximum.
START total: {sum(x['starts'] for x in runs)}. STOP total: {sum(x['stops'] for x in runs)}. External EventIdentifier collisions: {sum(x['externalCollisions'] or 0 for x in runs)}; internal queue-ID collisions: {sum(x['internalCollisions'] or 0 for x in runs)}.
Each accepted run proves expected/callback/enqueued/persisted START and STOP counts in acceptance.json, with raw tap/event records. All run details, maxima, drain/filesystem timings, queue depth and finalization transitions are in workload-summary.json and original per-run evidence.
Final independent PID+creation-time checks: {len(ids['identities'])} records; unresolved/live matching identities: {len(ids['unresolved'])}. Final host scan is in final-host-state.json. PID reuse is distinguished from a matching live process, never used to terminate an unrelated process.
Finalization uses the existing producer-close proof, retained exits, 4.6-second resettable event quiescence, 45-second bounded closure, exact queue drain, subscription close, durable flush and SEALED receipt. A finite empirical quiescence window is not a Windows delivery guarantee; expected lifecycle completeness remains mandatory.

## 19. Failure injection

PASS evidence includes exact/over-13.6 deadline and never-exits via the actual policy with an injected monotonic clock/handle; heartbeat/subscriber/queue/identity/handle failure; missing START/STOP; orphan/nonzero cleanup; warning write failure; monitor/finalizer failure; durable flush denial; archive copy/corruption and post-finalization hash corruption. Existing real subprocess consumer termination and finalizer crash tests remain included. Synthetic failures are expected negative tests, not erased failed campaigns. Do not describe simulated hard-deadline testing as a deliberately hung Windows process experiment.

## 20–23. Dry runs, durability and archive

Dry1 and Dry2 status is in the table. Each dry run must independently hash the same 12 fixed sacrificial `.bin` files twice, compare complete SHA-256/size/mtime inventories, generate baseline-style manifest and its hash, reconcile process lifecycle, seal durable evidence and verify the D: archive. No protected artifacts are substituted.

Eight successful workload/repetition runs reached durable finalization; Dry Run #1 did not. Archiving its failed evidence is preservation, not acceptance of that run. All canonical copying occurs after live monitors exited. Archive target: `{plan['archive']}`. `archive-verification.json` must say HASH_VERIFIED and match the complete ZIP/manifest SHA-256. Archive-copy failure prevents final acceptance regardless of all earlier passes.

## 24–29. Limitations, preservation and final disposition

- Underlying Windows storage/driver and intermittent probe runtime causes remain UNCONFIRMED. The provisional 13.6-second bound is empirical, not a guaranteed Windows property. New slow probe results do not explain historical incidents.
- Historical failures remain unchanged, including the original five-second failures and the prior missing STOP/finalization failures. The new rule applies only to this candidate's new runs. Prior candidate source preservation and historical archive checks are recorded separately.
- Protected VM/configuration: NOT ACCESSED. No protected hashing, topology reads, configuration edits, VM operations or VirtualBox launch were performed. Existing monitoring asserts zero VirtualBox starts, and final host evidence is retained. Production JARVIS: UNCHANGED by this work; no Core/provider operations or application edits.
- Live state remains D:-bounded, with containment/reparse/traversal tests and per-process TEMP/TMP. Installed interpreter/OS binaries still load from C:; C: sacrificial reads/hashes are intentional. No claim that Windows itself performs zero C: I/O.
- Protected-baseline eligibility: NOT ELIGIBLE. Dry Run #1 failed; Dry Run #2 is not run. Capture remains UNAUTHORIZED. PROTECTED-BASELINE-PROPOSAL.md is a conditional, unexecuted draft and is not a recommendation to start capture now.
- Report preparation errors are preserved: historical archive filename lookup corrected to review-evidence.zip; a read-only check before UAC completion found no heartbeat yet; restricted-context final CIM enumeration was denied and its empty output is explicitly unreliable. Successful host-context enumeration and identity rechecks supersede that failed diagnostic output. Existing historical archives hash-match their preserved values.
- HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Final requested status: **{state}**. STOP. Next owner review should address the newly reproduced >13.6-second probe and the cleanup evidence limitations; do not rerun dry tests, extend deadlines or start protected capture without that review.

## Commands and rollback

Exact source paths, executable hash identity and per-run config/source-hashes are preserved. Commands:

```powershell
& 'C:\\Users\\jonny\\Documents\\Codex\\2026-09-07\\cr\\outputs\\jarvis\\.venv\\Scripts\\python.exe' -B '{C / 'run_probe_policy.py'}'
& 'C:\\Users\\jonny\\Documents\\Codex\\2026-09-07\\cr\\outputs\\jarvis\\.venv\\Scripts\\python.exe' -B '{C / 'run_focused.py'}'
```

PowerShell host `{str(pathlib.Path('C:/Users/jonny/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe'))}` ran `-NoProfile -File` with `{C / 'test_queue.ps1'}` and `{C / 'test_finalization_gate.ps1'}`. Each real run used `{C / 'launch.ps1'}` with modes/durations in workload-summary.json; idle used Cluster 8, others default1. The monitor alone requested read-only elevation.

Rollback: do not delete evidence. Retire this unique candidate after confirming no matching retained processes remain. The prior 37-file candidate is still intact and hash-verified; selecting it restores the previous diagnostic tooling, not acceptance under the revised policy. Do not reuse old run directories or relabel their results. No production restoration, security setting change, database migration, or Git reset is required.
'''
with (R/'REPORT.md').open('x',encoding='utf-8') as f:f.write(text)
print(json.dumps(dict(status=state,runs=len(runs),probes=total,warnings=warn,maxLifetime=mx,maxHeartbeat=hb)))
