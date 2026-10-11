# Stage 6 — application identity and trace capacity review

**BLOCKED.** No large synthetic run is eligible. No candidate, matcher, observer, collector, threshold, queue or production source was changed.

The preserved medium run remains failed. Of its 22 unresolved application notifications, **0 are uniquely reconciled, 21 remain AMBIGUOUS, and 1 is UNMATCHED**. A capacity audit also finds that the application's 20,000-row tap limit is below the conservative projection. Neither a complete successful large-run capacity bound nor a deterministic correction to the missing notification identity has been established. Under the request's stop conditions, fresh identity stress and medium acceptance were not launched. This is a review boundary, not a passing disposition for those requirements.

## Evidence preservation and exact scope

Frozen candidate: `D:\JARVIS-STAGE6-LIVE\f469b94b665e4808af1c5bb6aa46b207\code`.

Preserved medium run: `D:\JARVIS-STAGE6-LIVE\f469b94b665e4808af1c5bb6aa46b207\code\protected-00a17b2c499c4966a5113c30924b367a`.

`freeze.json` records 116 candidate hashes and 383 medium evidence files with hashes, sizes and modification times. All 48 segments match the original manifest. All 1,078 members of the previous canonical archive were reverified, including its embedded manifest. Its ZIP SHA-256 remains `676d418f32aca30787c0a771b2cbf357bd29f97e45b9f3d4677f43970261f74e`. `final-preservation.json` confirms candidate and medium evidence unchanged after this inspection. No historical failure was overwritten.

New files are analysis scripts, offline adversarial fixture copies, test results and this report under this report directory, plus small sacrificial sink files under `D:\JARVIS-STAGE6-LIVE\capacity-forensics-958f65035f3d4a9782ba69925dbc6eaf`. No accepted application source changed. No elevated observer/UAC launch occurred. Initial sandbox CIM access was denied; the read-only host-context query succeeded with zero matches. Final host receipt again reports zero matching diagnostics/VirtualBox processes and zero diagnostic trace sessions.

## 1–8. Identity findings

The complete deterministic 22-event table is in **EVENTS.md**. **events-22.json** includes every raw event, callback/enqueue tap record, persistence receipt, competing full kernel lifecycle row, matching retained-handle record, native evidence where present, and all captured same-PID/parent-PID identities. Unknown fields are explicitly marked; raw historical streams are unchanged.

All 21 ambiguous events are STOP notifications with `parentPid=0`. Multiple kernel instances share the notification PID and basename. Every candidate has its own creation FILETIME and kernel process sequence. Matching kernel exits and retained handles establish individual process termination; they do **not** supply a creation identity absent from the CIM notification. These OS-created console helpers are not direct owned-child PE-debug targets. Missing PE entry for such a helper is not replaced with a Python marker.

Event 22 is START, queue 1155, PID 15988, parent 14172, notification FILETIME 134344258554456464. The sole captured kernel instance for PID 15988 has creation 134344258378580171, sequence 37872 and parent PID 21484 / parent sequence 37871. No captured kernel row has PID 14172. The START cannot be attached to that earlier process with a different parent. Because kernel lifecycle capture is scoped to the launcher tree, absence from its rows is not proof that the notification was unrelated. Its relationship remains unknown; it is not silently discarded.

Canonical identity for this run is **run/session + PID + process creation FILETIME + kernel process sequence**, corroborated by normalized image identity and retained-handle creation/exit where available. Parent linkage additionally requires the **parent process sequence**, not just parent PID.

| Source | Actual identity / limitations |
|---|---|
| Kernel lifecycle | PID, CreateTime, ProcessSequenceNumber, ParentProcessSequenceNumber, image, start/exit QPC and exit FILETIME. |
| Native PE | Owned-child PID + GetProcessTimes creation FILETIME; PE-entry QPC, thread/debug events and exit. Joined to exact kernel identity. |
| Retained handle | Handle kept for the process lifetime, verified creation FILETIME/image/exit. Numeric handle values are local to their owning process and are not global identity keys. |
| Application CIM | PID, basename, parent PID, event-generation FILETIME; **no process creation/sequence identity**. STOP parent is zero in these 21 cases. |
| Queue | Reference plus monotonic queue sequence within the observer run. External EventIdentifier may collide. Queue identity identifies a notification, not a process instance. |
| Checker | First forms exact kernel/handle lineage; notification association still rejects multiple candidates; whole cleanup gate fails on unresolved application lineage. |

