# Stage 6 native control-probe isolation experiment

**FINAL STATUS: BLOCKED.** Two diagnostic runs completed measurement collection; the C: read run failed monitor finalization with **Queue residue/count mismatch**. No further load, acceptance or dry run was executed. All observed process handles are reconciled and no diagnostic process remains.

Partial result classification: **GENERAL_PROCESS_RUNTIME_DELAY**, limited to observed multisecond delay before the earliest marker in a native arithmetic helper. This is evidence against a whoami-only explanation for every multisecond delay; it does not prove that the original >5-second incidents have the same cause. Underlying Windows cause remains **UNCONFIRMED**.

## Blocking evidence and ordering

Failed run: `D:\JARVIS-STAGE6-LIVE\90e9469000dd4530a86b98fad67d7089\code\reads1-13f55e1dce534d32a76888fc594bb4c3`.

Monitor PID **6128**, creation FILETIME **134343453938649012**, exited **1**. Collector/workload completed, workload exit **0**, resource sampler exit **0**, all **133** retained probe handles signaled with actual exit code **0**. Last probe PID **12872**, creation FILETIME **134343455457819048**, exit FILETIME **134343455457997850**, lifetime **0.0178802 s**; this was **A_D**, not a timed-out probe.

The monitor's final drain returned with backlog zero at QPC **1782780190023**. The STOP event then enqueued at QPC **1782780302870**, **0.0112847 s later**, during final process enumeration (**0.1144022 s**). Reconcile subsequently found one unpersisted queue entry. Queue statistics: **266 enqueued; 265 selected/persisted/removed; 1 remaining**. The missing canonical event is STOP for PID 12872, queue sequence **266**, external EventIdentifier **264**. It remains recorded in `pipeline.json` as `preunsubscribe.pending` and `teardown.discard`, and in queue/tap sidecars; it is absent from canonical `events.jsonl`. The name `teardown.discard` is an existing trace label, not evidence that this pass deliberately deleted the event. The original source intentionally leaves pending entries intact during teardown.

This is an observed finalization ordering gap: producers can enqueue after the final Drain and before Reconcile. It is not evidence that the validated EventIdentifier reference/removal correction deleted a sibling event. The monitor and queue files are byte-identical to their previously validated sources. The fail-closed rejection is correct; the finalization procedure did not satisfy complete event persistence. No successful monitor-result/durable-finalization receipt exists for this run, and none has been manufactured.

## 1. Current probe implementation (N1)

`D:\JARVIS-STAGE6-LIVE\90e9469000dd4530a86b98fad67d7089\code\J6Probe.exe`, SHA-256 `23240ef9f8b0a9a324110b1c2331de31dc1b0e08f5359cb707e51a939af56cd3`, is the existing byte-identical whoami copy from the previous diagnostic workspace. **Whoami is the probe itself**: not a child command and not the collector's peer/identity-verification mechanism. No fresh copy was taken from protected Windows files. It runs with no arguments, working directory `D:\JARVIS-STAGE6-LIVE\90e9469000dd4530a86b98fad67d7089\code`, stdout/stderr DEVNULL, CREATE_NO_WINDOW and close_fds=True. Parent Python collector PID, CreateProcess arguments, creation identity and handle evidence appear in every raw probe row. Parent validation uses kernel process times/retained handles independently of whoami output.

The environment is inherited with process-local TEMP/TMP routed to the run's D: temp directory. `environment-policy.json` records nonsecret SystemRoot/ComSpec/architecture values and explicitly omits other values to avoid credential disclosure. No .env or secrets were opened or copied. The inherited environment was not reduced to a new acceptance configuration.

Whoami's intended work is a user-identity query and output, discarded here. Prior PE imports include token/SID/account and LSA functions, resource/localization and output functions; import presence does not establish the actual path. Its internal filesystem/security calls or child-process absence were not proven by this process-name-filtered monitor. The helper source has no child-process or filesystem operations. No claim is made that the Windows loader performs no filesystem work.

## 2. Controls (N2)

- **A:** minimal native entry, timing markers, immediate exit. No external work beyond the diagnostic mapping/timer and normal process initialization/exit.
- **B:** same helper executable, 10,000 bounded unsigned arithmetic iterations, with a checked result. No identity query.
- **C:** unchanged existing whoami-equivalent probe, no internal markers.
- **D:** alternate native identity mechanism: OpenProcessToken(TOKEN_QUERY) and GetTokenInformation(TokenUser) into temporary process memory. No SID/name translation, domain lookup, exported token data or displayed identity. Memory and token handle are released before exit.

