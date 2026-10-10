# Release 1.0.18, the time fix: build and checks on this PC (2026-10-10)

Owner, 2026-10-10 evening: "keep friday as he is, 1.0.18 time fix only". Release 1.0.18 is one fix on top of the
installed 1.0.17-0d38218c4e1d: the Core's own answer to "what time is it", "time", "date" and "what is the date" is a
sentence (`It's 2:36 PM on Saturday 10 October 2026.`) instead of the raw ISO reading Siri read out (the Mac's round 6,
request 8). Record of the change and its review: `docs/RELEASE-1.0.18.md` on branch `claude/release-1.0.18`. Two
earlier builds called 1.0.18 (the Workshop, never offered) are recorded in `docs/release-rehearsal-20261010-1018/`; this
build's folders carry `-time` or its own release id.

The source is the worktree `D:\JARVIS-release-work\src-1.0.18` on branch `claude/release-1.0.18` (from 0d38218), release
commit **cffb826**. The owner's installed JARVIS (`%LOCALAPPDATA%\JARVIS`, 1.0.17, running) was never addressed.

## The worktree, made like the repo (2026-10-10, 20:00 to 20:40)

The worktree has no `.venv` and shares the repo's large folders. Two findings before the suites could pass there, both
about the worktree, not about JARVIS:

