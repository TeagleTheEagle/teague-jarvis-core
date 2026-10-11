from pathlib import Path
import json,hashlib,math,re,subprocess,os
R=Path(__file__).parent;DOC=R.parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(n,v):
 with (R/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
data=read(R/'probe-evidence.json');dist=read(R/'lifetime-distributions.json');loc=read(R/'timeout-locations.json')
# Preserve initial broad search unchanged; classify observer 15000 ms separately.
definitions=[];references=[];separate=[]
for x in loc['definitions']:
 if '15000' in x['text']:separate.append(dict(x,meaning='15-second evidence observer; NOT five-second acceptance timeout'))
 elif Path(x['path']).suffix=='.md' or Path(x['path']).name.startswith('make_'):references.append(x)
 else:definitions.append(x)
live=[]
for code in Path('D:/JARVIS-STAGE6-LIVE').glob('*/code'):
 for p in code.iterdir():
  if not p.is_file() or p.suffix not in ('.py','.ps1'):continue
  s=p.read_text(encoding='utf-8-sig',errors='replace')
  if not any(t in s for t in ('J6Probe','wait_original','class Probe')):continue
  for i,line in enumerate(s.splitlines(),1):
   if re.search(r'wait\(timeout\s*=\s*5\)|WaitForExit\(5000\)',line):live.append(dict(path=str(p),line=i,text=line,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
save('classified-timeout-locations.json',dict(definitions=definitions,references=references,separateObserver=separate,liveDDefinitions=live))
# Correct native cohort labels using explicit recorded control identity, not filename assumptions.
corrections=[]
for row in data['rows']:
 if '90e9469000dd4530a86b98fad67d7089' in row['path']:
  t=next(x for x in read(Path(row['timingRecord'])) if x['pid']==row['pid']);corrections.append(dict(pid=row['pid'],created=row['created'],control=t.get('control'),executable=t['executable']))
save('native-cohort-labels.json',dict(note='Initial broad extraction default kind is not authoritative for native-control rows; these explicit control values supersede it. Main 727-probe cohort excludes the native-control campaign.',rows=corrections))
slow=sorted(data['slowIncidents'],key=lambda x:int(x['created']));M=max(x['lifetime'] for x in data['rows']);C=max(x['createProcessSeconds'] or 0 for x in data['rows']);budget=math.ceil((M+C)*1.5*10)/10
save('proposed-model.json',dict(status='PROPOSED_ONLY',decision='REVISE_PROBE_ACCEPTANCE_MODEL',classification='LOCALLY_CHOSEN_DIAGNOSTIC_LIMIT',currentLimitUnchanged=5,proposedSoftMarkerSeconds=5,proposedLaunchToExitBudgetSeconds=budget,derivation=dict(maxKernelLifetime=M,maxObservedCreateProcess=C,conservativeSum=M+C,safetyMarginFraction=.5,rounding='ceil 0.1 s'),heartbeatThresholdUnchanged=10,quietSecondsUnchanged=4.6,finalizationDeadlineUnchanged=45,collectorWaitUnchanged=60,overallMonitorLifetimeUnchanged=600,notes='Empirical candidate for explicit review and new validation; not Windows worst-case guarantee, not permission to implement, not historical reclassification.'))
incident='\n'.join(f"| {x['run'].split('-')[0]} / {x['pid']} | {x['mode']} | {x['lifetime']:.7f} | {x['createProcessSeconds']*1000 if x['createProcessSeconds'] is not None else 'unrecorded'} | {x['maxHeartbeat']:.7f} | {x['starts']}/{x['stops']} | yes | {x['exitCode'] if x['exitCode'] is not None else 'unrecorded'} |" for x in slow)
distribution='\n'.join(f"| {k} | {v['n']} | {v['median']:.7f} | {v['p95']:.7f} | {v['p99'] if v['p99'] is not None else 'insufficient n'} | {v['max']:.7f} | {v['above5']} | {v['above10']} |" for k,v in dist['distributions'].items())
def link(path,line):return f'[{Path(path).name}:{line}](<{path}:{line}>)'
current=Path('D:/JARVIS-STAGE6-LIVE/0c5c564771a0475da2d8da4d655574e9/code')
report=f'''# Stage 6 probe-timeout requirement review

**REVISE_PROBE_ACCEPTANCE_MODEL — PROPOSAL ONLY.** Do not implement or resume acceptance on the strength of this report. The existing five-second failure rule remains in force until the owner approves a specific change. The historical failures remain failed, and their underlying Windows causes remain UNCONFIRMED.

## 1. Exact timeout locations and provenance (T1)

Classification: **LOCALLY_CHOSEN_DIAGNOSTIC_LIMIT**, subsequently preserved as an explicit owner acceptance constraint. It is not a Python default or a demonstrated JARVIS response-time/security requirement. No original rationale for choosing the exact number was found.

- Earliest located preserved introduction: {link(DOC/'stage6-heartbeat-journal-20260918/dryrun.py',56)}, literal `p.wait(timeout=5)` inside `run(name)`. File's dated context and later source lineage locate this earliest known instance; they do not prove a first Git introduction date.
- Propagated: {link(DOC/'stage6-monitor-timing-20260918/collect.py',24)}, {link(DOC/'stage6-heartbeat-decoupled-20260918/campaign.py',25)}, {link(DOC/'stage6-eventdrain-resume-20260920/collect.py',40)}, {link(DOC/'stage6-dlive-20260920/candidate/collect.py',41)}.
- Current actual live definition: {link(current/'probe_timing.py',38)}, `Probe.wait_original()` explicitly calls `Popen.wait(timeout=5)`; current caller {link(current/'collect.py',55)}. No config/default/environment selection supplies this value.
- Test assertion/caller: {link(current/'test_probe_handles.py',8)}. It requires native probe exit 0 within the same literal, as a test fixture bound.
- Separate limits: observer `WaitForSingleObject(...,15000)` at {link(current/'probe_timing.py',33)} and `join(timeout=16)` at line 44 are evidence/cleanup waits, not acceptance extensions. They do not turn the timeout into PASS.
- Python API default is `timeout=None`: installed `subprocess.py:1259`; Windows `_wait` at 1581–1595 converts explicit seconds to integer milliseconds and throws `TimeoutExpired` on WAIT_TIMEOUT. Exact file/extract in `stdlib-wait.json`.
- `git log --all -S J6Probe -- docs tests` found no commits; the earliest files are not tracked according to `git ls-files`. Exact first author/commit is therefore **not discoverable in inspected Git history**, not invented. HEAD stayed 9460dbc44f63c95d1128c1a27f124f87d99b530b.
- Search covered 922 documentation/source files before this review, plus current tests search (no J6Probe/probe_timing matches) and live D code copies. `classified-timeout-locations.json` lists every matching location found ({len(definitions)} source/generated-source references, {len(live)} D definitions, documentation references separately). `timeout-locations.json` preserves the initial broad search, including three distinct 15000-ms observer references explicitly reclassified in the refined inventory. No claim that inaccessible/deleted documents were searched.

Specification context: {link(DOC/'stage6-heartbeat-decoupled-20260918/DESIGN.md',5)} fixes heartbeat/publisher/event-pump identity and ten-second freshness; its state machine requires complete event counts, pinned exit identity, durability and cleanup. It does not justify exactly five seconds for native probe execution. {link(DOC/'stage6-monitor-diagnosis-20260918/REPORT.md',94)} requires complete sacrificial event coverage and fail-closed behavior. {link(DOC/'stage6-probe-diagnosis-20260920/REPORT.md',35)} previously identified local test provenance and explicitly retained owner authority. Broader Core completion/deployment documents reviewed define recovery/identity/preservation, not a five-second whoami SLA.

The later user directives explicitly say **do not increase the five-second timeout**. That is binding current scope even though origin is local. This review proposes changing the acceptance specification; it does not assert that local provenance cancels those instructions.

## 2–4. Intended property and actual wait behavior (T2/T3)

The code mechanically bounds how long one collector wait can block. Preventing an indefinite/hung test is a reasonable inference, not a documented original author's explanation. It is not sufficient to prove absence of orphans, valid identity, monitor health or STOP delivery; each has separate checks.

Sequence: QPC launch-request marker → CreateProcess brackets → retained Popen process handle → creation FILETIME capture → independent 15-second observer thread → main QPC marker → `wait(timeout=5)` → normal return or exception. The five-second wait begins **after** process creation/handle capture. It excludes time already spent inside CreateProcess and excludes later event-delivery time. Thus it is not exactly a launch-to-exit SLA, and process lifetime >5 alone is not identical to a main wait timeout.

Windows `_wait` uses one relative handle wait, not a polling loop or wall-clock comparison. QPC measures diagnostic intervals. In the latest run the main wait measured 4.9979482 s, catch at 5.0006168 s after launch, immediate handle status 258. These recorded granularities do not explain the 5.6248818-s lifetime; the process really was still unsignaled when checked.

stdout/stderr are DEVNULL; no output pipe/communicate deadlock exists in this probe path. The probe is copied native whoami, no Python/PowerShell startup within that executable. The harness launches the probe directly, with a separate workload and resource sampler. No child process is launched by `Probe`; undocumented internal whoami child behavior has not been exhaustively traced and is not asserted absent.

Timeout does **not** terminate the probe. The exception latches FAILED_CLOSED, stops further probe/workload admission and publishes a failed closure request. Retained handles and independent observer later capture actual exit/signaled state and (newer runs) real exit code. They never synthesize STOP events. Workload cleanup is cooperative first, with only its retained-child fallback; unresolved exit/identity blocks acceptance.

The collector's `Reader.poll()` at {link(current/'collect.py',42)} is not called while `wait_original()` blocks. A separate monitor keeps publishing, but simply changing `5` to a larger number could also lengthen collector health blindness. That direct edit is **not** the proposed correction. {link(current/'journal.py',75)} implements current reader age rejection; {link(current/'FinalizationGate.cs',1)} additionally checks strict >=10-second intervals during finalization. Neither is changed in this review.

## 5. All located >5-second incidents (T4)

Offline review deduplicated 1,684 kernel-identified probes across 22 preserved runs; seven had recorded lifetime >5 s, none >10 s. This mixed historical set includes different infrastructure revisions and native controls; it is not one controlled statistical population. No new probes were necessary or launched.

| Run / PID | Load | Kernel lifetime s | CreateProcess ms | Max run heartbeat s | START/STOP | Retained exit | Exit code |
|---|---|---:|---|---:|---|---|---|
{incident}

Each of the seven has preserved failure evidence and recorded completed cleanup/no unresolved identity in its campaign reconciliation. For the first four older records, null cached returncode remains **unrecorded**, not success. The `minimal` run independently violated heartbeat health (15.672 s); it would still fail under the proposed model. For `none`/`a3`, max interval was below ten but successful poll samples do not prove uninterrupted healthy observation at every instant. Newer healthy-heartbeat cases do not erase those differences.

Latest 5.625-s case has **no canonical persisted STOP**. It is NOT an example meeting the hypothetical “both START and STOP captured” condition. The monitor rejected failed producer closure before sealing; its failure remains independently disqualifying. Raw per-incident paths and source hashes: `probe-evidence.json`, `read-input-hashes.json`.

## 6–10. Distributions, health, lifecycle and cleanup (T6)

Like-for-like comparison uses 727 unchanged-whoami D-workspace probes: earlier instrumented diagnosis plus latest candidate runs. Native helpers are excluded. Percentiles use linear interpolation; p95 only n>=20, p99 only n>=100. Failures truncate runs; order is nonrandomized and background load uncontrolled. These are observed distributions, not reliable tail probabilities or a Windows worst-case bound.

| Load | n | Median s | p95 s | p99 s | Maximum s | >5 s | >10 s |
|---|---:|---:|---:|---|---:|---:|---:|
{distribution}

That cohort contains 727 confirmed kernel exits, 727 STARTs and 726 canonical STOPs (latest missing STOP). Earlier 577-probe diagnosis reconciled 577/577 pairs despite two failed timeout runs. Latest idle was 94/94; latest C reads 56/55. Healthy heartbeat during a slow probe proves neither STOP completeness nor successful overall acceptance.

Recorded reconciliations show no live/unresolved identities or orphans at their respective cleanup snapshots. No new processes were launched by this review, and no new runtime cleanup claim is substituted for those dated records. No force termination performed in this pass. Old PID reuse remains distinguished from a surviving original process. Supporting reports: eventdrain `REPORT.md:136`, probe diagnosis `REPORT.md:103`, finalization `identity-reconciliation.json` and `final-host-state.json`.

## 11. Is five seconds semantically required? (T5/T7)

**Not established as an inherent Stage 6 monitor/preservation safety property.** It remains a binding current acceptance constraint until changed explicitly. Its operational purpose is bounded test progress, whereas the security property is reliable, identified, complete, healthy lifecycle observation with finite failure handling.

A 5.625-s probe with valid retained identity, uninterrupted healthy monitoring, exact START and STOP evidence, normal bounded exit and verified cleanup would not by that duration alone violate the substantive documented preservation/monitor invariants. It would still fail today's explicit five-second rule. This conclusion is conditional and does **not** pass the latest failed run, which lacks STOP evidence, nor any older failure with incomplete exit/health evidence.

## 12–13. Proposed acceptance model and bound (T8)

**Do not implement yet.** Proposed narrow harness change, with owner review of both semantics and the empirical budget:

1. Keep five seconds as a persisted **SLOW_PROBE** diagnostic marker. Reaching it is neither success nor automatic loss of process identity. No process retry, relaunch or retrospective failure relabelling.
2. Keep one retained handle per unambiguously known PID/creation identity until final proof. Preserve duplicate-PID rejection. Stop accepting new probes when an existing unresolved probe reaches the slow marker; drain that known work rather than accumulating more.
3. Replace a long blind blocking wait with bounded wait slices (at most the existing 50-ms poll cadence) while checking publisher identity/liveness, journal freshness, subscriber/consumer failure signals, event progress and the same retained process handle. The separate monitor must keep heartbeat/event draining active. On any error latch failure immediately. Empty queue/no event is not itself subscriber proof; final exact lifecycle evidence is mandatory.
4. Proposed hard **launch-request-to-confirmed-exit acceptance budget: {budget:.1f} seconds**. Fixed absolute monotonic deadline, including CreateProcess time, never renewed by heartbeat/event/progress. This is a candidate for validation, not an established safe Windows bound. Derivation uses the largest retained kernel lifetime across all inspected cohorts ({M:.7f} s), plus the largest separately observed CreateProcess call ({C:.7f} s, native control PID 8952), then a disclosed 50% engineering margin and upward 0.1-s rounding: `ceil(({M:.7f} + {C:.7f}) × 1.5 × 10) / 10 = {budget:.1f}`. Summing different maxima is deliberately conservative; they were not measured together. First-instruction/internal Windows cause remains unknown. No percentile or sample maximum establishes a universal guarantee.
5. Admission deadline is the **earlier** of that per-probe deadline and remaining fixed workload/campaign budget. Keep the existing workload duration+15-second outer guard, monitor 600-second lifetime cap, 45-second closure budget, 60-second collector exit wait and 4.6-second quiet calculation. Do not let a sequence of slow probes renew any campaign deadline. Reject admission without enough remaining budget. Successful process return still needs exit code 0, identity recheck and exact START/STOP reconciliation.
6. After producers close and all tracked handles signal, apply the existing finalization gate unchanged: complete identities, queue empty, no active persistence, healthy subscriber and heartbeat, quiet interval reset on new events, unsubscribe/final drain, durable evidence/manifest/archive verification. A signaled handle never substitutes for STOP.
7. Ten-second monitor health threshold is independent and unchanged. A 13.6-second process can only be eligible if health is checked throughout it and remains healthy; a ten-second heartbeat lapse still fails. A hung CreateProcess or blocked synchronous evidence read is not excused: late/unknown observation prevents acceptance. These are finite acceptance deadlines, not a promise that Windows I/O or scheduling can always be preempted at the deadline. A watchdog/reporting gap leaves the run failed or unresolved.

This explicitly relaxes the current *probe performance cutoff*, subject to owner approval, while retaining—and checking independently—the documented identity, health, event, cleanup and bounded-progress requirements. It would be misleading to say there is no numerical relaxation. It is more than merely changing a constant because blind waiting is removed, time origin includes creation, health remains independently enforced and success still requires complete evidence.

The proposed 13.6-s budget fits within the existing +15-s workload grace and 15-s independent exit-observer bound in the measured/nominal case. Their clocks currently start at different times: implementation must reconcile absolute deadlines and cannot assume that arithmetic alone guarantees safe cleanup. If this cannot fit without changing other bounds, return for review. No automatic timeout tuning or growth on subsequent failures.

## 14. Required fail-closed behavior and validation (T9)

| Failure | Required disposition |
|---|---|
| Never exits / exceeds fixed budget | FAIL; close admission; retain identity/handle; no PASS even after later exit |
| Identity lost, handle invalid, duplicate PID | FAIL/cleanup UNKNOWN; no PID-only termination or fabricated identity |
| STOP missing | FAIL at finalization deadline regardless of signaled handle |
| Heartbeat stale/dead | FAIL at unchanged threshold; slow probe cannot suppress checks |
| Queue stops progressing / consumer fails | FAIL on health/progress error or unreconciled deadline; no evidence retry into duplicates |
| Subscriber dies | FAIL; no quiet-time inference of health from silence |
| Cleanup fails / orphan survives | FAIL or BLOCKED; archive failed evidence; never accept |
| Flush/hash/archive failure | FAIL; successful process outcome cannot override evidence failure |

Before acceptance: deterministic threshold boundaries at 5 s, proposed 13.6 s and 10-s heartbeat; delayed creation; eventual exit before/at/after deadline; invalid/stale handles; duplicate identities; missing/late/duplicate START/STOP; subscriber/publisher death during slow wait; backlog with no consumer progress; permanent hang; failed cleanup/durable archive; proof old runs remain failed. Then existing 69 tests, 307-assertion gate fixture, unchanged 222/10k queue tests, actual clustered exits, five workloads and both prerequisite-ordered dry runs. No such execution is authorized by this review.

Likely future files: diagnostic `probe_timing.py`, `collect.py`, tests and report/acceptance classification wiring only. Do not edit EventIdentifier queue logic, D workspace boundaries, JARVIS runtime, finalization gate, production or security configuration. Any need to change other bounds or authority must be reviewed. Rollback: keep original candidate/evidence untouched; stop using any future new candidate; never overwrite failed evidence.

## 15–21. Retained status and decision

15. Finalization correction: previously 307 new assertions and idle 94/94 PASS; full workload and dry-run acceptance incomplete. Not re-executed or modified here.
16. D workspace: previous 69/69 focused suite PASS; live artifacts remained D in latest runs. Existing C Windows/runtime binaries are unavoidable read dependencies, not D live-evidence fallback. Not rerun here.
17. EventIdentifier: previous 222 assertions and 10,000-event stress PASS; no queue change or new run.
18. Protected VM/configuration: NOT ACCESSED. No VirtualBox launch or protected hashing.
19. Production: UNCHANGED. Only new review evidence/report tooling written; no timeout, source candidate, runtime or configuration edits.
20. Protected-baseline eligibility: NOT ELIGIBLE / NOT AUTHORIZED. Full acceptance and both dry runs remain blocked. No baseline procedure executed.
21. **REVISE_PROBE_ACCEPTANCE_MODEL.** Review the specific semantics/budget above before authorizing implementation. Current five-second rule remains unchanged. Do not resume the five-workload campaign or dry runs on this report alone.

Historical Stage 1 cause remains UNCONFIRMED. The new finalization race, C-filesystem stalls and native pre-entry/process-lifetime delays remain separate findings; no common Windows/root cause is established.

Evidence: `timeout-locations.json`, `classified-timeout-locations.json`, `git-history-search.json`, numbered current-source extracts, `stdlib-wait.json`, `probe-evidence.json`, `native-cohort-labels.json`, `lifetime-distributions.json`, `proposed-model.json`, `read-input-hashes.json`. Raw historical files are referenced/hash-inventoried, not rewritten. Final archive verification is reported separately after copying this review.
'''
with (R/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
print(json.dumps(dict(decision='REVISE_PROBE_ACCEPTANCE_MODEL',proposedBudget=budget,sourceDefinitions=len(definitions),liveDefinitions=len(live),report=str(R/'REPORT.md'))))
