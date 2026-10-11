# MONITOR_ARCHITECTURE_DEFECT

Diagnostic-only outcome, 2026-09-18. No protected VDI/configuration reads, VM operations, production changes, Windows security changes, baseline retry or accepted-monitor correction performed. Original monitor/capture source hashes remain unchanged. All new code is sacrificial diagnostic tooling in this evidence directory.

## 1. Confirmed findings versus historical uncertainty

HISTORICAL 13.7-SECOND HEARTBEAT DELAY CAUSE: UNCONFIRMED.

NEW SYNTHETIC FINDING: heartbeat publication failed in File.Move(temp,target,true) with Access denied. The collector observed monitor-failure.json and stopped. This is a monitor evidence-publication failure, not a JARVIS/VirtualBox/protected-data defect. No 10-second health failure was reproduced before this different failure.

Controlled native MoveFileExW replacement tests on sacrificial files:

| Condition | Replacement successes | Failures | After reader closes |
|---|---:|---:|---:|
| No reader | 30/30 | 0 | N/A |
| Ordinary Python open reader held | 0/30 | 30 WinError 5 | 30/30 succeed |
| Explicit Windows share-read/write/delete reader held | 0/30 | 30 WinError 5 | 30/30 succeed |
| Append-only writer while ordinary reader held | 30/30 | 0 | N/A |

The controlled tests establish an open-reader/replacement failure mechanism on this host. No native handle trace captured the exact competing handle at the live synthetic monitor failure; that specific attribution remains inferred. Share-delete alone is NOT a proven fix. The new evidence does not establish the cause of the historical heartbeat delay, original Stage 1 incident or any other historical error.

## 2. Design review

Original hashing: unelevated Python process; hashlib reads 4-MiB chunks synchronously. It checks monitor state between chunks, at roughly 0.25-second intervals when reads return promptly.

Original heartbeat: separate elevated PowerShell process, foreground runspace/main script loop. Drain-Events → synchronous JSON write/rename → collector-finished check → Wait-Event -Timeout 1. There is no heartbeat background job, timer thread or shared hashing runspace. WMI indication delivery queues events in that monitor session; the foreground loop consumes them.

Therefore hashing cannot directly block the heartbeat by occupying the same thread/runspace. CPU scheduling, storage/filter contention, system pauses, clock adjustments, slow heartbeat publication/observation, or an event-loop delay remain possible. A blocked filesystem operation in the monitor can delay both its heartbeat and its event-queue drain. A blocked Python read can postpone its next health check. This design is not hard-real-time.

PowerShell event delivery and script processing are distinct. Queued events can await the next Get-Event while foreground work is busy; no assumption of immediate script execution during a synchronous call is valid. The actual original monitor used queued events, not an -Action callback sharing the hasher.

Sources: https://learn.microsoft.com/en-us/powershell/module/cimcmdlets/register-cimindicationevent and https://learn.microsoft.com/en-us/previous-versions/windows/desktop/krnlprov/win32-processstarttrace

## 3. Sacrificial workload and measurements

Used a newly generated 1-GiB random file under this directory on C:, the same host volume as the protected VM. Protected files were never used. Intended phases: 30 seconds idle, 90 seconds one hasher, 90 seconds two hashers. Actual: idle and single-hasher phases finished; the two-hasher phase stopped early on publication failure. This is NOT a passing complete stress campaign.

Buffered single hasher: 106,338,189,312 bytes hashed, 99 full passes in its bounded phase. Two hashers stopped after 15,233,712,128 and 14,474,543,104 bytes. These buffered passes benefit from cache and do not represent cold 55.6-GiB VDI I/O.

A concurrent sacrificial unbuffered read/hash probe used FILE_FLAG_NO_BUFFERING | FILE_FLAG_SEQUENTIAL_SCAN, without changing global cache/security settings. It read 4,013,948,928 bytes over 13.813 seconds before stopping on monitor failure. Its planned 60 seconds did not complete. This increased physical C: I/O but is not equivalent to the original compressed VDI workload.

Before failure, 148 monitor timing records / 147 intervals / 1,411 collector observations:

