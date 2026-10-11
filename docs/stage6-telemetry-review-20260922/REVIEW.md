# Stage 6 TEST telemetry review — 2026-09-22

Disposition: REVIEW COMPLETE; implementation and another medium attempt NOT performed.

This document is a proposed correction, not acceptance evidence. The preserved medium attempt remains INCONCLUSIVE. Its correctness checks passed, but its required measurements were incomplete. Nothing here retroactively completes those measurements or explains historical failures.

## Evidence and precise defect

Reviewed frozen candidate root:
`D:\JARVIS-STAGE6-LIVE\ee61943f57a04354b41526fac01bd52f\code`

Preserved result:
`C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-medium-20260922\REPORT.md`

In `durable_sink.hpp`:

- Lines 44, 82 and 120 retain aggregate flush time and maximum flush time, but no per-segment samples. A p95 cannot be recovered.
- Lines 83–85 and 120 retain total readback/hash-verification time, but no individual maximum. This interval includes file reading, hashing and record/sequence validation; it is not pure CPU hashing time.
- Lines 59–60 add elapsed time around every predicate wait, including immediate returns. Positive `backpressureSeconds` does not establish that any transfer actually waited for a credit, or how many did.
- Lines 40 and 61 retain finalizer high-water; lines 70–71 and 102–105 manage writer occupancy. These totals are not a queue history or lag measurement.
- Line 45 holds first/last writer and finalizer timestamps, but line 120 does not expose them. Full-run rates include setup and closure and must not be labelled isolated service throughput.
- Lines 92 and 116–120 provide the existing segment metadata/manifest/result boundary where new measurements can be persisted after collection.

The inspected heartbeat path enforces health/staleness, but does not define a separate slow-heartbeat warning counter or warning threshold. Do not manufacture a zero warning count from the absence of a recorder.

## Proposed smallest complete telemetry candidate

Make a separate TEST candidate in a fresh D: workspace; preserve the current frozen candidate, checker, failed/inconclusive runs and archives unchanged.

### Per-segment timing

Store fixed-width monotonic start/end ticks for durable flush and readback/hash verification on the existing Segment object. Record the counter frequency and explicit measurement version. Preserve the current operation boundaries and state transitions. The finalizer owns these fields until existing ownership transfer completes; no additional lock or live filesystem write is needed for these fields.

Persist successful samples in the existing finalized segment metadata in both manifest and result. Their metadata must agree except for the already-defined MANIFESTED state difference. Bind the new fields through the manifest hash/seal and fresh-run evidence inventory. Use a new, explicit TEST telemetry schema version; do not silently reinterpret old evidence.

Compute count, mean, maximum and p95 offline from the verified samples. Define p95 as nearest rank: sorted sample at one-based rank ceil(0.95 * count). For 15 samples this equals the maximum; it is not evidence of a population tail bound. Require one complete sample per successfully finalized segment. Failed/incomplete samples remain diagnostic only and cannot satisfy successful coverage.

### Actual backpressure episodes

Under the existing gate, immediately before the existing predicate wait, count one episode only when finalizer credits are exhausted and no failure has already occurred. Do not count condition-variable wakeups, spurious wakeups or immediate predicate success as episodes.

Record started, completed and failure-interrupted episodes and their elapsed ticks. A successful run requires started == completed, interrupted == 0. Preserve the old aggregate field's meaning; expose actual blocked-episode duration separately. Elapsed wait includes scheduling and mutex reacquisition and must not be attributed solely to disk time.

No change to the two-credit limit, predicate, notification order, failure propagation or timeout behavior is proposed.

### Queue history and lag

The earlier owner proposal explicitly requests queue time series; three new scalar metrics alone do not close it. Proposed narrow completion: a preallocated, bounded in-memory sequence of snapshots at existing queue-state mutations, with monotonic ticks, transition sequence, input depth, in-flight items/bytes, queued finalizer segments and pending/in-service credits. Include initial and final snapshots. Record inside the existing gate, with no extra lock, polling thread or live file append. Distinguish input depth from in-flight accounting and queued segments from pending credits.

For the finite 64-probe candidate, propose a separate 65,536-snapshot telemetry cap, declared and allocated before collection. This is a telemetry bound, not an increase to an authoritative queue limit. Validate the exact byte cost at build time and include it in preflight. Exhaustion must preserve diagnostics and fail measurement acceptance; never overwrite old samples or silently downsample. This proposal does not qualify that cap for a large campaign.

Record an admission tick on each existing bounded Item to measure admission-to-dequeue and admission-to-write-completion lag. Record finalizer enqueue/dequeue/completion ticks on Segment for queue lag and service-window measurements. Derive count/mean/max from these observations without inventing a new performance threshold. Reconcile queue snapshots with existing counters and high-water marks. Snapshot transitions reconstruct piecewise-constant occupancy; they are not CPU/disk resource samples.

Expose the existing first/last writer/finalizer ticks with explicit window definitions. A bytes-per-window rate includes idle gaps within that window; summed measured service time is a different denominator and must be labelled separately. Neither establishes maximum sustainable throughput.

### Heartbeat reporting decision

Continue preserving the complete existing heartbeat and health evidence and the unchanged <10-second acceptance bound. Report actual threshold violations independently.

