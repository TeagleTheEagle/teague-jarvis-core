# Stage 6 — authoritative writer and independent identity diagnosis

**BOTH_BOUNDARIES_STILL_DEFECTIVE**

This is diagnostic/focused sacrificial evidence, not medium or large acceptance. No production/runtime application file changed. No protected VM/configuration or 59.7 GB dataset was accessed. No VirtualBox operation occurred. All old failures retain their original disposition.

## Findings

The actual C# writer has two measured bottlenecks: producer-lock competition during an unpaced burst, and synchronous durable segment flush during paced load. Hash finalization is not the bottleneck. Bounded dequeue amortization reduces the lock wait but fails the required throughput margin, so it is NOT adopted.

The real identity experiment captured 16 probes / 32 CIM events with kernel/native/retained-handle agreement. It did not establish an independent discriminator inside each CIM event. One candidate in a filtered, controlled kernel table is not proof excluding an older delayed incarnation. Zero false unique selections were made because unresolved events remain ambiguous. This is not a validated positive matcher.

## Mandatory report

### Writer

1. **Historical timelines:** `historical-timelines.json` records all available QPCs and totals. Historical stage/queue time series were not captured; they are UNKNOWN. New timelines are in every `timings.json` and `writer-analysis.json`. New measurements do not fill historical gaps.

| Preserved failure | Admitted / persisted | Rejected | Producer mean | End-to-end consumer mean | Queue high-water | Rollover max |
|---|---:|---:|---:|---:|---:|---:|
| high-rate-result.json | 82926 / 82926 | 1 | 164951.1/s | 68536.8/s | 65536 | 0.464437s |
| large-record-result.json | 108166 / 108166 | 1 | 86696.2/s | 26462.0/s | 65536 | 0.357678s |

2–3. **Producer/consumer rates:** table above uses explicitly different windows; those averages cannot reconstruct an instantaneous deficit. Historical peaks/sustained rates are UNKNOWN. Fresh 50 ms samples provide interval rates (not per-instant peaks) in `writer-analysis.json`.

4–5. **Queue growth/high-water:** initial diagnostic reached 65,536 outstanding queued rows before its first rollover. During the paced 121,515/s diagnostic, queue grew from 33,941 to 65,536 while persisted remained 105,749 in one durable flush. At rejection, admitted minus persisted equals the capacity: exhaustion at that observed deficit is mathematically established. An unbounded-duration producer faster than durable service cannot be rescued by any finite buffer. Old averages alone do not prove an exact exhaustion time.

6–12. **Actual hot-path instrumentation:** following table is the first fresh unpaced run. Quantiles are bounded 8,192-sample reservoir estimates; total/count/max are exact instrumented measurements. Nested times are not additive. Writer lock hold includes time released in Monitor.Wait and is explicitly an upper bound on actual hold. Instrumentation overhead is not independently subtracted. Individual normal flushes are absent; buffered Write internal flushes cannot be separated by this instrumentation. No process-identity enrichment occurs here.

