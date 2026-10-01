# ONE_MORE_DISCRIMINATING_EXPERIMENT_REQUIRED

Analysis only, using the preserved single run `protected-6d70ad58f22749b59f4dae6e9bf2ed10`. No implementation, tests, live rerun, UAC, current process census, protected VM access or production operation. All 381 input archive members were verified before analysis; the five detailed segments were also checked against their recorded hashes. The historical archive is unchanged.

## 1. Findings summary
Authority independence coincided with zero authority loss while detailed loss remained 100,564. This supports the predeclared coupling hypothesis for this run only; authority is not permanently qualified. Historical ETW-loss root cause remains UNCONFIRMED.
Three surfaces remain distinct: (A) detailed session loss, (B) a missing collector registration cascading into target rejections, and (C) a later management-census mismatch. A precedes B and C. The B state cascade is established; attribution of its missing parent payload to A is strongly supported but not directly proven. C does not consume detailed lifecycle state and is not shown to be caused by A or B.

## 2. Detailed loss timing
All QPC values use frequency 10,000,000. The exact first lost-event instant is UNKNOWN. Last zero-count query spans 6324646242924–6324646243224; first nonzero query spans 6324647250925–6324647251282 and reports 3,436. The conservative first-increment bracket is 6324646242924–6324647251282.
All six observed increases are concentrated in a 0.6295738-second sampled window, ending at 6324652538662 with 100,564. No later increase is recorded. The collector START observed by authority is at 6324647351168, inside this window; its console START is at 6324648037440. Neither START exists in the complete, non-overflowed detailed callback sidecar. Collector STOP and console STOP later exist there, rejected UNKNOWN_INSTANCE.

| Last/next query bracket (QPC) | Count change |
|---|---:|
| 6324646242924–6324647251282 | 0 → 3436 |
| 6324647250925–6324648296583 | 3436 → 28117 |
| 6324648296319–6324649339476 | 28117 → 51575 |
| 6324649339241–6324650382208 | 51575 → 72835 |
| 6324650381875–6324651450373 | 72835 → 93429 |
| 6324651449879–6324652538662 | 93429 → 100564 |

The eight target creation events occur at 6324655073221 through 6324661208784: all AFTER the observed loss-increase window. First target START rejection callback: sampler at 6324662493882. First target STOP rejection callback: probe 1 at 6324662608457. Management census exception: 6324692858613. Its exact failed comparison instant is not separately recorded; it lies after TERMINAL_EVIDENCE_COMPLETE at 6324690697557 and before the exception marker. Thus target rejection does not overlap observed counter growth; missing ancestor creation does.

### Existing stall, burst and storage evidence
- Metadata scopes lasted 450.6452 ms at 6324638236264–6324642742716, 198.0930 ms at 6324642743183–6324644724113, and 98.6566 ms at 6324644728643–6324645715209. Their enclosing callbacks took approximately 450.6866 / 198.1325 / 98.7004 ms. These are nested durations, not additive separate delays. A sampler/management thread guard wait reached 646.7210 ms during the first two callbacks.
- The last long callback ended 52.7323 ms before the last zero-count query began. These stalls precede observed loss, not overlap its measured growth. They could build backlog, but no recorded counter proves that they caused exhaustion.
- During the six growth intervals, completed callbacks progress: 10,276; 9,209; 10,926; 29,057; 50,078; 118,996. There is no complete consumer stall throughout the loss window. Consumer CPU advances by 593.75 ms over approximately 629.57 ms (one consumer thread, about 94%). Peak sampled completion rate is approximately 1.093 million/s. Scheduling and CPU pressure cannot be isolated from these counters alone.
- During most counter growth, allocated/free buffers remain 44/28 and BuffersWritten remains 639. At the last increment allocated/free become 53/37 and BuffersWritten 770. Maximum allocated is 53, below requested maximum 64. Minimum free over the whole run is 17. No sampled exhaustion is observed; an inter-sample transient remains possible.
- Writer rotation 6324650680197–6324652106169 overlaps the late loss window. Its flush takes 130.8847 ms; pending queue grows from 902 records/224,260 bytes to 8,221/2,043,754. However loss had already reached 72,835 before this flush began, so it cannot explain the initial loss by itself. Whole-run queue peaks at 11,771 records / 4,021,640 bytes, later than onset.
- Five detailed segments hash-verify: 122,969 admitted records equal 122,969 persisted records, 40,576,650 bytes, sink fault 0; final pending queue 0. RealTimeBuffersLost and LogBuffersLost are 0. These are distinct from EventsLost=100,564 and do not excuse it.
- Final completed callback count in loss-telemetry.json is 1,349,953. The last periodic diagnostic sample contains only 1,308,296 because sampling precedes final consumer completion; it is not the final total. Final selected 122,969, rejected 1,226,984. Detailed maximum callback duration 450.6866 ms; sampled delivery-lag maximum 1.5498659 seconds. Authority sampled maximum lag 2.6907751 seconds despite zero loss, so lag alone is not a sufficient explanation.

