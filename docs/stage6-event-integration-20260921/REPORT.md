# Stage6 authoritative stream and instance identity integration

**CAPACITY_ARCHITECTURE_STILL_DEFECTIVE**

The new TEST candidate removes the checker’s bounded-tap read dependency and preserves required callback evidence in a complete segmented application stream. Focused path/queue/integrity tests passed. Two offered-load tests failed at the bounded queue item limit; positive independent CIM instance correlation is also unresolved. This is unaccepted partial integration, not a production or frozen-baseline change.

## Mandatory findings

1. **pre-integration hash verification:** PASS:116 frozen hashes plus6 prior evidence checks, restored host-state hash,143/8/42-member archives fully verified;1078/155-member archive hashes unchanged. Fresh exclusive host preflight passed.

2. **actual dataflow map:** DATAFLOW.md maps exact files/classes/functions, buffers, source identities and acceptance dependencies before integration. ETW/native and CIM are parallel independent observations, not one source synthesized from another.

3. **authoritative evidence definition:** New application-authority stream preserves callback/enqueue records plus persistence event/receipt envelopes. Existing raw mirrors must agree. Kernel/native/source-loss/heartbeat/probe evidence remains mandatory; none was demoted.

4. **secondary tap definition:** EventTap.Snapshot remains capped at20,000 first rows, now a secondary view in the new candidate only. Truncated count explicit. Frozen accepted code unchanged.

5. **exact 20,000-row behavior:** Old EventTap.Add drops NEW rows after20,000 and increments Overflow. Old ExactEventQueue also caps cumulative enqueue identities at20,000. New view increments Truncated only after authoritative admission; streaming queue bounds outstanding references and releases completed references.

6. **canonical process-instance identity:** Kernel-instance table key:boot/run scope+PID+CreateTime+kernel ProcessSequenceNumber; exact parent sequence. This identifies known kernel instances but does NOT supply a missing creation discriminator in a delayed independent CIM event.

7. **identity source:** Inspected existing kernel payload, retained-handle creation and native PE evidence. Official CIM START/STOP schemas do not expose process CreateTime/sequence. No new Windows identity API experiment or live CIM session in this pass.

8. **active process table design:** New process_instances.InstanceTable retains all supplied completed/live-history rows until reconciliation, validates creation/sequence uniqueness, parent identity, handle creation and native-entry ordering. Delayed observations never discard earlier compatible incarnations. Currently post-capture table; no claim of validated live enrichment service.

9. **application enrichment rule:** Raw preserved unchanged; separate candidates/selected/result/reason. Missing independently event-bound discriminator always remains AMBIGUOUS if compatible candidates exist, otherwise UNMATCHED. Caller-supplied creation fields/current PID lookup do not force selection. This is a safe rejection boundary, NOT a completed positive unique-match implementation.

10. **historical 22-event status:** Historical21 AMBIGUOUS/1 UNMATCHED unchanged. No historical raw data or report rewritten.

11. **identity tests:** 24 synthetic adversarial safety cases PASS after one preserved transitional creation-collision failure was corrected. Positive unique CIM acceptance NOT SATISFIED. These are not24 positive integration acceptance passes.

12. **false unique matches:** 0 false unique matches in the synthetic safety matrix; achieved with explicit ambiguity rejection. Real fresh PID-reuse/independent-source correlation not demonstrated.

13. **PID reuse result:** Synthetic reuse,rapid reuse,parent reuse,identical names,delayed/out-of-order cases tested. Actual Windows PID reuse NOT RUN; no synthetic identity claimed as real evidence.

14. **authoritative sequence design:** Application stream sequence assigned under ingestion lock; envelope has source,eventType,rawTimestamp,QPC,segment,serialized flag,raw payload and unresolved identity state. Canonical enrichment remains separately recorded. Sequence is global across application callback/enqueue/persistence channels only. Cross-provider single global sequence is not integrated; kernel trace remains its existing independent stream.

15. **segment design:** CREATE_NEW flat D: app-authority-NNNNN.jsonl segments,8MiB each,max16,384; SHA256 and first/last/count/bytes; manifest exclusively created. No rotation or overwrite. Finite record/storage budgets retained as provisional ceilings.

16. **segment integrity:** 36,000-record complete case verified:3 segments,17,406,246 bytes,zero sequence gaps. Failed prefixes independently hashed/checked but remain failed runs.16 focused integrity/wiring/syntax assertions PASS, including11 deliberate failure cases.

