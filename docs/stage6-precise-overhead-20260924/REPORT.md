# Precise offline measurement-overhead benchmark

**MEASUREMENT_OVERHEAD_CONFLICT**

The original recorder/fixture binary, all callback code, instrumentation fields, record capacity, locks, sampling and file/queue behavior were unchanged. No build, live ETW session, UAC, broader integration, protected VM access, production operation or deadline change occurred. This is an offline diagnostic-overhead screen only, not Stage 6 acceptance or proof of live non-perturbation.

## Primary result

Predeclared maximum: 32 batches x 8 balanced pairs = 256 pairs. Completed: 32 batches / 256 pairs / 512,000,000 recorded callbacks. AB pairs: 128; BA pairs: 128. Warm-up and pilot excluded. Fixed campaign duration: 1082.375 seconds. No extra trials, retries, ordinary-noise exclusions or result-dependent stopping.

Mean paired dispatcher CPU increase: **+1.400073%**. Primary two-sided 95% interval: **[+1.191267%, +1.608880%]**. Upper bound must be <=+1.0%. Halfwidth: 0.208806 percentage points. Interpretation: **point estimate above budget and lower confidence bound above budget**.

For pair i: d_i = 100*(CPU_enabled_i/CPU_disabled_i - 1), using the fixture's Windows GetThreadTimes kernel+user CPU counters and equivalent callback counts. Each batch mean is the average of its eight d_i. Primary interval = mean(batch means) +/- 2.0395134463964077 * sampleSD(batch means)/sqrt(32), df31. Neighboring pairs are not treated as independent in the primary interval. Batch SD: 0.579151; standard error 0.102380 percentage points.

Supplementary unclustered paired interval: [+1.155200%, +1.644946%]; not substituted for primary. Descriptive lag-1 correlation of batch means: 0.08622035017526543. The t interval assumes adequately independent/stable batch means and cannot eliminate systematic host bias. No confidence claim identifies the historical ETW mechanism.

Every pair's disabled CPU, enabled CPU, absolute difference (100ns), percent difference, order and callback count is in pairs.json. All trial JSONL, process/thread identities, creation and exit FILETIMEs, retained-handle wait results and final CPU counters are archived. All 32 fixture processes exited with code 0 and retained handles closed without reported errors.

## Secondary observations

| Metric (units in label) | Disabled mean | Enabled mean | Paired change and batch 95% interval |
|---|---:|---:|---|
| throughput | 477778.563711 | 470880.725022 | -1.427135% [-1.654898, -1.199373] |
| processCpuSeconds | 2.086914 | 2.115723 | +1.400073% [+1.191267, +1.608880] |
| wallSeconds | 2.093750 | 2.124428 | +1.482663% [+1.243531, +1.721795] |
| sampledMedianLatencyUs | 2.107812 | 2.105859 | -0.073982% [-0.280065, +0.132101] |
| sampledP95LatencyUs | 2.285156 | 2.334375 | +3.050954% [+1.350288, +4.751620] |
| sampledP99LatencyUs | 2.891406 | 2.923047 | +1.823416% [+0.562096, +3.084735] |
| sampledMaximumLatencyUs | 20.921875 | 24.081250 | +79.983875% [+45.277494, +114.690256] |
| cumulativePeakWorkingSetBytes | 7575888.000000 | 7576192.000000 | +0.004034% [-0.001528, +0.009597] |
| cppAllocationCount | 4000000.000000 | 4000000.000000 | +0.000000% [+0.000000, +0.000000] |

Intervals excluding zero (observed shifts, not a newly invented materiality threshold): throughput, processCpuSeconds, wallSeconds, sampledP95LatencyUs, sampledP99LatencyUs, sampledMaximumLatencyUs. Inspect these alongside the primary result; no secondary metric substitutes for dispatcher CPU. Per-trial sampled maximum latencies and all raw values remain available; maxima are not exhaustive. Process memory high-water is cumulative within a process. C++ allocation counts exclude internal Windows allocations. No queue, contention, coordination integration or live ETW behavior was exercised by this unchanged fixture.

## System and identity

AMD Ryzen 7 3700X 8-Core Processor; 16 logical processors; Windows reported 10.0.26200.0. No affinity, priority, power, BIOS, scheduler or security settings changed. Exact OS/context is in preflight.json. A restricted-context WMI read was denied before benchmarking; the ordinary host-context read-only census succeeded. No Windows elevation or UAC was used.

Executable: `D:\JARVIS-STAGE6-LIVE\a34f91e1db274bf78fc5a80e2a9d417c\code\J6MeasurementFixtureV3.exe`.

SHA-256: `4938c85e2b4c5185e882683718ec2b7d38fa10ba6172c165da471f976d0ea70e`. Existing Visual Studio 2022 x64 C++17 /O2 executable; no rebuild. Its source/header hashes are preserved in the previous candidate manifest and reverified. Orchestrator runs with the existing bundled Python and uses CreateProcessW with flags=0, original candidate CWD, inherited environment, stdout/stderr redirected to the fresh D: evidence directory and NUL stdin. No credentials or environment values were printed. Primary thread identity comes directly from the returned creator handle; benchmark CPU comes from that executable's unchanged GetCurrentThread accounting.

Commands executed: bundled Python `-B <report>\preflight.py`, `-B <report>\benchmark.py`, then `-B <report>\analyze.py`. The harness launches exactly `<unchanged fixture> benchmark` once per batch. `finish.py` performs preservation, syntax and archive verification after measurement. No fixture tests or calibration were rerun unnecessarily.

Invalid conditions were predeclared (API/harness error, count/order mismatch, malformed output, interruption, drift or watchdog). Exclusions: **0**. Harness errors: **0**. Ordinary noisy samples retained. One fixed 300-second batch watchdog / 2400-second campaign watchdog belongs only to this offline harness; neither changes Stage 6 deadlines, and neither triggered.

## Preservation / cleanup / limitations

240 candidate files unchanged; 760 predecessor/evidence files unchanged; 383 historical evidence files unchanged; 116 historical candidate files unchanged; historical archive unchanged; previous 275-member archive hash-verified and its original inputs unchanged. Frozen checker unchanged. Historical 21 AMBIGUOUS / 1 UNMATCHED unchanged. Historical trace-loss cause remains UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Final point-in-time read-only host census: **0 matching diagnostic processes / 0 matching trace sessions**, timestamp 2026-09-23T23:40:26.9836569Z. No VirtualBox process observed. Protected files were deliberately not opened or hashed; this action did not target them. Production was not accessed or modified.

Only new offline harness/report/evidence files were created in this report directory and `D:\JARVIS-STAGE6-LIVE\precise-overhead-20260924-4b0db487`. No existing candidate or implementation file was edited. Full identities/hashes and raw records are in the archive. The broad project sync script is not used because it overwrites unrelated records; a unique bounded nonsecret canonical archive is created. No prior archive or evidence is overwritten. See archive-receipt.json for exact archive path/hash/member verification. No commit.

## Owner review / next action

STOP after this benchmark. If the screen passes, the remaining separately reviewed step is to complete the still-unimplemented creator identity timing, both observer taps, coordination/control-thread measurements, bounded export/analyzer and required integration tests, then measure the full instrumentation; this subset screen alone cannot approve that integration or any live run. If the threshold is not established or conflicts, review the raw result and precision/overhead distinction before any further benchmark or optimization. No more trials will run automatically.

Rollback: no existing implementation changed. Retain this evidence and continue to treat the partial successor as incomplete and NOT LIVE ELIGIBLE.
