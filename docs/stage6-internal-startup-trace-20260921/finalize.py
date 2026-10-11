import pathlib,json,hashlib,zipfile,os,difflib
R=pathlib.Path(__file__).parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=read(R/'analysis.json');v=read(R/'reconciliation.json');host=read(R/'host-final.json');plans=[read(R/n) for n in ('plan.json','followup-plan.json','control-plan.json')]
assert not host['liveMatches'] and not host['relevantProcesses'] and not host['traces'] and host['traceExit']==0
for i,p in enumerate(plans):
 C=pathlib.Path(p['code']);m=read(R/'diagnostic-hashes.json') if i==0 else p['diagnosticHashes']
 for x in m:assert sha(C/x['name'])==x['sha256']
 for x in p['sourceHashes']:assert sha(C/x['name'])==x['sha256']==sha(pathlib.Path(p['source'])/x['name'])
 for file,x in read(pathlib.Path(p['root'])/'sacrificial-sources.json').items():
  f=pathlib.Path(file);assert sha(f)==x['sha256'] and f.stat().st_mtime_ns==x['mtime'] and f.stat().st_size==x['bytes']
for x in read(R/'first-failure-freeze.json'):
 f=pathlib.Path(x['path']);assert sha(f)==x['sha256'] and f.stat().st_mtime_ns==x['mtime']
receipt=plans[0]['previousArchive'];previous=pathlib.Path(receipt['path']);assert sha(previous/'evidence.zip')==receipt['zipSHA256'] and sha(previous/'archive-manifest.json')==receipt['manifestSHA256']
with zipfile.ZipFile(previous/'evidence.zip') as z:
 m=read(previous/'archive-manifest.json');assert len(z.namelist())==262
 for x in m['files']:assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256']
