# Revised Stage 6 probe acceptance — sacrificial validation

Decision: **MONITOR_STILL_DEFECTIVE**, with canonical archival success established separately by the required `archive-verification.json` receipt. No protected baseline capture is authorized or performed. This is validation infrastructure acceptance, not Stage 6 completion.

## Blocking result — Dry Run #1

Dry Run #1 FAILED. Probe PID 9240 / creation FILETIME 134343506525182730 generated a slow warning at 5.008060 seconds. At 13.603420 seconds after launch request the retained handle was still nonsignaled (258), so the fixed 13.6-second policy failed closed. Its independent observer returned WAIT_TIMEOUT after 15.014988 seconds (15.017654 seconds since launch). A STOP callback was later recorded at launch +23.643717 seconds. This is callback timing, not a captured kernel exit time. Exact final lifetime and the underlying Windows cause remain UNCONFIRMED.

The monitor's largest recorded heartbeat gap was 9.574968 seconds; collector-observed maximum heartbeat age was 1.067545 seconds. Neither proves continuous sub-second health during finalization. The longest instrumented filesystem call in this failed run was journal.write 0.020536 seconds; uninstrumented delays must not be assigned a cause from that metric.

17 STARTs and 17 STOPs were preserved, but retained-handle closure did not satisfy acceptance. The monitor rejected the failed producer proof and exited 1. Finalization stopped at WAITING_FOR_PROCESS_EXITS; no SEALED/durable receipt, baseline manifest or manifest hash was created. The cancelled hash worker exited 1. Dry Run #2 was NOT RUN, as required. No retry or deadline increase was made.

The original hard-deadline error remains in probe-timings.json; cleanup overwrote the collector failure summary with an observer-timeout exception. The dry worker's cleanup stderr was not persisted. These reporting limitations are disclosed, not repaired in this stopped campaign. Full derived timeline: dry1-failure-timeline.json. Later zero-live-process checks do not retroactively cure failed retained-handle acceptance.

## 1. Exact files changed

Only a new validation candidate was created. Previous candidate/history files were not edited. Full before/after hashes and exact unified diff are in `changes.json`, `source-before.json`, `final-source-hashes.json`, and `source.diff`.

- `D:\JARVIS-STAGE6-LIVE\e863e012a81649fe9c82fce9838aa2e3\code\accept_run.py` — before `d00c26cc59ce87d60064c837b96956b7880d888e78f6a51dfeccc56820d79a1a`; after `e0fb3babb4266d5234cf8547729a65b6ac466d68c389b26268ee1a7ef37fbfbf`
- `D:\JARVIS-STAGE6-LIVE\e863e012a81649fe9c82fce9838aa2e3\code\collect.py` — before `9b7c686b5b1ac34c6be25c89ee121219247fd3437b7f654c0b3d520c290bc179`; after `992622fc2f92d249a12169f2186b11b32e9709c6ec9dfd1299f42d06d772ca42`
- `D:\JARVIS-STAGE6-LIVE\e863e012a81649fe9c82fce9838aa2e3\code\launch.ps1` — before `42062295bed3d72802f08d6341c050c73b00b7109f5780e492ff1f72639a4e15`; after `7404c9674a5f6b42a8e5affc47742b9ce87a868c965bb96aaae148ec2c703127`
- `D:\JARVIS-STAGE6-LIVE\e863e012a81649fe9c82fce9838aa2e3\code\monitor.ps1` — before `54ef5abd1f3db5ce4fe0a92609126a2df47c24fd81635b3f5bd26698d5d90c49`; after `06d2fa84f6320560503f9ade072fd526d4b49e60a8f463047fa57d620679e0cc`
- `D:\JARVIS-STAGE6-LIVE\e863e012a81649fe9c82fce9838aa2e3\code\probe_analysis.py` — before `1112ac400bbd9bf2d63593551fe42ce8f6b6e9f689998fd5c2d81e0f4fcbc1f2`; after `d235d75cb781d66e1bacf3be1ca2b72044b0141dce96d0b905cb90438ff6d601`
- `D:\JARVIS-STAGE6-LIVE\e863e012a81649fe9c82fce9838aa2e3\code\probe_policy.py` — before `NEW`; after `218bb5f61b27d0db4d6e50406e707811c29977a1e6604276e7e3c0fb394f6050`
- `D:\JARVIS-STAGE6-LIVE\e863e012a81649fe9c82fce9838aa2e3\code\probe_timing.py` — before `a5958953b2089bd375e81b20befada7d87cf7de1a9161871d1aa8758d8a1c74d`; after `0c295ada1c59de16ed958f56c6f954a31bfeec479a59746c976f6c1fe3e85b03`
- `D:\JARVIS-STAGE6-LIVE\e863e012a81649fe9c82fce9838aa2e3\code\run_probe_policy.py` — before `NEW`; after `c8009407e9a495a666f67364707ddfdc68a84e261f9bf25634822103056f6787`
- `D:\JARVIS-STAGE6-LIVE\e863e012a81649fe9c82fce9838aa2e3\code\test_probe_policy.py` — before `NEW`; after `22cffdc95a4fc2411b95af4c6093db0e63c99bf9780af677dcfb140c9f22ff38`

