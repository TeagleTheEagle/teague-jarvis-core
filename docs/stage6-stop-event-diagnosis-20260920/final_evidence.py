"""Produce diagnosis evidence and report. Never changes monitor behavior."""
import collections,datetime,hashlib,json,math,os,pathlib,shutil,statistics
from prepare import R,OLD,read,sha,write
def dist(xs):
 xs=sorted(xs);n=len(xs)
 return {'count':n,'median':statistics.median(xs) if n else None,'p95':xs[math.ceil(.95*n)-1] if n>=20 else None,'p99':xs[math.ceil(.99*n)-1] if n>=100 else None,'max':max(xs) if n else None,'min':min(xs) if n else None}
reports={run:read(R/run/'analysis.json') for run in ('smoke','repeat1','repeat2')}
combined=collections.defaultdict(list);correlations=[]
for run in ('repeat1','repeat2'):
 a=reports[run];f=read(R/run/'ready.json')['frequency'];resources=read(R/run/'resources.json')
 for row in a['rows']:
  for kind in ('start','stop'):
   v=row[kind];cb=v['callback'][0];q=v['enqueue'][0]
   base=int(row['creation_filetime'] if kind=='start' else row['kernel_exit_filetime'])
   combined[(kind,'kernel_lifecycle_to_notification')].append((int(cb['nativeTime'])-base)/1e7)
   combined[(kind,'notification_to_callback_tap_wall')].append(datetime.datetime.fromisoformat(cb['utc'].replace('Z','+00:00')).timestamp()-(int(cb['nativeTime'])/1e7-11644473600))
   combined[(kind,'callback_tap_to_enqueue_signed')].append((q['qpc']-cb['qpc'])/f)
   def stages(n):return [x for x in v['pipeline'] if x['stage']==n]
   if stages('drain'):combined[(kind,'queue_residence')].append((stages('drain')[0]['qpc']-q['qpc'])/f)
   for metric,left,right in [('drain_to_serialized','drain','serialized'),('serialization','serialize.begin','serialized'),('append','write.begin','persisted')]:
    if stages(left) and stages(right):combined[(kind,metric)].append((stages(right)[0]['qpc']-stages(left)[0]['qpc'])/f)
   if stages('persisted'):combined[(kind,'persisted_to_offline_reconciliation')].append((v['reconciliation_qpc']-stages('persisted')[0]['qpc'])/f)
   if not v['counts']['A_persisted_records']:
    nearest=sorted(resources,key=lambda s:abs(s['qpc']-q['qpc']))[:2]
    correlations.append({'run':run,'pid':row['pid'],'kind':kind,'phase':row['phase'],'enqueue':q,'nearest_resource_samples':nearest,
       'interpretation':'Nearby samples are correlation only; collisions also occur outside C reads.'})
metrics=[{'kind':k[0],'metric':k[1],'seconds':dist(v)} for k,v in combined.items()]
write('combined-latencies.json',metrics);write('loss-resource-correlation.json',correlations)
before=read(R/'original-inventory.json');after=[]
def fail(e):raise e
for base,dirs,files in os.walk(OLD,onerror=fail):
 for n in files:
  p=pathlib.Path(base)/n;s=p.stat();after.append({'path':str(p.relative_to(OLD)),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'sha256':sha(p)})
if before!=sorted(after,key=lambda r:r['path']):raise RuntimeError('Historical evidence changed')
for v in read(R/'source-hashes.json'):
 if sha(OLD/v['path'])!=v['sha256'] or sha(R/'source-snapshot'/v['path'])!=v['sha256']:raise RuntimeError('Original source changed')
if any(read(R/run/'monitor-config.json')['scriptHash'].lower()!=sha(R/'monitor.ps1') for run in reports):raise RuntimeError('Diagnostic source drift between runs')
shutil.copytree(OLD/'loads2',R/'historical-loads2')
copied=[]
for p in sorted((OLD/'loads2').iterdir()):
 if p.is_file():
  if sha(p)!=sha(R/'historical-loads2'/p.name):raise RuntimeError('Historical copy mismatch')
  copied.append({'name':p.name,'sha256':sha(p)})
