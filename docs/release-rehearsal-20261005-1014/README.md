# Release 1.0.14: build and checks on this PC (2026-10-05)

Release `1.0.14-e03872680e1d` (commit e038726): the fixes of `docs/POST-CUTOVER-FIXES.md`, the installer change found
by the 1.0.12 sandbox Stage 7 rehearsal (with its review findings), and the desktop shutdown fix found by the 1.0.13
release regression (`docs/release-rehearsal-20261005-1013/README.md`). Everything below ran on this PC in folders on
D:; the owner's installed JARVIS (`%LOCALAPPDATA%\JARVIS`) was never addressed (0 of its processes before and after
every step). The check in the test VM (Stage 7) is a separate owner-approved step: `docs/STAGE7-CHECK-1.0.14.md`.

## Before the build

- Development suites at e038726: 373 Python, 52 desktop, 18 Intelligence tests and 17 interface scripts pass.
- Independent reviews: the installer change (2 medium, 6 low findings; 7 applied, 1 recorded as a known limit) and
  the desktop shutdown fix (2 low findings, both applied).

## Build and comparison with 1.0.11

- `build-1.0.14.log.txt`, `JARVIS-1.0.14-e03872680e1d.release.json`: 10,645 files, 1,177,431,353 bytes, built in
  133 s; zip 525,633,503 bytes, sha256 `ceb7d9e1922cebbf650753c4028473c5962c558ed70ec9f4be20f9fdc740d8d3`.
- `JARVIS-1.0.14-e03872680e1d.compare-1.0.11.json`: the same 10,645 paths; changed: 14 shipped source files (exactly
  `git diff 60d406f e038726` outside docs, tools and tests), 3,973 bytecode files and the 29 pip launcher/RECORD files
  that record the build folder; pinned inputs (Python, packages, Electron, models, runtime DLLs) identical. The
  package's `installer.py` (outside the manifest) is byte-identical to `tools/installer.py` at e038726.
- `D:\JARVIS-release-work\pkg-1.0.14` (zip and record), zip hash equal to the record.

## Release regression (`regression-1.0.14-report.json`, `regression-1.0.14-summary.txt`)

PASS with the release's own Python and Electron (no development environment, no system Node), 425 s: 373 Python
tests (1 skipped: the 8.3 short-name installer test skips itself because drive D: has no short names; it runs in the
development suite on C:), 52 desktop, 18 Intelligence, 17 interface scripts; 73 test files overlaid from e038726; the
release verified unchanged before and after. The two desktop tests that failed on 1.0.13 passed.

## Zip install (`zip_install_rehearsal-1.0.14.output.txt`)

Zip hash equals the record; Windows extraction gives `install.cmd`, `installer.py`, `release`; `install.cmd --home
<sandbox> --no-shortcuts` installed 1.0.14 in 56 s; launched (8 processes, Core answering); verified after use;
uninstall **with JARVIS running** removed all 10,645 program files, kept data/config/profile, 0 processes left.

## Stage 7 pass in a sandbox, 1.0.11 -> 1.0.14 (`stage7-local/`)

`docs/release-rehearsal-20261004-1012/rehearse-stage7-release.ps1 -Package D:\JARVIS-release-work\pkg-1.0.14
-PreviousPackage D:\JARVIS-release-work\pkg-1.0.11 -Base D:\JARVIS-release-work\stage7-local-1.0.14`, version 2 guest
scripts, sandbox home and staging, no shortcuts, 2026-10-05 01:38-01:51 (13.4 min). **ALL STAGE 7 STEPS PASSED**:

| Phase | Result |
|---|---|
| Install | PASS (01:38-01:41); then the driver asked for the Windows restart |
| restart check without a restart | refused, as intended (uptime check) |
| AfterRestart (with `-NoRestartCheck`) | PASS |
| Uninstall and reinstall | PASS: 10,645 program files removed, 0 processes, data and config kept; reinstall PASS |
| Update (1.0.11 installed, updated while running, rollback, update again) | PASS: update 64.8 s (stop 1.7 s), rollback 9.9 s, update again 33.1 s (verify_installed 11.5 s, stop 1.5 s); both memories and 8 processes each time, nothing left from the other release |
| Interrupt | PASS: installer killed after 13.7 s with 3,300 of 10,645 files copied; 1.0.11 still current, verified, running (8 processes) with both memories, no 1.0.14 folder in place; the rerun finished in 36.6 s, verified, started with both memories, stopped cleanly |

Every phase's first record (E0) notes the Windows build (26300.9550, 26H2 on this PC) and the Administrators
membership. Live JARVIS processes before and after: 0 and 0; sandbox processes after: 0.

## Stage 7 tools, version 2: decision tests with the 1.0.14 label

`test-stage7-step-v2.ps1` (launcher, test mode, fake tree, no VirtualBox): 17 cases PASS. `test-stage7-pass-v2.ps1`
(guest driver, fake discs, every phase skipped): 8 cases PASS. Outputs beside them.

## Not checked here

Anything in VirtualBox; a real Windows restart; Desktop/Startup shortcuts; a non-administrator account; live AI
provider replies with the new 429 wording or gemini-3.8-flash (needs the owner's keys).
