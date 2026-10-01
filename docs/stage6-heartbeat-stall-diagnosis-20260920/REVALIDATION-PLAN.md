# Diagnostic continuation and future correction validation

No correction has been selected or implemented. Existing queue identity/removal behavior is preserved. Diagnostic copies add only bounded monotonic timing, native thread CPU-time sampling, in-memory runtime metrics, a separate 100ms wake observer, and journal placement controls.

## Resume diagnosis after owner resolves the canceled elevation

1. Preserve the canceled `smoke` directory. Use a fresh run identity; never reuse or overwrite it. First verify the launcher, monitor and VirtualBox process state read-only.
2. Validate the diagnostic monitor with a fresh short smoke run and retained process handles. Require complete callback/enqueue/persistence coverage and zero trace overflow. Elevation is only for read-only process monitoring and synthetic evidence output, with the normal UAC prompt.
3. Run serial 150-second comparisons, avoiding overlapping load generators: A C hashing/C journal; B C hashing/D journal; C D hashing/C journal; D D hashing/D journal; E CPU-only/C journal; F C sequential reads/C journal. Event evidence and collector controls deliberately remain on C: in all comparisons, so journal placement is the only output-location variable. A negative B result cannot rule out event-evidence I/O on C:.
4. Repeat A independently at least twice more (three total attempts). Run one additional A with external resource sampler and optional in-monitor runtime sampling disabled; retain essential heartbeat, queue, callback and process-handle evidence. Minimal telemetry is diagnostic only and cannot qualify protected hashing.
5. Keep the ten-second reader threshold and fail-closed latch unchanged. A failed diagnostic run remains failed; do not reset its reader or convert it into acceptance. Continue other preplanned diagnostic cases only after its own processes exit and safe cleanup is established.
6. Analyze lock-request/acquisition/hold durations, file-stat/append regions, heartbeat write/flush, wait deadline overrun, independent observer jitter, CPU-time deltas, GC pause-duration deltas and storage sampling windows. Report instrumentation overhead separately. These are not kernel ETW scheduling or storage-driver traces; classify only to the precision supported.
7. Propose the smallest correction only after this evidence. Do not select journal relocation, a new publisher or a queue redesign from the existing correlation alone.

## After a separately approved future correction

1. Preserve current/historical failures and freeze corrected source hashes.
2. Run complete focused monitor regressions, including unchanged ten-second stale rejection, identity/fail-closed checks, malformed/partial records and retained handles.
3. Run collision regressions against the exact queue collection: 222 assertions, live-session reference proof and 10,000-event concurrent deliberate-collision stress. Require no loss, duplication or sibling deletion.
4. Prove actual START/STOP callback → enqueue → persistence coverage against independent retained process handles, and zero residue.
5. Run all five required acceptance workloads. Require both live-reader health and offline heartbeat-interval validation. Any failure stops acceptance.
6. Run required persistence/producer/consumer/monitor/hash-worker/finalizer failure injection; failed evidence must never be accepted.
7. Run full sacrificial Dry Run #1 with representative hashing, source preservation, durable finalization and archive verification. Stop on failure.
8. Only if #1 passes, run independent Dry Run #2 with the same criteria.
9. Reconcile source/evidence hashes, all process identities/exits, zero VirtualBox activity, zero protected VM access and production unchanged. Archive/hash-verify all failures as well as successes.
10. Only complete MONITOR_VALIDATED evidence can justify proposing protected-baseline hashing for separate owner approval. This diagnostic pass never authorizes it.
