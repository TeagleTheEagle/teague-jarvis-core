# Stage 6 full dry-workflow harness integration — 2026-09-20

DRY_RUN_HARNESS_VALIDATED, with the accompanying HASH_VERIFIED archival receipt. This validates the TEST harness and miniature end-to-end run only. Dry Run #1 and #2 were NOT RUN. Stage 6 status was not advanced; protected baseline hashing remains unauthorized.

## Mandatory report

| # | Requirement | Result |
|---|---|---|
| 1 | Exact files changed | Seven new files in `D:\JARVIS-STAGE6-LIVE\b675935592fe41d48968e22be8cc6641\code`: dry_contract.py, dry_health.py, dry_hash_worker.py, dry_collect.py, dry_finalize.py, dry_launch.ps1, test_dry_integration.py. Existing 66 candidate files untouched. Report/preparation/regression/archive scripts are additional evidence tooling under this report directory. |
| 2 | Pre-change hashes | source-before.json lists all 66 exact prior paths/hashes; original-source-preservation.json confirms original and copied files unchanged. New files have no prior hash. final-source.json records all 73 final candidate hashes. |
| 3 | Original mode producer | launch.ps1:7; idle/disk/sustained/cpu/Dhash/dry workload labels. Historical file unchanged. |
| 4 | Original phase consumer | collect.py imports collect_hardened.py; collect_hardened.py:11 requires A-E diagnostic subset. Different semantics; no blind rename. |
| 5 | Canonical contract | Version-1 contract.json pins scenario, run ID, allowlisted input inventory and immutable thresholds. state.json owns ordered phases/history. Single writer per phase, explicit handoff at child/observer exit. DESIGN.md contains complete flow. |
| 6 | Compatibility | Old mode/letter-phase input rejected before observers. Historical entry points retained for reference and old tests; they are not the supported integrated dry command. No silent translation. |
| 7 | Workflow map | prepare/validate → both independent observers ready → hash worker + real policy probes → hash1 → hash2 → metadata → worker/probe closure → observer quiescence/closure → unchanged cleanup checker → fsync evidence → manifest/hash → archive verification → final metadata verification. |
| 8 | Dual evidence | PASS: 7 application START, 7 application STOP, 7 kernel create, 7 kernel exit. Independent CIM stream, ETW stream and retained handles, no synthetic lifecycle records. |
| 9 | D: containment | All active state/evidence/control/temp/manifest/archive paths under unique D: run. Mini input there too; full dry input is only the pinned pre-existing sacrificial C: directory. Protected/arbitrary/reparse inputs rejected. No environment change outside child process scope. |
| 10 | Focused tests | 30/30 PASS before miniature; 30/30 repeated in final regression suite. Tests include legacy contract, phase/stale rejection, hash/metadata, containment, failed lifecycle, primary error, flush/archive failures. |
| 11 | Miniature integration | MINIATURE_INTEGRATION_PASS. `D:\JARVIS-STAGE6-LIVE\b675935592fe41d48968e22be8cc6641\code\integrated-miniature-807c92300b9049e8b5bb553c15e41d5c`. 12 × 4096-byte synthetic artifacts = 49,152 bytes; no full-sized dry run. |
| 12 | Hash pass #1 | PASS: all 12 actual tiny files hashed. |
| 13 | Hash pass #2 | PASS: independently reread and hashed; all hashes/metadata equal. Both passes lie inside the independently recorded hash-worker kernel lifetime. |
| 14 | Lifecycle | 7 identities = 6 retained-handle exits + 1 strictly qualified post-exit acquisition; 0 unexplained identities. All children/helpers accounted by independent tree matching. |
| 15 | Heartbeat | PASS: max interval 1.0545855s; max hash-worker observed age 0.7489230s; max collector observed age 0.8858209s; fixed 10s limit unchanged. |
| 16 | Cleanup | PASS: both observers exited normally, retained handles closed, no primary failure. Probe count 2, max policy-confirmed duration 0.033001s, hard-deadline violations 0. |
| 17 | Finalization | PASS: independent application collector unsubscribed, quiescence completed, final drain empty; native trace stopped/consumer joined. Queue 19 enqueued/selected/persisted/removed, residue 0. Offline acceptance began only after OBSERVERS_CLOSED. |
| 18 | Manifest | PASS after CLEANUP_VERIFIED and durable FINALIZED. SHA-256 `dde92bcf5a831b3df88c812377bc7a590594750d7c96ec83b9db9e52fa7171c4`. |
| 19 | Archive | Miniature archive 40 members verified; SHA-256 `556b3a0d5023a5abef1847a68eebe44e2e3c56cda8c986f22ea2c53b944122ff`. Entire campaign/report archive separately copied/hash-verified to canonical database; see archive-verification.json. |
| 20 | Regressions | 201 unittest cases PASS: integration 30, dual 40, kernel 12, hardening 24, probe 26, monitor 69. Queue 222 assertions PASS including 10,000-event collision stress. Finalization 270 executed assertions PASS. Eight command groups exit 0. Actual counts retained rather than copied from previous runs. |
| 21 | Live processes | 0 matching live across 215 recorded identities from this and preceding campaigns; 0 scoped diagnostic/VirtualBox processes. No termination performed. |
| 22 | Trace sessions | 0 J6Kernel sessions; read-only enumeration succeeded. |
| 23 | Production | UNCHANGED: 223 recorded application hashes match. No JARVIS launch/provider/configuration change. |
| 24 | Protected VM/config | NOT ACCESSED; no inventory, hash, copy or VirtualBox launch. Invalid protected-path unit test rejects text before any filesystem access. |
| 25 | Dry Run #1 readiness | Harness entry point exists, contract consistent, candidate frozen, full sacrificial 12-file input available (1,073,786,880 bytes; metadata only inspected). Ready for owner review; live preflight must be repeated at actual execution. |
| 26 | Final status | DRY_RUN_HARNESS_VALIDATED. Stop before Dry Run #1. |