Persisted selected categories: process=450, scheduler=15895, registry_classic=10150, registry=6550, file=89924. These are admitted-record counts, not incoming or lost-event provider totals. All detailed payload records belong to application observer 3440 / creation 134347996384951532 or its console 27512 / creation 134347996387547509. No target payload may be assumed present merely because segment persistence succeeded. Provider-specific loss and the exact missing payload identities are not directly recoverable.

## 3. Exact lifecycle-state findings
Detailed and authority use the same essential ParentKnown predicate: accept the launcher root, or find a registered parent with matching PID, creation/lifetime and parent sequence where supplied. START inserts into the `(PID, creation)` map only after that check. STOP requires that exact key. The maps are local to each observer. Detailed receives no collector START at any point; authority receives and admits it as sequence 12 at callback QPC 6324658953294. Detailed therefore cannot register collector 15508 / creation 134347996400262078 / kernel sequence 76419.
Authority registers each parent before its child and each exact instance before STOP. Detailed processes each target START before that same target STOP; child/helper STARTs follow their parents’ rejected STARTs. No late collector START appears after those rejections. This is NOT evidence of child-before-parent callback reordering or STOP-before-START delivery. Missing parent registration explains the cascade without a selector implementation defect.
Detailed START processSequence=0 here is an unread field after the early rejection, not proof of a zero kernel sequence. The recorded parent sequence is available. Do not force-match these diagnostic records into authoritative acceptance.

| Target | Exact identity PID / creation FILETIME | Parent PID / creation FILETIME |
|---|---|---|
| sampler | 17472 / 134347996407984941 | 15508 / 134347996400262078 |
| sampler_console | 23448 / 134347996408955533 | 17472 / 134347996407984941 |
| hash_worker | 25220 / 134347996407986600 | 15508 / 134347996400262078 |
| hash_console | 8524 / 134347996408730676 | 25220 / 134347996407986600 |
| probe_1 | 21444 / 134347996408723312 | 15508 / 134347996400262078 |
| probe_1_console | 3112 / 134347996409564971 | 21444 / 134347996408723312 |
| probe_2 | 5028 / 134347996412956595 | 15508 / 134347996400262078 |
| probe_2_console | 1708 / 134347996414121458 | 5028 / 134347996412956595 |

For ALL eight detailed STARTs: parentKnown=false, disposition UNKNOWN_PARENT, admitted=false. For ALL eight detailed STOPs: instanceKnown=false, disposition UNKNOWN_INSTANCE, admitted=false. For ALL eight authority STARTs/STOPs: ADMITTED; parentKnown=true on START and instanceKnown=true on STOP.

| Target | Detailed START event / callback QPC | Detailed STOP event / callback QPC |
|---|---|---|
| sampler | 6324655073221 / 6324662493882 | 6324657779804 / 6324662626362 |
| sampler_console | 6324656043484 / 6324662524373 | 6324657795289 / 6324662627128 |
| hash_worker | 6324655074673 / 6324662493971 | 6324663310208 / 6324672578400 |
| hash_console | 6324655818671 / 6324662504872 | 6324663325771 / 6324672579359 |
| probe_1 | 6324655811412 / 6324662504522 | 6324656988759 / 6324662608457 |
| probe_1_console | 6324656652904 / 6324662571659 | 6324656999277 / 6324662609562 |
| probe_2 | 6324660044121 / 6324662651812 | 6324661481905 / 6324662679338 |
| probe_2_console | 6324661208784 / 6324662662720 | 6324661491203 / 6324662680155 |

