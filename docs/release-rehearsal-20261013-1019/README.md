# Release 1.0.19 (OpenRouter only): build and checks on this PC (2026-10-13)

Build **1.0.19-629bb5621d34** (commit 629bb56 on branch `claude/release-1.0.19`, which starts from 1.0.18's commit
cffb826 and so carries the time fix). The owner's decision of 2026-10-13: one AI service, OpenRouter, with Qwen models
only, and Fish Audio for the voice; OpenAI, Qwen through Alibaba Cloud and Brave removed (`release-notes.json`, the
1.0.19 entry). 1.0.18 was approved for its Stage 7 check on 2026-10-10 but never checked in the VM and never installed;
1.0.19 supersedes it. The owner's everyday JARVIS is 1.0.17-0d38218c4e1d, so every update check here is 1.0.17 -> 1.0.19.

Everything below ran on this PC in sandboxes under D:\JARVIS-release-work; the owner's installed JARVIS (1.0.17, running
throughout) and his Desktop and Startup shortcuts were never addressed and are recorded unchanged where the script looks.

## The build (15:25 local)

`tools/build_release.py --version 1.0.19`: 10,766 files; zip `JARVIS-1.0.19-629bb5621d34.zip`, 533,398,008 bytes, sha256
`838371836d31758082d191738ebc3b41d0e34fe4b6598af6153d970ab8b21541`; record `JARVIS-1.0.19-629bb5621d34.release.json`.

## Comparison with 1.0.18 (`JARVIS-1.0.19-629bb5621d34.compare-1.0.18.json`)

10,768 files before, 10,766 after: 0 added, 2 removed (`app/wearables/diagnose_openai.py`, the old OpenAI diagnostic,
and its bytecode), 19 shipped source files changed, all of them the files of the provider change (`providers.py`,
`connection_checks.py`, `server.py`, `actions.py`, `development.py`, `store.py`, `voice_engine.py`, `wearables/service.py`,
`verify_repair_sandbox.py`, `static/app.js`, `static/dashboard-model.js`, `static/index.html`, `static/reliability.js`,
`static/voice-preview.js`, `env.template`, `API.md`, `CLAUDE.md`, `README.md`, `release-notes.json`). Python, its packages,
the models and Electron are the same pinned parts; `JARVIS.exe` and its `package.json` differ only in the version they
carry. Four Microsoft C++ runtime files (`msvcp140.dll`, `msvcp140_1.dll`, `msvcp140_2.dll`, `concrt140.dll`) are version
14.51 where 1.0.18's were 14.50: the build copies them from Windows itself, and a Visual C++ runtime update was installed
on this PC on 11 October; the copies equal Windows' own files. The release regression below ran on these files.

Against 1.0.17 (git, 0d38218..629bb56, the program only): the 1.0.18 time fix in `server.py` plus the files above.

## Release regression: PASS (`regression-1.0.19.output.txt`, `regression-1.0.19/`)

`tools/release_regression.py` on a byte-identical copy of the release with the release's own Python and Electron
(`JARVIS.exe` as node), 16:12 to 16:37 local, run alone: **750 Python tests OK (skipped=7, by their own conditions; the
same 7 as for 1.0.18), 60 desktop, 18 Intelligence, 26 interface scripts; every suite PASS; the release verified unchanged
before and after** (`regression-report.json`: `"passed": true`). Two earlier starts of the same run (15:30 and 15:51) were
cut off when the chat session was interrupted and gave no result; the build was not changed between them.

## The Setup (`JARVIS-Setup-1.0.19-629bb5621d34.setup.json`, `setup-1.0.19.log.txt`)

`tools/setup/build_setup.py` with Inno Setup 6.7.3 (ISCC sha256 `0a875703…`, as for 1.0.17 and 1.0.18) from this package,
16:47 to 16:49 local, 148.4 s: `JARVIS-Setup-1.0.19-629bb5621d34.exe`, 406,914,757 bytes, sha256
`8e5bb3dceef85fc486f3d03b3864dfa3479c8833ffe471646cdd33dbcc36092f`; the template unchanged (sha256 `82c2d322…`);
unsigned (decision D3); both application ids as before.

## Zip install: PASS (`zip_install_rehearsal_v2-1.0.19-629bb5621d34.output.txt`)

The zip against its record, extracted, `install.cmd` into a sandbox home on D: (the shortcuts withheld, no launcher
script), launched through `releases\1.0.19-629bb5621d34\electron\JARVIS.exe` (the Core answering in 18.7 s, 8 processes:
`JARVIS.exe` and `python.exe`), verified after use, uninstalled: all 10,766 program files removed, data, config and
profile kept, 0 JARVIS processes left.

## The Setup rehearsal, version 2: PASS (`setup-rehearsal-v2-1.0.19/setup-rehearsal-v2.json`, `...output.txt`)