write('preservation-final.json',{'original_files_unchanged':len(before),'original_source_files_unchanged':7,'diagnostic_monitor_same_hash_all_runs':sha(R/'monitor.ps1'),
 'historical_load_copy_verified':copied,'production_changed_by_task':False,'protected_VM_access_by_task':False,'normal_VirtualBox_configuration_access':False,
 'limitations':'No protected file hashes collected, as forbidden. Historical access cannot be reconstructed from this task.'})
text='''# Stage 6 process STOP-event loss diagnosis — 2026-09-20

**FINAL STATUS: STRONG_CAUSAL_EVIDENCE**

Reproduced mechanism: **QUEUE_DRAIN_LOSS — duplicate PowerShell EventIdentifier values cause removal of a different queued event before it can be drained.** This mechanism is identified in two new instrumented campaigns and confirmed with a direct synthetic removal test. The original three losses lack queue identifiers and cannot be conclusively assigned this cause retrospectively. They are compatible with the reproduced mechanism, not individually proven.

**PROTECTED BASELINE ELIGIBILITY: NOT JUSTIFIED.** No correction, sacrificial acceptance dry run or protected hashing was performed.

1. **Three historical identities** (creation FILETIME, retained-handle record):

| PID | Creation FILETIME | Creation UTC | Recorded successful wait to collection freeze |
|---:|---|---|---:|
'''
historical=read(R/'historical-missing-identities.json')
for x in historical:text+=f"| {x['probe']['pid']} | {x['probe']['created']} | {x['created_utc']} | {x['seconds_wait_to_collection_freeze']:.6f} s |\n"
text+='''
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
'''
for run,a in reports.items():
 for p in a['phases']:
  c=p['counts']['stop']
  text+=f"| {run} / {p['phase']['mode']} | {p['expected_exits']}/{p['handle_exits']} | {c['A_callback']} | {c['A_enqueued']} | {c['A_drained']} | {c['A_serialized']} | {c['A_write_completed']} | {c['A_persisted_records']} | {c['A_reconciled']} | {c['B_WMI_callback']} |\n"
text+='''
Two full repetitions: **302 probes, 302 handle-confirmed exits, 302 START callbacks/enqueues, 301 STARTs persisted; 302 STOP callbacks/enqueues, 287 STOPs persisted.** Smoke: four probes, all four STARTs/STOPS captured at all stages. Campaigns use approximately one-second nominal probe spacing versus historical five-second spacing; synchronous evidence/storage activity reduced the achieved rate. Every phase records actual duration, process identity and input path. Instrumentation/parallel observer perturb timing; these are diagnostic results, not acceptance passes.

Dual observer: A persisted STOP and B COM STOP both present for 287/302; only B for 15; only A zero; neither zero. Kernel handles independently confirmed all 302 exits. B is a separate subscriber/transport to the **same WMI provider**, not an independent ETW provider. Independent kernel wait/GetProcessTimes is a different lifecycle mechanism but does not claim to capture notifications. No additional ETW package or broad system trace was installed/launched because the existing observations already localized loss downstream of receipt.

10. **Finalization race:** none of the reproduced lost events was pending at teardown, and every one was already queued before sibling removal. Events can arrive after collector-finished within the existing grace; those observed events were captured. No observed callback/enqueue arrived after collection.freeze. The original final-drain → freeze → unsubscribe interval can theoretically discard a late queued event (the original finally clears it), but that mechanism did not explain the reproduced losses. Original missing exits were 285–383 seconds before freeze; an ordinary two-second shutdown tail is insufficient to explain those records without unsupported extreme delay. No grace added.

11. **Queue integrity:** both runs had zero hook errors/trace overflows, no observed same-source ID duplicates and no pending/discarded events at teardown. ReceivedEvents is the existing PowerShell collection; no capacity/overwrite setting changed. Native dropped-event counters are not exposed. Installed PowerShell reports 7.6.5; System.Management.Automation assembly version 7.6.0.500, SHA-256 `2d8af026e589c5603629bfc3e7c57265b4167b12eca3ae549c6a6c3ca7e4967b`. Read-only IL inspection shows GetNextEventId incrementing `_nextEventId` without an interlocked operation in that method. Real concurrent START/STOP notifications received the same ID. `queue-mechanism-proof.json` independently confirms that removing one numeric ID removes both synthetic queued events. No installed assembly was changed. Queue occupancy/sequence/thread observations and teardown state are preserved in tap/pipeline/loop traces.

12. **Latency distributions**, both full campaigns combined, seconds. p95 uses nearest rank with at least 20 samples; p99 requires at least 100. Metrics involving missing drain records exclude those records and show their sample counts. Callback-to-enqueue is signed because handler ordering can put the callback tap after enqueue. FILETIME-to-wall measurements are separate from QPC pipeline measurements; wall adjustments could affect those cross-clock estimates.

| Kind | Metric | Samples | Median s | p95 s | p99 s | Max s |
|---|---|---:|---:|---:|---:|---:|
'''
for m in metrics:
 v=m['seconds'];fmt=lambda n:'unavailable' if n is None else f'{n:.6f}'
 text+=f"| {m['kind']} | {m['metric']} | {v['count']} | {fmt(v['median'])} | {fmt(v['p95'])} | {fmt(v['p99'])} | {fmt(v['max'])} |\n"
