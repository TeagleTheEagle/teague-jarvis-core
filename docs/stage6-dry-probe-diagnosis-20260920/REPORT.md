# Stage 6 dry-run hard-deadline and cleanup evidence diagnosis

**INCONCLUSIVE** — the exact cause of historical PID 9240 remaining alive beyond the fixed deadline is not established. The six-case diagnostic ladder did not reproduce a >13.6-second probe. The closest new whoami lifetime was 10.6020237 seconds. Historical Dry Run #1 remains FAILED; Dry Run #2 and protected hashing were not run. No acceptance thresholds or production code changed.

## 1–2. Exact identity and reconstructed timeline

- PID: 9240; process creation FILETIME: 134343506525182730; parent collector PID: 776 (historical parent creation time not recorded).
- Image: `D:\JARVIS-STAGE6-LIVE\e863e012a81649fe9c82fce9838aa2e3\code\J6Probe.exe`.
- SHA-256: `23240ef9f8b0a9a324110b1c2331de31dc1b0e08f5359cb707e51a939af56cd3`; byte-identical to the inspected `C:\Windows\System32\whoami.exe`. Version: 10.0.26100.1882. It describes itself as displaying logged-on user information.
- Command: that absolute executable with no arguments, shell=False, CREATE_NO_WINDOW, close_fds=True; working directory was the D: candidate code directory. Output was not captured or exposed; stdout/stderr were DEVNULL.
- Same executable hash and launcher semantics as the eight passing repetition/workload runs. Dry-run hashing executes in a separate Python child, not inside this probe.
- The expected work was the ordinary whoami operation and exit. Actual internal calls, loaded DLL paths, security lookup/network activity, opened files, temp activity and internal threads were not traced historically; they are UNKNOWN. The image is native Windows code; it is not a PowerShell/Python script. Installed OS dependencies can still reside on C: although the copied executable is on D:.

| Stage | Seconds after launch / evidence |
|---|---|
| T0 launch requested | 0.0000000 (QPC 1833818671884) |
| T1 CreateProcess returned | 0.0024366 (QPC 1833818696250) |
| T2 retained handle acquired | UNKNOWN exact assignment; bounded by CreateProcess return and Popen return; initial identity capture separately recorded |
| Popen returned | 0.0024802 (QPC 1833818696686) |
| Initial identity recorded | 0.0024965 (QPC 1833818696849) |
| T3 process entry marker | UNKNOWN |
| T4 intended work started | UNKNOWN |
| T5 intended work completed | UNKNOWN |
| T6 process-internal cleanup began | UNKNOWN |
| T7 hard deadline observed | 13.6034202 (QPC 1833954706086) |
| T8 independent observer timeout | 15.0176541 (QPC 1833968848425) |
| T9 process exit began | UNKNOWN |
| T10 kernel handle signaled | UNKNOWN |
| T11 primary STOP callback | 23.6425811 (QPC 1834055097695) |
| T12 primary STOP enqueued | 23.6426092 (QPC 1834055097976) |
| T13 STOP append completed | 23.6455036 (QPC 1834055126920) |
| T14 cleanup fully completed | UNKNOWN exact instant; collector never captured final exit code/kernel exit time for PID9240; later identity scans found no live matching process |

The independent wait lasted 15.0149882 seconds and returned WAIT_TIMEOUT. Immediate retained-handle state at the hard deadline was 258 (nonsignaled). These are real failed observations, not an arbitrary late event callback. Collector producer closure was recorded at +13.6069091 s; failed collector closure at +22.9803186 s. These are campaign cleanup markers, not process-internal cleanup. The exact kernel signal/exit time and exit code were lost historically. STOP receipt is not substituted for them.

## 3–5. Child processes, handles and pipes

Historical PID 9240's child tree was not recorded. The new bounded all-process WMI observation found one conhost.exe START for each of 253 probes, including the native controls. All 253 associated helpers have corresponding observed STOPs. This establishes console-host activity in the new experiment, not its cause or historical presence for PID9240. No retained kernel handles were acquired for those short-lived console helpers; child exit evidence is therefore weaker than probe exit evidence. WMI delivery counters do not independently prove no child event was lost.