17. **queue design:** New C# queue bounded by64MiB payload AND65,536 items; one writer; publication lock excludes filesystem operations. One writer in-flight item adds at most8192 bytes. Managed-object/string overhead is not claimed as a measured total RSS bound. Checker materialization separately fails above64MiB serialized input.

18. **queue capacity derivation:** NOT SUFFICIENTLY JUSTIFIED.64MiB retains prototype payload ceiling;65,536 items adds a finite object bound, but measurements prove it is too small for tested producer/writer mismatch. No blind capacity increase performed. A finite ceiling is not proof of sufficient sustainable throughput.

19. **large-record result:** FAIL preserved. Large-record case:108,167 attempted,108,166 admitted/persisted,one rejected admission,13 segments,106,569,009 bytes. Queue reached65,536 items/64,627,793 bytes. No rerun or threshold change.

20. **backpressure result:** Observed item-bound exhaustion failed closed in both actual EventTap component loads; all admitted records drained and manifests remain faulted. Reader rejects corrupt/missing/reordered/duplicate/partial/gapped/bad-hash manifests. Full writer-delay/disk-full/ETW-loss injection campaign NOT RUN; a static existing ETW-loss gate check is not live ETW-loss injection.

21. **tap truncation result:** PASS COMPONENT:24,000 callback/enqueue records +12,000 persistence records; bounded view20,000,explicit truncation4000; complete authoritative reader uses24,000 callback records. No actual lifecycle PASS inferred from generated inputs.

22. **integrated high-rate result:** FAIL. Actual modified EventTap.Add/Persisted/sink exercised; normal-size offered164,951.103 records/sec but queue filled. No full Windows/ETW/PowerShell drain/heartbeat integrated acceptance was performed. Standalone prior prototype success is not substituted.

23. **producer rate:** Normal-size164,951.103 records/sec over0.5027308s to failure; larger records86,695.355/s over1.2476447s. Small complete case159,247.362/s over0.2260634s; short burst only.

24. **consumer rate:** End-to-end persisted rate including finalization:normal-size68,536.801 records/sec;larger26,461.975/s. Neither establishes sustainable100,080/s.

25. **queue high-water:** Both failed cases reached65,536 items. Normal31,807,662 bytes;large64,627,793 bytes. Neither reached the64MiB byte cap first. Queue occupancy returned0 after close.

26. **trace-loss count:** Fresh ETW loss NOT MEASURED; no ETW session. Each capacity failure has exactlyone rejected admission and therefore is incomplete despite admitted/persisted equality. No silent PASS.

27. **sequence-gap count:** Complete36,000-record case0. Failed persisted prefixes are contiguous but each rejected an attempted record; prefix integrity does not make full runs complete.

28. **medium validation:** NOT RUN. Required positive independent identity and sustainable capacity prerequisites failed. No UAC observers or native hash workers started.

29. **medium duration:** NOT MEASURED.

30. **authoritative record count:** No integrated medium record count. Generated complete component case36,000; two failed prefixes82,926 and108,166.

31. **average rate:** No integrated medium average.

32. **peak rate:** No integrated medium peak; generated component producer rates are separately labelled above.

33. **record-size distribution:** No accepted integrated distribution. Failed prefix average wire sizes approximately484.73 bytes(normal),985.23 bytes(large); exact distributions in failed-record-sizes.json. These include envelopes and differ from the old prototype.

34. **max record size:** See failed-record-sizes.json; no integrated medium maximum established.

35. **segment count:** Component segments:3 complete;5 normal-size failed;13 larger-record failed.

36. **rollover max:** Maximum measured combined flush/close/hash-finalize/manifest-metadata rollover:0.4644371s normal,0.3576777s large. Individual flush versus hash costs were not isolated; no Windows/storage cause asserted.

37. **heartbeat max:** NOT MEASURED in new full observer; unchanged10s threshold. Generated stream tests have no monitor heartbeat acceptance.

38. **deadline violations:** No real lifecycle probes/deadline acceptance run. Existing13.6s/15s values unchanged. Test writer join uses a separate bounded5s close; all tested writers exited.

39. **START/STOP reconciliation:** NOT RUN for actual Windows processes. Concrete queue regression222 assertions/14 groups incl10,000-event collision stress PASS;100 new streaming-mode entries persisted/removed with no remaining references. External collisions9993;internal collisions0. Does not replace process START/STOP proof.

