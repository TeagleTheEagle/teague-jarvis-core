# Stage 4 Electron GPU startup diagnosis — 2026-09-15

**DIAGNOSIS COMPLETE — STOP FOR REVIEW. No runtime correction implemented.**

The unchanged actual Electron probe fails in Codex's restricted Windows command context and passes in the host command context. The controlled comparison supports an **acceptance execution-environment compatibility issue**, not a demonstrated defect in JARVIS's response-commit boundary. The specific failing DLL/load restriction remains unidentified.

Production remains unchanged and blocked. The shared response-commit correction is frozen. No Stage 4 acceptance commit and no Stage 5.

## Observed comparison

| Run | Actual result | Client / Core exits |
|---|---|---|
| Original response-commit acceptance failure, `2f8a9d94206e48b4a59082b328539567` | Reconciliation passed; first Electron startup failed; no ready event or screenshot | Electron 2147483651; Core 0 |
| New unchanged probe in `use_default`, `7127c26343fb4250ab7e10ae1b2f57ca` | Same startup failure reproduced; six GPU subprocess failures | Electron 2147483651; Core 0 |
| New unchanged probe in host `require_escalated` context, `34f6fb7b049442e89d66dd7073b25ae4` | **29/29 checks passed; two screenshots captured and visually inspected** | All five client launches 0; Core 0 |
| Earlier controller checkpoint, `ba76c336d41c454ba35934626c336b80` | 29/29 passed | All five clients 0; Core 0 |

Complete case lists, hashes and original result paths are in `result-comparison.json`; unchanged copies are in `results/`. The new host run tested both authenticated real interfaces, shared Core identity and TEST conversations, foreign cancellation denial, reopening without request replay, renderer crash isolation, and separately authorized Core shutdown. It did not substitute a browser or mock renderer.

The successful screenshots show `STAGE4_TEST` authentication and explicitly unavailable physical voice/capture. They were captured before submitting the probe's request: they establish visible authenticated interfaces, not a screenshot of a final answer. The subsequent form-completion and ownership checks passed separately.

The later PASS does not erase either failed run. Only this existing Electron probe was rerun; no broader response-commit, Python or Stage 1–4 suite was rerun during diagnosis, and no overall Stage 4 acceptance claim is made.

## Exact executable and launch construction

- Electron package and executable product/file version: **44.2.0**. The successful running clients also returned `process.versions.electron = 44.2.0`. The failed client did not reach that report; its version is established from the same installed binary/package.
- Executable: `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\desktop\node_modules\electron\dist\electron.exe`
- Executable SHA-256: `07b043bf9b0a0ac14a82fac0b612b7b7ed13cde727d706d74e41a45278ab51f1`.
- Both commands, from `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis`:

```powershell
.venv\Scripts\python.exe -B tests/lifecycle_stage4/fixtures.py --electron-app-probe
```

The unchanged `electron_app_probe()` launches the existing local Node executable at `C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe`, using `-e` and its inline fork helper. That helper forks with Electron as `execPath` and the following source-derived argument arrays:

```text
<repo>\desktop\main.cjs --stage4-test --stage4-root=<fresh TEST root>
<repo>\intelligence\main.cjs --stage4-test --stage4-root=<same TEST root>
```

The original failure's exact TEST root is `tests\lifecycle_stage1\evidence\TEST-STAGE4-cdd43dab3cae416a8bf4c85dcc0d8d64`. The new restricted run uses `TEST-STAGE4-0aa457e028ad41789b774eb37ec80596`; the host run uses `TEST-STAGE4-2e25327be258447596a7c7805ca24810`, under the same evidence directory. Result JSON preserves all exact paths.

Working directory is inherited from the command above: neither Python's client `Popen` nor Node's `fork` overrides it. Python uses `close_fds=True`, `CREATE_NO_WINDOW` (0x08000000), piped stdin/stdout/stderr. Node uses `windowsHide:true` and `stdio:['ignore','pipe','pipe','ipc']`. The TEST configuration is transferred through the existing private parent channel; its credentials were not collected, printed or copied into evidence.

These are exact inspected launch constructions, not a captured OS command line for the short-lived GPU child. The attempted live sample ran after the host probe had exited and captured no processes. No GPU child PID, creation time, inherited handle list or complete Chromium subprocess switches were captured.

## Environment and sandbox comparison

`context-comparison.json` contains the selected nonsecret environment, token observations and their limits. The following allowed child environment values were **identical** between the current restricted and host commands:

`SYSTEMROOT`, `WINDIR`, `TEMP`, `TMP`, `USERPROFILE`, `APPDATA`, `LOCALAPPDATA`, `COMSPEC`, `PATH`.

