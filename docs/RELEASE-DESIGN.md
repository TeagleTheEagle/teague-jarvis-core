# JARVIS release design (Stage 6 FINAL package, Stage 7 installer)

Status: **proposed** 2026-10-01, for owner approval before construction.
Governing criteria: reference/governing/STAGE6-MASTER-V1.txt Gates 17–20 (as amended by
AMENDMENT-v2), and the Stage 7 section of 1241140b (installer, update, uninstall,
reinstall, failure paths, release regression, release manifest).

## What was reused from earlier attempts

| Source | Kept | Not kept |
|---|---|---|
| deployment_test/package.py, upgrade.py (Stage 4 TEST) | Per-file SHA-256 manifest; side-by-side `releases/<build>`; verify-before-activate; rollback only if data unchanged; uninstall removes only manifest-listed files, never data; bundled Python stdlib + `_pth`; Electron identity check | DPAPI bindings, signed enrollment, maintenance fences, pipe transport, TEST client, deterministic provider/silent audio (TEST-only machinery) |
| Build-JARVIS.ps1 (PyInstaller) | — | Browser-only, data inside the program folder, opaque re-packing |

## Layout (per user, no administrator rights)

```
%LOCALAPPDATA%\JARVIS\
  current.json                 {"release": "<id>", "previous": "<id>|null"}  (atomic replace)
  JARVIS.ps1                   launcher: reads current.json, starts that release's desktop app
  releases\<version>-<build>\  read-only after install
    manifest.json              every file: path, sha256, bytes; versions; build identity
    app\                       JARVIS source (server, desktop, intelligence, static, ...)
    python\                    official CPython 3.12.10 embeddable (x64) + locked site-packages
    electron\                  Electron 44.2.0 (sha256 07b043bf…, the verified binary)
    models\                    Whisper base.en + openWakeWord models (bundled, hash-pinned)
  data\                        canonical data: jarvis.sqlite3, generated files, core.lock,
                               core-connection.json, logs\  — never touched by update/uninstall
  config\                      .env (owner-supplied keys), personality.txt, preferences.json
```

Program and data are separate, so updates, rollback, uninstall and reinstall never
touch memory or keys. One Core per data folder is already enforced (core_lock.py).

## Code changes needed

1. One runtime-layout module: data dir, config dir, models dir, Python path come from
   `JARVIS_DATA_DIR`, `JARVIS_CONFIG_DIR`, `JARVIS_MODELS_DIR` (set by the launcher), with
   today's repo-relative paths as the development fallback. Replaces scattered
   `ROOT / 'data'`, `APP_ROOT / '.env'`, `ROOT / 'personality.txt'`, model paths, and
   `.venv\Scripts\python.exe` in desktop/backend.cjs.
2. `tools/build_release.py`: assembles a release from pinned inputs only — the Python
   embeddable zip (python.org, SHA-256 pinned), wheels from `requirements-lock.txt`
   (pip `--require-hashes`, cp312 win_amd64), the verified Electron, hash-pinned models —
   then writes manifest.json and `JARVIS-<version>.zip` + release manifest (Stage 7 §16).
3. `install.ps1` / `maintenance.ps1` shipped in the zip: install, update (stage → verify →
   stop Core → switch current.json → start), rollback, uninstall (keep data by default;
   removing data needs an explicit typed confirmation), reinstall, verify.
4. Tests for each, plus rehearsal on this PC in a sandbox `%TEMP%` install root
   (install, A→B update, interrupted update at each step, rollback, uninstall,
   reinstall, data preserved) before any VM work.

## Owner-only steps (unchanged rules)

- Gate 16R: creating/qualifying the fresh Windows 11 VM (VirtualBox, admin) and the
  `RESUME_STAGE6_FRESH_VM` token with an approved execution prompt.
- `RESUME_STAGE6_RECOVERY` before Gate 18.
- Production cutover (switching your everyday JARVIS) and Stage 7 start.
- Entering API keys (config\.env) on any machine.

## Open choices (defaults proposed)

| Choice | Proposed default | Why |
|---|---|---|
| Installer form | Signed-hash zip + `install.ps1` | No admin, no new tooling; a setup .exe (e.g. Inno Setup) needs a system install |
| Models | Bundled | Offline install; Gate 17 "no hidden development-machine dependency" |
| Python | CPython 3.12.10 embeddable | Last 3.12 Windows binary release; matches the clean-VM baseline (3.12.10) |
| Personality/preferences | Move to config\ (first run copies defaults) | Updates must never overwrite them |
