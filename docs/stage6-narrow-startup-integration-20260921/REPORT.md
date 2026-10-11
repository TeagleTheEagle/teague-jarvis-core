# Stage 6 narrow startup-trace integration validation

Disposition: BLOCKED — full large-run trace retention capacity has not been established. Small integration validation passed; no large-run authorization was exercised.

## Boundary and changes

Fresh candidate: `D:\JARVIS-STAGE6-LIVE\7a3f06371aa14bb18e08339837103d62\code`. All 389 prior frozen source hashes were reverified before and after. The 59.7 GB dataset and protected VM/configuration were not read or modified. Production was not modified.

Frozen `large_collect.py`, `baseline_hash_worker.py`, `bounded_sampler.py`, `probe_timing.py`, queue, monitor and finalization code remain byte-identical. New wrappers add separate marker files and delegate the same collector/workers; the native tracer selects already identity-qualified descendants for detailed metadata. There is no attach-to-arbitrary-PID command. The tracer and independent application observer alone receive per-run UAC elevation.

The small-only configuration admits only the new 12-file, 786,432-byte synthetic root. Campaign/monitor/workload hold are 90/180/0 seconds for this small fixture; the frozen large 1080/1200/788 configuration was not changed. Safety thresholds remain 10-second heartbeat, 13.6-second process deadline, 15-second independent observation.

Changed-artifact before/after SHA-256 values are in `changed-artifact-hashes.json`; exact launcher/native diff is in `integration.diff`. Generated objects and manifests are hashed too.

## Validation

- Eight focused adapter tests passed (exit status propagation, exceptions, unchanged wait forwarding, identity/result preservation, command rejection, marker identity/order, bounded marker retention and no evidence overwrite).
- Python syntax: three new modules parsed. PowerShell launcher parser: no errors. Native build: exit 0; inherited variable-shadow warning retained in build evidence.
- Evidence/integrity assertions: 560/560 passed, including 389 prior and 106 current source hashes. These are not 560 runtime test cases.

| Case | Collector result | Lifecycle | Retained / qualified post-exit | Maximum heartbeat | Trace events / cap | Cleanup |
|---|---|---|---|---|---|---|
| normal | DIAGNOSTIC_COMPLETE | 9 START / 9 STOP | 8 / 1 | 1.0404373 s | 155,105 / 200,000 | PASS |
| controlled-startup-failure | FAILED | 9 START / 9 STOP | 8 / 1 | 1.0555400 s | 142,035 / 200,000 | PASS |

Normal execution completed both hash passes for all 12 files, preserved metadata, passed the unchanged dual-evidence checker and finalizer, and produced a verified 47-member inner archive. Manifest SHA-256: `502941a6696ff28c6f6ae58d484b1cff09765d144464c0b31970f20091aa5d40`.

Controlled failure: `CONTROLLED_HASH_START_FAILURE` was injected in the new small TEST worker wrapper before calling the unchanged hash worker. The process exited nonzero; the collector and launcher preserved failure. No hash pass or successful baseline manifest was created. Both observers exited normally. Cleanup PASS does not change the collector failure into a successful collection.

Both runs recorded launcher entry, collector Python entry/start, helper invocation/create/return, PID/creation identity, monotonic timestamps, return/exception state and final shutdown. Detailed ETW events cover collector, hash worker, sampler, lifecycle probes and owned helpers. Exact 30 recorded identity entries (including observer/launcher entries) were checked after completion: zero matching live identities; zero matching diagnostic or VirtualBox processes; zero trace sessions.

## Comparison with pre-integration behavior

Comparison is against the unchanged collector implementation and output contract, not a new timed A/B benchmark. Normal status remains DIAGNOSTIC_COMPLETE; state reaches VERIFIED; both file/hash maps equal the pre-run independent synthetic manifest. Existing cleanup/finalization functions accepted the results without changes. Failure status remains FAILED, records the original exception, omits successful manifests and still proves actual cleanup. New diagnostic data is additive in separate files.

## Remaining integration limitation

The trace remains capped at 200,000 detailed events and fails closed on overflow. A short normal run retained 155,105 events, of which 122,809 belonged to the independent PowerShell observer. The controlled case retained 142,035. Neither overflowed; neither demonstrates sufficient capacity for the frozen long collector with its 788-second hold and repeated helpers. Prior standalone 80-probe validation retained 183,217 events before this broader helper integration. These are capacity warnings, not a fabricated large-run failure. No cap or deadline was increased.

Python ENTRY markers deliberately identify wrapper entry. The separate native J6EntryObserve PE-entry/debug-register experiment is not inserted into the frozen probe creation path; these Python markers must not be reported as native PE entry or first Windows instruction. Full native-entry equivalence remains unproven.

Minimum next review: restrict detailed trace selection to the required collector branch (keeping complete identity-qualified process lifecycle coverage), then specify bounded durable D: retention with explicit overflow/write-failure behavior if necessary. Separately decide whether the large-run contract requires the native PE-entry marker for each existing probe; if so, integrate it without replacing the real probe identity or changing its wait/deadline semantics. Do not simply enlarge the cap or silently omit required evidence. Validate these changes on small data before any large rerun.

## Preservation, archive and rollback

Normal run: `D:\JARVIS-STAGE6-LIVE\7a3f06371aa14bb18e08339837103d62\code\protected-cda0e6c7d5774746afaef2d4e93602f8`. Controlled failure: `D:\JARVIS-STAGE6-LIVE\7a3f06371aa14bb18e08339837103d62\code\protected-f188cd5baa194c3c9c307e33427bf8e3`. Both are preserved. The normal archive is verified independently; the outer evidence archive contains both runs, candidate artifacts and this report. Its final receipt is `archive-verification.json`.

Rollback: select the previous frozen candidate; do not launch the new traced launcher. No changes to frozen originals or runtime require reversal. Keep the isolated candidate and failed-case evidence. No deletion, source reset, production action or protected-source operation is needed.

Historical probe/sampler/storage delay causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED. No fresh large hashing, real protected baseline, VirtualBox operation or production operation was performed.

BLOCKED — large-run detailed-trace retention and native-entry equivalence remain unvalidated.
