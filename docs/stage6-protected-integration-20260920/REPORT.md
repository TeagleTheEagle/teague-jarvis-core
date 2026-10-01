# Protected-baseline collector integration — BLOCKED

Windows reported cancellation of the J6BaselineTrace.exe UAC launch before either observer or the monitored worker started. The single launch attempt was preserved; no reissue/retry occurred. No monitor/runtime defect is established by that cancellation. The candidate is implemented and component-tested, **not acceptance-validated**.

## Mandatory result

| # | Item | Result |
|---|---|---|
| 1 | Files changed | 11 new candidate source/config/binary files listed below; 73 existing files unchanged |
| 2 | Pre-change hashes | frozen-before.json records every original candidate hash; candidate-source.json records 84 final candidate hashes; adapter-diff.patch records the separate adapter changes |
| 3 | Old restrictions | dry_contract.source_for/inventory/validate: two fixed synthetic scenarios, exactly 12 .bin files, campaign90; dry_collect.main: actual campaign90; app_monitor and kernel_trace: monitor180 |
| 4 | New mode | Explicit protected_baseline entry points; deterministic recursive mixed-extension inventory; exact root allowlist; realProtectedAccess=false and no approved protected roots in frozen configuration |
| 5 | Read-only guarantees | Binary rb handles, final-path/volume/file-ID verification before reading, metadata checks, worker audit-hook mutation defense; no VirtualBox API or source writes in collector. This is not an OS sandbox against malicious native code |
| 6 | Containment | PASS component tests: traversal, unapproved roots, real VM/config rejection before access, duplicate paths, actual NTFS junction, hardlink and opened-handle escape |
| 7 | Measured throughput | 227.368 MB/s using slower complete logical hash pass; cache/volume effects remain relevant |
| 8 | Estimated two-pass duration | 524.835s for 59,665,402,098 bytes on measured synthetic D: workload; not a demonstrated C: duration |
| 9 | Proposed campaign | 1080s = ceil30(2 x estimated two-pass duration + 30s), synthetic candidate only |
| 10 | Proposed monitor | 1200s = campaign + 120s; both application and kernel bounds adjusted only in separate baseline adapters |
| 11 | Long-run monitor | NOT RUN; planned target 788s (1.5 x estimated two-pass duration) |
| 12 | Dataset | 12 synthetic files, 59,665,402,098 bytes, including 32/16/7GiB files and nested mixed extensions; no VM copy |
| 13 | Calibration hash pass 1 | PASS: 262.418s; no live-observer acceptance claimed |
| 14 | Calibration hash pass 2 | PASS: 261.031s; every SHA-256 matches; no live-observer acceptance claimed |
| 15 | Metadata | Calibration and final metadata unchanged for all 12 large dataset files; focused negative tests mutate only their own separate fixtures |
| 16 | Baseline-style manifest | Focused manifest/ordering checks passed; no large monitored baseline manifest exists |
| 17 | Failure injection | 37 new tests PASS; injected unreadable/evidence/archive/manifest/worker/observer/heartbeat/deadline failures plus real junction and source-mutation cases. No claim of live fault-injection acceptance |
| 18 | Protected-mode Dry Run #1 | NOT RUN |
| 19 | Protected-mode Dry Run #2 | NOT RUN |
| 20 | Max heartbeat | NOT MEASURED for new large mode; observers never started; historical approximately1.06s values are not reused as current evidence |
| 21 | Lifecycle reconciliation | No monitored workload started. Launcher returned failure; after-check found zero matching diagnostic/VirtualBox processes and zero diagnostic trace sessions |
| 22 | Archive | See accompanying archive-verification.json for exact count/hash; finalized preparation/failure evidence only, not successful large-run evidence |
| 23 | Cleanup | PASS for canceled launch: no diagnostic helper left running; no force termination |
| 24 | Protected VM/configuration | NOT ACCESSED |
| 25 | Production | UNCHANGED; 223 application hashes verified |
| 26 | Limits | Monitored long run, finite-bound validation and two large protected-mode dry runs are outstanding; C: throughput may differ; synthetic reads may be cached; real capture/topology reconciliation is not approved by this result |
| 27 | Protected-baseline eligibility | NOT ELIGIBLE |
| 28 | Final status | BLOCKED — UAC cancellation |

## Exact test results

