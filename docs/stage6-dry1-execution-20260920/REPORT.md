# Sacrificial Dry Run #1 — 2026-09-20

DRY_RUN_1_PASS, with the accompanying HASH_VERIFIED canonical archive receipt.

One attempt only: `D:\JARVIS-STAGE6-LIVE\b675935592fe41d48968e22be8cc6641\code\integrated-dry1-8c2cbaeef9d04a8080b9bcf22fae89cd`. No automatic retry, harness correction, timeout adjustment, production operation, protected VM access or Dry Run #2 occurred.

## Evidence summary

| # | Requirement | Result |
|---|---|---|
| 1 | Pre-run integrity | PASS: 73 candidate hashes, 223 application hashes unchanged; previous 1,886-member archive reverified. 215 recorded identities checked, no matching live or scoped diagnostic/VirtualBox process; no J6Kernel session. D: free approximately 1784.578 GiB. No previous integrated dry1 run existed. |
| 2 | Sacrificial artifacts | 12 existing .bin files, 1,073,786,880 bytes, exact approved source directory. |
| 3 | Hash pass #1 | PASS; 1.0592277 seconds. Actual bytes read and SHA-256 computed for all 12. |
| 4 | Hash pass #2 | PASS; 1.0322082 seconds. Independently reread all 12; hashes match pass #1. |
| 5 | Metadata preservation | PASS: preflight, run contract, both passes and post-run sizes/modification times agree. |
| 6 | Reconciled process identities | 19 — collector, hash worker, eight policy probes and associated console/helper descendants. |
| 7 | Application START | 19 independently captured and persisted for tracked identities. |
| 8 | Application STOP | 19 independently captured and persisted. |
| 9 | Kernel CREATE | 19. |
| 10 | Kernel EXIT | 19. |
| 11 | Retained-handle exits | 18. |
| 12 | Qualified post-exit acquisition | 1; unchanged strict cleanup rule. |
| 13 | Unexplained identities | 0; no PID reuse ambiguity. |
| 14 | Orphan helpers | 0; child/tree evidence reconciled and final identity check clear. |
| 15 | Maximum process lifetime | 2.9041293s across the tracked tree. Probe maximum kernel lifetime 0.0280315s; maximum policy-confirmed elapsed 0.0310244s. Observer infrastructure uses its existing separate bounds. |
| 16 | Hard-deadline violations | 0. Eight probes passed unchanged 13.6s policy and independent 15s observation. |
| 17 | Heartbeat | Maximum interval 1.0497771s; maximum observed age 1.0130661s; both below unchanged 10s. |
| 18 | External EventIdentifier collisions | 1 in this run. Existing collision protection unchanged. |
| 19 | Internal queue-ID collisions | 0. |
| 20 | Quiescence/finalization | PASS: 43 raw application events enqueued/selected/persisted/removed; residue 0. Independent subscriptions closed, native trace stopped/consumer joined. No event loss or duplicate persistence. |
| 21 | Durable finalization | PASS; actual fsync/flush and finalizer receipts verified. |
| 22 | Baseline-style manifest | Created only after verified lifecycle closure and durable finalization; contents match both hash passes. |
| 23 | Manifest SHA-256 | `6b2001e8aa218367feb94eb130f37fb45be89a8e3fb42ece28e58beb327406ab` |
| 24 | Archive verification | Dry-run archive: 40 members independently reverified; SHA-256 `e6a175fb21adb02a7a99e1bf457664ba8077644c644cd243a4de2bc51d5cd473`. Canonical campaign archive receipt separately records its full member count and hash. |
| 25 | Live-process cleanup | PASS: 239 prior/current identity observations checked; 0 matching live and 0 scoped diagnostic/VirtualBox processes. No forced termination. |
| 26 | Kernel trace cleanup | PASS: read-only enumeration returned success; 0 J6Kernel sessions. |
| 27 | Protected VM/config | NOT ACCESSED. No VirtualBox launch or protected hash/inventory/copy. |
| 28 | Production | UNCHANGED; 223 recorded application hashes match. All 73 candidate sources also unchanged. |
| 29 | Historical PID status | PID 13340/9240 causes UNCONFIRMED. Historical 87 helper gaps UNKNOWN. Prior kernel-only evidence remains kernel-only. |
| 30 | Final status | DRY_RUN_1_PASS. Stop before Dry Run #2. |

## Interpretation and preservation

The success conclusion uses actual hashes, native process identities/creation and exit records, independently persisted CIM lifecycle events, retained handles or strict post-exit proof, unchanged probe policy, final queue reconciliation, closed observers and verified archive bytes. It does not rely only on a launcher exit code.

Raw out-of-scope application notifications (5) and native infrastructure records are preserved, explicitly excluded from the tracked 19-identity equation, and included where applicable in final host cleanup checks. The live checker has no insufficient identities or per-identity errors. Kernel faults/loss/flush/stop/consumer status are all zero. All application subscription and durable-finalization checks passed.

The two hash passes are full logical reads and SHA-256 computations; no uncached physical disk-read claim is made. This pass demonstrates current Dry Run #1 acceptance under observed conditions, not a proven cause for historical Windows/storage/probe delays. Historical failed runs remain failed and untouched.

No new regressions were run because the harness was unchanged and this authorization was one acceptance dry run only. Source/application hashes and previous acceptance archive were reconciled. Synthetic input files were read only, and no API keys, environment files or paid providers were used. All live artifacts remained within the D: run; archival to canonical storage occurred only after monitoring and cleanup ended.

Rollback requires no production or VM action: preserve the run and stop using it if later review finds an issue. Do not delete or rewrite prior evidence. No commit was created. Stage 6 is not declared complete, and protected baseline capture remains unauthorized.

HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

See PROPOSED-DRY-RUN-2.md for the next procedure, OWNER REVIEW ONLY.
