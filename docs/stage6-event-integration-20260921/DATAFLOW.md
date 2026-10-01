# Actual acceptance dataflow and narrow integration boundary

Frozen source: D:\JARVIS-STAGE6-LIVE\f469b94b665e4808af1c5bb6aa46b207\code. All original files remain unchanged. Only a fresh copy is eligible for integration. No archived launcher is executed as-is.

| Boundary / exact file and function | Current identity, buffer, destination | Role / acceptance dependency |
|---|---|---|
| startup_trace.cpp LifecycleEvent / Acquire / Sample | Kernel subject PID+CreateTime+ProcessSequenceNumber+parent sequence; retained handles;8192 lifecycle rows; etw-result.json | AUTHORITATIVE_ACCEPTANCE_EVIDENCE; cleanup_checker.check |
| startup_trace.cpp Event; trace_sink.hpp TraceSink.add/finish | Detailed thread/image/file/registry/scheduler records;64MiB queue,8192-byte record,8MiB segments,128GiB/196531200 records/16384 segments | SUPPORTING_FORENSIC_EVIDENCE, required by integration_verify.inspect; cannot filter away |
| owned_entry.cpp; native_bridge.py | Directly owned child creation identity, PE entry, exit, debugger records; native-PID-creation.json and bridge closure | AUTHORITATIVE_ACCEPTANCE_EVIDENCE; integration_verify.inspect |
| timed_monitor.ps1 subscription.start | Independent CIM START/STOP; PID,parentPID,name,TIME_CREATED; raw fields lack process CreateTime/sequence | AUTHORITATIVE_ACCEPTANCE_EVIDENCE; not replaceable by second ETW transport silently |
| EventTap.cs Capture/Add | A-callback and A-enqueue receipts; first20,000 TapRow objects; Overflow thereafter drops NEW rows; app-tap.json | Currently authoritative callback/enqueue proof, NOT UI pagination |
| event_queue.cs ExactEventQueue.Enqueued/Select/PersistAndRemove | Exact PSEventArgs object reference + monotonic queue sequence; cumulative20,000 identities retained; exact RemoveAt under SyncRoot; app-events.jsonl | AUTHORITATIVE_ACCEPTANCE_EVIDENCE; identity collision correction must remain |
| timed_monitor.ps1 Drain/finally | app-receipts.json,app-result.json,app-heartbeats.json; raw events; queue closure | AUTHORITATIVE_ACCEPTANCE_EVIDENCE; checker and baseline finalizer |
| LoopTiming.cs |1,000,000 point/span cap; timing overflow fatal; stage-timing.json | Required diagnostic health/forensics; unchanged threshold, no silent drop |
| lineage.py associate / parent_valid | Conservative time/image/parent compatibility; no nearest match; ambiguities fatal | cleanup_checker.check; historical ambiguity unchanged |
| cleanup_checker.py load/check/evaluate | Reads full app-tap and raw/queue receipts plus kernel/retained/native evidence | All lifecycle acceptance currently depends on complete tap |
| integration_verify.py inspect | Full detailed trace manifest verification plus native coverage | Must pass before baseline_finalize.finalize |
| baseline_finalize.py require_ready/finalize | cleanup gate,hash equality,heartbeat<10,metadata,source hashes; durable-files,baseline manifest,evidence.zip | Final acceptance/archive; no failure may be sealed as pass |

Dependency graph:

EventTap.Add → app-tap.json → cleanup_checker.load/check callback uniqueness → cleanup result → baseline_finalize.require_ready → final manifest → archive acceptance.

EventTap.Overflow → timed_monitor queue.health failure → app-result failure → cleanup/finalization rejection.

ExactEventQueue cumulative capacity → queue failure → same rejection. This second bound must not be hidden by fixing the tap alone.

## Proposed narrowly bounded changes

1. A new C# authoritative sink is used directly by EventTap.Add before a bounded secondary view. Preserve full original TapRow in a sequenced envelope; no source field replaced. Segmented D: output uses CreateNew, SHA256,counts,sequence boundaries and sticky error. Explicit finite queue bytes AND item count. The existing 20,000 row snapshot becomes a diagnostic view only when the complete authoritative manifest verifies.
2. Raw drain/persistence receipts also enter the same application sequence through a distinct event kind. Preserve existing raw file write and exact removal; no in-memory admission is called durable. Only successful final drain/hash/verification establishes durability.
3. Cleanup loads verified authoritative envelopes and reconstructs its callback/raw/receipt inputs from them, checking the existing mirrors byte-for-value. It never treats a truncated view as complete. Final manifest explicitly records authoritative manifest hash and view truncation.
4. New queue streaming mode bounds OUTSTANDING exact object references at20,000, releases only successfully persisted/removed identities and keeps monotonic cumulative counters. Legacy default behavior is preserved for existing regression tests. No change to exact-reference removal, persistence order or failure semantics.
5. Immutable final outputs use exclusive creation in new entry points. Only explicitly mutable health/control/state files retain overwrite semantics. No old report/launch script is executed against historical paths.

## Independent identity constraint

CIM TIME_CREATED is event generation time, not guaranteed process creation/exit. A handle opened on callback belongs to the process existing at lookup, which can be a later PID incarnation. It is supporting observation only. It cannot promote a reused/delayed event to UNIQUE_MATCH. Retain every compatible instance; no time-nearest or upper-lifetime assumption excludes older delayed STOPs.

The new instance table stores kernel creation/sequence/parent identity and independent handle/native observations. An independently event-bound creation discriminator can select one exact instance; absent that discriminator, possible candidates are preserved and ambiguity fails closed. Do not claim generic generated table tests establish real CIM discriminator availability. Historical22 remain21AMBIGUOUS/1UNMATCHED.

The medium campaign is gated on focused results. If real independent source identity remains unprovable or actual capacity fails, preserve partial integration and do not manufacture medium/large acceptance.
