# Stage 6 monitor timing diagnosis

**FINAL STATUS: STRONG_CAUSAL_EVIDENCE**

**Protected retry eligibility: NOT JUSTIFIED. No correction implemented.**

Two fresh sacrificial failures locate the blocking region inside synchronous `FileStream.Flush(true)` on the monitor's heartbeat path. The call took **11.0008449 seconds** during C: hashing and **12.2537014 seconds** during C: read-only load. The reader rejected those runs at ages **10.025585** and **10.0162301** seconds respectively. Event processing cannot proceed while this serial call is outstanding.

This establishes the application call that delayed these NEW runs. It does not identify the exact storage-driver, device, filesystem/filter, or scheduling activity inside that call. It does not retroactively establish the cause of the preserved 14.084-second gap or original 13.7-second delay.

## Controls and stepped load

The workload uses an existing random 1 GiB sacrificial file and aligned, unbuffered 4 MiB reads. CPU-only work hashes an in-memory 4 MiB buffer. D: uses a hash-verified copy of that synthetic file. Monitor and heartbeat journal remain on C: in all comparisons. The C:/D: disks are distinct Windows physical-disk instances; read-only device inventory is in `cleanup.json`. Neither source is a VM artifact.

| Phase | Requested duration | Result | Maximum adjacent-record interval | Maximum Flush(true) call |
|---|---:|---|---:|---:|
| Idle control | 30 s | Completed | 1.0670153 s | 0.0040373 s |
| Low-rate C: reads | 25 s | Completed | 7.6849770 s | 6.6373379 s |
| Moderate C: hashing | 30 s | Completed | 7.9032939 s | 7.8810028 s |
| Full-speed C: hashing | 35 s | Completed | 7.9324750 s | 7.9280581 s |
| Sustained C: hashing | 150 s | FAILED CLOSED after about 25.6 s; remainder not run | 7.2919939 s before final stall | **11.0008449 s** |
| CPU-only, one worker | 40 s | Completed | 1.5125496 s | 0.4562363 s |
| C: read-only, no hashing | 50 s | FAILED CLOSED after about 32.9 s; remainder not run | 9.9856880 s before final stall | **12.2537014 s** |
| D: hashing | 50 s | Completed in separate run | 1.0701239 s | 0.0058969 s |

The consumer stops the run after rejection; therefore there is no next heartbeat after either final stall. Adjacent-record interval maxima must NOT be substituted for the final blocking duration. Failure output and unfinished phase records are preserved, not converted to passes. The D: phase was not reached in the failed CPU/disk sequence; a separate fresh diagnostic completed that remaining comparison. `collect-original.py` preserves the earlier driver; the sole driver extension adds the standalone D: plan.

These are diagnostic comparisons, not two successful sacrificial acceptance runs. CPU-only means this worker did no disk workload; background host disk activity was still measured. One CPU worker is not a whole-machine CPU saturation test. Resource samples are observations, not proof of exclusive workload isolation.

## Exact new failure timeline

QPC frequency was 10,000,000 ticks/second. Full marks are in each run's `loop-trace.json` and parsed `analysis.json`.

### Sustained C: hashing, sequence 102

- Record timestamp: QPC **121596657116**, UTC **2026-09-18T04:30:36.8630720Z**.
- Write begins/ends: **121596659120 → 121596659406** (28.6 microseconds).
- Flush begins: **121596659599**.
- Reader rejects: poll begins **121696910772**; after exception **121696912955**; age **10.025585 s**.
- Flush ends: **121706668048**; elapsed **11.0008449 s**.
- Publication-complete mark: **121706668413**.
- Stop-marker check observes the collector failure; no next heartbeat is emitted. Event grace/drain and cleanup follow.

### C: disk-read-only, sequence 57

- Record timestamp: QPC **123267222816**, UTC **2026-09-18T04:33:23.9196395Z**.
- Flush begins/ends: **123267224717 → 123389761731**, elapsed **12.2537014 s**.
- Reader rejects at QPC **123367385103**, observed age **10.0162301 s**, while flush is still outstanding.
- No next heartbeat; the run stops and cleans up.

The managed Flush(true) bracket includes managed buffering, OS flush and any time preempted while inside the call. No native kernel-stack/ETW trace was taken, so attributing every tick specifically to hardware flush would exceed the evidence.

## Historical 14.084-second gap

The longest known heartbeat-to-heartbeat interval remains **14.0840902 s**, from the earlier, uninstrumented run:

T0 = sequence 103 record timestamp, 04:15:28.3967161Z, QPC 112511993563.

T1 (last action), T2 (blocking start), T3 (blocking end), T4 (next action) = **NOT RECORDED**.

T5 = sequence 104 record timestamp, 04:15:42.4808051Z, QPC 112652834465.

These are record-construction timestamps, not flush-completion proofs. The exact missing-time category for that historical event remains **UNKNOWN**. The new experiments identify a reproducible candidate mechanism only. Original 13.7-second delay: **UNCONFIRMED**. **HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.**

## Stage and event timing

Across the new runs, journal open was at most 4.320 ms, Write at most 2.400 ms, record construction at most 5.171 ms, and size checking at most 3.034 ms. No rotation was used. Journal close was at most 1.774 ms. Flush dominated the failing iterations. Raw stage durations, loop durations, queue depth, event timestamps and overlapping resource samples are retained in the analysis files.

Event-drain maximum was 0.500 s in the stepped run and 3.240 s in the CPU/disk run. The latter contained a **3.237-second event-log AppendAllText** call. This is another synchronous storage operation on the event/heartbeat path and remains a design risk. JSON serialization stayed below 0.184 ms. Queue snapshots were small (maximum depth 2 in the CPU/disk run) and final measured backlog was zero. No application mutex/semaphore exists in this path; internal OS/.NET lock waits are not independently measured.