Helpers are CRT-free native C executables built using installed MSVC 14.44.35207 and Windows SDK 10.0.26100.0. A/B import only Kernel32; D additionally imports ADVAPI32 for the two documented calls. No interpreter, explicit sleep, disk I/O, subprocess, console I/O, retry loop or provider is in helper source. Build commands, exact source, PE imports and hashes are preserved. ASLR, NX and CET-compatible linking remain enabled; no host security setting was changed.

One build failure is preserved: private macro TOKEN_CONTROL collided with a Windows SDK definition. It was renamed J6_TOKEN_CONTROL before any experiment. `build-evidence.json`, `before-build-fix/` and `build-retry-evidence.json` preserve the failure and successful build. This was diagnostic build wiring, not a runtime/security correction.

## 3. Locations and exact command forms (N3)

**D image root:** `D:\JARVIS-STAGE6-LIVE\90e9469000dd4530a86b98fad67d7089\code`. **C image root:** `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-native-control-20260920\images`.

`J6ProbeNative.exe 0 <inherited-marker-handle-hex>` is A; mode `1` is B. `J6ProbeToken.exe 2 <inherited-marker-handle-hex>` is D. C is `J6Probe.exe` with no arguments. The handle is an ephemeral anonymous mapping handle, not a credential; only the explicitly listed handle is passed to the helper. Actual arguments are recorded per invocation.

A_C/A_D, B_C/B_D and D_C/D_D use byte-identical C/D images, checked before and after. C_D uses the pre-existing D whoami copy; whoami was not recopied to C or modified. All working directories and live control/evidence/temp paths remain D:. The C image copies are deliberate location controls, not live logging paths. Installed DLLs, Python, PowerShell and OS-managed paging/security activity can still involve C:.

The native markers use a 4096-byte anonymous, non-executable shared mapping rather than a filesystem marker file. Windows backs this kind of mapping with system paging; this does **not** prove independence from OS-managed paging/storage. [Microsoft mapping semantics](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createfilemappinga). Mapping views and handles are released following retained-handle exit confirmation.

## 4. Idle distributions (N5)

144 probes, all exit code 0, all START/STOP persisted, no timeout. Counts are 20–21 per variant. One idle C-resident A probe reached 0.162 s; this is preserved. Full lifetime and creation distributions appear below and in `control-summary.json`.

## 5. C: read distributions (N6)

133 probes, 19 per variant, all exit code 0 and zero timeouts. Collection completed but monitor finalization **FAILED**; these observations are partial diagnostic evidence, not successful acceptance. B_D reached **3.3124412 s**, D_D **2.8058982 s**, C_D **4.1213346 s**. A variants and C-resident helpers did not show multisecond lifetimes in this sample. This is not evidence of a guaranteed bound for those variants.

| Condition/control | N | Min / median / p95 / max lifetime (seconds) | >1 / >3 / >5 s | Timeouts |
|---|---|---|---|---|
| idle/A_D | 21 | 0.017508 / 0.018195 / 0.022023 / 0.025355 | 0 / 0 / 0 | 0 |
| idle/A_C | 21 | 0.017938 / 0.018588 / 0.023151 / 0.162113 | 0 / 0 / 0 | 0 |
| idle/B_D | 21 | 0.017034 / 0.017785 / 0.020064 / 0.020853 | 0 / 0 / 0 | 0 |
| idle/B_C | 21 | 0.017239 / 0.017838 / 0.018585 / 0.019617 | 0 / 0 / 0 | 0 |
| idle/D_D | 20 | 0.018393 / 0.019489 / 0.022156 / 0.026924 | 0 / 0 / 0 | 0 |
| idle/D_C | 20 | 0.018240 / 0.019119 / 0.020814 / 0.023225 | 0 / 0 / 0 | 0 |
| idle/C_D | 20 | 0.020889 / 0.022323 / 0.024888 / 0.026488 | 0 / 0 / 0 | 0 |
| disk/A_D | 19 | 0.017493 / 0.018262 / not meaningful / 0.025732 | 0 / 0 / 0 | 0 |
| disk/A_C | 19 | 0.017617 / 0.018168 / not meaningful / 0.019271 | 0 / 0 / 0 | 0 |
| disk/B_D | 19 | 0.017370 / 0.018052 / not meaningful / 3.312441 | 1 / 1 / 0 | 0 |
| disk/B_C | 19 | 0.017189 / 0.018128 / not meaningful / 0.022003 | 0 / 0 / 0 | 0 |
| disk/D_D | 19 | 0.018282 / 0.019181 / not meaningful / 2.805898 | 2 / 0 / 0 | 0 |
| disk/D_C | 19 | 0.018545 / 0.019177 / not meaningful / 0.022436 | 0 / 0 / 0 | 0 |
| disk/C_D | 19 | 0.021289 / 0.022283 / not meaningful / 4.121335 | 1 / 1 / 0 | 0 |