| Metric | Median | p95 | Maximum |
|---|---:|---:|---:|
| Heartbeat interval | 1.0232 s | 1.0429 s | 1.0768 s |
| Heartbeat publication duration, successful writes | 1.344 ms | 1.891 ms | 9.418 ms |
| Event drain duration | 0.0866 ms | 0.7973 ms | 21.153 ms |
| Wait-Event duration | 1.0197 s | 1.0372 s | 1.0602 s |
| Collector heartbeat-file read | 0.431 ms | 0.619 ms | 0.956 ms |

Maximum observed age: idle 1.0370 s; single hasher 1.0524 s; two hashers 1.0237 s. Monitor CPU: 3.516 CPU-seconds over 147.973 elapsed seconds (not system-normalized CPU percentage). Monitor priority self-reported Normal. Collector and workers observed at Normal priority. Other PowerShell process CPU deltas are recorded in process-cpu-summary.json; elevated process priority was unavailable to the unelevated sampler and not fabricated.

54 valid resource samples, covering part of the run:
- Total CPU: median 12.06%, peak 26.29%.
- C: current disk queue: median 0, peak 3.
- C: average disk-read latency counter: peak 9.399 ms.
- C: % Disk Time: peak 142.56. This counter is not a bounded wall-clock active percentage and can exceed 100; do NOT describe this as 142% physical activity. Exact bounded active-time measurement was not obtained.
- Available RAM: minimum 21,937 MiB; committed memory peak 40.07%.
- Wall-time/monotonic interval discrepancies: within approximately 0.367 ms during recorded intervals; no large clock jump observed in this synthetic run.

No evidence here establishes CPU/memory saturation as the cause. Physical I/O rose in the direct-read period, but the observed terminal failure was file replacement denial, not a measured 13.7-second scheduling stall. No Defender trace or filesystem-filter operation trace was collected; involvement is unconfirmed. Security tools were not disabled. The historical run lacked these measurements.

## 4. Event coverage

Initial synthetic filter added an exact long process name, Stage6EventProbe.exe. It captured 45 start records from 46 launched probes before the monitoring failure, with no stop records. At least the last probe overlaps the failure boundary; the initial PID-only aggregation can collapse reused PIDs and is not accepted as complete coverage proof.

A separate 45-second coverage run used prefix filters and two harmless copies of Windows whoami.exe, with no Oracle code launched. Result: 20/20 start events and 20/20 stop events, with unique PIDs in that bounded set. Long-name stop events arrived as Stage6EventPro. The diagnostic exact-name filter had missed those shortened names; the existing baseline VirtualBox filters already use VBox% / VirtualBox% prefixes.

The six required real names are covered by the original prefixes, including shortened stop names that retain those prefixes. They were NOT actually launched. No absolute minimum detectable process duration is proven. The shortest captured probe had a 37.42-ms launch/wait upper bound, not a measured exact process lifetime. Maximum start receipt after launch-begin was 1.690 seconds. WMI TIME_CREATED is event creation time; it must not be treated as exact kernel process birth/death. Event creation-to-receipt latency in analysis.json is not end-to-end launch latency.

Limitations: WMI delivery delay, subscription failure, queue loss under untested load, renamed binaries outside prefixes, and monitoring gaps during startup/teardown remain relevant. No finite test proves all shorter-lived processes will be detected. A monitor must fail closed on subscription/health errors and require zero event counts for capture acceptance.

## 5. Threshold assessment

The original 10-second limit was selected locally by the capture implementation, not traced to an owner-specified numeric acceptance requirement. This run gives no justification to increase it. Maximum observed healthy interval 1.077 seconds leaves substantial empirical headroom, but the truncated stress campaign is insufficient to establish a legitimate worst case.

Keep 10 seconds unchanged pending review/validation. Use monotonic elapsed time since the last verified sequence advance, with UTC retained for audit, rather than relying only on wall-clock age. Expiry or monitor failure must stop hashing and invalidate the capture. Detection is bounded by event delivery and the next collector check/read completion; do not promise instantaneous interruption of an in-flight OS read.

