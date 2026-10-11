# Stage 6 process STOP-event loss diagnosis — 2026-09-20

**FINAL STATUS: STRONG_CAUSAL_EVIDENCE**

Reproduced mechanism: **QUEUE_DRAIN_LOSS — duplicate PowerShell EventIdentifier values cause removal of a different queued event before it can be drained.** This mechanism is identified in two new instrumented campaigns and confirmed with a direct synthetic removal test. The original three losses lack queue identifiers and cannot be conclusively assigned this cause retrospectively. They are compatible with the reproduced mechanism, not individually proven.

**PROTECTED BASELINE ELIGIBILITY: NOT JUSTIFIED.** No correction, sacrificial acceptance dry run or protected hashing was performed.

1. **Three historical identities** (creation FILETIME, retained-handle record):

| PID | Creation FILETIME | Creation UTC | Recorded successful wait to collection freeze |
|---:|---|---|---:|
| 13248 | 134341814135468126 | 2026-09-18T05:03:33.546812+00:00 | 383.480446 s |
| 22544 | 134341814525504930 | 2026-09-18T05:04:12.550493+00:00 | 344.476556 s |
| 21896 | 134341815115021482 | 2026-09-18T05:05:11.502148+00:00 | 285.523763 s |

Exact launch/wait-completion QPC and UTC estimates, start-notification times, nearby queue trace, and freeze timing are in `historical-missing-identities.json` / `historical-shutdown-timeline.json`. Numeric original handle values and actual kernel exit FILETIMEs were not recorded; do not invent them.

2. **Did they exit?** Each historical Popen.wait completed and exit code 0 was recorded while retaining its process handle and reading creation identity. This is affirmative contemporaneous exit evidence, not an inference from present-day absence. It supports successful exit; it does not independently identify every possible external termination cause. In new runs we additionally saved actual GetProcessTimes exit FILETIME and verified signaled retained handles through finalization.

3. **Last stage of each original missing STOP:** UNKNOWN; no historical callback/enqueue trace exists. None reached the historical persisted event file. For every newly reproduced missing event, the last recorded stage is **A-enqueue**, followed by sibling removal under the same event ID. Do not replace original missing records with new evidence.

4. **Windows notification result:** new native TIME_CREATED notifications arrived at both MI/CIM and independent System.Management/COM subscriptions for every probe. No Windows notification loss is demonstrated in these new runs. Native emissions before either callback are not directly counted; E9 documented behavior alone cannot prove loss or completeness.

5. **Callback result:** both new campaigns recorded every START and STOP at A's callback hook. The hook attaches after the original handler; its timestamp is a tap observation, not the first internal native callback instruction.

6. **Enqueue result:** every START and STOP reached PowerShell ReceivedEvents. There were 16 cross-source numeric EventIdentifier collisions across the two runs. These are **event-ID collisions**, not PID reuse: every probe retained a distinct process identity.

7. **Drain result:** 16 real events (15 STOP, 1 START) did not reach drain. Every missing event had already entered the queue before its same-ID sibling's Remove-Event call. `repeat*/collision-analysis.json` contains exact per-event timing and IDs.

8. **Serialization result:** all drained events were serialized; no additional loss between drain and serialization.

9. **Persistence result:** every serialized event had a completed append and matching file record. No additional write loss. Independent handles are never converted into synthetic STOP records.