40. **native PE-entry result:** NOT RUN; native code/executables unchanged. Candidate launcher still references old frozen source expectations and is explicitly not ready to launch.

41. **sampler result:** NOT RUN; sampler code unchanged.

42. **finalization result:** App sink manifests generated exclusively,verified; finalizer wired to include authoritative summary and identity enrichment. Full baseline finalizer has NOT passed and cannot pass missing identity/capacity. No successful baseline manifest sealed.

43. **cleanup result:** All subprocess invocations returned; writer manifests report exited and queue0. Final exclusive host check:0 matching diagnostic/VirtualBox processes,0 trace sessions. No unrelated process termination. These component drivers did not record a new per-process creation-time ledger; no claim of full medium retained-handle proof.

44. **archive verification:** Old143/8/42-member archives fully verified before work;all five recorded historical archive hashes remain unchanged. New archive receipt records exact member count/hash after finalization. Both capacity failures and transitional identity failure are included.

45. **expected large-run duration:** No new accepted projection. Prior calibration only:59,665,402,098 bytes/pass,262.4176685s and261.0306052s. Not rerun; no actual large-run duration predicted from failed integration.

46. **conservative duration:** UNVALIDATED; inventory/finalization/observer-wide duration bound not measured here.

47. **expected large-run records:** UNVALIDATED: no passing integrated medium rate.

48. **upper-bound records:** UNVALIDATED. Configured fail-closed ceilings are not demand predictions.

49. **expected segment count:** UNVALIDATED.

50. **upper-bound segment count:** UNVALIDATED for complete run;application stream hard maximum16,384 segments only.

51. **expected trace storage:** UNVALIDATED.

52. **upper-bound trace storage:** UNVALIDATED for all channels. Application128GiB ceiling alone is not complete storage budget.

53. **queue requirement:** UNVALIDATED; existing tested item cap exhausted. Need measured producer burst/consumer deficit model; no arbitrary increase.

54. **D: required reserve:** NOT ESTABLISHED from passing actual integrated evidence.

55. **D: free space:** 1,794,853,462,016 bytes at final measurement.

56. **D: headroom:** UNVALIDATED because required reserve not accepted; free capacity alone insufficient.

57. **safety margin:** No sufficient numerical margin established. Observed writer rates/rollover variability and source-identity gaps preclude large-run readiness.

58. **frozen candidate hash result:** PASS116 frozen candidate hashes+6 additional checks unchanged; restored host hash unchanged. New candidate has5 modified inherited files,3 new core modules and focused test helpers; before/after hashes recorded. No accepted source revision changed.

59. **protected VM access result:** NOT ACCESSED. No protected VM/configuration reads,hashing,VirtualBox command,boot or snapshot operation.

60. **production-change result:** UNCHANGED. No production code/configuration/credential/provider operation.

61. **historical-cause status:** Historical delay causes remain UNCONFIRMED. HISTORICAL STAGE1 CAUSE: UNCONFIRMED. New queue item-bound failures are established only for these generated-load runs.

62. **large-run eligibility:** NOT ELIGIBLE. No medium or59.7GB run; no protected baseline procedure approved by this result.

63. **final status:** CAPACITY_ARCHITECTURE_STILL_DEFECTIVE

## Root cause and exact limitations

The generated normal-size load admitted82,926 records and then rejected attempt82,927 at65,536 pending items. Its peak payload was31,807,662 bytes, below67,108,864; storage/record/segment/record-size ceilings were not exhausted. The larger case similarly filled65,536 pending items. This establishes the immediate admission failure mechanism. The offered load exceeded completed writer throughput. Rollover timing groups flush,close and hashing; it does not establish which Windows/storage/driver operation caused latency. No queue increase,deadline adjustment,retry or failure relabelling was used.

The current CIM schema contains process ID and event generation time, but no subject creation key. Supported retained-handle/kernel keys identify process instances; they do not automatically bind delayed CIM messages to those instances. See Microsoft’s [START schema](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/krnlprov/win32-processstarttrace) and [STOP schema](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/krnlprov/win32-processstoptrace). The new table therefore fails closed even with one compatible candidate when independent event-instance proof is absent. This intentionally exposes the missing positive capability; it must not be marketed as solved identity integration.

## Files and rollback

New candidate: `D:\JARVIS-STAGE6-LIVE\6d305fb9fc7440c5bf485466e9d708df\code`.

