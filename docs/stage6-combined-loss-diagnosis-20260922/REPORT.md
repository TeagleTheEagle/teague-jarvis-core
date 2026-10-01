# Combined tracing loss diagnosis — 2026-09-22

STATUS: INCONCLUSIVE — exact ETW loss cause is not reconstructable from the preserved measurements. The small combined integration remains failed; large validation remains blocked.

## Scope and preservation

Offline analysis only. No acceptance rerun, tracing-setting change, new observer, workload, protected VM/configuration access, or production change occurred. New analysis files and this report are the only changes. A final read-only host census found zero matching diagnostic/VirtualBox processes and zero diagnostic trace sessions at 2026-09-22T08:22:51.2684866Z.

Examined candidate: `D:\JARVIS-STAGE6-LIVE\ac2f7b1000034e9bbcb0486fcb6ef9cb\code`.
Failed run: `protected-a54707487ac94440953b1c99967abd0b` under that candidate. Despite its prefix, this was a 12-file, 786,432-byte synthetic run, not protected VM hashing.

Original archive: `C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 SMALL LARGE INTEGRATION FAILURE 20260922 ac2f7b10\evidence.zip`.
All 711 archive members verified. Archive SHA-256: `1e9de5a21ca32a4f88f5acb4b1306fe56794a6d1b3fcf3a14f7d710d9a4ef141`.
Post-analysis verification found all 72 snapshotted failed-run artifacts unchanged and the archive unchanged. See `preservation-before.json` and `preservation-after.json`.

One initial analysis encountered Windows access denial on an intentional historical negative-test fixture. That error and the initial script are preserved. No permissions were changed. The successful analysis verifies every archived member and compares the accessible frozen-source/current failed-run evidence; it does not claim a fresh read of the inaccessible negative fixture.

## Confirmed failure

| Channel | EventsLost | RealTimeBuffersLost | LogBuffersLost | Exit |
|---|---:|---:|---:|---:|
| Authoritative kernel lifecycle | 4 | 0 | 0 | 95 |
| Detailed startup trace | 50,130 | 0 | 0 | 95 |

