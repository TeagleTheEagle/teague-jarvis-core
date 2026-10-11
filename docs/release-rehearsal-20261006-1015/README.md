# Release 1.0.15: build and checks on this PC (2026-10-06)

Owner, 2026-10-06: "build 1.0.15 now", later "continue 1.0.15". This folder is the record. Two builds were made:
build 1 (`1.0.15-02ae75ed0374`) was superseded after its release regression (one test's wait too short); **build 2,
`1.0.15-63362929d7ad` (commit 6336292), is the release under acceptance.** Its program files are identical to build
1's (only a test file changed between the two commits; tests do not ship).

Everything ran on this PC in folders on D:. The owner's installed JARVIS (`%LOCALAPPDATA%\JARVIS`, 1.0.14, running
with 8 processes throughout) was never addressed: every rehearsal counts processes by their program folder and
stops only those from its own sandbox folder. The check in the test VM (Stage 7) is a separate owner-approved step:
`docs/STAGE7-CHECK-1.0.15.md`.

## Before the build

- The three open points of the list (`docs/RELEASE-1.0.15-SCOPE.md` section C): the Alibaba maintenance notice
  looked at (nothing to change); the new header looked at in a test desktop window (`header-check/`: the app's own
  Electron and window options, its own profile, a sandbox Core; one width rule fixed, all eight sections show from
  1280 to full width and nothing sits under the Windows buttons at nine sizes); the release notes written.
- Development suites at commit 02ae75e: 634 Python, 52 desktop, 18 Intelligence tests and 23 interface scripts
  pass. Commit 6336292 changes one test file only (see build 1).
- Every one of the eight parts of the list had one independent review; all findings applied (their records are in
  `docs/`).

## Build 1: `1.0.15-02ae75ed0374` (commit 02ae75e), superseded

- `build-1.0.15.log.txt`, `JARVIS-1.0.15-02ae75ed0374.release.json`: 10,669 files, 1,177,965,355 bytes; zip
  525,845,944 bytes, sha256 `a0a507bb4798f40dcf0aa88ea4146fb6212573948ac5d3af9c5cc97e1a0efc98`.
- `JARVIS-1.0.15-02ae75ed0374.compare-1.0.14.json`: pinned inputs identical to 1.0.14; shipped source 43 files
  changed, 19 added, 1 removed (`configure_gemini.py`), exactly the files of `git diff e038726 02ae75e` outside
  docs, tools and tests (the 33 other names in that diff are test files). The package's `installer.py` is
  byte-identical to `tools/installer.py`.
- **Release regression NOT PASSED** (`regression-1.0.15-02ae75ed0374.output.txt`, `...desktop-log.txt`): 634 Python
  (1 skipped: the 8.3 short-name installer test, as for 1.0.14), 18 Intelligence, 23 interface scripts and 51 of 52
  desktop tests pass. The failure: "one authenticated job captures the actual 13 panels with no external
  submission" (`desktop/test/inspection-job.test.cjs`) waits 100 seconds for the interface inspection job; after 100
  seconds it was still running. Measured afterwards in the same regression copy (a temporary test file, removed
  again): the job ended correctly after 113 seconds, all 13 panels captured, nothing submitted. The same test took
  98 s in the 1.0.12 regression and 89 s in the 1.0.14 one; the 100-second wait had almost no room left and the
  heavier pages of 1.0.15 used it up. A test wait too short, not a wrong result. **The test now waits up to 240
  seconds** (commit 6336292). Because the regression carries the tests of the release's own commit, build 1 was not
  taken further.

## Build 2: `1.0.15-63362929d7ad` (commit 6336292), the release under acceptance