`docs/release-rehearsal-20261007-1017/rehearse-setup-v2.ps1`, 16:52 to 16:57 local. The owner's real Desktop and Startup
`JARVIS.lnk` carry the same sha256 before, after every step and at the end (desktop `7dca2506…`, startup `f8675687…`, the
shortcuts at 1.0.17's `JARVIS.exe`); the Installed-apps entry absent before and after; the live JARVIS's processes the
same before and after. The silent install with `/DIR`, `/HOME` and `/NOSHORTCUTS` in 83.8 s (inside: verify package
8.1 s, copy 11.9 s, verify copy 8.0 s, switch 0.2 s; `withheld`); the program, the package release and the uninstaller
present, no `JARVIS.ps1`; `JARVIS.exe` started (the Core up in 21 s) and shut down cleanly (0 left); the reinstall in
66.6 s; the uninstall through the entry's own uninstaller in 12.2 s: 10,766 program files removed, data kept.

## `pkg-1.0.19` (16:58)

`D:\JARVIS-release-work\pkg-1.0.19` holds the zip, its record, the Setup and its record, read back equal to the records
(zip `83837183…`, Setup `8e5bb3dc…`; the Setup's record names the same package).

## Stage 7 pass in a sandbox, 1.0.17 -> 1.0.19, version 4 scripts: ALL PASSED (`stage7-local-1.0.19/`)

`docs/release-rehearsal-20261007-1017/rehearse-stage7-release-v4.ps1 -Package D:\JARVIS-release-work\pkg-1.0.19
-PreviousPackage D:\JARVIS-release-work\pkg-1.0.17 -Base D:\JARVIS-release-work\stage7-local-1.0.19`, 16:58 to 17:14
local, nothing else running. **ALL STAGE 7 STEPS PASSED for 1.0.19-629bb5621d34**: 56 PASS check records across the
five phases and the restart check (the driver's four starts each said what it must: "The install step PASSED", "Windows
has not been restarted since the install step", "ALL STAGE 7 STEPS PASSED" twice), then the cleanup through the sandbox
entry's own uninstaller (18.5 s; 21,534 program files of the two releases removed, data kept, entry gone, package folder
gone, `clean: true`). Install from the Setup 71.5 s wall; uninstall 12 s and reinstall 71.1 s wall; 1.0.17 installed and
updated to 1.0.19 while running 73.2 s wall, rollback 13 s, update again 33.8 s wall, one update through the Setup 67.3 s
wall; the interrupted update's rerun 34.1 s wall. Every lap far inside the Gate 20 bound. The driver needed no change;
the owner's real shortcuts and his running JARVIS untouched (`rehearsal-summary.json`).

## Stage 7 check in the test VM: STAGE_7_COMPLETE, 29 of 29 (2026-10-13, 17:34 to 19:41 local)

The owner approved the check at 17:20 ("I approve the Stage 7 check of 1.0.19";
`governance/STAGE7-1.0.19-APPROVAL-RECORD.json`), built the disc at 17:26 (`stage7-disc-1.0.19-629bb5621d34.json`: zip,
Setup and the three guest files hash-equal to the approval, every payload file read back, the copy in media hash-equal),
started the VM at 17:29 from FRESH-PREREQ with both discs, and ran `stage7` twice. Every phase passed in the VM
(guest `stage7-driver-log.jsonl`: Install 18:01, AfterRestart 18:17, Uninstall 18:25, Update 19:18, Interrupt 19:38, then
"all phases passed"); 28 PASS records plus the restart decided from Windows' own boot id (7 -> 10). The snapshot
**STAGE7-PASS-1.0.19-629bb5621d34** (`9c81ad38-310e-46f1-b79a-a99de5934ca6`) was taken at 19:41 after a clean shutdown,
all nine earlier snapshots kept; the `.vbox` file read at the evaluation: that snapshot current, `currentStateModified`
false. Timings on the installer's own laps, all inside the Gate 20 bound: first install 539.6 s (Setup wall 753.9 s),
reinstall 179.8 s, update 537.7 s, rollback 119.4 s wall, update again 300.9 s, update through the Setup 162.0 s,
update after the interruption 401.8 s, every stop under 8 s; no disposition needed (1.0.17's check needed one). One
note, as in 1.0.17's check: 4 processes at the login launch, 8 at every other. The evaluation
`docs/stage7-1.0.19-evidence/stage7-evaluation.json` (schema v2), the host and guest manifests and the records are
copied under `docs/stage7-1.0.19-evidence/` (the Inno Setup logs stay on D:). Evaluated from the records on D: only; no
VirtualBox command run by Hermes.

## Not yet

The update of the owner's everyday JARVIS from 1.0.17 to 1.0.19 (his separate decision; `docs/UPDATE-EVERYDAY-1.0.19.md`
for approval, through the Setup). Before it: his key file must hold `OPENROUTER_API_KEY` (1.0.19) and keep the old
provider lines while a rollback to 1.0.17 is still wanted.

## The everyday update's launcher (version 3), rehearsed: run 3, 37 of 37 (2026-10-13, 20:31 to 20:37 local)

`rehearse-everyday-update-1019.ps1` runs `tools/host/update-1.0.19/Invoke-EverydayUpdate.ps1` in a sandbox on D: that
mirrors the owner's PC (1.0.17 installed by its own Setup with the sandbox switches, the sandbox entry and package
folder, a planted key file with fake values). Run 3 is on the launcher after its independent review (2 high, 6
medium, 8 low; `docs/UPDATE-EVERYDAY-1.0.19.md`, section "Independent review"): records in `update-rehearsal-3/`
(the summary, the output, the launcher's records; the fake key value appears in none, checked). Run 2 (before the
review, 32 of 32, `D:\JARVIS-release-work\update-rehearsal-1.0.19-2\`) and run 1 (a harness defect, nothing of the
update ran) stay on D:.
