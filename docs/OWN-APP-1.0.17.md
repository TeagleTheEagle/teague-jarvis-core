# Release 1.0.17, JARVIS as his own app: what was built (the record of docs/OWN-APP-PLAN.md)

Owner: "start 1.0.17" (2026-10-07, about 00:45 local). The plan is approved (`docs/OWN-APP-PLAN.md`; record
`../governance/OWN-APP-PLAN-APPROVAL-RECORD.json`). This file records what was built, how it was checked, and what
is still open. The three Core items of the phone checks (`docs/PHONE-CORE-FIXES-20261007.md`) ride in this release.

Status: **items 3.1 to 3.3 built, tested, rehearsed in a sandbox and independently reviewed, findings applied
(section 2); item 3.4 (JARVIS-Setup.exe) built with Inno Setup 6.7.3 and rehearsed in a sandbox, not yet reviewed
(section 3); version 4 Stage 7 scripts not started (section 4; the version 3 files were read and the changes
designed, see the handover). Nothing built here reaches the everyday JARVIS until the
release's Stage 7 check and update, on the owner's approvals.**

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

## 3. Item 3.4: JARVIS-Setup.exe (written, not yet built)

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
Not yet independently reviewed (the next session, with the version 4 scripts).

## 4. Still to do in this release

Version 4 Stage 7 scripts (copies of version 3; the Install phase from the Setup silently, the Installed-apps entry
checked, the uninstall through it, one update through the Setup); the release-notes entry; the build of 1.0.17 proper
from a clean tree; the comparison with 1.0.16; the release regression; the zip and Setup rehearsals; the sandbox
Stage 7; then `docs/STAGE7-CHECK-1.0.17.md` for the owner's approval, the VM check and the everyday update.

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
