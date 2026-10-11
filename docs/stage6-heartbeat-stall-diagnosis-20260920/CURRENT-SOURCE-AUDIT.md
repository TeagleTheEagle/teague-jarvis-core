# Current corrected monitor audit — H1/H2

Authoritative source inspected: `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-eventidentity-fix-20260920\monitor.ps1` and `event_queue.cs`. Their exact SHA-256 hashes are recorded in source-before.json and preserved-before.json. Originals are unchanged. This audit is of the corrected candidate, not the earlier numeric-removal monitor.

## Historical 14.565-second interval

Frequency: 10,000,000 monotonic ticks/second. Heartbeat record 153 UTC is 2026-09-20T00:22:26.6465441Z; record 154 is 2026-09-20T00:22:41.2114958Z. Those are record-construction timestamps. Record interval: 14.5649514 seconds. Actual publication-complete marker interval: 14.5650069 seconds. Markers have exact QPC ticks, not independently recorded UTC timestamps.

| Point | Exact QPC | Observation |
|---|---:|---|
| T0 | 1700760158311 | publication.complete, sequence 153 |
| T1 | 1700767538426 | event.serialize.end |
| T2 | NOT RECORDED | Next individual call entry unknown; Stamp(serialized), Join-Path, Test-Path, Get-Item precede the next marker |
| T3 | 1700843804700 | event.append.begin; this is a region, not proof File.AppendAllText had already been entered |
| T4 | 1700905765853 | event.append.end; includes stamp, validation/lock, write, removal and diagnostic operations |
| T5 | 1700905766228 | event.end |
| T6 | 1700905808380 | publication.complete, sequence 154 |

T1→T3: 7.6266274 seconds. T3→T4: 6.1961153 seconds. The time is in event draining, before the next heartbeat construction. The old trace cannot separate individual file calls, queue-lock waits or scheduling pauses within those spans. It does not establish a filesystem driver cause. `historical-interval.json` preserves the surrounding trace and overlapping resource windows.

## Synchronous path inventory

| Operation | Current path / symbol | Live-loop behavior |
|---|---|---|
| Event draining | monitor.ps1 / Drain → ExactEventQueue.Select | Synchronous before heartbeat construction |
| Queue locking | event_queue.cs / Enqueued, Select, PersistAndRemove, Stats, Reconcile | SyncRoot; File.AppendAllText is outside the queue lock; exact-index deletion remains protected |
| Event serialization | Drain / ConvertTo-Json | Synchronous |
| Event metadata I/O | Drain / Test-Path, Get-Item.Length | Synchronous per event |
| Event evidence append | ExactEventQueue.PersistAndRemove / File.AppendAllText | Synchronous open/append/close per event; historical trace did not split its suboperations |
| Heartbeat creation | record.begin/end / ConvertTo-Json, UTF8.GetBytes | Synchronous |
| Heartbeat file-size check | journal.size / FileStream.Length | Synchronous property access |
| Heartbeat journal open | journal.open / FileStream(CreateNew, Write, FileShare.Read) | Once before loop, not reopened per heartbeat |
| Heartbeat append | journal.write / FileStream.Write | Synchronous |
| Normal flush | journal.flush / FileStream.Flush(false) | Every heartbeat; not durable Flush(true) |
| Durable flush | durable.flush / FileStream.Flush(true) | After loop/grace/final enumeration and collection.freeze only |
| Close | journal.close / FileStream.Dispose | At finalization/error, not each heartbeat |
| Rotation | none | Not implemented; Reader rejects rotation |
| Finish-file query | finish.query / Test-Path | Synchronous each loop |
| Process enumeration | Get-CimInstance Win32_Process | Initial and final checks, outside live loop |
| Subscriber callbacks | Register-CimIndicationEvent, EventTap | Asynchronous callbacks/enqueue; consumed synchronously by Drain |
| Performance counters | resources.ps1 / Get-Counter, Get-Process | Separate process; indirect CPU/storage interference possible but not established |
| In-loop diagnostic telemetry | Mark, Stamp, GC.CollectionCount | Bounded in-memory trace; serialized to disk after collection |
| Evidence hashing | Get-FileHash script identity | Before loop; final evidence hashing/archive outside live publication |
| Archive writes | external finalization | None in heartbeat loop |
| Sleep/wait | Wait-Event -Timeout 1 | Live loop; early wake allowed. Excess over one second is not itself proof of CPU starvation |
| Grace | Start-Sleep -Seconds 2 | After loop, unchanged |
| Console/pipeline output | Wait-Event piped to Out-Null; subscriptions at startup | No per-heartbeat console output; diagnostics saved after loop |
| Retries | none | No arbitrary retry/backoff loop |

No synchronous live Flush(true), FlushFileBuffers or fsync was found. File.Write/Flush(false) and per-event append can still take time; removing durable flushing does not make ordinary I/O nonblocking.

## Historical resource observations — correlation only

Two resource sampling windows overlap the interval. They themselves span approximately 10.221 and 7.318 seconds, limiting resolution. C: idle time was 0–7.565%, queue depth 1–15, reported average write latency 5.409–264.912ms, read throughput up to 103.72MB/s. D: was approximately 99.54–99.95% idle. Aggregate CPU samples were 0–6.464%, available memory about 21,458–21,565MiB. The monitor process CPU counter rose 0.046875 seconds across the two samples; the hashing process counter rose 0.109375 seconds. This is consistent with waiting, but does not distinguish I/O blocking, scheduling, locks or a runtime pause. Monitor priority was unavailable to the historical non-elevated resource sampler; do not infer it from a blank field. Per-core values and process/thread snapshots remain in the raw evidence.

No historical GC pause-duration, kernel scheduling trace or individual file-call timing exists for this event. The earlier 13.7/14.084-second delays and Stage 1 cause remain unconfirmed and separate.
