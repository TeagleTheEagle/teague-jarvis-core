# Stage 6 targeted diagnostic hardening — 2026-09-20

Disposition: **DIAGNOSTIC_INFRASTRUCTURE_VALIDATED**, limited to this bounded sacrificial diagnostic. Stage 6, the large synthetic protected-collector campaign and real protected-baseline capture are NOT accepted by this report. Protected-baseline hashing remains unauthorized.

Final candidate: `D:\JARVIS-STAGE6-LIVE\2ef4a4641a234b7dbfdce8db88cb1e39\code`.

Monitored run: `D:\JARVIS-STAGE6-LIVE\cd45670bb1894d5b99a1b469e4771535\code\hardening-cf2a523b5ef74f7380411829d2fd1477`.

The final candidate changes only the offline checker and its tests relative to the monitored candidate. All monitor, sampler, probe and launcher executable/script bytes match. The final checker independently passes the preserved monitored run. This distinction is recorded in `final-source-reconciliation.json`; no additional live run is implied.

## 1. Lineage defect

The previous checker expanded application-event ancestry using parent PID across the entire history. In the preserved ladder run, unrelated processes preceded the diagnostic incarnation of their reported parent PID by approximately 25.740 seconds. PID equality incorrectly pulled them into the diagnostic tree. Original records and the failed checker outcome remain preserved.

Review also demonstrated a delayed-event ambiguity: a same-name PID can have multiple incarnations before notification time. The intermediate checker assigned a delayed STOP to the newer incarnation by treating its creation time as an upper bound for the earlier event. `delayed-reuse-before-after.json` preserves that counterexample. The final checker retains both candidates and returns UNKNOWN.

## 2. Exact checker correction

`lineage.py` binds application evidence using kernel PID/creation identities, native notification time, receipt ordering, image name and parent evidence. Parent validation requires the exact kernel parent sequence and child creation within its parent's observed lifetime. Multiple plausible candidates, duplicate creation identities, impossible ordering or missing required evidence fail closed.

`cleanup_checker.py` uses those associations instead of PID-only expansion; exact image, retained-handle, independent kernel, application START/STOP, queue and durable-finalization checks remain required. `evidence_support.py` keys retained handles by PID plus creation time and no longer skips every later incarnation just because its PID was previously seen. Kernel reconciliation remains authoritative when polling misses a short-lived child.

Conservative limitation: a delayed same-image event spanning PID reuse can remain UNKNOWN even if the process eventually exited. That is an evidence failure, not permission to reassign it. Truncated image names are also rejected; there is no prefix-matching exception.

## 3. PID-reuse tests and regressions

Final focused command: bundled Python `-B run_tests.py`, working directory the final candidate above.

Final result: **117 tests PASS, 0 failures, 0 errors, 0 skips**, 31.110 seconds. Evidence: `hardening-tests-1b3646f0cee44f6d90d7ba1966160a5a/result.json` and `tests.txt` under the final candidate.

Coverage includes the ten requested PID/lineage cases, wrong parent sequence, missing child, wrong image, impossible receipt order, unchanged input evidence, delayed START/STOP across same-image reuse, original failure remaining failed, original valid run remaining valid, and rechecking the actual prior PID-reuse evidence. The simple retained-handle key unit case is supplemented by actual retained-handle/kernel comparisons in the combined run; it is not presented as standalone process proof.

Existing monitor, journal, path containment, process, retained-handle, finalization, queue, failure and probe-policy tests are included. Queue campaign: **222 assertions PASS**, including **10,000 events**, 9,993 external EventIdentifier collisions, zero internal collisions, losses, duplicates or sibling deletions. The queue/timing source used for that campaign is byte-identical to the final candidate. Final wrapper check: **5 checks PASS**. All 61 Python files parse; affected PowerShell files parse. The actual observer successfully compiled and ran the C# instrumentation.

Earlier 112- and 115-test runs and their generated outputs are retained separately; these are not added to the 117 final test count.

## 4. Exact sampler blocking call

Preserved process PID 10612 ran `diag_resources.ps1` in a separate PowerShell process. Its synchronous `Get-Counter -MaxSamples 1` requested total processor usage, physical-disk idle/queue/read/write latency and bytes, available memory/pages and context switches. One call took **28.4084415 seconds**. The loop checked its stop file only between calls, then slept 500 ms; its 180-second outer bound did not interrupt a blocked call. The parent waited 15 seconds for cleanup and failed while the sampler was still executing. It later exited.

This sampler was already outside the observer's heartbeat thread, but its uncancellable query and required cleanup could outlive diagnostic completion. The older monitor also inspected process properties synchronously. This establishes a sampler cleanup defect; it does not establish the cause of either original large-run failure.

## 5. Sampler redesign

`bounded_sampler.py` creates one fixed-purpose worker suspended, retains its identity, assigns it to an unnamed Windows Job with kill-on-close, then resumes it. No arbitrary command/query interface is exposed. No inherited handles are enabled for this worker. Worker results use a bounded 4 KiB pagefile-backed named mapping with a unique run identifier; no C: evidence file is used.

