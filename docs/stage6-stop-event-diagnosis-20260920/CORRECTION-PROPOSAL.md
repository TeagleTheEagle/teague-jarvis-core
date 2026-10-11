# Proposal only — exact queued-event removal

Evidence: repeat1 records 11 cross-source EventIdentifier collisions. Every one of its 11 missing events was observed at A's callback and queue-entry hooks before its sibling's removal, but never reached drain. Separate System.Management observations also received these notifications. An isolated synthetic queue test assigned two session-owned events the same ID and demonstrated that Remove-Event -EventIdentifier removes both. The installed GetNextEventId IL contains a non-atomic increment of _nextEventId; real concurrent events demonstrably received the same number.

Classification of the reproduced mechanism: **QUEUE_DRAIN_LOSS** (overbroad removal by a collided numeric event ID). Historical missing PIDs 13248/22544/21896 lack EventIdentifier/callback/queue records, so their exact individual causes remain unproven. Do not retrofit the new traces into those records.

Smallest proposed change: after successfully appending a drained event, remove only that exact PSEventArgs object from the session ReceivedEvents collection, under its existing SyncRoot. Locate it by reference identity, verify it belongs to one of this monitor's registered source identifiers, and remove that one index. If it is unexpectedly missing or mismatched, fail closed and preserve diagnostics. Do not clear a subscription or remove all events with a numeric ID. Never hold the queue lock while serializing, writing or flushing evidence. Continue to process both distinct events even if their IDs collide. No PowerShell installation/assembly patch is proposed.

Likely files: a new validation-only candidate copy of monitor.ps1; a narrowly scoped event_queue.cs helper; focused test fixture for queue removal/collision/failure behavior. Preserve the original candidate, its 10-second reader and durable-finalization logic. No JARVIS runtime, production, security, authentication or VM file change.

No correction is implemented in this diagnosis. No grace-period, timeout, filter, notification-source or acceptance-policy change is proposed. The recorded 18.965-second enqueue delay needs to remain visible; fixing removal does not prove all timing problems solved.

Revalidation after approval:
1. Existing focused suite plus exact-object removal tests: two different subscriptions sharing an ID, same-source collisions, distinct PIDs, concurrent arrival while draining, write failure retains event, missing/reference-mismatched event fails closed, unrelated events untouched, no lock held across file I/O, no false STOP synthesis.
2. Prove duplicate PID/creation-time rejection and retained process handles remain intact; numeric event-ID collisions must no longer erase another event.
3. Repeat original five-class campaign and instrumented repetitions against the same synthetic inputs. Require all actual START and STOP notifications, all independent handle exits, zero unexplained losses, no diagnostic overflow and no stale heartbeat. Keep the existing 10-second threshold.
4. Repeat termination, reader/writer restart, malformed/partial records, stale/stalled publisher, write failure, delayed/failing finalization, hashing-worker death, hash mismatch and identity ambiguity injections. Failed cases remain unaccepted.
5. Independently require durable finalization and archive hash verification; healthy heartbeats or exited handles are insufficient.
6. Only after all load gates pass: independent full sacrificial Dry Run #1, then Dry Run #2. Preserve source hashes before/after and archive every failure.
7. Confirm no live diagnostic processes, protected VM access or production changes. Only a complete MONITOR_VALIDATED campaign can support an owner-reviewed protected-baseline retry. It does not itself authorize that retry.

Rollback: stop using the new candidate; retain both old and new infrastructure/evidence. No production rollback or filesystem cleanup is needed. Do not remove archived failures.