Strict correlation hierarchy: validate run/source and kernel lifecycle; require exact PID and available creation/sequence identity; reject conflicting parent/image/lifetime evidence; check native/handle corroboration; then require exactly one supported notification candidate. Notification delay has no established upper bound here. Do not turn notification time into process time, bind to the nearest exit, consume earlier candidates greedily, assume exactly-once delivery as a new guarantee, or use one-use pairing to manufacture uniqueness.

**Mechanism supported:** PID_REUSE + APPLICATION_EVENT_MISSING_CREATION_IDENTITY, with absent STOP parent discrimination. **Not established:** a clock conversion defect, parent-PID reuse for event 22, notification duplication, a specific buffering cause, or loss of the 21 STOP records. All their records exist. Event 22 is unmatched, not proven outside the run.

**Correction: none.** No deterministic correlation change can recover a missing instance identity from these records. The correction portion is INCONCLUSIVE. A future evidence-acquisition design must establish an independent instance discriminator and prove compatibility with short-lived console helpers before changing the gate. This report does not authorize weakening or replacing independent application evidence.

## 3. Clock audit

| Field | Units and meaning | Ordering / uncertainty |
|---|---|---|
| CIM TIME_CREATED / `nativeTime` | UTC FILETIME, 100 ns units since 1601; event-generation time | Not process creation/exit. Unit resolution is not delivery accuracy. Maximum delay unmeasured. |
| ETW start/stop QPC | Raw QPC; ClientContext=1 and RAW_TIMESTAMP enabled | Same-machine frequency recorded as 10,000,000 ticks/sec. Event time differs from callback time. |
| Kernel/handle creation and exit | GetProcessTimes / kernel FILETIME, integer 100 ns units | Compared as integers; no local-time conversion or floating-point subtraction used for identities. |
| Native entry, app tap, receipts | QueryPerformanceCounter / Stopwatch ticks | Converted by recorded frequency. Cross-thread near-equality does not prove causal order. |
| `receivedQpc` | **Exact queue enqueue QPC**, despite its name | It is not the independent A-callback marker. The latter is in app-tap.json. |
| `drainedQpc` / `persistedQpc` | Metadata assembly / completed append-and-remove receipt | Neither is the source process exit time; append receipt alone is not the later durable-finalization proof. |
| Python `perf_counter_ns`, state `qpc` | Nanoseconds; divide by 1e9 | State field name `qpc` is misleading: do not divide it by native QPC frequency. |

QPC conversion here is 100 ns per tick; Python nanosecond values retain their own unit. No calibrated wall-clock-to-QPC error bound is present, so cross-clock proximity is not used to disambiguate. No conversion change was justified. Microsoft's [Win32_ProcessTrace documentation](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/krnlprov/win32-processtrace) describes TIME_CREATED as event-generation UTC time, not the process creation field. [QPC guidance](https://learn.microsoft.com/en-us/windows/win32/sysinfo/acquiring-high-resolution-time-stamps) distinguishes interval timing from UTC and cautions about cross-thread ordering uncertainty.

## 9–10. Identity validation

**20/20 offline identity regression categories passed.** These exercise PID/parent reuse, delayed and out-of-order notifications, equal identities, native evidence present/missing, retained/post-exit evidence, zero/one/two candidates, invalid lifetimes, unit conversion, creation mismatch, fail-closed ambiguity and the previously passing real-evidence fixture. Native tests operate on copies; segment integrity is independently verified, not represented as a fresh runtime test.

The first test attempt passed 10 cases then failed an assertion because its mutation selected an out-of-scope kernel row. The checker correctly ignored that row for collector acceptance. The new test was corrected to mutate exact in-scope sequence 37288. Its original script, fixture copies and failure explanation are preserved. This was not a matcher defect.

**Fresh identity stress: NOT RUN.** Existing medium evidence contains 563 kernel rows, 518 distinct PIDs and 45 additional process incarnations; 560 collector-tree identities have kernel exits. This historical evidence informs diagnosis, not fresh acceptance. A new campaign would not create discriminating fields in the already preserved events. The full-pipeline capacity stop condition below also prevents launching a new acceptance run.

## 11–18. Measured medium trace capacity

