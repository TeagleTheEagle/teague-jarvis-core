# Stage 6 synthetic dataset rehome and monitored collector result

**PROTECTED_COLLECTOR_STILL_DEFECTIVE**

Dataset rehome and preflight passed. The single monitored attempt failed; no retry or acceptance finalization occurred. No protected VM/configuration access, VirtualBox launch, production change, deadline change, security change, or real protected hashing was performed.

## Source and destination

- Old synthetic source: `D:\JARVIS-STAGE6-LIVE\1c1f5d0c390b42cc9ba9f4f6221dabc6\code\large-synthetic`
- Current approved workspace: `D:\JARVIS-STAGE6-LIVE\e23d36c0a24246c996aa28e5d5561863\code`
- New synthetic destination: `D:\JARVIS-STAGE6-LIVE\e23d36c0a24246c996aa28e5d5561863\code\large-synthetic`
- Copy evidence: `D:\JARVIS-STAGE6-LIVE\e23d36c0a24246c996aa28e5d5561863\code\rehome-1ae56ff933c9432b8e90ce326cb86c8c`
- Failed monitored run: `D:\JARVIS-STAGE6-LIVE\e23d36c0a24246c996aa28e5d5561863\code\protected-3148cf4d88354dd0aff4ec47ea0182ef`
- Calibration: `D:\JARVIS-STAGE6-LIVE\1c1f5d0c390b42cc9ba9f4f6221dabc6\code\calibration.json`; SHA-256 `8876f2fe62b3e4cf23f22289bf9f318acf1f8159da62d4912cec3d1a9f268753`.
- New dataset manifest: `D:\JARVIS-STAGE6-LIVE\e23d36c0a24246c996aa28e5d5561863\code\rehome-1ae56ff933c9432b8e90ce326cb86c8c\dataset-manifest.json`; SHA-256 `7ed9f3581dedd5ff391599c20b460f8090af57cd0d0b8fe8e4e0826babda1fb0`.

Normal exclusive file-level copying was used: no links, junctions, aliases, transformations or generated content. Each old file was hashed during copying and each destination was independently re-read. All 12 old/new/calibration hashes matched. Relative paths, sizes, modification timestamps, compression/encryption flags and directory structure matched; destination file identities are distinct and link counts are one. The old dataset remains in place. Copy plus independent destination verification took 1265.782 seconds.

The actual collector containment checks accepted the new dataset and rejected the old external path. All 12 canonical opened-file identities were verified. No dataset manifest routing points to the old source; provenance records intentionally retain the original path.

## Exact changes

Only validation configuration changed: `D:\JARVIS-STAGE6-LIVE\e23d36c0a24246c996aa28e5d5561863\code\baseline-allowlist.json` changes its exact synthetic root from old to new; `D:\JARVIS-STAGE6-LIVE\e23d36c0a24246c996aa28e5d5561863\code\run-source.json` updates that configuration hash. Real protected roots remain empty and realProtectedAccess remains false. Collector, guard, diagnostic executable code and thresholds did not change. Before/after hashes and original configuration bytes are in `configuration-change.json`, `allowlist-before.json`, and `run-source-before.json`. New copy/evidence/report scripts are confined to this report directory. No repository runtime or production files were edited.

## Failed acceptance and eventual cleanup are distinct

Probe PID 23408, creation FILETIME 134343831274954036, parent PID 9808, executable `D:\JARVIS-STAGE6-LIVE\e23d36c0a24246c996aa28e5d5561863\code\J6Probe.exe`:

- CreateProcess call: 0.0053532 seconds.
- Fixed deadline violation observed: 13.6024536 seconds after launch; handle remained unsignaled (258).
- Independent 15-second wait returned timeout, observed after 16.4830513 seconds. The configured limit was not increased.
- Kernel lifetime: 17.1945539 seconds. Eventual exit code 0 and signaled handle do not erase the failure.

Sampler PID 7712, creation FILETIME 134343831405852703:

- CreateProcess call: 12.0594708 seconds.
- Cleanup observation: 5.3665398 seconds; allExited=false and handleState=258, although Job active count was zero.
- The existing bounded sampler cleanup requested termination. Its eventual kernel exit code was 230, and independent retained-handle/START/STOP evidence subsequently proved exit. No additional manual termination was performed.
- This remains CLEANUP_FAILED at its original acceptance boundary. Later reconciliation does not retroactively pass it.

Hash pass #1 was cancelled by workload-stop after the probe failure. Its RuntimeError('Workload cancellation') and worker nonzero exit are preserved as secondary consequences. The exact underlying causes of both delays remain UNCONFIRMED. Their temporal overlap is evidence, not proof of a shared cause.

