# JARVIS Stage 6 — kernel child/startup trace diagnostic

Final status: **INCONCLUSIVE**. New kernel identity reconciliation is validated for the recorded sacrificial trees, but a complete retained-handle proof is still unavailable for very short-lived helpers; the existing collector still fails its stricter polling-only check. The long-running historical process cause remains unconfirmed. This is not Stage 6 acceptance or permission to hash protected artifacts.

## 1–4. Counts, categories and exact reasons

Historical population: **217 helpers, 130 retained, 87 unresolved acquisition gaps**. All 87 have individual records in `historical-87-coverage.json`, classified **UNKNOWN**. The old polling observer silently skipped failed `OpenProcess` calls and did not timestamp discovery/open attempts. Three old image-query exceptions (31, 5, 5) lack per-process association, so they cannot be assigned to those 87. Absence of an acquisition record does not prove the process had already exited. Earlier successful STOP matching does not recover a missing handle.

Final-build K8: **97 scoped processes = 94 retained + 3 explicitly justified nonretained**, zero unexplained new identity gaps. This includes 24 principal probes and **73 helpers/collector processes: 70 retained + 3 nonretained**. Observed images: {'conhost.exe': 48, 'J6Probe.exe': 24, 'python.exe': 25}.

Final-build K9: **30 scoped processes = 28 retained + 2 nonretained**, zero unexplained identity gaps. Seven are principal probes; **23 are helpers/launchers: 21 retained + 2 nonretained**. Counts include diagnostic launchers and their console helpers; they are not silently omitted.

Each final nonretained case records immediate **OpenProcess error 87**, kernel start and stop events sharing PID, creation FILETIME and process sequence number, and an acquisition attempt later than the kernel stop timestamp. The exact observed category is `OPEN_ERROR_87_AFTER_KERNEL_EXIT`; no access-denied or PID-reuse case is relabelled as an exited process. Their **handle coverage remains INCOMPLETE**, while their kernel identity/exit coverage is complete in these traces. Per-process reasons and timings are in each `kernel-reconciliation.json` and `etw-result.json`.

## 5–7. Architecture, retention and startup tracing

An existing PowerShell launcher establishes its PID plus kernel creation time. It starts a UAC-approved `J6KernelTrace.exe` session before launching probe work. The native consumer retains the launcher handle, enables only Microsoft-Windows-Kernel-Process keyword 0x10 in a unique temporary realtime session, and records scoped descendants. It uses installed Windows ETW/TDH APIs: no driver, persistent channel, ETL, registry change, security change or command-line capture.

Installed event schemas were observed directly: **ProcessStart v4 / ProcessStop v2** provide CreateTime, ProcessSequenceNumber, ParentProcessSequenceNumber, ExitTime and ExitCode. QPC event timestamps distinguish kernel occurrence from callback delivery. Parent sequence/creation/exit bounds are checked; PID alone is insufficient. Retained handles use QUERY_LIMITED_INFORMATION and SYNCHRONIZE, never termination rights. Existing explicit-launch/Toolhelp handles are reconciled against ETW identities and exits. WMI child notifications provide an additional comparison on K9.

Timeline sources: T0/T1 main launch/CreateProcess return and T2 retained handle come from `probe-timings.json` or `*-cleanup.json`; T3/T4 kernel notification/acquisition from ETW; T5 and synthetic work/cleanup markers from `internal-*.jsonl`; T9/T10 kernel exits from ETW/retained handles; T11 callback and T12 WMI persistence from `tap.json`/`events.jsonl`; T13 from cleanup receipts and launcher results. **The unchanged Microsoft whoami principal probe has no internal entry/work/return marker: those stages remain UNKNOWN.** A kernel process-start event is not proof that application main has begun.

Live state remains on `D:\JARVIS-STAGE6-LIVE\991e246fb08b45a3904e4cadfa8f4e99\code`. No active evidence uses the archive destination. Final native evidence uses CREATE_NEW and FlushFileBuffers; session stop, ProcessTrace completion and event/buffer-loss counters are recorded. All temporary sessions ended. Windows DLL/runtime loading still uses installed C: dependencies; these are not claimed to have moved to D:.

