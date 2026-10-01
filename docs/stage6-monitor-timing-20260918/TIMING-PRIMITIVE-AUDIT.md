# Timing primitive review (diagnostic only)

The preserved append-only monitor runs event draining, heartbeat construction, FileStream.Write, FileStream.Flush(true), stop-marker inspection and Wait-Event serially on one PowerShell runspace. Separate hashing prevents direct runspace blocking, not shared storage or scheduler contention.

| Operation | Placement | Existing bound / interpretation |
|---|---|---|
| WMI/CIM start/stop subscriptions | Startup | Synchronous registration; no explicit operation timeout. Not between established heartbeat records. |
| Get-CimInstance process enumeration | Startup/finalization | Synchronous; no explicit operation timeout. Not normally between heartbeat records. |
| Get-Event queue snapshot and Remove-Event | Each loop | Synchronous queue work; no application-level duration deadline. |
| Event JSON serialization and AppendAllText | Each event drain | Serialization/open/write/close run before the next heartbeat. No I/O timeout specified. |
| FileStream constructor | Once before first heartbeat | CreateNew, Write, ShareRead. No per-iteration open. |
| FileStream.Length | Each loop | Size check, not rotation. No application-level duration bound. |
| FileStream.Write | Each loop | Synchronous managed file write. No application-level I/O timeout. |
| FileStream.Flush(true) | Each loop | Flushes buffered data including intermediate disk buffers; no 10-second timeout argument. Instrumented as one managed call including OS flush, not separate kernel tracing. |
| Wait-Event -Timeout 1 | Each loop | Explicit one-second event wait, not the default indefinite wait. Measured overrun includes scheduling/runtime effects and is not a direct scheduler ready-time metric. |
| Test-Path finish marker | Each loop | Synchronous metadata operation with no explicit deadline. |
| Start-Sleep 2 | Final grace only | Not an in-loop 14-second delay. |
| Journal close/unsubscribe/diagnostic trace serialization | Finalization | Not normally between heartbeat records. |

No explicit mutex/semaphore or external subprocess wait exists in the monitor loop. No pipeline console output is intentionally retained: Wait-Event output is discarded. Subscriber delivery and .NET GC/runtime activity can still affect execution; their time cannot be assigned without appropriate measurements. GC collection counts are sampled, not GC pause durations. No priority is changed.

Diagnostic differences: bounded in-memory timing markers, extra queue-depth snapshots, event timestamps and final trace output. These add observer overhead. Resource counters run separately and batch output at exit. Heartbeat write/Flush(true), event filters, journal semantics, and the consumer's 10-second threshold are preserved.

Official references:

- [Microsoft FileStream.Flush](https://learn.microsoft.com/en-us/dotnet/api/system.io.filestream.flush?view=net-9.0): the Boolean overload controls flushing intermediate buffers.
- [Microsoft FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers): documents storage flush behavior and the possible inefficiency of per-write flushes. This supports investigation, not attribution of this incident.
- [Microsoft Wait-Event](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/wait-event?view=powershell-7.5): explicit timeout is in seconds; omitted timeout waits indefinitely.

## Preserved 14.0840902-second incident

- T0: sequence 103 record timestamp, 2026-09-18T04:15:28.3967161Z; QPC 112511993563.
- T1: final action before gap: NOT RECORDED.
- T2: blocking-call start: NOT RECORDED.
- T3: blocking-call end: NOT RECORDED.
- T4: first action after gap: NOT RECORDED.
- T5: sequence 104 record timestamp, 2026-09-18T04:15:42.4808051Z; QPC 112652834465.

Those timestamps are record construction times, not proofs of flush-completion times. The collector subsequently rejected a stale/future heartbeat. Missing time remains unassigned in the historical trace. New instrumented runs must be reported separately, even if a plausible matching mechanism is reproduced. The earlier 13.7-second event and historical Stage 1 cause remain UNCONFIRMED.
