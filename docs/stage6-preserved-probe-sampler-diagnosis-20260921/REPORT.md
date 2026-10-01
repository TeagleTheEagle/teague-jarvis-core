# Stage 6 preserved probe and sampler diagnosis

**Final status: INCONCLUSIVE**

The original probe and sampler failures remain failures. They overlap, but the current evidence establishes neither a common cause nor independent causes. Bounded sacrificial testing did not reproduce either original failure. No correction, deadline increase, full-size campaign, acceptance retry or protected baseline capture was performed.

## 1. PID 23408 timeline

Identity: PID 23408, creation FILETIME 134343831274954036, kernel sequence 32578, parent PID 9808 / sequence 32179. Image `D:\JARVIS-STAGE6-LIVE\e23d36c0a24246c996aa28e5d5561863\code\J6Probe.exe`. SHA-256 `23240ef9f8b0a9a324110b1c2331de31dc1b0e08f5359cb707e51a939af56cd3`, byte-identical to the currently installed `C:\Windows\System32\whoami.exe`.

QPC frequency 10,000,000 Hz. Time zero is the saved probe launch request, QPC 2158637688544. The table uses raw same-host monotonic measurements, not reconstructed wall-clock guesses. Event timestamps, callback timestamps and observed signaled-handle timestamps are distinct.

| Seconds from probe launch | Observation | Evidence |
|---:|---|---|
| 0.000000 | launch | probe-timings.json |
| 0.000075 | CreateProcess begin | probe-timings.json |
| 0.000597 | kernel process start | etw-result.json |
| 0.005428 | CreateProcess returned | probe-timings.json |
| 0.005477 | handle acquired | probe-timings.json |
| 1.039959 | sampler query requested | sampler-results.json |
| 1.040279 | sampler CreateProcess began | sampler-results.json |
| 13.090466 | sampler kernel process start | etw-result.json |
| 13.099750 | sampler CreateProcess returned | sampler-results.json |
| 13.099995 | sampler resumed | sampler-results.json |
| 13.134754 | sampler cleanup began | sampler-results.json |
| 13.602454 | hard deadline observed | probe-timings.json |
| 16.488779 | independent wait returned timeout | probe-timings.json |
| 17.171637 | child 4792 created | kernel parent sequence 32578 |
| 17.195310 | kernel exit event | etw-result.json |
| 17.196183 | child 4792 exit | etw-result.json |
| 17.197735 | kernel tracer observed signaled handle | etw-result.json |
| 18.501294 | sampler cleanup returned failed | sampler-results.json |
| 19.182236 | kernel STOP callback | etw-result.json |
| 19.203184 | sampler kernel exit | etw-result.json |
| 19.211344 | sampler signal observed | etw-result.json |
| 19.262830 | application STOP callback | app-events.jsonl |
| 19.263693 | application STOP persisted | app-receipts.json |
| 19.514570 | final probe cleanup reconciliation | probe-timings.json |
| 20.275591 | sampler STOP callback | app-events.jsonl |
| 20.276639 | sampler STOP persisted | app-receipts.json |

Probe entry, work begin/end, internal cleanup/return and exact kernel-handle signaling instant are **UNKNOWN**. The retained-handle observation bounds the exit signal; it is not substituted for the exact signaling instant. Kernel creation-to-exit FILETIME duration is 17.1945539s. Launch-to-kernel-exit QPC is slightly different because process creation follows launch.

## 2. Process tree, handles and I/O

Parent: Python collector PID 9808, created 134343830676760972, sequence 32179, launched by PID 24372. Its command is supported by the frozen launcher source: the existing Python executable with `-B`, `large_collect.py`, and this run name. It exits 1 after failure cleanup.

Exactly one kernel-sequence-qualified probe child is recorded: `C:\Windows\System32\conhost.exe`, PID 4792, created 134343831446664454, sequence 32581, parentSequence 32578. It was created 17.1710418 seconds after probe creation, lived 0.0244561 seconds, and exited 0 approximately 0.000944 seconds after the probe. It did not exist at the 13.6-second probe deadline. No earlier child is recorded; kernel loss counters are clear and historical event reconciliation passed. Child command line is **UNKNOWN**, not inferred.

