# Release 1.0.18: build and checks on this PC (2026-10-10)

Owner, 2026-10-10: "build 1.0.18". Release 1.0.18 is the Workshop (`docs/WORKSHOP.md`, built and reviewed on 2026-10-07:
JARVIS working with files, commands, his own Python environment, lessons and missions in his own folder on this PC;
commands ship as "ask first"). The owner's installed JARVIS (`%LOCALAPPDATA%\JARVIS`, 1.0.17, running with 8 processes
throughout) was never addressed: every rehearsal counts processes by their program folder and stops only those from its
own sandbox folder, and the Setup rehearsal and the Stage 7 harness record the owner's real Desktop and Startup
shortcuts before and after. The check in the test VM is a separate owner-approved step: `docs/STAGE7-CHECK-1.0.18.md`.
Every check below ran one after another on the otherwise idle PC (the 1.0.17 lesson: the regression alone).

## Development suites at the release commit (4afd891), about 09:39 to 09:46 local

With the repo's `.venv` and the system node: **809 Python tests OK (266 s, none skipped), 60 desktop, 18 Intelligence,
27 interface scripts.** Logs in `D:\JARVIS-release-work\dev-suites-1.0.18` (Python) and `...\dev-suites-1.0.18-node`
(the rest: the runner's first pass stopped after the Python suite on printing a symbol from the desktop log, a defect
of the runner, not of JARVIS; the node suites were run again with the output encoding fixed). The only commits after
the Workshop's last code commit (0773df5) change docs and `tools/host/update-1.0.17/`, which is not shipped.

## The build: `1.0.18-4afd891c38f4` (commit 4afd891)

- `build-1.0.18.log`, `JARVIS-1.0.18-4afd891c38f4.release.json`: 10,772 files, 1,186,294,251 bytes; zip
  `D:\JARVIS-release-work\release\JARVIS-1.0.18-4afd891c38f4.zip`, 533,444,176 bytes, sha256
  `8d44eba680bacf2e9a7e0c0a0cabd29c243412639ecf5a51154b56c10b845bc4`; built from the clean tree, 09:46-09:49 local.