columns=['| Workload | Process-only median/max (ms) | Full ETW median/max (ms) | Full ETW + entry median/max (ms) |','|---|---:|---:|---:|']
for c,g in v['selfEffect'].items():columns.append('| '+c+' | '+' | '.join(f"{g[m]['median']*1000:.3f} / {g[m]['max']*1000:.3f}" for m in ('processOnly','fullETW','fullETWWithEntry'))+' |')
table='\n'.join(columns);F=pathlib.Path(plans[1]['root']);C=pathlib.Path(plans[1]['code'])
source_links='\n'.join(f'- `{C/n}`' for n in ('entry_observer.cpp','startup_trace.cpp','startup_driver.py','startup_launch.ps1','startup-config.json','startup-source.json','J6EntryObserve.exe','J6StartupTrace.exe'))
report=f'''# Stage 6 — internal process startup trace gap closure

**Final status: INTERNAL_STARTUP_TRACE_VALIDATED — bounded diagnostic instrumentation only.**

The previously blind interval is now bounded by the actual PE-entry execution marker, primary-thread scheduling and kernel image/file/registry events. A future captured delay can be separated into process creation, pre-entry startup, observed I/O/registry/scheduling intervals and post-entry execution. This does **not** establish the historical cause, resolve the failed large collector, validate a complete 59.7 GB run, or authorize protected baseline capture.

## 1. Previous blind interval

The preserved probe is byte-identical to the original `whoami.exe` copy: SHA-256 `23240ef9f8b0a9a324110b1c2331de31dc1b0e08f5359cb707e51a939af56cd3`. Previously, the parent measured CreateProcess and the retained handle/ETW measured eventual exit, but no internal instruction boundary separated pre-entry loader work from execution within the executable. Historical T3–T8 detail remains UNKNOWN; new tests do not fill it retrospectively.

`analysis.json` contains individual monotonic T0 launch, T1 CreateProcess entry, T2 return, T3 primary-thread handle available, T4 kernel process/thread events, T5 first image event, T6 PE-entry marker and first scheduled primary-thread event. T3 is **handle availability**, not proof the thread ran. T7 runtime initialization complete and T8 intended whoami work begin remain explicitly UNKNOWN. Some thread/image activity occurs before CreateProcess returns; signed intervals must not be clamped or reordered.

## 2. Earliest new internal marker

Forty traced probes reached a hardware execution breakpoint at their actual PE `AddressOfEntryPoint`. The non-elevated controller reads the DOS/PE headers from **its own newly created child**, verifies x64 PE format/range, arms that child's primary-thread debug register, records the exception QPC/address and restores the saved registers immediately. It does not patch executable bytes, write an image file, inject a DLL, attach to existing unrelated processes or change Windows security policy. All probe file hashes remain unchanged.

This is an **observer-timestamped instruction-boundary marker**, not a marker emitted by whoami and not Windows's first instruction. Loader activity, DLL entry/TLS initialization and console setup may already have occurred. The marker precedes the executable's own entry routine/CRT work; no claim is made that it precedes every security operation in loaded DLLs. Precise CRT completion/main entry/private identity-query boundaries remain unavailable without further instrumentation. No functional probe replacement was made.

## 3. Process/thread startup timings

80 full-ETW probes passed: 40 normal and 40 entry-marked, ten per mode in each of four workloads. Another 40 normal probes ran with the unchanged process-only tracer. All returned success; no >5s, >10s or >=13.6s lifetime occurred. The existing 13.6s deadline and 15s independent retained-handle observation period are unchanged. No 10s heartbeat rule changed; this tracing experiment is not a new heartbeat acceptance campaign.

For the 40 entry-marked probes, CreateProcess-return-to-entry was **{v['entryAfterCreate']['min']*1000:.3f}–{v['entryAfterCreate']['max']*1000:.3f} ms**, median **{v['entryAfterCreate']['median']*1000:.3f} ms**. First primary-thread scheduled-to-entry was **{v['firstScheduleToEntry']['min']*1000:.3f}–{v['firstScheduleToEntry']['max']*1000:.3f} ms**. Kernel and retained-handle creation/exit identities agree. Individual primary-thread events and context switches are preserved rather than inferring scheduling from wall-clock gaps.

## 4. Image/DLL load timings

Kernel image events identify the executable and dependent DLL mappings. The debugger independently reports image/DLL events with file-handle-derived paths. The largest adjacent kernel image-event gap was **{v['largestImageEventGap']['seconds']*1000:.3f} ms**, between KernelBase.dll and advapi32.dll events. **This is not an advapi32 load-duration measurement or evidence of a slow DLL.** Gaps can include other work, scheduling and debugger pauses; no paired loader-operation start/end or loader stack was captured.

## 5. Filesystem startup timings

{a['filePairs']:,} process-qualified IRP start/end pairs were matched, with zero ambiguous or unmatched recorded starts/ends. The maximum recorded pair over probes and their console helpers was **{a['fileMax']['seconds']*1000:.4f} ms**. The 4,480 fully pre-entry pairs in marked probes had maximum **{a['startupFileStats']['max']*1000:.4f} ms**. Zero exceeded 100ms, 500ms or 1s. Exact paths, operation IDs, statuses, IRPs and raw QPCs are preserved; no file contents are captured.

The recorded operations include opens and metadata/cleanup operations. **No file-read event ID 15 occurred in this cached working set.** Therefore no read-operation latency is claimed. Memory-mapped/cache activity is not equivalent to a traced ReadFile request. Operations before a descendant can be identity-associated and internal path resolution without its own event remain visibility limitations. No protected VM/configuration path appears in the selected trace metadata.

## 6. Registry startup timings

Classic supported registry tracing supplied **{a['registryPairs']:,}** valid InitialTime/end pairs; 15,600 fall wholly before marked PE entry. The maximum measured registry duration was **{a['registryMax']['seconds']*1000:.4f} ms**. Zero measured pre-entry operations exceeded 100ms, 500ms or 1s. Key/path metadata and status are recorded; registry values, captured-data bytes, command lines and environment contents are excluded by the field allowlist. Three classic records lacked usable nonzero InitialTime and are not counted as timed operations.

## 7. Console/helper timings

{v['helperCount']} probe console helpers were matched using kernel process creation/sequence and parent sequence, not PID alone. Their start event occurred **{v['helperStartAfterParent']['min']*1000:.3f}–{v['helperStartAfterParent']['max']*1000:.3f} ms** after the corresponding parent start event. All 40 helpers belonging to marked probes started **before PE entry**, placing their creation in pre-entry startup for these runs. First helper scheduling and exit events are preserved. The longest helper kernel lifetime was {v['helperMaxLifetime']*1000:.3f}ms.

The initiating console creation request/API and private console-initialization completion are UNKNOWN. Unmarked probes have no main-entry boundary. No helper is blamed for the historical late creation or old delay, and the new ordering is not retroactively applied to the historical run.

## 8. Bounded reproduction results

{table}

Each cell has ten probes. Full ETW and entry-marked order alternated within each workload; the process-only control was a separate later run. Each run used newly generated small sacrificial files on C: and D: (exact bytes, hashes and metadata in each `sacrificial-sources.json`). Load read counts/times are in `load.json`. This is a cache-friendly bounded workload, **not** the original 59.7 GB storage pressure.

A preliminary two-probe diagnostic **failed its checker**: the debugger exit event preceded kernel handle signaling. It did not reproduce the historical deadline failure. It is preserved unchanged at `{plans[0]['root']}`. The marker worked; initial zero-time handle read returned WAIT_TIMEOUT, while the existing independent observer subsequently returned signaled. A fresh copy checks final exit only after that existing observer completes; no wait budget was increased. Full trace and control then passed with separate run identities. No failed acceptance run was relabeled or retried.

## 9. Slowest observed startup interval

Maximum CreateProcess duration in the full comparison was **{max(t['createSeconds'] for t in a['timelines'])*1000:.3f} ms**. Maximum process kernel lifetime was **{max(t['lifetime'] for t in a['timelines'])*1000:.3f} ms**. Maximum return-to-entry was **{v['entryAfterCreate']['max']*1000:.3f} ms**. These use distinct origins: CreateProcess can include work before the kernel creation time. No anomalous multi-second interval exists to classify in these new tests.

## 10. Instrumentation self-effect

Entry marking increased median lifetime by **4.246–6.796ms (approximately 16–23%)** compared with full ETW alone. This is a measurable effect; debug timing must not be treated as directly representative of uninstrumented startup. Measured event-handler work summed **{v['debugHandling']['min']*1000:.3f}–{v['debugHandling']['max']*1000:.3f}ms** per marked probe, excluding notification/scheduling latency while Windows had stopped the debuggee. No subtraction is used to invent an uninstrumented duration.

Full ETW versus the later process-only control changed medians by **-0.185 to +2.367ms**. This sequential comparison characterizes observed differences, not a causal isolated overhead bound. Cold-cache, scheduling and order effects remain. The native controller also differs from the historical Python Popen launcher: explicit handle-list inheritance with NUL streams and a native launch loop. Both comparison modes share that controller; the executable and intended whoami work remain unchanged. The effect of that wrapper relative to historical Popen is not isolated.

The full trace contains **{a['totalEvents']:,}** selected events: 7,688 process/thread/image, 34,935 scheduling, 20,390 file, 73,899 classic registry and 46,305 manifest registry. Event/buffer loss, callback faults and the bounded 200,000-record overflow count are zero. Callback delivery lag reached **{a['maxCallbackLag']:.3f}s**; analysis uses original kernel timestamps, not callback delivery. Remaining buffer headroom is limited; a longer/heavier run must fail closed on overflow rather than silently omit evidence. No large-scale trace acceptance is claimed.

## 11. Strongest supported classification

**Historical delay cause: INCONCLUSIVE.** None of the slow-process categories is supported for a new failure, because the delay did not reproduce. **Instrumentation disposition: INTERNAL_STARTUP_TRACE_VALIDATED** for this bounded diagnostic scope: future captured pre-entry versus post-entry delays can now be distinguished and correlated with the measured kernel events. A specific DLL, registry, security or scheduler cause still requires direct evidence; remaining private work/CRT boundaries may require further diagnostic review if a future post-entry stall occurs.

## 12. Historical 17.195-second probe

Remains a genuine failed deadline with confirmed eventual exit. **Underlying cause UNCONFIRMED.** The new trace was not present historically and cannot explain or repair that record. Historical failed evidence and the prior 262-member archive remain unchanged.

## 13. Historical sampler

Historical CreateProcessW delay of 12.059s and cleanup-bound failure remain preserved. Internal Windows cause and common cause with the probe remain **UNCONFIRMED**. This pass traced the unchanged whoami probe, not a rerun of the sampler acceptance case. No sampler/runtime correction is justified.

## 14. Remaining uncertainty and changes

No original >13.6s delay reproduced. Private security/identity operation timings, CRT/main-work boundaries, exact console creation request, loader duration/stacks, Defender/filter causation and historical behavior remain unproven. Cached small workloads do not establish performance at protected-data scale. Scheduling events indicate execution opportunities/context switches; no unsupported wait-stack diagnosis is made.

New diagnostic-only files in the successful copy:

{source_links}

All original 100 monitor/collector source files, probe executable, queue semantics and timeout policy are unchanged in every copy. The new controller's exit check was corrected after a reproduced diagnostic race; metadata schema caching and restricting detailed console tracing to actual probe helpers reduced overhead. Classic registry events added operation timing. Exact source before/after versions, diffs, compiler commands, hashes and run manifests are archived. A preflight archive-count assertion incorrectly omitted the embedded manifest from the total and was corrected before copying/launching. A final read-only host inventory initially failed serialization due to PowerShell's automatic Matches variable; the corrected inventory passed. Both tooling failures are preserved explicitly.

Four invalid-invocation checks passed; native builds and Python/PowerShell syntax checks passed. **530 trace assertions + 1,040 source/cleanup/control reconciliation checks** passed (overlapping evidence checks, not distinct Core feature tests). No production/Core regression suite was rerun because no Core/application/validated monitor implementation changed.

## 15. Protected VM access

**NOT ACCESSED.** No protected file inventory, read, hash, VM command or normal VirtualBox configuration access was performed. Process inventories observed no VirtualBox process before/after; this diagnostic did not launch VirtualBox. It is not an independent proof about all unrelated host activity throughout the interval. No real protected baseline capture occurred.

## 16. Production changes

**NONE.** No JARVIS process, provider, runtime behavior, configuration, API credential, database, security setting, account, ACL or deployment change. No paid/live provider request.

## 17. Cleanup and archive verification

Across the preliminary failure, full trace and minimal control: **491 kernel-tracked identities**, **408 retained-handle exits**, **83 strictly qualified post-exit cases**, no unresolved identity. All observers exited with code 0 and ETW sessions stopped cleanly. Final identity-qualified host inventory checked **497 recorded identities** including launchers/observers: **zero matching live processes**, zero relevant diagnostic/VirtualBox processes and **zero diagnostic trace sessions**. All tracked handles closed. Synthetic source contents and metadata are unchanged.

Evidence is archived in a new immutable TEAGUE INDUSTRIES DATABASE record. `archive-verification.json` records exact member count and SHA-256 for ZIP, manifest and report. Payload members and embedded manifest are checked against both source files and hashes after creation; archival success is conditional on that receipt. No credentials, protected artifacts or sacrificial bulk payload bytes are archived.

## 18. Protected-baseline eligibility

**UNAUTHORIZED / NOT ELIGIBLE from this diagnostic result.** The failed large collector remains unresolved; no full monitored synthetic revalidation, dry run or protected hashing was performed. Stop for owner review before any subsequent campaign.

## 19. Final status and rollback

**INTERNAL_STARTUP_TRACE_VALIDATED**, with the scope and instrumentation-effect qualifications above. No historical cause has been established. No functional JARVIS or collector correction is proposed from these fast runs. Rollback needs no runtime change: keep the diagnostic copies/evidence preserved, do not deploy them, and retain the original frozen candidate. All temporary elevated tracers have already exited; no persistent elevated service or task exists from this work.

**HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.**

### Supported mechanism references

- [Microsoft: debugger main loop](https://learn.microsoft.com/en-us/windows/win32/debug/writing-the-debugger-s-main-loop): debug events suspend the debuggee until continued; explains the explicit timing qualification.
- [Microsoft: process debug information](https://learn.microsoft.com/en-us/windows/win32/api/minwinbase/ns-minwinbase-create_process_debug_info): thread-start address is approximate, so the marker uses the validated PE entry address rather than assuming lpStartAddress proves entry.
- [Microsoft: system ETW providers](https://learn.microsoft.com/en-us/windows/win32/etw/system-providers): supported system logger mechanisms for thread scheduling and registry events.
- [Microsoft: file-operation end](https://learn.microsoft.com/en-us/windows/win32/etw/fileio-opend): correlating start/end using the IRP identifies the operation interval.
- [Microsoft: registry event timing](https://learn.microsoft.com/en-us/windows/win32/etw/registry-typegroup1): InitialTime identifies operation start; records without a usable start are excluded.
'''
with (R/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
with (R/'preservation-final.json').open('x') as f:json.dump(dict(originalCandidateFiles=100,originalCandidateUnchanged=True,allDiagnosticHashesUnchanged=True,allSacrificialContentsAndMetadataUnchanged=True,priorArchiveMembers=262,priorArchiveVerified=True,failedRunUnchanged=True,productionChanged=False,protectedAccess=False,protectedBaselineAuthorized=False),f,indent=2)
paths=[('report/'+f.name,f) for f in sorted(R.iterdir()) if f.is_file()]
for label,p in zip(('preliminary-failure','full-trace','minimal-control'),plans):
 C=pathlib.Path(p['code']);F=pathlib.Path(p['root']);m=read(C/'startup-source.json')
 for x in m:
  f=C/x['name']
  if f.suffix not in ('.obj','.pdb'):paths.append((label+'/code/'+f.name,f))
 paths.append((label+'/code/startup-source.json',C/'startup-source.json'))
 for f in sorted(F.rglob('*')):
  assert not f.lstat().st_file_attributes&0x400
  if f.is_file() and f.name!='D-load.bin':paths.append((label+'/run/'+f.relative_to(F).as_posix(),f))
rows=[]
for name,f in paths:
 assert f.name not in ('.env',);rows.append(dict(name=name,source=str(f),bytes=f.stat().st_size,sha256=sha(f)))
assert len({x['name'] for x in rows})==len(rows)
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 INTERNAL STARTUP TRACE 20260921');A.mkdir(exist_ok=False)
raw=(json.dumps(dict(status='INTERNAL_STARTUP_TRACE_VALIDATED',scope='BOUNDED_DIAGNOSTIC_ONLY',historicalCause='UNCONFIRMED',files=rows),sort_keys=True,indent=2)+'\n').encode()
with (A/'archive-manifest.json').open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
with zipfile.ZipFile(A/'evidence.zip','x',zipfile.ZIP_DEFLATED) as z:
 for x in rows:z.write(x['source'],x['name'])
 z.writestr('archive-manifest.json',raw)
with (A/'evidence.zip').open('r+b',buffering=0) as f:os.fsync(f.fileno())
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==len(rows)+1
 for x in rows:assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256']==sha(pathlib.Path(x['source']))
 assert z.read('archive-manifest.json')==raw
with (A/'REPORT.md').open('xb') as f:f.write((R/'REPORT.md').read_bytes());f.flush();os.fsync(f.fileno())
receipt=dict(status='HASH_VERIFIED',disposition='INTERNAL_STARTUP_TRACE_VALIDATED',path=str(A),members=len(rows)+1,zipSHA256=sha(A/'evidence.zip'),manifestSHA256=sha(A/'archive-manifest.json'),reportSHA256=sha(A/'REPORT.md'),protectedBaselineAuthorized=False)
for d in (R,A):
 with (d/'archive-verification.json').open('x') as f:json.dump(receipt,f,indent=2);f.flush();os.fsync(f.fileno())
print(json.dumps(receipt))
