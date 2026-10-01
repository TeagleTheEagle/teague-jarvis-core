# Stage 6 — one small integrated loss diagnostic

**INTEGRATED DIAGNOSTIC EVIDENCE FAIL. Stage 6 remains incomplete.**

The original ETW event loss did not recur. A different mandatory evidence check failed for four OS console helpers. No second attempt, acceptance promotion, capture-setting correction or evidence-rule change was made.

## Exact execution and preserved boundaries

Date: 2026-09-23 Australia/Sydney (evidence UTC timestamps fall on 2026-09-22).

Candidate: `D:\JARVIS-STAGE6-LIVE\693f0cd17ff4419aaf404604a23edc5f\code`.
Run: `protected-ecf34c358dd84cdeb4a1e39006baf05a` beneath that candidate. The prefix is the existing TEST collector convention, not evidence of protected-source access.

Dataset: 12 sacrificial files, 786,432 bytes. No 59.7 GB dataset or protected VM/configuration was accessed. Production JARVIS was unchanged. No VirtualBox launch, Windows security changes, installation, paid call or acceptance commit occurred.

Prepared a fresh copy of the verified 181-file small-integration candidate and overlaid exactly the validated telemetry sources/headers and two tracer binaries. Rebound only the new candidate's launcher DLL path and synthetic allowlist. Regenerated its source manifest. Exact before/after hashes and two path-binding diffs are preserved. Previous candidates were not edited.

Preflight: zero matching diagnostic/VirtualBox processes and zero diagnostic trace sessions. Existing 10 small-binding/health tests passed; launcher syntax passed. TEST capture settings, providers, 180/1200-second tracer limits, 10-second heartbeat limit, 13.6-second probe deadline and 15-second observer bound remain unchanged.

Actual command: installed `pwsh.exe -NoProfile -File <report-directory>\run.ps1 -Case normal`, once. Three separately identified UAC prompts launched the authority tracer, detailed tracer and supporting CIM application observer. Collector, hash worker, sampler, native entry tracing, retained handles and queue/finalization logic were the existing integrated paths. Normal orchestration remained non-elevated.

## Result by component

| Component | Result |
|---|---|
| Collector / both SHA-256 passes | PASS, exact equality for all 12 files |
| Metadata and final synthetic source hashes | PASS |
| Collector elapsed invocation | 1.4998845 seconds |
| Authority ETW loss | 0 EventsLost, 0 real-time/log buffer loss |
| Detail ETW loss | 0 EventsLost, 0 real-time/log buffer loss |
| Telemetry collection | PASS, no telemetry/query/phase errors |
| Recorded lifecycle | 14 instances / 28 durable START/STOP records |
| Mandatory identity coverage | FAIL: 10/14 verified; four image fields missing and four capture predicates contradictory |
| Application queue | 22 enqueued/persisted/removed, zero remaining, no queue failure |
| Application finalization | reported success; unsubscribed and durable finalization true |
| Maximum application heartbeat | 1.0547305 seconds |
| Sampler | one query, bounded cleanup completed, thread exited |
| Native bridge | four threads exited, no bridge errors |
| Launcher cleanup | collector and all three observers exited with code 0 |
| Final host census | zero matching processes / zero diagnostic trace sessions |

The unchanged `small_check.check()` rejected `EVIDENCE_COVERAGE`; it was not changed to accommodate the result. Its later acceptance predicates were not represented as having passed. Independent raw-artifact measurements above do not substitute for failed qualification. `diagnostic-check-failure.json` preserves the exact first rejection. A subsequent offline inspection wrapper recorded the existing coverage function's inputs/output without changing its result or any candidate source; it did not rerun the workload.

## Exact evidence blocker

All four failures are classified by the existing checker as `OS_CONSOLE_HELPER`, image `\Device\HarddiskVolume6\Windows\System32\conhost.exe`. Creation/exit evidence belongs to specific recorded instances; this is not a PID-only inference. Each tracer retained a creation-matching handle, but its handle-derived image was empty and image API status was 31.