The probe has no arguments, uses cwd `D:\JARVIS-STAGE6-LIVE\e23d36c0a24246c996aa28e5d5561863\code`, CREATE_NO_WINDOW, stdout/stderr DEVNULL and Popen's default close_fds=True. There are no stdout/stderr pipes to fill. The retained TreeTracker and kernel tracer independently bind handles to creation times and report exits/handle closure. A full inherited-handle table, opened-file list and thread-wait stacks were not captured. The child's late appearance does not prove console attachment was the blocking operation.

## 3. Delay-owning probe stage

CreateProcess returned after 0.0053532s. Almost the entire 17.195s process lifetime precedes the recorded console-helper creation. This excludes a long parent CreateProcess call and an already-running recorded child as explanations for this probe's deadline breach. It does **not** distinguish initialization, an internal security lookup, scheduler delay, blocking I/O, or another pre-helper activity. Recorded process CPU accounting is zero ticks; accounting granularity does not prove that no user instructions executed. Classification: **UNKNOWN**.

## 4–5. Sampler timeline and failed boundary

Sampler query ordinal 6, mode `normal`, PID 7712, creation FILETIME 134343831405852703, kernel sequence 32579; it is a sibling of the probe, not its child. The fixed command uses the existing Python executable, `-B`, `sampler_worker.py`, this run name, mode normal, and a per-query Local\J6Secondary mapping name. No arbitrary caller command is accepted. CreateProcessW uses CREATE_SUSPENDED | CREATE_NO_WINDOW, bInheritHandles=False, followed by bounded Job assignment and ResumeThread. No stdout/stderr capture pipe is created; results use the existing 4096-byte mapping.

CreateProcessW consumed **12.0594708s**. The launch-based two-second query budget was already expired before ResumeThread at +13.099995s. Its normal query would read GlobalMemoryStatusEx/GetSystemTimes and return JSON, but no result or internal worker-entry timestamp exists. The original timeout/cancellation reason was overwritten by REQUIRED_CLEANUP_UNPROVEN. Source sequencing and elapsed time support an exhausted-query-budget interpretation; the report does not invent an absent recorded branch reason.

Cleanup began at +13.134754s and returned at +18.501294s: **5.3665398s**. Existing code uses a two-second predicate loop, then (if still unsignaled) one existing two-second handle wait after closing the Job. These are not a single two-second end-to-end cleanup deadline. The 47 predicate observations span 3.35438s, with one **2.4006101s observation gap**. Individual WaitForSingleObject/QueryInformationJobObject/sleep/TerminateJobObject call entry/exit timings are not present, so the owner of that gap is UNKNOWN.

At the failed boundary, Job active count was zero but the retained process handle remained unsignaled. Both predicates are required. A recorded termination request succeeded; eventual kernel exit code 230 (0xE6, the existing sampler termination code) was observed at +19.203184s, after cleanup had already failed. Thread eventually stopped. Job-empty alone was correctly not accepted as process-exit proof. No evidence justifies relaxing this rule.

## 6. Temporal relationship

Probe lifetime overlaps sampler creation/cleanup for 16.1550308s. The probe starts first; sampler creation begins +1.040279s, returns +13.099750s, then both remain unresolved across the probe deadline. The sampler observation gap overlaps the independent probe wait's late return. A shared external stall is plausible but **UNCONFIRMED**. Different observed blocking stages do not prove independent causes. No causal arrow is established.

## 7–9. Monitor, events and cleanup

Historical heartbeat maximum: **1.0561466s**, below unchanged 10s threshold. Longest instrumented stage: wait.event, 1.0553855s; no timing overflow. Historical 372 STARTs / 372 STOPs reconciled to 372 kernel identities, 343 retained-handle exits plus 29 qualified post-exit cases. All 809 queued events persisted and were removed; zero remaining, four external EventIdentifier collisions, zero internal queue collisions. Observer durable finalization succeeded.

Final historical exit proof is separate from the failed sampler deadline. Fresh final host checks found zero matches among **517 recorded PID/creation identities** (375 historical including launcher/observers, plus 142 newly observed retained identities), zero matching diagnostic/VirtualBox processes and zero diagnostic trace sessions. Fresh TreeTracker reports all acquired handles signaled and closed, no recorded tracker errors, and its thread stopped. Short-lived reproduction helpers were not exhaustively traced with ETW/CIM; complete new child-event coverage is not claimed.

Last successful historical resource sample before the stalls recorded 28% memory load and 24,584,843,264 available physical bytes. It is not a sample during the stall. Disk metrics were explicitly NOT_COLLECTED; no scheduler-stack, Defender/filter latency or image-load wait trace exists. No storage/security root cause is asserted.

