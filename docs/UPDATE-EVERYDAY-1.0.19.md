# Updating your everyday JARVIS to 1.0.19 (plan for your approval)

Status: **2026-10-13 20:20 local: the launcher's sandbox rehearsal passed (run 2, 32 of 32, below); its
independent review is running. APPROVED BY THE OWNER at this point ("I approve the update of my everyday JARVIS to
1.0.19", first clock reading 2026-10-13T09:20:02Z, 20:20 local; record
`../governance/UPDATE-1.0.19-APPROVAL-RECORD.json`), the review's findings to be applied before the launcher is
placed; if a finding changes the launcher, the rehearsal is run again and the owner told before step 1. Step 0 (the
key file) is the owner's.**
Updating the everyday JARVIS is your decision (`CLAUDE.md`). 1.0.19 (`1.0.19-629bb5621d34`) passed its Stage 7 check
in the test VM today, 17:34 to 19:41 local (`STAGE_7_COMPLETE`, 29 of 29 checks, every timing inside the bound,
`docs/stage7-1.0.19-evidence/`, commit `90f7f83`). The launcher for this update is **version 3** of the one that
updated you to 1.0.17 on 2026-10-07: the same three steps, the same Setup method, with the differences 1.0.19 needs
(below).

## In plain words

Your everyday JARVIS (1.0.17, installed at `%LOCALAPPDATA%\JARVIS` since 2026-10-07 evening, 1.0.16 still beside it)
gets 1.0.19, the OpenRouter release: one AI service for everything, with one key. Your memories, conversations,
personality, preferences and settings stay exactly where they are: the update adds the new program beside the old one
and switches to it; the database file is checked byte-for-byte unchanged by the update. 1.0.17 stays installed, so
going back is one step. Before anything changes, a fresh backup of your data is made and test-restored.

**One thing is different from every earlier update: your key file must be right for 1.0.19 before step 1.** 1.0.17
accepted `JARVIS_PROVIDER=openai` or `qwen`; 1.0.19 accepts only OpenRouter. See "Three things only you can check".

## What 1.0.19 brings (over your 1.0.17)

From the 1.0.18 and 1.0.19 entries of `release-notes.json`, in short:

- **One AI service, OpenRouter, Qwen models only** (your decision of 2026-10-13). Chat, pictures, web search and the
  optional cloud hearing all go through OpenRouter with one key, `OPENROUTER_API_KEY`. `JARVIS_PROVIDER` may be
  `openrouter` or left out. A model line naming another maker's model is refused with a plain message.
- **A backup model**: Settings > AI > Backup lets OpenRouter try its own backup Qwen model when the first one fails;
  the reply says so.
- **Fish Audio for JARVIS's voice** (`FISH_API_KEY`, optional `FISH_MODEL`, `FISH_VOICE_ID`). Without a Fish key, the
  browser's own voice. A voice choice saved as OpenAI or Qwen now reads as automatic.
