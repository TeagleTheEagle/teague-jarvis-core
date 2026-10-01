# Final narrow ETW measurement successor — stopped at overhead screen

**MEASUREMENT_OVERHEAD_CONFLICT**

No live diagnostic, ETW session, UAC, medium/large validation, protected VM access or production operation occurred. No ETW settings, acceptance semantics, deadlines, queues or frozen checker were changed. Historical trace-loss cause remains UNCONFIRMED. Historical 21 AMBIGUOUS / 1 UNMATCHED remains unchanged. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

## Decision and actual results

The authorized early feasibility screen cannot establish the <=1% additional dispatcher-CPU budget reliably. Eight balanced enabled/disabled pairs used the **same executable**, replaying 16,000,000 synthetic callbacks through actual TDH property APIs for the unknown-parent START branch. Mean paired CPU increase: **0.753251%**. Paired t-based 95% interval: **-1.383468% to +2.889970%**; halfwidth **2.136719 percentage points**. This exceeds the predeclared precision allowance of one percentage point and includes overhead above budget. It does NOT prove overhead exceeds 1%; it fails to demonstrate compliance. The interval is a descriptive paired estimate, not a guarantee about independent host scheduling noise.

Disabled throughput: 487,673.741 callbacks/sec; enabled: 483,465.773 callbacks/sec (about 0.863% lower). Sampled maximum callback latency: 33.0 versus 107.2 microseconds. These are sampled maxima, not exhaustive maxima; the difference is not assigned a causal explanation. All trials consumed at least 2.0 seconds of dispatcher CPU. Peak process working set: 7,581,696 bytes. Additional counted C++ allocations: zero; baseline TDH-wrapper allocations remain in both modes. This allocator counter does not observe allocations internal to Windows libraries. No live queue or contention behavior was evaluated.

The explicit owner stop condition applies when overhead cannot be measured reliably. Further integration stopped. No repeat benchmark, timeout increase, configuration change or favorable trial selection was used. Full coordination timing, control-thread sampling, identity correlation, export, analyzer and the 38-case coverage requirements remain incomplete, NOT passed.

## Implemented subset / exact successor changes

Fresh successor: `D:\JARVIS-STAGE6-LIVE\a34f91e1db274bf78fc5a80e2a9d417c\code`.

Copied the 235 manifest-listed predecessor artifacts. Only these copied configuration files differ:

- `baseline-allowlist.json`: binds synthetic root to this fresh successor; protected-root list remains empty.
- `preservation-policy-v4.json`: binds candidate and evidence destination to this fresh successor.

New prototype sources:

- `loss_measurement_v3.hpp`: fixed-capacity lifecycle and coordination recorders; no callback file I/O, new lock, allocation or TDH lookup in the recorder. Local sequence denotes recorder continuity ONLY, not ETW completeness or acceptance authority.
- `loss_measurement_fixture_v3.cpp`: offline tests and same-binary feasibility benchmark; no ETW session operations.

New derived files: `J6MeasurementFixtureV3.exe`, `loss_measurement_fixture_v3.obj`. A copied predecessor manifest is retained as `predecessor-source-v3.json`; it is NOT a valid new live-candidate manifest. `candidate-artifact-manifest.json` in this report explicitly marks the partial successor INCOMPLETE_NOT_LIVE_ELIGIBLE.

No hooks were added to owned_entry.cpp, native_bridge.py, authority_trace_v3.cpp, startup_trace.cpp, helper_handoff_v1.hpp or loss_diagnostic_v2.hpp. No analyzer, full evidence schema or new accepted live binding was produced. Do not launch the partial successor.

Report-local tooling: prepare.py, screen.py, verify.py, archive.py, build-fixture.cmd; prototype copies, build logs, failed header snapshots, benchmark/test JSON, inventories, diff, census and review procedure are preserved here. The complete inventory and SHA-256 values are in candidate-artifact-manifest.json and the archive manifest. The diff includes all actual successor edits.

## Validation performed

- Build: `cmd.exe /d /c "<this report directory>\build-fixture.cmd"`; Visual Studio 2022 x64, C++17 /O2, TDH/Advapi/Psapi libraries. Third build PASS. First two builds FAILED due to the SDK `DUPLICATE` macro colliding with the enum name. Both failed logs/header versions remain preserved. Renamed the prototype enum member to DuplicateRecord; this does not alter existing observers.
- `<successor>\J6MeasurementFixtureV3.exe tests`: **13/13 PASS** (exit 0). Covers fixed-capacity recorder behavior, overflow/no overwrite, sequence, absent optional fields, allocation, LastError and basic duration accounting. These are NOT the full requested integration regressions.
- `<successor>\J6MeasurementFixtureV3.exe benchmark`: exit 0, 16 measured trials / 8 pairs; overhead screen CONFLICT. Executable SHA-256: `4938c85e2b4c5185e882683718ec2b7d38fa10ba6172c165da471f976d0ea70e`.
- Python orchestration: `C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -B <report>\screen.py`.
- Static capacity checks compile: one lifecycle recorder 1,441,824 bytes; coordination recorder 1,049,088 bytes; two lifecycle recorders + coordination + proposed 64KiB identity allowance total 3,998,272 bytes, under the proposed 6.1MiB ceiling. Final export buffers are unimplemented and not claimed validated.
- Python syntax checked using ast.parse without importing candidate code or writing bytecode; results recorded separately.
- Read-only host process census plus `logman.exe query -ets`: **0 matching processes / 0 matching trace sessions** at the recorded census timestamp. This is a point-in-time cleanup check, not continuous monitoring. Offline fixture exits independently recorded by the parent process wait.

## Preservation and archive

Postcheck: 760 frozen predecessor/evidence records match hash, size and modification time; 383 original historical evidence files match; 116 historical candidate files match. Five existing archives / 3,557 members were verified, plus the older 1,078-member historical archive. The frozen checker is unchanged. Preserved .vbox/VM/configuration files were deliberately not accessed to make this claim; preservation here means no operations targeted them.

New evidence is copied to a unique bounded canonical archive directory. The broad Sync-TeagueIndustries.ps1 would overwrite unrelated snapshots/document manifest; it is therefore not used for this narrowly scoped preservation action. Only this report and manifest-listed TEST candidate artifacts are archived. No environment files, keys, credentials, runtime database or protected VM content is included. See archive-receipt.json for exact archive path, SHA-256 and verified member count. Archive results are claimed only by that completed receipt.

## Rollback / next review

The predecessor remains untouched and available at `D:\JARVIS-STAGE6-LIVE\d45028a56e344926a311c04ba01f6a80\code`. No rollback execution is needed; do not use the incomplete successor for a live run. Retain this partial candidate and all failed evidence. No commit created.

Next proposed owner review: a more precise, bounded offline measurement protocol that can resolve a 1% difference without artificial baseline inflation, while covering additional real callback paths and eventual full instrumentation. No repeated benchmark or further implementation is authorized by this stopped action. The one-run procedure is conditional and NOT executable or eligible for approval until the overhead conflict and remaining implementation/tests are resolved.
