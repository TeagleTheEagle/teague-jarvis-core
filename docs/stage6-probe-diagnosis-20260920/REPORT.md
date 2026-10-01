# Stage 6 probe timeout diagnosis — 2026-09-20

**STRONG_CAUSAL_EVIDENCE** for C:-load-associated post-creation probe delay. **Internal root cause remains UNCONFIRMED.** Strongest category: **PROBE_RUNTIME_DELAY**, meaning elapsed process lifetime after CreateProcess returns; this does not establish that the delay occurred in whoami's user code rather than loader, security, scheduling or exit activity. Monitor acceptance remains **MONITOR_STILL_DEFECTIVE**. No correction or limit increase was implemented.

## 1. Exact probe implementation and audit (P1/P3/P6)

`D:\JARVIS-STAGE6-LIVE\fb8ef11d2c4d44cca4d352d4a9fdfc93\code\J6Probe.exe` is byte-identical to `C:\Windows\System32\whoami.exe`, SHA-256 `23240ef9f8b0a9a324110b1c2331de31dc1b0e08f5359cb707e51a939af56cd3` (authoritative machine-readable binary/source hashes take precedence; see verification below).

The launcher is `D:\JARVIS-STAGE6-LIVE\fb8ef11d2c4d44cca4d352d4a9fdfc93\code\collect.py` running under Python 3.12.14. Actual parent PIDs, working directory, arguments and flags are recorded per probe in `probe-timings.json`. Arguments are empty; working directory is `D:\JARVIS-STAGE6-LIVE\fb8ef11d2c4d44cca4d352d4a9fdfc93\code`. `subprocess.Popen` delegates to Windows CreateProcess, CREATE_NO_WINDOW, close_fds=True, stdout/stderr=DEVNULL. No pipe buffering or communicate() waits occur for the probe. stdin is inherited. Popen's retained process handle is kept through final reconciliation; Python closes the creation thread handle. The monitor is a separate elevated read-only PowerShell process, not the probe's executable.

This native program performs a user-identity query, not zero work. It has no Python/PowerShell interpreter, profile loading or module imports in the probe. The collector's one-second cadence and 50-ms poll sleep occur outside it. Static imports include token/SID/account and LSA functions, loader/localization/output functions, ExitProcess, Sleep and SleepConditionVariableSRW. Import presence does not prove the no-argument execution path invoked them. The Microsoft binary's source/internal call sequence was not available: internal sleeps, retries, filesystem access, security scanning, subprocess creation and exit teardown cannot be declared absent or responsible. DEVNULL prevents account output from being captured. No account names, secrets or credentials were collected.

Expected behavior is a short successful native invocation; there is no supported maximum whoami lifetime. Observed idle lifetime was about 22 ms. P6's managed-runtime condition does not apply: the current probe is already native. No substitute executable was used; this leaves general Windows-loader delay versus whoami-specific work unresolved. [Microsoft whoami documentation](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/whoami).

## 2. Historical 6.052-second reconstruction (P2)

Original preserved run: `D:\JARVIS-STAGE6-LIVE\ab1566cc23dd43cab43afef00cba5940\code\stress-hash-317f8edced6f46e6935d2328f62d56b9`.

PID 12080: creation FILETIME **134343417221517952** (2026-09-20 01:35:22.1517952 UTC), exit FILETIME **134343417282039583** (01:35:28.2039583 UTC), difference **6.0521631 s**. Kernel/user CPU counters were both zero at their reporting resolution. This is not proof of no execution. Cached Popen returncode was null: a zero exit code was not captured for that historical probe and is not inferred.

T0 launch request and T1 CreateProcess return were not preserved. T2 first instruction, T3/T4 work start/end and T5 exit initiation were not observed. T6 exact kernel handle-signal instant was not recorded; kernel exit FILETIME is available. T7 later retained-handle verification established exit but has no individual observation timestamp. T8 final record-persistence instant was not recorded. The timeout exception record QPC is 1744565336986, not the exact initial wait-return time. START event record UTC is 01:35:24.5980246; STOP record UTC is 01:35:30.6849421. Those are event-pipeline timestamps, not first instruction, exact exit or durable-flush timestamps.

