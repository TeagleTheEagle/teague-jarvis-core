# Switch-over plan: make the new JARVIS your everyday JARVIS

Prepared 2026-10-01. **Owner decision required before step 4 and step 6.** Nothing here
has been run against your real data. Tools were tested on synthetic installations only
(`test_switch_over.py`).

- **Old JARVIS**: `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis`
  (its Python runs from Codex's runtime folder — keep Codex installed until step 8).
- **New JARVIS**: `C:\Users\jonny\JARVIS-claude-workspace\repo`.

The old installation is **copied from, never changed or deleted**. It stays as the
rollback for as long as you want.

| Step | Who | What happens |
|---|---|---|
| 1. Quit the old JARVIS | You | Tray icon → *Quit JARVIS Desktop*. Also close any browser JARVIS tab. |
| 2. Back up the old JARVIS | You (or Claude, with your OK) | Old JARVIS → Settings → **Backup & recovery** → *Create verified backup*, then *Test restore in temporary folder*. Both must pass. The backup lands in `outputs\jarvis-backups\<ID>.zip`. (Command line: `.\.venv\Scripts\python.exe recovery.py create`, then `rehearse --id <ID>` in the old folder.) |
| 3. Dry run in the new JARVIS | Claude | `.venv\Scripts\python.exe switch_over.py --archive <backup.zip>` — re-verifies every checksum and the database, lists what would be imported, **changes nothing**. |
| 4. Import your memory | Claude, **after your approval** | Same command with `--apply`. Quit the new test JARVIS first (it refuses otherwise). Only saved data is imported (memory, conversations, tasks, settings, generated documents); the new code stays. The test memory is moved to `data\pre-switchover-<time>`, not deleted. Database integrity and row counts are checked against the backup; any failure puts everything back. Add `--include-personal-config` to also take the old personality/preferences if they differ. |
| 5. Check it | You | Open the new JARVIS: your memories, conversations and settings should be there; real AI and voice working. |
| 6. Switch the shortcuts | You, **your decision** | In the new folder run `Install-JARVIS-Shortcuts.ps1` (right-click → Run with PowerShell). It replaces the Desktop and Startup *JARVIS Desktop* shortcuts, so JARVIS now starts from the new installation at login. No admin rights needed. |
| 7. Live with it | You | Keep the old installation untouched as the fallback. |
| 8. Retire the old one | You, later | After a trouble-free period (suggested: two weeks), you can uninstall Codex. The new JARVIS does not depend on it. Keep the backup .zip. |

## Rollback (any time)

Quit the new JARVIS (tray → *Quit JARVIS completely*), then run the **old**
`Install-JARVIS-Shortcuts.ps1` in `outputs\jarvis`. The old JARVIS is exactly as you left
it, minus anything said to the new JARVIS after the switch (that stays in the new data
folder and can be brought back the same way in reverse).

## What is not carried over automatically

- `.env` (API keys): already copied by you on 2026-10-01; never handled by Claude.
- Speech and wake-word models: already installed in the new JARVIS.
- Windows shortcuts: step 6.
- The old installation's Codex-runtime Python: not needed by the new JARVIS.
