# Stage 6 telemetry candidate and single medium attempt

**MEDIUM_CHECKER_DEFECTIVE — Stage 6 INCOMPLETE.**

250 final focused checks passed (21 native cases, 40 telemetry checks, 21 composition checks, 114 prior checker regressions, 43 declaration checks, 5 intake checks, 6 baseline comparisons). One live medium attempt followed. No medium retry, large validation, protected access or production operation occurred.

## Exact blocker and diagnosis

The public checker rejected `SCHEMA_FIELDS:$.bundle.qualification.writer`. New telemetry was correctly verified on disk, but the wrapper's v3 compatibility view normalized only top-level manifest/writer records, omitting the duplicate writer embedded in the analyzer's qualification report. The strict schema correctly rejected the extra fields.

Read-only diagnosis proved the nested writer equals the authoritative writer exactly. Normalizing only that proven duplicate in an in-memory diagnostic replay makes the existing rules pass. This is diagnostic evidence, NOT acceptance, and does not alter frozen code or the rejected run. The synthetic composition fixture lacked the actual analyzer's new nested telemetry fields, so it missed this integration case.

Minimum proposed correction: in a new versioned candidate, require nested raw writer equality before applying the same projection to the duplicate. Add a positive fixture from actual analyzer output and rejection fixtures for nested-writer substitutions, missing timing and unknown fields. Preserve this attempt as rejected. The owner medium contract requires stopping when a frozen checker defect is discovered; no checker patch or new medium attempt was performed.

## Required medium results

| # | Requirement / measurement | Actual result |
|---|---|---|
| 1 | Run ID | identity-7136d8a7cb68487bb5205a2444302611 |
| 2 | Workload | 64 probes: 16 idle / 16 churn / 32 overlap, one worker; fresh TEST identity |
| 3 | Input/data size | Process events only; 114836 authoritative bytes; no source dataset hashing |
| 4 | Workload seconds | 6.103895 |
| 5 | Campaign through final cleanup seconds | 163.720328 |
| 6 | Authoritative records | 264 |
| 7 | Records/sec (writer lifetime) | 5.64337733765363 |
| 8 | Run evidence bytes | 8247740 |
| 9 | Segments | 15 |
| 10 | Segment bytes | {'min': 5303, 'max': 7909, 'mean': 7655.733333333334} |
| 11 | First sequence | 1 |
| 12 | Last sequence | 264 |
| 13 | Gaps | 0 |
| 14 | Duplicates | 0 |
| 15 | Overlaps | 0 |
| 16 | Missing segments | 0 |
| 17 | Durable segments | 15 |
| 18 | Segment hashes | PASS |
| 19 | Durable manifest | PASS; does not confer campaign acceptance |
| 20 | Writer capacity | 65536 items / 67108864 bytes; unchanged |
| 21 | Writer high-water | 55 items / 22912 bytes |
| 22 | Finalizer capacity | 2 |
| 23 | Finalizer high-water | 2 |
| 24 | Maximum queue utilization | Finalizer 100.0%; writer items 0.083923%; writer bytes 0.034142% |
| 25 | Backpressure events | {'started': 2, 'completed': 2, 'interrupted': 0, 'ticks': 480489} |
| 26 | Rejected admissions | 0 |
| 27 | Average flush seconds | 0.042828366666666666 |
| 28 | p95 flush seconds (nearest rank) | 0.1077743 |
| 29 | Maximum flush seconds | 0.1077743 |
| 30 | Average readback/hash seconds | 6.431333333333333e-05 |
| 31 | Maximum readback/hash seconds | 9.13e-05 |
| 32 | Kernel START | 132 |
| 33 | Kernel STOP | 132 |
| 34 | Canonical identities | 132 |
| 35 | False unique | 0 |
| 36 | Authoritative ambiguity | 0 |
| 37 | Direct creator captures | 65 |
| 38 | Tracer-helper verifications | 2 |
| 39 | Qualified post-exit helpers | 64 |
| 40 | Missing mandatory identity evidence | 0 |
| 41 | Identity contradictions | 0 |
| 42 | Native entries | 65 |
| 43 | CIM unique | 0 |
| 44 | CIM ambiguous | 258 |
| 45 | CIM unmatched | 5 |
| 46 | Max heartbeat seconds | 1.7880686 |
| 47 | Slow heartbeat warnings | NOT CONFIGURED — explicitly approved; <10-second failure threshold unchanged |
| 48 | Slow probe warnings | 0 |
| 49 | Maximum probe seconds | 0.5807977 |
| 50 | Hard deadline violations | 0 |
| 51 | Application observer | Exit 0; secondary finalization complete; sampler not instantiated |
| 52 | Tracer | Exit 0; no recorded kernel loss |
| 53 | Writer | No fault; attempted/accepted/written equal; threads exited |
| 54 | Finalizer | 15 manifested segments; two-credit bound preserved |
| 55 | Checker | REJECT: SCHEMA_FIELDS:$.bundle.qualification.writer |
| 56 | Version | stage6-checker-telemetry-v4 composed with unchanged v3 lifecycle rules |
| 57 | Queue drain | PASS; 843 telemetry transition snapshots; exact state/lag reconciliation |
| 58 | Trace finalization | PASS; zero trace sessions |
| 59 | Cleanup | PASS; creation-bound process evidence closed; final host census zero |
| 60 | Archive member count | See verified receipt |
| 61 | Archive verification | Required before final disposition; see receipt |
| 62 | Original source hashes | 156/156 unchanged |
| 63 | Frozen candidate hashes | 160/160 unchanged |
| 64 | Protected VM access | NONE |
| 65 | Production change | NONE |
| 66 | Historical 21 ambiguous / 1 unmatched | UNCHANGED; new 258/5 is separate |
| 67 | Historical causes | UNCONFIRMED; HISTORICAL STAGE 1 CAUSE: UNCONFIRMED |
| 68 | 59.7 GB justified | NO: medium checker gate rejected |
| 69 | Next proposed gate | Separately versioned projection correction + analyzer-produced fixtures; do not patch frozen run or automatically retry |
| 70 | Final status | MEDIUM_CHECKER_DEFECTIVE; Stage 6 INCOMPLETE |