Report-only additions under `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-probe-acceptance-20260920`: plan/manifests, edit_candidate.py, summarize.py, make_report.py, archive.py, report/evidence JSON, source.diff, and PROTECTED-BASELINE-PROPOSAL.md. These are outside production code. No application runtime or Git acceptance commit changed.

## 2–5. Previous and revised rules; implementation

Previously the main probe wait used a locally selected five-second hard diagnostic limit. New runs use a five-second SLOW_PROBE_WARNING and a fixed 13.6-second launch-to-exit bound. The heartbeat remains strictly below ten seconds.

`Probe` records monotonic launch-request time before CreateProcess. `wait_tracked` uses the earlier of that time +13.6 seconds and the enclosing campaign deadline. Retained-handle waits use at most 50 ms slices with repeated publisher/subscriber/queue health and process-creation identity checks. Deadline checks do not reset after warnings, filesystem work, or waits. Delayed confirmation beyond the bound fails conservatively even if later evidence says the process exited earlier. A blocked API cannot be preempted by this Python loop; the separately running monitor and subsequent deadline check must still reject late confirmation.

Warning records include PID, creation time, monotonic timestamp, observed elapsed time, threshold and reason in D:-resident slow-probe-warnings.jsonl and probe-timings.json. Kernel FILETIME-to-QPC mapping is an estimate, not direct instruction/exit-initiation tracing. Exact kernel lifetime, monotonic launch/confirmation and bridge evidence are retained separately.

Warnings grant only ELIGIBLE_PENDING_LIFECYCLE. The unchanged finalization barrier plus validate_lifecycle require unique retained identities, normal exits, exact START/STOP, no residue, successful subscriber closure, durable flush, archive/hash verification. There is no retry or dynamic timeout extension.

## 6–7. Focused tests and regressions

- Revised policy: 26/26 tests PASS (boundary times, health, identity, handle, lifecycle, cleanup, archive/flush failure).
- Existing Python monitor regression suite: 69/69 PASS; errors 0, failures 0, skips 0.
- Exact EventIdentifier/queue regression: 222 assertions PASS; all 10,000 stress events enqueued, persisted and removed; zero loss/duplicates/internal collisions, 9,993 external-ID collisions handled.
- Late-event finalization gate: 171 assertions across 21 groups PASS. Assertion count includes scheduling-dependent polling; group coverage is unchanged.
- Python AST: 26 files PASS. PowerShell parse results in powershell-syntax.json. Syntax is not runtime acceptance.

## 8–18. Real-run results, lifecycles, collisions and finalization

| Run | Probes / START / STOP | >5 s warnings | Max lifetime s | Hard failures | Max heartbeat s | Result |
|---|---:|---:|---:|---:|---:|---|
| campaign-hash-2f7d38cff2c64d4cafc70a791c1fcf33 | 121 / 121 / 121 | 1 | 9.0607155 | 0 | 1.0967048 | PASS |
| cpu-10c7ab859365447f9038cdb6e627dff7 | 58 / 58 / 58 | 0 | 0.1021532 | 0 | 1.0858316 | PASS |
| dhash-aba7f8ffe7b24994a7f5b8ff41b787f8 | 87 / 87 / 87 | 0 | 0.1369691 | 0 | 1.146798 | PASS |
| dry1-e778870314ae4c3dbfc5274a9fb7a3d0 | 17 / 17 / 17 | 1 | None | 1 | 9.574968 | FAIL |
| hash1-b543dbc3509a4041a75db1cfa4b7f61c | 127 / 127 / 127 | 2 | 7.2973537 | 0 | 1.1220357 | PASS |
| hash2-857602f9b8b44a70bcec80b295013f92 | 107 / 107 / 107 | 2 | 6.2894358 | 0 | 1.1212441 | PASS |
| hash3-ebb12208ee9b47c6a5bd4656d3629c14 | 121 / 121 / 121 | 1 | 5.3202442 | 0 | 1.1656238 | PASS |
| idle-836ccf84cf4b4b5c9dc42080296df878 | 94 / 94 / 94 | 0 | 0.0329476 | 0 | 1.1047751 | PASS |
| reads-bf49470da544427c9cf3bc06b7776f68 | 96 / 96 / 96 | 1 | 6.4111175 | 0 | 1.17327 | PASS |

Real probes: 828; warnings: 8; hard-deadline failures: 1; maximum fully captured kernel lifetime among analyzed passing runs: 9.0607155 seconds; maximum heartbeat interval across all runs: 9.5749680 seconds. The failed probe exceeds the independent 15-second observer bound, but its exact kernel lifetime was not captured; 9.0607155 is NOT the overall lifetime maximum.
START total: 828. STOP total: 828. External EventIdentifier collisions: 18; internal queue-ID collisions: 0.
Each accepted run proves expected/callback/enqueued/persisted START and STOP counts in acceptance.json, with raw tap/event records. All run details, maxima, drain/filesystem timings, queue depth and finalization transitions are in workload-summary.json and original per-run evidence.
Final independent PID+creation-time checks: 854 records; unresolved/live matching identities: 0. Final host scan is in final-host-state.json. PID reuse is distinguished from a matching live process, never used to terminate an unrelated process.
Finalization uses the existing producer-close proof, retained exits, 4.6-second resettable event quiescence, 45-second bounded closure, exact queue drain, subscription close, durable flush and SEALED receipt. A finite empirical quiescence window is not a Windows delivery guarantee; expected lifecycle completeness remains mandatory.

