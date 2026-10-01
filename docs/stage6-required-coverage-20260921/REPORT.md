# Required evidence coverage — stopped qualification

Final status: **REQUIRED_EVIDENCE_COVERAGE_STILL_DEFECTIVE**.

Fresh run: `D:\JARVIS-STAGE6-LIVE\cf20ac6a7a2e4cc69d944d7ffdfbc608\code\identity-41c2bfafcfa34b098bc2eb7d902a2535`.

The non-vacuous checker correctly rejected incomplete image coverage. No retry, combined validation, medium validation, large dataset run or protected baseline capture occurred.

1. **Class matrix:** see DESIGN.md. Controlled probes/workers require kernel START, canonical identity, STOP, retained handle, creation time, full handle-derived image, native PE entry, exit and parent identity. Console helpers retain the existing strictly proved post-exit error-87 exception; native entry is not applicable to OS-created helpers. Observer infrastructure is explicitly accounted for, not silently omitted.
2. **Previous defect:** the preserved draft iterated supplied verification lists; empty lists produced no contradictions and could pass. That old source and failed empty-list case remain unchanged.
3. **Correction:** coverage.py evaluates an independent required identity set covering every authoritative kernel row, classified against declared worker/probe/observer identities and exact helper image. Missing lists/partial sets fail. Exact image paths replace basename equivalence. Duplicate or unexpected identities fail. The live analyzer requires both the existing structural checks and the new coverage result; structural component PASS alone cannot qualify.
4. **Accounting:** each evidence type has explicit valid/contradictory/missing/NA states. Optional annotations have an explicit optional state. Post-exit qualifications are separately identified and cannot be claimed by controlled probes/workers. See analysis-v2/coverage-live-result.json for every identity.
5. **Worker cause:** the previous tracer retained its handle but never queried a full process image; the PowerShell launch bypassed native entry tracing. This was a capture-path omission, not proof of Windows access denial.
6. **Worker correction:** a fixed qualification-only native export uses the existing own-child debugger. It retains the CreateProcess handle, queries creation/image before debug continuation, records worker-created.json, traces PE entry and closes handles after exit. The dedicated C# task allows existing observer closure/release-handles sequencing. The hidden console workload is preserved. Worker PID 8888, creation 134344510029935962: complete verification in this run.
7. **Helper cause:** the previous tracer retained the long-lived worker console helper but did not query its image. Short-lived console helpers also have the pre-existing discovery-after-exit race.
8. **Helper correction:** immediately after OpenProcess and matching GetProcessTimes, QueryFullProcessImageNameW records the full image/error and query QPC interval. Worker helper PID 9516, creation 134344510030508859: complete required verification; native entry NA. Sixteen short-lived helpers meet the existing error-87 post-exit exception; they are not reported as successfully image-queried.
9. **Image semantics/current blocker:** full process-handle QueryFullProcessImageNameW, normalized through QueryDosDevice; no process-name substitution. All 16 controlled probes have error 31 and empty image results. Every failed query began after that identity's kernel STOP. Original retained probe exit evidence and debugger file-handle image paths exist, but the new strict process-handle requirement does not silently substitute those paths. The source of delayed callback delivery or underlying Windows error mechanism is not established. See image-query-failure.json.
10. **Negative tests:** 26/26 deterministic coverage cases pass, including all 13 requested categories. Empty handles and natives now fail specifically. These tests establish checker behavior, not real-process acceptance.
11. **Positive tests:** fixture complete coverage passes; real worker/helper coverage passes; real probes retain valid creation/exit/native evidence but fail the required process-handle image check. Full real positive coverage therefore does not pass.
12. **PID reuse/exit race:** deterministic later-incarnation, early-exit, missing-query and retained-after-exit fixtures pass expected dispositions. No actual PID or parent PID reuse observed in this live run. Do not represent fixtures as observed Windows reuse.
13. **Authoritative identities:** 36, 72 durable lifecycle records across 4 segments.
14. **Required identities:** 36 in coverage, including 2 explicitly classified application-observer infrastructure instances; 34 worker/probe/descendant instances.
15. **Verified identities:** 20 under the matrix: 4 with complete required direct handle/image evidence and 16 with the narrowly qualified helper post-exit exception. This is NOT 20 successfully queried images.
16. **Missing required evidence:** 16 image results, all controlled probes.
17. **Contradictory evidence:** 0 in final coverage. A separate initial adapter-format rejection is preserved below.
18. **Handle coverage:** 20 retained acquisitions and 16 qualified post-exit acquisition records; 36 accounted for. The latter are not retained handles.
19. **Image coverage:** 4 valid / 16 missing required / 16 NA under the explicit post-exit exception. Twenty applicable image requirements; four satisfied.
20. **Native coverage:** 17 valid (16 probes + worker); 19 NA (OS console helpers + application observer). No missing mandatory native entry.
21. **Kernel START:** 36.
22. **Kernel STOP:** 36.
23. **False unique matches:** 0; no authoritative identity ambiguity. Current supporting CIM: 66 AMBIGUOUS, 16 UNMATCHED; zero forced matches.
24. **Maximum heartbeat:** 1.5740427 seconds; maximum observed age 1.0187707 seconds, below unchanged 10-second bound.
25. **Deadline violations:** 0. Existing deadlines unchanged.
26. **Cleanup:** launcher reports worker/application/kernel exited with code 0; native bridge threads closed; queue reconciled. Independent final host inspection reports zero matching diagnostic/VirtualBox processes and zero diagnostic trace sessions. No forced termination.
27. **Archive:** archive-verification.json records the final canonical archive path, member count and SHA-256 receipt. Previous 101- and 402-member archives and their original files were verified; 1,011 preservation comparisons passed. Historical failed evidence remains unchanged.
28. **Frozen checker:** unchanged SHA-256 `e6fbefd3fd463c6c8e09d0e8273a81b46ee2806515cae05e7837ea905a3e69d6`. All 138 newly frozen candidate files remain unchanged after execution. Exact before/after source/binary hashes and source diffs are recorded in preservation-after.json and *.diff.
29. **Protected VM/configuration:** not accessed. No protected preservation hashing was performed; this statement describes actions taken, not a new protected hash proof.
30. **Production:** no production JARVIS change or launch. Only separate TEST validation sources, binaries and evidence changed.
31. **Historical 21/1:** preserved 21 AMBIGUOUS / 1 UNMATCHED; not replaced by current counts.
32. **Historical causes:** UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
33. **Next gate:** review creator-side probe image capture before debug continuation, using the already-owned process handle and exact creation identity. Do not increase deadlines or substitute names. A future authorized correction should preserve this failed run, test the capture path and repeat fresh kernel qualification before proposing combined validation. No such further capture correction or rerun was performed after mandatory missing evidence was found.
34. **Disposition:** REQUIRED_EVIDENCE_COVERAGE_STILL_DEFECTIVE. Kernel authority is not qualified; protected-baseline eligibility remains blocked.

