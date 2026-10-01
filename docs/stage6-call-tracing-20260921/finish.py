import pathlib,json,hashlib,zipfile,os
R=pathlib.Path(__file__).parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=read(R/'analysis.json');first=read(R/'plan.json');second=read(R/'followup-plan.json');F=pathlib.Path(second['root']);C=pathlib.Path(second['code']);host=read(R/'host-final.json')
assert not host['liveMatches'] and not host['relevantProcesses'] and not host['traces'] and host['traceExit']==0
old=R.parent/'stage6-preserved-probe-sampler-diagnosis-20260921';frozen=read(old/'freeze.json')
for record in (frozen,read(R/'overflow-failure-freeze.json')):
 for x in record.get('rawFiles',record.get('files',[])):
  p=pathlib.Path(x['path']);assert sha(p)==x['sha256'] and p.stat().st_size==x['bytes'] and p.stat().st_mtime_ns==x['mtime_ns']
for x in first['sourceHashes']:assert sha(pathlib.Path(first['source'])/x['name'])==x['sha256']
for plan in (first,second):
 for x in plan['diagnosticHashes']:assert sha(pathlib.Path(plan['code'])/x['name'])==x['sha256']
receipt=read(old/'archive-verification.json');oldArchive=pathlib.Path(receipt['path']);assert sha(oldArchive/'evidence.zip')==receipt['zipSHA256'] and sha(oldArchive/'archive-manifest.json')==receipt['manifestSHA256']
with (R/'preservation-final.json').open('x') as f:json.dump(dict(originalFailedFiles=40,originalCandidateFiles=100,previousArchiveMembers=240,previousArchiveUnchanged=True,firstOverflowRunUnchanged=True,bothDiagnosticCopiesMatchManifest=True,productionChanged=False,protectedAccess=False),f,indent=2)
def line(name,needle):return next(i for i,s in enumerate((C/name).read_text().splitlines(),1) if needle in s)
maps={
'probe_start':[
 ['probe_timing.py',line('probe_timing.py','def __init__'),'Probe.__init__: QPC/clock bridge; fixed executable, no arguments; Popen DEVNULL streams, CREATE_NO_WINDOW'],
 ['python-subprocess-call-path.txt',1,'Popen._get_handles/_get_devnull/_make_inheritable: DEVNULL opens, GetStdHandle/DuplicateHandle; _execute_child/list2cmdline; env=None inherited inside CreateProcess; no caller environment block'],
 ['probe_timing.py',line('probe_timing.py','original=subprocess'),'Measured subprocess._winapi.CreateProcess: process/thread handles and PID/TID returned; Popen retains process handle and closes thread handle'],
 ['probe_timing.py',line('probe_timing.py','def observe'),'GetProcessTimes first identity query; independent retained-handle WaitForSingleObject(15000); unmodified whoami internals unavailable']],
'sampler_start':[
 ['bounded_sampler.py',line('bounded_sampler.py','def query'),'Mapping creation; CreateJobObjectW; SetInformationJobObject; fixed absolute executable; list2cmdline; command buffer'],
 ['bounded_sampler.py',line('bounded_sampler.py','if not K.CreateProcessW'),'CreateProcessW: inherited environment NULL, handle inheritance False, CREATE_SUSPENDED|CREATE_NO_WINDOW; no pipe creation'],
 ['bounded_sampler.py',line('bounded_sampler.py','r.update(createReturned'),'GetProcessTimes/QueryFullProcessImageNameW; AssignProcessToJobObject; retained registration; ResumeThread; CloseHandle(thread)'],
 ['sampler_worker.py',line('sampler_worker.py',"_mark('script_entry_observed')"),'Earliest observed Python script marker; imports/path validation/query/mapping/return markers']],
'cleanup':[
 ['probe_policy.py',line('probe_policy.py','def wait_tracked'),'Unchanged fixed launch deadline and retained-handle wait; independent observer status retained'],
 ['bounded_sampler.py',line('bounded_sampler.py',"r['cleanupBeginQpc']"),'Initial handle check; TerminateJobObject if needed; WaitForSingleObject + QueryInformationJobObject predicate loop; Job close; existing second wait if needed; GetProcessTimes/GetExitCodeProcess/CloseHandle'],
 ['evidence_support.py',line('evidence_support.py','def finish(self,root'),'TreeTracker scan/add spans, identity-bound retained exits and handle close'],
 ['trace_launch.ps1',line('trace_launch.ps1','finally'),'etw-stop; wait up to existing 30000ms; observer disposal. Native tracer flush/stop/consumer results retained; individual native shutdown calls not newly timed']]
}
with (R/'call-maps.json').open('x') as f:json.dump(maps,f,indent=2)
maptext='\n'.join('### '+name+'\n\n'+'\n'.join(f'- `{C / row[0] if row[0] != "python-subprocess-call-path.txt" else R / row[0]}:{row[1]}` — {row[2]}' for row in entries) for name,entries in maps.items())
normal=[x for x in a['samplerInternal'] if x['case'].startswith('normal')]
report=f'''# Stage 6 process-start and cleanup call tracing

**Final status: INCONCLUSIVE.** Diagnostic call tracing is implemented in separate disposable copies. The original delay did not reproduce, and no runtime correction is justified. No full 59.7 GB campaign or real protected hashing was run.

## 1–3. Exact start/cleanup call maps

{maptext}

Environment/argument **contents** were not captured. Only fixed call labels, times, thread IDs, numeric handles, fixed test identities and API status values are recorded. Probe environment=None and sampler environment=NULL mean the OS inherits the environment within CreateProcess; a separate environment-block creation call does not exist in the parent path. CreatePipe was hooked but no probe/sampler pipe was created. stdout/stderr are DEVNULL for the probe; the sampler uses shared memory. Therefore stdout/stderr drains are not applicable to these workers. The diagnostic parent has ordinary console output; it is not used as a worker result pipe.

## 4–5. Slowest calls in valid follow-up

- Probe: `{a['slowestProbeApi']['call']}`, **{a['slowestProbeApi']['seconds']:.7f}s**; independent exit observation returned signaled, not a timeout.
- Sampler: `{a['slowestSamplerApi']['call']}`, **{a['slowestSamplerApi']['seconds']:.7f}s**, a 25ms wait request in the deliberately delayed query. It returned timeout as expected for that individual polling wait, not cleanup failure.
- Maximum probe CreateProcess: {a['callMaxima']['winapi.CreateProcess']:.7f}s.
- Maximum sampler CreateProcessW: {a['callMaxima']['bounded_sampler.CreateProcessW']:.7f}s.
- One high-level span exceeded 2s: delayed `sampler.query_total` **2.0329322s**, comprising the unchanged two-second query deadline plus cleanup. It is not a single blocking Windows API call. Zero spans exceeded 5s; no hard process deadline or cleanup-bound violation reproduced.

Each elapsed call interval includes any thread descheduling while the call is in progress; it does not alone prove blocking inside the Windows implementation. Starts/ends use the existing QPC clock, with thread identities and raw requested wait durations. Last-error state, return values and exceptions are preserved by wrappers. No output text or credentials are logged.

## 6. Console helpers

Kernel sequence/creation-qualified evidence records **{len(a['helpers'])} helpers**, one per probe/sampler worker, with parent sequences and creation/exit times. Latest helper creation was {max(x['fromMainStartSeconds'] for x in a['helpers']):.7f}s after its parent began in this run. Probe helper timing remains relative to kernel process start/exit; unmodified whoami work boundaries are not visible. No helper is blamed for the historical delay. All {a['trackedKernelIdentities']} tracked kernel identities have exit proof: {a['kernelRetainedExits']} retained-handle exits and {a['kernelPostExit']} strictly qualified post-exit handle-acquisition cases. Kernel event/buffer loss and fault counters are zero.

## 7. Internal markers and explicit gaps

The **probe binary is unchanged**, SHA-256 `23240ef9f8b0a9a324110b1c2331de31dc1b0e08f5359cb707e51a939af56cd3`, still byte-identical to the preserved whoami copy. No injected DLL, debugger, replacement helper or speculative flag was used. Its true entry, runtime initialization, console initialization, security lookup, filesystem work and teardown markers remain **UNAVAILABLE**. Kernel helper creation cannot substitute for them.

Only the disposable sampler-worker source gained bounded shared-memory markers. All 72 markers are preserved. For three normal queries, earliest script markers appeared {min(x['firstScriptMarkerAfterKernelStartSeconds'] for x in normal):.7f}–{max(x['firstScriptMarkerAfterKernelStartSeconds'] for x in normal):.7f}s after kernel start; imports took {min(x['stages']['imports'] for x in normal):.7f}–{max(x['stages']['imports'] for x in normal):.7f}s. Query bodies took {min(x['stages']['query_body'] for x in normal):.7f}–{max(x['stages']['query_body'] for x in normal):.7f}s. GlobalMemoryStatusEx, GetSystemTimes, serialization and result-mapping boundaries are individually recorded.

The earliest marker follows the Python loader and minimal tracing imports/mapping setup; it is **not the process's first instruction**. Script cleanup_begin/end are adjacent logical boundary markers with no explicit intervening cleanup, not measured interpreter/OS teardown. Atexit markers precede closing the diagnostic mapping; later runtime destruction remains uninstrumented. No fictitious console/security lookup stage is added where the sampler does not perform one. Missing end markers in intentionally terminated delayed/hung fixtures correctly remain missing.

## 8. Cleanup timings

Five sampler cleanup durations were {min(x['seconds'] for x in a['samplerCleanup']):.7f}–{max(x['seconds'] for x in a['samplerCleanup']):.7f}s; every handle signaled, every Job reached zero active processes, and all handles closed. No cleanup observation timeout occurred. Maximum TerminateJobObject: {a['callMaxima']['bounded_sampler.TerminateJobObject']:.7f}s. Maximum QueryInformationJobObject: {a['callMaxima']['bounded_sampler.QueryInformationJobObject']:.7f}s. Final process-tree reconciliation: {a['callMaxima']['tree.final_reconciliation']:.7f}s.

Kernel observer requested shutdown, flush/stop/consumer results were zero, and launcher observed exit code 0 within {a['observerShutdown']['shutdownWaitSeconds']:.7f}s. This is aggregate shutdown observation; individual native ControlTrace/CloseTrace spans were not modified or separately measured. No CIM application observer was launched, so unsubscribe is not applicable. No new heartbeat acceptance claim is made. The preserved historical maximum remains 1.056s and no heartbeat limit changed.

## 9. Reproduction and preserved instrumentation failure

Attempt 1: 80 probes and five sampler cases completed without the original failures, but diagnostic output **FAILED** because the 200,000-record buffer overflowed by 13,206 records. Of the stored records, 193,553 were repetitive background Process32NextW enumeration calls. This failure is preserved at `{first['root']}` and retains its failed status.

A narrow diagnostic-only correction in a second copy omits repetitive background per-process API spans, retaining whole-scan/discovery spans and all labelled launch/sampler/independent-observer calls. The 200,000 limit did not change. The original copy and run were not edited. The follow-up is `{F}`.

Follow-up: 20 idle probes + 60 under small synthetic D: hashing; three normal sampler queries, one intentionally delayed query, one cancellation. All completed. Maximum probe lifetimes: idle {a['probeStats']['idle']['max']:.7f}s; hashing {a['probeStats']['D-small-hash']['max']:.7f}s. **4,296 live-call spans plus one separately saved final-write span = 4,297 total**, zero overflow. No original >13.6s probe or cleanup-bound failure reproduced. No thresholds were increased. Both datasets are 58,720,256-byte newly generated sacrificial files, not protected VM data. Their bytes/metadata were verified unchanged; only their hashes are archived, not the bulk data.

Wrapper validation checked returns, exception propagation, monotonic ordering, last-error preservation, enumeration filtering and independent-observer retention; Python syntax and PowerShell parser checks passed. These are instrumentation checks, not a Core or protected-baseline acceptance suite.

## 10. System pressure

97 bounded, read-only PDH samples were recorded from a separate diagnostic thread, with no counter-setup errors. CPU maximum was 21.8435%; available memory minimum 23,619 MiB. C: logical-disk queue maximum 1; D: maximum 0. C: maximum sampled mean read/write latencies were 0.8693/5.8600ms; D: sampled mean write latency maximum 6.972028ms. D: reported no physical read operations during the cache-friendly small working set. Thus this run does not recreate the full large-file storage pressure.

No reproduced anomalous call exists to correlate with these counters. Coarse CPU/disk counters do not establish per-thread scheduling delay. Defender/filter and code-integrity/image-load stack traces were not available in the fixed process-lifecycle tracer; these remain explicit gaps. No security settings were changed or security mechanism bypassed.

## 11–15. Classifications and correction gate

- **Probe: INCONCLUSIVE.** The preserved 17.195s lifetime and late helper are real; new fast calls do not explain the old delay.
- **Sampler: PROCESS_CREATION_DELAY**, limited to the directly measured 12.059s historical CreateProcessW interval. The Windows/internal cause of that interval and subsequent cleanup delay remain **INCONCLUSIVE**. The new run did not reproduce either.
- **Common cause: NOT ESTABLISHED.** Neither shared cause nor independence is proven.
- **Minimum functional correction: NONE justified.** Only the demonstrated diagnostic trace-volume defect was corrected in a fresh copy; no runtime behavior or security change was made.
- Residual uncertainty: whoami internals, actual thread wait stacks, security/filter activity, pre-script Python loader work and historical cleanup-gap ownership. Instrumentation overhead and the small cached load limit extrapolation. No broad or full-size retry is authorized by this report.

## 16–19. Preservation and disposition

Protected VM/configuration **NOT ACCESSED**; VirtualBox remained closed; production JARVIS **UNCHANGED**. All 100 frozen candidate hashes, 40 preserved failed-run files (hash/size/mtime), the prior 240-member archive, both diagnostic copy manifests and the first overflow run were verified unchanged. Both observers exited. Final host checks found zero matching live identities, diagnostic processes or trace sessions across 346 recorded identities from the two runs.

New evidence is archived separately in TEAGUE INDUSTRIES DATABASE; exact member count and SHA-256 receipts are in archive-verification.json. The archive includes source diffs, both diagnostic source copies, failed/successful diagnostic traces, internal markers, pressure samples, kernel/cleanup evidence and old-archive references. No credentials or protected artifacts are included.

**Protected-baseline eligibility: BLOCKED / UNAUTHORIZED.** Final status: **INCONCLUSIVE**. Stop for review. The existing failed collector remains failed. Historical long-probe and heartbeat causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Rollback: no original candidate/runtime change needs reversal. Keep all diagnostic copies and evidence preserved; do not deploy them, delete the old run, alter limits or initiate protected capture.
'''
with (R/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
paths=[('report/'+p.name,p) for p in sorted(R.iterdir()) if p.is_file()]
for label,plan in [('overflow-attempt',first),('valid-followup',second)]:
 root=pathlib.Path(plan['root']);code=pathlib.Path(plan['code'])
 for p in sorted(root.rglob('*')):
  assert not p.lstat().st_file_attributes&0x400
  if p.is_file() and p.name!='synthetic-load.bin':paths.append((label+'/run/'+p.relative_to(root).as_posix(),p))
 for x in plan['diagnosticHashes']:paths.append((label+'/code/'+x['name'],code/x['name']))
 paths.append((label+'/code/trace-source.json',code/'trace-source.json'))
rows=[]
for name,p in paths:
 assert p.name!='.env';rows.append(dict(name=name,source=str(p),sha256=sha(p),bytes=p.stat().st_size))
assert len({x['name'] for x in rows})==len(rows)
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 PROCESS CALL TRACING 20260921');A.mkdir(exist_ok=False)
raw=(json.dumps(dict(status='INCONCLUSIVE',kind='DIAGNOSTIC_ONLY_NOT_ACCEPTANCE',files=rows),sort_keys=True,indent=2)+'\n').encode()
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
receipt=dict(status='HASH_VERIFIED',disposition='INCONCLUSIVE',path=str(A),members=len(rows)+1,zipSHA256=sha(A/'evidence.zip'),manifestSHA256=sha(A/'archive-manifest.json'),reportSHA256=sha(A/'REPORT.md'),protectedBaselineAuthorized=False)
for root in (R,A):
 with (root/'archive-verification.json').open('x') as f:json.dump(receipt,f,indent=2);f.flush();os.fsync(f.fileno())
print(json.dumps(receipt))