| PID | Creation FILETIME | Kernel lifetime (s) | START event → callback (s) | Image query after recorded STOP (s) |
|---:|---|---:|---:|---:|
| 1860 | See complete instance row in failed-identities.json | 0.0285611 | 1.9198032 | 1.8911634 |
| 6920 | See complete instance row in failed-identities.json | 0.6383990 | 1.9956905 | 1.3571754 |
| 7204 | See complete instance row in failed-identities.json | 1.4098171 | 2.3531305 | 0.9432747 |
| 24344 | See complete instance row in failed-identities.json | 0.1431178 | 1.9709252 | 1.8276841 |

Established: their START callbacks arrived after their kernel-recorded lifetimes had ended; the subsequent image queries occurred after exit. These rows cannot meet the required live tracer-handle image-capture predicate.

The existing post-exit exception requires `OPEN_PROCESS_FAILED`, error 87 and a qualified acquisition attempt after STOP. These four rows instead have retained handles and failed image queries. They do not satisfy that exception. No force matching, image substitution from the ETW image name, PID-name fallback or silent exception expansion was performed.

The exact Windows mechanism behind the callback delivery lag is not established. The timing proves the failed acquisition ordering, not why Windows delivered those notifications when it did. It also does not prove the historical tracing-loss cause.

## New telemetry findings

| Measurement | Authority | Detailed |
|---|---:|---:|
| Callbacks received | 53 | 1,507,334 |
| Selected records | 28 | 154,835 |
| Counter snapshots | 52 | 30 |
| Actual buffers observed | 32 | 32,34,36,40,41,43 |
| Maximum query duration (s) | 0.0000728 | 0.0001442 |
| Maximum callback interval (s) | 0.0056942 | 0.5281064 |
| Maximum measured guard wait (s) | 0.0000030 | 0.7532471 |
| Maximum metadata interval (s) | 0.0056915 | 0.5280658 |
| Maximum sink WriteFile (s) | 0.0004190 | 0.0037647 |
| Maximum sink FlushFileBuffers (s) | 0.2129189 | 0.2424044 |

Every sampled loss counter and both final loss counters were zero. Guard metrics aggregate callback and sampling users; they are not exclusively callback wait times. Timing includes descheduling, so none of these values identifies a CPU, storage or driver cause by itself.

77.32% of persisted detailed events belonged to the application observer. Of 83,894 records after collector return, 83,817 belonged to that observer. The monitor-heavy finalization pattern therefore recurred without ETW loss on this attempt. This weakens any claim that such traffic alone necessarily causes loss, but does not establish a safe worst-case capacity or rule out resource-dependent effects.

Full phase/counter snapshots, per-process results, metrics and failure identities are archived. This single run neither explains nor erases the earlier 4/50,130 loss counts.

## Preservation, cleanup and disposition

Final read-only census: 2026-09-22T23:08:32.0310616Z; zero matching diagnostic/VirtualBox processes, zero diagnostic trace sessions. Existing stop-file cleanup was used; no forced process termination. Earlier census and launcher cleanup evidence remain preserved.

Finalization verifies current frozen source hashes, the prior integration/telemetry candidates, synthetic metadata and archive membership. The separate archive receipt is authoritative for archive success and hashes. No historical failure was overwritten.

Rollback: deselect this new TEST candidate and retain all its diagnostic evidence. No production restoration is needed.

**Next proposed work:** narrowly review the OS-helper image-capture timing path and the existing post-exit qualification boundary. A correction must provide the required independent evidence reliably; merely copying the ETW image into the handle-image field or treating these cases as the existing error-87 exception would weaken the contract. Any change to that evidence boundary requires explicit review. Do not rerun integrated acceptance, increase deadlines, tune buffers or advance to large/protected validation on this result.

Historical tracing/delay causes remain UNCONFIRMED. Historical 21 AMBIGUOUS / 1 UNMATCHED unchanged. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