## Integration-test requirement coverage

H7.1/2: focused contract tests 1–3/22/30. H7.3/4/5: tests 4–6 plus actual miniature hash files. H7.6/7/8: actual miniature independent events, kernel worker lifetime and live heartbeat/liveness samples; mocks are not used for those conclusions. H7.9/10/11/12: live state history and observer exit receipts plus tests 9–12/23/26/28. H7.13/14/15: explicit failure tests 26, 11 and 27. H7.16/18: tests 13–16 and fixed source/containment checks. H7.17: actual 223-file preservation reconciliation. H7.19/20: tests 17–19/22/24. Detailed logs are in the D: integration-focused-1.txt and integration-regress directory.

The miniature native trace also records infrastructure outside the collector tree; those records remain in raw evidence and final identity inventory. Counts above are the reconciled collector/hash-worker/probe/helper tree, not raw machine-wide CIM counts. Out-of-scope notifications are retained, not counted as missing tracked events. The three evidence mechanisms are independent collection paths over the same Windows OS, not independent operating systems.

## Preserved scope, limitations and rollback

No accepted cleanup, EventIdentifier, queue, heartbeat threshold or probe deadline semantics changed. Original historical failures and previous archives remain unchanged. Fresh runs cannot explain historical PID 13340/9240 causes (UNCONFIRMED) or turn 87 historical helper gaps into known exits (UNKNOWN). HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Unit tests deliberately preserve expected injected failure artifacts. There was no failed miniature live run or hidden retry. Phase/writer integration is new TEST infrastructure; production runtime and accepted components are untouched. No acceptance commit was created.

The miniature proves integration, not large-file timing reliability. C: runtime/Windows executable dependencies remain; all critical live monitoring state is D:. Full-size hashing and the historical hard-deadline scenario remain unvalidated until the separately approved Dry Run #1 succeeds. Fresh preflight, sufficient free space, and the two known diagnostic UAC approvals are still needed then.

Rollback: discontinue the new D: candidate, preserving all its evidence, and retain the unchanged prior accepted diagnostic candidate. No production or VM restoration/deletion is required. Do not run historical launch.ps1 as an integrated dry run; only the documented dry_launch.ps1 entry point represents the new canonical contract.

See DRY-RUN-1-PROCEDURE.md for the exact reviewed command. It was NOT executed in this pass.
