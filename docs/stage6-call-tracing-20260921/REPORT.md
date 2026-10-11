# Stage 6 process-start and cleanup call tracing

**Final status: INCONCLUSIVE.** Diagnostic call tracing is implemented in separate disposable copies. The original delay did not reproduce, and no runtime correction is justified. No full 59.7 GB campaign or real protected hashing was run.

## 1–3. Exact start/cleanup call maps

### probe_start

- `D:\JARVIS-STAGE6-LIVE\fb25b7f8e8ce47f2a3f8f24f09efdd70\code\probe_timing.py:18` — Probe.__init__: QPC/clock bridge; fixed executable, no arguments; Popen DEVNULL streams, CREATE_NO_WINDOW
- `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-call-tracing-20260921\python-subprocess-call-path.txt:1` — Popen._get_handles/_get_devnull/_make_inheritable: DEVNULL opens, GetStdHandle/DuplicateHandle; _execute_child/list2cmdline; env=None inherited inside CreateProcess; no caller environment block
- `D:\JARVIS-STAGE6-LIVE\fb25b7f8e8ce47f2a3f8f24f09efdd70\code\probe_timing.py:21` — Measured subprocess._winapi.CreateProcess: process/thread handles and PID/TID returned; Popen retains process handle and closes thread handle
- `D:\JARVIS-STAGE6-LIVE\fb25b7f8e8ce47f2a3f8f24f09efdd70\code\probe_timing.py:34` — GetProcessTimes first identity query; independent retained-handle WaitForSingleObject(15000); unmodified whoami internals unavailable
### sampler_start

- `D:\JARVIS-STAGE6-LIVE\fb25b7f8e8ce47f2a3f8f24f09efdd70\code\bounded_sampler.py:25` — Mapping creation; CreateJobObjectW; SetInformationJobObject; fixed absolute executable; list2cmdline; command buffer
- `D:\JARVIS-STAGE6-LIVE\fb25b7f8e8ce47f2a3f8f24f09efdd70\code\bounded_sampler.py:36` — CreateProcessW: inherited environment NULL, handle inheritance False, CREATE_SUSPENDED|CREATE_NO_WINDOW; no pipe creation
- `D:\JARVIS-STAGE6-LIVE\fb25b7f8e8ce47f2a3f8f24f09efdd70\code\bounded_sampler.py:37` — GetProcessTimes/QueryFullProcessImageNameW; AssignProcessToJobObject; retained registration; ResumeThread; CloseHandle(thread)
- `D:\JARVIS-STAGE6-LIVE\fb25b7f8e8ce47f2a3f8f24f09efdd70\code\sampler_worker.py:11` — Earliest observed Python script marker; imports/path validation/query/mapping/return markers
### cleanup

- `D:\JARVIS-STAGE6-LIVE\fb25b7f8e8ce47f2a3f8f24f09efdd70\code\probe_policy.py:8` — Unchanged fixed launch deadline and retained-handle wait; independent observer status retained
- `D:\JARVIS-STAGE6-LIVE\fb25b7f8e8ce47f2a3f8f24f09efdd70\code\bounded_sampler.py:57` — Initial handle check; TerminateJobObject if needed; WaitForSingleObject + QueryInformationJobObject predicate loop; Job close; existing second wait if needed; GetProcessTimes/GetExitCodeProcess/CloseHandle
- `D:\JARVIS-STAGE6-LIVE\fb25b7f8e8ce47f2a3f8f24f09efdd70\code\evidence_support.py:138` — TreeTracker scan/add spans, identity-bound retained exits and handle close
- `D:\JARVIS-STAGE6-LIVE\fb25b7f8e8ce47f2a3f8f24f09efdd70\code\trace_launch.ps1:19` — etw-stop; wait up to existing 30000ms; observer disposal. Native tracer flush/stop/consumer results retained; individual native shutdown calls not newly timed

Environment/argument **contents** were not captured. Only fixed call labels, times, thread IDs, numeric handles, fixed test identities and API status values are recorded. Probe environment=None and sampler environment=NULL mean the OS inherits the environment within CreateProcess; a separate environment-block creation call does not exist in the parent path. CreatePipe was hooked but no probe/sampler pipe was created. stdout/stderr are DEVNULL for the probe; the sampler uses shared memory. Therefore stdout/stderr drains are not applicable to these workers. The diagnostic parent has ordinary console output; it is not used as a worker result pipe.

## 4–5. Slowest calls in valid follow-up

