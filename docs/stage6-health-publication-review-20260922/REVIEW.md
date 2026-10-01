# Stage 6 TEST health-publication correction review

Disposition: REVIEW COMPLETE — IMPLEMENTATION PROPOSED, NOT VALIDATED.

This review authorizes no medium retry, large run, protected baseline hashing or VM operation. The failed frozen candidate remains unchanged. Production is outside scope.

## Evidence

Frozen candidate: `D:\JARVIS-STAGE6-LIVE\0c93b626e738469d90b2d38e478edfea\code`.

Failed run: `identity-fb816854880943888ef68df7d4dec0c8`.

The fourth idle probe raised JSONDecodeError during its health callback. Its failure-caught QPC 3573060420495 lies within the monitor's health-output span 3573060415307–3573061160287, frequency 10000000. The exception was caught 0.0005188 seconds after that span began. The span lasted 0.074498 seconds.

`qualified_worker.py:16` reads and parses app-health.json. `timed_monitor.ps1:5` opens that file with FileMode.Create and FileShare.Read, then serializes, writes and flushes. The call at line 39 repeats this overwrite. An incomplete readable publication is structurally possible. The observed overlap supports that mechanism strongly. Exact read bytes and the truncate syscall timestamp were not captured, so those details remain unconfirmed. The earlier report's reader line 18 refers to the surrounding health check; the JSON read itself is line 16.

The previous attempt remains MEDIUM_VALIDATION_FAILED. Its archive contains 221 verified members, SHA-256 b4ec0ebe10481818bd744b6d551e64b8ac24ceffbbb567008020b4af4400f43e. The earlier missed-UAC-gate attempt remains separately BLOCKED; neither becomes accepted through this review.

## Narrow proposed integration

Create a separate versioned TEST candidate. Reuse the existing bounded append-only journal protocol in journal.py; do not modify that shared historical implementation or patch the failed candidate.

1. In the candidate timed_monitor.ps1, replace the repeatedly truncated live health snapshot with a single exclusively created D:-local app-health.jsonl stream. Preserve FileShare.Read. Serialize complete newline-terminated records before writing. Never reopen with truncate, replace the live file, rotate it or reset its sequence.
2. Use the existing journal identity and record fields: run, pid, process creation time, QPC frequency, seq, pump, ticks, UTC, ACTIVE state and zero violations. Sequence increases once per successful event-pump health publication. Check existing subscriber/queue health before publishing. No separate thread may manufacture healthy pump progress.
3. Keep the existing 4096-byte record and 1048576-byte journal bounds; overflow fails closed. Do not assume these bounds fit any future large run; measure within the current medium gate. Keep the monitor's duration, event collection, deadlines and loop timing unchanged. Preserve current durable flush behavior for this correction; changing flush policy is not part of it.
4. Publish app-ready.json only after the first complete health record has been flushed. Retain its existing external fields/schema. Construct the reader's run binding from the independently bound current run directory, not new implicit authority in a client field. To avoid a second exists-before-complete readiness race, serialize readiness to an exclusive bounded D:-local staging file, flush and close it, then publish to the previously absent final readiness name without overwrite. Any publication failure aborts. Windows reader/writer behavior must be tested; it is not declared proven by this design.
5. Add a small TEST health-reader adapter over existing journal.Reader and PublisherWatch. Keep the creation-verified process handle alive; verify publisher liveness for every health check. Require positive matching QPC frequency, current run/creation identity, monotonic sequence and timestamp, valid complete record and ACTIVE/zero-violation state. Preserve rejection of replacement, truncation, malformed completed records and stale/future time.
6. Explicitly enforce 0 <= age < 10 in the adapter. Existing generic journal.Reader rejects age > 10, and test_journal.py deliberately permits exactly 10. Do not relax the medium contract or change the generic reader/tests. Adapter failures must latch, including this stricter boundary; subsequent valid data must not revive a failed run.
7. An unfinished trailing record is not a published health update and never renews freshness. While it is incomplete, only the last complete valid record may satisfy the existing strict freshness bound. No initial complete record means failure. Malformed newline-terminated records fail immediately; do not catch-and-ignore JSON errors, retry until success, or grant a new grace period.
8. On normal finalization, freeze collection, flush/close the journal durably, and require no incomplete trailing record. On interruption/write failure, preserve the journal and fail the run. Close reader and publisher handles in finally paths. Worker completion/launcher exit must reflect final validation failures. Keep live-health-checks.json entries in their current qpc/age shape so the existing analyzer and checker need no compatibility rewrite.
9. Preserve app-heartbeats.json, event records, queue identity semantics, kernel authority, independent handle/native verification, sampler policy, writer/finalizer and cleanup requirements unchanged. Bind the new artifact through the existing complete intake manifest and source freeze. No relaxed checker rule or retrospective acceptance.

