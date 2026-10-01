# Fresh dual-evidence diagnostic design

The old 97-identity run remains KERNEL_ONLY_HISTORICAL_EVIDENCE; application START/STOP was NOT CAPTURED. Its archive and files remain immutable.

Independent collection paths:

1. `app_monitor.ps1`: real Win32_ProcessStartTrace and Win32_ProcessStopTrace CIM subscriptions. The application receives notifications through PowerShell's event queue. The unchanged ExactEventQueue records receipt/enqueue QPC, persists the original notification, and removes that exact object reference. A separate receipt records completion. EventIdentifier is diagnostic metadata, never an identity/removal key. EventTap independently records callback and enqueue observations. This stream never reads or derives events from the ETW output.
2. `kernel_trace.cpp`: a separate native realtime Microsoft-Windows-Kernel-Process ETW session. It captures kernel creation FILETIME, sequence identity, parent sequence, image and kernel exit; retains handles when OpenProcess succeeds. Both paths rely ultimately on Windows, but are distinct subscriptions and consumer/persistence paths. They are not assumed statistically independent or infallible. Any missing counterpart fails reconciliation.
3. `evidence_support.py`: launcher-created process handles and live Toolhelp-discovered child handles. Query/synchronize rights only, with creation time, signal state and exit time/code. No termination rights or PID-only exit inference.

The two monitors start before the stress process. Infrastructure (the outer PowerShell launcher and observers) is recorded separately from the stress collector and its complete descendant tree. The latter is the tracked validation set. Unrelated process metadata in the broad CIM subscription has no command lines, environment, credentials or contents, and is not counted as a probe. Scope filtering must be corroborated by expected launches and synthetic child markers; it must not conceal a missing helper.

Correlation uses kernel PID+creation FILETIME+process sequence, parent identity and image. A CIM event only has PID, parent, image name and provider time; it may bind only when a single kernel lifetime for that PID exists in the capture and the parent/image agree. PID reuse or ambiguity fails closed. WMI TIME_CREATED remains a provider event timestamp, not a kernel creation timestamp. Kernel and retained-handle path spellings must use a captured Windows volume mapping when compared, never basename-only equivalence for full paths.

For the no-handle alternative require the recorded beginning of OpenProcess, not its return time, to be strictly later than the kernel exit QPC. Capture the Win32 failure immediately. Generic access denial, equal timestamps, missing/error timing or conflicting retained evidence cannot qualify.

Application START and STOP must be separately persisted and have unique matching queue receipts. Both kernel create/exit records remain mandatory. Missing events cannot be reconstructed from a handle, ETW counterpart or PID absence.

All active state and temporary files are on the fresh bounded D: run. Existing queue reference semantics and deadlines remain unchanged. App event finalization uses the existing 4.6-second quiet interval and 45-second bound, then closes subscriptions, drains residue, verifies the exact queue and flushes evidence durably. A 10-second monitor heartbeat interval remains a failure. No accepted baseline, VM, production path or acceptance dry run is involved.

Phase D gathers and audits fresh evidence first. Only after that model is demonstrably usable will a cleanup checker accept HANDLE_CONFIRMED_EXIT or KERNEL_CONFIRMED_POST_EXIT_HANDLE_ACQUISITION. All other cases remain INSUFFICIENT_EVIDENCE. Cleanup success never changes a primary failure into a pass.