## 8–9. Console helpers and Job Objects

`conhost.exe` children are real observed participants, not ignored. Python fixture children can outlive their parent; parent-first/orphan fixtures retain or kernel-track them through exit. The observed tree also includes Python launchers, workload helpers, PowerShell telemetry and console children. Native probes use CREATE_NO_WINDOW. K9 principal stdout/stderr remain DEVNULL; synthetic fixture output is concurrently drained and bounded, with byte counts, EOF, errors and hashes. No shell wrapper is inserted into principal execution. OpenConsole/cmd and external security service helpers were not established by these traces; their absence from the scoped descendant tree does not exclude service-mediated work.

Jobs can improve containment, but assignment/breakaway/nesting and kill-on-close policies can change process behavior. Their completion-port messages alone are not a universal lifecycle delivery guarantee. **No Job Object was added**, preserving comparison with historical process creation. Review sources: [Microsoft Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects), [EnableTraceEx2](https://learn.microsoft.com/en-us/windows/win32/api/evntrace/nf-evntrace-enabletraceex2).

## 10–13. Stress, reproduction, timing and dependency findings

K8 final build: PASS for scoped kernel identity/exit reconciliation and the explicit retained-plus-justified-nonretained target. 36 explicit parent launches, 12 synthetic leaf children, all observed console descendants and collector account for 97 identities. Final helper counts above exclude the 24 principal probes. Earlier stress: 97 = 90 + 7, preserved separately. Both report zero ETW loss/fault counters.

Four narrow **two-pass sacrificial C: hashing** comparisons ran; the fourth used the final immediate-error-capture build. No acceptance manifest/campaign/dry-run sealing occurred. None reproduced >13.6 seconds. Their main-probe totals are **37 START/STOP pairs**. Native controls stayed separately labelled; whoami was not replaced. No 15-second observer failure occurred. Current read calls were short (maximum across comparisons about 0.03824 s), so these runs did not recreate the earlier multi-second C: stalls.

| Run | Main probes | Max kernel lifetime s | Max heartbeat interval s | Max sampled age s | Retained scoped | Nonretained scoped | Kernel identity result |
|---|---:|---:|---:|---:|---:|---:|---|
| kernel-e-249991cf96074a2f91b68d45ad58de7a | 7 | 0.0303382 | 1.4277857 | 1.4085805 | 28 | 2 | PASS |
| kernel-e-d8aa353354d04839859bdc30d711aaed | 7 | 0.0291423 | 1.0525919 | 0.8219372 | 28 | 2 | PASS |
| kernel-e-e8058af96b8b4b8b8812a8e534217a88 | 15 | 0.0582957 | 1.0568593 | 0.8707799 | 44 | 2 | PASS |
| kernel-e-f1472451c39c423c954b537bf56b7690 | 8 | 0.0300976 | 1.0483104 | 0.842879 | 30 | 2 | PASS |

All four collectors retained their original **FAILED** result at `event-tree-reconciliation` (two missing polling handles per run). The separate kernel reconciler passes the identity/exit check; it explicitly records `producerStatus=FAILED_PRESERVED`. It does not rewrite the producer ledger or call the campaign accepted.

Synthetic child-first fixtures demonstrate an explicit parent wait; parent-first fixtures demonstrate children outliving their parent. They validate tracing, **not historical causation**. No delayed main/child tree was reproduced on the final collector; no stack, loader phase, inherited-pipe wait or security-scanning cause is established. Complete handle inventories/thread stacks were not captured. Earliest process events therefore do not yet distinguish startup from teardown or an internal wait in the historical failures.

## 14–15. Cleanup proof and remaining unknowns

All retained stress/helper handles were signaled and closed, with matching creation/exit identities. All scoped ETW rows have matched kernel exits. No STOP was synthesized from handle state. K9 WMI queues have zero residue, enqueued=persisted=removed, and complete 37 main START/STOP pairs. Output and primary/secondary failures are preserved. WMI and ETW observers exited through retained launcher/process handles; all native trace stop calls and ProcessTrace results succeeded. Final read-only checks: **360 recorded identities, zero matching live; zero scoped diagnostic/VirtualBox processes; zero remaining J6Kernel sessions**. A current absence check supplements, rather than replaces, recorded exit evidence.

Limits: 87 historical gaps remain UNKNOWN; some new helpers have kernel events but no retained handle; delayed/buffered ETW callbacks cannot guarantee acquisition before every short process exits. The normal collector is not yet integrated with the new independent ETW reconciliation and still fails its old handle-only criterion. Shared services outside the descendant tree, internal whoami entry/exit stages, and historical stacks remain unobserved. ETW observer launch receipts retain exit evidence, but do not persist a separate creation-time field for the observer itself; this should be added before using it as acceptance infrastructure. These limits prevent an unqualified CHILD_COVERAGE_VALIDATED or historical root-cause claim.

## 16–17. Historical failures remain failures

**PID 13340:** 14.0241948-second kernel lifetime; alive at the 13.611-second observed deadline; exited normally before the separate 15-second observer expired. Console child 19276 lacked a historical retained handle. Internal delay owner remains UNKNOWN.

**PID 9240:** alive at 13.603 seconds and at the independent 15-second observation; later STOP appeared. Original kernel exit timing/code remain unavailable in the old evidence. It is not equivalent to PID 13340's before-15-second exit.

**HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.** No historical timeout was reclassified as a flake or passed retroactively.

## 18–20. Invariants and preservation

13.6-second hard deadline, 15-second independent observer and 10-second heartbeat threshold are unchanged. No acceptance Dry Run #1/#2, protected hashing, VM/configuration inspection or VirtualBox launch occurred. Production JARVIS was not modified or started. **223 tracked application files and all 56 inherited diagnostic source files match prior hashes.** The previous 650-member evidence archive was verified before work and its SHA-256 is unchanged afterward. No commit was created.

## Validation, exact changes and rollback

New D: files: `kernel_trace.cpp`, `J6KernelTrace.exe`, `smoke.py/.ps1`, `stress.py/.ps1`, `reproduction.ps1`, `reconcile.py`, `test_reconcile.py`. Build objects, source/binary history and report/evidence utilities are diagnostic artifacts. No inherited runtime/monitor/probe/queue file changed. Final native source SHA-256: `d3390461457313c827d767e6f529b74327a25f94fddba6be75782a9b9cf678cd`; executable: `870b7e4c333b9e925c4853adb2067174cd834143d728378e93c97daa3d527945`. Source manifests and exact build commands are included. One compiler local-variable-shadow warning remains; compilation succeeds.

Tests: reconciliation **12/12**, cleanup/child matching **24/24**, revised probe **26/26**, existing monitor **69/69**, queue **222 assertions plus 10,000-event stress**, finalization **204 assertions**. Commands/results are in `kernel-regress-7058f7f0f6f64cf5898a25895fd46bc0/results.json`. Final native error-capture refinement was then validated by fresh K8/K9 runs. Prior smoke and earlier native-build runs remain transitional evidence. A report-reader schema-key error was corrected and preserved in `report-preparation-failure.json`; it did not affect execution.

Rollback: cease using the new isolated diagnostic candidate and continue to preserve its evidence. All prior 56 source files remain intact; production/runtime rollback is unnecessary. No VM, ACL, account, service or persistent trace configuration was changed. Do not delete historical evidence.

## 21–23. Archive, eligibility and disposition

The finalized nonsecret source/evidence archive and per-member SHA-256 manifest are copied to `C:/Users/jonny/OneDrive/Desktop/TEAGUE INDUSTRIES DATABASE/06 SOURCE RECORDS/STAGE6 KERNEL CHILD TRACE 20260920` only after live collection ends. See `archive-verification.json` for the actual verified member count and archive/manifest hashes; archive success is conditional on that receipt, not assumed here.

**Protected-baseline eligibility: NOT ELIGIBLE / NOT AUTHORIZED.**

**Final status: INCONCLUSIVE.** Next review should decide whether the explicitly recorded kernel start/exit identity may close a short-lived helper's cleanup requirement when handle acquisition is impossible, and define the minimal integration into the authoritative collector. Preserve the old failed runs. Do not rerun acceptance dry runs or protected hashing from this diagnostic result.
