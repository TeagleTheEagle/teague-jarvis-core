# Updating your everyday JARVIS to 1.0.14

Status: **DRAFT (2026-10-05, Claude Code). Not approved; nothing has run on your real JARVIS.** Updating the everyday
JARVIS is your decision (`CLAUDE.md`). It is offered only after 1.0.14 passes its Stage 7 check in the VM
(`docs/STAGE7-CHECK-1.0.14.md`). The launcher is to be rehearsed in a sandbox on D: first (results added here).

## In plain words

Your everyday JARVIS (1.0.11, installed at `%LOCALAPPDATA%\JARVIS` since the switch-over) gets the new program
version 1.0.14. Your memories, conversations, personality, preferences and keys stay exactly where they are: an
update only adds the new program beside the old one and switches to it. The old version stays installed beside it,
so going back is one step. Before anything changes, a fresh backup of your data is made and tested.

## What 1.0.14 brings

The fixes in `docs/POST-CUTOVER-FIXES.md`: no "Core stopped" box when you quit; the version shown in Settings >
About; clear messages when an AI provider refuses (no credits versus a rate limit, which provider); backups on a
read-only disc no longer hang; Gemini's default model updated; updates and uninstalls that wait for JARVIS to close
properly and refuse rather than half-finish.

## What is proven first

- On this PC: the build compared with 1.0.11 (only the changed JARVIS files differ), its full test suite with its
  own Python and Electron, the zip install, and the whole Stage 7 pass in a sandbox, including updating from 1.0.11
  while running, rolling back and an update killed halfway (`docs/release-rehearsal-20261005-1014/README.md`).
- In the test VM: the Stage 7 check of 1.0.14 (must pass before this plan is offered for approval).
- 1.0.14 changes no part of the database layout (no table or schema change since 1.0.11), so 1.0.11 reads your data
  just as before if you ever roll back.

## The steps

You double-click one launcher, `D:\JARVIS-update-1.0.14\tools\update-step.cmd`, once per step, in your own account
(jonny), with JARVIS **quit** (right-click its icon near the clock > Quit JARVIS completely). Each step writes a
record and stops; you tell me "step N done" and I check the record before the next. No administrator rights; a UAC
prompt is a STOP. Nothing is deleted anywhere.

| # | Who | What happens | Undo |
|---|---|---|---|
| 1 | Launcher | Checks: the 1.0.14 package against its hash; your JARVIS is 1.0.11 and every program file verifies; JARVIS is not running; 4 GB free on C:. Unpacks the package to `D:\JARVIS-update-1.0.14\package`. Changes nothing in your JARVIS. | nothing changed |
| 2 | Launcher | A fresh backup of your JARVIS with its own backup code (the same as Settings > Backups: "Create verified backup", then "Test restore"); the backup lands in `%LOCALAPPDATA%\JARVIS\data-backups` and a hash-checked copy in `D:\JARVIS-update-1.0.14\backup`. Your program files are checked again afterwards. | the backup simply stays |
| 3 | Launcher | The 1.0.14 installer adds 1.0.14 beside 1.0.11, checks every file, and switches your JARVIS to it in one step. Data, settings, keys, profile and shortcuts are not touched (the record proves the database file is byte-for-byte the same before and after). JARVIS is **not** started. | step R |
| 4 | You | Start JARVIS from its Desktop icon and check (list below). | |
| 5 | You | Restart the PC once (Start > Power > Restart, jonny) and check JARVIS starts by itself after you sign in (never tested on this PC yet). | |
| R | Launcher, **only on your word** | If anything is wrong in step 4 or 5: tell me; I record your word and one more double-click switches your JARVIS back to 1.0.11 (still installed). | update again later |

**Your check in step 4** (5 minutes): Settings > About shows `Version 1.0.14-e03872680e1d (installed)`; your
memories and recent conversations are there; ask something and JARVIS answers (Groq); say something and voice
works; then quit from the icon near the clock: no "Core stopped" box should appear.

## Records

`D:\JARVIS-update-1.0.14\evidence\` (check.json, backup.json, update.json, rollback.json if used); I copy them to
`docs/update-1.0.14-evidence/` with a manifest. The records hold hashes, counts per database table and timings, never
your messages or keys. I never read your key file or the contents of the backup.

## What you accept by approving

1. **The update runs on your real JARVIS** (owner-only), started by you, one step at a time.
2. **Keys and provider stay as they are** (Groq). If you want Gemini now, add the line `GEMINI_MODEL=gemini-3.8-flash`
   to your key file yourself, separately; Qwen waits for Alibaba's identity check.
3. **Known limits that remain:** install under a non-administrator Windows account is untested (your account is an
   administrator; the update itself needs no administrator rights); a program JARVIS opened (for example Notepad)
   should be closed before an update or uninstall.
4. **Space:** 1.0.14 adds about 1.2 GB on C: (13 GB free today); 1.0.11 stays as the rollback copy. Removing it
   later is a separate step on your word.

## After the update

A few days of normal use; then, on your word: the cleanup listed in `docs/CURRENT-STATUS.md` (test VM, data copies
on D:, the old folder and Codex, the old 1.0.11 release folder).

## Approval

After the Stage 7 check has passed and this plan says READY FOR YOUR APPROVAL, reply in your own words, for example:
"I approve the update of my everyday JARVIS to 1.0.14". I then record it, put the launcher in
`D:\JARVIS-update-1.0.14\tools\` with its hashes, and you start with step 1.