- `build-1.0.15-build2.log.txt`, `JARVIS-1.0.15-63362929d7ad.release.json`: 10,669 files, 1,177,965,365 bytes; zip
  525,847,763 bytes, sha256 `1019dce00702da4e15dac5ea8203a1a1034311fbbe30b352097517b16deec027`. The copy in
  `D:\JARVIS-release-work\pkg-1.0.15` (zip and record; build 1's were removed from there) has the same hash.
- `JARVIS-1.0.15-63362929d7ad.compare-build1.json`: against build 1, 0 source files changed, added or removed; only
  the 3,979 bytecode files and the 29 pip launcher/RECORD files that record the build folder and time differ.
- `JARVIS-1.0.15-63362929d7ad.compare-1.0.14.json`: as build 1 against 1.0.14 (43 changed, 19 added, 1 removed;
  pinned inputs identical). `installer.py` byte-identical to `tools/installer.py`.

## Release regression of build 2: PASS (`regression-1.0.15-63362929d7ad.output.txt`)

With the release's own Python and Electron (no development environment, no system Node), 1,003 s: 634 Python tests
(1 skipped, as above; 807 s), 52 desktop (183 s), 18 Intelligence, 23 interface scripts; 92 test files overlaid
from 6336292; the release verified unchanged before and after. The capture test took 180 s this time (within its
new wait; the installed JARVIS and the morning's load were running beside it).

## Zip install of build 2 (`zip_install_rehearsal-1.0.15-63362929d7ad.output.txt`)

Zip hash equals the record; Windows extraction gives `install.cmd`, `installer.py`, `release`; `install.cmd --home
<sandbox> --no-shortcuts` installed 1.0.15 in 28 s; launched (8 processes, Core answering); verified after use;
uninstall **with JARVIS running** removed all 10,669 program files, kept data/config/profile, 0 processes left.

## Stage 7 pass in a sandbox, 1.0.14 -> 1.0.15, version 3 scripts (`stage7-local/`)

`rehearse-stage7-release-v3.ps1 -Package D:\JARVIS-release-work\pkg-1.0.15 -PreviousPackage
D:\JARVIS-release-work\pkg-1.0.14 -Base D:\JARVIS-release-work\stage7-local-1.0.15-run2`: version 3 guest scripts,
sandbox home and staging, no shortcuts, no provider key in the environment, 2026-10-06 10:25-10:37 (11.5 min).
**ALL STAGE 7 STEPS PASSED**, and the restart check was exercised with what Windows really says:

| Start of the driver | Result |
|---|---|
| 1: Install | PASS (10:25:50-10:29:19): package, extract, install 28.9 s, verify, launch (8 processes), duplicate Core refused, local speech recognition 4 s, the restart check's record written (`stage7-install-boot.json`: this PC's count of starts 60, newest start entry 17114); then the driver asked for the Windows restart |
| 2: on the same start of Windows | "Windows has not been restarted since the install step" (the real record against the real Windows), as it must |
| 3: with a file saying "one start later" (`-BootIdentityFile`, standing in for the restart nobody performs here) | the restart seen; AfterRestart PASS (JARVIS up, both memories); Uninstall PASS (all 10,669 program files removed, data/config/profile kept) and reinstall; Update PASS: 1.0.14 installed over the kept data, updated to 1.0.15 while running (30.1 s wall; stop 1.2 s; 8 processes, both memories), rollback to 1.0.14 (9.6 s; both memories), update again (17.3 s; `verify_installed` 8.0 s); Interrupt PASS: installer killed after 11.4 s with 3,751 of 10,669 files copied, 1.0.14 still current, verified and running with both memories, no 1.0.15 folder in place; the rerun finished in 32.5 s, verified, started with both memories, stopped cleanly |
| 4: nothing left to do | ALL STAGE 7 STEPS PASSED, no phase run |

Live JARVIS processes before and after: 8 and 8; sandbox processes after: 0. Every run's first record (E0) notes the
Windows build and the Administrators membership. Records: `stage7-local/` (the harness log and summary, the driver
log, every run's records; the Core logs are left in the work folder).

**The first run (`stage7-local-run1-superseded/`, 10:08-10:23) found a defect in the checks script and is
superseded.** Its pass also said ALL STAGE 7 STEPS PASSED, but its fourth start ran the AfterRestart phase again
and failed it: the AfterRestart run and the Uninstall run had been given the same folder (`stage7-20261005-231141`),
because `Invoke-Stage7.ps1` names a run's folder after its start to the second, the driver starts the next phase at
once, and the after-restart checks took under a second with JARVIS already up; the second run's SUMMARY replaced
the first's, so the driver saw no passed AfterRestart run. In the 1.0.14 check the two runs were 8 s apart, in its
sandbox rehearsal 2 s: the defect was in versions 1 and 2 and had never been hit. Fixed in the version 3 checks
script (a run whose folder exists waits for a free second; `docs/STAGE7-DRIVER-V3.md` section 4); the rerun above
shows AfterRestart at `232921` and Uninstall at `232922`. The first run was started from a Git Bash shell, whose
`whoami` is not Windows', so its E0 records say "unknown" for the Administrators membership (recorded, never a
failure); the rerun was started from PowerShell.

## Stage 7 tools, version 3: decision tests with the 1.0.15 label

- `tools/host/stage7-v3/test-stage7-step-v3.ps1` (the launcher in test mode, fake tree, no VirtualBox): **18 cases
  PASS** (`test-stage7-step-v3.output.json`): the 17 cases of version 2 with the version 3 approval file and the
  1.0.15 names, plus a version 2 approval file refused; the records of the 1.0.11 check (version 1 places) and of
  the 1.0.14 check (its own label) in the fake tree never count.
- `tools/host/stage7-v3/test-stage7-pass-v3.ps1` (the guest driver, fake discs, no phase runs): **21 cases PASS**
  (`test-stage7-pass-v3.output.json`). Between this run and the one of 2026-10-06 03:00 the PC was restarted once:
  this PC's count of starts went from 59 to 60 and its newest "operating system started" entry from 15977 to
  17114, which is exactly what the new restart check goes by.
- `tools/host/stage7-v3/Start-Stage7Vm.ps1` now takes the previous build's own Stage 7 disc
  (`JARVIS-STAGE7-<id>.iso`) when that build has no package disc: 1.0.14 never had one, and its Stage 7 disc carries
  its zip and record at the root. Not run here (it needs VirtualBox); its syntax was checked.

## Everyday update 1.0.14 -> 1.0.15, rehearsed in a sandbox (2026-10-06, after the VM check)

`rehearse-everyday-update-1015.ps1` is the 1.0.14 harness (`docs/release-rehearsal-20261005-1014/rehearse-everyday-update.ps1`)
with the build names and ids changed and the launcher taken from `tools/host/update-1.0.15/` (the 1.0.14 launcher
copied unchanged except its default folder and the plan it names; the 1.0.14 files stay as their approval recorded
them). Records in `update-rehearsal/` (`rehearsal-summary.json`, `rehearsal.output.txt`, `evidence/`). **13 of 13
checks PASS** (13:00-13:03 local): 1.0.14 installed into `D:\JARVIS-release-work\update-rehearsal-1.0.15\home` and
started once; the launcher refused without an approval file and refused while the sandbox JARVIS ran; step 1
(package hash, 1.0.14 verified, unpack 16 s); step 2 (backup with 1.0.14's own code, 156 files, verified, test
restore passed, hash-checked copy); step 3 (update 27.2 s: verify package 7.6 s, copy 9.3 s, verify copy 9.2 s, stop
0.8 s, switch 0.3 s; verified; database byte-for-byte unchanged); 1.0.15 started on the same data; a rerun changed
nothing; rollback with its approval file PASS (1.0.14 verified); a rerun after it changed nothing. The owner's
installed JARVIS ran throughout with 8 processes before and after and was never addressed; no sandbox process was
left. The plan for the owner: `docs/UPDATE-EVERYDAY-1.0.15.md`.

## Not checked here

Anything in VirtualBox; a real Windows restart (the restart check was exercised with what Windows really says, and
with a file standing in for "one start later"); Desktop/Startup shortcuts; a non-administrator account; with the
real providers: replies shown while written, speech recognition by Qwen, the backup provider taking over, a real
loss of the internet (all tested with stand-ins; the local model was asked for real on 2026-10-06).
