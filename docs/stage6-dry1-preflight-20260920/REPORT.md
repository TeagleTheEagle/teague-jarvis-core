# Dry Run #1 preflight — BLOCKED

2026-09-20. No monitor, probe, workload, Core or VirtualBox process was launched. No UAC prompt was issued. Dry Run #1 has NOT RUN; this is not a failed dry run and not a regression of the validated cleanup rule.

## Exact blocker

Accepted candidate: `D:\JARVIS-STAGE6-LIVE\a0e59a0a26ca41d3885c6c6b0e3d7a25\code`.

1. `launch.ps1:7` writes `case.json` containing `mode`, not `phase`; line 12 launches the elevated monitor and line 15 invokes `collect.py`.
2. `collect.py:2` imports `collect_hardened`.
3. `collect_hardened.py:11` immediately reads `config['phase']` and restricts it to A-E. This occurs before its main try/finally. The current dry-launch configuration is therefore statically incompatible and would raise KeyError before collection/cleanup initialization. It was not executed to reproduce an already-demonstrable contract mismatch.
4. `dual_launch.ps1` supplies the independently validated application + kernel observers and invokes `cleanup_checker.py`, but runs only `stress.py`. It does not run the baseline-style two-pass hashing/manifest workflow. That stress run cannot be substituted for Dry Run #1.
5. `cleanup_checker.py` reads actual stress-specific producer and observer evidence including `stress-result.json`. The older dry acceptance path neither produces this dual evidence nor invokes this checker. Renaming output or manufacturing events is not a valid integration.

Exact numbered source excerpts and hashes are preserved in `preflight.json`. All 66 accepted candidate hashes match, so this is a pre-existing integration gap between accepted components, not unexpected source drift. The prior cleanup-checker validation remains valid within its documented sacrificial scope.

## Minimum proposed correction — not implemented

Add a bounded TEST dry-run orchestration/collector adapter, preferably new files alongside an isolated candidate copy, that:

- invokes the existing `dry_worker.py` against only the 12 pre-existing sacrificial .bin artifacts;
- uses the unchanged approved probe policy (13.6-second hard deadline and 15-second independent observer), heartbeat threshold (10 seconds), D-only live paths and primary-error preservation;
- starts the accepted independent application collector and native kernel observer before creating tracked work, and captures genuine producer/parent/child/retained-handle records compatible with the validated checker;
- holds final acceptance until hashing, metadata preservation, both independent lifecycle streams, strict cleanup reconciliation, bounded finalization and durable archive verification all pass;
- safely finalizes observers on configuration, launch, collection or acceptance failure without converting primary failures into passes.

Likely new files: `dry_acceptance_launch.ps1`, `dry_acceptance_collect.py`, `test_dry_acceptance_wiring.py` (names proposed only). Existing validated checker, probe policy, queue correction and timeout constants should remain unchanged. If source changes beyond this adapter are needed, review their exact diff before use.

Focused validation before the one real dry run: configuration compatibility checked before any monitor starts; actual observer startup/cleanup and source manifests; real producer/worker evidence mapping without synthetic lifecycle events; missing stream/failed worker/deadline/cleanup failure rejection; original error preservation; accepted source hash verification. Do not use another stress test as Dry Run #1.

The current authorization is to execute the accepted candidate and stop on a failed pre-run check. Gate F requires unchanged candidate source except validation outputs. This report therefore requests review of the above narrow harness integration rather than modifying that candidate under execution-only approval. No Windows/runtime/production/security correction is proposed.

Rollback: retain the current accepted candidate and archive unchanged; discontinue any future separate adapter candidate if validation fails. No production rollback, file deletion or protected VM action is required.

## Mandatory report

| # | Requirement | Result |
|---|---|---|
| 1 | Pre-run integrity | Source/evidence integrity PASS; executable dry-run integration BLOCKED. 66 candidate hashes unchanged; previous archive 1,147 members verified. |
| 2 | Synthetic artifacts | 12 existing .bin files; 1,073,786,880 bytes. Metadata inventoried only. D: free 1,784.586 GiB at inspection. No new run workspace created/reused. |
| 3 | Hash pass #1 | NOT RUN. |
| 4 | Hash pass #2 | NOT RUN. |
| 5 | Metadata preservation | Pre-run sizes/modification times recorded; no workload executed; before/after dry-run proof NOT RUN. |
| 6 | Total run process identities | NOT RUN; no diagnostic campaign processes launched. |
| 7 | Application START | NOT RUN. |
| 8 | Application STOP | NOT RUN. |
| 9 | Kernel CREATE | NOT RUN. |
| 10 | Kernel EXIT | NOT RUN. |
| 11 | Retained handle count | NOT RUN. |
| 12 | Post-exit acquisition count | NOT RUN. |
| 13 | Unexplained identities | Current dry-run reconciliation NOT RUN; no PASS inferred. |
| 14 | Orphan helpers | Current snapshot: zero scoped diagnostic processes; no current run helpers created. |
| 15 | Maximum process lifetime | NOT MEASURED. |
| 16 | Hard-deadline violations | NOT TESTED; no threshold changed. |
| 17 | Maximum heartbeat | NOT MEASURED. |
| 18 | EventIdentifier collisions | NOT MEASURED. |
| 19 | Internal queue-ID collisions | NOT MEASURED. |
| 20 | Finalization/quiescence | NOT RUN. Existing evidence is not reused as current acceptance. |
| 21 | Durable finalization | Dry-run finalization NOT RUN. Preflight evidence archived separately. |
| 22 | Baseline manifest | NOT CREATED. |
| 23 | Baseline manifest SHA-256 | N/A. Separate preflight archive manifest hash appears in archive-verification.json. |
| 24 | Archive verification count | Prior accepted evidence: 1,147 members verified. New preflight report archive: see its HASH_VERIFIED receipt. No dry-run archive created. |
| 25 | Live-process cleanup | 203 known prior creation identities checked; zero matching live, zero scoped diagnostic/VirtualBox processes. No termination performed. |
| 26 | Kernel-trace cleanup | Read-only ETW enumeration succeeded; zero J6Kernel diagnostic sessions. No session started/stopped by this pass. |
| 27 | Protected VM access | NONE. No protected VM/configuration inventory, hashing or VirtualBox operation. |
| 28 | Production | UNCHANGED. 223 recorded application hashes match. No runtime launch or edit. |
| 29 | Historical PID status | 13340/9240 causes UNCONFIRMED. Historical 87 helper gaps UNKNOWN. Prior 97-process run remains kernel-only. |
| 30 | Final status | BLOCKED — accepted components lack a compatible complete dry-run entry point. |

No Dry Run #2. No protected baseline hashing. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
