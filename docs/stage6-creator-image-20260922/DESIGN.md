# Clarified TEST image capture contract

Authority: owner's explicit clarification following the early-image review. Frozen checker unchanged; separate TEST candidate only.

| Class | Handle / creation / full image source | Kernel START/STOP and parent | Native PE entry |
|---|---|---|---|
| DIRECT_PROBE | Creator-owned handle, or immediate duplicate of that same handle; creation/image persisted before first debug continuation | Mandatory | Mandatory |
| DIRECT_WORKER | Same creator-owned requirement | Mandatory | Mandatory |
| OS_CONSOLE_HELPER | Creator handle NA; immediate tracer OpenProcess, exact creation match, full image queried while instance remains valid, retained exit/closure | Mandatory | NA under existing OS-helper rules |
| OTHER_INDIRECT_HELPER | No implicit allowance; unclassified instance fails | Mandatory | Must be explicitly reviewed |
| APPLICATION_OBSERVER infrastructure | Existing explicit launcher/observer identity, tracer verification and clean exit; not reclassified as a worker | Mandatory for its captured lifecycle | Existing NA |

The existing narrowly qualified post-exit acquisition exception remains only for OS console helpers: recorded OpenProcess error 87 and attempt BEGIN strictly after canonical kernel STOP, with complete instance/lineage and no contradiction. It is not a retained handle or an image success. Missing records, access denied, missing timing, or direct-process missing handles cannot use this exception. No extension to other helper classes is authorized.

Capture: native_bridge.py immediately duplicates process/thread handles returned by CreateProcess with existing DEBUG_ONLY_THIS_PROCESS. TraceOwned validates PID/thread/creation; add QueryFullProcessImageNameW before its first WaitForDebugEvent/ContinueDebugEvent. Write early-image-PID-creation.json with CREATE_NEW, FlushFileBuffers and exact errors. The final native record includes the successful durable-publication QPC. Qualification requires query <= persistence < PE entry <= kernel STOP and exact canonical creation/image agreement. No new suspension flag, deadline or retry. Failure remains blocking; the existing debugger lifecycle is driven only to collect/close the failed sacrificial process, never to qualify it.

Worker RunQualification already captures an initial creator handle/image; common TraceOwned capture supplies identical per-instance durable evidence for worker and probes. OS helpers remain discovery-based; full-path, creation, query-time and exit checks stay mandatory wherever applicable. Kernel strings and image-file debug records remain corroboration, not replacements for process-handle images.

Early evidence includes source=creator-owned-handle, creator PID, process/thread identity, handle identity, GetProcessTimes creation FILETIME, image, result/error, process state, monotonic query/acquisition times and record identity. Final archive hashes/seals persisted files; analyzer reopens bytes rather than using cached image state.

Validation: original 26 coverage cases with the clarified roles; additional source/time/error/malformed-path/reuse/missing-record cases; rapid real probes; then one fresh kernel qualification with both existing observers. No automatic retry, combined, medium, large or protected run.

Rollback: abandon the new candidate and retain preserved cf20ac6a7a2e4cc69d944d7ffdfbc608 and both archived failed/review records. Production has no changes to roll back.
