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
backups, device pairing and the phone client, glasses.
