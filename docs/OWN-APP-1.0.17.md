# Release 1.0.17, JARVIS as his own app: what was built (the record of docs/OWN-APP-PLAN.md)

Owner: "start 1.0.17" (2026-10-07, about 00:45 local). The plan is approved (`docs/OWN-APP-PLAN.md`; record
`../governance/OWN-APP-PLAN-APPROVAL-RECORD.json`). This file records what was built, how it was checked, and what
is still open. The three Core items of the phone checks (`docs/PHONE-CORE-FIXES-20261007.md`) ride in this release.

Status: **items 3.1 to 3.3 built, tested, rehearsed in a sandbox and independently reviewed, findings applied
(section 2); item 3.4 (JARVIS-Setup.exe) built with Inno Setup 6.7.3, rehearsed in a sandbox (section 3; that
rehearsal superseded, section 6) and independently reviewed together with the version 4 Stage 7 scripts on
2026-10-07, findings applied (section 7); the version 4 scripts written, their decision tests passing
(`docs/STAGE7-DRIVER-V4.md`); the Setup rehearsal that watches the real shortcut folders and the version 4 sandbox
Stage 7 harness written (section 7). Next: the real build of 1.0.17 and its checks (section 4). Nothing built here
reaches the everyday JARVIS until the release's Stage 7 check and update, on the owner's approvals.**

## 1. Items 3.1 to 3.3 (commit 09fed5f)

### 3.1 JARVIS.exe in the build

