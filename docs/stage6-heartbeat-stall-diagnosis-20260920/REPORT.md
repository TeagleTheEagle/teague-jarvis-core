# C: hashing heartbeat stall diagnosis

**Final status: BLOCKED**

Windows canceled the elevated read-only monitor launch (`Start-Process -Verb RunAs`: “The operation was canceled by the user.”). The smoke directory contains only its case configuration: no monitor identity, heartbeat, probes or load generator were created. No elevation retry was attempted. Controlled A/B testing and three reproductions therefore remain NOT RUN. The original stall is not resolved.

1. **Exact timeline:** `historical-interval.json` and CURRENT-SOURCE-AUDIT.md contain T0–T6 with exact monotonic ticks. Heartbeat record interval is 14.5649514s; publication-marker interval is 14.5650069s. Record UTC timestamps are 2026-09-20T00:22:26.6465441Z and 00:22:41.2114958Z. Individual file-call entry/completion timestamps were not captured historically.
2. **Current heartbeat path:** synchronous event drain → record construction → FileStream.Length → Write → Flush(false) → finish-file query → Wait-Event. Flush(true), close and final enumeration occur after the live loop. No rotation, live archive writing or live evidence hashing. Exact symbols appear in CURRENT-SOURCE-AUDIT.md.
3. **Longest owning region:** the historical interval lies in event draining. Two broad spans are 7.6266274s after event serialization/before append and 6.1961153s around append/validation/removal. Neither isolates a single system call.
4. **Scheduling gap:** historical wait span around this interval was approximately 0.737s. Kernel scheduling delay is NOT MEASURED. Collector sampling also stalled, with maximum observed sampling gap 12.8034676s across the broader workload. That is not proof of CPU starvation.
5. **Journal I/O:** no multi-second heartbeat-journal operation is identified as the owner of this historical gap; the delayed span precedes record creation. Individual event-file I/O remains unresolved. New call timing has been prepared but not exercised by a live monitor.
6. **Event drain:** corrected candidate preserved all 279 STARTs/279 STOPs in the preceding failed acceptance run, including three external-ID collisions; its heartbeat failure remains distinct. No new process-event run occurred in this pass.
7. **Telemetry:** performance counters/Get-Process run in a separate process. Historical overlapping collection windows span approximately 10.221s and 7.318s. Live trace is memory-buffered; event evidence and finish checks are synchronous filesystem operations. Full/minimal observer comparison NOT RUN.
8. **CPU:** two overlapping historical samples report aggregate utilization 0–6.464%. Monitor CPU time rose 0.046875s and worker CPU time 0.109375s across sampled snapshots. These coarse observations do not prove scheduler starvation or exclude a pause. Native-thread CPU/GC diagnostic hooks are prepared, not measured in a live run.
9. **Storage:** overlapping historical C: samples report idle 0–7.565%, queue depth 1–15, average write latency 5.409–264.912ms and read throughput up to 103.72MB/s. D: was about 99.54–99.95% idle; available memory approximately 21,458–21,565MiB. Correlation only; no storage-driver cause established.
10. **A/B comparisons:** A, B, C, D, E, F all NOT RUN. Planned cases are serial 150s runs with only the specified source workload/journal location varying. Event evidence remains on C: to avoid confounding a journal-only comparison.
11. **Three C: reproductions:** NOT RUN. The canceled launch is not a reproduction failure and not a monitor runtime defect.
12. **Strongest supported cause category:** INCONCLUSIVE. Historical missing time is localized to the event-drain region, but synchronous I/O, lock contention, runtime pause and scheduler delay have not been separated.
13. **Minimum correction:** NONE SELECTED OR IMPLEMENTED. Do not move files, raise priority, change timeouts or redesign event collection from correlation alone. Complete approved diagnosis first.
14. **Residual uncertainty:** exact blocked call, native storage/driver cause, thread starvation, GC pause and observer contribution remain unknown. Historical 13.7s/14.084s delays remain separate and UNCONFIRMED. Original missing PIDs 13248/22544/21896 remain individually UNPROVEN. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
15. **EventIdentifier-fix regression:** timing-instrumented helper passed the existing 222 assertions and 10,000-event collision stress, twice; live-session reference-removal proof also passed. No loss, duplication, sibling deletion or queue identity collision. The second run exercised final timing source including sampling-overhead timestamps. Corrected original source remains unchanged; no queue redesign was made.
16. **Protected VM access:** NONE. No protected hashing, VM/configuration inspection, VirtualBox launch or dry run.
17. **Production changes:** NONE. Changes are fresh validation-only diagnostic copies, timing/analysis scripts and evidence. Exact hashes/diffs are in source-before.json, source-final.json and instrumentation.diff.
18. **Protected-baseline eligibility:** NOT JUSTIFIED.
19. **Evidence:** this directory preserves source snapshots, historical reconstruction, diagnostic preparation, two collision-regression runs, the canceled launch and the premature-analysis error. That analysis attempt failed because heartbeat.jsonl did not exist and wrote no result; it did not alter the monitor.
20. **Archive:** final receipt `archive-verification.json` records hash verification of the complete nonsecret archive in TEAGUE INDUSTRIES DATABASE. This is a blocked-diagnosis archive, not monitor acceptance.

## Next action and rollback

Owner action is required before a fresh elevated smoke launch: confirm readiness to approve the Windows UAC prompt. Do not reuse or overwrite the canceled `smoke` run. No monitor is currently running from that attempt. The complete approved diagnostic continuation and future acceptance sequence are in REVALIDATION-PLAN.md. Do not start protected hashing.

Rollback consists of not using this diagnostic copy; all preceding source/evidence is retained. There is no production, VM, security setting or permission change to roll back. Prior-source preservation verification is recorded in preservation-final.json.
