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

Optional, not installed yet: requirements-local-voice.txt (local speech-to-text) and
requirements-wearables.txt (PC microphone input for wearables).

## Test

```powershell
.venv\Scripts\python.exe -m unittest                       # 263 tests, all pass
cd desktop;      node --test test\*.test.cjs              # 32 tests, all pass
cd intelligence; node --test test\*.test.cjs              # 18 tests, all pass
```

The desktop backend test needs the wake models from setup_wake.py.

## Run the desktop app (isolated from the live installation)

```powershell
Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
.\desktop\node_modules\electron\dist\electron.exe desktop --user-data-dir="$PWD\data\dev-electron-profile"
```

Always pass `--user-data-dir`. The workspace build and the live installation are the
same Electron app: without it they would share `%APPDATA%\jarvis-desktop` and its
single-instance lock. The Core it starts uses the repository's own `data\` folder
(fresh database, no personal memory) and listens on 127.0.0.1 only.

Without a `.env` file no AI provider key is present, so AI replies are not expected
to work in this build (provider behaviour without keys not yet verified). Real provider keys are placed by the
owner only (git-ignored) and are never read or printed by Claude.
