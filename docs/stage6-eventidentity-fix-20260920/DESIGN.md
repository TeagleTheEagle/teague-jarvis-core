# Exact queued-event removal — validation only

All files in this candidate are synthetic validation infrastructure. Original candidate and diagnostic runs remain unchanged. Pre-change source hashes and paths are in source-before.json; the entire preceding evidence trees are inventoried in preserved-before.json.

## Identity and ordering

ExactEventQueue attaches to the actual System.Management.Automation.PSEventArgsCollection.PSEventReceived event before monitor readiness or probe launch. Its handler assigns a bounded monotonic QueueSequence under that collection's SyncRoot. The dictionary explicitly uses Object.ReferenceEquals and RuntimeHelpers.GetHashCode, never overloaded PowerShell equality. Entries remain retained for the collector lifetime. The 20,000-entry bound fails closed before sequence overflow can occur. External EventIdentifier, PID, timestamp and name are metadata only.

Select walks the actual collection in FIFO index order, retains the exact object and rejects a second outstanding selection. Enqueue notification sequence is evidence identity, not a claim about native process-event ordering. Concurrent arrival can append entries while a selection is being serialized or written.

## Persistence and consumption

PersistAndRemove uses an atomic consumer guard and validates the selected reference under SyncRoot, releases SyncRoot for File.AppendAllText, then reacquires it. Only after that write succeeds does it revalidate the exact object, find the matching index by Object.ReferenceEquals and RemoveAt that single index. No numeric-key deletion remains, including teardown. No queue lock spans disk I/O, waits or serialization; there is no second lock with an opposing acquisition order. The consumer guard rejects concurrent consumers instead of waiting. Bounded entries also bound reference lookup work. This does not claim Windows I/O itself has a hard real-time completion bound; the unchanged reader deadline rejects excessive delays.

A failed/uncertain append marks the collector failed, removes nothing, and refuses retry. Partial output is preserved and cannot qualify for acceptance. Retrying a successful operation cannot append twice because its selected capability has been consumed. An unexpected external remover is detected by the reference check and makes the run fail closed. The monitor has exactly one drain consumer; no other candidate path removes queue entries. Direct mutation by an unrelated consumer is not allowed or silently reconciled.

Append success is not durable acceptance. Existing final fsync, complete pipeline reconciliation, process exits, manifest hashing and archive verification remain required. New queue-state and late-residue failures also block finalization. The fixed two-second grace period and ten-second heartbeat threshold are unchanged. Teardown records residue rather than deleting it; any residue prevents campaign acceptance.

## Rollback and limits

Rollback means stop using this new candidate and retain it as evidence. Archived old scripts remain available, but remain defective and must not be used for protected hashing. No production or VM rollback is required. The previous 18.965-second enqueue delay remains a disclosed timing observation. Correcting collision deletion does not prove that all scheduling or notification-delivery problems are resolved.

Historical PID 13248 / 22544 / 21896 individual causation remains UNPROVEN. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