`historical-reconstruction.json` preserves the exact records, callbacks, exception and source artifact hashes. No missing timestamp is filled using a later run. Historical delay-owning internal stage remains **UNKNOWN**.

## 3. Exact timeout mechanism (P7)

`Popen.wait(timeout=5)` is called after CreateProcess/Popen returns and creation identity is read. Windows Python `_wait` passes **5000 ms** to WaitForSingleObject; WAIT_TIMEOUT raises TimeoutExpired. There is no polling loop in this wait. The native relative timeout includes process initialization/work/exit occurring after handle acquisition, but excludes time already spent inside CreateProcess. Monotonic QPC brackets measure the new observations. No wall-clock subtraction controls the timeout.

The new diagnostic observer waits on the same retained handle concurrently and never changes the main wait result. Its 15-second observation bound is evidence/cleanup only, not a probe timeout extension. A main timeout stays FAILED_CLOSED, ends that workload and preserves the exception. A zero-time handle check immediately after the timeout provides independent state. No timed-out probe was force-killed; workload shutdown was cooperative and every monitor/resource process returned 0.

Original code did not check the handle immediately at timeout; it reconciled later. New instrumentation supplies that missing observation without changing the original wait. Traceback formatting and persistence occur after timeout and can themselves read Python source on C:, so exception-record time is not the time the wait returned. These reporting delays cannot explain away the unsignaled handle observed at timeout. [Microsoft WaitForSingleObject](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject).

## 4. Timeout origin (P9)

**LOCALLY_CHOSEN_TEST_LIMIT in inspected history.** Earliest located explicit literal: `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-heartbeat-journal-20260918\dryrun.py:56`. It propagated through later harnesses. No inspected requirement establishes a guaranteed five-second whoami completion bound or explains the original choice. This is not a claim that every historical document was searched. The owner now explicitly requires retaining this limit; it remains a binding acceptance rule. No proposed timeout increase follows from this finding.

## 5. Idle distribution (P4)

116 probes: minimum **0.0210403 s**, median **0.02205175 s**, p95 **0.023309325 s**, p99 **0.023827065 s**, maximum **0.0280011 s**, zero timeouts. Percentiles use linear interpolation; p95 is only reported for n>=20, p99 for n>=100. These finite samples do not establish a worst-case bound.

## 6. Workload comparison (P5)

| Condition / run prefix | Probes | Lifetime min / median / max (s) | Timeouts | Max heartbeat interval / age (s) | Max D file call (s) | START / STOP |
|---|---|---|---|---|---|---|
| idle / baseline | 116 | 0.021040 / 0.022052 / 0.028001 | 0 | 1.053807 / 1.036626 | 0.016021 | 116 / 116 |
| disk / reads | 10 | 0.021457 / 0.023398 / 6.191391 | 1 | 1.075476 / 1.065836 | 0.002713 | 10 / 10 |
| sustained / hash1 | 43 | 0.020954 / 0.022158 / 6.556744 | 1 | 1.041383 / 1.017025 | 0.002256 | 43 / 43 |
| sustained / hash2 | 146 | 0.020619 / 0.021605 / 1.055688 | 0 | 1.079927 / 1.024523 | 0.077728 | 146 / 146 |
| sustained / hash3 | 136 | 0.020956 / 0.022108 / 3.732674 | 0 | 1.082480 / 1.047709 | 0.017352 | 136 / 136 |
| cpu / cpu | 39 | 0.020637 / 0.021333 / 0.033406 | 0 | 1.030979 / 1.018647 | 0.016149 | 39 / 39 |
| Dhash / dhash | 87 | 0.020940 / 0.022426 / 0.029120 | 0 | 1.129394 / 1.058181 | 0.123605 | 87 / 87 |