`sampler_worker.py` collects only `GetSystemTimes` and `GlobalMemoryStatusEx` in normal mode. Disk counters are explicitly NOT_COLLECTED. Optional sampling runs on its own supervisor thread/process, separate from the monitor's event/heartbeat loop. Routine process-property sampling was removed from that loop; necessary process identity checks remain individually timed.

## 6. Timeout and cancellation behavior

Each secondary query has a two-second observation budget and cancellation flag. Slow/hung/crashed/failed queries produce MISSING telemetry. Cleanup terminates only the owned Job or the exact still-suspended process if Job assignment failed. It waits within the existing two-second cleanup budget for both process signaling and an empty Job; these are distinct predicates. It closes retained handles and records exit identity/code. Missing required cleanup proof returns CLEANUP_FAILED and cannot be treated as successful telemetry or campaign cleanup.

An intermediate run exposed an immediate Job-accounting check performed after an already-signaled root wait. The fix uses the existing budget to observe both predicates; no timeout was increased. Exact internal Windows Job teardown timing is not claimed.

The 13.6-second probe deadline, 15-second independent observer period and 10-second heartbeat threshold are unchanged. Secondary query budgets are separate from those safety limits. Windows API scheduling is not a hard real-time guarantee; an unreturning OS operation must still lead to missing/unproven evidence rather than a fabricated PASS.

## 7. Monitor timing

`LoopTiming.cs`, `EventTap.cs` and `timed_monitor.ps1` record monotonic start/end/duration, loop sequence and thread identity. Final evidence contains **3,250 completed spans across 43 stage names**, zero overflow, consecutive loop identities and verified duration arithmetic.

Coverage: wake; event-source/subscription access; callback/enqueue; lock acquisition; selection/metadata/serialization; evidence path construction and append; exact queue removal; heartbeat creation, in-memory history append and health-file overwrite; control checks; process inspection; wait; next wake; subscription closure, final drain, reconciliation and durable flush. `timing-coverage-final.json` provides counts and maxima per stage.

There is no separate event-file existence check on this path: append opens the destination directly. The heartbeat history append is in memory; actual health publication is an overwrite, explicitly named as such. Those facts are not mislabeled as filesystem append measurements. High-volume trace collection stays in bounded memory and is written to D: after observation ends, keeping archive/OneDrive activity outside the live loop. Fatal process loss can prevent in-memory timing finalization; such a run cannot pass.

## 8. Probe/process timing

`probe_timing.py` additionally records handle-retention time. The preserved run includes launch request, CreateProcess return, retained-handle wait/exit observations, exact creation/exit FILETIME and independent kernel/app-event/persistence records. `process-timeline-final.json` joins those sources by identity and records child/helper identities.

Of 26 probes, eight native controls provide entry, initialization, work and cleanup/exit markers through the existing bounded mapping protocol. Eighteen whoami-based probes are uninstrumented internally; those timestamps are explicitly UNKNOWN. An observed signaled handle is an observation bound, not an invented exact kernel signaling timestamp.

Native control bytes are unchanged; a copy named `J6Native.exe` avoids the observed long-name STOP metadata truncation. Exact-name checking remains intact, with a regression proving truncated metadata stays UNKNOWN. This diagnostic helper adjustment does not change JARVIS or its acceptance probe policy.

## 9. Sampler failure injection

All seven cases passed their intended diagnostic assertions during the independently observed combined run:

| Case | Telemetry | Total seconds | Cleanup seconds | Exit proof |
|---|---|---:|---:|---|
| Normal | AVAILABLE | 0.098653 | 0.010395 | Job empty, handle signaled/closed |
| Slow | MISSING / query timeout | 2.026436 | 0.010354 | Complete |
| Hung | MISSING / query timeout | 2.015095 | 0.010254 | Complete |
| Exception | MISSING / exit 1 | 0.096589 | 0.010630 | Complete |
| Cancellation | MISSING / canceled | 0.144280 | 0.010674 | Complete |
| Cleanup observation timeout | MISSING / injected timeout | 4.007983 | 2.002928 | Independent post-injection check complete |
| Crash | MISSING / exit 7 | 0.092434 | 0.010554 | Complete |

The cleanup-timeout case deliberately suppresses acceptance of an empty-Job observation for the existing cleanup budget while retaining raw kernel results. After withdrawing that diagnostic fault, a zero-wait proof checks the actual Job/process state. It is explicitly an injected observation failure, not a claim that Windows cleanup genuinely stalled. A separate real-worker test makes required Job-query evidence unavailable and verifies CLEANUP_FAILED, even when the root has exited. No missing proof becomes success.

## 10. Combined sacrificial result