- **Removed:** OpenAI, Qwen through Alibaba Cloud, their voices and speech recognition, the second-provider backup,
  Brave search (web search is OpenRouter's, then SerpApi, then best-effort DuckDuckGo). The old `OPENAI_*`,
  `DASHSCOPE_*`, `QWEN_*` and `BRAVE_API_KEY` lines are ignored; keep them for now (see rollback).
- **From 1.0.18:** "what time is it" is answered as one sentence (*It's 2:36 PM on Saturday 10 October 2026*), on
  this PC, the phone and Siri.
- **Unchanged:** permissions, the emergency stop and every other safety rule; no new table or data format (the
  database tables of 1.0.19 are the same as 1.0.17's, compared file to file).
- **Not in 1.0.19:** the Workshop, goals, skills, standing responsibilities (the work on the merge branch; the release
  after this one).

## Three things only you can check before approving

1. **Your key file, `%LOCALAPPDATA%\JARVIS\config\.env`.** 1.0.19 needs a line `OPENROUTER_API_KEY=...` and the
   provider line either `JARVIS_PROVIDER=openrouter` or no provider line at all. Anything else on that line (your
   screenshot earlier today showed 1.0.17 printing back *"qwen via openrouter"*) makes 1.0.19 answer "Unsupported
   provider" just as 1.0.17 does now. **Fix it yourself before step 1** (I never open or edit the file); step 1 then
   checks it for you and, if 1.0.19 would still refuse it, stops with a message naming the provider word and whether
   the OpenRouter line is there, and nothing else. **Keep the old `OPENAI_API_KEY` and `DASHSCOPE_API_KEY` lines for
   now**: 1.0.17 does not know OpenRouter, so a rollback needs them (and the rollback sets the provider line back by
   restoring the whole file as it stood at step 1). Optional lines you may add from the release's `env.template`:
   `OPENROUTER_MODEL`, `OPENROUTER_FAST_MODEL`, `OPENROUTER_VISION_MODEL`, `OPENROUTER_CODING_MODEL`,
   `OPENROUTER_FALLBACK_MODEL`, `OPENROUTER_STT_MODEL`, `OPENROUTER_STT_LANGUAGE`, `FISH_API_KEY`, `FISH_MODEL`,
   `FISH_VOICE_ID`.
2. **Space on C:.** 19.6 GB free at 20:10. 1.0.19 adds about 2.4 GB (1.2 GB for the release, 1.2 GB for the Setup's
   new package folder) and the renamed 1.0.17 package folder (item 3) keeps its 1.2 GB; the launcher refuses below
   4 GB free. After the update three releases are installed (1.0.16, 1.0.17, 1.0.19); removing 1.0.16 and the renamed
   folder later is a separate step on your word, about 1.2 GB each.
3. **The 1.0.17 package folder, `%LOCALAPPDATA%\JARVIS-package`** (1.2 GB, real this time: your 1.0.17 Setup made it,
   and Settings > Apps uninstalls from it). 1.0.19's Setup unpacks into a folder of that name, and nothing is deleted
   under this plan, so the launcher **renames** it to `%LOCALAPPDATA%\JARVIS-package-before-1.0.19-629bb5621d34` at
   step 3, in the second before the Setup starts (step 1 only looks at it and records its uninstaller's hash). For the
   few minutes of step 3 the Uninstall button in Settings > Apps points at the old place; the Setup then writes the
   new package folder and the new uninstaller and the entry says 1.0.19. A rollback does not need that button. You may
   delete the renamed folder later, with 1.0.16.

## What is proven first

- On this PC, before the VM: the build compared with 1.0.18 (4,039 of 10,766 files differ, 19 real program files), the
  release regression, the Setup, the zip install, the Setup rehearsal with your real shortcuts watched, and the whole
  Stage 7 pass in a sandbox with the version 4 scripts, all PASS (`docs/release-rehearsal-20261013-1019/README.md`,
  commit `eccaea2`). OpenRouter itself was tested live by you on 2026-10-13 (6 of 6).
- In the test VM (`docs/stage7-1.0.19-evidence/stage7-evaluation.json`): install from the Setup, the entry, the
  restart with automatic start, the uninstall through Settings > Apps and the reinstall from the Setup, the update from
  1.0.17 while running, rollback, update again, one update through the Setup, an update killed mid-copy then rerun;
  29 of 29, memories checked at every step. Timings: install 539.6 s, reinstall 179.8 s, update 537.7 s, rollback
  119.4 s, update after the interruption 401.8 s, every one inside the 600-second bound (1.0.17 needed one
  exception; 1.0.19 needs none). Not covered there: an AI conversation (no keys in the VM) and a real microphone.
- **Your data and a rollback.** 1.0.19 adds no table or column. If you roll back, 1.0.17 runs on the same data; its
  shortcuts come back at its own `JARVIS.exe`; the Settings > Apps entry stays, saying 1.0.19, until the next update
  (it still uninstalls the program with the data kept); your key file is put back from the copy step 1 made, so the
  provider line and the OpenAI or Qwen keys are as they were, and the file as it stood at the rollback is kept beside
  it as `config\.env.rolled-back-from-1.0.19-629bb5621d34`. What 1.0.17 does not know it does not do: OpenRouter,
  Fish Audio, the backup model, the time sentence.
- **This launcher, version 3, rehearsed in a sandbox on D:** (`docs/release-rehearsal-20261013-1019/
  rehearse-everyday-update-1019.ps1`, records in `D:\JARVIS-release-work\update-rehearsal-1.0.19-2\`, run 2,
  2026-10-13 20:14 to 20:19 local, **32 of 32 checks**). The sandbox mirrors your PC:
  1.0.17 installed by its own Setup with the sandbox switches (the entry "JARVIS (sandbox) 1.0.17" under the sandbox
  id, which both Setups share, the package folder with its uninstaller), started once; then the launcher: refused
  without approval; refused while JARVIS runs; refused on a key file 1.0.19 would refuse (planted as provider qwen,
  no OpenRouter line; the message named the words and no value); step 1 (hashes, the Setup's record, the entry
  1.0.17 before, the key file accepted with its names recorded and a copy made, the package folder seen and not yet
  moved, 1.0.17 verified); step 2 (backup with 1.0.17's own backup code, 201 files, test-restored, copied to D: and
  hash-checked); step 3 (the package folder renamed aside with its uninstaller intact, 1.0.19's Setup silently in
  110.7 s wall: the installer inside it verify package 9.0 s, copy 28.1 s, verify copy 26.6 s, stop 0.7 s, switch
  0.4 s; the entry now 1.0.19 with the new uninstaller, the database file unchanged, the key file untouched, JARVIS
  not started); 1.0.19 started on the same data through its own `JARVIS.exe` (only `JARVIS.exe` and `python.exe`
  running); a rerun changed nothing; rollback (only with
  its approval file): 1.0.17 verified and started again, the key file put back from the copy and the changed file kept
  beside it, the entry still saying 1.0.19; a rerun after the rollback changed nothing; the sandbox uninstalled through
  its own entry at the end. Your real Desktop and Startup shortcuts hashed before, after every step and at the end;
  your real Settings > Apps entry (JARVIS 1.0.17) read at the start and at the end, both the same; your installed
  JARVIS never addressed (0 of its processes before and after: it was not running); no sandbox process left; the fake
  key value appears in no record and no line of output (checked by search). Run 1 (20:10 to 20:16,
  `update-rehearsal-1.0.19\`) stopped at every launcher step on a defect of the harness (it wrote the approval file in
  the old, version 2 format, which the launcher rightly refused); nothing of the update ran; the sandbox was
  uninstalled cleanly; the harness was fixed, nothing in the launcher.
- **Not rehearsable by me:** your real data (the sandbox database was new; the same backup code made and test-restored
  your real data at the 1.0.14 to 1.0.17 updates, every count equal), your real install folder, your real shortcuts
  being rewritten (the sandbox Setup withholds them; the VM check wrote and checked them), your real key file (the
  sandbox used fake values) and your real restart.
- **The launcher** (`tools/host/update-1.0.19/`): the 1.0.17 launcher with (a) step 1 expecting the Settings > Apps
  entry with the previous version and step 3 checking it says the new one with the new uninstaller; (b) the package
  folder examined at step 1 and renamed aside at step 3 right before the Setup; (c) the key file read for the names
  of its lines only, never a value, the stop when 1.0.19 would refuse it, the copy for the rollback; (d) the rollback
  putting the key file back and checking both shortcuts point at 1.0.17's `JARVIS.exe`; (e) "Claude" replaced by
  "Hermes" in its messages. Independently reviewed (section below; findings applied before approval) and rehearsed
  after the review. Its sha256 is recorded in the approval record at approval. The Setup:
  `JARVIS-Setup-1.0.19-629bb5621d34.exe`, 406,914,757 bytes, sha256
  `8e5bb3dceef85fc486f3d03b3864dfa3479c8833ffe471646cdd33dbcc36092f`; the zip `JARVIS-1.0.19-629bb5621d34.zip`,
  533,398,008 bytes, sha256 `838371836d31758082d191738ebc3b41d0e34fe4b6598af6153d970ab8b21541` (both in
  `D:\JARVIS-release-work\pkg-1.0.19` and `D:\JARVIS-release-work\release`, the same hashes the Stage 7 approval
  record names).

## The steps

You double-click one launcher, `D:\JARVIS-update-1.0.19\tools\update-step.cmd`, once per step, in your own account
(jonny), with JARVIS **quit** (right-click its icon near the clock > Quit JARVIS completely). Each step writes a record
and stops; you tell me "step N done" and I check the record before the next. No administrator rights; a UAC prompt is
a STOP. Nothing is deleted anywhere.

| # | Who | What happens | Undo |
|---|---|---|---|
| 0 | You | Fix the key file (item 1 above): `JARVIS_PROVIDER=openrouter` or no such line, and `OPENROUTER_API_KEY=...` present; the old key lines kept. Save it. | your own edit |
| 1 | Launcher | Checks: the 1.0.19 zip and Setup against their hashes and the Setup's record; your JARVIS is 1.0.17 and every program file verifies; JARVIS is not running; Settings > Apps lists JARVIS 1.0.17; 4 GB free on C:; the key file fit for 1.0.19 (names only) and a copy of it made beside it; the 1.0.17 package folder seen (its uninstaller's hash recorded). Unpacks the zip to `D:\JARVIS-update-1.0.19\package` (for the verify and rollback commands). About 5 minutes. | nothing changed in `%LOCALAPPDATA%\JARVIS` (one copy of the key file added beside it) |
| 2 | Launcher | A fresh backup of your JARVIS with its own backup code (as Settings > Backups: "Create verified backup", then "Test restore"); the backup lands in `%LOCALAPPDATA%\JARVIS\data-backups` and a hash-checked copy in `D:\JARVIS-update-1.0.19\backup`. The program still verifies afterwards. About 2 minutes. | nothing changed |
| 3 | Launcher | Renames the 1.0.17 package folder aside (item 3), then runs `JARVIS-Setup-1.0.19-629bb5621d34.exe` silently with its defaults (a line every half minute; 3 to 10 minutes: 187 s for 1.0.17 on this PC, 538 s in the VM). The installer inside it adds 1.0.19 beside 1.0.17, checks every file, switches your JARVIS to it, writes the Desktop and Startup shortcuts at the new `JARVIS.exe`; the Setup rewrites the Settings > Apps entry to JARVIS 1.0.19 with its new uninstaller. The launcher checks all of it, that the database file is byte-for-byte unchanged and the key file untouched; JARVIS is not started. | step R |
| 4 | You | Start JARVIS from its Desktop icon and check (list below). | |
| 5 | You | Restart the PC once (Start > Power > Restart, jonny) and check JARVIS starts by itself after you sign in (3.6 minutes after sign-in for 1.0.17). | |
| R | Launcher, **only on your word** | If anything is wrong in step 4 or 5: tell me; I record your word and one more double-click switches your JARVIS back to 1.0.17 (still installed): its shortcuts come back at its `JARVIS.exe`, your key file is put back as it stood at step 1 (the current file kept beside it), the Settings > Apps entry stays saying 1.0.19. | update again later |

**Your check in step 4** (10 minutes): the window, the taskbar and the tray say JARVIS; Settings > About shows
`Version 1.0.19-629bb5621d34 (installed)`; the "AI configuration" line names a Qwen model through OpenRouter, not
"Unsupported provider"; your memories and recent conversations are there; ask something and JARVIS answers; ask "what
time is it" and he answers in one sentence; say something and voice works (Fish Audio with a Fish key, otherwise the
browser's voice); Settings > AI shows the Backup switch; Settings > Apps > Installed apps lists JARVIS 1.0.19, Teague
Industries (do not press Uninstall); then quit from the icon near the clock: no "Core stopped" box. Not part of this
check: the phone, Gmail, Calendar, the Workshop.

## Records

`D:\JARVIS-update-1.0.19\evidence\` (check.json, backup.json, update.json with the Setup's log, rollback.json if used);
I copy them to `docs/update-1.0.19-evidence/` with a manifest. The records hold hashes, counts per database table,
timings and the **names** of the key file's lines (`OPENROUTER_API_KEY`, `JARVIS_PROVIDER` and the like; the provider
word), never a value, never your messages. I never read your key file or the contents of the backup.

## What you accept by approving

1. **The update runs on your real JARVIS** (owner-only), started by you, one step at a time, by the Setup.
2. **Your real shortcuts are rewritten by the installer** to point at 1.0.19's `JARVIS.exe` (checked afterwards; a
   rollback writes them back at 1.0.17's).
3. **The 1.0.17 package folder is renamed at step 3**, not deleted; 1.0.19's package folder of 1.2 GB takes its place
   and stays (Settings > Apps uninstalls from it). During step 3 the Uninstall button points at the old place.
4. **The launcher reads your key file for the names of its lines** (never a value; names only in the record) and
   **keeps a byte-for-byte copy beside it**, `config\.env.before-1.0.19-629bb5621d34`, for the rollback. The copy
   holds your keys like the original and sits in the same folder with the same protection; delete it when 1.0.19 has
   earned its keep (I will ask).
5. **1.0.19 answers only through OpenRouter.** If OpenRouter is down or the key is wrong, JARVIS says so; there is no
   second service. The backup model is a second Qwen model on the same service.
6. **A rollback to 1.0.17 keeps your data** and puts the key file back; 1.0.17 knows none of the 1.0.19 items; the
   Settings > Apps entry stays saying 1.0.19.
7. **Known limits that remain:** install under a non-administrator Windows account is untested (your account is an
   administrator; the update itself needs no administrator rights; a UAC prompt is a STOP); a program JARVIS opened
   should be closed before an update; the interactive Setup wizard (Next, Install) was not used: this update runs it
   silently with the same defaults the VM check used; the launch count in the VM was 4 processes at the login launch
   where this PC shows 8 (noted, no check depends on it).
8. **Space:** about 2.4 GB more on C:; 1.0.16 and the renamed folder stay until you say otherwise.

## After the update

The next release from the merge branch (the Workshop, goals, skills, standing responsibilities, the autonomy items)
through the same chain, with the changed-files-only updater you chose (point 1 of the efficiency list); the C: cleanup
(1.0.16, the renamed folder, the key-file copy) on your word.

## Independent review

Pending (one reviewer agent, started 20:20): the launcher's changes from version 2, the key-file handling (no value
may leak into output or records), the step 3 rename and its failure paths, the rollback order, PowerShell 5.1
pitfalls, and the harness's separation from the real installation. Findings and what was applied are listed here
before approval.

## Approval

When the status line says READY FOR THE OWNER'S APPROVAL and items 1 to 3 are done on your side, say: **"I approve the
update of my everyday JARVIS to 1.0.19"**. I then record it (the plan's hash, the two builds' hashes, the launcher's
hash), place the launcher and `update-authorized.json` in `D:\JARVIS-update-1.0.19\tools\`, and give you step 1.