| Run / phase | Expected exits / handle-confirmed | A callback STOP | A enqueued STOP | A drained STOP | A serialized STOP | A append-complete STOP | A file STOP | A reconciled STOP | B COM STOP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| smoke / idle | 4/4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| repeat1 / idle | 20/20 | 20 | 20 | 20 | 20 | 20 | 20 | 20 | 20 |
| repeat1 / disk | 52/52 | 52 | 52 | 51 | 51 | 51 | 51 | 51 | 52 |
| repeat1 / sustained | 21/21 | 21 | 21 | 20 | 20 | 20 | 20 | 20 | 21 |
| repeat1 / cpu | 20/20 | 20 | 20 | 16 | 16 | 16 | 16 | 16 | 20 |
| repeat1 / Dhash | 39/39 | 39 | 39 | 35 | 35 | 35 | 35 | 35 | 39 |
| repeat2 / idle | 20/20 | 20 | 20 | 18 | 18 | 18 | 18 | 18 | 20 |
| repeat2 / disk | 48/48 | 48 | 48 | 47 | 47 | 47 | 47 | 47 | 48 |
| repeat2 / sustained | 23/23 | 23 | 23 | 23 | 23 | 23 | 23 | 23 | 23 |
| repeat2 / cpu | 20/20 | 20 | 20 | 19 | 19 | 19 | 19 | 19 | 20 |
| repeat2 / Dhash | 39/39 | 39 | 39 | 38 | 38 | 38 | 38 | 38 | 39 |

Two full repetitions: **302 probes, 302 handle-confirmed exits, 302 START callbacks/enqueues, 301 STARTs persisted; 302 STOP callbacks/enqueues, 287 STOPs persisted.** Smoke: four probes, all four STARTs/STOPS captured at all stages. Campaigns use approximately one-second nominal probe spacing versus historical five-second spacing; synchronous evidence/storage activity reduced the achieved rate. Every phase records actual duration, process identity and input path. Instrumentation/parallel observer perturb timing; these are diagnostic results, not acceptance passes.

Dual observer: A persisted STOP and B COM STOP both present for 287/302; only B for 15; only A zero; neither zero. Kernel handles independently confirmed all 302 exits. B is a separate subscriber/transport to the **same WMI provider**, not an independent ETW provider. Independent kernel wait/GetProcessTimes is a different lifecycle mechanism but does not claim to capture notifications. No additional ETW package or broad system trace was installed/launched because the existing observations already localized loss downstream of receipt.

10. **Finalization race:** none of the reproduced lost events was pending at teardown, and every one was already queued before sibling removal. Events can arrive after collector-finished within the existing grace; those observed events were captured. No observed callback/enqueue arrived after collection.freeze. The original final-drain → freeze → unsubscribe interval can theoretically discard a late queued event (the original finally clears it), but that mechanism did not explain the reproduced losses. Original missing exits were 285–383 seconds before freeze; an ordinary two-second shutdown tail is insufficient to explain those records without unsupported extreme delay. No grace added.

11. **Queue integrity:** both runs had zero hook errors/trace overflows, no observed same-source ID duplicates and no pending/discarded events at teardown. ReceivedEvents is the existing PowerShell collection; no capacity/overwrite setting changed. Native dropped-event counters are not exposed. Installed PowerShell reports 7.6.5; System.Management.Automation assembly version 7.6.0.500, SHA-256 `2d8af026e589c5603629bfc3e7c57265b4167b12eca3ae549c6a6c3ca7e4967b`. Read-only IL inspection shows GetNextEventId incrementing `_nextEventId` without an interlocked operation in that method. Real concurrent START/STOP notifications received the same ID. `queue-mechanism-proof.json` independently confirms that removing one numeric ID removes both synthetic queued events. No installed assembly was changed. Queue occupancy/sequence/thread observations and teardown state are preserved in tap/pipeline/loop traces.

12. **Latency distributions**, both full campaigns combined, seconds. p95 uses nearest rank with at least 20 samples; p99 requires at least 100. Metrics involving missing drain records exclude those records and show their sample counts. Callback-to-enqueue is signed because handler ordering can put the callback tap after enqueue. FILETIME-to-wall measurements are separate from QPC pipeline measurements; wall adjustments could affect those cross-clock estimates.