Final checker: **PASS**. Producer: DIAGNOSTIC_COMPLETE, no primary or secondary failure. **67 identities / 67 STARTs / 67 STOPs**, including helpers; 64 handle-confirmed exits plus three qualified kernel-confirmed post-exit acquisition cases. Zero unexplained identities, lineage ambiguities or orphan evidence. 150 total observed queue events persisted and removed, zero residue. No ETW event/buffer loss. Maximum queue depth 22.

Maximum heartbeat interval **1.0416894 seconds**; maximum probe lifetime **0.0358531 seconds**; zero deadline violations. No EventIdentifier collision in this final run; zero internal queue-ID collisions. Stress collision behavior is separately proven by the 10,000-event regression. Durable application finalization, unsubscription and both observer exits passed.

This is a short combined diagnostic with fault injection. No full large-data campaign, protected collector run or acceptance dry run was performed.

## 11. Cleanup

`final-live-check.json` compares **143 recorded identities** from the diagnostic attempts and direct sampler checks against current process creation times. Zero matches remain. The independent scoped process scan found zero diagnostic/VirtualBox processes; the host ETW listing contained zero diagnostic trace sessions. No unrelated process was terminated. Sampler termination affected only its owned Job/process handles.

## 12. Residual uncertainty and preserved failures

All attempted versions are retained. New unsuccessful attempts:

1. v1: observer startup failed because PowerShell alias `measure` selected `Measure-Object` instead of the diagnostic function. Corrected with unique `Invoke-J6TimedStage`; normal and exception closure tested.
2. v2: premature empty-Job check caused cleanup rejection; fixed as described above without extending the budget.
3. v3: six native STOP names were truncated to `J6ProbeNative.`; strict checker failed. Evidence unchanged; short-name helper used in a fresh run.
4. v4: preflight rejected changes to two generated regression JSON files mistakenly included in the source manifest. No observers started. Generated output/source distinction corrected; hashes preserved.
5. v5 offline review: delayed same-image PID-reuse ambiguity preserved and corrected conservatively in v6. Final monitor/sampler bytes did not change, and final checker passes the same raw run.

Earlier failed evidence is not relabeled as passing. Rechecking an old record uses a separate result. Timing overhead and altered secondary telemetry can change performance; this bounded run establishes infrastructure behavior, not the large-load worst case. Read-only host scans are point-in-time evidence; they do not replace retained handles or kernel/application lifecycle proof. No claim is made about the Windows filesystem, driver, antivirus or scheduler cause of previous stalls.

## 13. Original probe-delay status

**UNCONFIRMED.** The original long probe was not reproduced or explained by this pass. Successful short probes do not erase it.

## 14. Original heartbeat-delay status

**UNCONFIRMED.** Previously demonstrated C: synchronous stalls remain evidence, but this pass does not establish the exact blocking operation in the original large synthetic failure or a common cause with the probe delay.

HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

## 15. Protected VM access

**NOT ACCESSED.** No protected VM/configuration file was opened, hashed, modified or copied. No VirtualBox command was launched. Process-name observation is not VM-file inspection. No protected-baseline capture was attempted.

## 16. Production change and rollback

**Production JARVIS unchanged by this work.** Changes are confined to new diagnostic candidate copies, test output and reports. No JARVIS runtime, provider, security policy, production data, VM permission or baseline file was changed.

Original 84-file diagnostic candidate remains hash-identical. Final source manifest verifies 96 candidate files. Exact paths, pre/post hashes, added files and unified diffs are in `candidate*.json`, `source-integrity-final.json`, `final-source-reconciliation.json` and `*.diff`. Changed original diagnostic files: `cleanup_checker.py`, `evidence_support.py`, `LoopTiming.cs`, `EventTap.cs`, `probe_timing.py`. Added paths include lineage, bounded sampler/worker, timed observer, fixed launcher, collector, tests and the byte-identical short-named native helper.

Rollback: do not select the new diagnostic candidate for future runs; retain it and all evidence, and refer to the preserved original candidate. The old defects remain known, so rollback is not permission to resume protected hashing. No production rollback or data migration is needed. No commit was created.

## 17. Archive verification

The previous 206-member archive is independently hash-verified. This report, candidate versions, all new failed/successful raw runs, focused-test results, collision results, timing/lifecycle joins, hashes and cleanup receipts are archived under:

`C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 TARGETED DIAGNOSTIC HARDENING 20260920`.

`archive-verification.json` records the exact new member count, ZIP hash and manifest hash. Every member and source is checked after archive creation. Credentials, environment files, production data and large synthetic/protected datasets are excluded. Archival happens after live monitoring ends. A failed archive check prevents the final disposition from being issued.

## 18. Final disposition and next boundary

**DIAGNOSTIC_INFRASTRUCTURE_VALIDATED** for the requested bounded experiment only, conditional on the accompanying successful final archive receipt.

Next owner-review item: authorize any further controlled synthetic large-data diagnosis using this candidate, with original failures retained and unchanged limits. Do not run the full synthetic campaign, acceptance dry runs, or real protected-baseline capture under this report alone.