Probe handles were retained from CreateProcess and identified by creation time. Existing CPython subprocess source explicitly builds an allowed inheritance list from standard handles when close_fds=True. stdout and stderr point to the null device, not parent output pipes; output-pipe backpressure is not supported by launcher evidence. stdin=None preserves/duplicates the parent's standard input (or creates an empty pipe if absent); the actual historical handle type was not captured. This is not proof that no pipe existed. Native controls additionally inherit only the explicitly listed anonymous mapping handle used for timestamps. No secrets, SID contents, stdin data or environment values were recorded.

The Python workload and resource sampler use stderr pipes, independently of probe stdout/stderr. Successful diagnostic cleanup captures their stderr and exit records. The historical cleanup discarded workload stderr. There is no measured evidence that a pipe, inherited handle, child wait, open file or console host kept PID9240 alive; these remain unconfirmed mechanisms.

## 6. Process-internal instrumentation and timing

The Microsoft whoami binary was not modified, injected or hooked. Its entry/work/cleanup timestamps remain UNKNOWN, even in the new near-reproduction. Instrumented native controls report QPC entry, initialization-complete, work-begin/end, cleanup-begin/end and pre-ExitProcess through an anonymous mapping. Control A performs no intended work; B performs a fixed 10,000-iteration arithmetic loop; D queries its own token without exporting token/user data. These controls do not reproduce all of whoami's account-name/security behavior.

The largest native case was PID18036 during ladder B: CreateProcess 3.3944941 s; entry at launch +3.4086067 s; arithmetic work 0.0000097 s; instrumented cleanup 0.0000046 s. This localizes that control's delay before instrumented work, predominantly inside process creation. It does NOT locate PID9240's historical delay. Another idle control took 1.6734978 s inside CreateProcess, so storage load is not the only context where startup delay occurred.

The final UnmapViewOfFile/ExitProcess/OS teardown cannot write a marker after process death. Retained handles and GetProcessTimes provide independent exit data. UTC/FILETIME↔QPC conversions produced some slightly negative sub-millisecond/millisecond teardown estimates; these are clock-bridge uncertainty, not negative runtime. Use the all-QPC pre-exit-to-observer interval as an upper bound; exact kernel signal instant is UNKNOWN. Raw estimates are preserved, not silently clipped.

## 7. Dry-run versus workload differences

Passing sustained-hash workload: one fixed 1 GiB synthetic file, native unbuffered/sequential ReadFile loop plus SHA-256, duration-bound repeated reads. Failed dry-worker: normal buffered Python open/read, 12-file enumeration, metadata/reparse checks, first SHA-256 inventory, second complete pass/comparison, baseline-style JSON manifest/hash. Same probe image, monitor, resource sampler and finalization barrier.

Historical first inventory file was never recorded. The exact operation during PID9240's lifetime is UNKNOWN: no worker internal trace survived. The first snapshot call and saving its result precede the second pass and manifest generation in source. No completed first/second-pass, manifest or archive evidence exists for the failed dry run. It is therefore unsupported to attribute the failure to archive creation, verification or durable acceptance sealing; those stages were not reached. Source metadata/hash work or the first inventory write could overlap, but the exact subcall is not established.

New ladder instrumentation measures individual reads, hashing, opens, metadata-stage markers and D: evidence writes. Case B's single pass took 35.0451718 s; its longest measured C: read took 4.0195427 s. Cases C–F's two passes finished in approximately 1.96–2.32 s. Cached versus cold I/O and changing host state are uncontrolled variables; no cache flush or security setting change was performed. The test does not prove deterministic equivalence between those host conditions.

## 8. Minimal reproduction ladder

