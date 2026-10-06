# Updating your everyday JARVIS to 1.0.15

Status: **READY FOR YOUR APPROVAL (2026-10-06, Claude Code). Rehearsed in a sandbox: all 13 checks passed. Nothing has run
on your real JARVIS.** Updating the everyday JARVIS is your decision (`CLAUDE.md`). 1.0.15 passed its Stage 7 check in
the test VM on 2026-10-06 (`STAGE_7_COMPLETE`, 27 of 27 checks, `docs/stage7-1.0.15-evidence/`).

## In plain words

Your everyday JARVIS (1.0.14, installed at `%LOCALAPPDATA%\JARVIS` since 2026-10-05) gets the new program version
1.0.15. Your memories, conversations, personality, preferences and keys stay exactly where they are: an update only
adds the new program beside the old one and switches to it. 1.0.14 stays installed beside it, so going back is one
step. Before anything changes, a fresh backup of your data is made and tested.

## What 1.0.15 brings

Everything in `docs/RELEASE-1.0.15-SCOPE.md` and the 1.0.15 entry of `release-notes.json`, in short:

- **The new look** for the whole interface: one header with eight everyday sections and More, the dashboard built
  from real data only, chat replies shown with their formatting.
- **AI providers:** OpenAI and Qwen only, with Fish Audio or the Qwen cloned voice for speech. Groq, Gemini and
  ElevenLabs are gone. **Answer speed** for Qwen in Settings > AI (Deep stays the default). **Backup provider** on:
  when the chosen provider refuses or cannot be reached, the other one answers that question and says so.
- **Permissions in one place** (Settings > Permissions): every tool listed, each can be switched off or set to ask
  first; an **emergency stop that holds** until you press RESUME on the PC, also across a restart; changes JARVIS
  makes to its own personality or style ask first.
- **Devices** (Settings > Devices): pairing by a code read from the PC, a key per device, revoke at any time. JARVIS
  still listens on this PC only; nothing is opened to the network. This is the PC side of the phone app.
- **Speech recognition** on this PC as before, or by the chosen provider (a choice in Settings > AI).
- **Automatic backups** (Settings > Backups): off until you choose a folder.
- **Answers without the internet:** if no provider can be reached and Ollama with a chat model is installed, the
  local model answers and says so. On by default; it does nothing without Ollama. (Ollama with qwen3:4b is installed
  on this PC, so this will be live for you.)
- **Replies that appear while they are written:** off by default, Qwen only.
- Smaller fixes: plain messages for a request too large for a plan and for a model not activated; a real-size
  connection check in Settings > Developer; backups and the switch-over carry your own style sheet; the screen
  label sent with a screenshot reads correctly.

## Two things only you can check before approving

1. **Your key file.** 1.0.15 accepts `JARVIS_PROVIDER=openai` or `JARVIS_PROVIDER=qwen` and nothing else. Your
   Test-AiKeys and speed runs showed qwen in use, so the line is most likely right already; if it still says groq or
   gemini, change it before step 4, otherwise JARVIS 1.0.15 says the provider is not supported until you do. I never
   read or edit the key file.
2. **Space on C:.** 10.4 GB free today; 1.0.15 adds about 1.2 GB; the launcher refuses below 4 GB free. After the
   update three releases are installed (1.0.11, 1.0.14, 1.0.15). Removing 1.0.11 later is a separate step on your
   word and frees about 1.2 GB.

## What is proven first

- On this PC: the build compared with 1.0.14 (the same pinned parts; 43 changed, 19 added and 1 removed source
  files, exactly the work since 1.0.14), its full test suite with its own Python and Electron (634 Python, 52
  desktop, 18 Intelligence, 23 interface scripts), the zip install, and the whole Stage 7 pass in a sandbox
  (`docs/release-rehearsal-20261006-1015/README.md`).
- In the test VM: the Stage 7 check passed (install, restart with automatic start, uninstall and reinstall, update
  from 1.0.14 while running, rollback, update again, an update killed mid-copy then rerun; 27 of 27 checks; update
  361 s, rollback 105 s, update again 262 s, stopping JARVIS at most 6 s). The first install in that VM took 675 s,
  above the 600-second bound you set at Gate 20 for Stage 6; that is put to you separately in
  `docs/stage7-1.0.15-evidence/stage7-evaluation.json` and does not bear on this update, whose timings on the real
  PC are quoted below.
- **Your data and a rollback.** 1.0.15 adds two tables to the same database (`control`: the emergency stop and the
  automatic-backup choice; `tool_modes`: your switch per tool) and a `devices` table, plus `owner-style.css` in the
  config folder and, only once a pairing has been started, two small files beside the key file
  (`.env.device-secret`, `.env.device-revoked`). Every table 1.0.14 uses is unchanged. If you ever roll back, 1.0.14
  runs on the same data and leaves the new tables alone: the VM's rollback step did exactly that with both test
  memories present. What 1.0.14 does not know it does not enforce: an emergency stop that holds, your tool switches,
  device keys and automatic backups (said in the release notes).
- **The personality text.** If your `personality.txt` is still the one 1.0.14 shipped, 1.0.15 gives it the new
  wording (changes JARVIS makes to itself ask first). A personality you changed yourself stays as it is.
