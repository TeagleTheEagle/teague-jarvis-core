# Creator-owned image capture and kernel qualification

**KERNEL_AUTHORITY_QUALIFIED** — under the owner-clarified TEST process-class matrix in DESIGN.md and the existing kernel-authority contract. This does not qualify combined, medium, large or protected-baseline validation.

Fresh qualification: `D:\JARVIS-STAGE6-LIVE\c090f8cbc0d444e493f1d801e36fd1bb\code\identity-966b1ef2a95b474ca969a9c315b7b58e`.

Required coverage: **36/36**, missing required **0**, contradictions **0**. This includes **16 explicitly qualified post-exit OS console-helper cases** under the existing narrowly bounded acquisition exception. These are not claimed as successful handle/image queries. Twenty identities have actual matching retained-handle/image evidence; 17 have required native PE-entry evidence. No new exception was introduced.

## Evidence and implementation record

1. **Creation path.** DIRECT_PROBE: qualified_worker.py → probe_timing.py Probe → subprocess.Popen → native_bridge.py CreateProcess hook → immediate process/thread DuplicateHandle → owned_entry.cpp TraceOwned. DIRECT_WORKER: qualified_launch.ps1 → C# Task → owned_entry.cpp RunQualification → CreateProcessW → creator handle/creation/image → TraceOwned. OS console helpers are created by Windows; authority_trace.cpp observes kernel START and opens/retains a handle only after matching its creation FILETIME. No creator handle is returned for those helpers.
2. **Previous failure.** All 16 previous probe process-image queries occurred after kernel STOP and returned error 31. That failure and its archive remain unchanged. The new capture runs before direct process continuation. The underlying Windows error/delivery mechanism is not claimed as diagnosed.
3. **API.** QueryFullProcessImageNameW on the creator-owned process handle or its immediate DuplicateHandle, after GetProcessId/GetThreadId/GetProcessTimes validation. OS helpers retain their approved creation-verified OpenProcess path. Full paths are normalized with QueryDosDevice; names alone never qualify.
4. **Implementation.** TraceOwned now writes exclusive `early-image-<PID>-<creation>.json` using CREATE_NEW and FlushFileBuffers before the first debugger continuation. The record contains source, creator PID, process/thread/handle identity, creation FILETIME, full image, query error/result, monotonic timing and process state. Final native evidence records actual successful persistence QPC. Reopened persisted records, not ephemeral state, feed coverage. Final archive records each file hash.
5. **Suspension.** No CREATE_SUSPENDED flag added. Existing DEBUG_ONLY_THIS_PROCESS and first-debug-event continuation provide the capture boundary. Capture/flush overhead remains inside unchanged deadlines and is measured, not assumed zero.
6. **Creator-owned semantics.** Direct capture uses the original CreateProcess handle or a same-process immediate duplicate; no later PID query. The record's creator PID must match the independently verified kernel parent. The duplicated process handle remains open through TraceOwned exit reconciliation.
7. **Creation semantics.** PID + handle creation FILETIME binds the independent record to the unique kernel scope/PID/creation/process-sequence instance. Later PID incarnations cannot substitute evidence. Handle PID and creator PID also checked.
8. **Image semantics.** Nonempty absolute full path, no NUL/traversal, exact normalized expected image, success/error=0, unsignaled process at capture, and acquisition ≤ query ≤ durable publication < native entry ≤ kernel STOP. OS-helper successful image queries must precede STOP. Query failures remain recorded, not guessed away.
9. **Exit-race validation.** 24/24 real rapid probes passed before the observed qualification. Lifetimes 0.0859461–0.1396755 seconds (mean 0.1040795667). The fresh qualification then validated 16 additional direct probes; all 16 exited before their kernel START callback was processed, while their early creator image evidence was already durable. No instance-bound CIM delivery timing is invented from ambiguous CIM records.
10. **Query-failure tests.** Focused fixtures simulate errors 5 (access denied), 6 (invalid handle), 31 (already exited), 122 (insufficient buffer), and 999 (unexpected error), plus malformed relative/NUL paths, wrong creation, reused PID, signaled-at-capture and late persistence. All reject. These are deterministic checker fixtures, not claims that each Win32 error was induced live. Native capture preserves exact real query errors; no retry-by-PID fallback exists.
11. **Matrix.** DIRECT_PROBE and DIRECT_WORKER require creator-owned handle/creation/image, kernel START/STOP, parent and native entry. OS_CONSOLE_HELPER has creator ownership NA but requires its approved tracer-handle evidence or the pre-existing strictly proved post-exit acquisition disposition. OTHER_INDIRECT_HELPER is rejected unless separately classified. APPLICATION_OBSERVER is explicit infrastructure with existing tracer/launcher closure rules. DESIGN.md defines each class.
12. **Non-vacuous regression.** **44/44 PASS**: original 26 required-evidence cases plus 18 ownership/timing/error/classification cases. Empty handle/image/native evidence, partial coverage, missing helper tracer evidence and unknown helpers fail. Optional and NA cases remain explicit. No `all([])` acceptance.
13. **Worker.** PID 22692, creation FILETIME 134345167228653288. Creator image persisted before its native entry and exit; kernel identity/parent/STOP and exit code agree. Worker passed without a post-exit image lookup.
14. **Helpers.** 18 OS console-helper instances accounted for: 2 successful creation-verified tracer handle/image captures, 16 narrowly qualified post-exit error-87 acquisition records. The latter require acquisition BEGIN strictly after canonical STOP and are not labeled retained handles or image successes. Missing evidence, other errors, contradictions or unknown helper classes still fail. Helper code/exception was not broadened.
15. **Real positive count.** 24 standalone rapid probes plus 16 qualification probes and 1 qualification worker = 41 directly created processes with early image/native evidence. Only the qualification run has complete authoritative kernel/CIM observer coverage; the standalone run is focused direct-capture validation.
16. **PID reuse.** Actual reuse observed: 0. Wrong-incarnation fixtures reject. No deliberate forced-reuse claim; rapid short lifetimes and reused-PID fixture coverage are distinct.
17. **Total required identities.** 36 authoritative captured identities: 16 DIRECT_PROBE, 1 DIRECT_WORKER, 18 OS_CONSOLE_HELPER, 1 APPLICATION_OBSERVER. The outer launcher and kernel observer are explicit infrastructure, separately identity/cleanup verified.
18. **Fully verified.** 36/36 under the clarified matrix, including the 16 existing qualified post-exit cases. Nineteen instances have at least one NA field; none is omitted from coverage.
19. **Missing handle requirement.** 0 after applying the exact existing helper disposition. Actual retained handles: 20; qualified failed acquisition records: 16. Do not read the coverage “handle” row's 36 accepted records as 36 acquired handles.
20. **Missing image requirement.** 0. Actual verified image records: 20 (17 creator-owned + 3 tracer-owned); 16 image fields NA only under the explicit qualified post-exit helper rule.
21. **Missing native entry.** 0. Required native entries 17/17; remaining 19 explicitly NA.
22. **Contradictions.** 0; no authoritative ambiguity or forced identity resolution.
23. **Kernel START.** 36.
24. **Kernel STOP.** 36. Both edges durably persisted: 72 records across 4 segments, sequence/hash/seal/readback checks passed; no ETW loss reported.
25. **Retained-handle agreement.** Creation, exact image, signaled exit, exit FILETIME/code, parent/instance and closure checks passed. Independent original probe handles remain checked in addition to the new image records.
26. **Native agreement.** 17 required PE entries match instance and timing. Early publication precedes native entry in all 17. Maximum image API duration 0.1302 ms; maximum query-through-durable-publication duration 118.7605 ms. These are observed values, not future worst-case guarantees.
27. **False unique matches.** 0. No later PID lookup or nearest-time matching.
28. **CIM secondary.** Enabled, healthy, independently persisted and queue-reconciled: 66 AMBIGUOUS / 8 UNMATCHED, zero forced unique matches. Ambiguity remains visible. These are current-run counts, not replacements for historical 21/1.
29. **Heartbeat.** Maximum interval 1.2792628 seconds; maximum observed age 0.9927536 seconds. Unchanged 10-second threshold.
30. **Deadlines.** 0 violations. Probe 5-second warning, 13.6-second hard deadline and 15-second independent observer period unchanged.
31. **Cleanup.** Worker/application/kernel exited with code 0, native bridge threads closed, retained handles reconciled, queue empty, durable finalization succeeded. Independent final host enumeration: zero matching diagnostic/VirtualBox processes and zero diagnostic trace sessions. No forced termination.
32. **Archive.** Final canonical archive path/member count/hash receipt: archive-verification.json. Before execution, prior 226- and 20-member archives and originals were verified; 1,393 historical/source comparisons passed. Both new live runs and focused results are preserved. No failed historical evidence was overwritten.
33. **Frozen checker.** Unchanged SHA-256 `e6fbefd3fd463c6c8e09d0e8273a81b46ee2806515cae05e7837ea905a3e69d6`. The legacy frozen checker was not modified or relabeled as implementing the new contract. New qualification applies structural/durable checks plus coverage.py under the explicit matrix. All 141 frozen candidate/review source comparisons passed after validation.
34. **Protected VM/configuration.** Not accessed or hashed. VirtualBox not launched. This is an action record, not a fresh protected-source integrity measurement.
35. **Production.** JARVIS production unchanged and not launched. No providers, credentials, production data, environment security settings, ACLs or services changed.
36. **Historical 21/1.** 21 AMBIGUOUS / 1 UNMATCHED preserved unchanged.
37. **Historical causes.** UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED. Successful early capture does not retroactively identify every prior probe/storage/sampler failure cause.
38. **Next proposed gate.** Owner review of the small combined procedure below; not executed.
39. **Final disposition.** KERNEL_AUTHORITY_QUALIFIED, scoped to this fresh run and frozen candidate. Stage 6 itself is not complete. Protected-baseline capture remains unauthorized.

