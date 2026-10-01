# Early image capture — required helper-contract review

Final status: **CONTRACT_REVIEW_REQUIRED**.

No candidate source, binary or checker was modified. No observer, probe, worker or qualification run was launched. This pass performed preservation verification, read-only source inspection, host process/trace inspection and new review-evidence generation only.

## Exact stopping condition

The current request, Phase 12, states: “If contract requires handle-derived image but no safe creator-owned handle exists: STOP and return CONTRACT_REVIEW_REQUIRED.”

The existing helper path meets that review condition: OS-created console helpers have required handle-derived image evidence when acquisition succeeds, but their creator-owned handles are not returned to the JARVIS TEST launcher. The current tracer calls OpenProcess after kernel discovery. That is an independent, creation-verified retained handle, but it is not the creator-owned handle required by the new wording. The existing post-exit exception covers only specifically evidenced failed acquisitions after STOP; it cannot be widened to remove the image requirement for successfully acquired helper handles.

No claim is made that Windows has no conceivable mechanism to obtain another process's handles. The inspected, approved TEST architecture has no safe creator-handle transfer channel for OS-created conhost processes. Adding one, changing how helpers are created, or silently treating discovery handles as creator-owned would exceed this correction's established evidence semantics.

The previous contract H1 and required-coverage DESIGN.md permit the established helper OpenProcess path. The new request also says indirectly created helpers should follow their approved requirements (Phase 5), but Phase 12 adds the explicit stop condition. Owner clarification is required rather than assuming that condition does not apply.

**Proposed narrow clarification, not applied:** creator-owned capture is mandatory for directly launched probes/workers/helpers. OS-created console helpers retain the existing kernel-discovery → immediate OpenProcess → creation match → QueryFullProcessImageName → retained exit/closure evidence, with only the already approved strict error-87 post-exit exception. Any missing required helper evidence or contradiction still fails; no new waiver is proposed.

## Creation-path inspection

Candidate root: `D:\JARVIS-STAGE6-LIVE\cf20ac6a7a2e4cc69d944d7ffdfbc608\code`.

| Class | Creator / call sequence | Handles and execution | Current image capture / consumer |
|---|---|---|---|
| Probe | qualified_worker.py → Probe in probe_timing.py:17–31 → subprocess.Popen → native_bridge.py:create:42–48 → original _winapi.CreateProcess | Returns process/thread handles on the native bridge thread; immediately duplicates both at native_bridge.py:28. Popen retains its process handle. Existing DEBUG_ONLY_THIS_PROCESS is added at line 45; no CREATE_SUSPENDED is added. | TraceOwned verifies process/thread IDs and creation FILETIME at owned_entry.cpp:24. No early process-handle image query occurs there. authority_trace.cpp:37 queries later after ETW discovery. analyze_v2.py consumes that late field. |
| Worker | qualified_launch.ps1 → C# task → owned_entry.cpp:RunQualification:88–108 → CreateProcessW | Returns process/thread handles; keeps them through TraceOwned and exit. Existing CREATE_NEW_CONSOLE, hidden window and DEBUG_ONLY_THIS_PROCESS. | GetProcessTimes + QueryFullProcessImageNameW at line 104 before TraceOwned; exclusive durable worker-created.json at line 106. Existing qualifier also checks later tracer capture. |
| OS console helper | Windows console infrastructure; no explicit conhost CreateProcess call in the qualification launcher | The TEST launcher receives handles for its directly created child, not for the OS console helper. No creator-owned helper handle transfer is implemented. | authority_trace.cpp callback at line 52 records kernel identity then Acquire at line 37: OpenProcess, creation match, image query, retain until exit. This is discovery-based, not creator-owned. |
| Application observer / its console helper | qualified_launch.ps1 Start-Process with approved UAC; helper is OS-created | Observer process object is retained by launcher; helper has the same discovery limitation | Tracer captures observer/helper handle evidence; launcher verifies observer exit. No change proposed to observer privilege or tracing scope. |

No new launch experiments were necessary to establish this source-level distinction. Exact existing full paths and source hashes are preserved in preflight.json and the referenced immutable prior archive.

## Minimum direct-process implementation proposal — not implemented

For directly created probes, add one full-image query using the already duplicated creation handle at the beginning of TraceOwned, immediately after matching GetProcessId/GetThreadId/GetProcessTimes and before any ContinueDebugEvent. Persist PID, creation FILETIME, full image, source=creator-owned-handle, handle acquisition/query QPCs, query result/error, process state and a unique record identity with exclusive creation and durable flush. Hash it during final evidence sealing. Preserve failures and do not retry via PID lookup. Bind later kernel/native/exit evidence to that same identity.

