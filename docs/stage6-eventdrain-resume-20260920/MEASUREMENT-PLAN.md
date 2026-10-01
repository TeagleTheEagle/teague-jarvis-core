# Diagnostic-only event-drain investigation

No protected VM/configuration or production path is used. Prior canceled evidence is preserved. A fresh five-second smoke run precedes the finer instrumentation. Seven 150-second cases follow serially: `a1`, `minimal`, `persist-d`, `none`, `dhash`, `a2`, `a3`.

| Case | Source workload | Event persistence | Journal | Telemetry |
|---|---|---|---|---|
| a1/a2/a3 | C: hashing | C: | C: | Full |
| minimal | C: hashing | C: | C: | External performance sampler and optional runtime samples disabled; authoritative callbacks and secondary diagnostic WMI observer retained |
| persist-d | C: hashing | D: bounded sacrificial directory | C: | Full |
| none | C: hashing | C: | C: | Also omits secondary diagnostic WMI observer; authoritative subscribers, enqueue taps, retained handles, timing and heartbeat remain |
| dhash | D: hashing | C: | C: | Full |

All cases retain the same ten-second Reader limit and fail-closed latch. A live-health failure stops that case's workload; the case is not retried or accepted. Later preplanned diagnostic cases may proceed only after all directly launched children have exited. An unexpected VirtualBox event, uncertain cleanup, monitor error or lost identity stops the batch for review. Offline interval checks can mark an otherwise completed diagnostic case FAIL. No run here is monitor acceptance.

## Event-drain call graph

`Drain → ExactEventQueue.Select → SyncRoot acquire → queue index/SourceIdentifier → reference dictionary lookup → select unique QueueEntry → release lock → PSEventArgs/SourceEventArgs.NewEvent access → ProcessName/ProcessID/TIME_CREATED/TimeGenerated properties → diagnostic Stamp → ConvertTo-Json → Join-Path → Test-Path → Get-Item.Length → PersistAndRemove → consumer guard → SyncRoot acquire → Valid/reference Index → release lock → File.AppendAllText → SyncRoot acquire → Valid/reference Index → exact RemoveAt → release lock → diagnostic Stamp → next event → Get-Event backlog → Drain complete`.

Process metadata comes from the already-delivered CIM event; there is no per-event Get-Process/Win32_Process lookup. `File.AppendAllText` contains its own open/write/close; the diagnostic measures the entire actual call without replacing it with a different file API. Its internal flush/close cannot be separately attributed by these source-level probes. Heartbeat Flush(false), final Flush(true) and final close have their own markers.

## What the measurements can establish

The bounded in-memory trace records QPC wall time, native thread ID and GetThreadTimes CPU execution time. Queue lock request/acquisition/release delimit waits and holds. Instrumentation sampling overhead is separately recorded. Queue CountOwned, item read, identity lookup, reference Index and exact removal are timed without changing identity logic. Per-event and drain scopes provide batch size, backlog and time per event. Enqueue callback timing is recorded on producer callback threads. Windows process exits are independently verified with retained handles.

Wait-Event can return early; excess over its one-second bound is a wake-delay observation, not proof of scheduling starvation. An independent 100ms diagnostic observer records sleep overruns but publishes no health or authority. Native CPU time is quantized and includes instrumented code; no kernel scheduler/ETW trace is available. Callback-tap ordering can be signed because the observer attaches after the native handler; do not label that delta as producer scheduling latency. Queue depth before a drain is observable in enqueue taps and prior post-drain state, not guaranteed to be an atomic batch snapshot. Maximum depth and post-drain backlog are recorded.

Full telemetry is in a separate process. It records processor/per-core counters, physical disk counters, memory/page counters and process/thread snapshots. Counter and process sampling durations are measured; coarse overlapping samples support correlation only. Minimal/none runs intentionally lack these optional metrics and must report them unavailable, not zero.

## Preservation and future validation

Only new diagnostic infrastructure/evidence files are created. Source hashes are captured per run; differences from the prepared monitor are timing and controlled evidence-placement/observer configuration, not a runtime correction. If a correction is justified, propose it for review first. Future acceptance still requires focused/collision regressions, complete real event coverage, all five workloads, failure injection, independent dry runs 1 and 2, durable finalization and verified archives. Protected-baseline eligibility remains NOT JUSTIFIED.
