# Fixes for the first release after the switch-over

Collected during Stage 6 and the switch-over (2026-10-04). Nothing here is started; source changes were frozen
until the switch-over was complete. Each needs a test; the release then goes through the normal build and
regression, and reaches the everyday JARVIS as an update (owner's word).

| # | What | Found |
|---|---|---|
| 1 | Verifying or importing a backup on read-only media never returns (`recovery.verify` makes its temp folder beside the archive; `tempfile.mkdtemp` retries forever on Windows). Use a writable temp location and fail with a message. | Gate 18 incident 04 |
| 2 | Stopping a running JARVIS can take about 95 s (installer waits for the Core, then ends window processes); the installer can stop its own process. | Gate 19 G5/G6; earlier note |
| 3 | The desktop shell shows a "Core stopped" notice after a requested shutdown. | Gate 17 |
| 4 | The interface does not show the installed version (release id). Show it in Settings. | switch-over step 6 |
| 5 | Every provider HTTP 429 is worded "Rate limit reached"; OpenAI's 429 `insufficient_quota` means no credits. Say which. | switch-over step 6 |
| 6 | Default Gemini model `gemini-2.5-flash` is retired by Google (the provider names `gemini-3.8-flash`). Update the default. | `tools/host/Test-AiKeys.ps1` on 2026-10-04 |
| 7 | Gate drivers before any reuse: restart check by uptime, not wall clock; quit JARVIS first; restore from a writable copy; record build.UBR in the Gate 18 script. | Gates 17, 18, 20 |
| 8 | Install under a non-administrator Windows account is untested. | Gate 16R disposition |
| 9 | `tools/host/Copy-BackupForGate18.ps1` (v1) lists every file because PowerShell 5.1 ignores `-Include` with `-LiteralPath`; v2 replaces it. Keep v1 only as evidence. | Gate 18 incident 01 |

Roadmap items that follow (`docs/ROADMAP.md`): lean Stage 7, code clean-up and provider pruning, automatic
backups, device pairing and the phone client, glasses. (Note added 2026-10-04: lean Stage 7 is done,
`STAGE_7_COMPLETE`.)

## Status in 1.0.12 / 1.0.13 (2026-10-04/05)

Started on the owner's "next move" / "now do the next move". Each fix was designed, challenged by an
independent check, then written with tests (root-level tests, so the release regression runs them).
The table above is kept as it was recorded; corrections are noted here. Build 1.0.12-d28016b12efe passed the
regression and the zip install, but the sandbox Stage 7 rehearsal found that an uninstall could start removing
program files while a closing JARVIS window still ran (item 2 below); 1.0.12 was never offered and is superseded
by 1.0.13 with that fixed.

| # | Status | Tests |
|---|---|---|
| 1 | Fixed. Working folders are made by a bounded helper (`recovery.work_folder`), never `tempfile`; a backup on read-only media is checked in the installation's own backup folder, or refused at once with a plain message. | `test_recovery.ReadOnlyMediaTests`, `test_switch_over` (read-only media, data folder refusing, command line) |
| 2 | Fixed in part. Finding: most of the ~95 s recorded as `stop` at Gate 19 G6 / Stage 7 G6 was re-verification of an already installed release, counted under the wrong label (a missing lap); clean stops measured 4.9-6.1 s in the VM and 1.1 s on the PC. Now: a separate `verify_installed` phase, rollback and uninstall report phase seconds, no 30 s wait on a connection file left by a crashed Core, the local shutdown request ignores proxy settings, the process-ending step never ends the installer itself, and install, rollback and uninstall refuse to run with an installed release's own Python. In 1.0.13: the process-ending step waits until the ended programs have really exited, looks again (up to 5 rounds) and refuses before any switch or deletion if one is still running; uninstall removes the launcher first and retries a file still in use for 10 s, so a rare failure leaves JARVIS not installed rather than half-removed (found in the 1.0.12 sandbox Stage 7 rehearsal: an uninstall reached `electron.exe` while a closing window still ran). Not done: a faster process-ending step (still PowerShell; a larger rewrite was judged not worth the risk). | `test_installer` (11 new, one ends copies of Windows' PING.EXE in a test folder) |
| 3 | Fixed. The desktop app tells a requested stop (the Core removes its connection file), a new Core (another token) and a crash (file left, process gone) apart; only a crash ("stopped unexpectedly") or a Core that stops answering ("not responding"; Claude's wording, the owner may change it) shows a box. Timing uses a steady clock, not the wall clock. The first update 1.0.11 -> 1.0.12 still runs 1.0.11's desktop code, so the old box can appear during that one update. | `desktop/test/core-watch.test.cjs`, two new tests in `desktop/test/backend.test.cjs` |
| 4 | Fixed. Settings > About shows "Version <release id> (installed)" or the development revision. | `test_settings_version.cjs` |
| 5 | Fixed. 429s are classified per provider from documented codes only: OpenAI no credits / spend or usage limits and Qwen bill problems say "billing limit, waiting will not help" and set no pause; rate limits name the provider; the interface no longer says "Groq" for every provider; Gemini 402 is no longer worded as Fish Audio. | `test_provider_errors.py`, `test_jarvis.LocalTests.test_billing_refusal_reaches_the_interface_without_a_pause` |
| 6 | Fixed. Default `gemini-3.8-flash` (Google's stable Flash model). Correction: Google did not retire gemini-2.5-flash; since 2026-09-18 it serves 2.5 models only to projects that used them before. The replacement id comes from Google's documentation, not from a saved Test-AiKeys record. A `GEMINI_MODEL` line in the key file still wins; `Test-AiKeys.ps1` now prints a hint when a gemini-2 model is refused. | `test_gemini_provider` (5 new) |
| 7 | Restart check by uptime and "quit JARVIS first" are in the Stage 7 scripts; the Stage 6 gate drivers stay unchanged as evidence. Recording build.UBR in Stage 7 and making the Stage 7 scripts work for a second release are part of preparing the 1.0.12 Stage 7 check (owner approval). | - |
| 8 | Still untested; no code needing administrator rights was found. A real test needs a standard account in the VM (owner). | - |
| 9 | Nothing to do in code (v1 is kept as evidence; v2 is the copy in use). | - |