Harmless process probes: stepped 17/17 starts and 17/17 stops; CPU/disk 8/8 starts and 8/8 stops; D: 5/5 starts and 5/5 stops. **30/30 starts and 30/30 stops captured overall.** Filters for VBox/VirtualBox are unchanged. No VirtualBox process was launched. Native event creation to drain and PowerShell queue timestamp to drain are recorded; neither is an exact process birth/death measurement. The stepped run's maximum observed delivery-to-drain delay was about 7.151 s. A blocked monitor can delay event consumption even when eventual counts match.

## Scheduling and resources

All three monitors self-reported **Normal** priority; no priority was changed. Maximum measured `Wait-Event -Timeout 1` duration was **1.070486 s**. Its approximately 70.5 ms overrun is a combined timer/runtime/scheduling upper bound, not per-thread ready-queue latency. The long stalls are inside flush, not the explicit wait. There is no evidence justifying a priority increase.

During the C: read-only failing flush, sampled total CPU peaked near **9.98%**, monitor cumulative CPU advanced only about **0.047 s**, C: active time reached **100%**, instantaneous C: queue reached **13**, and available memory stayed above **20,372 MiB**. These observations and the no-hashing reproduction support storage-path involvement rather than sustained CPU computation. They do not identify a particular driver or antivirus filter.

D: hashing reached about 234.9 MB/s sampled D: reads while the C: journal's flush stayed below 5.9 ms. Changing the workload volume changes several factors; this is supporting evidence, not proof that relocating the protected files is necessary or authorized.

Telemetry includes per-logical-processor usage, aggregate CPU, process CPU/working set/priority/thread state, system context switches, memory available/pages per second, disk idle/queue/latency/read and write throughput. Page counters are system indicators, not exact per-process page-fault attribution. GC collection counts are logged, not GC pause durations. MsMpEng was included in the process-sampling query but no useful Defender activity series was obtained. Antivirus involvement is neither established nor excluded. No security setting was changed.

## Minimum correction proposed — NOT implemented

The smallest first candidate is to remove **forced durable synchronization from each live heartbeat**:

1. Keep the single append-only stream, nonce/PID/creation identity, contiguous sequence, event-pump binding, bounds, liveness checks and 10-second rule.
2. Replace the in-loop `Flush(true)` with `Flush(false)` solely to make managed bytes visible to the reader without requiring a device durability barrier on every beat.
3. Require a final durable flush and successful close of all evidence before a baseline manifest can be accepted. Flush/close failures must block acceptance. A crashed/dead publisher remains immediately invalid through its pinned process handle; a crash-lost journal is not valid evidence.
4. Do not issue healthy heartbeats independently of event-drain progress. A separate publisher that keeps ticking while the event consumer is stalled would weaken the contract and is not proposed.
5. Explicitly test synchronous event-log append under the same load. Its observed 3.237-second delay remains a risk. If it prevents the unchanged contract from passing, return for review of a bounded event-evidence writer; do not silently add one or relax the timeout.

Files likely affected: a NEW reviewed version of the Stage 6 diagnostic `monitor.ps1`, its tests and evidence-finalization collector. Existing failed monitor/capture files remain immutable. Production JARVIS and the protected source do not change.

This candidate changes live-journal durability policy and therefore needs review; it is not claimed safe/accepted by these measurements. `Flush(false)` still performs synchronous writes and is not a universal nonblocking guarantee. Its suitability must be demonstrated. Moving a heartbeat to another volume or increasing priority is not justified as a guaranteed correction by the current tests.

Microsoft documents the distinction between flushing intermediate storage buffers and ordinary flushing: [FileStream.Flush](https://learn.microsoft.com/en-us/dotnet/api/system.io.filestream.flush?view=net-9.0). Microsoft also warns of per-write flush inefficiency: [FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers). These references support the design distinction, not historical incident causation.

## Required revalidation after separate approval

1. Focused identity/sequence/partial-record/stale/death/restart/capacity tests, plus visibility without forced durability and failure of final durable evidence flush.
2. Instrumented idle control and the same low/moderate/full/sustained C: workloads, including sustained hashing beyond the previous failure points; retain 10 seconds.
3. CPU-only, read-only C: and D: comparisons; retain failed/transitional runs.
4. Held-reader, inaccessible journal, malformed/partial record, disk-full/write/flush failure, publisher death, collector/hash-worker crash and restart tests. No stale record may restore health.
5. Process-event probes during load and stalls; validate queue bounds, event evidence completeness and fail-closed behavior.
6. Two complete sacrificial baseline-style runs with hash/rehash, source preservation, final durable evidence, manifest/hash and clean process exit. Stop on failure.
7. Archive/hash verify all evidence and obtain owner review. Only then consider a separately authorized protected baseline retry.

## Preservation and evidence

Only new diagnostic files under `docs/stage6-monitor-timing-20260918` and the synthetic D: comparison file were created. The copied journal reader is unchanged. The original monitor and failed evidence remain preserved. No protected VM/configuration access, production operation, priority/security change, or threshold change occurred.

`cleanup.json` verifies zero relevant helpers and zero VirtualBox processes after all tests. Synthetic files are retained; no deletion was performed. Syntax and source integrity results are in `verification.json`. Exact source/evidence hashes and archive verification are recorded with the archive. The synthetic binary and harmless probe executable are excluded from archival copying.

Primary evidence: `stepped/loop-trace.json`, `stepped/rejected-poll.json`, `stepped/analysis.json`; corresponding `isolation` files; `volume-d/analysis.json`; each run's raw resource counters, workloads, event list and probe identities. The separate `TIMING-PRIMITIVE-AUDIT.md` records all synchronous calls and their bounds.