| Case | Subset | Probes / START / STOP | Max lifetime (s) | Max heartbeat (s) | Result |
|---|---|---:|---:|---:|---|
| A | Probe-only, 30 s | 119 / 119 / 119 | 0.3344860 | 1.0584985 | Diagnostic subset completed |
| B | One 12-file hash pass | 93 / 93 / 93 | 10.6020237 | 1.0687262 | Diagnostic subset completed |
| C | Two passes + comparison | 11 / 11 / 11 | 0.0284920 | 1.0671024 | Diagnostic subset completed |
| D | Two passes + manifest/hash | 10 / 10 / 10 | 0.0290310 | 1.0526043 | Diagnostic subset completed |
| E | D + archive/fsync/verification | 10 / 10 / 10 | 0.0283397 | 1.0505788 | Diagnostic subset completed |
| F | E + final synthetic reconciliation; no acceptance seal | 10 / 10 / 10 | 0.0271042 | 1.0496102 | Diagnostic subset completed |

Total: 253 probes (128 unchanged whoami probes, 125 native controls); all retained probe handles signaled, with kernel exit times and zero exit codes captured. One five-second warning (PID24320); no 13.6-second deadline failure. Native controls and whoami alternate, so this is a diagnostic comparison, not the original one-probe-per-second acceptance campaign. No case retried for a pass. Diagnostic processes and artifacts live under `D:\JARVIS-STAGE6-LIVE\631d1b7ca4ff4c509c02a015ff1a6ce6\code`.

## 9–10. Resource and security correlation

Historical counter sampling had only one overlapping observation window: Get-Counter took 33.6280769 s; subsequent process sampling took 0.0047072 s. Aggregate CPU about20.8%, available memory20,734 MiB and point-in-time disk queues0 are samples with inadequate temporal resolution to explain a >15 s process delay. They neither prove nor exclude transient pressure. No probe thread stack was captured historically.

Near-reproduction PID24320 lived 10.6020237 s during case B. Five worker trace records overlap, including a 3.7087978-second C: read. Its conhost START callback arrived at launch +10.8918363 s; probe and helper STOP callbacks arrived around +11.8945 s. Callback timing is delayed observation and must not be treated as process entry or console readiness. Resource polling again straddled the slow interval and did not capture that probe's thread state. See closest-reproduction.json for raw evidence.

Defender and Code Integrity operational logs were enabled but returned NoMatchingEventsFound for historical 04:03:50–04:05:00 UTC. This does NOT exclude image scanning, file filters or security interference. No kernel stack, image-load ETW or file-filter latency trace was collected. No security control was disabled. No particular driver, Defender component, scheduler or filesystem is established as causal.

## 11–12. Kernel ground truth and cleanup audit

For all253 new probes: retained handle, creation FILETIME, kernel exit FILETIME, exit code0, independent observer result0 and explicit parent-handle close were recorded. The monitor's retained handle also exited; workload/sampler helper identities, stderr, times, exits and parent-handle closure were captured. Kernel handle signaling is never used to synthesize STOP events. The 253 START/STOP probe pairs and253 console-helper STOP observations are separate evidence.

Final independent checks: 276 recorded probe/helper/monitor identities, zero unresolved/live matches. Final host scan found zero J6Probe or candidate processes and zero VirtualBox processes. Two child PIDs were reused by unrelated later processes; creation time after the recorded STOP distinguishes them. Nothing was terminated by PID/name.

Historical limitations confirmed in code:

1. `probe_timing.py:finish_observation` raises on a15s observer timeout before collecting current kernel times/exit code, even if the process subsequently exits.
2. `collect.py` overwrites collector-failure.json with a later cleanup exception, masking the original traceback. The primary policyFailure survives elsewhere, but the missing traceback cannot be recreated.
3. Cleanup stops walking retained handles when one observation raises; the handle-verification output may be absent/incomplete.
4. Workload stderr is discarded in the finally cleanup branch, and no explicit handle-close receipt is recorded in the old campaign.
5. The historical probe-only event filter omitted conhost child lifecycles. A later no-matching-PID/creation check establishes current absence, not exact exit time, exit status, complete child tree or absence of an earlier orphan.
6. Historical34 events were enqueued/persisted/removed, queue remaining0; monitor exited1 after rejecting failed producer proof. That supports fail-closed behavior, not successful finalization. Temporary failed evidence remains deliberately retained.

