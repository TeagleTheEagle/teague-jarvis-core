"""Render measured diagnostic results; does not run workloads or change any monitor."""
import pathlib,json,hashlib,datetime
R=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def put(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
rows=read(R/'campaign-summary.json');by={r['run']:r for r in rows};supp={r['run']:r for r in read(R/'supplemental-campaign.json')}
old=read(R.parent/'stage6-heartbeat-stall-diagnosis-20260920'/'preserved-before.json');changes=[]
allowed=(R.parent/'stage6-eventidentity-fix-20260920').resolve()
for row in old:
 p=pathlib.Path(row['path']).resolve()
 if not p.is_relative_to(allowed):raise RuntimeError('Historical evidence path outside allowed diagnostic root')
 st=p.stat()
 if hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256'] or st.st_size!=row['bytes'] or st.st_mtime_ns!=row['mtime_ns']:changes.append(str(p))
put(R/'historical-424-preservation.json',dict(files=len(old),changes=changes,status='PASS' if not changes else 'FAIL',protectedVMAccess=False))
if changes:raise RuntimeError('Historical evidence mutation')
smoke=read(R/'smoke'/'monitor-exit.json');smokehandles=read(R/'smoke'/'retained-handle-verification.json')
assert smoke['exit_code']==0 and len(smokehandles)==5 and all(int(x['times'][1])>int(x['times'][0]) for x in smokehandles)
put(R/'smoke-cleanup-reconciliation.json',dict(monitor=smoke,probes=5,kernelExitsConfirmed=5,method='Existing retained-handle exit evidence; smoke was idle and created no hashing worker',status='PASS'))
def table(headers,rs):return '| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+''.join('| '+' | '.join(str(v) for v in r)+' |\n' for r in rs)
def f(v):return 'unavailable' if v is None else f'{v:.6f}'
ab=table(['Run','Diagnostic result','HB interval s','Max successful poll age s','Drain s','Longest substage','START / STOP'],[[r['run'],'PASS' if r['status'].startswith('PASS') else 'FAIL',f(r['interval']),f(r['age']),f(r['drain']),read(R/r['run']/'event-analysis.json')['longestIndividualSubstage']['stage'],f"{r['starts']} / {r['stops']}"] for r in rows])
timings=table(['Run','Lock wait s','Lock hold s','AppendAllText s','Test-Path s','Get-Item.Length s','Event metadata s','Largest batch / depth'],[[r['run'],f(r['lockWait']),f(r['lockHold']),f(r['write']),f(r['exists']),f(r['stat']),f(r['eventMetadata']),f"{r['maxBatch']} / {r['maxDepth']}"] for r in rows])
def counter(r,section,contains,suffix,stat):
 vals=[v[stat] for k,v in r[section].items() if contains in k and k.endswith(suffix)]
 return vals[0] if vals else None
storage=table(['Run','C queue max','C read latency max s','C write latency max s','Mean total CPU %','CPU max %','Telemetry samples'],[[r['run'],f(counter(r,'storage','(1 c:)','current disk queue length','max')),f(counter(r,'storage','(1 c:)','avg. disk sec/read','max')),f(counter(r,'storage','(1 c:)','avg. disk sec/write','max')),f(counter(r,'cpu','processor(_total)','% processor time','mean')),f(counter(r,'cpu','processor(_total)','% processor time','max')),next((v['samples'] for k,v in r['cpu'].items() if 'processor(_total)' in k),'unavailable')] for r in rows])
schedule=table(['Run','Max event s','Max queue residence s','Drain-start gap s','Producer callback gap s','Observer sleep excess s','GC pause total s'],[[r['run'],f(r['maxEvent']),f(supp[r['run']]['maximumEnqueueToProcessingSeconds']),f(supp[r['run']]['maximumConsumerDrainStartGap']),f(supp[r['run']]['maximumProducerCallbackInterarrival']),f(r['observerJitter']),f(r['gcPauseSeconds'])] for r in rows])
failure=[]
for r in rows:
 d=R/r['run'];p=read(d/'phases.json')[0];freq=read(d/'ready.json')['frequency'];finish=read(d/'collector-finished.json')
 failure.append([r['run'],finish['status'],f((p['end_qpc']-p['start_qpc'])/freq),'stale heartbeat' if (d/'rejected-poll.json').exists() else '5-second probe wait' if (d/'collector-failure.json').exists() else 'none'])
failuretable=table(['Run','Collector result','Elapsed phase s','Failure trigger'],failure)
sourcefiles='\n'.join('- `'+p.name+'`' for p in sorted(R.iterdir()) if p.is_file() and p.suffix in ('.py','.ps1','.cs','.exe'))
report=f'''# Stage 6 event-drain heartbeat diagnosis — 2026-09-20

FINAL STATUS: STRONG_CAUSAL_EVIDENCE

Strongest supported cause category: EVENT_EVIDENCE_WRITE_BLOCK.

Current source-level mechanism is directly observed: synchronous filesystem calls on the event-pump thread prevent the next heartbeat from being constructed/published during C: hashing. A 12.297422-second File.AppendAllText call and a separate 10.404254-second call were captured outside the queue lock. Test-Path also stalled for up to 5.995881 seconds. This establishes an infrastructure blocking mechanism, not the responsible kernel/driver/security component or the exact call responsible for the original historical interval.

No corrective change is implemented. Protected-baseline eligibility: NOT JUSTIFIED.

## 1. Fresh launch and scope

Fresh Windows UAC approvals successfully launched the read-only process monitor in PowerShell 7.6.5. The initial smoke captured all 5 START/STOP pairs, max heartbeat 1.045508 seconds. Each subsequent run has a distinct nonce, PID, creation FILETIME, launch executable/hash, ready identity and retained monitor handle. `launch.json`, `ready.json`, `monitor-config.json`, `source-hashes.json` and `monitor-exit.json` in each run are authoritative.

Eight monitors (smoke plus seven diagnostic cases) exited normally. No VirtualBox start was recorded. Initial/final enumerations and the final process snapshot found none; VBoxSDS was stopped. No protected VM/configuration path was accessed by this work. This is scoped tool/source evidence, not a newly installed system-wide file-access audit. No VirtualBox command, VM action, protected hashing, dry1/dry2, production action or Windows security change occurred.

Only sacrificial 1-GiB workload files were read: `docs/stage6-heartbeat-journal-20260918/sacrificial/large.bin` on C: and `D:/JARVIS-STAGE6-SACRIFICIAL-TIMING-20260918/large.bin`. Fixed diagnostic evidence/control paths were used. Only the process monitor was elevated; collectors/workloads were not administrative.

## 2. Call graph and exact source operations

Drain → select exact queue entry under SyncRoot → release lock → read PSEventArgs/CIM payload → read already-delivered process metadata → serialize JSON → construct path → Test-Path → Get-Item.Length → validate selected entry under lock → release lock → File.AppendAllText → revalidate same reference under lock → exact RemoveAt → release lock → next event → backlog query → drain complete → heartbeat construct/write/Flush(false).

Measured source locations: `monitor.ps1:29` drain, `:35` payload, `:37` metadata, `:43` Test-Path, `:44` file length; `event_queue.cs:73` actual File.AppendAllText and `:78` exact removal. `monitor.ps1:79`, `:81`, `:84` are journal length, journal Flush(false), and completion-file Test-Path. Durable final Flush(true) remains at `:92`. There is no per-event Get-Process or external process-metadata query. External filesystem calls are individually bracketed. File.AppendAllText's internal open/write/close steps are not independently traced; no native subcall is claimed.

## 3–7. Exact blocking, lock, queue, write and metadata evidence

{timings}

The longest write (minimal) was 12.2974218 seconds, with zero recorded thread CPU during that span. The `a2` write was 10.404254 seconds with 0.015625 thread CPU seconds. Both were outside SyncRoot. Instrumentation overhead maxima were below 0.000448 seconds. Native CPU accounting is quantized, so it supports waiting rather than sustained CPU execution but does not identify the kernel cause.

Maximum lock hold across all cases was 0.0007362 seconds; maximum wait was 0.0004495 seconds. These conservative maxima include initialization/finalization calls. Queue removal was at most 0.0000197 seconds. The longest drains contained one to six events, not a huge unbounded batch. All queues reconciled to zero residue; no internal identity collisions were recorded. Individual file calls dominate the slow drains.

{schedule}

Producer interarrival gaps include intentional pacing, collector file I/O and probe waits; they are not measured kernel scheduling starvation. Consumer drain gaps include Wait-Event and blocking filesystem calls. Full raw callback/enqueue observations and signed observer-order deltas are in `supplemental-campaign.json`. Exact OS scheduler latency is unavailable. The independent 100-ms observer continued with maximum excess under 29 ms even during long main-thread stalls; full-run GC pause totals are small. This does not establish a global scheduling or GC stall. Optional GC/CPU/disk telemetry is deliberately unavailable in minimal/none, never reported as zero.

## 8. A/B results

{ab}

`a1` is A: normal C hashing. `minimal` is B: optional resources/runtime metrics disabled. `persist-d` is C: only event persistence moved to the fixed D evidence directory. `none` is D: also secondary WMI telemetry disabled. `dhash` is E: hash source on D, original C event path. Heartbeat/control paths remained C in every case. The same 10-second limit, exact queue-entry algorithm and event completeness rules remained in force.

{failuretable}

PASS here means only that this diagnostic case completed with its recorded checks; it is NOT monitor acceptance. Four failed cases are preserved. `minimal`, `none` and `a3` stopped on the unchanged five-second probe wait. Their primary coverage validator reports FAIL because the successful-probe list excludes the timed-out probe; supplementary retained-handle reconciliation proves respectively 11/11, 40/40 and 19/19 exact START/STOP pairs and kernel exits. Cached return codes for those final probes were not captured and remain null. The probe timeout causes are unconfirmed; they are not erased or called passing runs.

`a2` failed directly at `journal.py:75` with stale/future heartbeat. The last successful poll age was 9.2434485 seconds; the rejected poll took 6.2496482 seconds and the prior heartbeat was 11.4062489 seconds old at catch time. The exact internal rejection age was not logged. Table ages are successful poll samples, not complete upper bounds. Offline heartbeat intervals separately expose the 15.6721902-second minimal-run gap and 11.4139848-second a2 gap.

Redirecting only events to D reduced max drain to 0.0365078 seconds and max append to 0.0005546 seconds. But C journal Flush(false) still took 6.7108482 seconds, completion Test-Path 3.9383027 seconds, and journal FileStream.Length 2.9826489 seconds. Event-only relocation is therefore insufficient to remove all measured blocking paths. D hashing with C evidence had max heartbeat 1.0872007 seconds and max drain 0.0902553 seconds.

## 9. Three independent C repetitions and resource context

All three required attempts were made once with fresh identities, without retrying any failure. `a1` completed (77 pairs); `a2` failed closed on heartbeat age (73 pairs); `a3` failed closed on probe wait (19 pairs). All three showed multi-second synchronous C filesystem operations. Only a2 reproduced a >10-second heartbeat in this three-run subset; a1/a3 are not represented as identical reproductions of the historical 14.565-second interval. Separately minimal reproduced a 15.672-second interval.

{storage}

The counters are coarse, nonrandomized observations. They show C storage pressure and multi-second sampled read/write latency alongside modest total CPU use; they cannot establish disk firmware, filter driver, antivirus, indexing, paging or another low-level cause. Raw per-core/process/thread/memory counters remain in each full-telemetry `resources.json` and derived `analysis.json`/`storage-correlations.json`. Minimal/none intentionally omit these counters. They still reproduce file blocking, so optional telemetry is not necessary for the mechanism.

## 10. Cause classification

EVENT_EVIDENCE_WRITE_BLOCK is directly supported by separately timed actual AppendAllText calls. File-existence queries and other C file operations also block. No observed multi-second lock, event-object property access, event metadata lookup, exact removal or oversized-batch explanation is supported. File metadata blocking must not be confused with process metadata lookup. MULTIPLE_CAUSES would overstate knowledge of distinct underlying causes; multiple APIs may share one unresolved filesystem mechanism.

## 11. Minimum proposed correction — NOT IMPLEMENTED

Propose a bounded validation-infrastructure live run directory on D for event evidence, heartbeat journal, ready/finish/stop controls, collector records and other run-local persistence. Both monitor and reader must use that single validated run root. C and D sacrificial hash-source locations remain unchanged so the problem workload is still exercised. Keep source/executables frozen initially; capture hashes and existing identity checks. Archive to the canonical evidence location only after collection/finalization. Reject unexpected paths, volume mismatch, reparse escapes and directory reuse. Do not add arbitrary path authority.

Likely future scope: copied diagnostic `launch.ps1`, `monitor.ps1`, `collect.py`, `resources.ps1`, and the run-control path wiring in `workload.py`; report/archive path resolution as needed. `journal.py` Reader semantics and `event_queue.cs` identity/removal behavior require no correction. The accepted collision-correction source remains untouched. D event-only testing already exists as an experiment, not an accepted correction.

This is the smallest next candidate addressing all *measured* C run-file blocking without changing the event algorithm or raising timeouts. It is not a proven fix. The three probe timeouts need their own identity/launch/exit timing verification; moving evidence alone may not fix executable loading or collector delays. Do not increase the five-second probe wait or ten-second health limit without a separately justified review.

After authorization, require collision/failure-injection tests, each A/B workload, at least three C stress attempts, exact START/STOP/retained-handle coverage, stale/missing/partial/rotation/capacity/publisher-death failures, final durability, and cleanup. A timeout or stale heartbeat remains a failure. Only then consider separately authorized full sacrificial revalidation and independent dry1/dry2. No protected hashing until the complete required monitor acceptance and preservation gates pass. If D run-root relocation fails, preserve the result and diagnose rather than invent another correction.

Rollback is to stop using the new disposable diagnostic candidate and retain the previous monitor unchanged. Never delete failed evidence. No VM, production, ACL, service, schema or runtime rollback is involved.

## 12. Remaining uncertainty

The original historical 14.565-second interval lacked this fine instrumentation. Its exact blocking native call and low-level cause remain UNCONFIRMED. New evidence establishes a matching class of blocking, not retrospective certainty. File.AppendAllText open/write/close attribution, filesystem/driver/security origin, producer kernel scheduling, three probe timeout causes and host background influences remain unresolved. A/B runs were sequential on one machine, not randomized or equal-duration where fail-closed termination shortened them. A single D comparison is not universal reliability proof. Reader polling itself can block in file I/O, as the a2 elapsed poll shows; no exact Reader filesystem subcall attribution is available here.

HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

## 13. EventIdentifier regression and source integrity

`queue-tests-67d2c73644704feea3d6477cae8ff09f/result.json`: 222 assertions PASS; real PSEventArgsCollection/reference-identity proof; 10,000 concurrent events, 9,993 reused external identifiers, zero losses/duplicates/sibling deletions/internal collisions. Current seven cases recorded {sum(r['starts'] for r in rows)} START and {sum(r['stops'] for r in rows)} STOP events across {sum(r['externalCollisions'] for r in rows)} external-ID collisions, zero internal collisions. All retained identities have exactly one pair. Smoke adds five pairs separately.

Seventy per-run hashes (ten actual monitor/collector/helper/launcher/workload files across seven cases) match final diagnostic source: no mid-campaign drift. The earlier smoke predates finer timing and is not falsely included in that equality claim. Analysis/report tooling was added or corrected for optional absent telemetry; raw runs are unchanged. `diagnostic-instrumentation.diff`, `source-before/`, `pre-refinement/`, per-run source hashes and `source-final.json` disclose the diagnostic-only changes. No application/Core source was edited; no acceptance commit was made.

## 14–16. Protection, cleanup and eligibility

Protected VM/configuration access: NONE in this pass. Production change: NONE. Ten-second limit unchanged. No dry runs or protected hashing. Protected-baseline eligibility: NOT JUSTIFIED.

`final-identity-source-check.json` initially preserved two access-denied PID rechecks. `pid-query-followup.json` proves both PIDs now belong to Chrome with later creation times, and `final-reconciliation.json` closes this as PID reuse, not live probes. No unrelated process was terminated. Original retained kernel exit records remain the stronger proof of the test processes' completion. All monitors/workloads/resource samplers exited normally; zero forced workload cleanup; final VBox/VirtualBox/J6Probe snapshot empty. Smoke exit proof is separately recorded. Diagnostic event files, flags, traces and D event evidence are intentionally retained evidence, not cleanup leaks.

{len(old)} historical collision-correction evidence files rehashed with unchanged sizes/mtime; prior canceled-run evidence is separately checked by archive sealing. The known protected post-incident LocalhostReachable=1, historical=0, future validation-copy=0 distinction remains unchanged; none of those protected files was reopened to recheck it here.

## 17–18. Evidence and archive verification

Evidence root: `{R}`.

Archive destination: `C:/Users/jonny/OneDrive/Desktop/TEAGUE INDUSTRIES DATABASE/06 SOURCE RECORDS/STAGE6 EVENTDRAIN RESUME 20260920`.

`archive-manifest.json` inventories every sealed source/evidence member with SHA-256 and size. `archive.py seal` verifies prior evidence and all ZIP members. `archive.py transfer` verifies every transferred file and every destination ZIP member. `archive-verification.json`, produced only after those checks, is the authoritative archive member count and ZIP/manifest hash receipt. The receipt is outside the sealed ZIP to avoid self-reference. Original failures, incomplete cases, source snapshots and supplemental reconciliations are included; no credentials or environment files are copied. Archive verification is separate from, and cannot grant, monitor acceptance.

## Exact diagnostic source/evidence tooling

All new work is under this diagnostic directory (plus the bounded D event-evidence directory and canonical archive). No previous report or raw evidence was overwritten.

{sourcefiles}

Commands actually used: fresh host-context `pwsh -NoProfile -File <this directory>/launch.ps1 -Run <case>` with separate Windows UAC approval; local Python `-B analyze.py <case>`, `event_analysis.py <case>`, `supplement.py`, `summarize.py save`, `final_checks.py`, and final archive seal/transfer. The queue command is `pwsh -NoProfile -File test_queue.ps1`. Exact per-run configuration and source hashes are preserved. No further workloads are authorized or started by these report tools.

STOP FOR REVIEW. No proposed correction, monitor acceptance, protected baseline capture or later Stage 6 operation is performed by this report.
'''
with (R/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
print(json.dumps(dict(report=str(R/'REPORT.md'),historicalFilesPreserved=len(old),campaignPairs=sum(r['starts'] for r in rows),status='STRONG_CAUSAL_EVIDENCE')))