{"baseline": 37, "dual": 40, "hardening": 24, "integration": 30, "kernel": 12, "monitor": 69, "probe": 26}; total 238 unittest cases passed. Queue 222 assertions passed including existing collision stress; finalization 203 assertions passed. Nine command groups returned0. Exact commands and outputs are archived. Safety thresholds remain heartbeat10s/probe13.6s/independent observer15s. No observed acceptance failure was hidden by increasing a threshold.

## Candidate additions

Candidate: `D:\JARVIS-STAGE6-LIVE\1c1f5d0c390b42cc9ba9f4f6221dabc6\code`

| Added file | Final SHA-256 |
|---|---|
| J6BaselineTrace.exe | d0e90a93a7d837928eed1d961ce7bed305e3a407d6828743d49ed272408837d0 |
| baseline-allowlist.json | 39eb9867e647974fa21499317aaeafd013bccc84e7c0b090dfc86c523250a281 |
| baseline-limits.json | ffdf8c8cfd0684cd4bf4433beb6bad076a547e65d405fca14d00feacbf74b45b |
| baseline_collect.py | c7d574dcca48efa9d5e5ffec91336b0db6e400d2c6393ac2add4656308d8c741 |
| baseline_contract.py | 386b5162f8dfc83b4a322250824f0177ba3d58cf1592ebe7f5e58d14933cd5ab |
| baseline_finalize.py | 9cbcd528310e7cbbafbfbdb41e0e19f302fdb62f3ba12d040ea9dacad8a4f3f5 |
| baseline_hash_worker.py | 46be070444eac9bfc6343e90cbf841f8b3f3e4a179987fa259998e0181f802c8 |
| baseline_kernel_trace.cpp | 8155ec139b293da695047ed6acc0a3ef41d9565b6f78eb0668ba4ff4070deac2 |
| baseline_launch.ps1 | d9bb7d98986c4355bd6bbd48b6096e8b76a208aee69c327ae583e5a22e79ef75 |
| baseline_monitor.ps1 | d20f963ebc634a084adc97ee227e7f8cf137c0fada470245cedc86e42c504b86 |
| test_baseline.py | ad3899bf721cfd599b380f8746ca1389c11d7f32e0701df779851ee1005da297 |

No original file in the old validated candidate or either old dry-run archive was modified. Test preparation/report scripts are separate under this report directory. The build emitted one inherited C4456 variable-shadow warning; compilation and Python/PowerShell syntax checks succeeded.

## Preserved preparation failures

`pre-live.json` records a report-only preflight self-match: its inline PowerShell command contained the candidate ID and matched its own broad process filter. No observer launched. `pre_live.ps1` now records/excludes its own process explicitly. `pre-live-large-validation.json` then passed. The frozen candidate was not modified by this reporting correction.

Failed launch directory: `D:\JARVIS-STAGE6-LIVE\1c1f5d0c390b42cc9ba9f4f6221dabc6\code\protected-4a00fe17ee1b454a9376fb5573b7b5c5`. Original launcher-error.txt and PREPARED state remain unmodified. Windows explicitly reported the UAC operation was canceled; neither observer readiness nor hash output exists. The post-cancellation check is `pre-live-post-cancel.json`.

## UAC reduction decision

Gate-wide elevated reuse is not supported by this architecture without a new lifecycle/control design. The native tracer binds to one root PID/creation time and output directory; Health binds run-specific observer identities; acceptance requires their shutdown and finalized streams. A persistent elevated broker would require changing those contracts. Following the owner's fallback instruction, preserve per-run diagnostic prompts. No UAC/security-policy/ACL change, persistent privileged service, broad command channel or elevated Codex session was introduced. No elevated helper remains from this canceled launch.

## Next action and rollback

When the owner is ready to approve the two diagnostic prompts, resume the first monitored synthetic large-data run in a fresh directory, preserving this cancellation. Do not count it as Dry Run #1. Recheck frozen hashes/processes/traces first. Then complete long-duration/large-data acceptance and both separately identified full dry runs under the approved stop rules. No real protected capture is eligible yet.

Rollback: retain all evidence, stop using the new candidate and select the untouched original sacrificial harness. No production/VM/ACL rollback is needed. Do not delete the approximately59.7GB synthetic dataset or historical evidence automatically.

HISTORICAL STAGE 1 CAUSE: UNCONFIRMED. Historical PID9240/13340 causes and prior storage stalls remain unconfirmed; this work does not reinterpret failed historical runs.