| Stage | Calls | Total ms | Median µs | p95 µs | p99 µs | Max ms |
|---|---:|---:|---:|---:|---:|---:|
| producerLockWait | 78317 | 8.669 | 0.000 | 0.600 | 0.900 | 0.063 |
| producerLockHold | 78317 | 201.178 | 1.200 | 3.400 | 4.600 | 12.900 |
| envelopeSerialization | 78317 | 126.712 | 0.600 | 1.600 | 3.800 | 12.888 |
| UTF8Encoding | 78317 | 44.823 | 0.100 | 0.500 | 2.400 | 7.591 |
| recordValidation | 78317 | 2.345 | 0.000 | 0.100 | 0.100 | 0.010 |
| writerLockWait | 78317 | 210.146 | 0.000 | 7.300 | 29.000 | 12.922 |
| writerLockHoldIncludingIdleWait | 78317 | 8.926 | 0.100 | 0.300 | 0.400 | 0.010 |
| queueDequeue | 78316 | 3.672 | 0.000 | 0.200 | 0.300 | 0.005 |
| segmentOpen | 5 | 1.534 | 220.400 | 706.100 | 706.100 | 0.706 |
| durableFlush | 5 | 826.845 | 149785.100 | 324906.500 | 324906.500 | 324.906 |
| segmentDispose | 5 | 0.775 | 135.200 | 223.500 | 223.500 | 0.224 |
| incrementalSHA256 | 78316 | 28.165 | 0.300 | 0.500 | 0.900 | 0.015 |
| finalSHA256 | 5 | 0.310 | 35.200 | 158.000 | 158.000 | 0.158 |
| segmentManifestMetadata | 5 | 0.106 | 16.700 | 50.800 | 50.800 | 0.051 |
| rolloverTotal | 5 | 828.101 | 149962.400 | 325218.500 | 325218.500 | 325.219 |
| fileWrite | 78316 | 24.323 | 0.100 | 0.200 | 0.400 | 0.169 |
| countSizeUpdate | 78316 | 2.555 | 0.000 | 0.100 | 0.100 | 0.011 |
| finalManifest | 1 | 25.057 | 25057.100 | 25057.100 | 25057.100 | 25.057 |

All eight runs have the same breakdown in `writer-analysis.json`; points record queue occupancy before/after each rollover and each rejection. Serialization/UTF-8 encoding happens under the producer lock. Disk I/O does not. Segment SHA-256 is incremental per record, with a small final digest operation; it does not reread the segment. No per-record manifest rewrite, file reopen, identity query or console I/O occurs. Size/sequence/admission validation MUST remain per record; queue acquisition CAN be batched; hashes CAN use bounded byte batches preserving order; durability/hash/manifest finalization belongs at segment/run finalization; secondary tap formatting is SECONDARY_ONLY but remains captured in the authoritative representation.

13. **Proven current bottleneck: MULTIPLE.** Unpaced writer lock wait 210.15 ms during a 228.12 ms producer burst; durable flush 826.84 ms during a 1.149 s total run. Paced margin trial spent 2.531 s in durable flush out of 2.899 s total. In a later 100k/s trial one durable flush took 1.505 s. D: raw control wrote 128 MiB in 0.0587524 s (buffered), then durable flush took 0.7843268 s; buffered bandwidth is not durable throughput. The Windows/storage/driver cause of these flush latencies remains UNCONFIRMED.

14. **Correction experiment only:** at most 128 rows dequeued per lock acquisition; one ordered writer; per-record append/hash unchanged; 65,536 outstanding-item and 64 MiB byte bounds include in-flight work conservatively. Default batch remains 1. Lock wait fell from ~210 ms to ~7 ms in the unpaced comparison, but both trials still overflowed. No parallel hash writer, deferred durability, timeout increase or queue enlargement adopted. Source/diff: `batch-experiment.diff`, `batch-design.json`. Batching multiple appends into a single byte write is NOT implemented: the measured dominant remaining cost is durable flush.

15. **Focused tests:** 30/30 assertions PASS: normal ordered stream/rollover, write/disk-full/create/hash failure, failure after part of a dequeue batch, partial append, sticky capacity failure, late admission and double-finalization rejection, and 36,000-row actual EventTap control. Reader refuses every failed stream. Queue regressions: 222 assertions PASS, 10,000-event stress with 9,993 external EventIdentifier collisions / zero internal collisions or loss, plus 100 concrete streaming-queue entries reconciled. These safety results do not pass throughput.

16–17. **Stress results and sustained accepted rate:** fresh actual writer with synthetic representative ~476-byte envelopes. This is not real ETW/CIM load acceptance. Original EventTap records averaged ~485 bytes; padded historical records ~985 bytes. No universally safe sustained rate established. A 3-second 50k/s run passed; a 2-second 100k/s run passed before the batching experiment, but subsequent distinct workloads failed. No failure is erased by the passing trials.

