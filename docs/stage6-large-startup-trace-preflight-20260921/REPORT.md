# Stage 6 large synthetic collector with startup tracing — preflight

**BLOCKED. No large synthetic acceptance run occurred.**

## Exact blocker

The frozen large collector and the bounded startup-trace experiment are separate validated paths. They are **not integrated**. Running the existing large launcher would start `J6BaselineTrace.exe` and ordinary `Probe` instances, not `J6StartupTrace.exe` plus the non-elevated `J6EntryObserve.exe` entry-marker controller. Therefore it would not meet the new requirement to capture startup evidence during the large monitored run.

The previous `INTERNAL_STARTUP_TRACE_VALIDATED` disposition applied only to the bounded diagnostic experiment. It did not validate the large collector's trace integration. It must not be promoted into that claim.

### Source evidence

- `D:\JARVIS-STAGE6-LIVE\e23d36c0a24246c996aa28e5d5561863\code\large_launch.ps1:19` — `$etw=Start-Process -FilePath (Join-Path $PSScriptRoot 'J6BaselineTrace.exe') -ArgumentList @($root,$PID,$identity.creationFiletime) -Verb RunAs -WindowStyle Hidden -PassThru`
- `D:\JARVIS-STAGE6-LIVE\e23d36c0a24246c996aa28e5d5561863\code\large_launch.ps1:25` — `@{etw=@{pid=$etw.Id;created=$etw.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=(Join-Path $PSScriptRoot 'J6BaselineTrace.exe')};app=@{pid=$app.Id;created=$app.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$pwsh}}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $root 'observer-identities.json')`
- `D:\JARVIS-STAGE6-LIVE\e23d36c0a24246c996aa28e5d5561863\code\large_launch.ps1:28` — `& $py -B (Join-Path $PSScriptRoot 'large_collect.py') $Run 1> (Join-Path $root 'work.stdout') 2> (Join-Path $root 'work.stderr')`
- `D:\JARVIS-STAGE6-LIVE\e23d36c0a24246c996aa28e5d5561863\code\large_launch.ps1:23` — `$app=Start-Process -FilePath $pwsh -ArgumentList @('-NoProfile','-File',(Join-Path $PSScriptRoot 'timed_monitor.ps1'),'-Run',$Run,'-KernelPid',$etw.Id) -Verb RunAs -WindowStyle Hidden -PassThru`
- `D:\JARVIS-STAGE6-LIVE\e23d36c0a24246c996aa28e5d5561863\code\large_collect.py:27` — `probe=Probe(CODE/'J6Probe.exe');probes.append(probe);tree.register(probe.process,'lifecycle-probe')`
- `D:\JARVIS-STAGE6-LIVE\68b6e62890e742b4bedb13cbb0f49e92\code\startup_driver.py:38` — `args=[str(CODE/'J6EntryObserve.exe'),str(root),mode,str(index)]`
- `D:\JARVIS-STAGE6-LIVE\68b6e62890e742b4bedb13cbb0f49e92\code\entry_observer.cpp:32` — `auto launch=Q(),cb=Q();BOOL made=CreateProcessW(exe.c_str(),cmd.data(),0,0,TRUE,CREATE_NO_WINDOW|EXTENDED_STARTUPINFO_PRESENT|(debug?DEBUG_ONLY_THIS_PROCESS:0),0,code.c_str(),&si.StartupInfo,&pi);auto ce=Q();error=made?0:GetLastError();`
- `D:\JARVIS-STAGE6-LIVE\68b6e62890e742b4bedb13cbb0f49e92\code\entry_observer.cpp:61` — `if(e.ExceptionCode==EXCEPTION_SINGLE_STEP&&armed&&ev.dwThreadId==pi.dwThreadId&&ULONGLONG(e.ExceptionAddress)==ep){marker=Q();entry=true;record("PE_ENTRY_EXECUTED",ev.dwThreadId,ep);if(!SetThreadContext(primary,&saved))fault=true;armed=false;}`
- `D:\JARVIS-STAGE6-LIVE\68b6e62890e742b4bedb13cbb0f49e92\code\startup_trace.cpp:56` — `static Row* Target(DWORD pid,LONGLONG q){for(auto& a:rows){auto&r=a.second;if(r.pid==pid&&q>=r.start&&(!r.stop||q<=r.stop)&&(r.image.find(L"J6Probe.exe")!=std::wstring::npos||(r.image.find(L"conhost.exe")!=std::wstring::npos&&std::any_of(rows.begin(),rows.end(),[&](const auto& p){return p.second.pid==r.parent&&p.second.sequence==r.parentSequence&&p.second.image.find(L"J6Probe.exe")!=std::wstring::npos;}))))return &r;}return nullptr;}`
- `D:\JARVIS-STAGE6-LIVE\68b6e62890e742b4bedb13cbb0f49e92\code\startup_trace.cpp:77` — `if(startup.size()>=200000){++startupOverflow;return;}`

