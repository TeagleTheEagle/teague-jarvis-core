# Validated Windows setup

Windows 11 x64; Python **3.12 x64**. Owner-reported clean VM validation used
3.12.10; this host uses 3.12.14. Python 3.11.9 reproduced a wearable cancellation
failure. This is a compatibility baseline, not a newly established explanation
of that failure. Preserve `JARVIS-CLEAN-DEPLOY-PASS`; never modify that snapshot.

Install prerequisites through their official installers before setup:

- Python 3.12 x64 with the Windows `py` launcher.
- Node.js 24.x for the JS-backed tests and Electron source tooling. This host
  uses 24.19.0; the clean VM's exact Node patch was not supplied. Packaged clients
  carry their own runtime; installing Node is not a requirement for every end user.
- Microsoft Visual C++ v14 x64 Redistributable for CTranslate2/faster-whisper.
  Official installer: https://aka.ms/vs/17/release/vc_redist.x64.exe . Do not copy
  individual DLLs from a development machine or disable Windows protections.

From a fresh source checkout:

```powershell
.\Setup-Windows.ps1 -LocalVoice -Tests -CheckOnly
.\Setup-Windows.ps1 -LocalVoice -Tests
.\.venv\Scripts\python.exe -B setup_local_voice.py
```

Setup checks Windows/Python bitness and version before creating anything; a wrong
existing venv is rejected rather than overwritten. Preserve the old environment
and recreate a separate one under Python 3.12. Setup does not install system
prerequisites automatically or elevate privileges. Missing prerequisites fail
with actionable messages. No Core is started and no credentials are read.

`requirements.txt` is the existing runtime dependency set.
`requirements-local-voice.txt` adds faster-whisper 1.2.1 and CTranslate2 4.8.2
(the installed host pair); `requirements-test.txt` contains only pytest 9.1.1.
The optional wearable microphone dependency remains in requirements-wearables.txt.
This is a pinned native STT pair, not a full transitive/offline dependency lock.
The clean VM's exact CTranslate2 package version was not supplied; reproduce the
pin in a disposable clone before claiming identical VM package composition.

The final setup check loads the required DLLs from System32 and imports both
native STT packages in a bounded subprocess. It does not download models or open
a microphone. `setup_local_voice.py` is the separate explicit model download;
it requires network access. Offline deployments must provision reviewed model
artifacts separately. Wake-model provisioning remains `setup_wake.py`.

Configure `.env` locally through the existing credential boundary. Never include
it, API credentials, enrollment records or production data in packages, reports
or snapshots for distribution. Setup neither copies nor logs these files.

Validation (offline provider tests; no paid requests):

```powershell
.\.venv\Scripts\python.exe -B check_windows_setup.py --local-voice --tests --installed
.\.venv\Scripts\python.exe -B -m unittest test_windows_setup -v
.\.venv\Scripts\python.exe -B -m unittest discover -s . -p 'test_*.py' -q
node --test desktop/test/*.test.cjs intelligence/test/*.test.cjs
node test_voice.cjs
```

JavaScript dependencies use pnpm, not npm: the only lockfile is
desktop/pnpm-lock.yaml (there is no package-lock.json, so `npm ci` cannot work).
See docs/DEV-SETUP.md for the exact commands. Native TEST bridge compilation has its
separate toolchain requirements in stage4_native/README.md. Neither this setup nor
Build-JARVIS.ps1 grants production cutover or changes runtime routing.

The older portable builder is not the canonical deployment acceptance mechanism.
It now rejects an unsupported Python before building, but no release was rebuilt
by this hardening. Existing launcher fallback behavior is intentionally unchanged;
use the explicit checked setup path, not its legacy developer-runtime fallback.

The owner reports clean backend/UI/local commands, local STT and Fish voice PASS.
OpenAI live response remains externally deferred for unavailable API balance.
These reports do not independently establish cross-machine canonical recovery,
production cutover or final installer acceptance. Historical reports remain intact.
