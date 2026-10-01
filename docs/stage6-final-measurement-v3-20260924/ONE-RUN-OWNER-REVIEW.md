# Future one-run diagnostic — OWNER REVIEW ONLY, presently BLOCKED

**Do not execute. Do not request UAC.** The early overhead screen returned MEASUREMENT_OVERHEAD_CONFLICT. The partial successor has no completed integrated instrumentation or valid successor acceptance manifest. It cannot satisfy the requested diagnostic. Supplying a runnable command for this partial candidate would incorrectly suggest readiness.

Before an exact launch can be proposed: separately review the offline measurement conflict; complete bounded instrumentation and all required coverage; demonstrate the <=1% screen reliably; build and freeze the completed successor, runtime identities, candidate-local DLL and binding; review the exact resulting hashes and commands. Do not reuse predecessor hashes as successor acceptance hashes. No live authorization is sought in this report.

## Fixed proposed inputs and constraints

- Exactly one new normal-case small sacrificial run, fresh identity and fresh D: run workspace; no old mutable run state.
- Twelve synthetic files `00.bin` through `11.bin`, 786,432 total bytes, each matched against the finally approved manifest. No external fallback or protected-root access.
- All active artifacts on D:, unchanged providers/buffers/100ms statistics sampling/queue semantics, no reordering of worker/sampler launches.
- Heartbeat <10 seconds; process hard deadline 13.6 seconds; independent observation 15 seconds; original single absolute cleanup deadline 20 seconds with its existing origin and NO resets.
- Creator/native identities joined by run + PID + handle-derived creation FILETIME; kernel sequence where available; never PID alone. QPC and FILETIME remain distinct.

## Exact sequence required after a later approval

1. Verify final manifest, runtime bindings, DLL, source/evidence preservation, expected synthetic hashes/count/bytes, canonical containment and absence of reparse escapes. Require zero matching processes/traces and VirtualBox closed using process inspection only. No protected files are opened for preflight.
2. Bind exactly one fresh run via the existing reviewed workspace-binding APIs. Do not refresh expected hashes to conceal drift. Record a successful immutable preflight before any observer starts.
3. Start only the three existing, sequential observers, with exact paths/arguments/publisher context frozen in the future launch review. Expected executable classes: candidate-local **J6AuthorityTraceV3.exe**; candidate-local **J6StartupTrace.exe**; approved **pwsh.exe -NoProfile -File <final candidate>\timed_monitor.ps1 -Run <fresh run> -KernelPid <authority PID>**. Authority/detail use the fresh root and exact launcher PID/creation FILETIME. Check executable hashes, not names alone. Cancellation, unknown identity, changed command or fourth prompt: STOP, no automatic reissue. All other logic remains non-elevated.
4. After observers are ready, execute the existing normal small collector; both hashes and unchanged metadata required. Diagnostic taps collect only fixed bounded records. No diagnostic field can replace missing authoritative evidence.
5. Preserve handoff-before-local-release proof; Phase A local finalization; collector return; independent terminal helper capture and receipt; pre-shutdown workload census; ordered observer shutdown; independent launcher/observer exits; final zero-process/zero-trace census. All acceptance cleanup uses the SAME original 20-second deadline.
6. After collection ends, export bounded run-correlated sidecars only. Unrelated/unresolved identities remain aggregate counts. Preserve partial sidecars and overflows. Offline primary window: earliest worker/sampler CreateProcess begin minus 2 seconds, through later native entry plus 2 seconds, capped at 8 seconds from window start. Missing markers means incomplete window. Whole-run loss counters remain reported.
7. Evaluate the existing versioned TEST checker only after terminal evidence is complete; frozen checker remains unchanged. No trace-loss relaxation. Check diagnostic completeness and output hashes separately. Local tap sequence is not ETW producer sequence or authoritative completeness proof.
8. On FIRST acceptance-critical failure, permanently reject, perform bounded failure cleanup and NON-ACCEPTANCE preservation; archive partial diagnostic output and hash-verify it. Never run success finalization after failure; later cleanup cannot turn failure into PASS. No automatic retry or repair.
9. Only if all existing acceptance predicates pass: success finalizer, durable manifest and verified acceptance archive. Reverify frozen source, predecessors, preservation, final cleanup. Report unavailable measurements explicitly. STOP after the single run.

## Required report / failure criteria

Report authority/detailed EventsLost, loss increment windows, minimum FreeBuffers, maximum NumberOfBuffers, callback receive/completion progress, control/consumer CPU sampling intervals, delivery lag, operation counts/durations/slow spans, writer/persistence state, target correlation and exact filtering reasons, completeness/overflow, cleanup and archive verification.

Missing required evidence, loss, stale binding, identity ambiguity/contradiction, deadline violation, unhealthy observer, sequence/segment defect, incomplete measurement, remaining process/trace, archive or preservation failure stays fail-closed. Session-loss coincidence does not prove which payload was discarded.

Possible future run statuses: TRACE_DIAGNOSTIC_RUN_PASS, TRACE_DIAGNOSTIC_RUN_FAILED, BLOCKED, PRESERVATION_FAILURE, INCONCLUSIVE. Diagnosis is separate: TRACE_LOSS_ROOT_CAUSE_PROVEN, TRACE_LOSS_STRONG_CAUSAL_EVIDENCE, TRACE_LOSS_CAUSE_UNCONFIRMED, NO_TRACE_LOSS_REPRODUCED, MORE_EVIDENCE_REQUIRED. A cause may remain unknown even if that future run passes.

No medium, large/59.7GB, protected baseline, VM, production or backup/restore operation follows. **Current eligibility: BLOCKED at the offline overhead screen; no exact final launch command or successor hash approval is available.**
