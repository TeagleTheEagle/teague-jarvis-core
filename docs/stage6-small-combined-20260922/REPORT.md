# Small combined durability and kernel authority validation

**SMALL_COMBINED_VALIDATED**, conditional on the final hash-bound acceptance sidecar accompanying the independently verified archive. Component seals and the intermediate adapter output do not by themselves constitute this disposition.

One actual small combined run was executed; no live retry, capacity/medium/large validation, VM operation or protected hashing occurred. The already-qualified launcher, worker, probes, tracer, writer/finalizer, thresholds and frozen checker were unchanged. A separate versioned TEST adapter reconciles their persisted evidence.

## Mandatory results

| # | Item | Actual result |
|---|---|---|
| 1 | Run ID | identity-c46702f5b0984f119754768f502d0b4b |
| 2 | Workload | One direct worker; 16 short-lived probes (idle 4/churn 4/overlap 8); OS helpers; live kernel events through existing bounded 8 KiB segment sink; independent CIM observer. Synthetic process/evidence data only; no dataset hashing |
| 3 | Authoritative records | 72 |
| 4 | Segments | 4 |
| 5 | First global sequence | 1 |
| 6 | Last global sequence | 72 |
| 7 | Sequence gaps | 0 |
| 8 | Duplicate sequences | 0 |
| 9 | Durable segments | 4, all original-handle flush/readback plus final independent SHA-256 verification |
| 10 | Failed segments | 0 |
| 11 | Hash verification | PASS; exact on-disk segment set equals manifest set; result metadata agrees |
| 12 | Finalizer queue high-water | 2 segments, existing limit 2 |
| 13 | Writer queue high-water | 25 items / 10,418 bytes |
| 14 | Maximum durable flush | 0.0365697 seconds |
| 15 | Kernel START | 36 |
| 16 | Kernel STOP | 36 |
| 17 | Canonical identities | 36 unique capture-scope/PID/creation/process-sequence instances |
| 18 | False unique matches | 0 |
| 19 | Authoritative ambiguity | 0 |
| 20 | Direct probes | 16 |
| 21 | Direct workers | 1 |
| 22 | OS console helpers | 18; one application-observer infrastructure instance additionally recorded |
| 23 | Creator-owned image coverage | 17/17: 16 probes plus worker, persisted before native entry |
| 24 | Successful tracer-helper coverage | 2; application-observer tracer verification separately recorded |
| 25 | Qualified post-exit helpers | 16, explicitly class C; not successful image queries and not counted as creator-owned capture |
| 26 | Required native entries | 17/17 |
| 27 | Missing required evidence | 0 under the explicitly approved matrix and its existing narrow helper exception |
| 28 | Contradictions | 0 |
| 29 | CIM unique | 0 |
| 30 | CIM ambiguous | 66 |
| 31 | CIM unmatched | 1; current-run count, separate from historical 21/1 |
| 32 | Maximum heartbeat | 1.0918706 seconds; maximum observed age 1.090401 seconds |
| 33 | Deadline violations | 0; all existing thresholds unchanged |
| 34 | Finalizer drain | PASS; threads exited, fault=0, complete manifest/result/seal. Successful finish checks pending/closed queues before sealing |
| 35 | Authoritative queue drain | PASS; attempted=accepted=written=72, remaining=0 |
| 36 | Manifest | PASS; four contiguous ranges, verified hashes, no skipped lifecycle state. Manifest captures HASH_VERIFIED metadata; result confirms subsequent MANIFESTED state |
| 37 | Cleanup | PASS; worker/application/kernel exit codes 0; native threads/handles closed; fresh independent host inspection: 0 matching diagnostics/VirtualBox processes, 0 trace sessions |
| 38 | Archive member count | 324 |
| 39 | Archive verification | Every member's size and SHA-256 checked against its source and inventory; receipt and final acceptance sidecar required |
| 40 | Frozen checker | Unchanged SHA-256 e6fbefd3fd463c6c8e09d0e8273a81b46ee2806515cae05e7837ea905a3e69d6 |
| 41 | Protected VM/configuration | NOT ACCESSED; no claim of new protected-source hashing |
| 42 | Production JARVIS | UNCHANGED; not launched |
| 43 | Historical 21/1 | 21 AMBIGUOUS / 1 UNMATCHED preserved unchanged |
| 44 | Historical causes | UNCONFIRMED; HISTORICAL STAGE 1 CAUSE: UNCONFIRMED |
| 45 | Proposed adapter/interface | combined-interface.json, schema stage6-small-combined-v1; definitions and logical/serialized identity-field mapping in INTERFACE.md |
| 46 | Next proposed gate | Owner review of separately versioned frozen-checker integration procedure below; not executed |
| 47 | Final status | SMALL_COMBINED_VALIDATED only with the verified final acceptance sidecar; Stage 6 itself remains incomplete |

