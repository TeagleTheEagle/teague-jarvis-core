# Stage 6 large-collector compatibility and integration review

Disposition: BLOCKED at large-pipeline integration design/capacity boundary. Stage 6 INCOMPLETE.

This is read-only source inspection plus new review evidence. No candidate changed, dataset hashed, observer launched, VM/configuration accessed, production operation or acceptance attempt occurred.

## Preserved passing baseline

Candidate: D:\JARVIS-STAGE6-LIVE\e55504d627d24f24a6f56f9e2435230b\code

All 162 files in stage6-health-journal-candidate-20260922/candidate-frozen.json rehashed and match. Existing medium archive SHA-256 reverified as 89ef23e92d3b32d291b68cd4ec1bb042e54ab0e22b914363672fdb6f34d4643c; 872 ZIP members, CRC integrity clean. This recheck does not constitute a new medium execution. Existing passing evidence remains valid for its declared finite process-only workload.

## Exact incompatibilities

1. large_launch.ps1:19 selects J6BaselineTrace.exe; :24 waits for app-health.json. dry_health.py:21 parses that snapshot. The validated monitor publishes app-health.jsonl. The large adapter must retain both existing observer creation-verified handles and check both for liveness; replacing Health with only an application publisher check would weaken the contract.
2. fresh_binding.py:6 requires exactly one worker, 64 probes, 60-second collection and a medium declaration. It cannot authorize the dynamically paced hashing/sampler workflow. Do not alter medium declarations or feed fabricated medium counts to its checker.
3. authority_trace.cpp:67 enables the process-lifecycle keyword; :71 ends collection after 180 seconds. Historical two-pass calibration took 523.4482737 seconds. Existing large campaign/monitor design used 1080/1200 seconds, independently of unchanged 10/13.6/15-second health/probe/observer safety limits. Reusing 180-second capture would not cover that workload.
4. owned_entry.cpp:104 launches qualified_worker.py explicitly. large_collect.py launches a baseline_hash_worker and periodic bounded sampler, plus dynamically paced probes. analyze_medium.py:83 rejects unclassified process instances; these classes require explicit creator-owned early handle/image/native evidence and complete parent-instance verification. OS-created helpers retain their separate approved rules.
5. baseline_contract.py:9,42 requires baseline-allowlist.json and baseline-limits.json; neither is present in the passing candidate. A fresh synthetic-only declaration must be bound to the new contained dataset and run, not copied with stale paths. Protected access stays false.
6. The passing authority tracer is process-lifecycle only. It does not replace the required detailed filesystem/registry/scheduling/image/thread startup diagnostic stream. Keeping the old detailed tracer alongside it changes the integrated capture/finalization/cleanup configuration; replacing that stream with lifecycle-only evidence would silently omit requirements.
7. durable_sink.hpp:41 caps telemetry at 65536 snapshots. The medium result has only 264 records and 843 snapshots; it does not establish capacity for full detailed tracing. Earlier detailed-trace report measured 97212 records in a rolling second and identified auxiliary/tap bounds and whole-pipeline storage qualification as unresolved. Those older measurements inform sizing only, not current acceptance. Do not feed the detailed stream into the qualified sink or increase queue/telemetry bounds without qualification.

## Proposed minimum integration design for review

Preserve the passing candidate and checker. Create a separate TEST-only large-integration candidate and versioned declaration/checker. First prove it on small synthetic data; do not start 59.7 GB or protected data.

- Adapt large launch readiness and dry_health.Health to the validated complete-record journal, preserving both observer handle checks and existing failure/finalization behavior.
- Declare collector, hash worker, sampler and probes explicitly. Use creator-owned creation/image capture and native entry for directly launched classes. Unknown helpers remain rejected; do not assign console rules by name alone.
- Bind source manifest, synthetic-only allowlist, limits, executable hashes, run identity, output paths and final seals to the fresh run. No mutable prior-run artifacts.
- Preserve separate authoritative kernel lifecycle, independent retained/native evidence, supporting CIM and detailed diagnostic tracing. Define the bounded ownership and shutdown order for both trace channels before implementation. The elevated component accepts no arbitrary commands, does not touch protected data and remains per-run UAC controlled.
- Define one complete capacity/reserve contract across both streams, metadata, snapshots/taps, segment finalizers, auxiliary files and archive temporaries. Demonstrate supported rate and duration before selecting production-sized synthetic collection. The historical 1080/1200 capture envelope is a planning input, not permission to raise process or heartbeat deadlines.
- Qualify the large checker using real small-run evidence and mutations: missing worker/sampler, mismatched creation/image, stale run, missing diagnostic channel, trace loss, segment/sequence/hash gaps, truncation, stale health, incomplete finalization, sampler/observer leftovers must fail.

Likely files: new large binding/checker/analyzer; copied large_launch.ps1, dry_health.py or dedicated adapter, large_collect.py, owned_entry.cpp integration entry, authority_trace.cpp capture configuration, process evidence adapters; synthetic declaration/allowlist/limits and new tests. Writer/diagnostic sink changes are NOT presumed necessary or authorized by this review; capacity results must determine whether they require a separate design. No Core/runtime/production files.

## Validation sequence after design agreement

1. Hash-freeze a new candidate; retain medium source unchanged.
2. Focused journal/observer and process-class binding tests.
3. One small normal hash/metadata/finalization run and one controlled failure, with all observer/helper cleanup independently proven.
4. Full existing monitor, identity, collision, durability and checker regressions.
5. Complete integrated capacity qualification; reject overflow, missing telemetry and archive failures.
6. Only with passing preparation, propose the fresh 59.7 GB synthetic run with unchanged health and process deadlines.
7. Protected baseline, OS-enforced VM isolation, fresh-Windows recovery and final cutover remain later mandatory gates with their specific preservation/authorization boundaries.

## Why this stops before launching

A format adapter alone cannot provide the absent diagnostic channel, large workload bindings and capacity proof. Selecting or redesigning the multi-channel capture/finalization arrangement is the remaining architecture decision. Neither raising the 180-second constant alone nor weakening the checker is a valid completion path. Review the explicit integrated design above before implementation of that boundary; no new live experiment was justified during this inspection.

Rollback: no rollback operation needed; leave frozen candidates unchanged and preserve this review. A future candidate can be deselected without deletion or production restore.

Historical probe/sampler/storage delay causes remain UNCONFIRMED. Historical 21 AMBIGUOUS / 1 UNMATCHED unchanged. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.