- `desktop\node_modules` was a junction to the repo's. `recovery.tree_files` refuses any link among a folder's
  children before it skips `node_modules`, so every backup test failed with "Backup refuses linked files/directories"
  (`recovery.py` line 173, the `desktop` folder loop; the earlier note that the `data\` junctions were the cause was
  wrong: `inventory` never walks `data\speech-models` or `data\wake-models`). Now `desktop\node_modules` is a real
  folder holding two junctions, `electron` and `rcedit`, to the repo's `.pnpm` targets: the shape of the repo's own
  `node_modules`. The `data\` junctions were replaced anyway by real copies of the models (15 files, sha256 equal to the
  repo's); `build\cache` and `build\wheels` stay junctions (the build only reads them).
- The desktop tests start `<root>\.venv\Scripts\python.exe` unless `JARVIS_PYTHON` is set; the suite runner sets it to
  the repo's `.venv` Python.

## Development suites at the release commit cffb826: PASS

With the repo's `.venv` (Python 3.12) and the system node, `JARVIS_PYTHON` set to the same `.venv`, one after another:
**783 Python tests OK (none skipped), 60 desktop, 18 Intelligence, 26 interface scripts.** 21:26 to 21:42 local
(`D:\JARVIS-release-work\dev-suites-1.0.18-time-cffb826-run2`; summary `dev-suites-summary-cffb826.txt` here).

The run before it, at the same commit (21:03 to 21:16, `...-cffb826`), did not pass: 2 errors in the new phone test
of `test_time_reply.py` and the desktop inspection job still `running` after its 240 s. Cause: the PC's drive C:
stalled. The owner was installing other programs then (Claude Code through Ollama about 21:00, a Qwen desktop app at
21:22; C: went from 7.7 to 5.1 GB free). A probe caught the stall: one `ALTER TABLE` on a brand-new test database in
`%TEMP%` (on C:) took 15 s (`project_budgets.setup`, under `App.__init__`); the phone test's own requests took at most
0.05 s. 20 repeats of the phone test showed whole tests of 50 to 116 s while every request stayed under 7 s; 15 more,
on a quieter disk, ran in about 1 s each. The run above, on the same commit with nothing changed, passed. The release
regression keeps its temporary files on D: (`tools/release_regression.py`), away from C:.

Earlier runs on the uncommitted fix (before the review): run 3 at 20:42, 782 Python OK, 60, 18, 26
(`dev-suites-summary.txt` here).

## The build: `1.0.18-cffb826de043` (commit cffb826)

`build-1.0.18-time.log.txt`, `JARVIS-1.0.18-cffb826de043.release.json`: built from the clean worktree with the repo's
`.venv` Python (`tools/build_release.py --version 1.0.18 --out D:\JARVIS-release-work\release`), 21:42 to 21:45 local:
10,768 files, 1,186,087,108 bytes; zip `D:\JARVIS-release-work\release\JARVIS-1.0.18-cffb826de043.zip`, 533,364,533
bytes, sha256 `312f03c383c9496910106f3bed4af0c9f1643865393d378082444f50b9138b57`. The build tools, the Setup template,
the rehearsal scripts and the version 4 Stage 7 files are byte-identical between 0d38218 (1.0.17) and `claude/main`.

## Comparison with 1.0.17: as expected (`JARVIS-1.0.18-cffb826de043.compare-1.0.17.json`)

`docs/release-rehearsal-20261004-1012/compare_manifests.py` against `1.0.17-0d38218c4e1d`: 10,768 files in both, 0
added, 0 removed. Of the shipped source exactly two files changed, `app/server.py` and `app/release-notes.json`: the
shipped files of `git diff 0d38218 cffb826` (the other two, `test_time_reply.py` and `docs/RELEASE-1.0.18.md`, are not
shipped). The rest: the 3,986 bytecode files and the 29 pip launcher/RECORD files that record the build folder. The
pinned inputs are identical except the two that carry the version number: `electron/JARVIS.exe`, whose two copies (both
246,257,152 bytes) differ in exactly 4 bytes, all in the version resource (17 to 18 twice, "7" to "8" twice), and
`electron/resources/app/package.json`, whose only change is `"version": "1.0.17"` to `"1.0.18"`.

## Release regression, run 1: NOT PASSED, one test (`regression-1.0.18-cffb826de043-run1.output.txt`, `...python-log.txt`)

`tools/release_regression.py --package D:\JARVIS-release-work\release\JARVIS-1.0.18-cffb826de043 --work
D:\JARVIS-release-work\regression-1.0.18-time`, with the release's own Python and `JARVIS.exe` (no development
environment, no system node; TEMP on D:), run alone, 21:46 to 22:13 local: 782 Python tests in 1,389 s with **1
failure** and 7 skipped (the same 7 as for 1.0.17, by their own conditions); 60 desktop (190 s), 18 Intelligence and
the 26 interface scripts passed; 110 test files overlaid from cffb826; the release verified unchanged before and after.

The failure: `test_music.OneThreadForTheMediaInterfaceTests.test_a_song_opened_on_a_thread_that_ended_can_still_be_seen_and_stopped`,
the test against the real Windows media interface (a one-second silent tone): "the real media interface refused the
open: Windows did not answer the music command in time" (`music.Mci`'s 10 s wait for Windows). `music.py` and
`test_music.py` are byte-identical to 1.0.17's, whose regression this test passed; it passed in tonight's development
suites. Reproduced right after, alone, with the release's own Python in the regression's copy and TEMP on D:: **5 runs
of 5 passed, 0.4 to 0.8 s each** (`repeat_music_test.ps1` in the session's scratchpad). Taken as Windows' media
interface not answering in time at that moment (the same kind of stall as drive C: earlier), not as a defect of the
build; the build is not changed. The regression runs again, alone, on the same build (run 2 below); the build is
accepted only on a run that passes.

## Release regression, run 2: stopped by the owner, no result

Started alone at 22:15 local on the same build (`--work D:\JARVIS-release-work\regression-1.0.18-time-run2`);
stopped from the owner's side during the Python suite (noticed at 22:29): no suite finished, no log written, no process
left running. The build is not yet accepted: the regression must pass in a complete run before the Setup, the
rehearsals and the sandbox Stage 7 pass.

## Release regression, run 3: PASS (`regression-1.0.18-cffb826de043-run3.output.txt`, `...python-log.txt`, `...desktop-log.txt`)

2026-10-11, after the PC's restart at 08:34, on the same build, alone (`--work
D:\JARVIS-release-work\regression-1.0.18-time-run3`), 08:55 to 09:21 local, with the release's own Python and
`JARVIS.exe` (no development environment, no system node; TEMP on D:): **782 Python tests OK (1,345 s; 7 skipped, the
same 7 as for 1.0.17 by their own conditions), 60 desktop (133 s), 18 Intelligence, 26 interface scripts; 110 test
files overlaid from cffb826; the release verified unchanged before and after.** `test_music`'s media-interface test,
the one failure of run 1, passed. **Build `1.0.18-cffb826de043` is accepted on this PC's regression.**

## The Setup (`JARVIS-Setup-1.0.18-cffb826de043.setup.json`, `setup-1.0.18-time.log.txt`)

Built by `tools/setup/build_setup.py` with Inno Setup 6.7.3 (ISCC sha256 `0a875703…`, the same as for 1.0.17) from
this package, 09:22 to 09:24 local, in 137.7 s: `JARVIS-Setup-1.0.18-cffb826de043.exe`, 406,919,489 bytes, sha256
`9fda604615c583edea95e49f4d69ffef892830157fe8ec5bba8939d30c1a8b57`; the template unchanged since 1.0.17 (sha256
`82c2d322…`); unsigned (decision D3); both application ids as for 1.0.17.

## Zip install: PASS (`zip_install_rehearsal_v2-1.0.18-cffb826de043.output.txt`)

The zip against its record, extracted, `install.cmd` into a sandbox home on D: in 29 s (the shortcuts withheld, no
launcher script), launched through `releases\1.0.18-cffb826de043\electron\JARVIS.exe` (the Core answering in 19.8 s, 8
processes: `JARVIS.exe` and `python.exe`), verified after use, uninstalled: all 10,768 program files removed, data,
config and profile kept, nothing left running.

## The Setup rehearsal, version 2: PASS (`setup-rehearsal-v2-1.0.18-cffb826de043.json`, `...output.txt`)

`docs/release-rehearsal-20261007-1017/rehearse-setup-v2.ps1 -Base D:\JARVIS-release-work\setup-rehearsal-v2-1.0.18-time`,
09:24 to 09:31 local. The owner's real Desktop and Startup `JARVIS.lnk` carry the same sha256 before, after every step
and at the end (desktop `7dca2506…`, startup `f8675687…`: the shortcuts at 1.0.17's `JARVIS.exe`); the live JARVIS had
8 processes before and after; the Installed-apps entry absent before and after. The silent install with `/DIR`,
`/HOME` and `/NOSHORTCUTS` in 86.1 s (the installer inside it: verify package 9.3 s, copy 11.9 s, verify copy 8.5 s,
switch 0.1 s; `withheld`), the program, the package release and the uninstaller present, no `JARVIS.ps1`; `JARVIS.exe`
started (the Core up in 20.1 s; `JARVIS.exe` and `python.exe` only) and shut down cleanly (0 left); the reinstall in
61.3 s; the uninstall through the entry's own uninstaller in 11.6 s: 10,768 program files removed, data, config and
profile kept.

## `pkg-1.0.18-time` (09:33)

`D:\JARVIS-release-work\pkg-1.0.18-time` holds the zip, its record, the Setup and its record, read back equal to the
records (zip `312f03c3…`, Setup `9fda6046…`; the Setup's record names the same zip). `pkg-1.0.18` holds the superseded
Workshop build and is not used.

## Stage 7 pass in a sandbox, 1.0.17 -> 1.0.18, version 4 scripts: ALL PASSED (`stage7-local/`)

`docs/release-rehearsal-20261007-1017/rehearse-stage7-release-v4.ps1 -Package D:\JARVIS-release-work\pkg-1.0.18-time
-PreviousPackage D:\JARVIS-release-work\pkg-1.0.17 -Base D:\JARVIS-release-work\stage7-local-1.0.18-time`, started by
full path, 09:32-09:46 local (14 minutes; nothing else running). **ALL STAGE 7 STEPS PASSED for 1.0.18-cffb826de043**:
28 check records PASS across the five phases plus the restart check (simulated "one start later" through
`-BootIdentityFile`), the same as 1.0.17's sandbox and VM passes (29 checks). The driver needed no change. The owner's
real shortcuts carry the same hashes before, after every start of the driver and at the end; 8 live JARVIS processes
before and after, never addressed; the sandbox's entry "JARVIS (sandbox)" 1.0.18 removed by its own uninstaller at the
cleanup (absent afterwards); 0 sandbox processes left. The records: `rehearsal-summary.json` (state `finished`),
`rehearsal.output.txt`, `evidence/` (the five run folders with their check records; the four Inno Setup logs of 2 to
4.5 MB each stay on D: only). The run folders carry UTC names (`stage7-20261010-2232..`), local 09:32 on 2026-10-11.

| Phase | Result and timings (the installer's own seconds inside the Setup) |
|---|---|
| Install (09:32-09:34) | the zip and the Setup against their records; the Setup silently in 71.2 s wall (inside: verify package 8.3 s, copy 12.3 s, verify copy 7.6 s, switch 0.4 s; `withheld`); the entry; the files verified; launch through `JARVIS.exe` in 14.8 s (8 processes); duplicate Core refused; local speech recognition; "restart Windows" asked for |
| Restart check | refused on the same start of Windows, passed with "one start later" (R1 in 0.3 s, 8 processes) |
| Uninstall (09:34-09:36) | through the entry's own uninstaller in 10 s (stop 1.6 s, remove 2.4 s; data kept); reinstall from the Setup in 73.2 s wall (verify package 8.4 s, copy 12.3 s, verify copy 8.6 s, switch 1.4 s); final stop |
| Update (09:36-09:43) | 1.0.17 extracted and installed (copy 8.6 s), updated to 1.0.18 while running (30.4 s wall; stop 1.6 s), rolled back (12 s), updated again (21.2 s), one update through the Setup (67.4 s wall; stop 1.9 s); 0 processes left after each |
| Interrupt (09:43-09:46) | 1.0.17 running, the update killed mid-copy, the update run again: installed (26.9 s wall) |

Every install, update and rollback is far inside the Gate 20 bound (600 s on the installer's own seconds; the longest
lap here is copy 12.3 s) and every stop inside 120 s (the longest 2.4 s). E0 again shows Git Bash's `whoami` refusing
`/groups` (the artefact of this PC noted for 1.0.17; E0 passes on its other readings).

**Build `1.0.18-cffb826de043` has passed every check this PC can give it:** the development suites, the review, the
comparison, the release regression (run 3), the Setup, the zip install, the Setup rehearsal and the sandbox Stage 7
pass.
