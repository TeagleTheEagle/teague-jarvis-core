# Stage 6 fresh dual-evidence cleanup validation — 2026-09-20

CLEANUP_CHECKER_VALIDATED, conditional on the accompanying completed HASH_VERIFIED archive receipt. This is diagnostic cleanup validation only. Stage 6 and full monitor acceptance are not declared complete. Protected baseline hashing remains unauthorized.

## Mandatory disposition

| Item | Result / evidence |
|---|---|
| 1. Historical 97-run | KERNEL_ONLY_HISTORICAL_EVIDENCE: 97 identities, 94 retained, 3 explained post-exit; original archive remains unchanged. `historical-classification.json`, `historical-archive-after.json`. |
| 2. Why it cannot satisfy C5 | Independent application START/STOP NOT CAPTURED. Historical evidence was never fabricated or regenerated. |
| 3. Fresh identity total | Initial fresh model run: 97. Subsequent corrected-checker live run: 97. Identity-level reconciliation, not count-only acceptance. |
| 4. Application START | 97 per run; 194 tracked across both. Independent CIM callbacks, enqueue receipts and durable event records. |
| 5. Application STOP | 97 per run; 194 tracked across both. Never synthesized from kernel/handle state. |
| 6. Kernel CREATE | 97 tracked per run. |
| 7. Kernel EXIT | 97 tracked per run. |
| 8. Retained handles | Initial run 91; corrected-checker run 94. Union of independently retained ETW/Toolhelp/explicit launcher handles, deduplicated by creation identity. |
| 9. Qualified post-exit | Initial run 6; corrected-checker run 3. OpenProcess began strictly after kernel exit; WinError 87, full application/kernel lifecycle and unique identity required. |
| 10. Unexplained | 0 in each new tracked tree. Does not reclassify historical gaps. |
| 11. PID safeguards | PID + kernel creation FILETIME + process sequence + parent sequence + image/parent agreement; retained creation and exit must match; multiple lifetimes/PID are rejected rather than guessed. |
| 12. Children/helpers | Each fresh tree includes collector, 24 short native probes, 12 synthetic parents, 12 child helpers and 48 console helpers = 97. Parent-first/child-first/overlapping exits exercised. Missing children reject. |
| 13. Checker files | New `cleanup_checker.py`, `test_dual_cleanup.py`; new `app_monitor.ps1`, `dual_launch.ps1`, `volume_map.py`; `kernel_trace.cpp` and rebuilt `J6KernelTrace.exe` add pre-OpenProcess timing. All changes confined to independent diagnostic candidate. `source-changes.json` records before/after hashes. |
| 14. Focused tests | 40/40 PASS before fresh validation and again in final regressions. Covers all 15 requested cases plus 25 failure/integrity cases. Raw logs retained. |
| 15. Corrected-checker fresh stress | PASS: `dual-07290815162f45d69e0ce858641f5d9a/cleanup-checker-result.json`; producer DIAGNOSTIC_COMPLETE, checker exit 0, no primary failure. |
| 16. Regressions | 171 unittest cases PASS in 5 groups: dual 40, kernel 12, hardening 24, probe 26, monitor 69. Queue 222 assertions PASS including 10,000-event stress. Finalization 205 assertions PASS including 1,000-process/2,000-event concurrent case. Seven command groups exit 0. `regression-summary.json`. |
| 17. Orphan helpers | 0 unexplained in both reconciled trees; all handles closed and independent final snapshot finds no matching identity. |
| 18. Live diagnostic identities | 0 matching across 203 recorded identities, including launchers and observers. Current PID reuse recorded as unrelated, not killed. Scoped live processes 0. `host-final.json`. |
| 19. Kernel trace cleanup | Temporary native session stopped/consumer joined; faults/loss zero; read-only logman enumeration succeeded and found 0 J6Kernel sessions. Both independent observers exited 0. |
| 20. Historical 87 gaps | UNKNOWN; no retroactive proof. |
| 21. PID 13340 | Historical cause UNCONFIRMED; previous kernel lifetime evidence preserved. |
| 22. PID 9240 | Historical cause UNCONFIRMED; failed dry run remains failed. |
| 23. Protected VM/config | NOT ACCESSED by this pass. No VM/config enumeration, hash, launch or modification. No protected integrity claim inferred from this non-access scope. |
| 24. Production | UNCHANGED; 223 previously recorded application files match. No Core/provider/production launch. Prior 61 diagnostic sources match unchanged. |
| 25. Archive | `archive-verification.json` must show HASH_VERIFIED after per-member and destination verification. Original failed checker result, canceled-UAC run and metadata exceptions included. |
| 26. Protected baseline eligibility | NOT AUTHORIZED. Full monitor/dry-run acceptance remains outside this pass. No Dry Run #1/#2 or protected hashes performed. |
| 27. Final status | CLEANUP_CHECKER_VALIDATED only for the fresh sacrificial dual-evidence cleanup rule. |