| Run suffix | Rate target/s | Requested | Admitted | Rejected | Queue peak | End-to-end rows/s | Flush max s | Result |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 19c702a9 | 0 | 200000 | 83182 | 1 | 65533 | 80813.7 | 0.408960 | FAIL |
| 6bfe70c0 | 75000 | 225000 | 206457 | 1 | 65418 | 48469.5 | 0.349957 | FAIL |
| ab62b617 | 100000 | 200000 | 200000 | 0 | 34568 | 71338.2 | 0.357590 | PASS |
| ac51fdbe | 100000 | 300000 | 83182 | 1 | 65535 | 30389.8 | 1.504930 | FAIL |
| c1c06271 | 121515 | 364545 | 100805 | 1 | 65494 | 49909.1 | 0.348544 | FAIL |
| c75f0c50 | 121515 | 607575 | 171286 | 1 | 65536 | 59076.8 | 0.357469 | FAIL |
| d96a57d9 | 50000 | 150000 | 150000 | 0 | 9078 | 42964.7 | 0.324894 | PASS |
| e638d80d | 0 | 200000 | 78316 | 1 | 65536 | 68139.7 | 0.324906 | FAIL |

Rate 0 means maximum-speed producer, not zero traffic. Batch=1: e638d80d, ab62b617, c75f0c50. Batch=128: remaining five runs. Ordering/hash-verified admitted prefixes have zero gaps/duplicates, even where a rejected admission invalidates the whole run.

18–20. **Capacity model / bounds / rejection:** historical measured aggregate peak 97,212 records/s × exploratory 1.25 margin = 121,515/s (~57.84 MB/s for 476-byte rows). This is a conservative cross-channel test target, not a proved application-channel maximum. Queue 65,536 rows / 64 MiB unchanged. At 121,515/s, an empty queue buffers only 0.5393 s with no drain; at 100k/s, 0.65536 s. A measured 1.505-second flush already exceeds both, before prior backlog. Thus existing finite buffer cannot cover observed pauses at those rates. No arbitrary enlargement adopted, no justified worst-case sustained service bound established. Four of five batching rate/burst trials rejected one admission each.

### Identity

21. **Raw CIM schema:** PID, ParentProcessID, ProcessName, TIME_CREATED, SessionID, Sid, SECURITY_DESCRIPTOR; STOP also ExitStatus. Existing actual observer retains PID, parent, name, TIME_CREATED, kind, receipt/drain QPC, EventIdentifier and internal queue sequence. It does not currently retain SID/session/exit status. None of these documented CIM schemas contains process creation time or kernel process sequence/start key. TIME_CREATED is event generation time, not process creation.

22. **Kernel fields actually observed:** Microsoft-Windows-Kernel-Process START version 4 / STOP version 2 carries ProcessID, ProcessSequenceNumber, CreateTime; START parent PID/parent sequence; STOP ExitTime/ExitCode. Full actual schema arrays appear in `identity-analysis.json`. Process table uses PID + creation + kernel sequence with run/boot scope, not PID alone.

23–24. **Native and handles:** 16 native PE entry markers agree with kernel CreateTime and retained GetProcessTimes creation/exit values. Native records include PID/TID, QPC, image identity, entry address, exit and independent handle wait results. All 16 independent waits signaled, exit code zero; handles were kept through observer closure in the successful diagnostic.

25. **Kernel key availability:** payload ProcessSequenceNumber is present on START/STOP in this installed provider. Documented ETW ProcessStartKey is boot-unique but extended emitter metadata must not be substituted for the payload subject. CIM does not expose that key. Sequence numbers from another API are not assumed equivalent.

26–30. **Creation experiment / positive matching:** 16 real processes, 32 real CIM START/STOP records, exact kernel/native/handle agreement, 32 events with one candidate in the controlled captured table. **Independently proven UNIQUE_MATCH count: 0; final diagnostic AMBIGUOUS: 32; UNMATCHED: 0; false unique selections: 0.** A filtered table with one candidate does not exclude an older delayed incarnation absent from that table. Retaining a handle prevents PID reuse while it remains open; it does not prove that every pending CIM event refers to that object. Do not count these as positive identity acceptance.

