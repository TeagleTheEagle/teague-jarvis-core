# One live helper-handoff revalidation

TRACE_DIAGNOSTIC_RUN_FAILED

Exactly one normal sacrificial attempt: `protected-4fc436a2cc6543e398388806441f522c`. No retry, candidate correction, checker replacement, ETW/configuration change or deadline change occurred. The three reviewed observers started; there was no additional elevation. The run was permanently rejected on authority terminal evidence failure. The success checker and success finalizer were not invoked.

## Result

The new helper handoff recorded the required order for the one outstanding collector-console obligation. Independent verification preceded local release by **67.7465 ms**; independent handle acquisition preceded release by **1,021.1059 ms**. This is a useful observation, **not accepted integration evidence**, because the authoritative stream lost events. The full handoff/terminal acceptance requirement remains open.

Terminal failure: `terminal trace loss/query`. Final counters: authority **EventsLost=2, faults=1**; detailed **EventsLost=31,239, faults=0**. Both report zero realtime/log buffers lost and successful flush/stop/consumer return codes. Zero buffer-loss counters do not cancel the EventsLost failure.

Both 12-file/786,432-byte hash passes agree. Source metadata remains unchanged. Maximum recorded application heartbeat interval: **1.3056142 seconds**, below the unchanged ten-second limit. Healthy hashing/heartbeat do not override missing authoritative evidence.

## Exact identity and handoff timing

QPC frequency: 10,000,000 ticks/second. Original cleanup entry `4707010281056`; deadline `4707210281056`, exactly twenty seconds later.

Collector: PID 13472, creation FILETIME `134346378912881531`, kernel sequence `66090`. Helper: PID 24896, creation FILETIME `134346378913229755`, kernel sequence `66091`, `C:\Windows\System32\conhost.exe`. Authority: PID 17612, creation FILETIME `134346378844472932`. Kernel session: `J6Kernel-{286BE78D-4461-4A40-A47A-7C0E39984E26}`.

| Measurement | QPC | Seconds from original cleanup entry |
|---|---:|---:|
| Authority OpenProcess begin | 4707003396505 | -0.6884551 |
| Authority OpenProcess return | 4707003396544 | -0.6884512 |
| Handle creation verification | 4707003396558 | -0.6884498 |
| Image verification complete | 4707003396965 | -0.6884091 |
| Obligations prepared | 4707012576262 | 0.2295206 |
| Handoff verification complete | 4707012930138 | 0.2649082 |
| Acquired receipt prepared | 4707012930414 | 0.2649358 |
| Collector observes receipt | 4707013219239 | 0.2938183 |
| Local pre-close | 4707013607603 | 0.3326547 |
| CloseHandle return | 4707013607743 | 0.3326687 |
| Phase A complete | 4707035797309 | 2.5516253 |
| Collector kernel STOP | 4707036136639 | 2.5855583 |
| Helper kernel STOP | 4707036152288 | 2.5871232 |
| Helper signal observed | 4707047981577 | 3.7700521 |

Publication-completed QPC was not separately persisted: UNKNOWN. Obligation publication is bounded by preparation and authority receipt preparation; acquired receipt publication is bounded by preparation and collector observation. No timestamp is fabricated. Hash bindings of all three receipts agree with the fresh run, workspace and obligation set. The independent final authority row agrees on exact creation, sequence, parent, image, handle identity and live image-query states. Collector and authority handles were distinct; no transfer occurred.

The requested signed `authority_verified_qpc - local_close_qpc` is **-677,465 ticks (-67.7465 ms)**. The positive verification lead is **67.7465 ms**; there is no observed late acquisition gap for this helper. The negative arithmetic sign means verification happened first.

No deadlock occurred in the acknowledgment path. Material timing equivalence to the historical run is not established by one rejected trial.

## Trace telemetry

