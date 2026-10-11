# Narrow dry-workflow integration

The accepted 66-file diagnostic candidate is preserved unchanged. A separate D: candidate adds seven adapter/test files. Exact originals and pre-change SHA-256 are in source-before.json. Newly added files have no pre-existing hash; their final hashes appear in candidate-source.json.

## H1/H2: existing paths and mismatch

Original `launch.ps1` writes `mode` (idle/disk/sustained/cpu/Dhash/dry), duration, cluster and thresholds to case.json, then calls collect.py. The current collect.py imports collect_hardened.py, whose top-level configuration requires `phase` A-E. These are workload labels versus diagnostic subset labels, not interchangeable names. A is idle; B is C: reads; C is C: hashing; D is D: hashing; E invokes ladder_worker.py subset C (two hashes). E does not mean the complete baseline/archive acceptance workflow.

`dry_worker.py.snapshot` inventories the fixed 12 sacrificial files, checks sizes/mtime, hashes twice, compares and creates baseline-manifest/hash. `finalize.py.finalize/accepted` provides original probe-specific evidence flushing/copy verification. `accept_run.py` connects the original monitor/probe results, finalization gate and archive receipt; it expects original-monitor file formats, not the new dual-evidence formats. None of these historical entry points is relabelled or rewritten.

Validated dual evidence: app_monitor.ps1 independently subscribes to CIM START/STOP, EventTap records callbacks/enqueues, ExactEventQueue persists/removes exact entries, bounded 4.6-second quiet/45-second close plus a final drain seals collection. J6KernelTrace.exe/kernel_trace.cpp supplies native ETW creation/exit and query/synchronize handles. evidence_support.py supplies explicit producer/Toolhelp retained handles. cleanup_checker.py correlates creation identity, parent, image, both streams and strict post-exit acquisition. Its source is unchanged. Both application and kernel observers remain unchanged.

## H3: canonical contract and ownership

New contract.json version 1 selects scenario miniature or dry1 and pins run identity, source allowlist, initial inventory and immutable thresholds. `mode`, diagnostic-letter `phase`, unknown fields/scenarios and stale run identities are rejected before any observer starts. Legacy fixtures remain unchanged and their regressions run; no silent translation is provided.

Runtime state.json is the only authoritative phase state, containing ordered history and monotonically increasing sequence. Transitions must name the current phase and its immediate successor. Durable pending-write + atomic replacement publishes state within the D: run directory. Launcher owns PREPARED/OBSERVERS_READY; collector owns WORKLOAD_RUNNING, then hands ownership exclusively to the hash worker until it exits; collector closes WORKLOAD_CLOSED; launcher closes OBSERVERS_CLOSED after both retained observer processes exit; offline finalizer owns remaining phases. There are no concurrent state writers.

Sequence: PREPARED → OBSERVERS_READY → WORKLOAD_RUNNING → HASH1_COMPLETE → HASH2_COMPLETE → METADATA_VERIFIED → WORKLOAD_CLOSED → OBSERVERS_CLOSED → CLEANUP_VERIFIED → FINALIZED → MANIFESTED → ARCHIVED → VERIFIED.

## H4/H5: actual workflow

dry_launch.ps1 validates frozen source and preparation contract, starts the same two UAC observers and records retained identities. It waits for application heartbeat readiness before admitting work. Both observers are running before the collector is launched. Native ETW starts first to observe the application-monitor infrastructure, as in the previously validated dual harness.

dry_collect.py runs dry_hash_worker.py as an actual child and runs unchanged J6Probe.exe through Probe.wait_approved and its independent observer, using the unchanged probe_policy.py. The hash worker ports the original two-pass snapshot loop, retaining input allowlisting, inventory comparison, metadata checking and byte hashing. It does not create an accepted manifest early. Real parent/child identities and handle evidence are written in the producer envelope expected by cleanup_checker.py; the filename stress-result.json is an existing serialization contract, not a claim that an unrelated stress result proves hashing.

Health checks retain/validate both observer creation identities and require application heartbeat age below 10 seconds while hashing/probing. Missing/partial heartbeat files fail closed; no speculative retry is added. Kernel consumer completeness/loss and exit proof are independently checked after closure. Hash-workflow failure remains preserved and blocks finalization.

The collector waits for actual worker/probe exit, preserves primary errors and attempts bounded evidence cleanup. Parent process exceptions never become PASS because later cleanup succeeds. The launcher always signals close and waits for each observer using existing bounds. Offline finalization checks producer success, unchanged cleanup_checker result, unchanged probe_policy.validate_lifecycle, observer exits, heartbeat samples, two hash passes, phase ordering and candidate hashes. Only then does it fsync evidence, write the baseline manifest/hash, create and verify the archive, recheck source metadata and publish the final result.

## Containment and limits

All live artifacts, state, temp, health, hashes, manifests and evidence archives are under a unique D: run. Miniature inputs are 12 × 4096 bytes within that run. Full dry1 input is the exact pre-existing C: sacrificial directory, never a caller-provided arbitrary path. This C: input is the intended load, not a monitor-state fallback. Protected/unapproved source text is rejected before resolving/opening it. Reparse/junction paths are rejected. Runtime executables/Windows dependencies remain on C:; no claim is made that all OS I/O occurs on D:.

Unchanged probe thresholds: warning 5s, hard deadline 13.6s, independent observer 15s; heartbeat 10s. Existing campaign admission bound 90s; existing observer TTL 180s and quiet/finalization bounds unchanged. Post-failure observation waits are cleanup evidence only and cannot erase a deadline failure.

Failure-injection unit tests use mocked boundary results only where explicitly testing isolated finalizer failure behavior. They are not substituted for live lifecycle evidence; the miniature live test supplies actual independent streams, real hashes, retained handles and archive proof. Full-size Dry Run #1 and Dry Run #2 remain NOT RUN in this pass.

Rollback: stop using the new separate candidate and retain all evidence; use the unchanged accepted candidate for its previously validated diagnostic scope. No VM, production or security-setting rollback is involved.
