# Stage 6 bounded large integration: small sacrificial attempt

**SMALL_INTEGRATION_FAILED — ETW event loss in both trace channels. Stage 6 INCOMPLETE.**

Fresh candidate: `D:\JARVIS-STAGE6-LIVE\ac2f7b1000034e9bbcb0486fcb6ef9cb\code`
Fresh normal run: `D:\JARVIS-STAGE6-LIVE\ac2f7b1000034e9bbcb0486fcb6ef9cb\code\protected-a54707487ac94440953b1c99967abd0b`

## Implemented TEST integration

Separate versioned small declaration/checker, unchanged native binaries and writer implementations. The health adapter consumes the validated append-only journal and retains creation-verified live handles for authority, detailed and application observers. The existing native RunCollector entry invokes the existing traced collector. A copied traced_collect.py performs PREPARED -> OBSERVERS_READY inside the traced collector, avoiding an untraced Python control child after observers start. Direct collector/hash worker/sampler/probe classes require creator-owned early image/native evidence; the new explicit DETAIL_OBSERVER class uses the existing tracer-handle requirements. Unknown classes still reject.

The two unchanged native tracers run separately with distinct output directories, shared exact launcher identity, and independent loss/error checks. Elevated processes accept their existing fixed monitoring arguments only. Three individually identified UAC prompts were approved; normal orchestration stayed non-elevated. Cleanup order is collector/helpers -> application observer -> detailed tracer -> authoritative tracer. No process was force-terminated by this campaign.

Changed/new candidate integration/configuration files (exact before/after hashes in final-hashes.json):
- baseline-allowlist.json
- baseline-limits.json
- dry_health.py
- small_binding.py
- small_check.py
- small_coverage.py
- small_launch.ps1
- test_small_binding.py
- traced_collect.py

Twelve newly generated 64 KiB synthetic files are the only dataset. Explicit synthetic-only allowlist, protected access false, no external data path. Existing 59.7 GB dataset not accessed. Frozen medium candidate and its declarations/checker remain unchanged. The copied medium entry points are not selected by this candidate.

## Validation actually executed

- New focused suite: 10/10 unittest tests, including 15 declaration mutations and three observer-exit subcases. No fabricated extra test count.
- Existing monitor regressions: 69/69 PASS, zero errors/failures/skips.
- Queue regression: 222 assertions PASS, including 10,000-event collision stress (zero internal collisions/loss/duplicate/sibling deletion).
- Existing finalization regression: **137 assertions PASS in this execution**. Historical counts are not substituted.
- Syntax: six Python files and one PowerShell launcher PASS.
- One actual small normal integration attempt; collector exit 0, application observer exit 0, authority and detailed tracers both exit 95.
- Both SHA-256 passes agree for 12 files / 786,432 bytes; metadata and current source content agree. Hash worker reported 0.313 seconds total, including its setup/metadata work.
- Maximum heartbeat interval: 1.2422593 seconds, below unchanged 10-second boundary.
- Application queue: 17 enqueued/persisted/removed, zero remaining; durable application finalization reported success.
- Authoritative tracer: 4 eventsLost; 12 recorded instances / 24 persisted lifecycle records. These counts DO NOT prove complete lifecycle coverage in a lossy run.
- Detailed tracer: 50130 eventsLost; 151173 accepted/persisted detail records. Persisting admitted records does not repair upstream ETW loss.
- Both tracers requested stop, flushed/stopped/consumed with API result 0 and internal fault counter 0; their nonzero loss counters correctly produced exit 95.
- Strict checker failed at OBSERVER_CLEANUP. Subsequent coverage/manifest acceptance predicates were NOT represented as passed. Controlled startup-failure run, real-evidence checker mutation suite, integrated sustained capacity test and large run NOT RUN after this failure.

## Failure meaning and narrow next investigation

Established: the simultaneous two-tracer configuration lost ETW events despite healthy application heartbeat and successful small hashing. Loss is independently reported by each tracer. This is a TEST acceptance failure, not evidence of a production JARVIS defect.

Not established: why loss occurred, the precise interval, whether causes were shared, whether initialization/flush bursts, provider volume, callback work, storage, scheduling or contention contributed. No cause is assigned by speculation. Unchanged medium success does not establish capacity for this combined configuration. Historical delay causes remain UNCONFIRMED.

Minimum next step is a bounded TEST trace-loss diagnosis: record per-session loss/buffer statistics at capture stages and correlate callback/consumer/drain progress with existing detailed timing. Preserve the failed run; do not re-run acceptance or increase queues, ETW buffers, deadlines or heartbeat limits simply to pass. Writer/sink redesign was explicitly outside this integration approval and remains a review boundary if needed. Current authority duration remains 180 seconds; large duration/capacity is not qualified.

## Cleanup, preservation and rollback

Collector tree proof: all exited=True, all handles closed=True, tracker stopped=True. Native bridge: four threads exited, no errors. Sampler: one query, bounded cleanup and supervisor exit recorded. Fresh independent host census at 2026-09-22T08:09:08.1509364Z found zero matching processes and zero diagnostic trace sessions. A mistyped census run-ID was rejected before the query; the successful fresh census is separately preserved. This was not a workload retry.

181 frozen candidate files and 162 prior medium files rehashed without drift. No native binary changes; no Core/runtime/production changes; no protected VM/configuration access; no VirtualBox launch. No acceptance commit. No changes to the 10/13.6/15-second safety limits.

Rollback: deselect this new TEST candidate; keep its source and all failed evidence. No production restore or deletion required. All evidence remains local pending the separately written archive verification receipt; archival is successful only when that receipt reports PASS.

Historical 21 AMBIGUOUS / 1 UNMATCHED unchanged. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
