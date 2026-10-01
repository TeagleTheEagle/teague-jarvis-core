# Clean-deployment hardening — 2026-09-18

## Scope and result
Deployment/setup only. No runtime/provider/UI/Store/voice identity changes, production restart, VM/snapshot changes, live provider calls, installations or acceptance commit. Existing unrelated working-tree changes were preserved.

Owner reports clean Windows VM PASS on Python 3.12.10, native STT, Fish voice, backend/UI/local commands; snapshot JARVIS-CLEAN-DEPLOY-PASS remains untouched. This turn did not independently inspect/replay that VM result. OpenAI live response is externally deferred for unavailable balance.

## Changed files
- README.md: replace Python 3.11+ instructions with validated 3.12 x64 setup and explicit Node/VC++ requirements.
- Build-JARVIS.ps1: read-only Python/Windows preflight before build mutation.
- requirements-local-voice.txt: pin CTranslate2 4.8.2 alongside faster-whisper 1.2.1.
- requirements-test.txt: isolate pytest 9.1.1 from runtime requirements.
- check_windows_setup.py: read-only version/bitness, optional Node 24.x, System32-only VC++ DLL checks and bounded native STT import probe. No .env or Core import.
- Setup-Windows.ps1: explicit py -3.12 selection, reject incompatible existing venv, optional STT/test dependencies, fail on subprocess errors, post-install import verification. No system installer, launcher, credential copy or model download.
- test_windows_setup.py: six focused tests, including missing prerequisites and unsupported runtime.
- docs/WINDOWS-DEPLOYMENT-PREREQUISITES.md: deployment assumptions, model provisioning, credentials, commands and limitations.

## Actual validation
- `.venv/Scripts/python.exe -B check_windows_setup.py --local-voice --tests --installed`: PASS; Python 3.12.14, Node v24.19.0, required native libraries and STT imports.
- `.venv/Scripts/python.exe -B -m unittest discover -s . -p test_*.py -q`: 212 PASS (existing suite discovery began before new focused file was created); python-regression.log.
- `.venv/Scripts/python.exe -B -m unittest test_windows_setup -v`: 6 PASS; focused.log.
- `node --test desktop/test/*.test.cjs intelligence/test/*.test.cjs`: host-context 35 PASS, 0 fail/skip; desktop-host.log.
- `node test_voice.cjs`: PASS; voice-regression.log (script does not publish a numeric assertion total).
- PowerShell Language.Parser.ParseFile on Setup-Windows.ps1 and Build-JARVIS.ps1: no syntax errors.

Preserved validation limitations: the first restricted-context Node command produced no output before interruption; desktop-regression.log is retained. The host-context rerun passed; this does not establish why the first invocation stalled. Direct powershell -NoProfile -File Setup-Windows.ps1 -LocalVoice -Tests -CheckOnly was rejected by execution policy before script execution. No policy was changed/bypassed. Therefore the PS setup flow and actual pip/venv installation were not validated end-to-end here; syntax checks and Python preflight are not substitutes. A restricted CIM process query was denied; host-context observation was used instead.

## Remaining limitations and rollback
The direct native STT pair is pinned; transitive packages and downloaded model revision are not fully locked for offline/bit-for-bit installation. Existing base requirements retain their reviewed ranges. Exact clean-VM Node/CTranslate2 versions were not provided. The host pair is verified here, not claimed identical to the VM. No model inference or new paid voice test was run.

Existing launchers and canonical packaged deployment logic remain unchanged. The new setup path cannot grant cutover or cross-machine recovery authority. End-to-end setup validation should use a disposable clone, never modify the accepted snapshot. No Stage 6/7 acceptance is inferred from these source-setup tests.

Rollback: reverse only the documented README/build/local-voice edits and remove the five new setup/test/documentation files after review; retain evidence. No data/runtime rollback or schema action is required.

HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