- Probe: `probe_timing.WaitForSingleObject`, **0.0429697s**; independent exit observation returned signaled, not a timeout.
- Sampler: `bounded_sampler.WaitForSingleObject`, **0.0405622s**, a 25ms wait request in the deliberately delayed query. It returned timeout as expected for that individual polling wait, not cleanup failure.
- Maximum probe CreateProcess: 0.0105634s.
- Maximum sampler CreateProcessW: 0.0072421s.
- One high-level span exceeded 2s: delayed `sampler.query_total` **2.0329322s**, comprising the unchanged two-second query deadline plus cleanup. It is not a single blocking Windows API call. Zero spans exceeded 5s; no hard process deadline or cleanup-bound violation reproduced.

Each elapsed call interval includes any thread descheduling while the call is in progress; it does not alone prove blocking inside the Windows implementation. Starts/ends use the existing QPC clock, with thread identities and raw requested wait durations. Last-error state, return values and exceptions are preserved by wrappers. No output text or credentials are logged.

## 6. Console helpers

Kernel sequence/creation-qualified evidence records **85 helpers**, one per probe/sampler worker, with parent sequences and creation/exit times. Latest helper creation was 0.0094207s after its parent began in this run. Probe helper timing remains relative to kernel process start/exit; unmodified whoami work boundaries are not visible. No helper is blamed for the historical delay. All 171 tracked kernel identities have exit proof: 149 retained-handle exits and 22 strictly qualified post-exit handle-acquisition cases. Kernel event/buffer loss and fault counters are zero.

## 7. Internal markers and explicit gaps

The **probe binary is unchanged**, SHA-256 `23240ef9f8b0a9a324110b1c2331de31dc1b0e08f5359cb707e51a939af56cd3`, still byte-identical to the preserved whoami copy. No injected DLL, debugger, replacement helper or speculative flag was used. Its true entry, runtime initialization, console initialization, security lookup, filesystem work and teardown markers remain **UNAVAILABLE**. Kernel helper creation cannot substitute for them.

Only the disposable sampler-worker source gained bounded shared-memory markers. All 72 markers are preserved. For three normal queries, earliest script markers appeared 0.0402508–0.0424623s after kernel start; imports took 0.0336191–0.0383156s. Query bodies took 0.0002077–0.0003234s. GlobalMemoryStatusEx, GetSystemTimes, serialization and result-mapping boundaries are individually recorded.

The earliest marker follows the Python loader and minimal tracing imports/mapping setup; it is **not the process's first instruction**. Script cleanup_begin/end are adjacent logical boundary markers with no explicit intervening cleanup, not measured interpreter/OS teardown. Atexit markers precede closing the diagnostic mapping; later runtime destruction remains uninstrumented. No fictitious console/security lookup stage is added where the sampler does not perform one. Missing end markers in intentionally terminated delayed/hung fixtures correctly remain missing.

## 8. Cleanup timings

Five sampler cleanup durations were 0.0102089–0.0106420s; every handle signaled, every Job reached zero active processes, and all handles closed. No cleanup observation timeout occurred. Maximum TerminateJobObject: 0.0000645s. Maximum QueryInformationJobObject: 0.0000218s. Final process-tree reconciliation: 0.0125214s.

Kernel observer requested shutdown, flush/stop/consumer results were zero, and launcher observed exit code 0 within 1.1748016s. This is aggregate shutdown observation; individual native ControlTrace/CloseTrace spans were not modified or separately measured. No CIM application observer was launched, so unsubscribe is not applicable. No new heartbeat acceptance claim is made. The preserved historical maximum remains 1.056s and no heartbeat limit changed.

## 9. Reproduction and preserved instrumentation failure

Attempt 1: 80 probes and five sampler cases completed without the original failures, but diagnostic output **FAILED** because the 200,000-record buffer overflowed by 13,206 records. Of the stored records, 193,553 were repetitive background Process32NextW enumeration calls. This failure is preserved at `D:\JARVIS-STAGE6-LIVE\1a88b8cd027343cdae56af2397cd6718\code\calltrace-b020605fa882408294968564be6249dc` and retains its failed status.

A narrow diagnostic-only correction in a second copy omits repetitive background per-process API spans, retaining whole-scan/discovery spans and all labelled launch/sampler/independent-observer calls. The 200,000 limit did not change. The original copy and run were not edited. The follow-up is `D:\JARVIS-STAGE6-LIVE\fb25b7f8e8ce47f2a3f8f24f09efdd70\code\calltrace-ef91d37690bb4ce59000827657778774`.

Follow-up: 20 idle probes + 60 under small synthetic D: hashing; three normal sampler queries, one intentionally delayed query, one cancellation. All completed. Maximum probe lifetimes: idle 0.0437210s; hashing 0.0403024s. **4,296 live-call spans plus one separately saved final-write span = 4,297 total**, zero overflow. No original >13.6s probe or cleanup-bound failure reproduced. No thresholds were increased. Both datasets are 58,720,256-byte newly generated sacrificial files, not protected VM data. Their bytes/metadata were verified unchanged; only their hashes are archived, not the bulk data.

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