| Measurement | Authority | Detailed |
|---|---:|---:|
| Final EventsLost | 2 | 31,239 |
| Sampled minimum FreeBuffers | 22 | 16 |
| Maximum NumberOfBuffers | 32 | 45 |
| Callback count | 49 | 1,817,538 |
| Maximum callback duration | 0.9196 ms | 409.9421 ms |
| Maximum sampled delivery lag | 2,389.8238 ms | 2,130.4104 ms |
| Writer queue high items | 2 | 20,584 |
| Writer queue high bytes | 870 | 6,810,377 |

Authority loss rose from 0 to 2 between counter observations QPC `4706993454849` and `4706994582238`. Detailed loss first rose by 14,043 between `4706991911227` and `4706992979642`, then by 17,196 by `4706994048487`. These observed increments precede cleanup entry and the handoff publication. They do not establish the underlying loss mechanism or exonerate every other interaction.

Detailed telemetry contains metadata/callback/guard spans around 410, 191 and 101 ms before those increments, with later writer flush/rotation pressure. Sampled free buffers did not reach zero; transient exhaustion between samples is neither proved nor excluded. Correlation is not a causal conclusion. Per-sample callback receive/completion rates, consumer CPU deltas, queue state and nearby spans are retained in `measurements.json` and raw diagnostics.

Writer queues ended with zero outstanding items/bytes. Authority persisted 20 selected records in two segments; detail completed 192,612 selected records in eight files. Persistence of delivered records cannot recover lost kernel events. A detailed counter sample at QPC `4707147217953` returned status 4201 with null counters near shutdown; it remains unavailable, not zero. The report extractor initially rejected this null comparison; that offline error and original extractor are preserved, then corrected only to report unavailable samples. No live code changed or reran.

Historical ETW loss cause remains **UNCONFIRMED**. The earlier zero-loss run remains comparison evidence only; previous failures and three disclosed legacy invocation errors retain their classifications. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

## Failure cleanup and preservation

The recorded rejection is QPC `4707037537407`; the underlying terminal-failure artifact has no timestamp. Do not claim complete first-failure ordering beyond the preserved records.

Failure-only observer shutdown completed at the launcher's final marker, **14.2864179 seconds** from cleanup entry. A zero-process/zero-trace preservation census completed at **17.2799677 seconds**, within the unchanged budget; eighteen recorded identities were absent. A later independent host census also found **zero matching processes and zero trace sessions**.

These are failure-cleanup observations. Successful terminal receipt, pre-shutdown workload census, ordered success shutdown proof, external-exit receipt and acceptance final census were not completed. Total successful acceptance-cleanup duration is therefore **NOT ESTABLISHED**, not 14.286 seconds. Eventual cleanup does not convert the rejected run into PASS.

The unchanged failure preserver reports `FAILURE_EVIDENCE_PARTIAL`: all **93 existing run files** were preserved and **95 ZIP members verified**, but six required terminal acceptance artifacts were never produced. No file was silently discarded, and no acceptance seal was generated. Original failure archive SHA-256: `0b74a1e0639fd2b8b7c1a94d914e423f5237cd937dea2c22aa16a68771784025`. Its manifest SHA-256: `68899c4fde3d754568569952de7065f1f786a988b4e03b3bfbee01c54e701b06`.

Canonical archival of this report plus original failure evidence is recorded separately in `archive-receipt.json`. A verified copy is not a success-finalization seal.

All **235 candidate files** and **334 predecessor/historical inputs** were reverified. Source-manifest SHA-256 remains `6a86a4f287388c8c58b3df4333792217b5205305f2157043a5a2ba5456c0b15b`; frozen checker remains `e6fbefd3fd463c6c8e09d0e8273a81b46ee2806515cae05e7837ea905a3e69d6`. Production JARVIS and protected VM/configuration were not accessed or modified. No medium/large/protected run occurred.

STOP for owner review. Proposed next action only: read-only review of this run's preserved trace-loss telemetry and incomplete terminal evidence. No correction, new run or configuration change is authorized by this result.