- `JARVIS-1.0.18-4afd891c38f4.compare-1.0.17.json` (`docs/release-rehearsal-20261004-1012/compare_manifests.py`):
  against 1.0.17, 12 shipped source files changed and 3 added (`workshop.py`, `static/workshop.js`,
  `static/workshop.css`; the fourth added file is `workshop.py`'s bytecode), 0 removed: the files of `git diff 0d38218
  4afd891` outside docs, tools and tests. The pinned inputs are identical except two files that carry the version
  number: `electron/resources/app/package.json` (its `version` line, 1.0.17 to 1.0.18) and `electron/JARVIS.exe`,
  whose two copies differ in exactly 4 bytes, all in the version resource (the binary file and product version 17 to
  18, and the two version strings), stamped by the same rcedit 5.0.2 (sha256 `3e7801db…`) with the same icon (sha256
  `1c78eef2…`). The rest is the 3,986 bytecode files and the 29 pip launcher/RECORD files that record the build folder.

## Release regression: PASS (`regression-1.0.18-4afd891c38f4.output.txt`, `...python-log.txt`, `...desktop-log.txt`)

With the release's own Python and `JARVIS.exe` (no development environment, no system node), run alone on the PC,
about 09:50 to 10:18 local: **808 Python tests OK (1,482 s; 7 skipped), 60 desktop (147 s), 18 Intelligence, 27
interface scripts; 111 test files overlaid from 4afd891; the release verified unchanged before and after.** The 7 skips
are the count of 1.0.17's regression, by the conditions written in the tests, which are unchanged: the tests of the
Setup template and of `tools/host/tell_jarvis.py` need repo-only tools a release does not ship, the two rcedit stamping
tests need `desktop/node_modules`, and the installer's 8.3 short-name test needs short names, which drive D: does not
have. All seven ran and passed in the development run above.

## The Setup (`JARVIS-Setup-1.0.18-4afd891c38f4.setup.json`)

Built by `tools/setup/build_setup.py` with Inno Setup 6.7.3 (ISCC sha256 `0a875703…`, the same as for 1.0.17) from this
package, 10:18-10:21 local, in 135.4 s: `JARVIS-Setup-1.0.18-4afd891c38f4.exe`, 406,974,294 bytes, sha256
`eb1f0ee38c5672e506e73d7b3692a077ce776153ab9c248b21baf7f313fd3d05`; the template unchanged since 1.0.17 (sha256
`82c2d322…`); unsigned (decision D3); both application ids as for 1.0.17.

## Zip install: PASS (`zip_install_rehearsal_v2-1.0.18-4afd891c38f4.output.txt`)

The zip against its record, extracted, `install.cmd` into a sandbox home on D: in 30 s (the shortcuts withheld, no
launcher script), launched through `releases\1.0.18-4afd891c38f4\electron\JARVIS.exe` (the Core answering in 23.1 s, 8
processes: `JARVIS.exe` and `python.exe`), verified after use, uninstalled: all 10,772 program files removed, data,
config and profile kept, nothing left running.

## The Setup rehearsal, version 2: PASS (`setup-rehearsal-v2-1.0.18-4afd891c38f4.json`, `...output.txt`)

`docs/release-rehearsal-20261007-1017/rehearse-setup-v2.ps1`, 10:21-10:28 local. The owner's real Desktop and Startup
`JARVIS.lnk` carry the same sha256 before, after every step and at the end (desktop `7dca2506…`, startup `f8675687…`:
the shortcuts at 1.0.17's `JARVIS.exe` written by the everyday update of 2026-10-07); the live JARVIS had 8 processes
before and after. The silent install with `/DIR`, `/HOME` and `/NOSHORTCUTS` in 82.7 s (the installer inside it: verify
package 8.1 s, copy 12.4 s, verify copy 8.3 s, switch 0.1 s; `withheld`), the entry "JARVIS (sandbox)" 1.0.18, Teague
Industries, with the sandbox uninstaller, no `JARVIS.ps1`; `JARVIS.exe` started (the Core up in 20.7 s; `JARVIS.exe` and
`python.exe` only) and shut down cleanly; the reinstall in 59.5 s; the uninstall through the entry's own uninstaller in
10.2 s: 10,772 program files removed, data, config and profile kept, the entry and the package folder gone.

## `pkg-1.0.18` (10:28)

`D:\JARVIS-release-work\pkg-1.0.18` holds the zip, its record, the Setup and its record, read back equal to the records
(zip `8d44eba6…`, Setup `eb1f0ee3…`).

## Stage 7 pass in a sandbox, 1.0.17 -> 1.0.18, version 4 scripts: ALL PASSED (`stage7-local/`)

`docs/release-rehearsal-20261007-1017/rehearse-stage7-release-v4.ps1 -Package D:\JARVIS-release-work\pkg-1.0.18
-PreviousPackage D:\JARVIS-release-work\pkg-1.0.17 -Base D:\JARVIS-release-work\stage7-local-1.0.18`, started from
PowerShell by full path, 10:28-10:42 local (14 minutes; nothing else running). **ALL STAGE 7 STEPS PASSED**, every check
PASS. The first pass whose previous build has its own `JARVIS.exe` and Setup (1.0.17): the driver needed no change. The
owner's real shortcuts carry the same hashes before, after every start of the driver and at the end; 8 live JARVIS
processes before and after, never addressed; the sandbox's entry absent before and absent after the cleanup (its own
uninstaller); 0 sandbox processes left. The records: `rehearsal-summary.json` (state `finished`, every step said its
line), `rehearsal.output.txt`, `evidence/` (the five run folders with their check records; the four Inno Setup logs of
2 to 4.5 MB each stay on D: only).

| Start of the driver | Result and timings (the installer's own seconds inside the Setup) |
|---|---|
| 1: Install (10:28:30-10:30:55) | the zip and the Setup against their records; the Setup silently in 71.1 s wall (inside: verify package 7.5 s, copy 14.0 s, verify copy 7.8 s, switch 1.1 s; `withheld`); the entry "JARVIS (sandbox)" 1.0.18; the files verified, `JARVIS.exe` present, no `JARVIS.ps1`; launch through `JARVIS.exe` (8 processes), duplicate Core refused, local speech recognition 4.6 s, stop and start; the restart record written; the driver asked for the restart |
| 2: on the same start of Windows | "Windows has not been restarted since the install step", as it must |
| 3: with "one start later" (`-BootIdentityFile`) (10:30:56-10:41:47) | AfterRestart PASS (8 processes); Uninstall PASS through the entry's own uninstaller in 10 s (stop 1.7 s, remove 2.2 s; all program files removed, data kept) and reinstall from the Setup in 69.2 s wall (verify package 7.9 s, copy 11.2 s, verify copy 8.0 s, switch 0.4 s); Update PASS: 1.0.17 extracted (112.7 s) and installed over the kept data (verify 7.4 s, copy 8.8 s, verify copy 7.8 s, switch 1.4 s; 8 processes), updated to 1.0.18 while running in 31 s wall (verify package 8.1 s, copy 10.3 s, verify copy 10.1 s, stop 2.2 s, switch 0.1 s), rollback to 1.0.17 in 10.4 s, update again in 18.6 s wall (verify 8.5 s, the present 1.0.18 verified 8.4 s, stop 1.3 s, switch 0.2 s), **G7 the update through the Setup** from 1.0.17 running in 67 s wall (verify package 10.0 s, verify installed 10.1 s, stop 1.3 s, switch 0.3 s; 8 processes); Interrupt PASS: 1.0.17 running (verify 7.7 s, copy 13.2 s, verify copy 7.5 s, switch 0.4 s), the installer killed mid-copy, 1.0.17 still current and running, the rerun in 28.8 s wall (verify 7.7 s, copy 9.5 s, verify copy 9.9 s, stop 1.3 s, switch 0.3 s), 8 processes |
| 4: nothing left to do | ALL STAGE 7 STEPS PASSED, no phase run |

Every install, update and rollback is far inside the Gate 20 bound (600 s on the installer's own seconds; the longest
lap here is copy 14.0 s) and every stop inside 120 s (the longest 2.2 s). E0 again shows Git Bash's `whoami` refusing
`/groups` (the artefact of this PC noted for 1.0.17; E0 passes on its other readings).

**Build `1.0.18-4afd891c38f4` has passed every check this PC can give it:** the development suites, the comparison, the
release regression, the Setup, the zip install, the Setup rehearsal and the sandbox Stage 7 pass.

## Found while writing the Mac brief (10:35): the `devices` route was never built

`docs/MAC-REQUESTS-20261007.md` (the form for the Mac session) promises a `devices` operation for paired devices (asked
by the Mac, the app's R6 device panel), and the Mac built the panel against it. The Core never got it:
`device_gateway.OPS` does not list `devices`, so 1.0.17 (installed) and this build answer it with HTTP 400 `{"error":
"Operation unavailable."}`; the app shows its "not on this Core yet" state. No other route or field of the form is
missing (checked in `device_gateway.py` and `wearables/service.py`). Put to the owner: add the route to 1.0.18 as build
2 (the checks above run again) or leave it for a later release. The Mac brief (`docs/MAC-BRIEF-20261010.md`) tells the
Mac session the route is not served yet.
