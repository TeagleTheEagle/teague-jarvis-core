# Stage 6 — durable segments and kernel authority qualification

**BLOCKED — kernel tracer UAC launch canceled before either observer or probe worker started.**

No retry occurred. Parts B/C are not accepted, and the frozen checker remains unchanged. This report does not claim KERNEL_DURABILITY_BOUNDARY_VALIDATED.

## Completed work and exact boundary

New isolated candidate: `D:\JARVIS-STAGE6-LIVE\a684e9f6f9ae4826af45c0a04c18d839\code`.

The new native `durable_sink.hpp` implements a small TEST evidence component. It uses the reviewed original-handle ownership design with Windows APIs directly, so the same implementation can service a native ETW collector without introducing a separate managed-runtime bridge. It does not replace the existing C# writer or frozen checker. All 125 inherited candidate files remain byte-identical; 510 preservation checks match.

New implementation files: `durable_sink.hpp`, `durable_test.cpp`, `authority_trace.cpp`, `qualified_launch.ps1`, `qualified_worker.py`. The two new executables are `J6DurableTest.exe` and `J6AuthorityTrace.exe`. `qualification.py` is an unfinished, unexecuted adapter/qualifier draft in this report directory, not integrated into acceptance. Preparation, build, test and evidence scripts plus their exact command/output records are archived separately. `final-source.json` records source/executable hashes. Existing binary/source snapshots and historical failures were not overwritten.

The first compilation failed due to the Windows `max` macro; the failed source/build log is preserved. A local `NOMINMAX` guard corrected that compile defect. Both subsequent builds succeeded; the kernel build reports an inherited local-variable-shadow warning. No compiler failure was relabeled as a runtime failure.

### Small component results

- Normal: 12,000 accepted/written/reread records, 45 segments; contiguous sequence, size/hash verification, durable manifest/seal, drained queues and exited threads all passed.
- Fault campaign: 14/14 **expected-rejection cases** passed. Each process returned the expected failure disposition, recorded sticky failure and produced no acceptance seal. These are controlled injected thread/operation failures, including simulated worker crashes; they are not physical power-loss or arbitrary OS process-kill qualification.
- The controlled writer/finalizer crash cases throw on the worker paths. The delayed-flush case refuses finalization after an injected delay before the API; it does not establish cancellation of a kernel I/O operation hung inside `FlushFileBuffers`.
- No full monitor/queue regression suite was rerun in this blocked pass. No medium, large, protected-data or combined run occurred.

Normal run: `durability-b62096a36a8947359157e9b3c78cbddb/case-0`.
Fault campaign: `durability-4be274956d1644828242f970d2ee4efc`.
Canceled kernel qualification: `identity-16d00617f55f400e8972fb2907594e62`.

## Durability and ownership semantics

`ACTIVE → CLOSED → DURABILITY_PENDING → DURABLY_COMMITTED → HASH_VERIFIED → MANIFESTED` is checked one transition at a time. CLOSED means logically sealed, not handle closed. `unique_ptr` moves the segment and original handle from the active writer to the finalizer queue; the writer loses ownership. A single finalizer owns the transferred handle, flushes, seeks and rereads it, compares SHA-256/byte count/record sequence, then closes it. Normal finalization independently reopens the immutable path read-only and verifies it before creating the manifest and its verified hash seal. The manifest records the verified states; the post-commit result records MANIFESTED. Both the manifest and its seal must be present and verified; a manifest alone is not successful acceptance.

`WriteFile` success is WRITTEN to Windows/cache, not a durable claim. `FlushFileBuffers` on the same write-capable original handle establishes the selected Windows durability boundary. There is no `Flush(false)` or `Flush(true)` in this native component. `CloseHandle` alone is never used as durability proof. No filesystem flush occurs while holding the ingestion lock. Queue saturation can propagate backpressure to the writer and admission; removing flush from the live writer does not eliminate finite-capacity constraints.

Microsoft describes the cached write/device flush distinction and the write-access requirement for [FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers). This is API-level durability evidence, not a physical storage/power-loss certification. The alternative managed implementation's [Flush(Boolean)](https://learn.microsoft.com/en-us/dotnet/api/system.io.filestream.flush?view=net-9.0) is not called by this candidate.

Normal segment limit: 65,536 bytes. Finalizer: two queued-plus-in-service segments, warning at one; maximum closed-segment backlog 131,072 bytes. The tracer candidate selects 8,192-byte segments with the same two-segment bound; that live configuration has NOT run. Ingestion retains the existing upper bounds of 65,536 items / 64 MiB, with existing finite record/storage/segment limits. Finalization retains a five-second wait. Pending capacity blocks the writer, which preserves finite input capacity; admission rejection is sticky failure. Failure cleanup can release incomplete pending evidence but never emits an accepted seal.

Residual implementation qualification: the component's direct read loops need explicit negative-`ReadFile` fault-path review/tests before promotion; the current tests establish successful readback/hash checking, not every OS read-error path. The current canceled qualification must not be resumed or accepted through an unreviewed adapter. More failure/identity proof remains necessary before checker integration.

## Mandatory report

