# Switch-over plan: making the tested JARVIS your everyday JARVIS

Status: **READY FOR YOUR APPROVAL (2026-10-04, Claude Code). Not approved, nothing executed on your real
JARVIS.** The switch-over is an owner-only decision (`CLAUDE.md`). The launcher was rehearsed in a sandbox on D:
the same day (`docs/release-rehearsal-20261004/rehearse-cutover.ps1`). This replaces the draft of earlier today
and `docs/SWITCH-OVER-PLAN.md` (2026-10-01).

## In plain words

Your everyday JARVIS lives in an old development folder and borrowed Codex's Python, which is now gone, so it
cannot start. After the switch-over JARVIS is an installed app: its own folder, its own Python, a Desktop icon,
starts when you sign in, with your memory and settings carried across. The old folder is only read and is left
exactly as it is.

## What is already proven

- Stage 6 is complete (`STAGE_6_COMPLETE`, 2026-10-04): this exact build installs, runs, updates and rolls back
  on a clean Windows PC.
- Gate 18: this exact backup of your data (`bcc2753f…zip`, made today) restored into this exact build in the
  test VM: 176 data files, every count equal (1,133 messages), JARVIS started on it.

## The build and the backup

- Build: `JARVIS-1.0.11-60d406fb6398.zip`, 525,622,280 bytes, SHA-256
  `1923651176dd3095e84b0628a5c7a90608b6db57fe06986670e0ea8246225a58` (FINAL; checked again before installing).
- Backup: `...\outputs\jarvis-backups\bcc2753f736f43ba946ec3f342b35c3a.zip`, SHA-256
  `b81be404e1677c48cffc7d26a8d77998b54fa2fa588bd4eeb5614e841ce0bfe3`, made 2026-10-04 by the old JARVIS's own
  backup code, test-restore passed. The old JARVIS has not run since, so it is current; step 1 checks that the
  old database has not changed since the backup and stops if it has.

## Where things are and will be

