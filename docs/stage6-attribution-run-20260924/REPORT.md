# One fixed component-attribution experiment

**INCONCLUSIVE**. Execution completed; this is not instrumentation qualification or Stage 6 acceptance.

Run ID: b36e199a3cbc433d93cf0c7be97cc3e5
Live evidence: `D:\JARVIS-STAGE6-LIVE\blocked-attribution-v1-b36e199a3cbc433d93cf0c7be97cc3e5`

## Execution

Exactly one invocation of the unchanged fixture in attribution mode: 40 complete blocks, 200 arms, 200,000,000 measured callbacks. Excluded warm-up: 4,000,000 callbacks from pinned source/run declaration, not independently emitted per arm. No missing/duplicate/invalid blocks, exclusions, retries, replacements or extensions. Normal exit 0; retained process and main-thread creation/exit identity consistent; closeErrors empty. Process PID 18712, main-thread ID 26356, process creation FILETIME 134346904057135019, exit FILETIME 134346908503896781.

Fixture duration 444.672s; wrapper duration 444.688s. Bound 1,200s unchanged.

Schedule BALANCED, not randomized: ABECD BCADE CDBEA DECAB EADBC DCEBA EDACB AEBDC BACED CBDAE repeated four times. Each arm: 20,000 excluded warm-up + 1,000,000 measured callbacks. Raw counters/wall/throughput/identities remain in the unchanged JSONL and native exit records. per-block.csv records all A_i through E_i and actual order. variant-supplementary.json reports absolute CPU and wall/throughput summaries.

## Fixed analysis

Each block supplies the contrast, then consecutive four-block groups yield ten means. df9 Student-t intervals; B-D and D-A use 97.5% individual intervals, other intervals descriptive 95%. Percentage uses that block's A. No alternate estimator or data pooling.

| Contrast | ns/callback estimate [interval] | % of A estimate [interval] | Confidence | Half-width / target (pp) | Precision |
|---|---:|---:|---:|---:|---|
| B-A | +51.953 [+26.511, +77.396] | +2.502% [+1.270, +3.733] | 95% | 1.232 / none | NO WIDTH GATE |
| B-D | +48.047 [+14.989, +81.105] | +2.266% [+0.735, +3.798] | 97.5% | 1.531 / 0.2 | NOT MET |
| C-A | +42.188 [+17.410, +66.965] | +2.021% [+0.870, +3.172] | 95% | 1.151 / 0.3 | NOT MET |
| D-E | -1.953 [-21.054, +17.147] | -0.076% [-0.975, +0.824] | 95% | 0.900 / 0.3 | NOT MET |
| E-A | +5.859 [-11.429, +23.148] | +0.311% [-0.502, +1.124] | 95% | 0.813 / 0.3 | NOT MET |
| D-A | +3.906 [-33.813, +41.625] | +0.235% [-1.537, +2.007] | 97.5% | 1.772 / 0.2 | NOT MET |
| B-C-D+A | +5.859 [-29.123, +40.842] | +0.245% [-1.393, +1.884] | 95% | 1.638 / 0.4 | NOT MET |

All six specified planning targets were missed. B-A has no prerequisite width; its wide interval did not invoke a retired gate.

These are conditional compiled-software contrasts, not pure clock/store/branch hardware costs. Residual is not an independent physical cost; algebraic reconstruction does not prove additivity. Negative store point estimate does not establish that stores are free or improve performance.

## Drift and inference assessment

Numerical conditional classification: **SUPPORTED_BUT_UNCERTAIN**. B-D lower 0.735pp exceeds 0.5pp, but D-A upper 2.007% exceeds 0.9%. Strong-support rule fails.

Final inference status: **INCONCLUSIVE**, supported-assumptions review not granted. B-D first/last twenty-block means are 2.739% and 1.794%; B-A halves 3.269% and 1.734%; D-A halves 0.531% and -0.060%. B-D group lag-one correlation is -0.459; D-A is +0.020. Treatment-centered position ranges: B 51.172ns, D 50.391ns, compared with B-D mean 48.047ns. Full slopes, position tables and group residuals are in analysis-final.json.

These descriptive differences may include sampling noise. They do NOT prove a scheduler, storage, compiler or benchmark-method defect; no post-hoc numeric rejection threshold was invented. The fixed nonrandomized schedule, ten grouped observations and substantial temporal/position variation leave the inference assumptions unresolved. inference-review.json is bound to this exact run, raw data, binding and diagnostics. No observations were deleted; no supplementary estimator was used to rescue the result.

## Historical sanity and decision

New B-A +2.502% [1.270,3.733] overlaps both preserved +1.400% [1.191,1.609] and +1.180% [0.914,1.446] intervals. Its different point estimate is reported; a reproducibility defect is NOT established. Historical evidence is separate, unchanged and not pooled.

<=1% remains a plausible optimization objective, not demonstrated: conditional D-A point estimate is +0.235%, but its adjusted upper bound reaches +2.007%, and inference assumptions remain unresolved. No implementation change is justified as accepted by this run. D still substitutes arrival time; it is not valid completion evidence. The full <=1.0% screen is unchanged and no instrumentation qualification occurred.

## Preservation and archive

Fixture SHA-256: `e3fd0f58ab7f37093791c4eb55a4c20b8984bfc7b2ba9e363ac32b3cb995a0b9`
Analyzer SHA-256: `9dd0495387bc948c1672c1e3a5d2e4c79eb527120b85eb92dc46beb3e7cfdb96`
Canonical binding SHA-256: `8129bfdc69af4e1122bf0c9591ca1383e87862e0988c2d60d40a556af81546bf`
Frozen checker SHA-256: `e6fbefd3fd463c6c8e09d0e8273a81b46ee2806515cae05e7837ea905a3e69d6`

Post-run preservation PASS: 65 pinned candidate/history artifacts, 284 prior archive members, unchanged driver/binding/raw and frozen checker. Final host census: 0 matching diagnostic/VirtualBox processes; 0 diagnostic trace sessions. Queries succeeded, no UAC. Production unchanged; protected VM/configuration not accessed. No ETW session or observer started.

New archive receipt records the completed archive/member/manifest hash verification. All new evidence is separate; prior archives and decisions were not overwritten. No acceptance commit. Rollback needs no runtime restoration: retain this read-only profiling evidence; no optimization was applied.

Historical 21 AMBIGUOUS / 1 UNMATCHED unchanged. Historical ETW-loss cause remains UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

STOP. No retry, sample extension, optimization or next gate. Owner review required before further work.