## Evidence interpretation

The 36 required instances all satisfy their applicable evidence classes: 17 direct creator-owned, two successful tracer-opened OS helpers, 16 existing qualified post-exit helper cases, and one application-observer infrastructure instance. Class C requires the unchanged exact error-87 acquisition-after-kernel-STOP proof and complete canonical lifecycle/lineage. There is no generic exemption for missing image/handle evidence or an unknown helper. Historical qualified cases remain historical; this run's independently measured count also happens to be 16.

All 67 secondary CIM events were enqueued, selected, persisted and removed; remaining 0, queue high-water 33. Raw events, internal tokens, persistence/removal receipts and their ambiguous/unmatched results remain archived. They never replace authoritative kernel identity. The writer progressed for 39 records while finalization was active.

Kernel durability seal is a component seal. Combined acceptance was withheld until independent class verification, secondary finalization, host cleanup, unchanged source checks and archive verification completed. combined-interface.json deliberately remains `acceptanceSealed=false`, `archiveStatus=PENDING`: it is the adapter's pre-archive result. The final acceptance sidecar binds its hash, the report, archive, archive manifest and source-preservation record after all checks. This avoids circular archive/self-hashing and preserves temporal evidence rather than rewriting the intermediate result.

## Focused rejection checks and preserved failures

Final adapter fixture result: **31/31 expected dispositions PASS** (one preserved complete control, 30 expected rejections). Covered missing START/STOP, missing handle/image/native records, canonical identity ambiguity, retained/helper contradictions, sequence gap/duplicate, missing/corrupt/extra segment, missing seal, durability/backlog fault, manifest mismatch, skipped state, stale heartbeat, deadline failure, queue residue, cleanup failure, unknown helper class, inventory omission and forced CIM match.

An initial fixture set was **30/31**: the retained-exit mutation incorrectly targeted the first sorted record, which was a qualified post-exit helper without a retained handle. It did not inject the intended contradiction. Only the fixture target was corrected to `retained=True`; no adapter/runtime acceptance rule was relaxed. The original script, failed result, mutation copies and diagnosis are preserved. No actual combined run failed or was retried.

The pre-existing 12,000-record/45-segment normal durability evidence and 14/14 expected fault rejections were hash-verified, including absence of an acceptance seal in every fault case. They were not rerun or presented as fresh failure injections. Combined rejection of their fault/limit outcomes was separately exercised on copies. These scoped tests do not add a claim of actual power-loss testing or exhaustive Windows I/O cancellation behavior.

Preservation preflight verified 288-member qualification and 402-member durability archives and original files; 829 comparisons passed. Final checks also verified 141 qualified source/review artifacts and five frozen adapter artifacts unchanged. All old failures, historical unknown causes, boundaries and limitations remain disclosed.

## Changed files and rollback

No candidate runtime source or binary changed. New TEST review/integration files exist only under:
`C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-small-combined-20260922`.

They include the separate combined.py adapter, copied unchanged coverage/analyzer tools, fresh fixture tests and preserved correction, run contract, interface, reports, source manifests and archive/finalization tools. Exact hashes are in the archive inventory and adapter-frozen.json. Disposable mutation fixtures and this run's live evidence use unique directories under the existing bounded D: candidate.

Rollback: discard adoption of this new adapter and retain the prior qualified candidate/contract. No runtime or production rollback is required. Do not delete archived failures or the frozen checker; no permanent elevated helper/service/task was installed.

## Exact future checker-integration proposal â€” OWNER REVIEW ONLY

1. Verify this archive/acceptance sidecar and the immutable legacy checker. Create a new versioned TEST checker candidate; retain legacy source, hashes and historical outcomes.
2. Add an explicit contract/version-selected entry point consuming the original stream/identity/image/native/CIM/health/cleanup artifacts. Unknown contracts fail; do not catch a legacy failure and silently route it through new policy.
3. Call the full read/verification pipeline, not merely trust `verificationStatus: PASS`. Reopen persisted segments and independent records; recompute class coverage, sequence and full-image/creation/parent/exit consistency. Require final archive-bound closure before combined acceptance.
4. Keep creator success, tracer-helper success, qualified post-exit helper disposition and failed helper evidence separate. Preserve raw CIM ambiguity and exact queue identity semantics.
5. Run negative fixtures plus directly affected legacy-checker regressions; require unchanged legacy outcomes. Preserve every failure.
6. Only with owner authorization, run a fresh small synthetic integration through that candidate checker, archive/hash-verify and stop. No automatic medium/large/protected/VM operation follows.

Further schema details and semantic-to-serialized identity mappings are in INTERFACE.md. No frozen-checker integration was performed in this pass.
