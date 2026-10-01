# Development setup (workspace build)

Verified 2026-10-01 on the owner's PC: Python 3.12.10, Node 24.19.0, Git 2.55.
Everything below installs into this repository only (all paths are git-ignored).

## Install

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-test.txt
.venv\Scripts\python.exe setup_wake.py          # official openWakeWord models -> data\wake-models
cd desktop
npx pnpm@9 install --frozen-lockfile            # Electron 44.2.0 from pnpm-lock.yaml
node node_modules\electron\install.js           # pnpm skips Electron's download step
```

Package manager decision: **pnpm**. desktop/pnpm-lock.yaml is the only JavaScript
lockfile; the old `npm ci` instruction could not work. intelligence/ declares the same
single dependency (electron 44.2.0) and has no lockfile of its own.

The downloaded electron.exe SHA-256 is
`07b043bf9b0a0ac14a82fac0b612b7b7ed13cde727d706d74e41a45278ab51f1`, identical to the
binary used by the twelve-fix Electron verification.

Local voice (installed and verified 2026-10-01; the VC++ x64 runtime was already present):

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-local-voice.txt   # faster-whisper 1.2.1, ctranslate2 4.8.2
.venv\Scripts\python.exe setup_local_voice.py                             # Whisper base.en -> data\speech-models
.venv\Scripts\python.exe check_voice_offline.py                           # network blocked; must transcribe the test sentence
```

The first model load after a download or reboot can take about a minute (measured
51 s once, then 0.6 s); a background Core warms the model at startup.
Not installed yet: requirements-wearables.txt (PC microphone input for wearables).

## Test

```powershell
.venv\Scripts\python.exe -m unittest                       # 271 tests, all pass
cd desktop;      node --test test\*.test.cjs              # 34 tests, all pass
cd intelligence; node --test test\*.test.cjs              # 18 tests, all pass
Get-ChildItem test_*.cjs | ForEach-Object { node $_.Name } # 16 more root JS test scripts, all pass
```

The desktop backend test needs the wake models from setup_wake.py.

## Run the desktop app (isolated from the live installation)

```powershell
Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
.\desktop\node_modules\electron\dist\electron.exe desktop --user-data-dir="$PWD\data\dev-electron-profile"
```

Always pass `--user-data-dir`. The workspace build and the live installation are the
same Electron app: without it they would share `%APPDATA%\jarvis-desktop` and its
single-instance lock. The Core uses the repository's own `data\` folder (fresh
database, no personal memory) and listens on 127.0.0.1 only.

## One Core, many clients (background Core)

The desktop app no longer owns the Core. On launch it joins the running Core through
`data\core-connection.json`, or starts one with `server.py --background` if none is
running. Closing the desktop app (window or tray "Close desktop app") leaves JARVIS
running for the Intelligence window and future phone/glasses clients; tray
"Quit JARVIS completely" stops the Core. `Start JARVIS.cmd` now opens the desktop app.

- Only one Core may own a data folder (`data\core.lock`, released by Windows on any
  exit or crash). A second start is refused with a clear message.
- `data\core-owner.json`: pid and port only. `data\core-connection.json`: origin and
  the client token (same trust level as the old desktop session file; git-ignored,
  removed when the Core stops). Core output goes to `data\logs\core.log`.
- To stop a dev Core without the tray: use "Quit JARVIS completely", or end the
  `python3.12.exe ... server.py --background` process.

Without a `.env` file no AI provider key is present, so AI replies are not expected
to work in this build (provider behaviour without keys not yet verified). Real provider keys are placed by the
owner only (git-ignored) and are never read or printed by Claude.

## Build and install a release (docs/RELEASE-DESIGN.md)

```powershell
.venv\Scripts\python.exe tools\build_release.py --version 1.0.0     # from a clean committed tree
build\release\JARVIS-<version>-<commit>\install.cmd                 # per user, no admin
```

Inputs are pinned (Python embeddable, requirements-lock.txt, Electron, models); the build
refuses anything that does not match. Rehearse in a sandbox before a real install:
`release\python\python.exe installer.py install --package . --home %TEMP%\jarvis-sandbox-home --no-shortcuts`,
then `JARVIS.ps1` in that home. Rollback / uninstall / verify / status: `installer.py <action> --home <home>`.