| Kind | Metric | Samples | Median s | p95 s | p99 s | Max s |
|---|---|---:|---:|---:|---:|---:|
| start | kernel_lifecycle_to_notification | 302 | 1.435698 | 1.985904 | 2.078569 | 2.482294 |
| start | notification_to_callback_tap_wall | 302 | 0.000543 | 0.001097 | 0.004835 | 0.007284 |
| start | callback_tap_to_enqueue_signed | 302 | 0.000021 | 0.000099 | 0.000218 | 0.000417 |
| start | queue_residence | 301 | 0.000462 | 1.884787 | 4.586607 | 7.452644 |
| start | drain_to_serialized | 301 | 0.000264 | 0.000874 | 0.002669 | 0.007474 |
| start | serialization | 301 | 0.000151 | 0.000311 | 0.001335 | 0.007301 |
| start | append | 301 | 0.000415 | 0.101562 | 2.833517 | 5.551340 |
| start | persisted_to_offline_reconciliation | 301 | 117.204422 | 239.903639 | 252.024791 | 256.029605 |
| stop | kernel_lifecycle_to_notification | 302 | 1.843239 | 2.876101 | 2.995604 | 3.024717 |
| stop | notification_to_callback_tap_wall | 302 | 0.000570 | 0.001091 | 0.003722 | 0.008738 |
| stop | callback_tap_to_enqueue_signed | 302 | 0.000022 | 0.000140 | 0.000419 | 18.965166 |
| stop | queue_residence | 287 | 0.002937 | 3.068528 | 5.553019 | 7.450171 |
| stop | drain_to_serialized | 287 | 0.000230 | 0.000443 | 0.001235 | 0.001428 |
| stop | serialization | 287 | 0.000133 | 0.000250 | 0.000650 | 0.001335 |
| stop | append | 287 | 0.000315 | 0.000501 | 5.614232 | 8.768477 |
| stop | persisted_to_offline_reconciliation | 287 | 119.686631 | 237.901988 | 253.032761 | 255.043324 |

Offline reconciliation latency includes the intentional delay before analysis; it is not a provider-performance claim. Full per-phase distributions are in each analysis.json. The first run contained a STOP callback-to-enqueue interval of 18.965166 seconds, eventually persisted. That is a separate scheduling/queue-processing delay whose internal cause was not established. Maximum observed heartbeat ages: repeat1 8.7602586 s; repeat2 6.566074 s; ten-second threshold unchanged. No new stale-heartbeat failure occurred.

13. **C: read correlation:** original three losses were all under C: reads. New losses occurred under idle, C: reads, C: hashing, CPU and D: hashing; this disproves a claim that C: pressure is necessary in the observed mechanism. Resource counters (disk active/idle, queue depth, read/write latency, throughput, CPU), callback/queue/write timing and nearest samples for each loss are saved in analysis.json / loss-resource-correlation.json. Storage pressure coincided with multi-second queue/append delays, but no causal disk explanation is asserted. The immediate loss mechanism is ID-based sibling removal.

14. **Strongest supported category:** QUEUE_DRAIN_LOSS for the reproduced cases. All 16 missing events map one-for-one to 16 collisions; 11 in repeat1, five in repeat2. Historical individual attribution remains INCONCLUSIVE. Overall final disposition is STRONG_CAUSAL_EVIDENCE rather than a claim to have reconstructed every historical loss.

15. **Proposed minimum correction:** remove only the exact successfully processed PSEventArgs object under ReceivedEvents.SyncRoot; verify owned subscription and reference identity, fail closed if absent/mismatched. Do not hold the lock across serialization or disk I/O. Do not remove by numeric EventIdentifier alone, clear the queue/subscription or modify PowerShell/runtime DLLs. No correction is implemented. `CORRECTION-PROPOSAL.md` identifies validation-only candidate monitor/helper/tests and the scope boundary.

16. **Residual uncertainty:** the exact old losses cannot be traced past the historical gap. Instrumentation affects timing. Native buffering/drop counters and independent ETW emission tracing are unavailable in this campaign. PowerShell event collection can still suffer scheduling delays; fixing removal would not prove timing acceptance. No host power-loss or storage-hardware durability guarantee was tested. Historical 13.7 s / 14.084 s causes remain UNCONFIRMED; only synchronous Flush(true) causing experimentally measured >10 s stalls is supported. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