`tools/build_release.py`: the verified Electron binary (hash unchanged, checked as before) is copied, renamed
`release\electron\JARVIS.exe` and stamped by rcedit with the icon (`desktop/jarvis.ico`), the names (ProductName,
FileDescription and InternalName "JARVIS"; CompanyName and LegalCopyright "Teague Industries"; OriginalFilename
"JARVIS.exe") and the version (`1.0.17.0`, the four-number form Windows shows; `version_quad` refuses a version that
is not numbers). `electron.exe` is not shipped. Beside it `resources\app\package.json` and `main.cjs` are the
bootstrap: JARVIS.exe started with no arguments runs it, and it loads `release\app\desktop\main.cjs`; Electron prefers
`resources\app` over its own `default_app.asar`, so a double-click never opens Electron's welcome window. The release
manifest records the stamped program (`program`: path, hash, version, the rcedit pin, the icon's hash).

**rcedit** is the Electron team's stamping tool, from the npm package `rcedit` 5.0.2 installed project-locally with
pnpm (`desktop/package.json`, `pnpm-lock.yaml`; decision recorded in `docs/DEV-SETUP.md`). The registry marks that
package "no longer supported"; the binary it carries (`bin/rcedit-x64.exe`, 1,360,384 bytes, sha256 3e7801db…) is
pinned in the build, which refuses any other, so the deprecation changes nothing about what ships.

`tools/release_regression.py` runs the suites with the release's own Electron under its new name.

### 3.2 The app knows where it lives

`desktop/install-paths.cjs` (new): from `<home>\releases\<id>\electron\JARVIS.exe` with a `manifest.json` beside,
the app derives the home, sets `JARVIS_DATA_DIR`, `JARVIS_CONFIG_DIR`, `JARVIS_MODELS_DIR` and `JARVIS_PYTHON` unless
already set (a rehearsal pointing at a scratch folder keeps its own), drops `ELECTRON_RUN_AS_NODE`, and the app's
profile folder is `<home>\profile` (`app.setPath('userData')`, what `--user-data-dir` did). In development (the repo)
nothing applies. **Stale start:** when `current.json` names another release whose JARVIS.exe exists, this one starts
that one, detached, with the `--` arguments (`--login-launch`), marks it `JARVIS_REDIRECTED` so a start is handed on
at most once, and exits; a second start of the current release still just brings the running JARVIS forward. The
window carries the icon too (`BrowserWindow` `icon`). `desktop/main.cjs` does this before anything else.

### 3.3 Shortcuts

`tools/installer.py`: the Desktop and Startup shortcuts point straight at the current release's JARVIS.exe with its
icon (the Startup one with `--login-launch`); they are rewritten on install, update and now also on rollback
(`rollback(shortcuts=True)`; `--no-shortcuts` applies to rollback on the command line, as the sandbox rehearsals need).
`JARVIS.ps1` is written only while a release before 1.0.17 is current (`ensure_launcher`): an update from 1.0.16 leaves
the old file alone (harmless) and a rollback to 1.0.16 writes it again if it is gone, with PowerShell shortcuts as
before. Uninstall removes it as before.

### Tests and checks

- `test_own_app.py` (6): the Windows version form; the bootstrap's content and that its relative path lands on this
  release's desktop app; what ships; the pinned rcedit is the one installed; a real stamping of a copy of rcedit's own
  small program, read back with `--get-version-string`.
- `test_installer.py` (+6, `OwnAppTests`): no launcher script for a release with its own program, shortcuts at the
  program with its icon and `--login-launch`; an older release keeps the script and PowerShell shortcuts; update then
  rollback then update again moves the shortcuts with the program and restores the script; a rollback without
  shortcuts writes none; the command line passes `--no-shortcuts` to rollback; uninstall removes the script. Every
  shortcut write in the whole module is now recorded instead of run (section 5).
- `desktop/test/install-paths.test.cjs` (6): the layout rule, what is not an installation, the environment values,
  current.json, the stale-start decision in each case, the arguments and the detached redirect.
- The rehearsal build `1.0.17-09fed5f54c31` (no zip, `D:\JARVIS-release-work\own-app-rehearsal`; 10,709 files,
  1,182,283,693 bytes) and the sandbox rehearsal `docs/release-rehearsal-20261007-1017/rehearse-own-app.ps1`, record
  `own-app-rehearsal-09fed5f.json`, all five steps as expected: install with the package's installer and no shortcuts
  (no JARVIS.ps1 written); the program file read by Windows as JARVIS, Teague Industries, 1.0.17.0, OriginalFilename
  JARVIS.exe, no electron.exe, the bootstrap present; a start with no arguments (a double-click) brought the Core up
  in 30.9 s with only `JARVIS.exe` and `python.exe` running from the sandbox, the data and profile in the sandbox
  home; the stale start (current.json naming a copy of the release) handed over: only the copy's JARVIS.exe ran, the
  old one none; both shutdowns clean (0 processes left, nothing forced); uninstall removed 21,418 program files, kept
  data, config and profile, 0 processes. The real JARVIS was not addressed (sandbox home only, provider keys blanked).

## 2. Independent review of items 3.1 to 3.3 (one reviewer, 2026-10-07): no build-breaking finding; 1 high, 3 medium, 7 low, all applied

- **High:** the release regression would have failed: `test_own_app.py` imports the build script, which never ships.
  The regression now adds `tools/build_release.py` from the release's commit to its copy, and the test skips where
  the script is absent.
- **Medium:** the 1.0.16 `JARVIS.ps1` was left after an update although its text starts an `electron.exe` that
  1.0.17 has not: it is now removed when the current release has its own program (plan decision D6, literally) and
  written again by a rollback to an older release. A stale start while an older release is current (after a
  rollback) ran the pinned program as if current: it now hands over to the older release's `JARVIS.ps1`, or says so in
  a box and exits. `remove_shortcuts` was not guarded in the installer tests: it is now recorded like the writes.
- **Low:** the launcher values are always set from the installation (an override only with
  `JARVIS_LAYOUT_OVERRIDE=1`); the profile folder is created before it is named and `sessionData` goes with it; the
  redirect starts in the release's app folder and compares ids without case; a start through an 8.3 short name is
  resolved; rcedit's provenance (an npm attestation from the Electron team's build; the upstream repository archived in
  April 2026) is noted at the pin, with the option to keep the binary in `build/cache` later; a failed stamping shows
  rcedit's own words; the copyright line reads "Copyright Teague Industries"; the test fixture has both bootstrap
  files. Verified by the reviewer: the bootstrap cannot be bypassed by an argument (Electron 44 loads `resources\app`
  before anything else); `__dirname`, the single-instance lock, `app.exit` before ready and the top-level return are
  right; the shipped root launchers (`Start-JARVIS.ps1` and the like) are development files that never worked from
  an installation, unchanged.