Diagnostic-only strengthening preserves primary-failure.json separately, samples kernel state even after an observer timeout, records bounded post-failure cleanup separately, captures helper stderr and explicit handle closure, and observes child process events. The separate post-failure cleanup observation is NOT a deadline extension and can never make a failed probe eligible. The new ladder did not hit the hard timeout, so this pass does not validate the post-timeout cleanup branch under the same failure. No equivalent correction was applied to the frozen acceptance candidate.

## 13–15. Classification, minimum proposal, uncertainty

**Strongest supported cause category: INCONCLUSIVE.** There is evidence of slow startup in a native control, a slow whoami process during C: reads, and previously unrecorded console helpers. None establishes the exact mechanism for PID9240. Historical absence of internal markers/exit details cannot be repaired retrospectively.

Minimum justified correction proposal: review and transfer only the diagnostic evidence-preservation changes into the validation collector/probe observer: append-only primary/cleanup failures, complete per-handle cleanup sampling despite one failed observer, explicit retained-handle close records, worker stderr retention, and separately classified helper-tree evidence. Likely files: collect.py, probe_timing.py, EventTap.cs/monitor.ps1 (child observation), plus focused cleanup tests. Preserve 5/13.6/15/10-second semantics. A new timeout result must remain a failure.

No probe execution/runtime correction is justified yet. Do not replace whoami, remove console handling, change inheritance or increase a timeout merely from this correlation. The next diagnostic proposal is a bounded console-startup/loader comparison with kernel/image-load evidence sufficient to distinguish initialization versus work/teardown. Its precise tooling and overhead need review before running; it is not implemented here. No production or security changes are proposed.

## 16–22. Regression, heartbeat, finalization and protection status

- Previous five-workload results remain their original PASS; original archive remains unchanged. Acceptance regressions were NOT rerun in this diagnostic-only pass.
- Diagnostic heartbeat maximum: 1.0687262s, below10s. Historical failed dry-run heartbeat maximum remains9.574968s.
- New probe START253 / STOP253; exact queue reconciliation passed in all six diagnostic runs. Child event evidence is explicitly weaker than retained-handle probe evidence.
- Diagnostic collection closed and flushed; acceptance SEAL was disabled. No Dry Run #1 retry, no Dry Run #2, no acceptance commit. Synthetic archive operations in E/F are diagnostic workload components, not Stage6 acceptance.
- Protected VM/configuration access: NONE. No VirtualBox launch, protected hashing, source copying, ACL/security/VM modifications.
- Production JARVIS changes: NONE. Frozen40-file acceptance candidate unchanged. New50-file diagnostic source/hash inventory is separate; no unexpected diagnostic source drift.
- Protected-baseline eligibility: NOT ELIGIBLE / UNAUTHORIZED. Stage6 remains incomplete. HISTORICAL STAGE1 CAUSE: UNCONFIRMED.

## 23. Evidence, preservation and rollback

Historical full848-member archive verified before inspection and final SHA-256 rechecked unchanged: `1497b9124102c4388f967141a44c31f6b7c9e8685643a8f2cc876085be640ef3`. All original failures remain failed. A new report-only TypeError while summarizing a single PowerShell resource object was preserved with its pre-fix source, then corrected only in the offline JSON reader. No instrumentation/run evidence changed.

This report, raw diagnostic source, exact build commands/output, run evidence, source hashes/diff, kernel/child reconciliation and historical reconstruction will be archived under `C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 DRY PROBE DIAGNOSIS 20260920`. Canonical archive verification is recorded separately in archive-verification.json; failure must be reported, never assumed successful. No secrets or .env are included.

Rollback: leave the diagnostic candidate unused after verifying all its processes exited; retain all evidence. The frozen acceptance source is intact, so no runtime rollback, Git reset, security edit, or production operation is necessary. Do not delete failed data.

## Revalidation plan — not executed

After a separately reviewed correction: focused probe tests → existing monitor regressions → queue/collision regressions → finalization regressions → three C: hashing repetitions → full five-workload campaign → Dry Run #1 → Dry Run #2 → durable finalization → archive verification → zero protected access and production unchanged. All existing stop rules remain. Do not start that sequence from this diagnostic result.

**Final status: INCONCLUSIVE. STOP FOR REVIEW.**