| # | Item | Actual result |
|---|---|---|
| 1 | Segment states | Six ordered states above; normal result has all six per segment. |
| 2 | Active writer | Single writer owns active handle; ordered global sequence; no append after ownership transfer. |
| 3 | Finalizer | Single worker; exclusive original-handle ownership; no record-content writes. Test corruption injection is outside that worker. |
| 4 | Durability APIs | WriteFile ≠ durable; successful FlushFileBuffers then readback SHA/sequence; manifest/seal each flushed and reread. |
| 5 | Segment size/bounds | Normal 65,536 bytes; 45 segments. Record ≤8,192 bytes; ≤16,384 segments; existing finite budgets retained. |
| 6 | Finalizer bound | Two including in-service; warning one; normal peak two / 130,969 bytes. |
| 7 | Global sequence | Normal 1–12,000 contiguous, zero duplicate/gap/overlap; all 12,000 independently reread. |
| 8 | Normal durability | One small component case PASS. Not full lifecycle acceptance. |
| 9 | Fault injections | 14 cases / 14 expected rejections / zero accepted seals. Write, partial write, close, transfer, startup, delay, flush, hash, backlog, missing segment, corruption, manifest, finalizer-worker crash, writer-worker crash. |
| 10 | Writer throughput | Producer: 12,000 / 0.006585 s ≈1.82M admissions/s burst. Append service: 12,000 / 1.3107561 s ≈9,155 records/s. End-to-end: ≈7,301 records/s. Not sustained capacity. |
| 11 | Finalizer throughput | Observed flush+hash service 1.5533365 s for 12,000 records ≈7,725 records/s; excludes inter-segment idle/overlap. Not a large-run rate. |
| 12 | Max flush | 0.066698 s in the normal run. |
| 13 | Backlog | Peak two / 130,969 bytes; input peak 11,457 items; 11,729 writes occurred while finalization was pending. |
| 14 | Canonical identity | Proposed capture scope + subject PID + creation FILETIME + ProcessSequenceNumber, with parent-instance/image corroboration. Fresh qualification NOT RUN. |
| 15 | Kernel source | Microsoft-Windows-Kernel-Process; new native tracer would durably frame selected real START/STOP records. UAC canceled before start. |
| 16 | Positive unique count | NOT MEASURED in this pass; no real qualification probes launched. |
| 17 | PID reuse | NOT RUN. Retained handles may pin PIDs; feasibility/coverage must be stated honestly in future qualification. |
| 18 | False unique matches | NOT MEASURED; no zero-error qualification claim. |
| 19 | Authoritative ambiguity | NOT MEASURED. |
| 20 | Kernel START | No capture occurred; count unavailable. |
| 21 | Kernel STOP | No capture occurred; count unavailable. |
| 22 | Retained-handle agreement | Real identity qualification NOT RUN. Component subprocess exit checks are not a substitute. |
| 23 | Native PE entry | Validated DLL copied unchanged; no new probe/native proof. |
| 24 | Kernel loss/gap cases | NOT RUN. Draft qualifier is unexecuted and not accepted. |
| 25 | CIM UNIQUE | No observer; unavailable. |
| 26 | CIM AMBIGUOUS | No new measurement; historical 21 unchanged. |
| 27 | CIM UNMATCHED | No new measurement; historical 1 unchanged. |
| 28 | Contract semantics tests | NOT RUN. Versioned amended contract unchanged; no frozen rejection checks removed. |
| 29 | Combined validation | NOT RUN, prerequisite B blocked. |
| 30 | Max heartbeat | NOT MEASURED: no observer started. Do not reuse previous heartbeat as new evidence. |
| 31 | Deadline violations | No component process hit its 15-second observation timeout; no live lifecycle/deadline qualification occurred. Existing 13.6/15/10-second probe/observer/heartbeat values unchanged. |
| 32 | Cleanup | Component processes returned; canceled launcher exited; fresh final host snapshot reports zero matching processes and zero diagnostic trace sessions. |
| 33 | Archive | Exact member count/hash in `archive-verification.json`; no archive success claimed before verification. |
| 34 | Frozen hashes | 510 preservation checks PASS; 125 inherited candidate files unchanged. |
| 35 | Frozen checker | UNCHANGED. SHA-256 `e6fbefd3fd463c6c8e09d0e8273a81b46ee2806515cae05e7837ea905a3e69d6`. |
| 36 | Protected VM | NOT ACCESSED; no protected/configuration hashing. |
| 37 | Production | UNCHANGED; no runtime/configuration/credential operations. |
| 38 | Historical 21/1 | Unchanged under their original contract; not reclassified. |
| 39 | Historical causes | UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED. |
| 40 | Next proposed gate | Finish focused component/adapter qualification, then a fresh authorized per-run UAC kernel/CIM qualification. Only after A+B pass may small combined validation run. No checker integration yet. |
| 41 | Final status | BLOCKED. |

## Preservation, rollback and next owner action

All outputs use new evidence paths. The canceled launch's `launcher-failure.json` preserves Windows' exact “operation was canceled by the user” result. Null observer exit codes mean NOT STARTED, not successful observer execution. The final host check independently confirms zero remaining matching processes/traces. No second prompt was issued. No automatic retry occurred.

Rollback is to leave this fresh, unaccepted candidate unused. Frozen code, historical reports, original candidates, amendment and accepted JARVIS baselines remain unchanged. No production rollback is needed. Do not delete the failed build/canceled-launch evidence.

Owner action needed for the blocked live step: permit a fresh per-run tracer UAC launch when available, then approve the independent application-event observer prompt after tracer readiness. The cancellation was a Windows UAC result, not an automatic tool-approval rejection. No broad elevation or policy change is requested.

Medium validation, the 59.7 GB campaign, frozen-checker integration and protected baseline capture remain unauthorized by this result. No readiness claim for those gates is made.