The existing debugger gate is a promising boundary: TraceOwned currently consumes and continues the initial debug event. No new CREATE_SUSPENDED flag is proposed. This design remains unimplemented/unvalidated; elapsed capture/flush overhead must be measured and remains inside unchanged deadlines. It must not be represented as zero overhead or as having validated historical timing equivalence.

Worker early capture already exists; it needs explicit durable record consumption and consistency checks, not an unnecessary replacement launch path. All required query-error simulations, rapid real processes and one fresh qualification must follow implementation and the helper-policy clarification. Combined validation remains unauthorized.

## Mandatory disposition record

All numerical process results below are explicitly **preserved prior-run evidence**, not a new acceptance result.

1. Current creation paths: table above, including actual APIs, handles and call sites.
2. Late-image mechanism: preserved 16 probe image queries began after their matching kernel STOP and returned error 31. This establishes late capture; underlying Windows error mechanism and historical delay causes remain unconfirmed.
3. Image API: QueryFullProcessImageNameW on the same creation-verified process handle; exact full-path normalization, never basename/PID-only guessing.
4. Early implementation: proposed above; not implemented because Phase 12 review condition applies.
5. Suspension: no new suspension proposed or applied. Existing DEBUG_ONLY_THIS_PROCESS/ContinueDebugEvent boundary inspected; no new timing claims.
6. Creator ownership: available for direct probe/worker handles; unavailable through the current approved OS-helper launch path.
7. Creation identity: actual handle GetProcessTimes creation FILETIME, matched to PID and later canonical kernel process sequence/capture scope.
8. Image identity: same retained handle's full path; no parent image, command line, kernel string, nearest timestamp or later reused PID substitution.
9. Exit-race tests: NOT RUN this pass. Prior run's delayed image queries remain failed.
10. Query failure tests: NOT RUN this pass; required after an authorized implementation.
11. Matrix: probes/workers require handles, creation, full image, native entry, kernel START/STOP. OS helpers require kernel identity/START/STOP and retained handle/creation/image/exit when acquisition succeeds, with the existing narrowly proved post-exit exception; native entry NA. Creator ownership for OS helpers is the unresolved new condition.
12. Non-vacuous regression: prior 26/26 evidence reverified unchanged; NOT rerun and not claimed as new implementation validation.
13. Worker coverage: prior PASS, including native entry; unchanged.
14. Helper coverage: prior PASS under discovery-handle rules; NOT proof of creator-owned capture.
15. Real positive validation count this pass: 0.
16. PID reuse: no new attempt; prior fixtures and zero observed live reuse remain unchanged.
17. Total required identities: prior 36 (34 worker/probe/descendants plus 2 observer infrastructure).
18. Fully verified identities: prior 20 under the old matrix, including 16 strictly qualified post-exit helper cases, not 20 successful full-image queries.
19. Missing handle count: prior 0 under its explicit exception rules; 20 retained handles plus 16 qualified acquisition records, not 36 handles.
20. Missing image count: prior 16, all probes.
21. Missing native entry: prior 0; 17 native entries, 19 NA.
22. Contradictions: prior final coverage 0; initial format rejection remains preserved separately.
23. Kernel START: prior 36.
24. Kernel STOP: prior 36.
25. Retained agreement: prior retained creation/exit agreement preserved; no current requalification.
26. Native agreement: prior 17 entries preserved; no current requalification.
27. False unique matches: prior 0; no new correlation.
28. CIM secondary: prior current-run 66 AMBIGUOUS / 16 UNMATCHED, preserved and not force-matched.
29. Maximum heartbeat: prior 1.5740427 seconds; no monitor launched this pass.
30. Deadline violations: prior 0; no deadlines changed.
31. Cleanup: fresh host inspection PASS, zero matching diagnostic/VirtualBox processes and zero diagnostic trace sessions. No termination required.
32. Archive: previous 226 members and all referenced originals hash-verified; 1,374 preservation comparisons passed, including 138 frozen candidate files. New review archive verification is recorded in archive-verification.json.
33. Frozen checker: unchanged `e6fbefd3fd463c6c8e09d0e8273a81b46ee2806515cae05e7837ea905a3e69d6`.
34. Protected VM/configuration: not accessed. This is an action record, not a new protected hash proof.
35. Production: unchanged; no production launch or access needed.
36. Historical 21 AMBIGUOUS / 1 UNMATCHED: unchanged, distinct from the latest prior run's counts.
37. Historical causes: UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
38. Next gate: owner clarification of OS-helper creator-ownership wording, then minimum direct-process capture correction, focused negative/rapid-exit tests and one fresh kernel qualification. No combined/medium/large run.
39. Final status: CONTRACT_REVIEW_REQUIRED.

Only new review/preflight/archive files were created in this pass. No candidate or accepted application source changed. Rollback requires no runtime action; retain this review alongside prior evidence. Do not delete historical archives.