## Mandatory collector results

| Item | Result |
|---|---|
| 1. Dataset size | 59,665,402,098 bytes |
| 2. Files | 12 |
| 3. Largest file | base.vdi: 34,359,738,368 bytes |
| 4. Total monitored full-hash duration | Unavailable: no completed monitored pass |
| 5. Monitored pass #1 | Incomplete; cancelled after primary failure |
| 6. Monitored pass #2 | NOT RUN |
| 7. Complete-pass throughput | Not available; no invented measurement |
| 8. Hash equality | Copy old/new/calibration PASS; monitored two-pass equality NOT ESTABLISHED |
| 9. Source preservation | Both roots: all 30 metadata/ACL entries unchanged; file sizes/mtime unchanged |
| 10. Heartbeat | Maximum interval 1.0561466s; maximum age 1.0535403s; limit 10s |
| 11. Longest monitor stage | wait.event: 1.0553855s; timing overflow 0 |
| 12. Sampler | 7 queries; 6 available; 1 CLEANUP_FAILED; sampler thread eventually exited |
| 13. Tracked STARTs | 372 |
| 14. Tracked STOPs | 372 |
| 15. Tracked descendants | 371 plus collector = 372 |
| 16. Lineage ambiguity | 0; unexplained identities 0 |
| 17. Probe deadlines | 1 failure in 178 probes; independent observer also timed out |
| 18. Queue | 809 enqueued/selected/persisted/removed; remaining 0; max depth 28; external EventIdentifier collisions 4; internal queue-ID collisions 0 |
| 19. Finalization | Observer durable finalization PASS; collector acceptance finalization deliberately NOT RUN |
| 20. Manifest | Copy manifest verified; successful collector baseline manifest NOT CREATED |
| 21. Manifest SHA-256 | Copy manifest `7ed9f3581dedd5ff391599c20b460f8090af57cd0d0b8fe8e4e0826babda1fb0`; failed-evidence archive has its own receipt |
| 22. Archive | Separate failed-evidence archive verified; exact count/hash in archive-verification.json |
| 23. Cleanup | 343 retained-handle exits + 29 qualified post-exit cases; zero unexplained. All 375 recorded identities including launcher/observers absent by PID+creation time. Zero matching diagnostic processes/traces. Earlier sampler-boundary failure retained |
| 24. Collector hashes | 84/84 unchanged |
| 25. Diagnostic hashes | 96/96 unchanged; integration 100/100 matches launch manifest; only reviewed synthetic configuration binding changed before launch |
| 26. Historical delays | Probe-delay and heartbeat-delay causes remain UNCONFIRMED |
| 27. Protected VM/config | NOT ACCESSED; no new protected preservation hash claim |
| 28. Production | UNCHANGED by this task |
| 29. Protected-baseline eligibility | BLOCKED; real capture remains unauthorized |
| 30. Final status | PROTECTED_COLLECTOR_STILL_DEFECTIVE |

Two transient retained-tree image-query WinError 5 records were preserved. The unchanged strict checker reconciled these using identity-bound kernel images and retained exits; no rule was weakened. The general run-review records missing hash-pass-1.json because the pass never completed; this is expected absent evidence in a failed run, not a successful pass.

## Evidence, reused validation and rollback

Newly executed: copy/hash verification, actual canonical containment/open checks, all five historical archive verifications, host process/trace preflight, one monitored run, full independent exit reconciliation, metadata/ACL/source hash verification and archive verification. The old 131-member and 133-member dry-run archives, 1,333-member collector archive, 755-member hardening archive and 120-member blocked-run archive remain unchanged. They support historical failure-injection behavior only; they are not current monitored acceptance.

Previously validated code regressions (238 collector/integration tests; 117 diagnostic tests; 222 queue assertions and 10,000-event collision stress; bounded sampler cases) were not rerun unnecessarily. Frozen byte checks establish continued applicability to unchanged code. This new failed run is not reclassified by those earlier passes.

Rollback requires no runtime change: leave both synthetic datasets and failed evidence preserved. If explicitly requested later, restore only the two saved configuration files together after verifying they have not subsequently changed. Do not weaken containment or point the current collector at the old external dataset. No rollback, deletion or retry was executed.

Next owner review: diagnose the preserved probe runtime delay and sampler creation/cleanup delay from this exact run before another monitored attempt. Keep 13.6/15/10-second limits unchanged. No real protected-baseline procedure is executable or authorized from this failed status.

HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