| Measurement | Result |
|---|---:|
| Trace event coverage | 106.6088296 s |
| Tracer ready → launcher final shutdown | 132.0938415 s |
| Prepared → observers closed | 135.3406972 s |
| Workload duration, including 90 s hold | 90.9390195 s |
| Records | 1,255,158 |
| Mean rate over trace event coverage | 11,773.4901/s |
| Exact rolling 1 s peak | 97,212 records / 97,212/s |
| Exact rolling 5 s peak | 145,611 records / 29,122.2/s |
| Exact rolling 10 s peak | 203,855 records / 20,385.5/s |
| Exact rolling 60 s peak | 849,156 records / 14,152.6/s |
| Segments | 48 |
| Total segment bytes | 398,028,029 |
| Bytes/record min / mean / max | 226 / 317.1138845 / 632 |
| Mean segments per event-coverage second | 0.4502441 |
| Maximum measured writer flush/close interval | 0.641417 s |
| Peak pending queue payload | 8,240,334 bytes |

Rolling windows use sorted QPC and half-open `[t,t+duration)` intervals. The earlier 97,026 value used fixed buckets; it is not the exact rolling peak. Segment filesystem modification times provide observed spacing, not exact CreateFile timestamps. Exact per-segment bytes, hashes, record counts and event intervals are in capacity-measurement.json; minimum observed modification spacing is 0.407469 s, maximum 17.1640669 s (including final tail close).

Provider counts: file **361,393**; scheduler **354,841**; registry_classic **310,955**; registry **198,597**; process **29,372**. At the 1-second peak, file contributes **84,304/97,212** records; scheduler 4,927; registry_classic 4,622; registry 2,933; process 426. Every trace process is counted by PID plus creation identity in capacity-measurement.json, not by PID alone.

## 19–26. Duration, projections and reserve

No new large hashing was performed. Existing calibration SHA-256 is `8876f2fe62b3e4cf23f22289bf9f318acf1f8159da62d4912cec3d1a9f268753`. Two 59,665,402,098-byte passes took 262.4176685 and 261.0306052 s: total **523.4482737 s**. The slower-pass rate is **227,368,082.49 bytes/s**; two slower passes project **524.835337 s**. These are cached logical reads, not a guaranteed physical-disk rate.

The previously selected 788-second synthetic observation hold is a minimum total worker observation duration, not an additional 788 seconds after hashing. Adding measured medium startup/closure/work overhead gives an illustrative expected collection duration of **830.160855 s**. The existing 1,080-second campaign allowance plus observed startup/closure gives **1,121.221835 s**. The tracer loop limit is **1,200 s**. That limit is not proof that blocked filesystem APIs, consumer closure, finalization or archive operations finish within 1,200 seconds. Successful large finalization duration remains unmeasured.

| Conditional planning scenario | Records | Trace bytes |
|---|---:|---:|
| Expected measured mean × 830.160855 s | 9,773,891 | 3,099,436,542 |
| Conservative sustained rate × 1,121.221835 s | 16,632,784 | 10,511,919,488 |
| Observed rolling peak maintained for 1,200 s | 116,654,400 | 73,725,580,800 at 632 bytes/record |
| Above × observed peak variability factor | 138,474,218 | 87,515,705,776 |

Comparable rolling 1-second peaks are 81,894, 83,109 and 97,212. The numerical sensitivity factor **97,212 / 81,894 = 1.18704667** is evidence-derived. It is a **provisional empirical margin**, not an accepted guarantee for unseen load. The 1,200/830.16 duration ratio, peak/mean ratio, maximum measured record size and process-count projection are accounted for separately. The serializer permits records up to 8,192 bytes; 632 is merely the measured maximum. Do not present the 87.5 GB scenario as a mathematical upper bound on future trace bytes.

Existing trace hard caps are **196,531,200 records**, **137,438,953,472 bytes (128 GiB)** and **16,384 segments**. Exceeding any limit rejects evidence. The request did not justify an arbitrary increase, and none was made.

Additional evidence is separate from detailed trace records. Medium non-segment evidence occupies **22,385,596 bytes**; duration/variability projection is **299,105,588 bytes**. Medium has 280 native entries; linear 1,200-second projection is 3,152. Kernel identity projection is 6,338 against an 8,192-row limit. CIM has 1,158 events and **2,316 tap rows**; projections are 13,035 CIM events / **26,070 tap rows** at 1,200 seconds. The conservative-duration tap projection is **24,358**, already above **20,000**. This is a predicted capacity risk, not an observed overflow in the preserved medium run.

No universal count bound for unrelated host notifications or proven total byte quota for all auxiliary/finalization artifacts was established. The raw tap also observes host notifications outside the filtered kernel tree. Raising only segmented trace capacity would leave this gap.