- `baseline_finalize.py`: `9cbcd528310e7cbbafbfbdb41e0e19f302fdb62f3ba12d040ea9dacad8a4f3f5` → `c06fbafc9b57b4202cd0bcd3c1a41c7dcc9f93806424bbe23f7489df8be6128d`
- `cleanup_checker.py`: `ae1f6cc045f9a9b943edf1904bf097c8f9540e3255a97df6e9c02f378eb3ccfd` → `e6fbefd3fd463c6c8e09d0e8273a81b46ee2806515cae05e7837ea905a3e69d6`
- `event_queue.cs`: `0d7f17be44e892a093c5babf95e84f1a3089b3e819cef716353da620b11703a3` → `e3ceb863925632fdfaf3d595e6ff1a54511e5b15268f7570ec7b1da5f4f80c01`
- `EventTap.cs`: `f6f6eb3ac2597b843d894b61463f10e22af5adf56912b16e7c3d77b7f8ba1b36` → `7763c6fe724000a77a33902205e3cca576124359d9a2f4d6305bf2ddc2106737`
- `timed_monitor.ps1`: `15d7bcadd1aa60e990381fb6f9cc0779e11afb2c3c2278d0af7267a3b89973ae` → `55ae883301dfdd777a1c86b9be922c837766101e62fdd3bf1bfe2507dc01720b`

Added integration modules:AuthoritativeEvents.cs,application_authority.py,process_instances.py. Before copies,diffs and added/helper hashes are recorded in candidate-hashes.json and the archive manifest. New preflight/report writers use exclusive creation. Only fresh run-scoped active JSONL/health files and deliberate corruption fixtures are mutable. Legacy historical scripts were not executed. The initial prefixed preparation copy was never used because existing containment requires32hex; a separate correctly named copy was created without weakening containment.

Rollback:leave the unaccepted copy unpromoted. The original116-file source remains unchanged and hash-verified. Do not delete failed evidence or overwrite restored historical records. The copied old launcher/source manifest has not been regenerated; do not use it. A DO-NOT-LAUNCH-INCOMPLETE notice records this. No install or commit exists to undo.

## Tests and commands

New scripts invoked bundled Python with -B and existing PowerShell7.6.5 -NoProfile -NonInteractive, without policy changes or UAC observers. Exact command arrays/results:tap-load-command.json,high-rate-result.json,large-record-result.json,queue-regression-command.json. identity_tests.py and stream_integrity_tests.py record24 safety cases and16 verifier/static/syntax checks. Three modified/new PowerShell scripts parsed successfully. A transitional duplicate creation-identity test failure and its narrow rejection correction are permanently preserved.

## Remaining work for review

1. Diagnose writer/rollover throughput with separated timing and derive a defensible finite item/payload budget; do not merely enlarge the queue.
2. Establish an independently event-bound discriminator or review a different independent event source. A new ETW subscription alone is not a new underlying event source; do not silently demote CIM evidence.
3. Complete positive identity correlation,full actual queue/observer stress and all-channel resource/finalization contracts;then prepare a new safe launcher and source manifest.
4. Only after those prerequisites pass, run medium sacrificial validation. No large-run command is ready for execution.

## Evidence

- [DATAFLOW.md](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-event-integration-20260921/DATAFLOW.md)
- [plan.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-event-integration-20260921/plan.json)
- [active-workspace.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-event-integration-20260921/active-workspace.json)
- [integration-changes-step1.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-event-integration-20260921/integration-changes-step1.json)
- [integration-changes-step2.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-event-integration-20260921/integration-changes-step2.json)
- [identity-matrix.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-event-integration-20260921/identity-matrix.json)
- [identity-transitional-failure.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-event-integration-20260921/identity-transitional-failure.json)
- [tap-integration-focused.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-event-integration-20260921/tap-integration-focused.json)
- [capacity-results.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-event-integration-20260921/capacity-results.json)
- [failed-prefix-verification.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-event-integration-20260921/failed-prefix-verification.json)
- [failed-record-sizes.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-event-integration-20260921/failed-record-sizes.json)
- [stream-integrity-result.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-event-integration-20260921/stream-integrity-result.json)
- [queue-regression-result.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-event-integration-20260921/queue-regression-result.json)
- [candidate-hashes.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-event-integration-20260921/candidate-hashes.json)
- [final-preservation.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-event-integration-20260921/final-preservation.json)

Archive verification is recorded in a separate exclusive receipt after copying and checking every member. No integration success or future authorization is implied by archival success.
