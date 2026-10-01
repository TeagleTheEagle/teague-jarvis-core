# CROSS_SESSION_COUPLING_SUPPORTED

Run remains REJECTED. Stage 6 remains INCOMPLETE. Authority EventsLost = 0; detailed EventsLost = 100,564. This matches owner-predeclared CASE A, supporting authority cross-session coupling as a contributor. One run does not establish historical root cause or qualify the detailed observer.

Run: `protected-6d70ad58f22749b59f4dae6e9bf2ed10`
Workspace: `D:\JARVIS-STAGE6-LIVE\51faa5f9320b4b05b75cc522648621a7\code`
Exactly one normal small attempt, three approved observer launches, no retry and no configuration changes during execution.

## Configuration and inputs
Authority requested mode 0x00000100 -> 0x08000100 only. Runtime returned authority mode 0x08400100; previous returned mode 0x00400100. The XOR is exactly 0x08000000. Detailed returned mode remains 0x02400100 (requested 0x02000100). Windows-added flags are distinguished from the requested mode. Every other recorded configuration field matches the preceding run. Source comparison confirms only the authority flag change; only the two approved workspace-path JSON files were rebound before launch.
Both 12-file / 786,432-byte synthetic SHA-256 passes matched; metadata unchanged. Frozen successor, predecessor, detailed observer, checker/finalizer and historical archives verify unchanged. Runtime/DLL/workspace bindings passed preflight.

## First failure and acceptance
The launcher recorded `Management census incomplete` at QPC 6324692858613. Collector returned 0; Phase A and terminal receipt were recorded before this failure. Pre-shutdown management census did not complete, so the acceptance shutdown/census path could not close. Detailed terminal EventsLost independently rejects the run. No checker or success finalizer was invoked. No repair or additional experiment was performed.
Authority observer exited 0, detailed observer 95, application observer 0. The original failure archive remains FAILURE_EVIDENCE_PARTIAL because expected acceptance records are missing; it is not a complete acceptance seal. Its 91 members hash-verify with zero mismatches. Missing records: external-exits-v3.json, final-census-v3.json, observer-tail-v3.json, workload-census-v3.json.

## Exact target process instances
The following correlation uses creator-retained native handles or independently creation-verified helper handles. It does not replace authoritative evidence. Detailed JSON retains each callback, sequence, disposition, admission and independently bounded loss-overlap interval.

| Role | PID | Creation FILETIME | Authority START / STOP | Detailed START / STOP | Authority loss overlap | Detailed loss overlap |
|---|---:|---|---|---|---|---|
| sampler | 17472 | 134347996407984941 | CALLBACK_ADMITTED / CALLBACK_ADMITTED | CALLBACK_REJECTED_UNKNOWN_PARENT / CALLBACK_REJECTED_UNKNOWN_INSTANCE | False / False | False / False |
| sampler_console | 23448 | 134347996408955533 | CALLBACK_ADMITTED / CALLBACK_ADMITTED | CALLBACK_REJECTED_UNKNOWN_PARENT / CALLBACK_REJECTED_UNKNOWN_INSTANCE | False / False | False / False |
| hash_worker | 25220 | 134347996407986600 | CALLBACK_ADMITTED / CALLBACK_ADMITTED | CALLBACK_REJECTED_UNKNOWN_PARENT / CALLBACK_REJECTED_UNKNOWN_INSTANCE | False / False | False / False |
| hash_console | 8524 | 134347996408730676 | CALLBACK_ADMITTED / CALLBACK_ADMITTED | CALLBACK_REJECTED_UNKNOWN_PARENT / CALLBACK_REJECTED_UNKNOWN_INSTANCE | False / False | False / False |
| probe_1 | 21444 | 134347996408723312 | CALLBACK_ADMITTED / CALLBACK_ADMITTED | CALLBACK_REJECTED_UNKNOWN_PARENT / CALLBACK_REJECTED_UNKNOWN_INSTANCE | False / False | False / False |
| probe_1_console | 3112 | 134347996409564971 | CALLBACK_ADMITTED / CALLBACK_ADMITTED | CALLBACK_REJECTED_UNKNOWN_PARENT / CALLBACK_REJECTED_UNKNOWN_INSTANCE | False / False | False / False |
| probe_2 | 5028 | 134347996412956595 | CALLBACK_ADMITTED / CALLBACK_ADMITTED | CALLBACK_REJECTED_UNKNOWN_PARENT / CALLBACK_REJECTED_UNKNOWN_INSTANCE | False / False | False / False |
| probe_2_console | 1708 | 134347996414121458 | CALLBACK_ADMITTED / CALLBACK_ADMITTED | CALLBACK_REJECTED_UNKNOWN_PARENT / CALLBACK_REJECTED_UNKNOWN_INSTANCE | False / False | False / False |

