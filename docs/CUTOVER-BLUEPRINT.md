# Cutover blueprint: making the tested JARVIS your everyday JARVIS (DRAFT)

Status: **DRAFT 2026-10-04 (Claude Code), started at the owner's request. Not approved, nothing executed.**
Cutover is an owner-only decision (`CLAUDE.md`). This document is the plan to be approved when the time comes;
writing it changes nothing on the PC. It updates `docs/SWITCH-OVER-PLAN.md` (2026-10-01), which was written
before the packaged release existed and describes switching to the development folder instead.

## In plain words

Today your everyday JARVIS runs from an old development folder and borrows Codex's Python. After the cutover
it is an installed app: its own folder, its own Python and Electron, a Desktop icon, starts when you sign in,
and carries your memory and settings across. The old JARVIS is copied from and then left exactly as it is, so
you can go back at any time.

## What must be true first

1. `STAGE_6_COMPLETE` (Gates 17 to 20). Gate 18 matters most here: it restores **your real backup** into the
   FINAL build inside the test VM, which is the same import the cutover does on this PC.
2. Your word to start. Nothing below is run on a hint or an earlier "go".
3. About 4 GB free on C: (the install is about 1.2 GB, unpacking needs the same again, plus your data). C: had
   16.5 GB free on 2026-10-04.

## The build

`JARVIS-1.0.11-60d406fb6398.zip`, 525,622,280 bytes, SHA-256
`1923651176dd3095e84b0628a5c7a90608b6db57fe06986670e0ea8246225a58`: the FINAL you selected, the exact file
tested in the VM. It is checked against that hash again before it is installed. No code changes in between.

## Where things are and will be

| | Old (today) | New (after cutover) |
|---|---|---|
| Program | `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis` | `%LOCALAPPDATA%\JARVIS\releases\1.0.11-60d406fb6398` |
| Your data (memory, conversations, tasks) | `...\outputs\jarvis\data` | `%LOCALAPPDATA%\JARVIS\data` |
| Your settings (personality, preferences, keys) | inside the old folder | `%LOCALAPPDATA%\JARVIS\config` |
| Starts from | "JARVIS Desktop" shortcuts | "JARVIS" shortcuts (Desktop and Startup) |

## The steps

Same working pattern as Stage 6: you double-click one launcher per step, each writes a record, I read the
record and tell you the next step. Nothing is deleted anywhere.

| # | Who | What happens | Can it be undone? |
|---|---|---|---|
| 1 | You | Quit the old JARVIS completely (tray icon). Close any JARVIS browser tab. | start it again |
| 2 | You | Fresh backup of the old JARVIS (Settings > Backup & recovery > Create verified backup, then Test restore). Both must pass. Fresh, so nothing said since the last backup is lost. | nothing changed |
| 3 | Launcher | Check the FINAL zip against its hash, unpack it, run its `install.cmd`. Installs into `%LOCALAPPDATA%\JARVIS`, creates the new "JARVIS" shortcuts. No administrator rights. The old shortcuts are **not** touched yet. | uninstall; your old JARVIS is untouched |
| 4 | Launcher | Dry run of the import: re-checks every checksum and the database of your backup and lists what would come across. Changes nothing. I read the list and report it to you. | nothing changed |
| 5 | Launcher, **after your OK on the list** | Import your data and your personality and preferences into the new install. The new install's empty data is moved aside, not deleted. Counts are checked against the backup; any failure puts everything back. | yes, automatically on failure |
| 6 | You | Put your AI keys into `%LOCALAPPDATA%\JARVIS\config\.env`. I never read or handle that file. | remove the file |
| 7 | You | Start the new JARVIS from its Desktop icon and check it: your memories and conversations are there, the AI answers, voice works, the version shows 1.0.11. | quit it |
| 8 | Launcher, **your decision** | Remove the old "JARVIS Desktop" shortcuts, so only the new JARVIS starts at sign-in. This is the actual switch. | old folder's `Install-JARVIS-Shortcuts.ps1` puts them back |
| 9 | You | Live with it. The old folder stays untouched as the fallback. | |
| 10 | You, later | After a trouble-free period (suggested: two weeks) you may retire the old folder and Codex. Keep the backup zip. | |

Only one JARVIS runs at a time: the old one is quit before the new one starts, and never both (one Core, one
memory).

## Going back

Quit the new JARVIS (tray > Quit JARVIS completely) and run `Install-JARVIS-Shortcuts.ps1` in the old folder.
The old JARVIS is exactly as you left it at step 1. What you said to the new JARVIS after the switch stays in
the new data folder; it can be carried back with a backup in the other direction.

## What is not carried across automatically

- **AI keys** (`.env`): step 6, yours to place.
- **Sign-ins held by the old app** (anything stored in its browser profile or session file): you sign in again
  where needed.
- **Speech and wake-word models**: not needed, the new build carries its own.

## Open points to settle before this is approved

1. **Not yet proven:** that a backup made by the *old* JARVIS imports cleanly into FINAL. Gate 18 tests exactly
   this in the VM with your real backup. If Gate 18 passes, this point closes.
2. **To check:** which connection settings besides the AI keys live outside the backup (maps key, Spotify,
   wearable connection file). I have not opened those files and will not; I need to work out from the code
   which of them the installed build reads, and list them for you.
3. **To write and rehearse:** the launchers for steps 3, 4, 5 and 8, tested in a sandbox folder first. They do
   not exist yet.
4. **Your choice:** whether step 2's backup is made by you in the old JARVIS's settings screen (recommended) or
   by command.
5. **Leftover to tidy with your OK:** `%LOCALAPPDATA%\JARVIS-package` (about 1.2 GB) from a rehearsal on
   2026-10-01.
6. **After the cutover:** the lean Stage 7 pass, then the two known rough edges (the "Core stopped" notice
   after shutdown; the installer stopping its own process) in the first release after cutover.

## Not part of the cutover

Phone and glasses access, any networking change, automatic backups, code clean-up. They follow in that order
in `docs/ROADMAP.md`, each on your word.
