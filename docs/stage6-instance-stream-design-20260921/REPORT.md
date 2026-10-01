# Stage 6 — independent instance identity and observer capacity

Status: **BLOCKED**

Design and focused sacrificial validation only. This is not a collector acceptance or a large-run authorization.

## Mandatory 48-item findings

1. **Current 22-event classification.** 0 UNIQUE_MATCH; 21 AMBIGUOUS; 1 UNMATCHED. Per-event candidates and missing discriminators are preserved below and in historical-22-reassessment.json.

2. **Canonical process-instance identity.** Proposed strict composite: run/boot scope + subject PID + kernel CreateTime + kernel ProcessSequenceNumber; exact parent sequence for lineage. Retained-handle creation/exit and owned native PE entry corroborate it. NOT yet proven across the independent CIM source.

3. **Independent identity source/API.** GetProcessTimes through retained process handles; supported SystemBasicProcessInformation snapshot SequenceNumber tested on this Windows build. Eight stable, distinct snapshot sequences. ETW extended ProcessStartKey is documented but not newly captured or equated with payload sequence. No single demonstrated discriminator exists across every mandatory source.

4. **Retained-handle correlation.** 64 actual concurrent/short native probes: 64 stable creation identities, 64 after-exit handle matches, 64 signaled exits and closed handles. Eight additional sequence probes also exited and closed their handles. Fresh kernel/CIM/PE cross-source correlation NOT RUN.

5. **Timestamp normalization.** Creation/exit FILETIME and CIM TIME_CREATED are unsigned UTC 100-ns values, but TIME_CREATED denotes event generation, not process creation. QPC values require the recorded frequency/run anchor; keep integer ticks and use differences within the same clock. Python perf_counter_ns is not raw QPC ticks. Callback, enqueue, persistence and event-generation clocks are distinct. Do not join by rounded timestamps or proximity.

6. **PID-reuse behavior.** Canonical identity never uses PID alone. Late OpenProcess must match creation identity from the original handle. No actual PID reuse occurred in the 64-probe sample; parent PID reuse and reordered/delayed application delivery remain unvalidated.

7. **Identity stress results.** 64 owned native probes in batches of eight; plus eight suspended/resumed sequence-query probes. Identical images, concurrency, short lifetimes and after-exit handle queries covered. Full required ETW/native/CIM identity stress NOT RUN; supported query success does not close it.

8. **False unique matches.** 0 observed within the limited fresh handle/snapshot checks; 0 historical events force-matched. This is not evidence of zero false matches in an unrun integrated PID-reuse stress.

9. **Application tap role.** Current tap is acceptance-critical observer evidence, NOT merely a UI view. Proposed bounded secondary view must follow complete authoritative capture. No required CIM evidence has been downgraded.

10. **Exact 20,000-row limitation.** Frozen EventTap.cs Add increments sequence, then increments Overflow and returns when sequence > 20000. New rows are discarded; earlier rows remain. Raw application evidence can continue elsewhere, but callback/enqueue proof is missing and timed_monitor/checker fail. Observer-side in-memory evidence cap; not database pagination. The 97,212/s figure is the detailed trace stream, not a measured CIM application-event rate.

11. **Authoritative capture architecture.** Design: all mandatory source records -> bounded admission queue -> append-only D: segments -> SHA-256/sequence manifest -> final run manifest -> optional bounded query view. Prototype validates one generated stream only. Current observer, checker and all-channel quotas are NOT migrated.

12. **Segmentation strategy.** CREATE_NEW, deterministic segment numbering, no overwrite or destructive rotation; preserve failed prefixes and a sticky failure. 8 MiB segments; maximum record size/budget enforced. All-channel memory overhead and finalization duration are not yet bounded by this standalone prototype.

13. **Continuity mechanism.** Global sequence assigned at admission under the queue lock, attempted/admitted/persisted totals, segment first/last/count/hash. Complete manifest must have ordered contiguous segments, no duplicate/gap/partial record, and sum(counts)=persisted=admitted=attempted with fault=0.