Conditional live evidence plus one uncompressed-size archive allowance is **175,656,446,259 bytes**. Another simultaneous archive copy would add approximately **87,814,811,364 bytes**. Independently, two full trace hard caps alone require **274,877,906,944 bytes**, before auxiliary evidence. D: had **1,795,658,928,128 bytes free** at final inspection. Space is ample for these scenarios, but **a complete safe reservation is NOT VALIDATED**: auxiliary bounds, archive/temporary overhead and successful close/finalization behavior still need qualification. No large allocation or duplicate dataset was created.

## 27–29. Segmentation and capacity tests

Source audit: trace_sink.hpp uses a single writer, 8 MiB segments, monotonic names, CREATE_NEW, SHA-256 per segment, WriteFile/FlushFileBuffers/CloseHandle before successful segment completion, a manifest and independent ETW loss checks. There is a **64 MiB pending payload queue before segmentation**, plus the writer's segment buffer and container overhead. Overflow is a failure, not silent rotation. That payload limit is not a total process-RSS limit. Synchronous writer flush/close may still block; the observed 0.641417 s does not prove a universal I/O bound. Thread/IRP bookkeeping and auxiliary telemetry also require their own bounds rather than assuming the segment queue bounds everything.

**30/30 small sacrificial capacity assertions passed**, using the exact hash-verified existing J6SinkTest.exe and preserved reduced-budget fixtures. Covered near/exact reduced limits, overflow, rapid small-segment rollover, output failure, simulated disk full, segment-create failure, byte cap, missing/corrupt segment, wrong hash, omitted/duplicate manifest segment, explicit trace fault, nonzero ETW loss and no overwrite. Actual reduced-budget helper processes were waited through retained handles; identities and closure are recorded per case. The no-overwrite helper exited normally with a failing test outcome as expected.

These checks do **not** constitute measured 97,212/s producer stress or near the actual multi-gigabyte conservative capacity. Those two capacity qualifications, fresh identity stress and medium rerun are **NOT RUN** after the safe-complete-capacity stop condition. No candidate correction was justified/applied to trigger medium reacceptance. No passing runtime result is inferred from offline tests.

## 30–39. Final disposition

| Required report item | Disposition |
|---|---|
| 30 Maximum heartbeat | Preserved medium 1.1429359 s; no fresh monitor run. |
| 31 ETW loss | Preserved medium 0; earlier 177,509-loss run remains archived as failed. |
| 32 Identity ambiguity | 21 AMBIGUOUS + 1 UNMATCHED; 0 uniquely resolved. |
| 33 Cleanup | Final host query: 0 matching diagnostic/VirtualBox processes, 0 diagnostic trace sessions. No termination performed. |
| 34 Archive | Previous 1,078 members reverified. New archive result is recorded separately in archive-verification.json; no success claimed until that receipt exists. |
| 35 Protected VM access | None. Protected files/configuration were not opened or hashed. |
| 36 Production change | None by this work. No production operation performed. |
| 37 Historical causes | UNCONFIRMED. No finding here explains historical probe/sampler/storage delays. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED. |
| 38 Large synthetic eligibility | NOT ELIGIBLE; no 59.7 GB run or protected-baseline procedure executed. |
| 39 Final status | **BLOCKED** — missing notification-instance evidence and incomplete full-pipeline capacity qualification. |

## Minimum next review and rollback

Review a bounded independent notification-instance evidence acquisition mechanism, including OS-created console helpers and out-of-scope PID reuse. Do not implement nearest-time matching or weaken the independent evidence requirement. Separately define a complete collector/observer capacity contract covering tap rows, process counts, all live evidence and finalization storage; then justify any narrowly bounded diagnostic capacity correction from that contract. Existing source remains frozen pending this review.

After a justified correction: run the requested identity stress; actual near-peak and bounded-capacity qualification; then a fresh medium run with complete native/application/kernel lifecycle, loss checks, unchanged heartbeat/deadlines, finalization and archive. Only after these pass should the large synthetic procedure be proposed for owner review. No large-run procedure is approved by this report.

Rollback is unnecessary for the frozen candidate because it was not modified. New analysis/tests are isolated additions; retain them as evidence. Do not remove prior failure archives or any synthetic dataset. Analysis-only development errors (archive member bookkeeping, out-of-scope test selection, historical trace format and helper import arguments) are preserved in their named error records; none modified historical evidence or runtime behavior.

Commands executed are reproducible from the new scripts: `python -B analyze.py freeze`, `identity`, `capacity`; `python -B identity_regressions.py`; `python -B capacity_faults.py`; `python -B capacity_plan.py`. The exact interpreter was `C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`. Existing outputs deliberately use exclusive/fresh paths; do not overwrite this report by rerunning scripts in place.
