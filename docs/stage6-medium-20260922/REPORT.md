# Stage 6 medium sacrificial attempt

**INCONCLUSIVE — required capacity telemetry is incomplete.**

One live attempt was executed. No retry, checker patch during execution, deadline change, protected VM access, large-data hashing or production change occurred. Preparation passed **162/162** checks: 114 existing regressions, 43 medium declaration/rule checks and 5 fresh-intake checks. Native binaries, writer/finalizer and monitor were unchanged.

All observed correctness checks passed: 64 probes, 132 complete canonical process instances, 264 authoritative records, 15 durable/hash-verified segments, no gaps/duplicates/overlaps/missing segments, no lost authority, no deadline violations, healthy heartbeat and complete cleanup. The medium checker returned EVIDENCE_VALIDATED_PENDING_ARCHIVE, not overall medium acceptance.

The unchanged writer does not persist per-segment flush samples, individual hash durations, backpressure-event counts or continuous queue time series. Therefore the required p95 flush, maximum individual hash duration and backpressure-event count are **NOT RECORDED**. Aggregate time/maxima cannot establish those values. This is incomplete measurement coverage, not evidence of a failed durability mechanism or a confirmed historical delay cause. No MEDIUM_VALIDATED acceptance seal is issued.

## Mandatory report

| # | Item | Actual result |
|---|---|---|
| 1 | Run ID | `identity-5df89a533dc149ea8c42768601eb45c3` |
| 2 | Workload | Frozen declaration: 16 idle + 16 sequential churn + 32 overlap in four batches of eight; one direct worker; all observed helpers/observer |
| 3 | Input/data size | No payload dataset; synthetic lifecycle activity only. Authoritative output 114,838 bytes; no 59.7 GB hashing |
| 4 | Elapsed workload | 5.8908261 s, first probe launch request to final probe reconciliation, monotonic QPC |
| 5 | Campaign duration | 91.686368 s from launcher creation to final independent host inspection, including UAC, observer startup/closure and analysis; archive preparation follows separately. Writer lifetime 51.6716073 s |
| 6 | Authoritative records | 264 |
| 7 | Records/sec | 5.109189 over the full writer window; not maximum sustainable producer throughput |
| 8 | Persisted run evidence | 8,109,509 bytes including intake manifest at post-run measurement; authoritative bytes 114,838 |
| 9 | Segments | 15 |
| 10 | Segment sizes | 5,229–7,908 bytes; mean 7655.867; target unchanged 8,192 bytes |
| 11 | First sequence | 1 |
| 12 | Last sequence | 264 |
| 13 | Gaps | 0 |
| 14 | Duplicate sequences | 0 |
| 15 | Overlaps | 0 |
| 16 | Missing segments | 0 |
| 17 | Durable segments | 15 |
| 18 | Segment hashes | PASS, all bytes independently reopened and verified |
| 19 | Manifest | Component manifest/seal and fresh intake PASS; global medium acceptance NOT SEALED |
| 20 | Writer capacity | 65,536 items / 67,108,864 bytes, unchanged |
| 21 | Writer high-water | 67 items / 27,846 bytes |
| 22 | Finalizer capacity | 2 pending/in-service segments, unchanged |
| 23 | Finalizer high-water | 2 |
| 24 | Maximum utilization | Finalizer 100%; writer items 0.102234%, bytes 0.041494% |
| 25 | Backpressure events | NOT RECORDED; accumulated backpressure time 0.0617944 s. No count inferred from elapsed time |
| 26 | Rejected authoritative admissions | 0 |
| 27 | Average durable flush | 0.035566073 s, recorded total / 15 completed segments |
| 28 | p95 durable flush | NOT RECORDED; cannot reconstruct from aggregate/max |
| 29 | Maximum durable flush | 0.0993878 s |
| 30 | Average segment hash | 0.000076380 s, recorded total / 15 segments |
| 31 | Maximum segment hash | NOT RECORDED |
| 32 | Kernel START | 132 |
| 33 | Kernel STOP | 132 |
| 34 | Canonical identities | 132 |
| 35 | False unique matches | 0 |
| 36 | Authoritative ambiguity | 0 |
| 37 | Direct creator captures | 65 (64 probes + worker) |
| 38 | Tracer helper verifications | 2; infrastructure application observer separately verified |
| 39 | Qualified post-exit helpers | 64, explicitly distinct from creator/tracer images. Previous small-run 16 remain historical, not rewritten |
| 40 | Missing mandatory evidence | 0 |
| 41 | Contradictions | 0 |
| 42 | Native PE entries | 65 |
| 43 | CIM unique | 0 |
| 44 | CIM ambiguous | 258 |
| 45 | CIM unmatched | 1 |
| 46 | Maximum heartbeat | 1.2278344 s; maximum measured age 1.2213142 s; unchanged threshold <10 s |
| 47 | Slow heartbeat warnings | Separate warning counter NOT RECORDED; all observed intervals/ages below hard threshold |
| 48 | Slow probe warnings | 0 |
| 49 | Maximum probe lifetime | 0.3855425 s from kernel creation/exit FILETIME |
| 50 | Hard deadline violations | 0; 13.6 s hard / 15 s independent observer unchanged |
| 51 | Application observer | Healthy collection/finalization, exit 0; sampler NOT APPLICABLE because qualified process-only pipeline does not launch one |
| 52 | Tracer | Healthy, no kernel loss/error, exit 0 |
| 53 | Writer | No fault, all 264 attempted/accepted/written, threads exited |
| 54 | Finalizer | Complete, bounded, all 15 manifested; 193 records progressed while finalizing |
| 55 | Checker | EVIDENCE_VALIDATED_PENDING_ARCHIVE; no manual override, not full measurement acceptance |
| 56 | Version | `stage6-checker-input-v3`, `stage6-medium-combined-v1`, `stage6-medium-declaration-v1`; kernel contract unchanged |
| 57 | Queues | Empty/reconciled, complete secondary persistence |
| 58 | Trace finalization | PASS; zero diagnostic trace sessions after exit |
| 59 | Cleanup | PASS: launcher reports worker, observer and tracer exited 0; final host inventory zero matching processes; all 132 identities reconciled |
| 60 | Archive members | 530; see independent archive-verification.json |
| 61 | Archive verification | Complete only with accompanying hash-verified receipt; failed/inconclusive disposition is preserved, not promoted by archive success |
| 62 | Frozen checker hashes | Initial/final identical `e6fbefd3fd463c6c8e09d0e8273a81b46ee2806515cae05e7837ea905a3e69d6` |
| 63 | Candidate hashes | Validated small checker unchanged `a0c5bf094841bf428bb62073082627e4e3ca88d1b330f3bcd8d611ecc51f2945`. Medium pre-run/final identical `64649825222ec4e0d06a50531944fc083db208cb9f47b88c6fc2baead7f63d6d` |
| 64 | Protected VM access | NONE; no protected VM/configuration file read, hashing or VirtualBox invocation |
| 65 | Production change | NONE |
| 66 | Historical 21/1 | UNCHANGED; new 258/1 is a separate run |
| 67 | Historical causes | UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED |
| 68 | 59.7 GB justified | NO; do not extrapolate this finite lifecycle run to large protected-collector readiness |
| 69 | Next proposed gate | Review minimal TEST writer telemetry to record immutable per-segment flush/hash durations and backpressure count, validate it offline/small, then separately authorize any new medium attempt. No implementation or retry undertaken here |
| 70 | Final status | INCONCLUSIVE |

