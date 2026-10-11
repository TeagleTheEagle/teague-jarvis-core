# Proposed checker interface — no frozen-checker edit

Adapter: combined.py, schema version `stage6-small-combined-v1`.

Entry points:

- `read_bundle(run_root, analysis_root, final_host_evidence)` reopens and hash/sequence-verifies the actual durable files and requires the on-disk segment set to equal the manifest set. It loads the independently generated lifecycle/coverage/CIM/health/cleanup evidence. This must precede validate; caller-supplied JSON summaries alone are insufficient.
- `validate(bundle)` recomputes structural kernel identity and non-vacuous class coverage, cross-checks manifest/result state and counts, health and finalization. It returns `verificationStatus: PASS`, `acceptanceSealed: false`, `archiveStatus: PENDING`. It cannot itself declare the archive or overall gate accepted.
- Final archival verification creates a separate hash-bound combined acceptance sidecar only after preservation, cleanup and archive integrity pass. Component durability seals are not combined acceptance seals.

## Serialized output fields

| Field | Meaning / required checks |
|---|---|
| schema | Exactly stage6-small-combined-v1; reject unknown versions |
| run | Fresh bounded D: run directory; do not accept an unrelated evidence root |
| contract | Kernel instance contract plus owner creator/helper clarification; matrix in CONTRACT.md and preserved qualified DESIGN.md |
| authoritative.records/starts/stops/canonicalIdentities | Counts independently derived from persisted events and matched summaries |
| authoritative.identities[] | Actual serialized identity keys are `scope`, `pid`, `created`, `sequence`; additional fields: image, startQpc, stopQpc, exitFiletime, exitCode, parentPid, parentSequence |
| identitySchema | Logical labels only: captureScope→scope; creationFiletime→created; kernelProcessSequence→sequence; pid→pid. Filetimes/sequences remain decimal strings without lossy conversion |
| verification.classes | DIRECT_PROBE, DIRECT_WORKER, OS_CONSOLE_HELPER, explicit APPLICATION_OBSERVER infrastructure; unknown helpers fail |
| verification.coverage | Required/verified/missing/contradictory counters; per-identity and per-field valid/missing/contradictory/NA dispositions |
| verification.creatorImages | Direct pre-entry creator-handle image count (class A) |
| verification.tracerHelperSuccess | Successfully acquired, creation/image-verified OS helpers (class B) |
| verification.qualifiedPostExitHelpers | Exact pre-existing narrowly qualified post-exit helper cases (class C); never creator image successes |
| verification.failedHelpers | Missing/contradictory helper verification (class D); must be zero |
| durable.segmentManifest | Original manifest bytes represented as parsed JSON; retain authoritative manifest path/hash and original file for verification |
| durable.first/last/gaps/duplicates/missing | One contiguous admitted-event sequence; not contiguous global Windows ProcessSequenceNumber values |
| durable.finalizerHighWater/writerHighWater/writerHighWaterBytes | Observed bounded queue peaks, with frozen limits independently checked |
| secondary | CIM counts/raw-file-linked classifications, persisted count and queue closure; authority=false |
| health | Heartbeat maxima, unchanged deadline results, observer/writer/finalizer closed states |
| finalization | Empty queues, all segments verified/manifested, trace/native closure, independent host cleanup result |

The acceptance envelope is meaningful only with its original input artifacts, frozen adapter/source hashes, exact contract, checksummed archive and final acceptance sidecar. It is not a signed remote trust statement. No credentials or production state are needed.

## Proposed future integration procedure — OWNER REVIEW ONLY

1. Preserve the frozen legacy checker/hash and this complete small-run archive. Create a separately versioned TEST checker candidate; do not overwrite the legacy checker or historical results.
2. Add an explicit contract/version-selected adapter entry point. Legacy evidence continues through its original rules; no automatic fallback from a failed legacy check to the amended contract.
3. Consume the original persisted files through read_bundle plus existing complete analysis checks. Recompute identity/class coverage and per-record/segment integrity. Do not trust a serialized PASS or logical-schema label without original evidence.
4. Gate combined acceptance on all independently evidenced lifecycle, durability, helper classes, CIM health, deadlines, cleanup and archival checks. Keep class C distinct from successful handle/image records; preserve missing/contradictory rejection.
5. Run focused wrong-contract/missing-record/sequence/hash/classification/cleanup/archive rejection tests and relevant frozen-checker regressions on copies. Compare legacy outcomes unchanged; preserve every failure.
6. If separately authorized, run one new small sacrificial integration through the candidate checker, then archive/hash-verify and stop for owner review. Do not automatically proceed to medium, large, protected hashing or VM operations.

This document is an interface proposal, not authorization to edit the checker. No checker integration is performed in this pass.