| | Old (today) | New (after the switch-over) |
|---|---|---|
| Program | `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis` | `%LOCALAPPDATA%\JARVIS\releases\1.0.11-60d406fb6398` |
| Your data | `...\outputs\jarvis\data` | `%LOCALAPPDATA%\JARVIS\data` |
| Your settings and keys | inside the old folder | `%LOCALAPPDATA%\JARVIS\config` |
| Starts from | "JARVIS Desktop" / "JARVIS INDUSTRIES" shortcuts | "JARVIS" shortcut (Desktop and Startup) |
| Working files of the switch-over | | `D:\JARVIS-cutover\` (unpacked package, backup copy, records, old shortcuts) |

## The steps

You double-click one launcher, `D:\JARVIS-cutover\tools\cutover-step.cmd`, once per step, in your own account
(jonny). It does one step, writes a record, and stops. After each step you tell me "step N done" and I check the
record before the next. Nothing is deleted anywhere. No administrator rights; a UAC prompt is a STOP.

| # | Who | What happens | Undo |
|---|---|---|---|
| 1 | Launcher | Checks: the build's hash; 4 GB free on C: (14.4 GB free today); nothing installed at `%LOCALAPPDATA%\JARVIS`; no JARVIS running; the backup's hash and test receipt; old database unchanged since the backup. Changes nothing. | nothing changed |
| 2 | Launcher | Unpacks the build to `D:\JARVIS-cutover\package` and installs it with its own installer into `%LOCALAPPDATA%\JARVIS`; verifies every file; creates the new "JARVIS" Desktop and Startup shortcuts. The new JARVIS is **not started**. The old shortcuts are not touched. | uninstall; old JARVIS untouched |
| 3 | Launcher | Copies the backup to `D:\JARVIS-cutover\backup` (hash-checked), and the new install verifies it and lists what would come across. Changes nothing in the new JARVIS. I read the list and report it to you. | nothing changed |
| 4 | Launcher, **after your OK on the list** | Imports your data, personality and preferences. Counts are checked against the backup; any failure puts everything back. Program files are verified again. | automatic on failure |
| 5 | You | Your AI keys: copy your existing key file into the new JARVIS with one command I give you (I never read or handle that file). | remove the file |
| 6 | You | Start the new JARVIS from its Desktop icon and check it: your memories and conversations are there, the AI answers, voice works, the version shows 1.0.11. | quit it |
| 7 | Launcher, **your decision after step 6** | Moves the three old shortcuts (Desktop: "JARVIS Desktop", "JARVIS INDUSTRIES"; Startup: "JARVIS Desktop") into `D:\JARVIS-cutover\old-shortcuts\`. This is the actual switch: only the new JARVIS starts at sign-in. | move the files back |
| 8 | You | Live with it. The old folder and the backup stay untouched. | |

Only one JARVIS runs at a time (one Core, one memory). The old one cannot start at present, so there is no
overlap.

## Rehearsed, and not rehearsed

- **Rehearsed in a sandbox on D: (2026-10-04):** all launcher steps with the real FINAL zip, a sandbox install
  folder, a copy of the old code with made-up data and a made-up backup, and made-up old shortcuts: check PASS,
  install PASS (unpack 17 s, install 30 s, verified), dry run PASS, import refused without your OK then PASS,
  shortcut move refused without your decision then PASS (3 moved, nothing deleted), a second run changes nothing.
  Refusals PASS: not approved; wrong backup hash. The rehearsal found and fixed one defect (the zip has a top
  folder).
- **Not rehearsed, because it can only happen for real:** installing into the real `%LOCALAPPDATA%\JARVIS`;
  creating shortcuts on your real Desktop (which OneDrive redirects) and Startup folder (shortcut creation itself
  passed in the VM at Gate 17); your real backup on this PC (it passed in the VM at Gate 18); the key file;
  the refusal when an old shortcut does not point at the old JARVIS.

## What you accept by approving

1. **No working "old JARVIS" to go back to.** Its Python is gone, so it cannot start today either. Your data
   stays safe in three places: the old folder (untouched), the backup zip, and the copy on D:. If the new JARVIS
   misbehaves, the way back is to uninstall it (your data and the old folder are unaffected) and fix forward.
   Repairing the old JARVIS's Python is a separate job I have not planned.
2. **The backup is today's Gate 18 backup**, not a new one. It is the exact file proven in the VM, and nothing
   has been said to the old JARVIS since.
3. **Keys and AI provider.** All connection settings are lines in one key file (`.env`): AI providers, voice,
   search, maps/YouTube, Spotify client id. Copying it gives the new JARVIS the same provider the old one used.
   Qwen (your new Alibaba account) can be switched on later by you in that file, once Alibaba has finished the
   identity check and `tools/host/Test-QwenKey.ps1` says WORKS. The optional phone/wearable connection file is
   not copied (phone work is a later phase). Sign-ins held in the old app's browser profile do not carry over.
4. **Known limitations of 1.0.11** (from Stage 6): slow shutdown possible; a "Core stopped" notice after
   shutdown; hangs if a backup lies on read-only media; install under a non-administrator Windows account
   untested (your account is an administrator; the install itself runs without administrator rights).
5. **Leftover from an earlier rehearsal:** `%LOCALAPPDATA%\JARVIS-package` (about 1.2 GB) stays; it is not used.

## After the switch-over

- A trouble-free period (suggested: two weeks), then on your word: delete the test VM and the data copies on D:,
  and retire the old folder and Codex. Keep the backup zip.
- Lean Stage 7 (packaged-app acceptance) on the test VM: its own plan, your word to start.
- First release after the switch-over: the fixes listed in the Stage 6 verdict.

## Not part of the switch-over

Phone and glasses access, any networking change, automatic backups, code clean-up (`docs/ROADMAP.md`), Stage 7.

## Approval

Reply in your own words that you approve this switch-over plan, for example: "I approve the switch-over plan".
I then record it, put the launcher in `D:\JARVIS-cutover\tools\` with its hashes, and you start with step 1.