## Preserved transitional failure

Initial analysis stopped with HANDLE_CREATION_CONFLICT because the new tracer emitted string `0` for unavailable handle-created values. All 16 were already-proved post-exit console-helper acquisition failures. analyze_v2.py adapts only that exact proved sentinel to null for the supporting CIM correlator; raw evidence is untouched and strict kernel/coverage checks still use it. Every adaptation is listed in analysis-v2/format-adaptation.json. The original analyze.py, failure record and output are retained. No failed handle/image requirement was changed into a success by this adapter.

## Exact changes and rollback

Separate candidate only: authority_trace.cpp + J6AuthorityTrace.exe; owned_entry.cpp + J6OwnedEntry.dll and compiler sidecars; qualified_launch.ps1. New review/coverage/test/analysis/preservation tools are under this report directory. All unchanged inherited sources remain preserved. Compiler emitted one pre-existing-style variable-shadow warning in authority_trace.cpp; builds succeeded. No frozen checker modification.

Rollback is to abandon this candidate and use preserved candidate `a684e9f6f9ae4826af45c0a04c18d839`; do not erase either candidate or historical failures. No production rollback is needed. Future cleanup of large evidence/datasets is not authorized here.

## Limits

No full monitor/large/combined acceptance was rerun. Durability behavior was validated on this run through existing segment/hash/sequence checks; no new power-loss claim. The new qualification-only native wrapper reuses existing debugger behavior; this run does not prove every Win32 failure cleanup path. The formatting adapter and new capture path remain TEST candidates. A passing component or healthy heartbeat cannot overcome missing required image evidence.