Percentiles use linear interpolation. p95 is withheld below n=20; p99 is withheld below n=100. **No per-control p99 is meaningful in this interrupted experiment.** The planned second baseline/read runs were not performed. Sequential interleaving rotated the starting variant between cases but was not randomized; small samples, loader-cache history and unrelated background activity remain limitations.

## 6. C: hashing (N7)

**NOT RUN.** Stopped on monitor finalization failure before this condition. Prior whoami results remain historical evidence only and are not substituted for the missing native comparison.

## 7. D: hashing (N8)

**NOT RUN.** The planned clean comparison remains outstanding. No five-workload acceptance or protected hashing was performed.

## 8. CreateProcess comparison

| Condition/control | CreateProcess median / max ms | Entry estimate max s | Work max microseconds | Exit tail estimate max ms | Observer estimate max ms |
|---|---|---|---|---|---|
| idle/A_D | 5.066 / 699.567 | 0.025217 | 0.100 | 0.148 | 1.110 |
| idle/A_C | 5.353 / 24.972 | 0.161925 | 0.100 | 0.178 | 0.966 |
| idle/B_D | 4.795 / 5.657 | 0.020713 | 10.300 | 0.161 | 0.900 |
| idle/B_C | 4.920 / 5.332 | 0.019474 | 10.600 | 0.132 | 0.954 |
| idle/D_D | 5.110 / 654.569 | 0.026744 | 7.700 | 0.341 | 1.083 |
| idle/D_C | 5.161 / 24.573 | 0.023068 | 7.000 | 0.164 | 1.235 |
| idle/C_D | 2.603 / 19.470 | unobserved | unobserved | unobserved | 1.912 |
| disk/A_D | 5.046 / 7.396 | 0.025429 | 0.100 | 0.289 | 1.136 |
| disk/A_C | 5.214 / 5.526 | 0.019138 | 0.100 | 0.142 | 0.860 |
| disk/B_D | 4.827 / 5.518 | 3.312315 | 10.100 | 0.131 | 0.950 |
| disk/B_C | 4.928 / 8.547 | 0.021876 | 9.800 | 0.160 | 0.863 |
| disk/D_D | 5.017 / 5.593 | 2.805733 | 7.700 | 0.272 | 1.322 |
| disk/D_C | 5.240 / 5.969 | 0.022259 | 7.100 | 0.300 | 1.291 |
| disk/C_D | 2.612 / 4.850 | unobserved | unobserved | unobserved | 1.682 |


First-launch idle CreateProcess calls reached **0.699567 s** (A_D) and **0.654569 s** (D_D), although their kernel lifetimes were short. No scan/loader explanation is claimed for this observation. For the slow C-read B_D probe, CreateProcess took **0.005327 s**. Its 3.312-s lifetime was not spent inside that API call.

## 9. Runtime/entry comparison (N4/N10)

B_D PID **18592**: kernel lifetime **3.3124412 s**; creation-to-earliest-entry-marker estimate **3.3123149 s**; CreateProcess-return-to-marker **3.3074854 s**; marker setup **9.5 microseconds**; arithmetic **9.7 microseconds**; exit-tail estimate **0.1071 ms**.

D_D PID **22068**: lifetime **2.8058982 s**; creation-to-entry estimate **2.8057326 s**; token query **6.6 microseconds**. A second D_D delay was **2.7554347 s**, again before its entry marker. These delays occurred before the intended arithmetic/token work, not during the measured body. `slow-controls.json` records all slow observations, including first-launch creation delays.

T0 launch request, T1 CreateProcess return, T2 Popen handle available, T3 earliest helper QPC, T4 work begin, T5 work complete, T6 immediately before unmap/close/ExitProcess and T8 independent exit observation are recorded. T3 is an earliest observable helper marker, not the literal first machine instruction. Normal loader initialization, scheduling and the initial timer call precede that observable boundary. Exact T7 kernel signaling instant is not directly observed; kernel FILETIME exit plus UTC/QPC bridges provide an estimate with recorded bridge uncertainty. A child may start before the parent returns from CreateProcess; no invalid universal ordering is assumed.

## 10. Exit-observation comparison

