# Candidate source review

Reviewed checker_v2.py, its closed schema and unchanged local qualification/coverage/correlation dependencies.

| Risk | Enforcement / evidence |
|---|---|
| Default PASS | No default selection. Public command requires exactly --replay-validated-small; self/immutable archive verification, raw adapter read/validation, typed rules and repeat preservation checks all precede PASS. |
| Swallowed exceptions | Command catches only to print REJECT and return 1. No fallback or acceptance seal on exceptions. Fixture harness preserves exact reasons and stops on unexplained results. |
| Missing fields | Closed schema requires every enumerated member at every object variant; no version inference. Missing runtime keys cannot become acceptance. |
| Empty collections | Independent direct workload and complete expected kernel set; explicit nonempty inventories/handles/native/segments/events/CIM plus eight empty-evidence rejection fixtures. |
| Boolean/numeric coercion | Exact bool/int Python types, finite floats, duplicate-key and nonfinite JSON rejection. String true and bool-as-counter fixtures reject. |
| Unknown enums/schema | Exact envelope version/contract/adapter. All helper classes explicit; no OTHER helper default. Legacy modes do not dispatch here. |
| Path trust | Pinned original archive and source manifest; source paths constrained to reviewed evidence roots; reparse ancestors, traversal/ADS/noncanonical paths rejected. No archive extraction by checker, no incoming Python executed. Disk-tamper fixtures mutate only new D: copies. |
| Evidence substitution | Entire recomputed adapter result equals supplied payload; structural inputs agree; coverage kernel attributes agree; CIM recomputed from raw, not caller-selected identity. |
| Mutable inputs | Original archive/seal and every archived source hash verified before and after analysis; candidate dependencies also rehashed. This is local offline immutable-evidence replay, not a hostile concurrent-filesystem or remotely signed trust service. No claim of OS-level denial against a same-user administrator is made. |
| Authority channels | Direct creator capture, actual tracer helper, qualified post-exit and infrastructure observer remain distinct. Missing/contradictory mandatory evidence rejects. |
| CIM uniqueness | Conditional policy accepts stipulated independent event-bound proof in a labelled unit fixture. Actual current CIM format has no such proof; public replay recomputes ambiguous/unmatched and rejects fabricated UNIQUE. No new event identity mechanism implemented. |
| Acceptance seals | Fixture rule success is RULES_SATISFIED_NOT_ACCEPTANCE. Component seals and the original pre-archive interface are not global acceptance. Public replay binds the existing final archive sidecar. This integration's final report gets its own archive/verification sidecar. |

## Deliberate limits

The schema is deliberately the known small evidence shape, with no general future-schema fallback. The binding is the reviewed small archive and run. This is a versioned checker integration candidate, not replacement of the frozen checker and not readiness for medium/large/protected acceptance by itself. The source-derived schema is structural validation; independent semantic requirements and persisted byte verification remain mandatory.

No old positive test suite with obsolete lifecycle assumptions was silently run against a different contract. The frozen legacy checker and historical results were preserved by hash; new checks run against the explicit amended contract only.

## Preserved preparation failures

prepare.py rejected an incorrectly transcribed expected manifest hash before candidate creation. Actual hash matched the prior receipt and seal. prepare_v2.py then rejected decoding the UTF-8 historical report with Windows default cp1252. prepare_v3.py changed only that read to explicit UTF-8. All three scripts and both failure records remain preserved. These were explained preparation defects, not evidence drift or failed live runs. No checker test failed and no live run was retried in this gate.