17. **Exact revalidation plan:** after reviewed correction, run prior focused tests plus exact-object removal/collision/concurrent-arrival/write-failure/unrelated-event tests; repeat all five workloads with complete real START/STOP evidence, retained identities and unchanged ten-second threshold; repeat all failure injections; require durable finalization and hash-verified archive; independently run Dry Run #1 then #2 only after load gates pass; verify cleanup and unchanged protected/production boundaries. Full plan/rollback in CORRECTION-PROPOSAL.md. No wait/grace increase or acceptance substitution.

18. **Protected baseline eligibility: NOT JUSTIFIED.** No protected VM or normal VirtualBox configuration opened/hashed; no VirtualBox launched; no production JARVIS changed; no settings/ACL/execution-policy changes. Diagnostic monitors used the authorized read-only elevated subscriptions; probes/workloads ran non-elevated on fixed sacrificial inputs. All run records remain explicitly unaccepted. No correction/acceptance commit.

19. **Evidence paths:** this directory; raw `smoke/`, `repeat1/`, `repeat2/`; `historical-loads2/` (hash-verified copy); `original-inventory.json`, `historical-missing-identities.json`, source-snapshot, EventTap.cs, instrumented monitor.ps1, collect.py, launch.ps1, analyze.py, collisions.py, synthetic proof script/result, full latency/correlation output, source hashes and preservation-final.json. The original 352 files and seven source snapshots are unchanged; all diagnostic monitor script hashes match across the three runs. No original failed evidence is overwritten.

20. **Archive:** `C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 STOP EVENT DIAGNOSIS 20260920`. Archive receipt records exact ZIP member count, full member SHA-256 verification and copied-file hash checks. This is a diagnosis/failure-evidence archive, not MONITOR_VALIDATED acceptance. Rollback is to stop using diagnostic copies while retaining all evidence; no production rollback necessary.

Documentation distinction:
- Observed source: original monitor.ps1 lines 13–29 (Drain/append/ID removal), 35–36 (CIM subscriptions), 58–67 (final drain/freeze/unsubscribe); original campaign.py lines 25–29 (retained process handles); original finalize.py line 38 (exact event count rejection).
- Microsoft documents that local CIM subscriptions use COM and queued events without Action: https://learn.microsoft.com/en-us/powershell/module/cimcmdlets/register-cimindicationevent?view=powershell-7.5
- ProcessStopTrace indicates termination and TIME_CREATED is event generation time, not independently retrieved process-exit time: https://learn.microsoft.com/en-us/previous-versions/windows/desktop/krnlprov/win32-processstoptrace
- Process handles signal at exit and remain valid while retained: https://learn.microsoft.com/en-us/windows/win32/procthread/terminating-a-process
- WMI documents dropped/overflow events, including permanent-consumer context; absence of such a record is not proof against temporary-subscriber loss: https://learn.microsoft.com/en-us/windows/win32/wmisdk/--eventdroppedevent and https://learn.microsoft.com/en-us/windows/win32/wmisdk/--eventqueueoverflowevent
- PowerShell reference source explains queue addition/removal and counter allocation: https://raw.githubusercontent.com/PowerShell/PowerShell/v7.5.3/src/System.Management.Automation/engine/EventManager.cs . Installed-version behavior was tested/inspected independently rather than assuming this older source exactly matches it.

Cleanup addendum: read-only post-run inspection checked 317 PID/creation records (306 probes including smoke, three monitors, eight load workers). It initially found one matching process object (repeat2 worker PID 12716) and one access-denied PID (old probe PID 12392). All workers/probes had already returned successful waits in their run evidence. A follow-up found 12716 absent; 12392 currently identifies as svchost, with creation time inaccessible. No process was terminated or authority weakened. The remaining current-PID creation-time limitation is disclosed rather than resolved from a name alone. All three monitors and resource samplers recorded exit 0. Current host snapshot: no VBox/VirtualBox/J6Probe processes; VBoxSDS stopped. See cleanup.json, cleanup-followup.json and host-state-final.json. The first cleanup checker reports process-object existence, not a proven live workload; it must not be used to infer a runaway test from that record alone. Archive tooling (`seal_archive.py`, `transfer_archive.py`) packages only this diagnostic directory; no synthetic input disks or protected files are copied. Final member count/hash is in archive-verification.json.
