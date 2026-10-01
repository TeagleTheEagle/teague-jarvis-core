from pathlib import Path
import json,hashlib,datetime
R=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(n,v):
 with (R/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
code=Path(read(R/'plan.json')['live_code']);runs=read(R/'workload-summary.json');lat=read(R/'latency-summary.json')
failed=next(x for x in runs if x['mode']=='disk');d=code/failed['run'];p=next(x for x in read(d/'probe-timings.json') if x['timedOut']);freq=p['frequency'];origin=p['launchRequestedQpc']
timeline={key:(p[key]-origin)/freq for key in ('createProcessCalledQpc','createProcessReturnedQpc','popenReturnedQpc','mainWaitEnteredQpc','timeoutCaughtQpc','immediateHandleCheckQpc','observerReturnedQpc','reconciledQpc')}
detail=dict(pid=p['pid'],created=p['finalKernelTimes'][0],kernelExit=p['finalKernelTimes'][1],kernelLifetime=(int(p['finalKernelTimes'][1])-int(p['finalKernelTimes'][0]))/1e7,createProcessSeconds=(p['createProcessReturnedQpc']-p['createProcessCalledQpc'])/freq,waitSeconds=(p['timeoutCaughtQpc']-p['mainWaitEnteredQpc'])/freq,immediateHandleState=p['immediateHandleState'],actualExitCode=p['actualExitCode'],finalHandleState=p['finalHandleState'],timelineSecondsFromLaunch=timeline,cause='UNCONFIRMED',missing=['first instruction','work begin/end','exit initiation','exact handle signal instant'])
save('timeout-timeline.json',detail)
gate=next(code.glob('finalization-tests-*/result.json'));g=read(gate);queue=read(next(code.glob('queue-tests-*/result.json')))
changed=['accept_run.py','collect.py','launch.ps1','monitor.ps1','FinalizationGate.cs','finalization_tests.cs','test_finalization_gate.ps1']
fresh=read(R/'fresh-latencies.json');idle=next(x for x in runs if x['mode']=='idle')
state=read(R/'identity-reconciliation.json');host=read(R/'final-host-state.json')
if state['unresolved'] or state['sourceDrift'] or any(host[k] for k in ('virtualbox','probes','workspaceProcesses')):raise RuntimeError('Cleanup/source uncertainty')
syntax=[]
import ast
for f in sorted((R/'candidate').glob('*.py')):ast.parse(f.read_text(encoding='utf-8-sig'));syntax.append(str(f))
save('python-syntax.json',dict(status='PASS',files=syntax,method='ast.parse; no bytecode'))
save('disposition.json',dict(status='MONITOR_STILL_DEFECTIVE',acceptance=False,reason='Unchanged five-second probe timeout reproduced under C: reads; five-workload campaign incomplete, dry runs ineligible.',protectedAccess=False,productionChanged=False,baselineEligible=False))
save('test-summary.json',dict(existing=read(code/'focused-result.json'),newGate=g,queue=queue,syntax=len(syntax),runs=[{k:x[k] for k in ('run','mode','status','probes','confirmedExits','starts','stops','timeouts','heartbeatMax','finalization')} for x in runs],notRun=['C hashing','CPU-only','D hashing','Dry Run 1','Dry Run 2'],changed=changed))
table='\n'.join(f"| {x['mode']} | {x['status']} | {x['probes']} | {x['starts']} | {x['confirmedExits']} | {x['stops']} | {x['heartbeatMax']:.6f} | {x['timeouts']} |" for x in runs)
measured='\n'.join(f"| {m} | {v['callback']['n']} | {v['callback']['median']:.6f} | {v['callback']['p95']:.6f} | {str(v['callback']['p99'])} | {v['callback']['max']:.6f} |" for m,v in lat['groups'].items())
report=f'''# Stage 6 bounded finalization correction — 2026-09-20

**MONITOR_STILL_DEFECTIVE.** The candidate passes focused validation and the actual idle/clustered-probe run. Full acceptance stops at a separate unchanged five-second process-probe timeout during C: reads. No timeout was raised, no failed run converted to PASS, and no protected-baseline hashing was performed.

## Required 28-item disposition

1. **Previous sequence:** `collect.py` stopped its workload and published completion before final retained-handle proof. `monitor.ps1` broke its loop, slept two seconds, drained, enumerated processes, reconciled, flushed and wrote its result while event subscriptions were still active. Only `finally` unsubscribed. Archive finalization was later in `finalize.py`. Exact audit: `AUDIT-DESIGN.md` and `audit-source-hashes.json`.
2. **Race:** a real STOP could enqueue after that drain and before unsubscribe. The preserved earlier STOP was about 11 ms late; reconciliation correctly rejected it. This is a new demonstrated race, not a diagnosis of historical missing events.
3. **New state machine:** RUNNING → PRODUCERS_CLOSED → WAITING_FOR_PROCESS_EXITS → EVENT_QUIESCENCE → FINAL_DRAIN → SUBSCRIPTION_CLOSED → DURABLE_FINALIZATION → RECONCILIATION → SEALED. Collector closes admission, retains handles and atomically publishes nonce-bound exit proof. The separate gate hooks actual queue delivery, tracks active persistence and exact START/STOP counts, resets quiet time on each event, and requires complete expected identities before closing. The unchanged ExactEventQueue still persists/removes exact references. After unsubscribe, final drain/reconciliation and durable heartbeat/event flush are mandatory. Post-boundary callbacks latch failure. External acceptance requires zero monitor exit, SEALED state and verified archive receipt.
4. **Delivery measurement:** 854 preserved sacrificial measurements across five workloads; 367 STOP callbacks exceeded the previous two-second grace. These are earlier measured runs, not fresh execution in this pass. Fresh completed/failed-run samples are separately in `fresh-latencies.json`.

| Workload | Samples | Callback median s | p95 s | p99 s (None = insufficient) | Max s |
|---|---:|---:|---:|---|---:|
{measured}

5. **Quiet bound:** 4.6 seconds. Fixed closure deadline 45 seconds inside the existing 60-second collector finalization wait. Probe wait remains five seconds; heartbeat threshold remains ten seconds.
6. **Justification:** maximum callback/enqueue latency 3.0071871 s + 50% margin 1.50359355 s, rounded upward to 0.1 s. This empirical margin is not a universal Windows notification guarantee. Missing records independently block closure even after quiet time; expiration fails closed. No retries reset the deadline.
7. **Late injections:** PASS: immediately before/during drain, +1/+10/+25/+100 ms, 4.599 s and 4.600 s, and closing-boundary events. The actual gate + exact queue were exercised with a virtual clock. Missing STOP prevents premature close; arrival persists and resets quiet. An event after closure is preserved by the test and invalidates sealing.
8. **Concurrent stress:** PASS: 1,000 synthetic process identities / 2,000 real queue events from four concurrent threads, zero loss/duplicates/internal collisions. Actual idle run additionally began with eight simultaneously launched harmless probes; all exited and reconciled. This does not claim 1,000 actual Windows processes were launched.
9. **Focused regressions:** existing 69/69 tests; new gate {g['checks']} assertions / {len(g['groups'])} groups; unchanged queue 222 assertions including 10,000-event concurrent collision stress; Python syntax {len(syntax)} files PASS; PowerShell parser checks PASS. New stress assertion count includes repeated no-premature-seal checks and is schedule-dependent. Source revision v1 focused tests preceded only the optional clustered first-batch fixture change; v2 actual idle validates that fixture. Gate/queue source remained identical between those tests and actual runs.
10. **Five workloads:** incomplete. Current results:

| Workload | Result | Launched probes | START persisted | Confirmed exits | STOP persisted | Max heartbeat s | Probe timeouts |
|---|---|---:|---:|---:|---:|---:|---:|
{table}
| C hashing | NOT RUN | — | — | — | — | — | — |
| CPU-only | NOT RUN | — | — | — | — | — | — |
| D hashing | NOT RUN | — | — | — | — | — | — |

11. **Late events:** idle gate observed {idle['finalization']['lateEventsAfterQuietStart']} event after quiet observation began. The gate counter is event-type agnostic; it must not be relabelled as a STOP-only counter. Raw tap/pipeline records retain event kinds. The failed read run closed without the timed-out probe's canonical STOP; that run is rejected and cannot prove complete lifecycle coverage.
12. **Quiet resets:** idle {idle['finalization']['quiescenceResets']}; failed C-read run 0 (successful-exit acceptance proof was intentionally not admitted after collector failure).
13. **START totals:** 150 persisted = 94 idle + 56 C-read. No invented event records.
14. **STOP totals:** 149 persisted = 94 idle + 55 C-read. All 150 retained probe handles independently confirm exit; handle evidence is not a replacement for the missing STOP.
15. **Heartbeat maxima:** idle 1.1956944 s; C reads 1.0509084 s. Timing was healthy despite the rejected read campaign. Composite analyzer correctly reports FAIL because collector/coverage failed.
16. **Probe timeout:** PID {p['pid']}, creation FILETIME {p['finalKernelTimes'][0]}, kernel lifetime {detail['kernelLifetime']:.7f} s. CreateProcess call {detail['createProcessSeconds']:.7f} s; wait observed {detail['waitSeconds']:.7f} s. Immediate retained-handle status WAIT_TIMEOUT (258), eventual exit 0 / signaled handle. Cause UNCONFIRMED. Exact trace: `timeout-timeline.json`, raw `probe-timings.json`, unchanged `collector-failure.json`. Monitor then failed closed with `Incomplete or failed producer/handle closure`, exit 1.
17. **Failure injection:** PASS in focused tests: delayed/closed-boundary event, subscriber/heartbeat failure, active/failed consumer, evidence write failure, durable flush refusal/failure, non-exited handle, missing STOP deadline, duplicate/ambiguous identity, mismatch, archive/hash failure. The legacy suite includes real sacrificed consumer termination and actual fsync/archive checks. Virtual-clock state tests are not represented as actual OS-provider death tests.
18. **Dry Run #1:** NOT RUN; all five workloads did not pass.
19. **Dry Run #2:** NOT RUN; prerequisite #1 unavailable.
20. **Durable finalization:** actual idle PASS (SEALED and verified per-run durable receipt/archive). C-read FAIL/NOT SEALED; failed evidence remains preserved separately. Diagnostic-report archive preservation is not monitor acceptance.
21. **Archive verification:** final status/path/member and SHA-256 results are in `archive-verification.json`, generated after this report. Only finalized nonsecret diagnostic evidence is archived. No live monitoring uses OneDrive/C: archive storage.
22. **Residual uncertainty:** five-workload acceptance and both full dry runs remain unproved. Finite quiet is an empirical bound; complete tracked identity counts remain essential. Unobserved future callbacks after monitoring ends are outside claimed coverage. Cross-user/provider-wide guarantees are not established. Timeout remains unexplained.
23. **Native-control delay:** earlier 3.312-second mostly pre-entry delay remains separate, with Windows/runtime cause UNCONFIRMED. Native helpers were not substituted for whoami acceptance probes.
24. **Historical causation:** this correction does not establish causes of historical missing events, earlier C: stalls, or Windows process delays. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
25. **Protected access:** NONE. No protected VM/config files inspected, opened or hashed. VirtualBox process checks only; final zero VirtualBox processes, VBoxSDS Stopped.
26. **Production:** unchanged; only seven files in the new diagnostic candidate differ/new. All 34 predecessor source files unchanged; all 37 candidate files hash-reconciled. No accepted JARVIS runtime source was edited.
27. **Protected-baseline eligibility:** NOT ELIGIBLE / NOT AUTHORIZED. Do not run protected baseline capture, VM operations or guest validation.
28. **Final status:** MONITOR_STILL_DEFECTIVE. The finalization candidate is partially validated; the five-second probe timeout is the current blocker. No complete acceptance claim.

## Exact changed infrastructure

Candidate: `{R/'candidate'}`

Live frozen copy: `{code}`

Changed existing: `monitor.ps1`, `collect.py`, `accept_run.py`, `launch.ps1`.

Added: `FinalizationGate.cs`, `finalization_tests.cs`, `test_finalization_gate.ps1`.

Before/after: `source-before.json`, `candidate-hashes-v1.json`, `candidate-hashes-v2.json`, `final-source-hashes.json`, `source.diff`. The unchanged queue, journal and probe-timing modules preserve collision/identity/timeout behavior.

## Synchronization and rollback

Gate callbacks hold only their own short memory lock. Queue locks are never held across filesystem persistence or subscription removal. The gate does not call queue methods while holding its lock; monitor takes queue snapshots before gate calls. Closing latches any later event as a failure, so a check/close race cannot silently seal extra events. Exact per-identity completeness is an additional independent barrier.

Control completion files use same-run D: temporary files followed by atomic rename; no C: fallback. All workload/probe admission ends before producer closure. Resource sampling is an observer that exits on monitor completion, not a probe producer; its retained Popen result is separately recorded as exit 0.

Rollback is abandonment of this new candidate/run directory; original validated/predecessor files were never overwritten. Keep all evidence and return to the preserved predecessor only for diagnosis, not acceptance. No deletion, VM rollback, production change, timeout increase or security change is needed.

## Next review

Review the new timeout record before another acceptance campaign. Do not increase the timeout or replace the acceptance probe without explicit justification/review. No additional workload or dry run was attempted after this failure. Zero matching live diagnostic processes, zero unresolved recorded identities; 155 read-only identity checks in `identity-reconciliation.json`.
'''
with (R/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
print(json.dumps(dict(status='MONITOR_STILL_DEFECTIVE',timeout=detail,report=str(R/'REPORT.md'))))