CALLBACK_ADMITTED means observed and selected/admitted; NOT_OBSERVED_BEFORE_SELECTION does not establish a selector rejection. Missing observations leave selector disposition/admission UNKNOWN. Exact analyzer labels and records are preserved without reinterpretation.

## Buffer / callback / persistence context
| Measure | Authority | Detailed |
|---|---:|---:|
| finalEventsLost | 0 | 100564 |
| effectiveAllocatedBuffersMin | 32 | 32 |
| effectiveAllocatedBuffersMax | 32 | 53 |
| effectiveAllocatedBuffersFinal | 32 | 51 |
| minimumSampledFreeBuffers | 24 | 17 |
| buffersWritten | 28 | 1768 |
| realTimeBuffersLost | 0 | 0 |
| logBuffersLost | 0 | 0 |
| received | 36 | 1308296 |
| completed | 36 | 1308296 |
| selected | 28 | 122969 |
| maximumSampledReceiveRate | 143.1833281150965 | 1093413.6061285192 |
| maximumSampledCompletionRate | 143.1833281150965 | 1093422.7948642317 |
| callbackDurationMaxSeconds | 0.0007613 | 0.4506866 |
| deliveryLagMaxSeconds | 2.6907751 | 1.5498659 |
| queueHighItems | 3 | 11771 |
| queueHighBytes | 1313 | 4021640 |
| errors | 0 | 0 |
| overflow | 0 | 0 |

Rates are differences between sampled counters divided by the actual sampled QPC interval, not instantaneous peak rates. Null detailed duration/lag means the existing histogram had no observations; it must not be reported as zero latency. No telemetry was added.
Both final writer queues have zero pending items/bytes and zero writer error. Authority persisted 28 selected records, detailed 122,969. Draining all admitted records does not recover upstream loss. Minimum sampled free buffers do not rule out pressure between samples. All raw counters, per-sample callback rates, loss increments and existing slow spans are archived.

### authority EventsLost increments
None observed; final count 0.

### detailed EventsLost increments
- QPC 6324646242924–6324647251282: 0 -> 3436
- QPC 6324647250925–6324648296583: 3436 -> 28117
- QPC 6324648296319–6324649339476: 28117 -> 51575
- QPC 6324649339241–6324650382208: 51575 -> 72835
- QPC 6324650381875–6324651450373: 72835 -> 93429
- QPC 6324651449879–6324652538662: 93429 -> 100564

## Cleanup and preservation
Maximum heartbeat interval 1.2525922 seconds (<10). Original cleanup origin/deadline 6324664756591 / 6324864756591, frequency 10000000. The 20-second absolute deadline was not reset. Launcher FINAL_SHUTDOWN occurred 14.5885048 seconds after origin. This does not establish acceptance cleanup because the required census/exit proof path failed.
Post-run read-only host census: zero matching diagnostic/VirtualBox processes and zero trace sessions. Independent recorded-instance census: 16 identities, all absent, zero unknown/live. This is eventual cleanup proof only; it does not erase the failed management census.
A separate post-quiescence NON-ACCEPTANCE archive includes raw run evidence, original failure archive and manifest, diagnostic sidecars, exact correlation, candidate/bindings, telemetry and preservation checks. It supplements the original partial archive without rewriting it. See archive-receipt.json for member verification and SHA-256.
Protected VM/configuration not accessed; production unchanged. No medium/large/59.7 GB run. No buffer/provider/deadline/checker/finalizer change. Historical causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

## Disposition
CROSS_SESSION_COUPLING_SUPPORTED. No Stage 6 PASS. STOP for owner review. Detailed loss and the management-census failure remain unresolved; no correction is authorized or implemented in this action.