## Changes, failure preservation and rollback

Changed only new TEST candidate copies: `durable_sink.hpp`, its compiled test/tracer binaries, launcher DLL-path binding, declaration/intent paths. Added `telemetry.py`, `checker_telemetry.py`, telemetry policy, focused tests and evidence tooling. The existing v3 checker/schema/adapter and original frozen sources stayed unchanged. The new wrapper makes telemetry mandatory before composing existing rules; its nested-copy omission is the current blocker. `changes.json` contains exact raw-byte before/after hashes and final diffs. `candidate-frozen.json` binds final source/binaries. The initial normalized-text hash is clarified in `metadata-clarification.json`.

Telemetry uses a preallocated 65536 x 80-byte (5,242,880-byte) queue trace, existing locked transitions, per-segment ticks and separately hashed finalization evidence on D:. No new live filesystem appends, observer authority, process deadlines or heartbeat limits. Flush p95 uses nearest rank; with 15 samples it equals the maximum. Readback/hash duration includes record validation, not pure CPU hash cost. Queue lag and two actual completed backpressure episodes are verified. Finite performance samples do not prove long-duration sustainable throughput or actual PID reuse (none observed).

Preserved preparation failures: initial fault-19 test did not reach a blocked predicate (20 passed / 1 failed); corrected only that injected test path and reran 21/21. Initial path preparation used single backslashes against a C# escaped DLL path and stopped before launch; corrected binding only. Initial legacy regression completed checks but failed exclusive locator creation because a prior locator was copied; a new output location preserved it and the fresh 114+43 regressions passed. Intermediate compiler outputs and line-ending normalization are retained. Existing tracer variable-shadowing warning remains disclosed.

The first final host inspection recorded one pwsh PID 17320, created during that inspection. Its parent command contained the D: scope string matched by the inspector. Subsequent read-only inspection found that PID absent, and the unchanged inspector invoked without an embedded D: parent command recorded zero matching processes/traces. No process was terminated and no exclusion rule was changed. Both observations are preserved; the exact prior command-line identity was not captured in the blocked record.

Both initial and corrected native test processes were reconciled by retained creator process handles, creation time, image identity and kernel signal/exit times. Comparison runs also retained creation/exit proof. All actual medium components reported exit 0. No cleanup deletion occurred.

Rollback: stop selecting this new TEST workspace; retain all evidence and the prior candidate. No production restore or VM action is needed. Original failed/inconclusive archives remain unchanged. The accepted Stage 4/5 application baseline was not edited. No acceptance commit, acceptance seal, protected hashing or production activation was created.

## Stage 6 remaining path

The current immediate gate is the checker integration defect. Medium acceptance must pass before large synthetic protected-collector validation is eligible. Then the existing preservation-safe roadmap still requires qualified collector evidence, separately authorized protected baseline capture, OS-enforced source isolation and validation-copy preparation, qualifying clean-Windows recovery/deployment evidence, and the applicable owner-controlled cutover decision. This finite process run is not a substitute for any of those gates. No protected-source permission, VM operation or production authorization is inferred from passing telemetry tests.

Historical delay causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