14. **Backpressure behavior.** 64 MiB payload queue; exhaustion fails closed. Larger-record capacity test filled it at 67,108,335 bytes and failed. 296,533 admitted versus 193,448 persisted: 103,085 admitted records absent from persisted prefix, explicitly invalidating the run. No retry or queue increase. Partial evidence remains, never complete.

15. **Trace-loss detection.** Require source/ETW loss counters, queue overflow and attempted/admitted/persisted reconciliation, writer/hash/flush/create faults, continuity, segment bytes/hashes and archive membership. Generated capacity tests cannot measure ETW loss. Frozen ETW and application counters remain required.

16. **Total medium-run records.** Preserved run: 1,255,158 records; 398,028,029 bytes, 48 segments. Reanalysis only; not current medium acceptance.

17. **Average record rate.** 11773.490101/s. Rolling 5-second: 145,611 total / 29,122.2 per second; 10-second: 203,855 / 20,385.5; 60-second: 849,156 / 14,152.6.

18. **Peak record rate.** 97,212/s in a rolling second, 32,830,208 bytes in that window; peak/mean 8.256855. Not assumed sustainable across an entire large run.

19. **Provider/category breakdown.** File 361,393; scheduler 354,841; classic registry 310,955; registry 198,597; process 29,372. Peak second file 84,304 dominates. Lifecycle/entry/handle/CIM/queue/health/hash/finalization are REQUIRED_FOR_ACCEPTANCE; current file/image/registry/thread/scheduling detail REQUIRED_FOR_FORENSICS. Optional presentation views only are secondary. No source category removed.

20. **Mean/max record size.** Mean 317.113884 bytes; median 307; p95 424; p99 473; max 632. Peak-window mean 337.717648. Preserved compression ratio 11.659967:1; not used to reduce reserve. New sequence fields add bytes, so old sizes are not a hard future bound.

21. **Measured hashing throughput.** Prior synthetic calibration: 59,665,402,098 bytes/pass; pass1 262.4176685s; pass2 261.0306052s; conservative observed 227,368,082.49 bytes/s. Cached logical reads may contribute. No fresh large hashing performed.

22. **Expected 59.7 GB run duration.** Illustrative 830.1608547s, from preserved calibration and existing hold/medium overhead model. Measured two-pass sum 523.4482737s. Successful large inventory-only/finalization/archival timings are not independently available; no invented durations.

23. **Conservative duration.** Illustrative 1121.2218352s. Existing 1200s collection-loop limit is not a proven bound on blocked system calls, flush, cleanup or archive. Full end-to-end upper bound UNVALIDATED.

24. **Expected trace count.** Average-rate model 9,773,891; sustained 60-second rate plus observed burst allowance model 11,831,994. Assumptions are explicit; these are projections, not captured records.

25. **Conservative trace count.** 15,951,264 using illustrative conservative duration and 83,059.4-record excess-burst allowance. Burst recurrence is not measured.

26. **Upper-bound trace count.** 17,066,180 is an empirical 1200s envelope, NOT a proven bound. Existing configured hard trace record limit 196,531,200 is a fail-closed resource ceiling, not predicted demand. Complete all-channel upper bound UNVALIDATED.

27. **Safety factor.** Observed peak variation 97,212 / 81,894 = 1.18704667; peak/mean 8.256855; conservative/expected duration approximately 1.3506. None proves a sufficient combined safety margin. Larger-record writer failure and unmeasured burst recurrence/process-count uncertainty prevent accepting a numerical global factor.

28. **Segment size.** Prototype retains 8,388,608 bytes. At observed peak bytes/sec approximately 0.256s/segment. Representative test 21 segments; maximum aggregate segment write/flush/close timing 0.394447s. Hash/rollover costs not independently instrumented. Selection remains provisional for full integration.

29. **Expected segment count.** Using old mean bytes: expected 448; conservative 604; empirical 1200s 646. Excludes new fields and other channels. Proposed hard shared maximum 16,384.

30. **Projected trace storage.** Old-mean projections: expected 3,752,089,579 bytes; conservative 5,058,367,290; empirical 1200s 5,411,922,633. Not a complete observer storage guarantee.

