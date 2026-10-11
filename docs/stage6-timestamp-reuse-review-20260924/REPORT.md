# Timestamp reuse: Phase 1 semantic review

Status: TIMESTAMP_REUSE_SEMANTICS_CONFLICT

No successor implementation, build, test, benchmark, live trace or UAC was performed. The owner's Phase 1 stop condition applies: equivalence across all required dispositions cannot be established from the existing candidate. This does not establish that a future shared completion endpoint is impossible.

## Inspected boundary

Candidate: D:\JARVIS-STAGE6-LIVE\a34f91e1db274bf78fc5a80e2a9d417c\code.

loss_measurement_fixture_v3.cpp:28-39 implements only UNKNOWN_PARENT. At line 36 the diagnostic QPC precedes field assignments and tap.append. The existing trailing QPC at line 38 follows append. Reusing that value would require changing record publication ordering or mutating a published record and would move the measured endpoint across recorder work. It is not a demonstrated equivalent substitution. The conditional D variant's arrival timestamp is not an eligible substitute.

trace_telemetry.hpp:65-69 has a genuine existing callback-scope endpoint. Its destructor obtains end before telemetry counters, diagnostic.callback and diagnostic.span. It executes after normal callback-body cleanup and handled exceptions, but holds only selected/eventQpc, not a complete lifecycle disposition/identity record. It is a plausible future integration point, not a proven all-disposition drop-in replacement.

The preceding stage6-final-measurement-v3-20260924/REPORT.md:13,24-31 explicitly records incomplete coverage and no observer hooks. The measurement header defines disposition values and a recorder; enum membership does not establish callback coverage.

## Disposition review

| Required disposition | Existing observer branch | Equivalence finding |
|---|---|---|
| ADMITTED | authority_trace_v3.cpp:53-54; startup_trace.cpp:47-48 | Real work completes before scope destruction, but no integrated lifecycle diagnostic completion record exists. |
| UNKNOWN_PARENT | authority:51; startup:45; fixture:28-39 | Only fixture path measured. Its pre-append and trailing timestamps bracket different work. |
| UNKNOWN_PROCESS_INSTANCE | authority:54; startup:48 | Early return is scope-timed; required disposition/identity is not transferred to the timer. |
| DUPLICATE | authority:52,54; startup:46,48 | Counter plus return, without full diagnostic disposition publication. |
| INVALID_IDENTITY | authority:52; startup:46 | Shares a condition with capacity/decode validity; no distinct completed diagnostic record. |
| DECODE_FAILURE | authority:49,52; startup:43,46 | Decoder validity feeds rejection logic; equivalent separate diagnostic endpoint not established. |
| EXCEPTION | authority:55; startup:49,90 | Catches increment faults; required partial identity/validity/disposition is not retained in CallbackScope. Fixture decode failures escape without its diagnostic record. |
| Other rejection | authority:48,52; startup:42,46,64,66,67,76 | Scope timer covers ordinary returns but does not implement the required rejection classification/record. |

The detailed observer calls LifecycleEvent before its outer provider selector (startup_trace.cpp:60-66). Lifecycle START/STOP then take the outer early return; outer selected remains false even for admitted lifecycle records. selected therefore cannot safely stand in for lifecycle disposition. No selector modification is proposed.

Both clocks use QPC, but common clock origin alone cannot prove endpoint equivalence. No new dynamic monotonicity, exception coverage or semantic-equivalence tests were run or claimed passed. The current endpoint excludes its own trailing instrumentation, so an explicit statement of included callback work would also be necessary before integration.

## Decision and next owner review

Stop before Phase 2. Merely deleting one QPC would not satisfy the requested all-path proof. Proposed next review only: define the lifecycle diagnostic completion boundary relative to recorder/telemetry epilogue work, and review a bounded per-disposition record handoff into the existing CallbackScope endpoint. This would be instrumentation integration, not an already-proven redundant-clock substitution. No such integration is implemented here.

Phases 2-5: NOT RUN. Implementation diff: none. Generated-code comparison and performance sanity benchmark: NOT RUN. No CPU savings or <=1% qualification claim.

## Preservation

Source and historical evidence were read only. Only this new report directory and its bounded evidence archive are written. Hash records and census are separate evidence files. No protected VM/configuration was accessed to verify preservation: no operation targeted them. Production JARVIS was not accessed or modified. No thresholds, queues, ETW settings, checker, binaries or historical results were changed.

Historical ETW-loss cause remains UNCONFIRMED. Historical 21 AMBIGUOUS / 1 UNMATCHED remains unchanged. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Rollback: no code change to roll back; preserve this review alongside predecessor evidence. No acceptance commit.