The slow B_D observer lag estimate was **0.6608 ms**; D_D delays had roughly **0.94–1.03 ms** observer lag. This supports real process-lifetime inflation rather than delayed collector observation for those cases. Every retained handle was signaled at final reconciliation, every actual exit code was 0. T3–T6 remain unobserved for C_D/whoami. Small exit estimates depend on clock bridge uncertainty and must not be interpreted as exact kernel signaling timestamps.

## 11. Whoami-specific findings (N9)

Whoami reached 4.121 s during C reads but was not the only delayed executable. Therefore a correction premised on identity-query work being the sole cause is **not supported**. The experiment does not isolate whoami's SID/name translation, LSA, localization or output substages. No ETW tracing or security change was performed. Further whoami internals are not the immediate critical path while native pre-entry delays and finalization failure remain.

## 12. Native findings and next instrumentation (N10)

Non-identity arithmetic helper delays refute a whoami-only account of all observed multisecond inflation. However, **no new probe exceeded five seconds**, and C/D hashing conditions are absent. The result does not prove the internal cause of the previous >5-second events or a problem with every Windows process.

If authorized after the finalization gate is repaired, a narrowly bounded trace could correlate these known helper/collector identities with process/image loading, thread scheduling and relevant I/O over a short reproduction, writing only to D:. Exact provider/filter/stack scope should be reviewed before execution; machine-wide security tracing or claims of perfect PID filtering are not implied. Defender, code integrity, filesystem filters and scheduler explanations remain hypotheses. No security control should be disabled for the comparison.

## 13. Timeout provenance (N11)

**LOCALLY_CHOSEN_TEST_LIMIT.** Earliest located literal remains `docs/stage6-heartbeat-journal-20260918/dryrun.py:56`, `p.wait(timeout=5)`. No inspected rationale establishes a Windows process completion guarantee. It is nevertheless an explicit current owner requirement and remains unchanged. The Windows Python implementation calls WaitForSingleObject with 5000 ms after Popen/identity acquisition; creation time already elapsed is excluded. The separate 15-second retained-handle diagnostic observer does not authorize a longer successful probe lifetime or convert a timeout into success.

## 14. Strongest supported cause/classification (N12)

Partial category: **GENERAL_PROCESS_RUNTIME_DELAY**, specifically pre-earliest-helper-marker inflation in a native control without identity work. Not WHOAMI_SPECIFIC_DELAY, not proven C_VOLUME_IMAGE_LOAD_DELAY, SECURITY_IDENTITY_LOOKUP_DELAY, SECURITY_SCANNING_DELAY or SCHEDULING_DELAY. The delays observed here occurred in D-resident helpers; the small C sample did not show them, but that is insufficient to attribute causation to D placement. Overall experiment status remains **BLOCKED** by finalization, not completed root-cause identification.

## 15. Minimum proposal (N13)

Do **not** replace whoami or increase the five-second limit on this evidence. First request a separate narrow review of monitor finalization: replace the fixed-grace/last-drain assumption with a bounded, explicit lifecycle-completeness and producer-quiescence handoff before durable finalization. It must reconcile every expected retained-handle-confirmed STOP, preserve exact queue-entry semantics, fail closed at the existing approved deadline, and prevent enqueues from escaping between the final drain and the sealed evidence state. Merely adding another sleep or uncoordinated Drain would not establish that invariant.

Likely affected file is the diagnostic `monitor.ps1` finalization block and focused diagnostic tests; the EventIdentifier removal algorithm should remain unchanged. Test late STOP arrival after drain/during final enumeration, simultaneous final enqueue, missing STOP, bounded deadline, evidence failure, duplicate identity and unchanged collision tests. This is a **proposal only**. No finalization correction is authorized/implemented in this experiment. Once reviewed and validated, resume the missing comparison conditions without erasing these failures.

## 16. Uncertainty and preserved failures

Historical 6.052-s internal cause: **UNCONFIRMED**. Windows/filesystem/driver/security cause: **UNCONFIRMED**. Historical Stage 1 cause: **UNCONFIRMED**. The new finalization sequence is independently observable and must not be conflated with old probe/heartbeat stalls. No event-loss cause in a Windows provider is established: the pending STOP reached the local queue and was preserved in sidecars, but missed canonical persistence before failure.

Preserved: initial token-helper compile failure and original source/image; all successful/failed raw runs; failed monitor stack; queue residue, tap and pipeline records; original earlier archive hash. No failures were retried away or reclassified as PASS.

## 17. D workspace/regression integrity