31. **Required D: reserve.** Proposed finite all-channel architecture: REQUIRED_RESERVE = 274,977,986,470 bytes. Includes 128 GiB shared authoritative quota, capped metadata/control, uncompressed final archive, temporary final manifest, 4-KiB allocation slack; streaming archive verification needs no second extracted copy. CONDITIONAL DESIGN ONLY; current collector does not enforce this shared quota.

32. **D: headroom.** At measurement: CURRENT_FREE = 1,795,214,123,008; proposed HEADROOM = 1,520,236,136,538 bytes. Actual cluster size 4096. Sufficient space alone cannot prove bounded capture.

33. **High-rate capacity test.** PASS representative-size case: 500,000 records, 169,388,895 bytes, 100,080 records/sec, producer 4.99598s, complete 5.13086s, 21 verified segments, queue high-water 13,209,813 bytes, no fault. Separate larger-record case FAIL at queue exhaustion, offered 124,985 records/sec; failure preserved. Both generated CAPACITY ONLY, no process evidence synthesized.

34. **Overflow/failure test.** 38/38 focused assertions PASS: slow writer/queue exhaustion, create/write/hash/full simulations, record/byte ceilings, corrupt/missing/duplicate segments, sequence gap/duplicate/reorder and partial record. A 500ms writer delay is controlled fault injection, not a deadline change. Real full-volume exhaustion not attempted.

35. **Application-tap decoupling test.** Standalone generated-stream PASS: 25,000 and 500,000 authoritative records despite bounded view of 20,000, truncation explicitly recorded. Actual frozen acceptance still depends on EventTap. Per Phase23: BLOCKED. This demonstration is not actual observer decoupling.

36. **Medium combined validation.** NOT RUN: actual tap integration and independent application instance identity remain unresolved. No elevated observers started in this pass; do not treat historical medium evidence as current acceptance.

37. **Heartbeat maximum.** Historical medium 1.1429359s only. No new integrated monitor heartbeat measurement; standalone capacity/handle tests are not heartbeat acceptance. Unchanged 10-second threshold.

38. **ETW loss.** Historical medium 0. Fresh ETW capture NOT RUN. Earlier loss/failed captures remain in immutable historical archives.

39. **Sequence-gap count.** Representative 500,000-record stream: 0; all hashes/sequence boundaries verified. Deliberate malformed cases rejected. Larger-record failed stream is incomplete by 103,085 admitted records, not relabelled lossless.

40. **Cleanup result.** Every owned benchmark/probe used retained-handle exit checks and closed handles. Final host enumeration: 0 matching diagnostic processes, 0 diagnostic trace sessions. No termination of unrelated processes. Final observation is separate corroboration, not substitute for retained-handle proof.

41. **Archive verification.** Historical archives reverified: 1078 and 155 members. New report/prototypes/results, including failed capacity prefix, are archived with a per-member SHA-256 manifest; final archive-verification.json records exact new member count, archive hash and canonical path. That receipt is outside the archive to avoid self-reference.

42. **Source-hash result.** 116 frozen candidate hashes and six prior evidence/source hashes unchanged. Nine new D: prototype artifacts hash-recorded; old sink SHA-256 02d7b459e2da6e7998ebff0fdf8d76c7e6e339774ffee6d7e4c84fca25fb8b36; copied prototype sink 64592f17d526f1bfd82a1bd598420552cb2835ce3becbd1f12b9c85207ba28bd. No frozen application/runtime changes.

43. **Protected VM access result.** NOT ACCESSED. No protected hashing/config reads, VM operations, or snapshot changes. This is an operation-scope statement, not a newly acquired protected-file integrity proof.

44. **Production-change result.** UNCHANGED by this work. No production launch, code/configuration changes, provider calls, credentials, installation or security-setting changes.

45. **Historical ambiguity statement.** Historical 0 unique / 21 ambiguous / 1 unmatched remains failed/ambiguous. Missing historical process-instance fields cannot be reconstructed by a new query or later success.

