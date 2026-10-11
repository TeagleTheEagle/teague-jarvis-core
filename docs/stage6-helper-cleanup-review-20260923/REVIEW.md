# Stage 6 — collector console-helper cleanup ordering diagnosis

STRONG_CAUSAL_EVIDENCE — read-only diagnosis complete. No correction or rerun.

## Finding

The collector discovers its own console helper, but requires every discovered descendant to exit before the collector returns. In the preserved run that helper remained alive until the collector exited. The newly expanded discovery scope therefore encounters a cleanup-ordering conflict. This is not a lost STOP event or a mere delayed callback: the local retained handle was genuinely unsignaled (258) at the failed cleanup check, and the later kernel STOP agrees with the external retained-handle exit.

The code ordering is established; the complete Windows console lifetime mechanism is not proven by this one run. No broad claim that every conhost.exe necessarily depends on its parent is made. Historical unrelated delay/tracing causes remain UNCONFIRMED.

## Exact identities and observed order

- Collector: PID 15280, creation FILETIME 134345949607329466, kernel sequence 55621; parent launcher PID 24608.
- Helper: PID 8436, creation FILETIME 134345949607928089, kernel sequence 55622, parent sequence 55621 / PID 15280. Image is conhost.exe, confirmed both by local live handle capture and external tracer image.
- Native collector PE-entry, retained handle and kernel lifecycle evidence identify the same collector instance.
- Last hash-worker return to failed tree-result timestamp: 20.0963813 seconds. This brackets the existing 20-second cleanup wait plus surrounding overhead; the exact tree.finish entry timestamp is UNKNOWN.
- At tree result QPC 4277813884778: helper still 258; local signalObservedQpc/exitFiletime absent; local closed=false. Every other retained tree row closed.
- Failure recorded QPC 4277814179328: tree-cleanup / Incomplete retained tree.
- Collector RETURN QPC 4277815674163, final shutdown marker QPC 4277815677980.
- Collector kernel STOP QPC 4277816127579, exit code 1; native retained handle independently signaled QPC 4277816159198.
- Helper kernel STOP QPC 4277816145229, exit code 0: 1.765 ms after collector STOP and 226.0451 ms after failed local tree result. External helper retained handle signaled QPC 4277816289425 and closed.

All values use the recorded QPC frequency 10,000,000. timeline.json preserves raw values and derived offsets. No unavailable timestamp is inferred.

## Source path and acceptance distinction

In the frozen candidate, large_collect.py invokes tree.finish(root,20) before returning and fails if supporting evidence/exit/close/thread predicates are false. evidence_support.py adds the collector anchor as a discovery parent; the anchor itself is excluded from exit rows, but its console child is not. TreeTracker.finish waits for all descendant signals, and closes only signaled descendant handles. finish_support also requires every descendant exit and closure.

traced_collect.py cannot return from collector.main, close the native bridge and leave the process until this local cleanup finishes. The launcher/native observer can see the collector and console-helper exits afterward. This explains the ordering mismatch visible in the evidence without requiring a timeout increase.

The v2 checker rejected at OBSERVER_CLEANUP because its combined predicate includes launcher.error is None. launcher.error was Collector failed. All actual observer exits were zero and true. The label does NOT establish an observer cleanup defect. Primary failure remains the collector's retained-tree contract. The v2 finalizer was not run.

Exact line references/excerpts are in source-references.json. No checker, source, deadline or Windows setting changed.

## Minimum proposed correction — NOT implemented

Use a reviewed two-phase cleanup contract only for independently classified collector-lifetime console helpers:

1. Before collector exit, retain and durably record exact helper identity, live image/query/acquisition timing, collector/kernel-parent binding and every handle-close result. Close the collector's own query handle explicitly; never claim that closing it proves process exit. Preserve direct-worker/probe cleanup requirements.
2. Record a distinct pending-external-exit disposition, not allExited/PASS. It must be tied to the exact collector and kernel instance, never inferred from name or PID alone. Require independent external retained-handle ownership established for that instance before relying on handoff; if this cannot be proven from the existing control surface, do not improvise a handoff.
3. After collector termination, require the existing external kernel/native/retained-handle evidence to prove collector and helper STOP, matching creation/image/parent/exit, handle closure, zero loss and bounded observer shutdown. Only then may the versioned checker/finalizer accept the complete cleanup transaction. Missing, contradictory or still-live evidence fails.
4. Do not exempt all console processes, manufacture STOP, ignore unclosed handles, broaden error-87 handling, alter fixed waits or retroactively pass the old run.

This changes when a narrowly identified helper's required exit proof may be completed. It requires an explicit contract/implementation review before modification. Current structural verifier and adapter require every tracker descendant already exited/closed; their pending-state semantics would also need review. Existing external ownership acknowledgement capability has not been established in this read-only pass.

Likely affected separate TEST copies: evidence_support.py, large_collect.py, tracker_adapter_v2.py, supporting structural verifier and versioned coverage/check/finalizer. Launcher coordination only if an explicit, reviewed external ownership proof is needed. Do not change native/authority mechanisms or assume that new coordination is already authorized.

## Focused validation proposal

First offline transition/negative tests: pending is not success; wrong parent/creation/sequence, missing external handle, contradictory image/exit, failed local close, stale binding, early finalization and external timeout all fail. Normal workers must still exit before local cleanup. Test that unrelated helpers cannot enter this class.

Then, only after approval, one small sacrificial fixture reproducing the actual collector-console ownership/lifetime and externally proves both exits. Capture a real pending state before collector exit and final closure afterward. Preserve all failures; no retry or integrated acceptance run without authorization. Keep existing timeouts. No medium/large/protected work.

Rollback: leave the current candidate unchanged and retain all failed evidence. No production rollback required.

## Preservation and disposition

194 candidate source hashes unchanged. Failed live archive SHA-256 unchanged; all 79 archived live-run file hashes still match. No process/observer launched; no live census claimed for this diagnosis. The last preserved post-run census remains zero matching processes/traces at 2026-09-22T23:57:11.9195169Z. Production and protected VM/configuration untouched.

Stage 6 remains INCOMPLETE. Historical 21 AMBIGUOUS / 1 UNMATCHED unchanged. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

NEXT ACTION: Review a bounded two-phase cleanup design and its external handle-ownership proof before authorizing implementation. STOP for owner review.