31. **START delivery:** {"count": 16, "min": 0.1302505, "median": 0.5854072, "p95": 1.1021182, "p99": 1.1021182, "max": 1.1021182} seconds; only 16 samples, p99 is a descriptive order statistic, not a tail guarantee.
32. **STOP delivery:** {"count": 16, "min": 0.1042936, "median": 0.6896961, "p95": 3.002844, "p99": 3.002844, "max": 3.002844} seconds. STOP can arrive before START. CIM generation occurred up to 3.002261 s after kernel exit in this capture; process-lifetime timestamp containment is invalid for these events.
33. **Event token:** diagnostic token = unique run ID + monotonic queueSequence; identifies only the event. Persist raw event unchanged, all captured candidates, reason for withholding selection, selected=null and correlation version. No kernel key is fabricated.

34. **Correlation rule:** kernel/handle/native equality establishes a process instance; it does not independently bind an unkeyed CIM event. Current production-of-evidence rule remains fail-closed AMBIGUOUS for compatible candidates / UNMATCHED for none. Future global positive acceptance needs an event-bound subject discriminator or a separately reviewed observational protocol whose exclusions are proven.

35. **PID reuse:** no PID reused among 16 current probes or 36 captured kernel rows; handle retention intentionally prevents it. Historical `historical-kernel-reuse.json` records actual earlier same-PID/different-create/different-sequence evidence, not fresh acceptance. It does not resolve the historical CIM events.

36. **Delayed/negative cases:** actual delayed START/STOP captured and left ambiguous. 24 synthetic adversarial safety cases rerun PASS, including reuse, delayed notification, forged event key, duplicate creation and parent mismatch; no raw-event mutation. Full independent positive matching and event-pressure/PID-reuse experiment remain NOT SATISFIED, not simulated as a pass.

37. **Historical 22 events:** 21 AMBIGUOUS / 1 UNMATCHED unchanged. New evidence is not retroactively attached to them.

### Integration, preservation and decision

38–40. **Tap / sequence / integrity:** actual EventTap control preserved 36,000 authoritative rows with secondary tap limited to 20,000 and 4,000 tap rows explicitly truncated. All completed writer prefixes verified against sequence, segment hash/count/size; failed admissions remain FAIL. New real application stream and all native trace segments hash-verified. No new acceptance criterion based on tap completeness.

41. **Trace loss:** corrected identity diagnostic: ETW eventsLost=0, buffersLost=0, realtimeBuffersLost=0, kernel faults=0; 182,733 detailed native/kernel records in 8 segments verified. This is one small diagnostic, not full capacity proof.
42–43. **Medium readiness/validation:** NOT READY / NOT RUN. Part A sustainable margin and Part B positive event-instance proof are unsatisfied. Part C integration and optional medium campaign were not attempted. Large dataset and protected hashing NOT RUN.

44. **Heartbeat:** corrected identity experiment maximum 1.2544289 seconds, below unchanged 10-second limit. Writer-only benchmarks have no process heartbeat observer and make no heartbeat acceptance claim.
45. **Deadlines:** corrected experiment zero process deadline violations. First diagnostic failed immediately due to NEW driver mixing Python monotonic seconds with QPC seconds (measured origins differed by ~31.4 s); kernel native lifetime was ~36 ms. Original failure is preserved, not relabelled PASS. Driver corrected only campaign-deadline clock domain; 13.6 s process / 15 s observer / 10 s heartbeat unchanged.

46–48. **Lifecycle/native/handle:** corrected diagnostic has all 16 START + 16 STOP probe events, all 16 native PE entries and exact retained-handle equality. 36 kernel instances have complete start/stop capture. This establishes raw lifecycle evidence, not unique CIM attribution across arbitrary previous incarnations.

49. **Cleanup:** latest exclusive host preflight shows zero matching diagnostic/elevated helper/VirtualBox processes and zero trace sessions. Both observer exit codes zero; worker zero on corrected run. Failed first worker exit 1 preserved; its kernel/observer exits zero and probe exited. No forced termination used.

50. **Archive:** see adjacent `archive-verification.json` created after report freeze; it records ZIP and manifest hashes, exact member count, archive reread verification and canonical path. Archival occurs after monitoring stopped.