46. **Historical cause statement.** Historical Stage 6 probe/sampler/startup delay causes remain UNCONFIRMED. Current queue exhaustion is established for the new larger-record capacity test only; underlying Windows/storage/driver cause not established. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

47. **Large-run eligibility.** NOT ELIGIBLE. Required future source-independent identity stress, actual tap decoupling, complete enforceable observer capacity bound, justified safety margin and medium combined validation are not satisfied. No 59.7GB or protected run performed.

48. **Final status.** BLOCKED — Phase23 actual acceptance still depends on the capped tap; identity and complete capacity proof also remain open.

## Identity source matrix and supported API constraints

| Source | Available instance evidence | Missing or restricted evidence |
|---|---|---|
| Kernel subject START/EXIT | Subject PID, CreateTime, ProcessSequenceNumber, parent sequence, image; ETW QPC | Extended header key not captured; emitter identity must not be confused with payload subject |
| Native owned PE tracer | Owned child PID + creation FILETIME, PE-entry QPC, exit; parent launcher identity | Not automatically a helper/conhost PE identity |
| Retained Windows handle | GetProcessId, GetProcessTimes creation/exit, QueryFullProcessImageName, wait signal/exit code | Numeric handle is local, not a portable instance key; no application events synthesized |
| CIM START/STOP | PID/name, parent PID where present, event generation TIME_CREATED; callback/enqueue QPC separately | No subject CreateTime or sequence; STOP parent may be zero; cannot resolve every reuse case |
| Supported process snapshot | PID, parent PID, SequenceNumber, image name | Only current snapshot; not history; sequence equivalence to ETW NOT established |
| Cleanup checker | Requires verified creation/sequence/lineage plus exit proof | Name/PID absence alone insufficient; ambiguity remains fatal |

The supported SystemBasicProcessInformation query was tested on Windows 10.0.26200.0 (UBR9457); SDK information class252 and public structure were inspected. Two snapshots per owned suspended process returned stable sequences for eight distinct instances. No administrator privilege was required for these owned-process checks. Suspension makes these fixtures unsuitable for measuring natural startup latency. Version/capability rejection must remain fail closed. ETW collection elevation was not exercised here.

