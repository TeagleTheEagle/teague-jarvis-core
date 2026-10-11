# Single final overhead qualification — OWNER REVIEW ONLY

Preparation is complete. Do not execute this procedure until separately authorized.

1. Read REPORT.md limitations and verify qualification-binding-final.json, source-binding.json, generated-code-review-final.json and the preparation archive receipt. Reverify all bound source/binary/protocol hashes and preserved predecessor inputs. Confirm no unexpected worktree/artifact drift.
2. Perform a read-only host process/trace census: zero matching J6/JARVIS Stage 6 diagnostic processes and sessions. No UAC or live trace creation. Confirm the dedicated D: workspace has no ONE-FINAL-ATTEMPT directory. Any mismatch, existing attempt or unavailable census: STOP before execution.
3. Execute exactly once from the report directory using the bound bundled Python:

```powershell
& 'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B 'C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-qualification-harness-v1-20260924\run_once.py' --execute-one-final-attempt
```

This invokes only `D:\JARVIS-STAGE6-LIVE\qualification-harness-v1-20260924\J6FinalQualification.exe --qualify 46e30ed33fba977e430b7d290d042a245160156bb67f9788d91e11b92abf1ab1` under retained-handle supervision. Do not invoke the executable directly and bypass the one-attempt binding.

Binary SHA-256: `d68159ce5c85a2cf71fbbe297a09e16cb214bce0d862024e6367535315d3ccfb`.

4. Preserve the reviewed schedule: 60 three-arm blocks; A unchanged baseline, B separate-clock reference, C optimized (the requested optimized comparison B is protocol C). 20,000 warm-up and 1,000,000 measured callbacks per trial; no extra trials/calibration. Same protocol, cases, counters, chunks, six statistical groups and 1,200-second launcher bound. No priority/affinity/security setting change.
5. Stop on first invalid record, identity/counter discrepancy, overflow, nonzero exit, interruption, incomplete block or deadline. Preserve raw/partial evidence and do not retry. Retain the one-attempt marker permanently. Bounded timeout cleanup may terminate only the fixture process held by the launcher; no PID-only cleanup.
6. Require complete 180-trial output, exact 180,000,000 measured and 3,600,000 warm-up callbacks, matching per-block input/output digests, valid raw CPU counters and exact process identity. Verify candidate hashes again. Do not replace failed trials or discard ordinary noise.
7. Review fixed Student-t intervals and predeclared drift/dependence diagnostics. Final optimized overhead is C/A-1, not B-C. Upper bound <=1.0% plus valid inference permits PASS; lower bound >1.0% means FAIL; unresolved precision means NOT ESTABLISHED. Material unresolved inference concerns remain INCONCLUSIVE. No alternative estimator, sample extension or additional profiling.
8. Final read-only census must show zero matching processes/traces. Archive raw data, analysis, identities, source/code bindings, first failure if any and final census to a fresh canonical evidence folder; hash-verify every member and archive. Do not declare final acceptance if cleanup or archive verification fails.
9. Report baseline/optimized CPU, ns/callback delta, overhead/95% interval, throughput shift, counts, runtime, memory/record observations and limitations. Individual callback latency is not sampled by this harness; report NOT MEASURED rather than add timing overhead. Stop for owner review regardless of result. No live integration, medium/large validation, protected access or production operation follows.
