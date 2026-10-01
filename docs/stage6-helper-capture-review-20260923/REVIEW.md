# Helper capture timing review — 2026-09-23

**REVIEW COMPLETE — Stage 6 BLOCKED. No implementation or live rerun.**

## Established failure mechanism

The authority tracer recorded START notifications 1.9198–2.3531 seconds after their event timestamps for four console helpers. Each helper had already exited. From the recorded START marker to the handle-image query, the tracer took only 25.2, 38.0, 94.1 and 29.0 microseconds respectively. The image calls themselves took 1.7–5.7 microseconds and returned error 31 with no image.

The run's maximum complete authority callback duration was 0.0056942 seconds. Although its per-row START marker is inside the callback rather than at entry, this aggregate upper bound is far smaller than the 0.9433–1.8912 seconds by which the queries followed STOP. Moving Acquire ahead of serialization within that callback cannot close these particular gaps. The failure is not a multi-second blocking image-query call.

This establishes a late-discovery/live-image-capture mismatch. It does not identify the exact Windows buffering, scheduling or delivery mechanism. Real-time ETW is buffered; Microsoft's documented FlushTimer minimum is one second. That does not promise notification before a short-lived process exits, and is not proof that FlushTimer alone caused these delays. [Microsoft EVENT_TRACE_PROPERTIES](https://learn.microsoft.com/en-us/windows/win32/api/evntrace/ns-evntrace-event_trace_properties).

The inspected code already uses the documented PROCESS_QUERY_LIMITED_INFORMATION right for QueryFullProcessImageNameW. Raising privileges or broadening rights is not justified by these records. The API documentation does not provide a guarantee that image data remains queryable after exit. [Microsoft QueryFullProcessImageNameW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-queryfullprocessimagenamew).

## Independent evidence already present

The existing Toolhelp-based `TreeTracker` in `evidence_support.py` obtained separate handles and images for three failed identities:

| PID / creation FILETIME | Tracker handle retained before kernel STOP | Tracker image |
|---|---:|---|
| 1860 / 134345919680809472 | 0.0081489 s | C:\Windows\System32\conhost.exe |
| 6920 / 134345919680049828 | 0.6241329 s | C:\Windows\System32\conhost.exe |
| 24344 / 134345919680297848 | 0.1271896 s | C:\Windows\System32\conhost.exe |
| 7204 / 134345919676472872 | No tracker row | Missing |

These are handle-based images according to the preserved tracker implementation, not names copied from the kernel stream. However, the existing rows do not record a full query begin/end interval or a process-alive check bounding successful image capture. They cannot retroactively satisfy those predicates. The 8.15 ms remaining lifetime in one case also illustrates the narrow timing margin.

The missing helper's parent is the collector PID 22712. The tracker inventory contains the registered hash worker, sampler and probes, but not the collector root. Its scan discovers only children of existing tracker rows. This explains why that collector-owned helper was outside this particular tracker's discovery set. It is a concrete coverage gap, not evidence that the process was absent.

## Existing contract remains binding

`small_coverage.py` requires the independent helper handle/creation/image/capture evidence. Its qualified post-exit branch requires failed OpenProcess with error 87, recorded acquisition after kernel STOP, canonical lifecycle identity and the other existing conditions. These four rows have successful OpenProcess/creation verification followed by failed image capture; none qualifies.

The historical review `stage6-early-image-20260922/REPORT.md` explicitly warns against expanding the exception to successfully acquired handles without images. The current rejection is therefore correct. No checker change, image substitution, error relabelling or historical PASS conversion is warranted.

## Minimum proposed experiment — requires review before implementation

Strengthen the existing independent tree-handle path instead of relying solely on delayed ETW callbacks:

1. Include the intended collector root in the bounded tracker inventory early enough to cover its own OS helpers. Bind the root by retained handle and creation time; reject mismatched/reused identities. Explicitly document tracker startup ordering. Do not enumerate unrelated processes into the evidence set.
2. Record handle acquisition, GetProcessTimes/GetProcessId, QueryFullProcessImageName begin/end/error, and handle-state observations around image capture. Keep query/synchronize-only rights, exact handle lifetime/closure proof, bounded storage and existing polling limits.
3. Keep discovery provisional until it matches the authoritative kernel PID + creation + sequence/parent-instance evidence. Snapshot parent PID alone must never confer qualification. Reject ambiguous lineage, mismatched images, PID reuse, missing STOP or contradictory exit facts.
4. First validate the new records as supporting evidence only. Any versioned checker integration recognizing this additional independent source must be explicitly reviewed; do not relabel it as the existing authority tracer's capture. Require the same live-image timing, identity and cleanup predicates, and preserve both sources when they disagree.
5. Missing early capture remains FAIL. Polling cannot guarantee catching every short-lived process; this experiment is not a guaranteed completion fix. Do not hold helpers alive, change workloads to remove helpers, enlarge timeouts, increase polling aggressiveness speculatively or broaden the post-exit exception.

Likely files: `evidence_support.py`, the narrow collector/tracker setup in `traced_collect.py` or its existing setup caller, focused tracker tests; only after explicit source-admission review, a separate versioned checker adapter and coverage tests. Exact setup location must be confirmed during the implementation design, before edits. No production/runtime, driver, schema, ACL or privilege change is proposed.

## Focused validation required

Use tiny sacrificial processes only: direct collector-owned helper coverage; worker-owned helper coverage; short lifetime/missed discovery; image-query failure; post-exit capture; PID/parent reuse; wrong creation time; duplicate/ambiguous records; missing kernel edges; handle/native contradiction; missing query timestamps; bounded cleanup. Both success and rejection must be non-vacuous. Preserve the fixed process/heartbeat bounds and every failure.

Only after supporting evidence is proven and any checker-source admission is approved should one fresh small integrated diagnostic be considered. No medium, large, acceptance or protected-baseline run is justified by this review.

Rollback: preserve current frozen candidates/checker; develop any experiment separately and deselect it if it fails. Historical artifacts remain immutable.

## Preservation and remaining uncertainty

Read-only source/evidence inspection and new review artifacts only. All 183 frozen candidate files verified unchanged. The previous 284-member archive's whole-file SHA-256 matches its receipt. Exact identities, timings and inspected source hashes are in `evidence.json`; no protected VM/configuration or production data was accessed. No tracing/UAC process or workload was launched. The previous run's final zero-process/zero-trace census remains historical evidence, not a fresh census this pass.

Original combined ETW loss cause remains UNCONFIRMED. No Windows/filesystem/driver cause is established. Historical 21 AMBIGUOUS / 1 UNMATCHED remain unchanged. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
