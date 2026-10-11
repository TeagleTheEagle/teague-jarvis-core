# Sacrificial Dry Run #2 — 2026-09-20

DRY_RUN_2_PASS, subject to the accompanying HASH_VERIFIED canonical archive receipt.

One fresh execution; no retry. The frozen workflow's existing selector remains `dry1` and raw receipt remains `DRY_RUN_1_PASS`. `campaign-intent.json` explicitly identifies this independent execution as campaign ordinal 2. No raw receipt was renamed or rewritten. Fresh observers and process identities were verified against Dry Run #1.

| # | Required evidence | Result |
|---|---|---|
| 1 | Run ID | `integrated-dry1-3d6ec5d9bd3643968a24f639a03ebe05` |
| 2 | Sacrificial files | 12; 1,073,786,880 bytes |
| 3 | Both hash passes | PASS: 1.1171335s and 1.0985375s; every SHA-256 matches |
| 4 | Source metadata | PASS: sizes/modification times agree before, during and after |
| 5 | Reconciled identities | 21 |
| 6 | Retained-handle exits | 18 |
| 7 | Qualified post-exit cases | 3; existing strict rules satisfied |
| 8 | Unexplained identities | 0; no checker errors |
| 9 | Orphan/helper result | PASS: all tracked descendants reconcile; zero orphan helpers |
| 10 | Deadline violations | 0; 9 probes satisfy unchanged 13.6s/15s rules |
| 11 | Maximum heartbeat interval | 1.0597656s; maximum observed age 1.0141441s; below unchanged 10s |
| 12 | START/STOP reconciliation | Application 21/21; kernel CREATE/EXIT 21/21 |
| 13 | Finalization | PASS: 49 raw events enqueued/selected/persisted/removed, residue zero; durable finalization PASS |
| 14 | Durable manifest | PASS; SHA-256 `3dffc8b2200659de021ed8dbde5591f3dae8464917c2839fccbcf8237b501ffe` |
| 15 | Archive | Raw run archive: 40 members verified. Complete canonical campaign archive count/hash recorded in archive-verification.json |
| 16 | Final cleanup | 265 known identity observations checked; zero matching live identities/processes, zero scoped diagnostic/VirtualBox processes, zero J6Kernel trace sessions |
| 17 | Protected VM/configuration | NOT ACCESSED; no protected hashing, inventory, copying or VirtualBox launch |
| 18 | Production | UNCHANGED; 223 recorded application hashes unchanged |
| 19 | Candidate source | 73 hashes unchanged; no harness/deadline correction |
| 20 | Proposed next procedure | PROPOSED-PROTECTED-BASELINE.md — OWNER REVIEW ONLY; not executed |

Full run directory: `D:\JARVIS-STAGE6-LIVE\b675935592fe41d48968e22be8cc6641\code\integrated-dry1-3d6ec5d9bd3643968a24f639a03ebe05`.

Preflight reverified Dry Run #1's 131-member canonical archive and its original source files. Final archival repeats that preservation check. Existing sacrificial input bytes were read again; mutable state, observers, events, contracts and output evidence were fresh. All live artifacts remained on D:. Canonical archival occurs only after observers and live collection have closed.

Maximum tracked process lifetime: 3.2447650s. Maximum probe kernel lifetime: 0.0268098s; maximum policy-confirmed elapsed: 0.0296607s. External EventIdentifier collisions: 1; internal queue-ID collisions: 0. The existing exact-entry collision protection remains unchanged.

The 7 out-of-scope application notifications and native observer/infrastructure records remain preserved and explicitly excluded from the tracked identity equation. Relevant identities were included in the final host check. The cleanup checker's raw `acceptance:false` is its diagnostic-only scope marker, not a failed verdict: `status:PASS`, no errors, and the integration finalizer separately verifies every dry-run acceptance condition. No kernel lifecycle evidence was synthesized from retained handles.

Raw run archive SHA-256: `54ca4220464bfe5fe849643771c6e55f1db854a4e0c7b5d6fd02274b4db9fe06`. The full campaign archive additionally contains report/check scripts, receipts and frozen candidate source snapshots.

## Limits and preservation

This is one successful independent sacrificial repetition, not proof that historical delays were explained. Full logical reads were hashed; no uncached physical disk-read claim is made. The approximately 1 GiB input does not prove that the protected approximately 55.6 GiB tree will fit the current fixed collector/monitor bounds.

Historical failed runs remain failed. PID 9240/13340 causes remain UNCONFIRMED; historical 87 helper gaps remain UNKNOWN. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

No additional regression campaign was run: the user authorized this single dry run with the validated harness unchanged. Existing regression results were preserved, not relabelled as newly executed tests. No paid providers, credentials, production runtime, VM or normal VirtualBox configuration were used. No commit was created.

Rollback requires no runtime, production or VM changes: retain the evidence and discontinue use of the candidate if later review identifies a defect. Do not delete earlier runs.

Stage 6 is not declared complete. Protected baseline capture remains unauthorized. STOP for owner review.
