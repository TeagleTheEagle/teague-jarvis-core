# Release 1.0.17: build and checks on this PC (2026-10-07)

Owner, 2026-10-07: "take the handoff ... continue with 1.0.17's release work in the order the status doc gives". This
folder is the record of the checks of release 1.0.17 ("JARVIS as his own app", `docs/OWN-APP-PLAN.md`, with the access
items of `docs/PHONE-ACCESS-PLAN.md`, the three phone-check fixes, the music stop fix and the start-up song). The
owner's installed JARVIS (`%LOCALAPPDATA%\JARVIS`, 1.0.16, running with 8 processes throughout) was never addressed:
every rehearsal counts processes by their program folder and stops only those from its own sandbox folder, and from
today every Setup rehearsal records the owner's real Desktop and Startup shortcuts before and after. The check in the
test VM (Stage 7) is a separate owner-approved step: `docs/STAGE7-CHECK-1.0.17.md`.

## Earlier in this folder (2026-10-07, 01:00 to 06:30)

- `own-app-rehearsal-09fed5f.json`, `rehearse-own-app.ps1`: items 3.1 to 3.3 rehearsed on the rehearsal build
  `1.0.17-09fed5f54c31` (five steps, all as expected; `docs/OWN-APP-1.0.17.md` section 1).
- `setup-rehearsal-09fed5f.json`, `rehearse-setup.ps1`, `JARVIS-Setup-1.0.17-09fed5f54c31.setup.json`: the first
  Setup rehearsal, **superseded**: it passed every step it checked and still wrote and then removed the owner's real
  shortcuts (`INCIDENT-real-shortcuts-20261007.md`; `docs/OWN-APP-1.0.17.md` section 6). That Setup carries the old
  script and must not be run again on this PC.
- `test-stage7-step-v4.output.json`, `test-stage7-pass-v4.output.json`: the version 4 Stage 7 tools' decision tests
  (19 launcher cases, 21 driver cases, all pass; `docs/STAGE7-DRIVER-V4.md`).

## The rehearsal build `1.0.17-b848d70e784d` and the Setup rehearsal, version 2 (13:05 to 13:15)

Made from commit b848d70 (the version 4 scripts, the review of item 3.4 applied, the music items) to prove the fixed
Setup against the real shortcut folders **before** the real build. Not a release: no zip, never offered.

- `JARVIS-1.0.17-b848d70e784d.release.json`: 10,768 files, 1,186,122,121 bytes, built in
  `D:\JARVIS-release-work\own-app-rehearsal`.
- `JARVIS-Setup-1.0.17-b848d70e784d.setup.json`: the Setup built by `tools/setup/build_setup.py` with Inno Setup
  6.7.3 in 130.9 s: 406,946,014 bytes, sha256 `6d378884…`; the record carries both application ids (`app_id`
  `{DC2C8033-…}` for the real JARVIS, `sandbox_app_id` `{7A3F1C52-…}` for a run with `/HOME`).
- `setup-rehearsal-v2-b848d70.json` (`rehearse-setup-v2.ps1`): **PASS, 13:11 to 13:15.** The owner's real Desktop and
  Startup `JARVIS.lnk` carry the same sha256 before, after every step and at the end (desktop `1829581c…`, startup
  `0be9b25f…`: the 1.0.16 launcher values as restored at 06:10); the live JARVIS had 8 processes before and after;
  no Installed-apps entry existed before. Steps: the silent install with `/DIR`, `/HOME` and `/NOSHORTCUTS` in
  101.8 s (the installer: verify package 9.6 s, copy 12.2 s, verify copy 25.1 s, switch 0.1 s), the installer's own
  word `withheld (the home is not this PC's own install home)`, the Setup's logged command carrying `--no-shortcuts`,
  the entry **"JARVIS (sandbox)" 1.0.17, Teague Industries** under the sandbox id with the sandbox uninstaller, no
  `JARVIS.ps1`; JARVIS.exe started (the Core up in 60.4 s; `JARVIS.exe` and `python.exe` only) and shut down cleanly;
  the same Setup again as a reinstall in 65.3 s (verified, nothing copied twice, `withheld` again); the uninstall
  through the entry's own uninstaller in 11.8 s: 10,768 program files removed, data, config and profile kept, the
  entry gone, the package folder gone, 0 processes, `withheld` and `--no-shortcuts` in the uninstall's command too.
  (The version 1 record of 01:40 was 7.9 MB because one field carried a PowerShell provider graph; this one is 8 KB.)