- **This launcher, rehearsed** (`docs/release-rehearsal-20261006-1015/rehearse-everyday-update-1015.ps1`, records in
  `update-rehearsal/`, 2026-10-06 13:00-13:03 local): 1.0.14 installed into a sandbox folder on D: and started once;
  refused without approval; refused while JARVIS was running; step 1 PASS (package hash equal, 1.0.14 verified,
  unpack 16 s); step 2 PASS (backup made with 1.0.14's own backup code, 156 files, verified, test restore passed,
  copy on D: hash-checked, program still verifies); step 3 PASS (update 27.2 s: verify package 7.6 s, copy 9.3 s,
  verify copy 9.2 s, stop 0.8 s, switch 0.3 s; verified; database file byte-for-byte unchanged); 1.0.15 started on
  the same data; a rerun changed nothing; rollback (only with its approval file) PASS, 1.0.14 verified; a rerun after
  the rollback changed nothing; 13 of 13 checks. Your real JARVIS was running the whole time with 8 processes before
  and after, and was never addressed; no sandbox process was left.
- **Not rehearsable by me:** your real data (the sandbox database was new; the same backup code made and
  test-restored your real data at Gate 18, the switch-over and the 1.0.14 update, every count equal), your real
  install folder, and your real restart.
- **The launcher** is the 1.0.14 launcher copied unchanged except its folder and the plan it names
  (`tools/host/update-1.0.15/`; the 1.0.14 files stay as their approval recorded them). sha256:
  `Invoke-EverydayUpdate.ps1` `1c555b022337865c1734b7e9908c5baf66eb96bc33b74d29d97e6e8c0ea952d2`, `update-step.cmd`
  `9c469bd44002e59066f5b8e7e2b077173826780840b37e7f4151e99be86d3388` (identical to 1.0.14's); the 1.0.15 package zip
  sha256 `1019dce00702da4e15dac5ea8203a1a1034311fbbe30b352097517b16deec027`.

## The steps

You double-click one launcher, `D:\JARVIS-update-1.0.15\tools\update-step.cmd`, once per step, in your own account
(jonny), with JARVIS **quit** (right-click its icon near the clock > Quit JARVIS completely). Each step writes a
record and stops; you tell me "step N done" and I check the record before the next. No administrator rights; a UAC
prompt is a STOP. Nothing is deleted anywhere.

| # | Who | What happens | Undo |
|---|---|---|---|
| 1 | Launcher | Checks: the 1.0.15 package against its hash; your JARVIS is 1.0.14 and every program file verifies; JARVIS is not running; 4 GB free on C:. Unpacks the package to `D:\JARVIS-update-1.0.15\package`. Changes nothing in your JARVIS. | nothing changed |
| 2 | Launcher | A fresh backup of your JARVIS with its own backup code (the same as Settings > Backups: "Create verified backup", then "Test restore"); the backup lands in `%LOCALAPPDATA%\JARVIS\data-backups` and a hash-checked copy in `D:\JARVIS-update-1.0.15\backup`. The program still verifies afterwards. | nothing changed |
| 3 | Launcher | The 1.0.15 installer adds 1.0.15 beside 1.0.14, checks every file, and switches your JARVIS to it in one step. Data, settings, keys, profile and shortcuts are not touched (the record proves the database file is byte-for-byte the same before and after). JARVIS is not started. | step R |
| 4 | You | Start JARVIS from its Desktop icon and check (list below). | |
| 5 | You | Restart the PC once (Start > Power > Restart, jonny) and check JARVIS starts by itself after you sign in (for 1.0.14 it did, about 6.5 minutes after sign-in). | |
| R | Launcher, **only on your word** | If anything is wrong in step 4 or 5: tell me; I record your word and one more double-click switches your JARVIS back to 1.0.14 (still installed). | update again later |

**Your check in step 4** (10 minutes): the new look with eight sections across the top; Settings > About shows
`Version 1.0.15-63362929d7ad (installed)`; your memories and recent conversations are there; ask something and
JARVIS answers (your provider); say something and voice works; Settings > Permissions lists the tools; Settings >
Devices lists this PC; Settings > AI shows Answer speed and the Backup provider ticked; then quit from the icon near
the clock: no "Core stopped" box.

## Records

`D:\JARVIS-update-1.0.15\evidence\` (check.json, backup.json, update.json, rollback.json if used); I copy them to
`docs/update-1.0.15-evidence/` with a manifest. The records hold hashes, counts per database table and timings, never
your messages or keys. I never read your key file or the contents of the backup.

## What you accept by approving

1. **The update runs on your real JARVIS** (owner-only), started by you, one step at a time.
2. **Keys and provider stay as they are.** The key file must say openai or qwen (above); nothing else about keys
   changes.
3. **A rollback to 1.0.14 keeps your data but not the 1.0.15 safeguards:** no emergency stop that holds, no tool
   switches, no device keys, no automatic backups while 1.0.14 runs.
4. **New behaviour that is on from the start:** the backup provider (the other provider answers when yours refuses,
   and the reply says so) and answers from the local model when no provider can be reached (it says so and cannot
   use tools). Both have a tick box in Settings > AI if you want them off.
5. **Known limits that remain:** install under a non-administrator Windows account is untested (your account is an
   administrator; the update itself needs no administrator rights); a program JARVIS opened (for example Notepad)
   should be closed before an update or uninstall; the parts of 1.0.15 that need a provider, a device or a backup
   drive were tested with stand-ins, not with the real ones.
6. **Space:** about 1.2 GB more on C:; 1.0.14 stays as the rollback copy, 1.0.11 stays until you say otherwise.

## After the update

A few days of normal use; then, on your word: the cleanup listed in `docs/CURRENT-STATUS.md` (test VM, data copies
on D:, the old folder and Codex, the 1.0.11 release folder). Then the phone plan, which builds on the Devices part of
1.0.15.

## Approval

Reply in your own words, for example: "I approve the update of my everyday JARVIS to 1.0.15". I then record it, put
the launcher in `D:\JARVIS-update-1.0.15\tools\` with its hashes and `update-authorized.json`, and you start with
step 1.