`ELECTRON_RUN_AS_NODE`, `ELECTRON_NO_ATTACH_CONSOLE`, `ELECTRON_ENABLE_LOGGING`, `ELECTRON_ENABLE_STACK_DUMPING`, `NODE_OPTIONS`, and `CHROME_LOG_FILE` were unset in both sampled parent environments. The harness passes only its fixed allowlist, not arbitrary inherited provider credentials. Node can supply its own internal IPC environment; that child environment was not independently dumped.

The restricted command token includes `CodexSandboxUsers`; its read-only CIM query for its own process was denied. The host token lacks that group. Both token snapshots show **Medium** integrity; the host Administrators group is **deny-only**. Thus `require_escalated` here means leaving the Codex command sandbox for the host context, not evidence that Electron ran as an elevated administrator. Windows security settings, ACLs and Chromium security options were not altered. Full token restrictions/job-object internals were not collected.

The existing shared TEST client already calls `app.disableHardwareAcceleration()` and appends `disable-gpu`. **Both failing and passing runs used those existing settings unchanged.** Chromium still attempted a GPU subprocess in the failures. No new GPU or sandbox flags were introduced. BrowserWindow still uses `sandbox:true`, `contextIsolation:true`, `nodeIntegration:false`; the existing authenticated native bridge, TEST protocol restrictions and permission denials remain in place. Host command execution is separate from Chromium's renderer sandbox and the TEST Core's isolation guard.

Each invocation creates new isolated TEST profiles, and each client launch gets a new profile inside its TEST root. No old profile or cache was deleted, reset, reused or repaired. Random namespace/profile/credential values necessarily differ between runs. Persistent profile corruption is not supported as the explanation: both failing and passing invocations began with fresh profiles. A context-specific profile/crypto/permission interaction is not excluded.

## GPU error and startup stage

The original and reproduced restricted failures both record:

```text
os_crypt_win.cc:77: Failed to encrypt ... (0x2)
STAGE4_TEST configuration received
gpu_process_host.cc:1035: GPU process exited unexpectedly: exit_code=-1073741515
[six GPU subprocess exits in each failed run]
gpu_data_manager_impl_private.cc:417: GPU process isn't usable. Goodbye.
```

The installed Microsoft Windows SDK `10.0.26100.0/shared/ntstatus.h` identifies `0xC0000135` (unsigned interpretation of -1073741515) as **STATUS_DLL_NOT_FOUND** and `0x80000003` (2147483651) as **STATUS_BREAKPOINT**. Exact definitions and source lines are preserved in `installed-sdk-status-codes.json`. The first is evidence of a subprocess dependency/load failure status; the second accompanies Electron's fatal termination. Neither identifies the missing DLL, whether it was absent versus inaccessible in that context, or a defective graphics driver. No DLL was installed/replaced and no driver was changed.

The crypto warning occurs before the fatal GPU failure in both restricted runs. Its causal relationship is not established. The filtered Windows Application event query (IDs 1000/1001 around both failures) returned `NoMatchingEventsFound`; this supplies no missing-module name and does not exclude security-software involvement.

Precise startup conclusions:

| Question | Supported answer |
|---|---|
| Did Electron's main process start? | Yes. Its stderr identifies PID 23264 in the original and 18952 in the reproduction. These are historical observations, not cleanup authorizations. |
| Did JARVIS-specific code execute? | Yes. The TEST entry branch logged receipt of configuration. This was not a crash before all JARVIS code. |
| Was authentication reached? | The configuration handler proceeds toward native worker attachment, but it has no intermediate authentication-result record before readiness. No completed ready/attached event reached the harness. Whether authentication had internally completed before the fatal crash is **unconfirmed**. |
| Was a window created? | No window/readiness record or screenshot exists for the failed runs. Construction occurs after attachment and `app.whenReady()` in source. Absence of a ready event does not prove that no transient window was constructed. **Unconfirmed.** |
| Did JARVIS renderer code run? | No DOM/readiness evidence was received in the failed runs. Exact renderer execution boundary is **unconfirmed**; do not claim the crash definitely preceded all renderer JavaScript. |
| Did the host run reach all these stages? | Yes: both real renderers authenticated, actual DOM checks passed, windows were captured, request completion was exercised. |
| Did Core cleanup succeed? | Yes, every compared current Core exited 0. All five host client launches exited 0. Final read-only namespace process checks found no remaining matching processes; no force termination was used. |

## Earlier passing conditions

`historical-launch-comparison.json` proves the entire `electron_app_probe()` source is identical in the current fixture, the earlier controller-recovery snapshot, and the pre-response-correction snapshot (normalized function SHA-256 `4c2a2a6f7246b289cc623e2820202ce82441822c981dd90d43434f0e96bcef9e`). The current shared client is also byte-identical to the preserved pre-response-correction event-polling snapshot.

