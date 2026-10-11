# Short human-operated Stage 4 TEST check

This is the remaining human acceptance criterion. Automated tests cannot be recorded as your manual result. The helper uses the existing authenticated TEST controller, isolated synthetic data and two actual Electron TEST clients. It does not attach to production, enable hardware or call a paid provider.

The failed run `human-lifecycle-7cc0db70a76149c9954eb82fc4c0c5b5.json` is preserved. Its SELECT and DENIAL inputs were correct; the driver attempted the wrong executable identity before reaching shutdown policy. The corrected driver performs DENIAL through the real authenticated Electron client and requires a matching Core-side policy receipt. Always start a new run below; never reuse the previous TEST identity or resume at CRASH.

Open a normal PowerShell window and run:

```powershell
Set-Location -LiteralPath 'C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis'
.\.venv\Scripts\python.exe -B tests\lifecycle_stage4\fixtures.py --human-lifecycle
```

Follow the console prompts:

1. Confirm both windows say **STAGE4_TEST / authenticated**. Copy the exact `SELECT TEST-...` text printed in the console. This selects only that disposable data identity.
2. Type `DENIAL`. The actual authenticated Teague TEST client attempts Core shutdown. The console must print `Ordinary shutdown: DENIED (authenticated Electron; Core policy SCOPE)`. Both clients and the Core must remain available. A handshake error or traceback is not this expected denial.
3. Type `CRASH`. Only the disposable Intelligence renderer is deliberately crashed; Teague and the separately authenticated controller must remain usable.
4. Type `EMERGENCY`. Core must become SUSPENDED while retaining ownership.
5. Type `SHUTDOWN`. Core must exit, release its lifetime lock and close the TEST clients normally.

The helper prints `HUMAN TEST LIFECYCLE PASS` only after all required checks. Tell Codex the result; the nonsecret evidence path is printed automatically. Credentials remain in private process pipes/memory and are not printed or saved in evidence. A failed/aborted session is preserved and cooperative authenticated cleanup is attempted; no unrelated process is terminated. Do not treat a traceback as PASS.

Physical microphone/headset/audibility remain deferred. This exercise validates human selection and use of existing TEST lifecycle controls, not production readiness or physical media.