## Candidate files expected to change

- timed_monitor.ps1: bounded journal publication, completed readiness publication, closure.
- qualified_worker.py: consume the health-reader adapter and close it on all paths; retain current output semantics.
- New narrowly scoped health-reader module and focused TEST fixtures.
- New preparation/source-freeze/evidence records for the separate candidate.

No changes are proposed to journal.py, the frozen checker/schema, native tracer/PE-entry implementation, application/runtime Core, production paths or protected VM/configuration. The exact new candidate path will be uniquely generated during separately approved preparation, not assigned to the failed workspace.

Other copied paths (app_monitor.ps1, baseline_monitor.ps1, dry_health.py and large/baseline launchers) also reference the old snapshot protocol. They are not the active medium path. This correction must not be advertised as fixing them, and they must not be run against the new journal publisher without a separate compatibility review. No broad search-and-replace.

## Required focused validation before another medium attempt

Use a new bounded D: sacrificial test directory. No UAC, CIM/ETW observers, VM access or large dataset is needed for initial protocol tests. Use actual PowerShell writer and Python reader integration, plus injected clocks for exact boundary checks.

| Case | Required result |
|---|---|
| Old overwrite mechanism held after truncation, before write | Reproduce parse failure deterministically; label sacrificial reproduction, not proof of historical bytes |
| New writer paused mid-record with concurrent reader | Only prior complete record is accepted; incomplete record does not renew timestamp/sequence |
| Resume partial write through newline | Exactly one new record becomes visible; no duplicate/skip |
| Initial empty/partial stream | Readiness not published; reader cannot claim healthy startup |
| Ready staging file paused before publication | Final ready path remains absent; once published its JSON is complete |
| Writer dies or throws mid-record | No success; liveness/final closure rejects; partial evidence preserved |
| Malformed complete JSON, invalid state, duplicate/skipped sequence | Immediate latched failure |
| Wrong run, PID/creation identity or frequency | Failure; no PID-only replacement acceptance |
| Negative/future age; exactly 10 seconds; above 10 seconds | Failure; just below 10 remains eligible |
| File replacement, truncation, inaccessible path | Failure without retries or fallback path |
| Capacity, short write, write/flush failure | Failure and preserved evidence; no cap increase |
| Actual repeated concurrent PowerShell/Python reads and writes | Ordered complete records, bounded bytes, no transient parse errors |
| Final flush/close, exception cleanup, handle ownership | No unclosed test processes or handles; final record boundary complete for success |
| Existing analyzer-produced output/checker fixtures | Same health output schema and strict lifecycle rules; no weakened negatives |

Rerun affected heartbeat/journal/process/publisher identity/path-containment/finalization regressions and current checker/telemetry composition regressions. Preserve every failed test. Do not claim a new numeric pass count until execution occurs. Tests must synchronize deliberate race boundaries using explicit gates, not arbitrary sleeps.

Only after focused integration and regressions pass should a separately authorized medium attempt use a fresh identity and complete lifecycle/telemetry/archive verification. No medium attempt is part of this review.

## Risks and acceptance boundaries

The append-only reader already has partial-record and concurrent-append tests, but integration into this monitor is unvalidated. Exact-ten-second behavior requires the explicit strict wrapper. Readiness publication must also be tested under Windows sharing rules. Event-heavy loops can increase journal growth; preserve hard capacity rejection rather than silently extending it. A stalled or interrupted write cannot make health fresh. Durable finalization and complete record checks remain mandatory.

This is a process-health transport correction, not a change in process authority or a substitute for kernel lifecycle completeness. Application-event ambiguity stays diagnostic; authoritative contradictions still fail. Historical 21 AMBIGUOUS / 1 UNMATCHED remain unchanged. Historical delay causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Rollback: stop selecting the new candidate and retain it and all evidence. The frozen failed candidate, accepted application baselines and production require no restoration. Never delete preserved evidence.

## Decision

The bounded journal integration is recommended for implementation and focused sacrificial validation only. It is not implemented, not validated, and does not close medium or Stage 6 acceptance. Next approval should cover only the listed TEST files and focused tests; a new medium attempt remains separately gated.