Order was idle, C reads, C hash #1, CPU, D hash, C hash #2, C hash #3. C sources were existing sacrificial large.bin only; no protected file was used. Read/hash workloads use unbuffered 4-MiB reads; hashing adds SHA-256. CPU-only hashes an in-memory 4-MiB buffer and does not saturate every CPU. C reads and hash #1 stopped at their first timeout, so their samples are truncated and must not be used to estimate an unbiased timeout probability. The comparisons are not randomized and do not control caches or every background Windows activity.

Seven probes exceeded 0.5 seconds; all occurred during C: reads/hashing and overlapped slow C: ReadFile calls. `slow-probe-read-overlap.json` records those intervals on the shared QueryPerformanceCounter clock. C: maximum workload read calls reached 3.78–4.22 seconds; D: maximum was 0.257 s. This supports a C:-activity association but does not prove what call blocked inside any probe or identify a Windows/storage/driver cause.

## 7. Process-start timings

| Run prefix | CreateProcess median / max ms | Main wait median / max ms | Observer latency estimate max ms | Workload elapsed s |
|---|---|---|---|---|
| baseline | 2.396 / 16.870 | 21.064 / 23.165 | 1.904 | idle collection 120 requested |
| reads | 2.513 / 5.258 | 22.386 / 5014.725 | 2.400 | 19.003 |
| hash1 | 2.481 / 4.780 | 21.323 / 5009.698 | 2.253 | 49.583 |
| hash2 | 2.476 / 5.286 | 20.720 / 1054.698 | 2.365 | 151.714 |
| hash3 | 2.426 / 4.652 | 21.171 / 3731.983 | 2.343 | 150.712 |
| cpu | 2.589 / 5.242 | 20.328 / 32.179 | 1.732 | 40.000 |
| dhash | 2.518 / 4.904 | 21.413 / 27.922 | 2.181 | 90.006 |


The two timed-out CreateProcess calls completed in about 2.5 ms. The post-return delay, not the CreateProcess API call duration, explains almost all their elapsed lifetime. First-instruction time remains unobserved; loader startup after CreateProcess return is still possible.

## 8. Runtime timings and timeout reproductions

| Case / PID | CreateProcess ms | Main wait seconds | Handle at timeout | Kernel lifetime s | Observer estimate ms | Exit code |
|---|---|---|---|---|---|---|
| hash1 / 20952 | 2.5093 | 5.0096976 | 258 | 6.5567445 | 1.9961 | 0 |
| reads / 23616 | 2.4920 | 5.0147245 | 258 | 6.1913914 | 2.3998 | 0 |


WAIT_TIMEOUT=258 immediately after the original wait proves both processes were still unsignaled at that point. C reads consumed 0.015625 s kernel and 0.015625 s user CPU; C hash #1 reported zero at its counter resolution. Low CPU does not distinguish blocked I/O, loader waits, scheduling or teardown. Exact monotonic T0/T1/wait/observer sequences and FILETIME bridges are in `timeout-timelines.json` and raw `probe-timings.json`.

## 9. Exit timings

All **577** new probes exited with actual kernel-retrieved exit code **0**. Maximum estimated exit-observer lag was **2.400 ms**; both timeout processes were observed promptly after kernel exit. The estimate uses precise UTC/QPC bridges, includes sampling/clock uncertainty and is not an exact kernel-signal timestamp. The two failures returned from their main wait at 5.0097 and 5.0147 s; those small overruns cannot explain their 6.19–6.56 s kernel lifetimes. Wait implementation defect is not supported by these reproductions. Exit initiation remains unobserved, so an internal exit delay cannot be excluded.

## 10. Reproduction disposition (P8)

Three independent C: hashing attempts were performed. #1 reproduced a 6.5567445-s timeout. #2 did not: maximum 1.0556877 s. #3 did not: maximum 3.7326741 s. C reads independently reproduced 6.1913914 s. This is **two new >5-second reproductions**, not three. All failed runs remain failed. These are diagnostic attempts only, not the suspended three-run acceptance gate or five-workload acceptance campaign.

## 11. Heartbeat status

All seven runs stayed below 10 seconds: maximum interval **1.1293936 s**, maximum age **1.065836 s**. Original analyzer FAIL labels for the two timed-out cases remain unchanged; they combine collector/probe failure with health/coverage disposition. Supplemental timing separates healthy heartbeat publication from failed probe acceptance without changing those outputs.