51. **Hashes:** `final-source-preservation.json` proves 116 frozen + 6 other recorded files unchanged; prior five archives and all 261 payload members of the 262-member current archive remain unchanged. Only new diagnostic copies, scripts and evidence changed. Exact changed-file before/after hashes follow.

| Fresh-copy changed file | Before SHA-256 | After SHA-256 |
|---|---|---|
| D:\JARVIS-STAGE6-LIVE\0febafa860ad4fc1aee8d72669c3484a\code\AuthoritativeEvents.cs | c108252d6eaba67c8452e285e1fa2931988f3d0f798569f5032b15cb2bb786d9 | 8e9b7d1468dd2a86d6831ee1ca86c333be6a7d78eabe228616e9f3158d05577b |
| D:\JARVIS-STAGE6-LIVE\0febafa860ad4fc1aee8d72669c3484a\code\timed_monitor.ps1 | 55ae883301dfdd777a1c86b9be922c837766101e62fdd3bf1bfe2507dc01720b | 106f1086f2bcc45837668a2affbaa6d3d345d51d01953cfce77da1dc422edb83 |

New diagnostic files and hashes are enumerated in `final-source-preservation.json`; original instrumented/batched versions and diffs are preserved. Additional diagnostic helpers: `WriterTiming.cs`, `WriterBench.cs`, `WriterFaults.cs`, `bench.ps1`, `focused.ps1`, `identity_worker.py`, `identity_launch.ps1`. `timed_monitor.ps1` only loads the timing dependency in this fresh diagnostic copy; its lifecycle/heartbeat semantics are unchanged. The mixed-clock fix applies only to the newly added identity_worker.

52–54. **Protection/history:** protected VM/configuration NOT ACCESSED; production JARVIS UNCHANGED. Historical delay causes UNCONFIRMED. The original 13.7/14.084/14.565/17.195-second events are not explained by this new mixed-clock driver failure. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

55. **Next proposed gate:** review the proven synchronous durability service deficit and the missing independent CIM subject discriminator. A bounded durability/finalization pipeline may move flush off ingestion, but cannot by itself prove sufficient sustained durable throughput; quantify that service rate and finalization bound before adopting it. Do not merely enlarge the queue or defer unlimited flush work. Decide an independently provable process-event identity protocol before a new integrated run. No medium, large, or protected baseline run is eligible.

56. **Final status: BOTH_BOUNDARIES_STILL_DEFECTIVE.**

## Rollback

Nothing was promoted. Keep the fresh D: diagnostic copy unaccepted and do not use its legacy launchers. Continue to reference immutable prior candidates. The original writer, prior instrumentation and batch experiment diff are retained, so rollback does not require editing any historical evidence. No production rollback is necessary. No files were deleted.

## Preserved transitional failures and limitations

The new preflight initially miscounted the embedded manifest (261 payloads + manifest = 262); corrected with exact embedded/external manifest comparison. One restricted-context CIM preflight received Access denied and left an exclusive empty evidence reservation; a fresh host-context preflight passed. One preparation command had quoting SyntaxError before any edit/test launch; standalone preparation fixed it. The new identity driver clock mismatch and all six failed writer trials remain preserved. Diagnostic timing perturbs the writer; quantiles are estimates and neither single passing trial establishes a worst-case bound. Resource/driver causation was not inferred from these measurements.

## Primary-source basis

- [CIM process START schema and TIME_CREATED semantics](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/krnlprov/win32-processstarttrace).
- [CIM process STOP schema](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/krnlprov/win32-processstoptrace).
- [Microsoft: process-object handles retain the PID until the object can be destroyed](https://devblogs.microsoft.com/oldnewthing/20110107-00/?p=11803).
- [ETW ProcessStartKey versus EventKey](https://learn.microsoft.com/en-us/windows/win32/api/evntrace/ns-evntrace-enable_trace_parameters).

These references support the documented semantics; measured provider schemas, delays and timing values are supplied by the local preserved runs. No source states that current CIM TIME_CREATED equals process creation or carries a kernel process-instance key.