Earlier September 12 host-context logs document a different, later startup problem: clients were authenticated but visual capture failed with `UnknownVizError`, and window metadata recorded `visible:false`. A subsequent already-existing explicit `win.show()` after page load produced 29/29 checks and screenshots (`9a357eec71cb4c2da67c035e6573532e`). The current source retains that call. No new show/window correction was made in this diagnosis.

Those earlier logs are labelled host-context, but do not contain complete token/environment snapshots. Their exact historical Windows token cannot be reconstructed from a passing result alone. The newly recorded restricted/host pair supplies direct present-day comparison on frozen source. Hidden-window capture failure and fatal GPU subprocess startup are distinct observed failure stages.

## Cause / evidence → minimum proposal → validation → rollback

**Cause supported:** the existing Electron acceptance invocation is incompatible with the tested restricted Windows command context. The same executable, arguments, selected environment, working directory and frozen source run successfully in the host context. The specific loader/permission mechanism underneath STATUS_DLL_NOT_FOUND remains unconfirmed. Timing, fresh profile IDs and security context are not a controlled identification of an individual DLL or ACL.

**Minimum proposed correction:** make the actual Electron acceptance execution context explicit in its documented runner procedure: use the demonstrated host context for this existing isolated TEST probe. Preserve the unchanged authentication, browser sandbox, Core isolation, screenshots, lifecycle and request checks. Do not treat a Node-only/browser-only test as replacement evidence. No JARVIS runtime, GPU, driver or transaction-boundary correction is indicated by the present evidence.

**Files/configuration potentially affected after review:** acceptance invocation/documentation only, such as the run instructions in `docs/CANONICAL-CORE-STAGE-4.md` and the linked acceptance report. This proposal does not change those files now. No changes proposed to `stage4_client.cjs`, `desktop/main.cjs`, `intelligence/main.cjs`, `tests/lifecycle_stage4/fixtures.py`, Store, SQLite schema, Windows security, production configuration or launchers. No permanent sandbox bypass or global tool-setting change is proposed.

**Validation plan:** review and retain this failing/passing pair, both screenshots and frozen hashes; accept the host-context result only as evidence for this exact actual-Electron probe. When the Stage 4 critical path is resumed, run any further required actual Electron probes in that explicit host context against the final reviewed source, retaining their exact commands and results. Keep all other unresolved acceptance gates and required persistence/regression checks. A future GPU failure should stop the run and preserve stderr; it must not trigger automatic flag changes or cache deletion.

**Regression plan:** this diagnosis changes no executable source. The unchanged actual Electron lifecycle probe was the only test run twice for comparison. Broader previously outstanding response-commit/Stage 4 checks remain outstanding until separately resumed; this report does not silently close them. If subsequent source changes occur, validate the affected regressions against those new hashes.

**Rollback:** no runtime patch, schema change, security change or production operation exists to reverse. If the proposed runner documentation is later adopted, reversing that documentation/invocation choice is sufficient; retain all evidence and do not delete profiles or roll back databases. Returning to the restricted command context should not be represented as a remedy—it reproduced the failure.

**Review requested:** accept the explicit host-context execution procedure for actual Electron TEST acceptance and its evidence, while leaving the response-commit implementation frozen until the existing Stage 4 work is resumed. No request to weaken security, activate production or begin Stage 5.

## Evidence preservation and boundaries

`frozen-source-after.json` verifies all 12 files in the response-correction source manifest unchanged from their reviewed hashes. `launch-source-after.json` verifies the eight sampled launch/executable files unchanged through diagnosis. The repository already contained unrelated edits; none was reset or committed. Newly generated files are diagnosis records and isolated TEST run artifacts only.

The selected archive includes result JSON, stderr, command records, nonsecret context comparison, SDK definitions, source hashes and the two inspected screenshots. Original TEST databases, credentials, handshake files, Electron profiles, binaries and raw account-group snapshots remain excluded. `manifest.json` and the separate copy verification record cover the selected files. Minor diagnostic-read/bookkeeping errors and missed live-process sampling are recorded in `diagnostic-observation-limitations.json`; none is counted as a runtime PASS.

The original historical Stage 1 PermissionError remains root-cause unconfirmed. Its later reproduced response-publication defect, the challenge/response IPC contention correction, and the earlier Windows memory-access crash remain separate findings. This GPU diagnosis establishes no common cause with any of them.

PRODUCTION FILES / DATA / CONFIGURATION CHANGED: NO  
PRODUCTION CORE RESTARTED: NO  
RESPONSE-COMMIT SOURCE CHANGED: NO  
GPU FLAGS / SECURITY SETTINGS CHANGED: NO  
PAID PROVIDER CALLS / PHYSICAL MEDIA: NO  
STAGE 4 ACCEPTANCE COMMIT: NONE  
STAGE 5 STARTED: NO

**STOP FOR REVIEW.**
