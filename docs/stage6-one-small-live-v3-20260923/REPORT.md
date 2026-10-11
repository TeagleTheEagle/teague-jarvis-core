# Exactly one Stage 6 small-live attempt — REJECTED

Primary disposition: **SMALL_LIVE_INTEGRATION_FAILED — AUTHORITATIVE_TRACE_LOSS**.

Run: `protected-f117995dd9ef4ed1b33c1b44b1973293`.
Normal case, 12 synthetic files / 786,432 bytes. Exactly one preparation and one
wrapper invocation occurred. No retry, candidate correction or checker replacement.

## First failure

`terminal-failure-v3.json`: `terminal trace loss/query`.
`launcher-failure.json`: `Authority terminal failure`.
External driver subsequently rejected with `LAUNCHER_FAILED`; that is the propagated
failure, not a replacement for the first terminal-evidence failure.

Final authority trace: `eventsLost=13`, `faults=1`, exit 95.
Final detailed trace: `eventsLost=120281`, `faults=0`, exit 95.
Application observer exited 0 and reported durable finalization, 10 persisted/removed
queue entries and zero queue residue. Successful supporting evidence cannot compensate
for authoritative loss. The underlying reason for trace loss is **UNCONFIRMED**.

## Original absolute deadline

Frequency: 10,000,000 QPC ticks/second.
Cleanup origin: 4361882652218.
Deadline: 4362082652218 (origin + 20 seconds).

| Recorded event | Seconds after cleanup entry |
|---|---:|
| Collector returned with exit 0 | 1.1080592 |
| Phase A pending-external-exit state recorded | 1.1367192 |
| Launcher records authority-terminal exception | 1.1993339 |
| Launcher records failure-cleanup FINAL_SHUTDOWN | 14.1944094 |

This attempt failed before the deadline due to terminal evidence loss. The deadline
was not reset or extended. No valid acceptance cleanup/census was completed; the
later independent census is eventual cleanup evidence only, not acceptance repair.

## Requirement dispositions

| Requirement | Actual outcome |
|---|---|
| Preservation preflight | PASS: 216 candidate files, four add-on files, 482 preserved inputs; prior archives 515 + 6,296 members verified |
| Fresh normal-case binding | Established; frozen source manifest/declaration bound to this new run |
| Observer readiness | All three reviewed observers reached readiness; collector started afterward |
| Collector | Returned 0; diagnostic completion only |
| Both synthetic hash passes | PASS: all 12 file records equal |
| Source metadata | PASS: metadata record reports 12 files / 786,432 bytes unchanged |
| Phase A | Published local durable/handle/tracker closure with acceptance=false and cleanupPass=false |
| Exact terminal helper receipt | FAIL: producer rejected trace-loss/query condition; no terminal receipt published |
| Retained/kernel/native consistency | NOT ACCEPTED; no complete terminal qualification |
| Authoritative trace loss | FAIL: 13 lost authority events |
| Detailed trace loss | FAIL: 120,281 lost detailed events |
| Sequence/segment acceptance | NOT EVALUATED by versioned checker after failure |
| Pre-shutdown workload census | NOT REACHED |
| Ordered success observer shutdown/tail receipt | NOT REACHED; existing bounded failure cleanup used |
| External acceptance exit proof/final census | NOT REACHED |
| Versioned TEST checker/success finalizer | NOT INVOKED |
| Normal acceptance seal/archive | NOT CREATED |
| Failure-preservation path | Invoked once; partial archive verified, acceptance_seal=false |
| Later host cleanup | Zero matching diagnostic/VirtualBox processes, zero trace sessions, zero unknown census results |
| Recorded-instance cleanup | 16 recorded identities checked; no matching live instance or unknown handle result |
| Production/protected VM | Not accessed or modified |

## Exact identities

| Role | PID | Creation FILETIME |
|---|---:|---|
| Launcher | 17868 | See preserved launcher-identity.json |
| Kernel authority | 22600 | 134346033820596555 |
| Detailed startup | 13544 | 134346033840904566 |
| Application observer | 6956 | 134346033859413978 |
| Collector | 22892 | 134346033876135644 |
| Collector console helper | 16144 | 134346033876712650 |

All three observer executable paths and their pre-run signatures/hashes are recorded
in `expected-uac-identities.json`. The two TEST tracers are unsigned; PowerShell has a
valid Microsoft signature. No fourth elevation was requested by the reviewed launcher.
No secure-desktop screenshot or automatic UAC approval was used.

## Failure preservation and later cleanup

The unchanged failure tool initially observed a still-live matching PowerShell instance:
PID 6368, creation FILETIME 134346033771024754. Its relationship is not inferred from PID
alone. The tool correctly returned **CLEANUP_UNPROVEN / FAILURE_EVIDENCE_PARTIAL**,
preserved metadata and omitted mutable source contents. It must not be relabeled complete.

Original failure ZIP:
`D:\JARVIS-STAGE6-LIVE\cab9745de28a4cae8aa6f6f7a516bf54\preservation\FAILURE-EVIDENCE-protected-f117995dd9ef4ed1b33c1b44b1973293\FAILURE-EVIDENCE-protected-f117995dd9ef4ed1b33c1b44b1973293.zip`

SHA-256: `bc5a01896fabbea6c76e12243c76a800abfd6710672c95b0f5d7639267d4b365`.
Two archive members verified; zero raw evidence files were included in that provisional
archive. Its manifest SHA-256 is
`bda1300b3e7a3fdd36f0050c97cf41107673d985c9b8886bcf6ee13b4efb0fb4`.

After the wrapper exited, a separate read-only host/recorded-instance census established
eventual cleanup. The raw failed run then contained 83 stable files. These are preserved
byte-for-byte in the canonical supplemental evidence package along with the original
partial archive and post-run reports. This is archival of a rejected result, not a second
run, retry of the failure tool, upgraded preservation status or acceptance seal.

The supplemental archive's inventory, hash verification and final frozen-source check
are recorded in `archive-receipt.json`. No original run or failure-preservation file is
edited by supplemental archival. Missing acceptance evidence remains missing.

## Limits / next review

Review the trace-loss finding and the initial preservation census separately before
authorizing any further investigation or attempt. No diagnosis beyond reporting the
observed failure counters was executed; no capture setting, deadline or code was changed.

Historical causes remain UNCONFIRMED. Historical 21 AMBIGUOUS / 1 UNMATCHED remain
unchanged. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

No medium/large/59.7 GB validation, protected hashing, VirtualBox operation, production
change or acceptance commit. Stage 6 remains incomplete. STOP FOR OWNER REVIEW.