## Scale and boundedness

Against the validated small run, direct probes increased 4x and measured probe-work duration increased from 1.6160791 to 5.8908261 s (3.645x). Segments increased from 4 to 15. The finalizer reached its two-credit bound and completed with no rejected admissions. These observations support correctness/bounded operation for this finite attempt; they do not prove long-duration rate stability or omitted queue-time-series measurements. No actual PID reuse occurred; existing rejection fixtures do not count as live reuse.

Observed writer-window rates: 2222.458 authoritative bytes/s and 17.418 segments/minute. Those include startup/UAC/closure waits and are not isolated finalizer-service throughput. Maximum active append was 0.0365529 s; append total 0.1903751 s. Full measured aggregates and explicit unavailable fields are in metrics.json.

## Exact preparation changes / preservation

`changes.json`, `preparation-changes.json`, source diffs and candidate-frozen.json identify every copied/new artifact and hash. Changed only the new copy's launcher DLL path, worker workload selection, declaration-aware combined adapter and versioned input schema. Added separate fresh-binding/medium checker/analyzer support. Original frozen checker, original small checker and all native runtime/monitor/writer binaries remained unchanged. No changes occurred after the medium source freeze. 802 preservation comparisons passed.

Commands (Python uses the bundled interpreter with -B): prepare.py; read-only host_preflight.ps1; install.py; validate_preparation.py (114+43); freeze.py (5 binding checks); final preflight; qualified_launch.ps1 -Run identity-5df89a533dc149ea8c42768601eb45c3; one kernel UAC then one application-observer UAC; analyze_medium.py; final host inventory; evaluate.py; metrics.py; report_archive.py. Exact command outputs are preserved by their JSON result files and the task tool transcript. No calibration rerun or second medium attempt.

The checker remains separate and does not replace either prior candidate. Rollback is to stop selecting the new medium TEST workspace; no production files or configuration require restoration. Preserve all evidence and the unsuccessful overall disposition. No cleanup deletion is required.

STOP. No large validation, protected baseline capture, VM activity or production operation is authorized by this result.