## 12. Filesystem status

Longest measured live D: call: **0.1236047 s**, File.AppendAllText during D hashing. Longest drain: **0.1255423 s**. No monitor evidence-write failure was recorded; all seven monitor journal durableFlush receipts are true. C: workload reads remain capable of multisecond delays. This pass did not identify the underlying filesystem, filter driver, Defender or storage mechanism.

## 13. START/STOP and cleanup

**577 expected START / 577 persisted; 577 confirmed STOP / 577 persisted**, one of each per recorded unique process identity. **16 external EventIdentifier collisions; zero internal queue-ID collisions.** Retained handles independently confirm all exits. **590** final PID+creation-time checks: no live/unconfirmed recorded identities. No forced cleanup. Final host snapshot: zero VirtualBox, J6Probe or workspace processes; VBoxSDS stopped. No termination by PID alone.

## 14. Strongest supported cause (P10)

**PROBE_RUNTIME_DELAY / STRONG_CAUSAL_EVIDENCE**, bounded to a real post-CreateProcess lifetime delay associated with C: load. The wait did not falsely report timeout for an already-signaled process. This does not isolate probe work from loader, security, scheduling or exit behavior. No claim of a proven OS/storage/driver mechanism, and no claim that all historical stalls have one cause.

## 15. Minimum proposed correction / next review (P11)

**No proven corrective change is justified yet. Do not increase either threshold.** The narrow next diagnostic is to compare this identity-query binary with a reviewed minimal native lifecycle probe that records entry and pre-exit markers in D-backed/shared observation state, keeps the same five-second handle wait and retains complete START/STOP/identity evidence. This would test whether whoami-specific initialization/work is avoidable and bracket loader versus body/exit delay. It is a proposed control experiment, not an accepted replacement or established fix. If both binaries delay, narrowly scoped thread/loader/I/O tracing is needed before choosing a correction. No runtime/JARVIS change is proposed. Replacement of the acceptance probe requires owner review and equivalence evidence.

## 16. Remaining uncertainty and preserved failures

Historical 6.052-s internal cause remains UNCONFIRMED. Internal first instruction/work/exit timestamps are unavailable for both old and new cases. Possible loader, identity lookup, security and scheduler explanations remain hypotheses. We did not capture native blocked-call stacks or all OS I/O. The historical null exit status is not reinterpreted as zero. Preserve both current failed runs, earlier failed archives, the transient invocation-path typo (failed before script execution; `invocation-error.json`) and all non-failing controls. The successful runs do not make the failures flakes.

## 17. D:-workspace integrity/regression status

Live code/run/heartbeat/event/control/status/temp/timing artifacts remain under `D:\JARVIS-STAGE6-LIVE\fb8ef11d2c4d44cca4d352d4a9fdfc93\code`. All seven run trees passed containment/reparse inspection. Fresh negative checks rejected C paths, D sibling paths, traversal and malformed run IDs. 18 frozen diagnostic files match their initial hashes and per-run snapshots: **zero source drift**. Previous 15 source files retain hashes/sizes/modification timestamps. The prior 69/69 relocation suite is historical evidence against unchanged infrastructure, not a newly executed acceptance suite. Installed Python, PowerShell, .NET and Windows binaries/DLLs still reside on C:; D artifact containment does not eliminate those read dependencies or OS-managed C: activity.

## 18. EventIdentifier regression status

Fresh unchanged queue regression: **222 assertions PASS**, including **10,000 generated/enqueued/selected/persisted/removed**, zero residue/loss/duplicates/sibling deletion and zero internal collisions. Synthetic external collisions: 9,993. Separate from the 16 real-run external collisions. Actual PowerShell event-queue reference checks passed. Exact queue source and correction unchanged.

## 19. Protected VM access

**NOT ACCESSED.** No protected VM/configuration enumeration, hash, registration, boot or VirtualBox command. The only C workload target was the named sacrificial large.bin. Monitoring subscribed to process events and final process/service state read-only. No claim of a new protected-source integrity baseline is made because the protected files were deliberately not read.