## Independent evidence and precise boundary

Application notifications originate from separately registered Win32_ProcessStartTrace/StopTrace CIM subscriptions, drained through ExactEventQueue and persisted before removal. EventTap independently records callback/enqueue receipts. Native ETW uses Microsoft-Windows-Kernel-Process; it does not generate application events. Retained-handle creation/exit data is another independent path. Both Windows event providers ultimately observe the same OS; this is not a claim of independence from Windows itself.

The tracked scope is the actual stress collector and all kernel descendants, cross-checked against the independently derived application parent tree and explicit producer/child records. Each run also records two kernel infrastructure identities outside that tree (application observer + console host). Their exits/observer identities are preserved and included in the final current identity check. Application out-of-scope records: 1 in the first run, 14 in the second. These are retained and explicitly excluded from the 97-process equation; they are not missing tracked lifecycle events. Command lines/environment/secrets were not recorded by the broad application collector.

First-run queue: 195 enqueued/selected/persisted/removed, residue 0, max depth 113. Final-run queue: 208 each, residue 0, max depth 119. Maximum heartbeat intervals: initial 1.0551644s; final 1.0685684s, both below unchanged 10s. Natural EventIdentifier collisions: 0 in these two captures; collision behavior is proved separately by focused mutation tests and the 10,000-event stress (9,993 external collisions, zero internal collisions/loss/duplicate/sibling deletion).

## Preserved transitional failures and minimum checker correction

The first UAC launch was canceled before observers/stress began. `dual-b1ecb7ee68844a67893aa06a019427c0` remains preserved. Owner explicitly approved reissuing the diagnostic prompts.

The first checker implementation rejected two identity-bound QueryFullProcessImageNameW errors (WinError 31 and 5). Those handles were actually retained, signaled, creation/exit-matched and closed. The initial checker incorrectly treated image metadata loss as missing exit proof. Its source is saved as `cleanup_checker.initial.py`; the original FAIL result remains in the first run. A separate `cleanup-checker-reviewed.json` records the corrected replay; no failed file was overwritten.

The narrow correction accepts a missing image query only when the exact per-row `(PID, creation time)` error matches the preserved error journal, its stage is image-query, its timing lies between retained acquisition and observed signal, and the full kernel image/lifetime plus independent app image/parent agree. It still requires retained creation/exit/code/parent/signal/closed proof. It never converts image-query failure into post-exit acquisition proof. Generic handle failures, access-denied no-handle cases, conflicting known images and unknown images without the bound error all fail. The fresh final run includes one such preserved image-query WinError 5; its OS cause is unconfirmed. No Windows security setting was altered.

The native instrumentation records the beginning of OpenProcess, not only its return. No-handle acceptance requires `kernel stop QPC < acquisition begin QPC <= acquisition return QPC`, explained error 87, no PID ambiguity and complete independently persisted application START/STOP. A failed open before/equal to exit is rejected.

## Integrity, finalization and limits

Final live run source manifest matches all final candidate files with no drift. First-run launcher change is documented: the later driver adds read-only volume-map capture before observers and invokes the tested checker only after both observers finalize. Diagnostic source hash inventory and application preservation are independent records.

Live artifacts remain on D:. Final archival to the OneDrive database occurs only after observers/processes and ETW session are closed. There is no live heartbeat dependency on archive synchronization. Python runtime, PowerShell executable and Windows modules still reside on C:; no claim is made that all OS activity is on D:.

The monitor, EventIdentifier queue implementation, existing probe policy and finalization gate were not changed. No timeout increased: 13.6s primary deadline, 15s independent policy period, 10s heartbeat threshold remain as before. This campaign validates cleanup evidence, not hard-deadline reliability under full hashing/dry-run load, and does not explain the historical timeout/storage causes. Neither successful cleanup nor these new results retroactively pass an earlier failed run.

Rollback: stop using this new diagnostic candidate and retain it with its evidence; the previous immutable D: source remains available unchanged. No production rollback or protected VM operation is required. Do not restore/delete previous evidence. No acceptance commit created.

HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Next owner review: approve any resumption of the full monitor sacrificial acceptance sequence separately. Protected baseline hashing remains prohibited until the required preceding gates genuinely pass and it is explicitly authorized.