All acceptance-critical live artifacts remain in `D:\JARVIS-STAGE6-LIVE\90e9469000dd4530a86b98fad67d7089\code` and its unique run directories. Helper executable C copies are an explicitly approved independent variable. No .env, credentials or production state enter the workspace. Frozen **24** diagnostic files and **18** prior source files were verified: no drift/prior modification. C/D helper executable hashes match. The copied monitor, journal/Reader, queue, event tap, workload and workspace implementations remain unchanged.

The earlier 69/69 relocation regressions are preserved prior evidence, not rerun results for this incomplete experiment. Current live heartbeat/path observations do not override the failed finalization. No additional monitored experiment was launched after the failure.

## 18. Heartbeat status

Idle maximum interval **1.2067322 s**, age **1.1820508 s**. C-read maximum interval **1.0759111 s**, age **1.0737948 s**. Both stayed below unchanged **10 s**. Longest observed live D File.AppendAllText: **0.2091705 s** idle and **0.0673389 s** C reads. Healthy heartbeats did not guarantee complete finalization.

## 19. START/STOP and cleanup

Idle: **144 START / 144 STOP persisted**, complete. C reads: **133 START / 132 STOP persisted**; **one STOP pending in preserved queue/pipeline evidence**. Combined canonical totals: **277 START / 276 STOP**; **277 actual process exits confirmed**. Do not count the pending sidecar STOP as a successfully persisted canonical event.

Final **280** PID+creation-time checks found zero live/unconfirmed recorded identities. Final host snapshot: zero J6Probe*, zero workspace processes, zero VirtualBox processes; VBoxSDS stopped. No forced cleanup or unrelated termination occurred. All known probe/workload/resource processes exited; monitor exited 1 for the recorded failure.

## 20. EventIdentifier integrity

Prior **222 assertions / 10,000-event collision stress PASS** is retained, with unchanged queue source. It was not rerun after the finalization stop. Current observed external collisions: idle 3, C reads 2; internal queue-ID collisions **0**. Exact reference queue preserved the late STOP as sequence 266. Reconciliation detected it; no collision-fix regression is demonstrated by this failure.

## 21. Protected VM/configuration

**NOT ACCESSED.** No protected files opened, hashed, copied, normalized or inspected. No VBoxManage, VM boot, registration or protected baseline work. Only the existing synthetic large.bin was used for C reads. Process-name monitoring and service-status queries did not open VM/configuration files. No fresh protected-integrity baseline is claimed.

## 22. Production and changed diagnostic files

**Production unchanged.** No JARVIS runtime, configuration, credentials, data, provider, security setting or accepted source modification. No paid/live calls. No install, driver change, ACL/UAC/Defender/firewall/execution-policy change.

New diagnostic copies only: native_probe.c, controls.py, controls-config.json, control_analysis.py; instrumented copies of probe_timing.py (args/explicit handle-list support), collect.py (round-robin selection), launch.ps1 (offset/analysis); two new native helper images on C/D. Evidence/build/reconciliation scripts remain under this report root. Pre/post hashes, all source and exact diff are included. Rollback is to leave this diagnostic candidate unused, keep previous source, and retain evidence; nothing was deployed to production.

## 23. Protected-baseline eligibility

**NOT AUTHORIZED / NOT JUSTIFIED.** No acceptance repetitions, final five-workload acceptance, dry runs or protected hashing occurred. Planned C hashing, D hashing and repeat idle/read/hash cases: **NOT RUN** after the monitor failure. No acceptance commit or later Core stage.

## 24. Evidence and archive verification

Report root: `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-native-control-20260920`. Live source/evidence: `D:\JARVIS-STAGE6-LIVE\90e9469000dd4530a86b98fad67d7089\code`. Canonical archive: `C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 NATIVE CONTROL DIAGNOSIS 20260920`. `archive-verification.json` records final member count and ZIP/manifest hashes after copy verification. Archival preserves a failed experiment; it does not supply the missing monitor durability/completeness receipt.

Executed monitored commands used installed PowerShell 7, `-NoProfile -File <D code>\launch.ps1` with `(Mode idle, Duration 150, Label idle1, Offset 0)` and `(Mode disk, Duration 150, Label reads1, Offset 1)`. Each used a fresh approved UAC read-only monitor. No other planned monitored case ran. Offline `reconcile_blocked.py` reads retained evidence and checks identities; it does not fill the missing event or rewrite runtime evidence. The ordinary analyzer was correctly not run on the failed case by the launcher; separate post-stop analysis is explicitly marked partial.

Final: **BLOCKED — monitor finalization review required before resuming the experiment.**