## Exact changes, integrity and rollback

Candidate root: `D:\JARVIS-STAGE6-LIVE\c090f8cbc0d444e493f1d801e36fd1bb\code`.

Changed executable artifacts: owned_entry.cpp, J6OwnedEntry.dll and generated .exp/.obj sidecars. qualified_launch.ps1 changes only its explicit DLL binding to this independent candidate. J6AuthorityTrace.exe, authority_trace.cpp, native_bridge.py, worker, probe, monitor, deadlines, durable sink and frozen cleanup checker are inherited unchanged.

New versioned qualification/evidence tools are in this report directory: coverage.py, analyze.py, fixture tests, preparation/build/rapid-validation/finalization/archive scripts. Exact source/binary before/after SHA-256 values are in preservation-after.json; source diffs are preserved. Build exit 0; PowerShell syntax PASS; no production implementation change.

Rollback: select preserved candidate cf20ac6a7a2e4cc69d944d7ffdfbc608 and its historical disposition if needed; retain both candidate trees and all evidence. Do not delete prior failures. No production rollback is necessary.

## Proposed small combined validation — owner review only

1. Verify this candidate, coverage contract, archive, frozen checker and prior failures; confirm zero diagnostics/traces/VirtualBox processes. Reserve a fresh D: run and use only a small new synthetic 12-file dataset with recorded inventory/hashes.
2. Review the narrow adapter that combines the existing small collector's two-pass hashing and metadata/manifest checks with this qualified kernel/creator-image evidence path. Do not modify the frozen checker or assume a legacy checker PASS implements the amended contract. Freeze and focus-test any required TEST adapter before execution.
3. Obtain the existing per-run UAC approvals for the kernel and independent application observers. Run the small synthetic collector once, with unchanged heartbeat/process/observer deadlines and complete worker/probe/helper class inventory.
4. Require both hash passes equal, source metadata unchanged, complete authoritative kernel records/segments, matching creator/tracer handle evidence and native entry, explicit helper exceptions only, healthy persisted CIM, empty queue, bounded finalization, manifest/hash and zero live identities/processes/traces.
5. Hash-verify the finalized archive. Preserve any failure and stop without retry. Stop after this small gate; no medium/59.7 GB/protected/VM operation follows automatically.

This procedure is a proposal, not authorization or evidence that combined integration has passed. The qualified helper post-exit exception and absence of observed real PID reuse remain explicit limitations. No claim of all possible Win32 failure-path cleanup coverage or power-loss survival beyond the previously scoped durability evidence is added.