The entry marker is supplied by the controller that creates the unchanged probe with `DEBUG_ONLY_THIS_PROCESS` and sets a hardware PE-entry breakpoint. Merely enabling the new kernel tracer does **not** add that marker to ordinary collector-launched probes.

Detailed kernel startup selection currently includes `J6Probe.exe` and its direct creation/sequence-qualified `conhost.exe` helper. It does not provide the same detailed coverage for the Python sampler/hash workers. Helpers have kernel scheduling/image/file/registry events where selected, but their own executable-entry markers and console-creation request call are not supplied by the validated debugger, which observes only its own probe. The new requirement for all monitored probe/helper processes therefore needs an explicit evidence-coverage contract; missing markers cannot be manufactured or labeled captured.

The bounded full-trace experiment retained 183,217 events for 80 probes under a 200,000-record limit. Overflow fails closed. That is only 16,783 records of remaining capacity in that experiment. The longer two-pass collector's volume is **unvalidated**, not proven to overflow. Simply increasing capacity or dropping events would not constitute validated integration.

## Preflight results actually obtained

| Check | Result |
|---|---|
| Frozen collector hashes | PASS: 84/84 |
| Frozen diagnostic hashes | PASS: 96/96 |
| Current integrated candidate hashes | PASS: 100/100 |
| Validated startup-trace hashes | PASS: 109/109 |
| Calibration evidence hash | PASS |
| Relocated dataset manifest hash | PASS |
| Synthetic inventory | 12 files; 59,665,402,098 bytes |
| Synthetic sizes / modification timestamps | Match preserved manifest |
| Synthetic root ancestry / file links | No root reparse point; files regular, single-link |
| Fresh SHA-256 of all 59.7 GB | NOT RUN after integration blocker; no fresh content-equality claim |
| Prior startup trace archive | 532 members verified |
| Prior process-call tracing archive | 262 members verified |
| Prior failed large-run archive | 196 members verified |
| Other historical archives / complete run preflight | NOT completed after integration blocker |
| D: free space | 1,796,351,361,024 bytes (1672.98 GiB) |
| Matching diagnostic / VirtualBox processes | 0 in read-only host inventory |
| Diagnostic trace sessions | 0 |
| UAC observer launches | 0 |
| Hash worker launches | 0 |
| New monitored hash pass #1 / #2 | NOT RUN / NOT RUN |
| New heartbeat / sampler / lifecycle acceptance | NOT RUN |
| New successful baseline manifest | NOT CREATED |

The metadata/manifest checks are not substitutes for the required fresh dataset content hashes or complete path-containment preflight. Those checks must be completed for a later authorized integrated run. No protected files were accessed to establish preservation; the task did not touch them.

## Minimum next step for review

Authorize a **narrow TEST-only collector/startup-trace integration and small sacrificial integration validation**, before reattempting the large campaign. Preserve the existing frozen candidates and all failed evidence. Proposed work is limited to:

1. A separate reviewed launch/adapter path wiring the validated read-only tracer and non-elevated entry observer to the actual collector's probe lifecycle. Preserve the real probe PID/creation identity, retained handles, health callbacks, cancellation and the existing 13.6-second launch deadline / 15-second observer semantics. A controller-process exit is not a substitute for the probe's exit.
2. Define and test trace coverage for each owned helper/sampler/hash-worker role. Preserve UNKNOWN where a supported event/marker is unavailable; any exclusion from the requested evidence needs explicit disposition. Do not add arbitrary process attachment or privileged execution authority.
3. Establish bounded, loss-detecting evidence retention suitable for the long run. Keep live state on D:, durable finalization and fail-closed overflow. The exact retention mechanism requires review/validation; this preflight does not approve or implement a redesign.
4. Exercise the composed path on a small synthetic dataset: two hash passes, startup markers, per-process attribution, sampler behavior, stale-heartbeat failure, deadline failure, trace overflow, finalization and cleanup. Verify original source hashes remain intact and quantify tracing overhead within the composed collector.
5. Only after that integration gate passes, repeat the complete large-run preflight, including all dataset SHA-256 hashes, historical archive requirements and the two established per-run UAC prompts.

Likely new/affected validation components: the large-launch adapter beside `large_launch.ps1`, probe adapter beside `large_collect.py` / `probe_timing.py`, diagnostic entry controller, startup tracer's selection/retention, and integration evidence/reconciliation. No JARVIS production/Core behavior change is indicated. No implementation was performed in this pass.

## Preservation / disposition

Only new preflight/report/archive tooling and evidence were written. All 389 checked candidate files still match their frozen hashes. Existing failure records and archives are unchanged. No process termination, VM launch, protected hashing, production change, security change or timeout/threshold change occurred.

Historical 17.195-second probe and sampler delay causes remain **UNCONFIRMED**. No common cause is established. **HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.**

This is an integration-readiness block, **not a newly reproduced collector/runtime failure**. The previously failed collector run remains failed. Protected baseline eligibility remains **UNAUTHORIZED**. No real protected-baseline execution procedure is released as ready from this blocked result.

Final status: **BLOCKED**. Stop for review.
