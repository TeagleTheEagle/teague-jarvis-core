# Fixed blocked-attribution experiment — OWNER REVIEW ONLY

NOT AUTHORIZED OR EXECUTED IN THIS IMPLEMENTATION PASS.

One future offline experiment only. No UAC, ETW, observer integration, optimization, medium/large validation, protected VM, or production access.

## Immutable experiment

Executable: `D:\JARVIS-STAGE6-LIVE\component-attribution-20260924-7f29a680\J6AttributionFixture.exe`

SHA-256: `e3fd0f58ab7f37093791c4eb55a4c20b8984bfc7b2ba9e363ac32b3cb995a0b9`

Executable command line, exactly once through the existing retained-handle launcher:

`"D:\JARVIS-STAGE6-LIVE\component-attribution-20260924-7f29a680\J6AttributionFixture.exe" attribution`

This is not a command to execute now. Do not invoke the old run.py entry point: its historical reference gate is intentionally unchanged.

40 blocks; five variants/block; 1,000,000 measured callbacks/arm; 20,000 excluded warm-up callbacks/arm. 200,000,000 measured plus 4,000,000 warm-up callbacks. No reference phase, selftest phase, replacement block, retry or extension. Existing 1,200-second launcher bound. Expected runtime approximately 7–10 minutes, not a guarantee.

Balanced, NOT randomized, schedule below repeated exactly four times:

```
ABECD BCADE CDBEA DECAB EADBC DCEBA EDACB AEBDC BACED CBDAE
```

A BASELINE_DISABLED; B FULL_ENABLED_REFERENCE; C CLOCK_ONLY; D STORAGE_ONLY; E BOOKKEEPING_ONLY. Warm-up count is established from pinned source and the explicit execution declaration; it is not emitted per arm. Do not label it independently measured.

## Procedure after separate owner authorization

1. Verify final-source-freeze.json, candidate.json and the finalized implementation archive. Reverify every candidate artifact, including executable/source/audit/original launcher and historical evidence hashes. Require zero matching diagnostic processes/traces and no VirtualBox process. No protected files are inspected to establish this.
2. Generate a new UUID hex run ID. Create one previously nonexistent empty `D:\JARVIS-STAGE6-LIVE\blocked-attribution-v1-<32-lowercase-hex-run-id>` directory. No reparse point or old raw state is allowed. Preserve the approved run ID/workspace outside the run evidence as invocation inputs.
3. Use bundled Python with `-B` and this exact analyzer's `bind --run-id <ID> --workspace <DIR> --output <DIR>\binding.json`. It verifies the candidate, requires an empty D: workspace, and creates the binding exclusively. Preserve its printed canonical binding SHA-256 outside the run directory. Binding creation does NOT authorize execution. The TEMPLATE document cannot satisfy the analyzer.
4. Load the existing `stage6-component-attribution-20260924\run.py` definitions without executing __main__, as previously validated by `stage6-reference-precision-20260924\repeat_reference.py`. Use the same output-only path adapter: executable and string/CWD remain the original fixture directory; `W / 'raw'` maps to this fresh run directory. Call the unchanged `launch('attribution')` function once. Preserve creator-owned process/main-thread handles, creation/exit FILETIMEs, output, stderr, exit status, and close errors. No affinity/priority/environment change. This pass has NOT installed a new executable runner.
5. Any malformed output, count/order/identity/API error, interruption, nonzero exit or timeout permanently rejects the attempt. Preserve the first failure and partial records. No analysis classification or success finalization. The existing launcher timeout is not proof of process termination: require identity-verified cleanup under existing authorization; if it cannot be established, stop for owner review. Do not terminate by PID alone or retry.
6. Only after a successful process exit, build a new `receipt.json` conforming exactly to the analyzer's `validate_execution` expected dictionary. Bind schema `j6.blocked-attribution.execution.v1`, run ID, canonical binding hash, raw file SHA-256, exact exit-file byte SHA-256, blocks=40, warmupPerArm=20000, warmupEvidence from contract-v1.json, retries/replacements/extensions/referencePhases=0, interrupted/APIError=false, status=COMPLETE. This is a wrapper declaration about the pinned fixture, not invented independent warm-up measurement. Preserve original raw JSONL and native exit records unchanged.
7. Analyze using the fixed successor:

```
<bundled-python> -B <successor>\analyzer_v1.py analyze --binding <DIR>\binding.json --binding-sha <CANONICAL-SHA> --run-id <ID> --workspace <DIR> --raw <DIR>\attribution.jsonl --exit <DIR>\attribution-exit.json --receipt <DIR>\receipt.json --output <DIR>\analysis-initial.json
```

The output is initially INCONCLUSIVE pending inference review; numerical conditional classification is explicitly provisional. Review all order/position/temporal drift and grouped residual diagnostics. Do not invent an automated drift threshold or choose a different estimator.
8. If assumptions can be supported, record a separate `j6.blocked-attribution.inference-review.v1` document with exact runId, rawSHA256, bindingSHA256, diagnosticsSHA256, boolean assumptionsSupported/materialDriftOrDependence and a substantive evidence basis. Analyze the SAME immutable records with `--review <review-file>` into a NEW output file. This is analysis only, not another benchmark. Missing, stale or unresolved review cannot establish a supported classification. Non-overlapping historical intervals remain INCONCLUSIVE for review, not an automatic reproducibility defect.
9. All seven contrasts use within-block ns differences and percentage relative to that block's A. Average consecutive groups of four blocks; ten group means; df=9. B-D and D-A receive 97.5% individual intervals (Bonferroni joint coverage at least 95%, conditional on model assumptions). Other contrasts receive descriptive 95% intervals. Planning targets are recorded, not silently substituted for final qualification. No pooling of historical datasets.
10. STRONGLY_SUPPORTED requires B-D adjusted lower >0.5 percentage points AND D-A adjusted upper <=0.9%. DISPROVEN requires B-D upper <=0.5 with half-width <=0.20; otherwise positive lower >0 yields SUPPORTED_BUT_UNCERTAIN, and unresolved savings yields INSUFFICIENT. These prospective deterministic tie/precedence rules are in contract-v1.json. Material/unresolved inference assumptions override all to INCONCLUSIVE.
11. Even STRONGLY_SUPPORTED is only justification for a separately reviewed optimization experiment. D stores arrival time and is not production-valid completion evidence. Full instrumentation remains subject to <=1% dispatcher CPU; this analyzer NEVER qualifies instrumentation.
12. Perform read-only final census; require zero matching diagnostic processes and zero trace sessions with successful queries. Reverify source/history hashes. Archive raw data, binding, declarations, calculations, inference review, cleanup and all failures into a new nonsecret evidence archive. Hash-verify all members and archive. If any preservation/cleanup/archive check fails, report it explicitly. Stop for owner review regardless of result.

No command in this document was executed as a benchmark in this pass.