## 3. Item 3.4: JARVIS-Setup.exe (built and rehearsed 2026-10-07; that rehearsal is superseded: section 6)

`tools/setup/JARVIS-Setup.iss.in` (the Inno Setup script template) and `tools/setup/build_setup.py` (fills it for a
built package, verifies the package against its manifest first, runs Inno Setup's compiler, records the Setup's hash).
The Setup installs per user without administrator rights (`PrivilegesRequired=lowest`), unpacks the package into
`%LOCALAPPDATA%\JARVIS-package` (the staging the Stage 7 check uses), removes an older package's release files first,
runs `installer.py install --package <that folder>` with the package's own Python (the answer kept in
`setup-result.json`), offers "Start JARVIS" (only when the install succeeded), and registers the entry "JARVIS,
Teague Industries, <version>" in Installed apps under the user's own registry hive (a fixed application id, so a newer
Setup updates the entry). Uninstall first runs the package's installer with `uninstall` (program removed, data kept)
and only when that succeeds removes the package folder and the entry; a refusal (JARVIS still running) keeps everything
so it can be run again. Silent mode `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART`; `/HOME=<folder>` for a sandbox home
(remembered in `setup-home.txt` for the uninstall); `/LOG=<file>`.

**Built and rehearsed (2026-10-07, about 02:00 local):** the owner installed Inno Setup 6.7.3 for their own account
(`%LOCALAPPDATA%\Programs\Inno Setup 6`, no administrator rights). `JARVIS-Setup-1.0.17-09fed5f54c31.exe` built from
the rehearsal package in 119 s (404,912,417 bytes, sha256 b790b956…, record `setup-rehearsal` folder and
`docs/release-rehearsal-20261007-1017/JARVIS-Setup-1.0.17-09fed5f54c31.setup.json`). The sandbox rehearsal
(`rehearse-setup.ps1`, record `setup-rehearsal-09fed5f.json`): silent install with `/DIR`, `/HOME` and
`/NOSHORTCUTS` into a sandbox in 79.9 s, the installer's answer "installed", the Installed-apps entry "JARVIS 1.0.17,
Teague Industries" present in this account's hive with the sandbox uninstaller; JARVIS.exe started from the install
(Core up in 20.3 s, JARVIS.exe and python.exe only); a second run of the same Setup as a reinstall in 59.5 s; the
uninstall through the entry's own uninstaller in 18.3 s: the installer answered "uninstalled" (10,709 program files
removed, data, config and profile kept), the entry gone, the package folder gone, 0 processes. The entry existed in
the owner's registry hive for the minutes between, as the plan allows for a sandbox test that cleans up after itself.
**This rehearsal also wrote and then removed the owner's real shortcuts, unnoticed at the time: section 6.**
Not yet independently reviewed (the next session, with the version 4 scripts).

## 4. Still to do in this release

The build of 1.0.17 proper from a clean tree (`tools/build_release.py`, then `tools/setup/build_setup.py` for its
Setup); the comparison with 1.0.16; the release regression; the zip rehearsal and the Setup rehearsal that watches
the real shortcut folders (`docs/release-rehearsal-20261007-1017/rehearse-setup-v2.ps1`); the sandbox Stage 7 pass
with the version 4 scripts (`rehearse-stage7-release-v4.ps1`); then `docs/STAGE7-CHECK-1.0.17.md` for the owner's
approval, the VM check and the everyday update. Done since the first draft of this section: the version 4 Stage 7
scripts, the release-notes entry, the review of section 7.

