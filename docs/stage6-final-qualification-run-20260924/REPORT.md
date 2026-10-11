# OVERHEAD_SCREEN_NOT_ESTABLISHED

Exactly one fixed attempt completed: 60 three-arm blocks / 180 trials; 180,000,000 measured callbacks and 3,600,000 warm-up callbacks; 125.953 seconds. Exit 0, no timeout. Optimized protocol C is the owner-requested optimized B; protocol B remains the separate-clock reference.

Baseline: 615.365 ns/callback. Optimized: 632.813 ns/callback. Paired increase: 17.448 ns/callback. Bound mean within-block percentage overhead: +3.006276%, 95% Student-t interval +0.874011% to +5.138541%. Ratio of grand means is not substituted for the bound estimator.

Throughput shift: -2.800798%, 95% interval -3.712097% to -1.889498%. Counts, ordering, chunk totals, thread/retained-process identity, counter continuity and matching workload digests passed the unchanged validator.

Drift diagnostics: first/last-half overhead 2.085521% / 3.927030%; slope +0.022620 percentage points/block; grouped lag-1 -0.191356. Six group means span 0.932904% to 5.362155%. Position means and all calculations remain in analysis.json. Variation is disclosed; no stationarity claim or alternative estimator. The interval crosses the limit, so neither PASS nor definitive above-limit FAIL is established.

Individual callback latency and runtime memory telemetry were not collected. This synthetic workload does not measure live ETW, total JARVIS or production performance.

All bound harness/protocol inputs and 1,219 predecessors unchanged. Prior 105-member archive verified. Final host census: zero matching diagnostic processes and zero trace sessions. No UAC, live ETW, protected VM access or production changes. Historical causes remain UNCONFIRMED.

Smallest owner decision: review deferral of this diagnostic instrumentation branch before continuing Stage 6 without depending on it. No retry, extension, profiling, optimization or integration is performed or implied.