text+='''
Offline reconciliation latency includes the intentional delay before analysis; it is not a provider-performance claim. Full per-phase distributions are in each analysis.json. The first run contained a STOP callback-to-enqueue interval of 18.965166 seconds, eventually persisted. That is a separate scheduling/queue-processing delay whose internal cause was not established. Maximum observed heartbeat ages: repeat1 8.7602586 s; repeat2 6.566074 s; ten-second threshold unchanged. No new stale-heartbeat failure occurred.

13. **C: read correlation:** original three losses were all under C: reads. New losses occurred under idle, C: reads, C: hashing, CPU and D: hashing; this disproves a claim that C: pressure is necessary in the observed mechanism. Resource counters (disk active/idle, queue depth, read/write latency, throughput, CPU), callback/queue/write timing and nearest samples for each loss are saved in analysis.json / loss-resource-correlation.json. Storage pressure coincided with multi-second queue/append delays, but no causal disk explanation is asserted. The immediate loss mechanism is ID-based sibling removal.

14. **Strongest supported category:** QUEUE_DRAIN_LOSS for the reproduced cases. All 16 missing events map one-for-one to 16 collisions; 11 in repeat1, five in repeat2. Historical individual attribution remains INCONCLUSIVE. Overall final disposition is STRONG_CAUSAL_EVIDENCE rather than a claim to have reconstructed every historical loss.

15. **Proposed minimum correction:** remove only the exact successfully processed PSEventArgs object under ReceivedEvents.SyncRoot; verify owned subscription and reference identity, fail closed if absent/mismatched. Do not hold the lock across serialization or disk I/O. Do not remove by numeric EventIdentifier alone, clear the queue/subscription or modify PowerShell/runtime DLLs. No correction is implemented. `CORRECTION-PROPOSAL.md` identifies validation-only candidate monitor/helper/tests and the scope boundary.

16. **Residual uncertainty:** the exact old losses cannot be traced past the historical gap. Instrumentation affects timing. Native buffering/drop counters and independent ETW emission tracing are unavailable in this campaign. PowerShell event collection can still suffer scheduling delays; fixing removal would not prove timing acceptance. No host power-loss or storage-hardware durability guarantee was tested. Historical 13.7 s / 14.084 s causes remain UNCONFIRMED; only synchronous Flush(true) causing experimentally measured >10 s stalls is supported. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

17. **Exact revalidation plan:** after reviewed correction, run prior focused tests plus exact-object removal/collision/concurrent-arrival/write-failure/unrelated-event tests; repeat all five workloads with complete real START/STOP evidence, retained identities and unchanged ten-second threshold; repeat all failure injections; require durable finalization and hash-verified archive; independently run Dry Run #1 then #2 only after load gates pass; verify cleanup and unchanged protected/production boundaries. Full plan/rollback in CORRECTION-PROPOSAL.md. No wait/grace increase or acceptance substitution.

18. **Protected baseline eligibility: NOT JUSTIFIED.** No protected VM or normal VirtualBox configuration opened/hashed; no VirtualBox launched; no production JARVIS changed; no settings/ACL/execution-policy changes. Diagnostic monitors used the authorized read-only elevated subscriptions; probes/workloads ran non-elevated on fixed sacrificial inputs. All run records remain explicitly unaccepted. No correction/acceptance commit.

19. **Evidence paths:** this directory; raw `smoke/`, `repeat1/`, `repeat2/`; `historical-loads2/` (hash-verified copy); `original-inventory.json`, `historical-missing-identities.json`, source-snapshot, EventTap.cs, instrumented monitor.ps1, collect.py, launch.ps1, analyze.py, collisions.py, synthetic proof script/result, full latency/correlation output, source hashes and preservation-final.json. The original 352 files and seven source snapshots are unchanged; all diagnostic monitor script hashes match across the three runs. No original failed evidence is overwritten.

20. **Archive:** `C:\\Users\\jonny\\OneDrive\\Desktop\\TEAGUE INDUSTRIES DATABASE\\06 SOURCE RECORDS\\STAGE6 STOP EVENT DIAGNOSIS 20260920`. Archive receipt records exact ZIP member count, full member SHA-256 verification and copied-file hash checks. This is a diagnosis/failure-evidence archive, not MONITOR_VALIDATED acceptance. Rollback is to stop using diagnostic copies while retaining all evidence; no production rollback necessary.

Documentation distinction:
- Observed source: original monitor.ps1 lines 13–29 (Drain/append/ID removal), 35–36 (CIM subscriptions), 58–67 (final drain/freeze/unsubscribe); original campaign.py lines 25–29 (retained process handles); original finalize.py line 38 (exact event count rejection).
- Microsoft documents that local CIM subscriptions use COM and queued events without Action: https://learn.microsoft.com/en-us/powershell/module/cimcmdlets/register-cimindicationevent?view=powershell-7.5
- ProcessStopTrace indicates termination and TIME_CREATED is event generation time, not independently retrieved process-exit time: https://learn.microsoft.com/en-us/previous-versions/windows/desktop/krnlprov/win32-processstoptrace
- Process handles signal at exit and remain valid while retained: https://learn.microsoft.com/en-us/windows/win32/procthread/terminating-a-process
- WMI documents dropped/overflow events, including permanent-consumer context; absence of such a record is not proof against temporary-subscriber loss: https://learn.microsoft.com/en-us/windows/win32/wmisdk/--eventdroppedevent and https://learn.microsoft.com/en-us/windows/win32/wmisdk/--eventqueueoverflowevent
- PowerShell reference source explains queue addition/removal and counter allocation: https://raw.githubusercontent.com/PowerShell/PowerShell/v7.5.3/src/System.Management.Automation/engine/EventManager.cs . Installed-version behavior was tested/inspected independently rather than assuming this older source exactly matches it.
'''
with (R/'REPORT.md').open('x',encoding='utf-8') as f:f.write(text)
print(json.dumps({'original_unchanged':len(before),'historical_copy_files':len(copied),'report':'REPORT.md','classification':'STRONG_CAUSAL_EVIDENCE','cause':'QUEUE_DRAIN_LOSS','protected_baseline':'NOT JUSTIFIED'}))