## 10. Bounded reproduction results

Command: existing Python executable, `-B`, `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-preserved-probe-sampler-diagnosis-20260921\narrow_reproduction.py`. Fresh run: `D:\JARVIS-STAGE6-LIVE\e23d36c0a24246c996aa28e5d5561863\code\narrow-1e4b8986e27742f7b47df58b26969ec1`. All live artifacts and process-local TEMP/TMP remained on D:. No UAC, ETW/CIM observer, VirtualBox or JARVIS Core was launched.

| Condition | Probes | Min lifetime s | Median s | Max s | Max CreateProcess s | Deadline failures |
|---|---:|---:|---:|---:|---:|---:|
| idle | 20 | 0.021457 | 0.022468 | 0.030352 | 0.011691 | 0 |
| synthetic-D-hash | 60 | 0.022294 | 0.026040 | 0.031812 | 0.004596 | 0 |

Hashing repeatedly read up to the first 64 MiB of the existing synthetic tail.img, with a 35-second maximum worker budget. Actual load duration was 19.800475s; 22,800,236,544 logical bytes read across 340 cycles. This cache-friendly 64 MiB working set does not simulate the full 59.7 GB storage footprint, and logical read throughput is not physical disk throughput. No full dataset hash pass or protected-size acceptance run was repeated. Original dataset inventory/metadata remained unchanged.

| Sampler case | Result | Create s | Total query + cleanup s | Cleanup s | Exited / handle closed / Job active |
|---|---|---:|---:|---:|---|
| normal | AVAILABLE / normal response | 0.008185 | 0.090970 | 0.010352 | True / True / 0 |
| delayed | MISSING / QUERY_TIMEOUT | 0.006963 | 2.015373 | 0.010200 | True / True / 0 |
| cancellation | MISSING / CANCELED | 0.006228 | 0.132707 | 0.010329 | True / True / 0 |

Delayed mode is the existing intentional five-second sleep with the unchanged two-second query budget; missing telemetry plus proven cleanup is expected. Cancellation used the existing hung fixture and a 0.1s cancellation signal. These injected missing-result cases are not reproductions of REQUIRED_CLEANUP_UNPROVEN. All three retained exits were proved. No original failure reproduced, so no automatic retry or expanded test ladder occurred. Fresh heartbeat/event acceptance was not attempted or claimed.

## 11–13. Decision, minimum correction and uncertainty

**INCONCLUSIVE.** The sampler's prolonged process-creation call and later unsatisfied exit predicate are established observations. The probe's internal delay-owning operation and any shared underlying cause remain unknown. Neither COMMON_CAUSE_STRONG_EVIDENCE nor INDEPENDENT_FAILURES_STRONG_EVIDENCE is supported. No functional correction is presently justified; therefore none was implemented.

Smallest proposed next diagnostic change, for review: add timestamps around the fixed sampler's individual creation/resume/terminate/wait/accounting calls, and capture narrowly bounded startup/thread-wait evidence for the same fixed probe/sampler images under a small sacrificial load. Preserve existing Job ownership, retained identities, fail-closed rules and 13.6/15/10-second limits. Any additional elevated tracing must use the existing per-run approval boundary or receive separate review. Do not switch helpers, loosen cleanup predicates, or extend budgets merely because small tests pass. An entry/exit-instrumented native control can be a comparison only; it must not silently replace the accepted probe.

## 14–18. Preservation, eligibility, archive and final status

- Protected VM/configuration: **NOT ACCESSED**. No real baseline hashes, configuration reads or VirtualBox operations.
- Production JARVIS: **UNCHANGED**. Only new diagnostic/evidence scripts were added under this report directory, with fresh sacrificial evidence on D:.
- Frozen failed run: all **40 raw files** preserve hash, size and modification time; all **100 candidate source hashes** and the source-manifest hash remain unchanged.
- Original **196-member archive** fully hash-verified before testing and unchanged afterward. Its SHA-256 remains `83273efa887a3ab5fd5490b6cd02779d2bbccd695d741fa0b4ba102b22762c47`. New archive receipt is separate and does not reclassify the failed run.
- Protected-baseline eligibility: **BLOCKED / UNAUTHORIZED**.
- Final status: **INCONCLUSIVE**.

All historical long-probe and heartbeat-delay causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Rollback: no candidate/runtime changes to undo. Preserve both old and new evidence; leave the failed run unchanged. No deletions, retries, acceptance sealing or protected-baseline steps are authorized by this result.