Primary references: [process handles](https://learn.microsoft.com/en-us/windows/win32/procthread/process-handles-and-identifiers), [documented snapshot API](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntquerysysteminformation), [ETW enable properties](https://learn.microsoft.com/en-us/windows/win32/api/evntrace/ns-evntrace-enable_trace_parameters), [CIM START schema](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/krnlprov/win32-processstarttrace), [QPC clock guidance](https://learn.microsoft.com/en-us/windows/win32/sysinfo/acquiring-high-resolution-time-stamps). A second ETW subscription is a separate transport, not an independent event source.

## All original 22 events

- Event 1: **AMBIGUOUS**. Notification has no creation/sequence identity. Independent exits prove processes ended, not which notification belongs to which reused PID. Candidates: `[{"pid":7020,"created":"134344257633281784","sequence":"37405","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37404"},{"pid":7020,"created":"134344257815300996","sequence":"37522","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37521"}]`. New snapshot/extended keys were not captured historically.
- Event 2: **AMBIGUOUS**. Notification has no creation/sequence identity. Independent exits prove processes ended, not which notification belongs to which reused PID. Candidates: `[{"pid":10356,"created":"134344257736528052","sequence":"37471","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37470"},{"pid":10356,"created":"134344257919754132","sequence":"37586","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37585"}]`. New snapshot/extended keys were not captured historically.
- Event 3: **AMBIGUOUS**. Notification has no creation/sequence identity. Independent exits prove processes ended, not which notification belongs to which reused PID. Candidates: `[{"pid":520,"created":"134344257756499817","sequence":"37483","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37482"},{"pid":520,"created":"134344257936429755","sequence":"37596","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37595"}]`. New snapshot/extended keys were not captured historically.
- Event 4: **AMBIGUOUS**. Notification has no creation/sequence identity. Independent exits prove processes ended, not which notification belongs to which reused PID. Candidates: `[{"pid":14128,"created":"134344257609973936","sequence":"37391","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37390"},{"pid":14128,"created":"134344257969900738","sequence":"37616","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37615"}]`. New snapshot/extended keys were not captured historically.
- Event 5: **AMBIGUOUS**. Notification has no creation/sequence identity. Independent exits prove processes ended, not which notification belongs to which reused PID. Candidates: `[{"pid":18660,"created":"134344257706543566","sequence":"37453","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37452"},{"pid":18660,"created":"134344258054271430","sequence":"37668","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37667"}]`. New snapshot/extended keys were not captured historically.
- Event 6: **AMBIGUOUS**. Notification has no creation/sequence identity. Independent exits prove processes ended, not which notification belongs to which reused PID. Candidates: `[{"pid":17112,"created":"134344257835272896","sequence":"37534","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37533"},{"pid":17112,"created":"134344258144681579","sequence":"37730","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37729"}]`. New snapshot/extended keys were not captured historically.
- Event 7: **AMBIGUOUS**. Notification has no creation/sequence identity. Independent exits prove processes ended, not which notification belongs to which reused PID. Candidates: `[{"pid":18404,"created":"134344257892046561","sequence":"37568","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37567"},{"pid":18404,"created":"134344258191682092","sequence":"37758","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37757"}]`. New snapshot/extended keys were not captured historically.
- Event 8: **AMBIGUOUS**. Notification has no creation/sequence identity. Independent exits prove processes ended, not which notification belongs to which reused PID. Candidates: `[{"pid":4156,"created":"134344258060974664","sequence":"37672","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37671"},{"pid":4156,"created":"134344258198376947","sequence":"37762","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37761"}]`. New snapshot/extended keys were not captured historically.
- Event 9: **AMBIGUOUS**. Notification has no creation/sequence identity. Independent exits prove processes ended, not which notification belongs to which reused PID. Candidates: `[{"pid":13648,"created":"134344258077682958","sequence":"37685","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37684"},{"pid":13648,"created":"134344258215202733","sequence":"37774","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37773"}]`. New snapshot/extended keys were not captured historically.
- Event 10: **AMBIGUOUS**. Notification has no creation/sequence identity. Independent exits prove processes ended, not which notification belongs to which reused PID. Candidates: `[{"pid":19800,"created":"134344257798535946","sequence":"37510","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37509"},{"pid":19800,"created":"134344258262259635","sequence":"37802","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37801"}]`. New snapshot/extended keys were not captured historically.
- Event 11: **AMBIGUOUS**. Notification has no creation/sequence identity. Independent exits prove processes ended, not which notification belongs to which reused PID. Candidates: `[{"pid":19032,"created":"134344258131323778","sequence":"37722","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37721"},{"pid":19032,"created":"134344258279009462","sequence":"37812","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37811"}]`. New snapshot/extended keys were not captured historically.
- Event 12: **AMBIGUOUS**. Notification has no creation/sequence identity. Independent exits prove processes ended, not which notification belongs to which reused PID. Candidates: `[{"pid":10752,"created":"134344258151495272","sequence":"37734","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37733"},{"pid":10752,"created":"134344258297691093","sequence":"37822","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37821"}]`. New snapshot/extended keys were not captured historically.
- Event 13: **AMBIGUOUS**. Notification has no creation/sequence identity. Independent exits prove processes ended, not which notification belongs to which reused PID. Candidates: `[{"pid":2376,"created":"134344257868689941","sequence":"37554","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37553"},{"pid":2376,"created":"134344258311140168","sequence":"37830","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37829"}]`. New snapshot/extended keys were not captured historically.
- Event 14: **AMBIGUOUS**. Notification has no creation/sequence identity. Independent exits prove processes ended, not which notification belongs to which reused PID. Candidates: `[{"pid":11768,"created":"134344258047618048","sequence":"37664","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37663"},{"pid":11768,"created":"134344258324987559","sequence":"37840","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37839"}]`. New snapshot/extended keys were not captured historically.
- Event 15: **AMBIGUOUS**. Notification has no creation/sequence identity. Independent exits prove processes ended, not which notification belongs to which reused PID. Candidates: `[{"pid":13648,"created":"134344258077682958","sequence":"37685","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37684"},{"pid":13648,"created":"134344258215202733","sequence":"37774","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37773"},{"pid":13648,"created":"134344258355212240","sequence":"37858","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37857"}]`. New snapshot/extended keys were not captured historically.
- Event 16: **AMBIGUOUS**. Notification has no creation/sequence identity. Independent exits prove processes ended, not which notification belongs to which reused PID. Candidates: `[{"pid":15188,"created":"134344258225338277","sequence":"37780","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37779"},{"pid":15188,"created":"134344258365244089","sequence":"37864","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37863"}]`. New snapshot/extended keys were not captured historically.
- Event 17: **AMBIGUOUS**. Notification has no creation/sequence identity. Independent exits prove processes ended, not which notification belongs to which reused PID. Candidates: `[{"pid":17400,"created":"134344258289115775","sequence":"37818","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37817"},{"pid":17400,"created":"134344258421085722","sequence":"37898","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37897"}]`. New snapshot/extended keys were not captured historically.
- Event 18: **AMBIGUOUS**. Notification has no creation/sequence identity. Independent exits prove processes ended, not which notification belongs to which reused PID. Candidates: `[{"pid":15420,"created":"134344257872030083","sequence":"37556","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37555"},{"pid":15420,"created":"134344258452404256","sequence":"37918","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37917"}]`. New snapshot/extended keys were not captured historically.
- Event 19: **AMBIGUOUS**. Notification has no creation/sequence identity. Independent exits prove processes ended, not which notification belongs to which reused PID. Candidates: `[{"pid":10272,"created":"134344258328316159","sequence":"37842","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37841"},{"pid":10272,"created":"134344258469207665","sequence":"37928","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37927"}]`. New snapshot/extended keys were not captured historically.
- Event 20: **AMBIGUOUS**. Notification has no creation/sequence identity. Independent exits prove processes ended, not which notification belongs to which reused PID. Candidates: `[{"pid":18404,"created":"134344257892046561","sequence":"37568","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37567"},{"pid":18404,"created":"134344258191682092","sequence":"37758","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37757"},{"pid":18404,"created":"134344258472583176","sequence":"37930","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37929"}]`. New snapshot/extended keys were not captured historically.
- Event 21: **AMBIGUOUS**. Notification has no creation/sequence identity. Independent exits prove processes ended, not which notification belongs to which reused PID. Candidates: `[{"pid":15188,"created":"134344258225338277","sequence":"37780","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37779"},{"pid":15188,"created":"134344258365244089","sequence":"37864","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37863"},{"pid":15188,"created":"134344258502814164","sequence":"37948","image":"\\Device\\HarddiskVolume6\\Windows\\System32\\conhost.exe","parentSequence":"37947"}]`. New snapshot/extended keys were not captured historically.
- Event 22: **UNMATCHED**. No captured kernel identity meets notification PID/name/parent/time constraints. Parent/PID reuse makes relation possible but does not prove membership. Candidates: `[]`. New snapshot/extended keys were not captured historically.

## Exact changes, evidence and rollback

Frozen files were not edited. Only copied sacrificial sink/benchmark sources and generated artifacts changed. `sink-prototype.diff` records the exact sink delta; build scripts record compiler command lines. The nine prototype artifact hashes are:

- `D:\JARVIS-STAGE6-LIVE\instance-stream-62cd5dabd4cb46b593990f1fae4b2a28\code\J6Probe.exe` — `23240ef9f8b0a9a324110b1c2331de31dc1b0e08f5359cb707e51a939af56cd3`
- `D:\JARVIS-STAGE6-LIVE\instance-stream-62cd5dabd4cb46b593990f1fae4b2a28\code\J6StreamBench.exe` — `4a3edc5f699fe9409b197d8d6f8dae839c4764a84d4ab1e458a0ec6686df3f08`
- `D:\JARVIS-STAGE6-LIVE\instance-stream-62cd5dabd4cb46b593990f1fae4b2a28\code\stream_bench.cpp` — `33632acc8a47061d240397d65c8f28a183cec2c8f784d22b7f69d019e0c82539`
- `D:\JARVIS-STAGE6-LIVE\instance-stream-62cd5dabd4cb46b593990f1fae4b2a28\code\stream_bench.obj` — `4253b390c38f653a5f36ca7641290afb327266dd37c6caa8104a4fe07d6c0261`
- `D:\JARVIS-STAGE6-LIVE\instance-stream-62cd5dabd4cb46b593990f1fae4b2a28\code\trace_sink.hpp` — `64592f17d526f1bfd82a1bd598420552cb2835ce3becbd1f12b9c85207ba28bd`
- `D:\JARVIS-STAGE6-LIVE\instance-stream-62cd5dabd4cb46b593990f1fae4b2a28\representative-code\J6StreamBench.exe` — `4ce297e594cb1541bc9dab39b71fc48b08e44fda6ca59eb1692b7c4d683a3cd9`
- `D:\JARVIS-STAGE6-LIVE\instance-stream-62cd5dabd4cb46b593990f1fae4b2a28\representative-code\stream_bench.cpp` — `018403629bdbb766862207b2a4b0b9b17fbf79d8867edf7b0710bc26d0f2d3ec`
- `D:\JARVIS-STAGE6-LIVE\instance-stream-62cd5dabd4cb46b593990f1fae4b2a28\representative-code\stream_bench.obj` — `39dd98f075cf5191b7f31204283d5c5d2bdeb1bbf456ae2b8b390839f8420cb1`
- `D:\JARVIS-STAGE6-LIVE\instance-stream-62cd5dabd4cb46b593990f1fae4b2a28\representative-code\trace_sink.hpp` — `64592f17d526f1bfd82a1bd598420552cb2835ce3becbd1f12b9c85207ba28bd`

Evidence: [DESIGN.md](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-instance-stream-design-20260921/DESIGN.md), [freeze.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-instance-stream-design-20260921/freeze.json), [historical-22-reassessment.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-instance-stream-design-20260921/historical-22-reassessment.json), [handle-checks.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-instance-stream-design-20260921/handle-checks.json), [handle-summary.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-instance-stream-design-20260921/handle-summary.json), [sequence-probe.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-instance-stream-design-20260921/sequence-probe.json), [measurements.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-instance-stream-design-20260921/measurements.json), [stream-tests.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-instance-stream-design-20260921/stream-tests.json), [stream-fault-tests.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-instance-stream-design-20260921/stream-fault-tests.json), [representative-result.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-instance-stream-design-20260921/representative-result.json), [reconciliation.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-instance-stream-design-20260921/reconciliation.json), [final-host-state.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-instance-stream-design-20260921/final-host-state.json), [prototype-hashes.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-instance-stream-design-20260921/prototype-hashes.json), [sink-prototype.diff](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-instance-stream-design-20260921/sink-prototype.diff).

Rollback requires no production action: do not promote these prototypes. Continue to retain the unchanged frozen candidate and historical archives; preserve the new failed capacity run. Do not delete evidence to roll back. No commit, installation, VM change or threshold adjustment occurred.

## Exact next boundary

The supported handle/snapshot queries improve owned-process evidence but do not provide an absent instance discriminator inside delayed CIM notifications. No safe blanket association has been established. Review the remaining independent-source contract before replacing CIM evidence with a keyed ETW source; such a replacement must not be treated as already authorized.

A narrow actual tap-stream adapter would have to preserve every original callback/enqueue receipt in segmented authoritative storage and migrate checker reads to that storage, retaining the bounded view only downstream. The standalone prototype has not done this. The full capture must also enforce a shared finite quota across every channel and prove sufficient byte throughput, including the preserved larger-record queue failure. Only after these gaps close can the medium integrated identity/capacity run be meaningful.

No large-run command is supplied as ready to execute. Protected files and real protected baseline capture remain off-limits.