## 5. Disclosure: the owner's shortcuts, 2026-10-07 01:10 local

While the new installer tests ran, one existing test called `installer.rollback` without a `shortcuts` argument. With
the new default (shortcuts rewritten on rollback) and no guard in that test class, the real PowerShell ran and
rewrote the owner's Desktop and Startup `JARVIS.lnk` to point at a temporary test folder. Seen at once in the test
output (the phase list carried `shortcuts`), checked (both shortcuts dated 01:10:59, target the temporary folder) and
restored by hand to exactly what the 1.0.16 installer writes (powershell.exe, `-NoProfile -WindowStyle Hidden
-ExecutionPolicy Bypass -File "%LOCALAPPDATA%\JARVIS\JARVIS.ps1"`, the Startup one with ` -LoginLaunch`, working
folder the home, window style 7, description JARVIS), read back and equal. The installed JARVIS itself was not
touched (its launcher's presence was read only). Since then every test in `test_installer.py` records shortcut writes
instead of running them, so no test can reach the real folders again; the reviewer was asked to confirm it.

## 6. Disclosure: the Setup rehearsal and the owner's shortcuts, 2026-10-07 01:37 to 01:39 (found 06:04)

**What happened.** The sandbox rehearsal of item 3.4 (`docs/release-rehearsal-20261007-1017/rehearse-setup.ps1`,
record `setup-rehearsal-09fed5f.json`) ran `JARVIS-Setup-1.0.17-09fed5f54c31.exe` with `/NOSHORTCUTS`, `/DIR` and
`/HOME` pointing at a sandbox on D:. The Setup's own logs on D: show that the switch never reached the package's
installer: the silent install at 01:37:49 and the reinstall at 01:39:22 ran `installer.py install --package ...
--home <sandbox>` without `--no-shortcuts`, and the uninstall at 01:39:47 ran `installer.py uninstall --home
<sandbox>` without it (its answer, `package-uninstall-result.json`, has a `shortcuts` lap). `installer.py` writes
and removes the shortcuts in the real Desktop and Startup folders of the account whatever `--home` says. So the
rehearsal's install wrote the owner's real `JARVIS.lnk` on the Desktop and in Startup pointing at the sandbox's
1.0.17 `JARVIS.exe`, the reinstall wrote them again, and the uninstall removed both. Nobody noticed: the record of
the rehearsal checked the sandbox and the Installed-apps entry, not the real shortcut folders; the restore of 01:10
(section 5) had happened before, so the status of 01:41 said the shortcuts were in order. The owner's JARVIS kept
running until the PC was shut down at 02:40; after the restart it did not start at sign-in, and the owner's
screenshot of the Desktop at 06:04 showed no JARVIS shortcut.

**Why the switch was lost.** The Setup script read the switch with Inno Setup's `{param:NOSHORTCUTS|}`, which
returns a value only for the `/NAME=value` form; a bare `/NOSHORTCUTS` reads as empty, so neither the marker file
`setup-noshortcuts.txt` was written nor `--no-shortcuts` passed. The record of item 3.4 (section 3) and the
build tool's own text said the switch protected the build PC; that was never tested against the real folders.

**Put right (06:10).** The two shortcuts were written again from this repository's `installer.write_shortcuts`
with the 1.0.16 launcher values (the same PowerShell the 1.0.16 installer runs: `powershell.exe -NoProfile
-WindowStyle Hidden -ExecutionPolicy Bypass -File "%LOCALAPPDATA%\JARVIS\JARVIS.ps1"`, the Startup one with
`-LoginLaunch`, window style 7, the install home as the working folder) and read back. The installed JARVIS itself
was not touched (its `current.json`, launcher, releases, data and config are as the 1.0.16 update left them).

**Fixes, in this commit.** (1) `installer.py` writes or removes the real shortcuts only when the home is this PC's
own install home (`own_home`, `%LOCALAPPDATA%\JARVIS`): a home that is anywhere else (a rehearsal, a sandbox, a
test) never touches them, whatever the switches say. The rule is the default of `install`, `rollback` and
`uninstall` themselves (`shortcuts=None`), not only of the command line, so a Python caller that forgets the
keyword is safe too (the incident of section 5 was such a call); the command line's answer says `shortcuts:
written | removed | skipped (--no-shortcuts) | withheld (the home is not this PC's own install home)`; no
`%LOCALAPPDATA%` means never "own". `test_installer.py` proves install, the legacy removal, rollback and
uninstall with another home record no shortcut write or removal, and with the own home the four writes and
removals as before. (2) The Setup script reads the switch with a `HasSwitch` function that accepts the bare form
and the `=value` form, for the marker file and for every installer call; the script was compiled once from the
rehearsal package to prove it (the exe is a compile check only, not offered). Independent review of the fix:
1 high (a brace inside the new Pascal comment, which would not have compiled), 2 medium, 6 low, all applied.

**Still open.** The Setup built at 01:35 (`JARVIS-Setup-1.0.17-09fed5f54c31.exe` on D:) carries the old script and
must not be run again on this PC; the real build of 1.0.17 gets the fixed script. The next sandbox rehearsal
(a new copy of `rehearse-setup.ps1`) records the real Desktop and Startup folders before and after each step
(hash or absence) and fails on any change, which this one did not. The owner's Desktop shortcut's
icon is PowerShell's, as 1.0.16 had it.

## 7. Version 4 Stage 7 scripts, the two rehearsal scripts, and the independent review of item 3.4 with them (2026-10-07)

**Written (the version 3 files untouched):** `tools/guest/stage7-v4/` and `tools/host/stage7-v4/`, recorded in
`docs/STAGE7-DRIVER-V4.md` (install from the Setup, the Installed-apps entry, uninstall through it, reinstall from the
Setup, one update through the Setup as step G7, the DVD-sized disc with the Setup beside the zip; 29 checks per
pass); their decision tests, 19 launcher cases and 21 driver cases, pass. `docs/release-rehearsal-20261007-1017/
rehearse-setup-v2.ps1`: the Setup rehearsal with the owner's real Desktop and Startup `JARVIS.lnk` recorded (hash or
ABSENT) before, after every step and at the end, stopping at once on any change; it also requires the installer's own
word "withheld" and `--no-shortcuts` in the Setup's logged command, the entry "JARVIS (sandbox)" with the version,
exit code 0 of the Setup and the uninstaller, and the live JARVIS's process count unchanged.
`rehearse-stage7-release-v4.ps1`: the version 3 harness with the version 4 driver, the same watch after every start
of the driver, the entry required absent before, and a cleanup through the sandbox's own uninstaller at the end that
fails the run if the sandbox's entry or package folder survives.

**Independent review (one reviewer, 2026-10-07) of item 3.4 (`tools/setup/`), the version 4 scripts and the two
rehearsal scripts: no high finding; 8 medium and 9 low.** Applied:

- M1: the disc builder's version 4 copy of `New-PackageIso.ps1` lives beside `New-Stage7Disc.ps1` in the launcher
  folder; when a launcher folder was placed without it, the repo copy is used; the check plan lists it as a seventh
  tool with its hash.
- M2: a Setup or uninstaller run inside the VM could be silent for a quarter of an hour (the unpack of 1.2 GB plus
  the installer's work) against the owner's 15-minute rule: the guest driver now says every half minute that the
  Setup is still running and how many files the package folder holds.
- M3: the checks did not assert the installer's own word on the real shortcuts (the one line that proves the
  2026-10-07 incident cannot recur): I2, U1, U2 and G7 now require "written"/"removed" on the VM and "withheld" in a
  sandbox, and on the VM that the Setup got no folder or shortcut switch at all.
- M4: a refused install (JARVIS running) left the Installed-apps entry saying "JARVIS 1.0.17" and a finished page
  saying "installed"; the silent Setup exits 0 either way. The Setup now removes the entry it wrote when the installer
  refuses, the finished page says that nothing was installed, and the records say that `setup-result.json` is the
  verdict, not the exit code.
- M5: the uninstall removed the program before Windows' own "are you sure" question: the Setup now asks first,
  with the data-kept wording, and a "No" does nothing at all.
- M6: a sandbox run shared the real JARVIS's application id, so once the real 1.0.17 is installed no sandbox
  rehearsal could run on this PC, and a run with `/HOME` would have rewritten the real entry: a run with `/HOME`
  now registers as "JARVIS (sandbox)" under a second application id, `/HOME` without `/DIR` is refused before
  anything is done, the two ids are read from the template into the Setup's record (`app_id`, `sandbox_app_id`), and
  the guest driver and both rehearsals read the sandbox id from that record.
- M7: the no-shortcuts marker file survived a later install into the same package folder: it is removed with the
  old package files, so each install decides from its own command line.
- M8: the harness's cleanup was only recorded: it now fails the run (exit 2, state STOPPED) when the sandbox's
  entry or package folder survives or the installer did not withhold the real shortcuts.
- L1, L2: the Setup rehearsal's `home_file` is a plain string (the version 1 record carried a 2 MB provider graph
  in that field), a stale answer file is deleted before each run, and exit codes and the live process count are
  asserted. L4: the Setup's four-number version comes from `build_release.version_quad` (the same refusal as the
  build); `test_own_app.SetupScriptTests` (3) covers the placeholders, the two ids and the refusal. L5: a dead
  `[InstallDelete]` entry removed, `createallsubdirs` added, the home path saved as UTF-8 and read back as such, a
  trailing backslash stripped from `/HOME`. L6: the application ids in one place (the template) and in the record.
  L7: a missing Setup or uninstaller fails the step with a record instead of ending the phase; I4 requires that no
  `JARVIS.ps1` was written for a release with its own program (decision D6); G7 checks the shortcut targets after
  the update through the Setup; the Setup is hashed once. L8: `test_installer.py`'s runner block moved to the end
  (it sat before `OwnAppTests`, so `python test_installer.py` ran half the module; the suite runner was unaffected).
  L9: the records corrected (this file, the disc record's schema `jarvis-stage7-disc-v4`, the switches text).
- Not applied, recorded: L3 (a finer watch of the real shortcut folders between the driver's twenty installer
  calls would need a background thread; the installer's own-home rule is the primary defence and the end state is
  compared). The reviewer also found the compile check of 06:32 was of the template as it then stood; the rewritten
  template was compiled again today against a dummy package (`UsePreviousLanguage=no` was needed once `AppId` uses
  a code constant, found by that compile) and compiles.

**Verified by the reviewer (not re-checked here):** `HasSwitch` and the switch forwarding to the uninstaller's second
phase; `{param:HOME|}` with the quoted form; the cmd quoting of the installer command; `own_home`, `shortcuts_for`,
the `None` defaults and the guarded shortcut writes in every installer test; the order of `[InstallDelete]`, `[Files]`,
`ssPostInstall` and `[UninstallDelete]`; the registry key and its values against the I3/G7 comparisons; the switch
rule of `RunSetup`; the launch fallback; G7's flow; the DVD setting; the decision tests. **Not verified by anyone
yet:** the real 1.0.17 build and Setup (next), the durations in the VM, Inno's exact behaviour after a refused
installer run (the exit code and the finished page, now handled either way), and the I4 shortcut-target comparison on
the VM.