Both observers report requested shutdown, zero consumer/flush/stop errors, and no sink fault. The checker correctly rejected observer cleanup. Zero buffer-loss counters do not cancel nonzero event-loss counters. Microsoft defines these as distinct statistics: [EVENT_TRACE_PROPERTIES](https://learn.microsoft.com/en-us/windows/win32/api/evntrace/ns-evntrace-event_trace_properties).

The counters were recorded only after stopping. Therefore neither the loss interval nor the missing events' process/provider can be established. Capture is system-wide before consumer-side filtering; it would be unsafe to claim that the missing events belonged only to unrelated processes. Authoritative loss remains an acceptance failure.

## What the retained measurements establish

The authority writer accepted and wrote all 24 admitted lifecycle records. Its peak producer queue was two records/881 bytes, finalizer peak one segment, total producer lock wait 0.0000032 seconds, backpressure 0.0000003 seconds, and maximum flush 0.046152 seconds. It exited with no residue. This provides no evidence of authority-writer saturation; it does not prove upstream capture completeness.

The detailed writer persisted 151,173 records / 49,690,415 bytes in six segments. Peak queue was 3,940,175 bytes against its 64 MiB limit. Its maximum recorded write interval was 0.729962 seconds. Source inspection establishes that this interval covers segment WriteFile + FlushFileBuffers + CloseHandle, not one individually timed filesystem operation. No detailed sink overflow/fault was recorded.

Application observer PID 17084 accounted for 120,252 detailed records (79.55%). Of 84,529 retained events after the collector returned, 84,448 belonged to that observer. The peak retained event-time window contained 82,673 records in one second, predominantly the observer's file events. Thus the detailed trace is substantially measuring monitoring/finalization activity. This is an evidence-backed investigation lead, NOT proof that this activity caused either loss counter.

Recorded event-to-callback lag reached 3.3719496 seconds for authority and 1.8977005 seconds for detail. These are delivery delays, not measured callback execution times. They cannot identify whether buffering, scheduling, callback work or another mechanism owned the delay.

Application heartbeat maximum was 1.2422593 seconds. Its 17 queued records were persisted and removed, with no residue. Healthy application heartbeats and complete admitted queues do not establish loss-free ETW capture.

See `analysis.json`, `phase-analysis.json`, `authority-deliveries.json`, and `longest-deliveries.json` for computed distributions and counts.

## Timeline and implementation observations

QPC origin is authority readiness; frequency 10,000,000 ticks/second. Python nanosecond monotonic values were converted explicitly in `timeline.json`.

| Milestone | Seconds after authority ready |
|---|---:|
| Detailed tracer ready | 47.9105652 |
| Application observer ready | 75.5592896 |
| Collector invocation | 75.7235229 |
| Collector return | 77.8819747 |
| Final shutdown marker | 92.0845918 |

The collector call took 2.1584518 seconds. The largest retained event burst occurred after its return. No time-series loss counters exist to associate that burst or any startup interval with event loss.

Both trace implementations request 64 KiB buffers, minimum 4, maximum 64, and a one-second flush timer. Actual allocated/free buffer counts were not recorded; requested values alone are not proof of actual allocation. Authority enables its provider before creating the ProcessTrace consumer thread. Detail enables classic flags at session start and additional providers before creating that thread. This leaves an unmeasured startup interval; its contribution is UNKNOWN.

Callbacks perform metadata extraction and identity/serialization work under shared guards; sampling also uses shared state. No callback-duration, guard-duration or provider-enable timing was captured. Possible startup, consumer-work and scheduling contributions remain hypotheses.

The current detailed binary was traced to the exact historical batched build. Binary hash `baca39cee51a146989c573fc98492b8e88c9f90e2d191559d774f7f88b4a8c65` and source match. The corresponding `trace_sink.hpp` is absent from the current candidate but available with matching recorded hash in historical candidate `3316657ba1864413a0c95ea1dc7bf6ff`. See `verified-build-lineage.json`. The earlier `source-lineage.json` comparison to a different binary is preserved, not used to infer current sink behavior. The verified implementation flushes outside the producer queue lock. Missing current header packaging is a build-reproducibility issue, not an established runtime-loss cause.

## Minimum next diagnostic step — proposed, not implemented

Create a separate TEST instrumentation candidate, preserving current binaries and every failed artifact. Keep provider selection, buffer configuration, deadlines, queue rules and acceptance criteria unchanged.

1. Timestamp session creation, OpenTrace, each provider enable, ProcessTrace entry, first callback, readiness, stop request, flush and stop.
2. Capture bounded periodic and phase-boundary read-only ControlTrace QUERY statistics: EventsLost, RealTimeBuffersLost, LogBuffersLost, actual NumberOfBuffers/FreeBuffers and query duration/status. Use separate query storage. Record any instrumentation failure explicitly.
3. Add bounded in-memory callback/filter counts and timings for guard wait/hold, metadata extraction and sink admission; distinguish write, flush and close durations. Do not introduce synchronous callback evidence writes.
4. Preserve observer identity/phase so loss-counter changes can be correlated with startup, collector work and observer finalization. Counter sampling localizes an interval, not individual missing events.
5. Validate instrumentation on tiny sacrificial data, then compare authority-only, detail-only and combined capture with identical tiny workloads as diagnostic runs, without acceptance sealing or automatic retries.

This is preferable to speculative buffer increases, provider removal or relaxed loss checks. No corrective mechanism is justified yet. Live diagnostics require the established per-run observer UAC approvals. No medium/large validation or protected capture is authorized by this report.

## Disposition

Previous focused test results remain historical: 10 integration tests, 69 monitor tests, 222 queue assertions/10,000-event stress and 137 finalization assertions passed before the failed small live attempt. They were not rerun here. Both synthetic hash passes and metadata preservation succeeded, but that does not override tracing loss. The controlled-failure acceptance case remains NOT RUN.

Historical 21 AMBIGUOUS / 1 UNMATCHED classifications remain unchanged. Historical delay causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Protected-baseline eligibility: NOT ELIGIBLE. Stage 6 remains incomplete. Exact combined-loss cause: UNCONFIRMED. No capture settings changed; no acceptance rerun.