## 20. Production and changed files

**Production JARVIS unchanged. No application/runtime/security/configuration/provider/database changes; no paid calls.** No execution-policy, ACL, UAC, Defender, firewall or other security setting changed. Existing UAC approval elevated only the read-only monitor.

Only new diagnostic copies changed: collect.py adds timing/retained-handle observations; probe_timing.py and probe_analysis.py are new; launch.ps1 creates the bounded diagnostic runs. The copied monitor, queue, journal/Reader, workload and workspace implementation are byte-identical. Evidence/preparation/reconciliation/report/archive scripts are new under this report directory; preparation helper is `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\prepare_probe_diagnosis.py`. No acceptance probe, threshold or correction is changed in the existing candidate.

| Diagnostic file | SHA-256 |
|---|---|
| collect.py | 049efbc403e4ae7246b02387f361b3854dfc04d242364c8608d4c99681f02423 |
| launch.ps1 | 40cc0f91b09e0f3b31692012445dc98d8ea74df258d1971ca079df113a1c4e30 |
| probe_analysis.py | 1112ac400bbd9bf2d63593551fe42ce8f6b6e9f689998fd5c2d81e0f4fcbc1f2 |
| probe_timing.py | a5958953b2089bd375e81b20befada7d87cf7de1a9161871d1aa8758d8a1c74d |


Pre-change hashes: `source-before.json`; complete post hashes: `final-source-hashes.json`; exact collector diff: `diagnostic-source.diff`; all source copies and scripts are archived. Rollback means leave this diagnostic workspace unused and keep the previous candidate; there is no production rollback. Do not delete failed evidence.

## 21. Protected-baseline eligibility

**NOT AUTHORIZED / NOT JUSTIFIED.** No protected hashing, suspended acceptance repetitions, final five-workload acceptance campaign or dry run was performed. Stage 6 remains blocked pending probe issue review and all outstanding monitor acceptance gates. **HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.** Historical 13.7/14.084/14.565-second delays are not conclusively assigned a common cause.

## 22. Evidence/archive and commands

Report/evidence: `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-probe-diagnosis-20260920`. Live evidence: `D:\JARVIS-STAGE6-LIVE\fb8ef11d2c4d44cca4d352d4a9fdfc93\code`. Final archive destination: `C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 PROBE DIAGNOSIS 20260920`. `archive-verification.json` is the authoritative post-copy member-count/SHA-256 receipt; archive success is claimed only after that receipt exists. Prior evidence.zip and manifest hashes were rechecked unchanged against their prior receipt (`prior-archive-preservation.json`).

Actual invocation pattern (each separate run received UAC approval):

```powershell
& 'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe' -NoProfile -File 'D:\JARVIS-STAGE6-LIVE\fb8ef11d2c4d44cca4d352d4a9fdfc93\code\launch.ps1' -Mode <mode> -Duration <seconds> -Label <label>
```

Exact tuples: `(idle,120,baseline)`, `(disk,100,reads)`, `(sustained,150,hash1)`, `(cpu,40,cpu)`, `(Dhash,90,dhash)`, `(sustained,150,hash2)`, `(sustained,150,hash3)`. Per-run case.json, launch.json, source-hashes.json and probe-timings.json record the actual runtime identities/arguments. Each launcher then ran `collect.py`, `analyze.py`, `event_analysis.py`, `probe_analysis.py` with that unique run ID under the existing venv Python `-B`.

Fresh post-run commands: `python -B reconcile.py`, `python -B final_checks.py`, unchanged `pwsh -NoProfile -File test_queue.ps1` with process-local D TEMP/TMP; Python AST parse and PowerShell ParseFile validation (no bytecode or script execution). Evidence finalization: `python -B archive.py seal`, then `python -B archive.py transfer`, after all collection ended. No OneDrive archive writes were part of the live heartbeat path.

Final diagnostic status: **STRONG_CAUSAL_EVIDENCE**. Stop for owner review; no correction implemented.