| Target | Authority START event / callback QPC | Authority STOP event / callback QPC |
|---|---|---|
| sampler | 6324655073218 / 6324668964873 | 6324657779800 / 6324678980376 |
| sampler_console | 6324656043481 / 6324678978645 | 6324657795286 / 6324678980745 |
| hash_worker | 6324655074670 / 6324678977091 | 6324663310205 / 6324678983522 |
| hash_console | 6324655818668 / 6324678978274 | 6324663325769 / 6324688983946 |
| probe_1 | 6324655811409 / 6324678977917 | 6324656988755 / 6324678979651 |
| probe_1_console | 6324656652901 / 6324678978990 | 6324656999274 / 6324678980065 |
| probe_2 | 6324660044116 / 6324678981204 | 6324661481902 / 6324678982380 |
| probe_2_console | 6324661208781 / 6324678981679 | 6324661491200 / 6324678983041 |

The exact registration/admission/rejection instruction timestamp is UNKNOWN: the sidecar stores event QPC and callback-entry QPC, plus final disposition, but no independent decision QPC. Event/callback order and predicates are sufficient for the state conclusions above; callback-entry timestamps must not be relabelled as exact decision times.

## 4. Authority versus detailed
Both use process provider 22fb2cd6-0e7b-422b-a0c7-2fad1fd0e716 at information level. Authority keyword=0x10 and requested mode=0x08000100; detailed keyword=0x70 plus file 0x1f0, registry 0x400000000000ac33 and system logger context-switch/dispatcher/registry flags, requested mode=0x02000100. Buffers stay 64 KiB / requested min 4 / max 64 / flush 1 / QPC / per-processor. Detailed also performs payload metadata/serialization under its state guard; authority has the reviewed capture/handoff path. These pre-existing differences prevent attributing every detailed symptom to a single setting.
Authority accepted because its collector/parent STARTs reached and populated its map. Detailed rejected because that collector entry was absent; its console map entries were then also absent. The observed detailed target callbacks remain chronologically ordered. Classification of **delayed/out-of-order delivery causing these rejections: UNSUPPORTED by this run**. Classification of **upstream loss removing ancestor coverage, then a registration cascade: STRONG_CAUSAL_EVIDENCE**, with exact lost-payload attribution still unproven.

## 5. Management census
Expected management set from small_launch_v4.ps1:38 is five exact instances:
- launcher: PID 8352, creation 134347996174975719.
- authority: PID 18448, creation 134347996360081320.
- detailed: PID 25224, creation 134347996374111814.
- application: PID 3440, creation 134347996384951532.
- external controller: PID 11736, creation 134347996147735955.

WorkloadCensus queries Win32_Process, filters names or D:-workspace command lines, obtains creation time through Get-Process, and requires every matched process to belong to that five-instance set. It then requires found.Count == expected.Count. That last comparison threw. The raw `$all`, `$found`, counts and missing identities were not persisted before the throw. Exact missing entry/entries: UNKNOWN. The eight target workloads are not members of this management set.
The method does not read detailed ETW rows. Its receipt input is authority terminal evidence for collector/helper; that receipt already passed. Therefore incomplete detailed lifecycle evidence is not a direct input causing this comparison. Command-line visibility, early management-process exit or another enumeration issue are possibilities, not established causes. No census correction is justified yet.
Terminal receipt was captured at 6324688989746 and observed at 6324690248295; TERMINAL_EVIDENCE_COMPLETE at 6324690697557; census exception at 6324692858613. Final shutdown at 6324810641639. Original cleanup deadline 6324864756591. The failed acceptance census remains failed even though preservation-time and final host censuses later recorded zero processes/traces and all 16 recorded instances absent. The preservation manifest’s cleanup flags are not a substitute for missing workload-census/external-exits/final-census/observer-tail acceptance evidence.