## 6. Minimum proposed correction — NOT IMPLEMENTED

Retain the separate elevated event-monitor process and unelevated hasher. Do not add another privileged service or alter JARVIS/Core.

Replace overwrite-by-rename heartbeat publication with a bounded append-only heartbeat journal, avoiding replacement of a file being read. Use run identity, monitor PID/creation identity, increasing sequence, monotonic timestamps, event-drain sequence and explicit subscription/error state. Flush each completed record. Reader consumes complete records; partial/truncated data must never renew health. Enforce byte/record bounds and fail closed on append/read/subscription errors. No speculative retries or timeout increases. A fresh isolated run must not accept another run's heartbeat.

Heartbeat must attest successful event-pump progress, not merely an independently ticking thread that could hide a stalled event receiver. Keep event records and monitor verdict separate from collector verdict; a monitor-final PASS must never override a failed collector. Preserve final drain/closure evidence.

The 30/30 append control supports this mechanism only. Full monitor integration, sustained stress, fault injection and coverage tests have NOT validated it. No original monitor/collector file was modified. Expected future changes are confined to reviewed baseline capture/monitor tooling and diagnostic tests, not JARVIS runtime or Windows security configuration.

## 7. Exact safe retry procedure — NOT EXECUTED

1. Review/authorize the proposed heartbeat IPC correction; preserve all current evidence and original helper hashes.
2. Implement only the corrected diagnostic/capture tooling in a fresh versioned evidence directory. Keep hashing unelevated and the event monitor minimally scoped.
3. Before protected access, complete sacrificial idle, buffered, physical-I/O and concurrent-reader stress runs at the unchanged 10-second limit. Test partial journal records, stale/run-mismatched records, monitor exit, event-subscription failure, and stop/start event completeness using harmless short-lived probes and prefix filters. Any failure invalidates the trial.
4. Require fresh monitor identity, active start/stop subscriptions, zero VirtualBox processes, recent monotonic sequence advancement, successful event-drain self-test and no stale files. Keep VirtualBox closed.
5. Hash the complete 12-file protected inventory and relevant normal configuration once, recording topology and post-incident network=1 separately from historical=0 and validation-copy=0. Check health between bounded chunks; stop on any relevant event, monitor failure or age >10 seconds. No timeout relaxation.
6. Re-read/hash all protected artifacts for a complete second pass; compare counts, sizes, timestamps and all hashes. Complete final event drain and zero-process check before classifying the manifest.
7. Require BOTH collector and monitor success. Canonically serialize/hash the manifest; archive only nonsecret evidence and verify every archive hash.
8. Stop after baseline capture. No account/ACL/copy/VM/guest step follows automatically.

Another protected baseline attempt is NOT JUSTIFIED YET. Historical delay remains unconfirmed and the proposed publication correction needs explicit review plus complete sacrificial validation.

## 8. Preserved diagnostic failures and cleanup

- Original historical stale-heartbeat failure preserved untouched.
- Resource sampler first attempt failed on a null process-priority value; resources-error.txt retained. Separate resources-v2 records unavailable priority as empty. Early resource coverage is incomplete.
- Synthetic monitor publication failed with Access denied; whole stress run recorded BLOCKED, direct-read run FAILED. Both stopped and retained evidence.
- First coverage-only harness had an identifier-array construction failure; event-coverage/failure.json and original script retained. Separate event-coverage-v2 completed after fixing only diagnostic identifier construction.
- First inline append probe failed at command-string Python parsing before execution; subsequent file-based probe ran 30/30 controls. No protected source involved.
- First coverage analysis incorrectly attempted to correlate WMI event-creation time with exact process lifetime and failed with an empty set. Script retained; coverage-analysis-v2.json explicitly corrects that assumption and does not claim exact native lifetimes.

Final process observation: zero VirtualBox or matching diagnostic helpers. No forced termination. The synthetic 1-GiB file and copied probe binaries remain local evidence, excluded from the normal project archive; no automatic deletion occurred. Original baseline tooling hashes unchanged.

HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
