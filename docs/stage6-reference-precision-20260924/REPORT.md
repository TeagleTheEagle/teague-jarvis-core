# Component-attribution reference precision only

**REFERENCE_PRECISION_NOT_ESTABLISHED**

Reference fixture and all existing callback/recorder/harness code remain unchanged. No rebuild, selftest or component-attribution mode ran. No UAC, live ETW, observer integration, optimization, production or protected VM operation occurred.

## Fixed design

16 reference processes x 40 balanced pairs = **640 pairs / 1,280 measured arms / 1,280,000,000 measured callbacks**. Each arm: 1,000,000 useful callbacks and the binary's unchanged, excluded 20,000-callback warm-up. Total excluded warm-up work: 25,600,000 callbacks. Actual AB pairs: 320; BA: 320. Ordinary noisy trials retained; **0 exclusions / 0 retries / 0 harness errors**. Elapsed 2813.110 seconds.

The fixture hardcodes callback count and has no command-line option to increase it. Rebuilding would change the required reference, so precision was improved through bounded repetition of the existing executable. Original launch() source executes unchanged via runpy. A new outer path-view adapter only routes raw outputs into fresh per-batch D: directories; executable path, CWD, process flags, warm-up, CPU accounting, trial ordering and callback semantics remain original. No observer/provider/buffer/queue/deadline changes. The original 1,200-second offline launcher bound stays unchanged; the outer 5,400-second budget only stops additional launches, and did not trigger.

The target was predeclared **95% half-width <=0.25 percentage points**, a profiling prerequisite, not the <=1% overhead acceptance screen. Prior group variance predicted about 0.19 points under stable conditions; this was not a guarantee. No interim estimate controlled stopping. All 16 batches completed before analysis.

## CPU and compatibility

Primary paired CPU increase: **+1.179679%**.

95% interval: **[+0.913629%, +1.445728%]**.

Half-width: **0.266049 percentage points**; target met: **False**.

Compatibility classification: **NOT_CLASSIFIED_UNTIL_PRECISION_SUFFICIENT** against preserved [1.191267%, 1.608880%]. Interval overlap: True. A different point estimate alone is not a reproducibility defect. Compatibility is evaluated only when precision is sufficient. This reference result does not itself clear the <=1% diagnostic overhead screen or approve integration.

Per pair: d = 100*(FULL thread CPU / BASELINE thread CPU - 1), using existing Windows GetThreadTimes kernel+user counters. CPU is not inferred from wall time. Calculate t95 across 16 batch means (df15, 2.131449545559) and across 128 adjacent five-pair group means (df127, 1.978819534681). Use the larger half-width about their common equally weighted mean. Batch half-width 0.266049; five-pair-group half-width 0.247804. This conservative envelope covers both chosen variance groupings; it still assumes sufficiently stable, independent groups and does not bound systematic host bias.

Raw per-pair baseline/full CPU, absolute CPU difference, percentage delta, ns/callback and actual order are in pairs.json and order.json. Original raw trial output and creator-handle-derived process/main-thread identities are archived without alteration.

| Supplementary measure | Result |
|---|---:|
| Baseline average ns/callback | 2117.309570 |
| Full average ns/callback | 2141.308594 |
| Paired added ns/callback | +23.999023 [+18.325553, +29.672494] |
| Throughput paired change | -1.282357% [-1.630972, -0.933742] |
| Process CPU paired change | +1.183177% |
| Wall-time paired change | +1.422137% |
| Individual-pair SD | 3.098037 percentage points |
| Batch lag-1 correlation, descriptive | 0.20665106198976577 |
| First eight batch mean | +0.959113% |
| Last eight batch mean | +1.400244% |

No supplementary metric substitutes for the approved dispatcher CPU measure. No noisy trial was deleted or reclassified because of its value. Existing sampled callback latencies, allocation counts and process high-water remain in raw records; no new profiler was enabled.

## Identity and verification

Existing executable: `D:\JARVIS-STAGE6-LIVE\component-attribution-20260924-7f29a680\J6AttributionFixture.exe`.

SHA-256: `e3fd0f58ab7f37093791c4eb55a4c20b8984bfc7b2ba9e363ac32b3cb995a0b9`.

The original full-reference callback's compiled object instructions match the original benchmarked callback before measurement; their preserved hash is 53c4ff14c74d2c5696732ab28dea7d8d79cae60714e074a846c3efd67d7199f1. Original source/header/object/executable, compiler/link command, build log and launch harness hashes remain unchanged afterward. No rebuild. Only new outer orchestration/calculation/report files were created in this report directory and fresh evidence under `D:\JARVIS-STAGE6-LIVE\reference-precision-20260924-9f34d820`. Exact hashes are archived.

Machine context comes from preflight-census.json: AMD Ryzen 7 3700X / 16 logical processors, reported Windows 10.0.26200.0. No affinity, priority, scheduler, power, security or environment settings changed. Existing executable and working directory preserved. The original launcher retains process and main-thread handles, verifies creation identities, observes exit and closes handles; all 16 processes returned exit code 0. No process-name/PID-only substitution supplies the recorded identity.

Commands: bundled Python `-B <report>\preflight_check.py`, `-B <report>\repeat_reference.py`, `-B <report>\analyze_reference.py`, `-B <report>\finalize.py`. Every fixture invocation is exactly `J6AttributionFixture.exe reference`. No invocation of selftest, attribution, CLOCK_ONLY, STORAGE_ONLY or BOOKKEEPING_ONLY.

All preserved predecessor/candidate/evidence records reverified, both previous archives reverified (36 + 143 members), original frozen checker and historical records unchanged. Historical 21 AMBIGUOUS / 1 UNMATCHED remains unchanged. Historical ETW loss cause: **UNCONFIRMED**. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Final read-only host census at 2026-09-24T01:05:41.4850641Z: **0 matching processes / 0 diagnostic trace sessions**. No protected VM/configuration files were opened or hashed; no VirtualBox was launched; production untouched.

The new bounded nonsecret canonical archive preserves raw pairs, order, protocol, calculations, source hashes, process identities and final census. archive-receipt.json contains actual archive path/hash/member verification. No previous archive overwritten. Broad project sync is not used because it would overwrite unrelated records. No commit or later Stage 6 activity.

## Disposition

STOP regardless of outcome. If REFERENCE_PRECISION_ESTABLISHED, the adjacent owner-review procedure describes the separately gated component experiment. If precision is not established, no extra batches run automatically. If evidence is inconsistent at adequate precision, preserve it as BENCHMARK_REPRODUCIBILITY_DEFECT rather than optimizing or relaxing the threshold. The historical +1.40% result remains preserved; this action does not retroactively alter it.