Before another medium attempt, the warning field needs an explicit disposition: either identify and implement an already-approved warning policy, or obtain approval to report NOT CONFIGURED (no separate warning policy) rather than a numeric count. This review does not invent a lower warning threshold or silently waive the requested field. No monitor timing or publication change is proposed.

## Persistence and failure behavior

No telemetry file writes, flushes or archive operations on the live event/heartbeat path. Collect bounded data in memory and persist after the writer/finalizer have stopped through the existing D: finalization mechanism. Queue telemetry can be a separately hashed, exclusive-create finalization artifact referenced by the versioned manifest; it must be written and verified before a successful seal. Archive only after live collection has ended.

Missing timing, invalid frequency, negative/reversed intervals, duplicate/missing segment samples, queue-history gaps, overflow, conflicting counters, missing telemetry artifacts, hash mismatch or finalization failure must reject measurement acceptance. Do not turn telemetry completion into proof of kernel lifecycle correctness: every existing independent identity, retained-handle, native-entry and secondary-stream rule remains required.

Additional finalization bytes and instrumentation can affect timing. Measure that overhead on small sacrificial runs; do not claim it is negligible before testing. Do not increase a deadline to accommodate it. Failure during collection keeps the original fault and any available diagnostic measurements; it does not create a successful evidence seal.

## Files/components likely affected — new copies only

- `durable_sink.hpp`: fixed-size timing fields, bounded queue telemetry and finalization serialization.
- `durable_test.cpp`: focused telemetry tests and existing failure-injection coverage.
- Rebuild TEST `J6AuthorityTrace.exe` and the durable test executable because `authority_trace.cpp:5` and `durable_test.cpp:2` include the header. No change to tracer authority/event selection is proposed.
- Versioned copies of `medium-checker/schema.json`, `medium-checker/combined.py`, `medium-checker/checker_medium.py`: required telemetry coverage, schema, metric reconciliation and finalization binding.
- A versioned metrics/report helper and declaration/freeze tooling to identify the new schema, measurement definitions, memory cap and exact binaries.

Do not edit original checkers, native-entry/creator identity logic, the application observer, production runtime, protected VM/configuration, thresholds, authoritative capacity or the historical acceptance contract.

## Focused validation before requesting a new medium attempt

1. Deterministic calculation tests: known distributions, one/zero samples, nearest-rank p95, duplicate/missing/reversed ticks, invalid frequency and manifest/result conflicts.
2. Predicate/episode tests: free credit yields zero episodes; one blocked transfer yields one; spurious wakeups do not add episodes; failure interruption cannot appear as successful completion.
3. Queue tests: known transitions, separate queued/in-flight accounting, correct lag boundaries, initial/final coverage, high-water consistency, fixed capacity, overflow and missing final telemetry rejection.
4. Small native durability run against synthetic data, preserving record bytes/order and all segment states; verify every timing and queue artifact is durably bound. Measure instrumentation and finalization overhead.
5. Existing durability fault matrix, including write/partial-write, transfer, finalizer, flush/hash, backlog, missing/corrupt segment and manifest failures. None may yield acceptance. Add telemetry write/hash/coverage failures.
6. Existing checker/declaration/fresh-run-binding regressions, plus new schema negatives. Preserve old checker tests and the previous 162-check result; report fresh counts rather than claiming they have been rerun.
7. If needed, one separately approved small integrated process run with the existing per-run UAC model to prove tracer/checker compatibility, observer cleanup and immutable source state. No medium or large run is authorized by this review.

Ready to request another medium attempt only after focused validation passes, all requested measurement fields have an explicit disposition, final candidate hashes are frozen, prior archives remain intact and cleanup is proven. A new medium attempt requires separate authorization and a fresh run identity. The previous attempt must remain INCONCLUSIVE.

## Rollback and preservation

Rollback is to stop selecting the proposed new TEST workspace. Preserve its evidence; select the unchanged prior candidate for comparison only. No production restore, VM operation or deletion is required. No implementation, compilation, live process test, medium retry, large validation or protected access occurred in this review.

Observed reference SHA-256 values (read-only inspection, not a full archive reverification):

| File under reviewed candidate | SHA-256 |
|---|---|
| durable_sink.hpp | 18abd0315bf9c733751c2d9c939d974209bde2f2a3f6af7b268b34958cee1c3a |
| authority_trace.cpp | 8f84c0b8ab38df23699127685527d064bf996a5f97ffcbc6b28abffae5ab0cf3 |
| durable_test.cpp | 1c900f958dc21a00f912d73549f67342c21ae6d919f4f877aa4f3b16866dc01c |
| medium-checker/checker_medium.py | 64649825222ec4e0d06a50531944fc083db208cb9f47b88c6fc2baead7f63d6d |
| medium-checker/schema.json | 1da2a00d7125a9c78b736d840345223ea0db147da5c30fd0bc817c1a8a8dcaf5 |
| medium-checker/combined.py | 2f475cca8906b7c92f66209d539f0ef97e73ba78760a677f546ca9d4ae8a9cab |

Historical 21 AMBIGUOUS / 1 UNMATCHED remain unchanged. New medium 258 AMBIGUOUS / 1 UNMATCHED remain separate supporting evidence. Historical delay causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