## 19. Failure injection

PASS evidence includes exact/over-13.6 deadline and never-exits via the actual policy with an injected monotonic clock/handle; heartbeat/subscriber/queue/identity/handle failure; missing START/STOP; orphan/nonzero cleanup; warning write failure; monitor/finalizer failure; durable flush denial; archive copy/corruption and post-finalization hash corruption. Existing real subprocess consumer termination and finalizer crash tests remain included. Synthetic failures are expected negative tests, not erased failed campaigns. Do not describe simulated hard-deadline testing as a deliberately hung Windows process experiment.

## 20–23. Dry runs, durability and archive

Dry1 and Dry2 status is in the table. Each dry run must independently hash the same 12 fixed sacrificial `.bin` files twice, compare complete SHA-256/size/mtime inventories, generate baseline-style manifest and its hash, reconcile process lifecycle, seal durable evidence and verify the D: archive. No protected artifacts are substituted.

Eight successful workload/repetition runs reached durable finalization; Dry Run #1 did not. Archiving its failed evidence is preservation, not acceptance of that run. All canonical copying occurs after live monitors exited. Archive target: `C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 REVISED PROBE ACCEPTANCE 20260920`. `archive-verification.json` must say HASH_VERIFIED and match the complete ZIP/manifest SHA-256. Archive-copy failure prevents final acceptance regardless of all earlier passes.

## 24–29. Limitations, preservation and final disposition

- Underlying Windows storage/driver and intermittent probe runtime causes remain UNCONFIRMED. The provisional 13.6-second bound is empirical, not a guaranteed Windows property. New slow probe results do not explain historical incidents.
- Historical failures remain unchanged, including the original five-second failures and the prior missing STOP/finalization failures. The new rule applies only to this candidate's new runs. Prior candidate source preservation and historical archive checks are recorded separately.
- Protected VM/configuration: NOT ACCESSED. No protected hashing, topology reads, configuration edits, VM operations or VirtualBox launch were performed. Existing monitoring asserts zero VirtualBox starts, and final host evidence is retained. Production JARVIS: UNCHANGED by this work; no Core/provider operations or application edits.
- Live state remains D:-bounded, with containment/reparse/traversal tests and per-process TEMP/TMP. Installed interpreter/OS binaries still load from C:; C: sacrificial reads/hashes are intentional. No claim that Windows itself performs zero C: I/O.
- Protected-baseline eligibility: NOT ELIGIBLE. Dry Run #1 failed; Dry Run #2 is not run. Capture remains UNAUTHORIZED. PROTECTED-BASELINE-PROPOSAL.md is a conditional, unexecuted draft and is not a recommendation to start capture now.
- Report preparation errors are preserved: historical archive filename lookup corrected to review-evidence.zip; a read-only check before UAC completion found no heartbeat yet; restricted-context final CIM enumeration was denied and its empty output is explicitly unreliable. Successful host-context enumeration and identity rechecks supersede that failed diagnostic output. Existing historical archives hash-match their preserved values.
- HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Final requested status: **MONITOR_STILL_DEFECTIVE**. STOP. Next owner review should address the newly reproduced >13.6-second probe and the cleanup evidence limitations; do not rerun dry tests, extend deadlines or start protected capture without that review.

## Commands and rollback

Exact source paths, executable hash identity and per-run config/source-hashes are preserved. Commands:

```powershell
& 'C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\.venv\Scripts\python.exe' -B 'D:\JARVIS-STAGE6-LIVE\e863e012a81649fe9c82fce9838aa2e3\code\run_probe_policy.py'
& 'C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\.venv\Scripts\python.exe' -B 'D:\JARVIS-STAGE6-LIVE\e863e012a81649fe9c82fce9838aa2e3\code\run_focused.py'
```

PowerShell host `C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe` ran `-NoProfile -File` with `D:\JARVIS-STAGE6-LIVE\e863e012a81649fe9c82fce9838aa2e3\code\test_queue.ps1` and `D:\JARVIS-STAGE6-LIVE\e863e012a81649fe9c82fce9838aa2e3\code\test_finalization_gate.ps1`. Each real run used `D:\JARVIS-STAGE6-LIVE\e863e012a81649fe9c82fce9838aa2e3\code\launch.ps1` with modes/durations in workload-summary.json; idle used Cluster 8, others default1. The monitor alone requested read-only elevation.

Rollback: do not delete evidence. Retire this unique candidate after confirming no matching retained processes remain. The prior 37-file candidate is still intact and hash-verified; selecting it restores the previous diagnostic tooling, not acceptance under the revised policy. Do not reuse old run directories or relabel their results. No production restoration, security setting change, database migration, or Git reset is required.
