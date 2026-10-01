# One small combined validation

Scope: one fresh sacrificial process/evidence run using the unchanged qualified c090f8cbc0d444e493f1d801e36fd1bb candidate. This is an integration-correctness test, not a capacity run, hashing rehearsal, VM operation or full Stage 6 acceptance.

Workload: existing DIRECT_WORKER launches 16 short-lived probes (idle 4, churn 4, overlap 8), with OS-created helpers and both independent observers. Synthetic workload data is their lifecycle/identity evidence; no large dataset or source-data hashing is needed for this gate. Live kernel events exercise multiple 8 KiB segment rotations through the actual writer/finalizer, not a synthetic substitution for process behavior. Require at least two nonempty authoritative segments, complete expected direct inventory, and all observed helper descendants.

Authority: unchanged base kernel contract plus owner-clarified creator-owned direct-process / tracer-opened helper matrix. Exact helper classes: A creator-owned pre-entry capture; B successful tracer helper capture; C existing qualified post-exit helper acquisition; D failed/missing helper verification. C never counts as A or B. OTHER_INDIRECT_HELPER has no default allowance. The frozen legacy checker remains untouched.

Durable stream: ACTIVE→CLOSED→DURABILITY_PENDING→DURABLY_COMMITTED→HASH_VERIFIED→MANIFESTED. Require global contiguous sequences, ordered ranges, hashes/readback, no missing/extra segment files, manifest/result/seal agreement, writer/finalizer exit and fault=0. Existing pending limit 2, queue limit 65,536 items/64 MiB; no limit adjustment. Manifest is written from HASH_VERIFIED metadata; final result records MANIFESTED after manifest persistence. This existing order is checked, not relabeled as skipped states.

Independent channels: preserve creator/tracer process-handle verification and native entry; keep raw CIM/application events, unique queue tokens, receipts and independent persistence. AMBIGUOUS/UNMATCHED remain explicit. A positive contradiction or collection loss fails; no forced matching.

Health: unchanged heartbeat <10 s, 13.6 s hard probe deadline, 15 s independent probe observer, existing finalization/observer bounds. Require all applicable independent checks and clean lifecycle closure, not merely process exit status.

Combined acceptance is a new post-run envelope. Existing kernel-authority-seal.json is a component durability seal only. It cannot represent global acceptance before the application observer, handles, queues, host cleanup and archive are verified. A combined acceptance seal may be issued only after all these conditions pass and the independent archive is verified. That final receipt/seal is a separately hash-bound archive sidecar, avoiding circular self-hashing.

Failure tests use copies of preserved evidence and deterministic mutations, never rewriting original evidence. Reuse verified 14/14 sink fault-rejection mechanisms for durability/backlog failure; test the combined adapter rejects faults/missing evidence. One actual fresh normal run; no automatic rerun if it fails.

Stop after the report and exact future checker-integration proposal. No frozen-checker edit, medium/large/protected validation or production change.