## The real build: `1.0.17-52342b46e48a` (commit 52342b4), the release under acceptance

- `build-1.0.17.log.txt`, `JARVIS-1.0.17-52342b46e48a.release.json`: 10,768 files, 1,186,082,321 bytes; zip
  `D:\JARVIS-release-work\release\JARVIS-1.0.17-52342b46e48a.zip`, 533,364,383 bytes, sha256
  `115344e5d621c65ba6b9d0ad535a7318c9f8bd1b6f9f96d5f61bf3977f3fdd41`; built from the clean tree 13:17-13:19 local.
  The copy in `D:\JARVIS-release-work\pkg-1.0.17` (zip and record, with the Setup and its record beside them) has
  the same hash.
- `JARVIS-1.0.17-52342b46e48a.compare-1.0.16.json`: against 1.0.16, 30 shipped source files changed and 86 added
  (the access items' new modules `mail.py`, `calendar_feed.py`, `nudges.py`, `speaker.py`, `network_devices.py`, the
  new panels, the Mac's record copy under `phone/ios/`, the branding files), 0 removed: the files of `git diff
  fccde24 52342b4` outside docs, tools and tests. The pinned inputs (Python, its packages, the models, the Windows
  runtime files) are identical; the four differences the script lists under "pinned inputs" are the planned program
  change of item 3.1 and nothing else: `electron/JARVIS.exe` and the two bootstrap files are new, `electron/electron.exe`
  is no longer shipped (the Electron binary itself is still verified against its recorded hash before it is renamed and
  stamped, and the manifest records that hash). The rest is the 3,981 bytecode files and the 29 pip launcher/RECORD
  files that record the build folder.
- `JARVIS-Setup-1.0.17-52342b46e48a.setup.json`: the Setup built by `tools/setup/build_setup.py` with Inno Setup
  6.7.3 from the release package: 406,915,840 bytes, sha256
  `0fd7220cde96508ca3ad5a86cf025a1e5c52c3d83b7f7a4d9a09847326aa16e1`, 221 s (the regression ran at the same time);
  template sha256 `82c2d322…` (the reviewed template, compiled against a dummy package first); both application ids
  in the record.

## Zip install of 1.0.17: PASS (`zip_install_rehearsal_v2-1.0.17-52342b46e48a.output.txt`)

`zip_install_rehearsal_v2.py` (this folder; the 2026-10-01 script with the launch through the current release's own
`JARVIS.exe`, since a release with its own program has no `JARVIS.ps1`): the zip hash equals the record; Windows'
extraction gives `install.cmd`, `installer.py`, `release`; `install.cmd --home <sandbox> --no-shortcuts` installed
1.0.17 in 433 s (the regression, the Setup build and the Setup rehearsal shared the disk at the time; 1.0.16's took 70 s
under a folder move) with the installer's word `withheld` and no launcher script written; `JARVIS.exe` started with no
arguments brought the Core up in 26.4 s (8 processes, `JARVIS.exe` and `python.exe` only); verified after use; the
uninstall with the package's installer removed all 10,768 program files, kept data, config and profile, 0 processes,
0 program files left, `withheld` again.

## The Setup rehearsal, version 2, on the real Setup: PASS (`setup-rehearsal-v2-1.0.17-52342b46e48a.json`)

`rehearse-setup-v2.ps1` on `JARVIS-Setup-1.0.17-52342b46e48a.exe`, 13:25 to 13:35 (the regression and the zip
rehearsal ran at the same time, so every copy took longer): the owner's real Desktop and Startup `JARVIS.lnk` carry the
same sha256 before, after every step and at the end (`1829581c…`, `0be9b25f…`); the live JARVIS had 8 processes before
and after; no entry existed before. The silent install with `/DIR`, `/HOME` and `/NOSHORTCUTS` in 477.3 s, the
installer's word `withheld`, `--no-shortcuts` in the Setup's logged command, the entry "JARVIS (sandbox)" 1.0.17,
Teague Industries under the sandbox id with the sandbox uninstaller, no `JARVIS.ps1`; `JARVIS.exe` started (the Core up
in 32.7 s) and shut down cleanly; the reinstall in 103.8 s (`withheld` again); the uninstall through the entry's own
uninstaller in 12.4 s: 10,768 program files removed, data, config and profile kept, the entry and the package folder
gone, 0 processes, `withheld` and `--no-shortcuts` again.

## Stage 7 pass in a sandbox, 1.0.16 -> 1.0.17, version 4 scripts (`stage7-local/`)

`rehearse-stage7-release-v4.ps1 -Package D:\JARVIS-release-work\pkg-1.0.17 -PreviousPackage
D:\JARVIS-release-work\pkg-1.0.16 -Base D:\JARVIS-release-work\stage7-local-1.0.17` (started from PowerShell by full
path): version 4 guest scripts, sandbox home and staging, no shortcuts (the Setup given `/DIR`, `/HOME` and
`/NOSHORTCUTS`, so it registers as "JARVIS (sandbox)"), no provider key in the environment, 2026-10-07 13:35-14:09
local (34 min; the release regression ran at the same time, so every copy took longer). **ALL STAGE 7 STEPS
PASSED**, 29 checks, with the restart check exercised against what Windows really says; the owner's real Desktop and
Startup shortcuts carry the same hashes before, after every start of the driver and at the end; the live JARVIS had 8
processes before and after; the sandbox's entry was absent before and is absent after the cleanup.

| Start of the driver | Result |
|---|---|
| 1: Install | PASS (13:35:21-13:39:00): the zip and the Setup against their records and the disc-style payload manifest; the Setup run silently in 144.5 s (the installer inside it: verify package 7.4 s, copy 42.1 s, verify copy 7.5 s, switch 1.3 s; the installer's word `withheld`; the half-minute progress lines); the entry "JARVIS (sandbox)" 1.0.17 with the package folder's uninstaller; the files verified, `JARVIS.exe` present, no `JARVIS.ps1`; launch through `JARVIS.exe` (the Core up in 19.8 s, 8 processes), a memory saved, duplicate Core refused, local speech recognition 5.4 s, stop and start (2.8 s); the restart check's record written; then the driver asked for the Windows restart |
| 2: on the same start of Windows | "Windows has not been restarted since the install step" (the real record against the real Windows), as it must |
| 3: with a file saying "one start later" (`-BootIdentityFile`, standing in for the restart nobody performs here) | the restart seen; AfterRestart PASS (JARVIS up, both memories); Uninstall PASS through the sandbox entry's own uninstaller in 12 s (10,768 program files removed, data, config and profile kept, the entry and the package folder gone, `withheld`), reinstall from the Setup in 154.8 s (the entry back, JARVIS back with its memory, verified); Update PASS: 1.0.16 extracted (331 s) and installed over the kept data (the Core ready 42 s), updated to 1.0.17 while running (398.8 s wall: verify package 68.8 s, copy 139.1 s, verify copy 188.3 s, stop 1.9 s, switch 0.6 s, under the regression's load; 8 processes, both memories), rollback to 1.0.16 (11.9 s; both memories), update again (66.9 s), and **G7, the update through the Setup** from 1.0.16 running (101.5 s wall for the unpack and the installer: verify package 9.2 s, the already-present 1.0.17 verified 8.4 s, stop 1.5 s, switch 0.1 s; `withheld`; the entry present with the version; the final stop clean); Interrupt PASS: installer killed after 33.5 s with 3,323 of 10,768 files copied, 1.0.16 still current, verified and running with both memories, no 1.0.17 folder in place; the rerun finished in 136.4 s, verified, started with both memories, stopped cleanly (13:39:03-14:09:18) |
| 4: nothing left to do | ALL STAGE 7 STEPS PASSED, no phase run |
| cleanup | the sandbox's own uninstaller (23.5 s): 21,443 program files removed (both releases), data kept, the entry and the package folder gone, `withheld`; 0 sandbox processes |

One artefact of this PC, not of the scripts: every run's first record (E0) says `administrators_group_member: unknown`,
because the harness was started from this session's Git Bash and `whoami /groups` there resolves to Git's own
`whoami` (the driver records a failed read as unknown and never stops on it, by design); in the VM Windows' `whoami`
answers, as in every earlier check. The Windows build is recorded in every E0.

## The release regression of build 1: NOT PASSED (`regression-1.0.17-52342b46e48a.output.txt`, `...python-log.txt`)

With the release's own Python and `JARVIS.exe` (no development environment, no system Node), 13:19-14:12 local: the
desktop suite (60, 138 s) and all 26 interface scripts passed; the Python suite ran 776 tests in 2,969 s (the sandbox
Stage 7 pass, the Setup build, the Setup rehearsal and the zip rehearsal shared the disk and the processor; the
1.0.16 regression's Python phase took 1,104 s) and reported **2 failures and 11 errors**, so the regression as a whole
did not pass. Two kinds:

1. **Tests that need files the release does not ship, or a development checkout** (deterministic in any release
   regression, test defects, not product defects): `test_own_app.SetupScriptTests` (3 errors: `tools/setup` is not
   shipped, so `build_setup` cannot be imported), `test_tell_jarvis` (the whole module: `tools/host/tell_jarvis.py` is
   not shipped), and `test_memory_stamp` (1 failure: it expected a memory stamped "development ...", but in the release
   copy the Core stamps with the release id, `1.0.17-52342b46e48a`, which is the right behaviour of item E). Fixed in the
   tests: the first two skip where the tool is absent, the third asserts the stamp the Core actually uses.
2. **Timeouts under the load, and the file-in-use errors that follow a timed-out test's cleanup** (9: `test_phone_access`
   twice, `test_phone_bridge.test_http_boundaries`, `test_phone_core` once, each a 10-second HTTP timeout or "The
   question did not finish" inside a local test Core, then a temporary folder that could not be removed because the
   test Core still held its database). The same tests passed three times today in the development suite (764, 775 and
   777 tests OK) and in every earlier regression; they are not changed in this release except by the items whose own
   tests passed. Not accepted on that reasoning alone: the regression is run again on an idle PC, below.

**Build 1 is superseded (never offered):** the test fixes are committed and the release is built again from that
commit as build 2 (the program is the same; only test files and records changed, as the comparison between the two
builds shows below). The number stays 1.0.17, as for 1.0.16's two builds: the approved plan names 1.0.17 and build 1
never left this PC's sandboxes. Every check of build 1 above (the comparison, the Setup rehearsal, the zip rehearsal,
the sandbox Stage 7 pass) is kept as evidence of the same program and is run again on build 2.

## Build 2: `1.0.17-0d38218c4e1d` (commit 0d38218), the release under acceptance

- `build-1.0.17-build2.log.txt`, `JARVIS-1.0.17-0d38218c4e1d.release.json`: 10,768 files, 1,186,082,321 bytes; zip
  `D:\JARVIS-release-work\release\JARVIS-1.0.17-0d38218c4e1d.zip`, 533,361,567 bytes, sha256
  `210b46235638e92bbef1634b853c53ae6838ed58e997543cab87ffa844bb01d9`; built from the clean tree at 14:14-14:16 local.
- `JARVIS-1.0.17-0d38218c4e1d.compare-build1.json`: against build 1, **0 source files changed, 0 added, 0 removed, the
  pinned inputs identical**: the same program; the only differences are the 3,986 bytecode files and the 29 pip
  launcher/RECORD files that record the build folder and time.
- `JARVIS-1.0.17-0d38218c4e1d.compare-1.0.16.json`: against 1.0.16 exactly as build 1's comparison above (30 shipped
  source files changed, 86 added, 0 removed; the four planned program files; the pinned inputs identical).

## Release regression of build 2: PASS (`regression-1.0.17-0d38218c4e1d.output.txt`, `...desktop-log.txt`)

With the release's own Python and `JARVIS.exe` (no development environment, no system Node), run alone on the PC,
14:16-14:42 local: **776 Python tests OK (1,296 s; 7 skipped, by the conditions written in the tests: the three
Setup-template tests and the `tell_jarvis` module, which need repo-only tools, the two rcedit stamping tests, which
need `desktop/node_modules` that a release does not carry, and the 8.3 short-name installer test, as in every
regression), 60 desktop (157 s), 18 Intelligence, 26 interface scripts; 109 test files overlaid from 0d38218; the
release verified unchanged before and after.** The nine timeouts of build 1's run did not recur: they were the load,
as the records said.

(The Setup, the zip and Setup rehearsals, the refresh of `pkg-1.0.17` and the sandbox Stage 7 pass of build 2 follow
below as each completes, one after another.)
