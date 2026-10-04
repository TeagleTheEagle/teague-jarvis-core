# Release 1.0.12: build and checks on this PC (2026-10-04)

Release `1.0.12-d28016b12efe` (commit d28016b), the fixes of `docs/POST-CUTOVER-FIXES.md`. Everything below ran on
this PC in folders on D:; the owner's installed JARVIS (`%LOCALAPPDATA%\JARVIS`) was never addressed. The check in
the test VM (Stage 7) is a separate owner-approved step: `docs/STAGE7-CHECK-1.0.12.md`.

## Before the build

- Development suites at the release commit: 365 Python, 50 desktop, 18 Intelligence tests and 17 interface
  scripts pass (before the changes: 325 Python, 36 desktop, 18 Intelligence, 16 scripts; two of the baseline runs
  timed out while the machine was busy and passed when run again).
- Each fix was designed by one independent check and challenged by another before code was written; the finished
  diff was reviewed by five independent checks, each finding tested by a sixth that tried to refute it: 9 findings
  confirmed (8 test gaps or wording, 1 real defect: the desktop watcher used the wall clock), all applied; 9 refuted.

## Build and comparison with 1.0.11

- `build-1.0.12.log`, `JARVIS-1.0.12-d28016b12efe.release.json`: 10,645 files, 1,177,430,195 bytes; zip
  525,629,601 bytes, sha256 `744056508ab607bed8e7f89c14809e879b8320ea28df1eb9b8d60c25b6b3c991`.
- `compare_manifests.py` -> `JARVIS-1.0.12-d28016b12efe.compare-1.0.11.json`: the same 10,645 paths. Changed: the
  14 shipped source files of commit d28016b (exactly the files `git diff 60d406f d28016b` lists outside docs, tools
  and tests), 3,973 compiled bytecode files and 29 pip launcher/RECORD files that record the build folder (the
  same 29 differ between 1.0.10 and 1.0.11). Python, its packages, Electron, the models and the Windows runtime
  DLLs: identical.

## Release regression (`regression-1.0.12-report.json`)

PASS with the release's own Python and Electron (no development environment, no system Node): 365 Python tests
(273 s), 50 desktop, 18 Intelligence, 17 interface scripts; 72 test files overlaid from the release commit; the
release verified unchanged before and after.

## Zip install (`zip_install_rehearsal-1.0.12.output.txt`)

Zip hash equals the record; Windows extraction gives `install.cmd`, `installer.py`, `release`; `install.cmd --home
<sandbox> --no-shortcuts` installed 1.0.12 in 50 s; launched (8 processes, Core answering); verified after use;
uninstall with JARVIS running removed all 10,645 program files, kept data/config/profile, 0 processes left.

## Stage 7 tools, version 2 (for every check after 1.0.11)

The 1.0.11 Stage 7 scripts work for one pass only (records, cycle marker and snapshot name in fixed places): with
the 1.0.11 records present they refuse a 1.0.12 pass or report it done. Version 2 copies (`tools/guest/stage7-v2`,
`tools/host/stage7-v2`; the 1.0.11 scripts unchanged as evidence) name everything after the check's label; the disc
carries `stage7-target.json` naming its egress folder; the VM is restored only from the approved snapshot and only
when VirtualBox records no change since it; E0 records the Windows build.

- `test-stage7-step-v2.ps1` (test mode, fake tree, no VirtualBox): 17 decision cases PASS
  (`test-stage7-step-v2.output.json`).
- `test-stage7-pass-v2.ps1` (fake discs, every phase skipped): 8 cases PASS (`test-stage7-pass-v2.output.json`).

## Stage 7 pass in a sandbox, 1.0.11 -> 1.0.12 (`rehearse-stage7-release.ps1`)

First attempt with 1.0.12 (2026-10-04 23:48-23:52, `D:\JARVIS-release-work\stage7-local-1.0.12`): Install PASS;
the restart check refused without a restart, as intended; AfterRestart PASS. At the start of the Uninstall phase
the harness stopped: PowerShell 5.1 turned a Python error message on the error output into a fatal error. The
sandbox showed the cause: the uninstall had removed `app\` and five Electron files and stopped at
`electron\electron.exe`, still in use by a JARVIS window that was closing, leaving a half-removed release that
`current.json` still pointed to. A direct repeat (install, launch, uninstall while running;
`D:\JARVIS-release-work\scratch\uninstall-race\`) passed, so it is a timing race.

Fixed for 1.0.13 in `tools/installer.py`: the process-ending step waits until ended programs have exited, looks
again (up to 5 rounds) and refuses before any switch or deletion if one is still running; uninstall removes the
launcher first and retries a file still in use for 10 s. `rehearse-stage7-release.ps1` and the version 2 guest
script now record such error output as part of the step instead of dying. 1.0.12 is superseded; this pass is to be
repeated on 1.0.13.

## Not checked here

Anything in VirtualBox; a real Windows restart; Desktop/Startup shortcuts; a non-administrator account; live AI
provider replies with the new 429 wording or gemini-3.8-flash (needs the owner's keys).