## 6. Earliest blocker and confidence
- Earliest observed acceptance violation: **DETAILED_ETW_SESSION_LOSS**; underlying loss mechanism UNCONFIRMED.
- Target rejection mechanism: parent-map absence followed by exact-instance absence, PROVEN from source and records. A selector-order bug is not established.
- Loss-to-missing-collector relationship: STRONG_CAUSAL_EVIDENCE; no direct lost-payload inventory.
- Management-census mismatch: separately proven failure; exact missing management identity/cause UNKNOWN. Logical independence of its input path is proven, but a common host timing/resource contributor cannot be ruled out.

## 7. Exactly ONE proposed discrimination experiment — OWNER REVIEW ONLY
Prepare a fresh TEST successor changing ONLY detailed startup_trace.cpp:106 LogFileMode from `EVENT_TRACE_REAL_TIME_MODE | EVENT_TRACE_SYSTEM_LOGGER_MODE` (0x02000100) to that expression OR `EVENT_TRACE_INDEPENDENT_SESSION_MODE` (0x0A000100). Authority remains byte-identical at requested 0x08000100. This is a configuration experiment, NOT a proven fix. Do not implement it in this review.
Before a separately authorized attempt, prove one-bit source/config delta and compile/SDK compatibility offline, detailed binary provenance, unchanged authority binary, providers, buffers, callback/state maps, helper handoff, telemetry, clocks, deadlines, checker/finalizer and loss rejection. Unsupported start/configuration combination must stop rather than trigger an alternative setting.
One fresh normal small run only: 12 synthetic files / 786,432 bytes, fresh D: workspace/run binding, existing three approved observers subject to separate live/UAC authorization, no retry. Preserve the original 20-second absolute cleanup deadline, heartbeat and process deadlines. No census correction bundled. Capture only the existing telemetry and compare collector START coverage, target admission, both final loss counters and unchanged cleanup/acceptance results. No protected VM or production access.

| Outcome | Predeclared interpretation | Acceptance |
|---|---|---|
| Detailed start/config rejected | Proposed mode not established as usable on this host | BLOCKED; no alternative setting/retry |
| Both zero loss, collector/targets present | Supports detailed isolation affecting delivery in this attempt; not historical proof | PASS only if EVERY existing criterion, including census, also passes |
| Both zero loss, collector missing or targets rejected | Loss counter alone does not explain coverage; retain exact state defect evidence | FAIL |
| Authority zero, detailed loss persists | Detailed independence did not resolve detailed loss in this attempt | FAIL |
| Authority becomes nonzero | Authority zero-loss is not stable under this experiment; no causal simplification | FAIL |
| Loss/coverage improves but management census still fails | Tracing result and census failure remain separate | FAIL |
| Any identity, deadline, persistence, cleanup or preservation failure | Preserve first failure; no causal PASS substituted | FAIL/BLOCKED as recorded |

This action is preferred because the only existing causal intervention improved authority coverage without changing its selector. It tests the remaining isolation hypothesis with one narrow reversible setting. Metadata stalls and high event volume are real, but the evidence does not yet justify a callback rewrite, buffer expansion, selector relaxation or census repair. The experiment may still fail acceptance at census; that must remain explicit.

## 8. Evidence references and disposition
Input archive SHA-256: ee431ece0f64256a83f15de3224fc03986490acab73e9c9561210bda8a351198
Raw evidence inside the archive: detail/loss-diagnostic-v2.json; detail/loss-telemetry.json; detail/etw-result.json; detail/startup-events.json and trace-00000..00004.jsonl; diagnostic-sidecars; integration-launcher.json; terminal-v3.json; terminal-observed-v3.json; observer-identities.json; external-controller-v3.json; original-failure-preservation/FAILURE-MANIFEST.json. Full eight-instance comparison is in adjacent analysis.json.
Source references in the archived candidate: startup_trace.cpp:40–52 (lifecycle state), :64–93 (payload callback), :106–111 (configuration); authority_trace_v3.cpp:38–58 (lifecycle), :72–75 (configuration); terminal_control_v3.ps1:60–83 (census); small_launch_v4.ps1:38 and :49–57 (management set/ordering); lifecycle_witness_v1.hpp:35–50 (timestamp semantics).
No historical evidence was edited. No new live process census or trace measurement was performed; cleanup statements refer to preserved evidence only. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

**ONE_MORE_DISCRIMINATING_EXPERIMENT_REQUIRED**. STOP for owner review. No implementation or run authorized by this report.
