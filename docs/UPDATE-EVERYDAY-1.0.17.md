# Updating your everyday JARVIS to 1.0.17 (plan for your approval)

Status: **APPROVED BY THE OWNER** ("I approve the update of my everyday JARVIS to 1.0.17", first clock reading
2026-10-07T07:58:40Z, recorded 2026-10-07T08:00:21Z; record `../governance/UPDATE-1.0.17-APPROVAL-RECORD.json`, plan sha256
`f74fff6f…` as committed in 08cbb7b; repo copy `docs/update-1.0.17-evidence/`). The launcher is placed in
`D:\JARVIS-update-1.0.17\tools\` with `update-authorized.json`; the owner's steps follow. (Before the approval: READY FOR
THE OWNER'S APPROVAL, 2026-10-07 19:00 local, the launcher's review findings applied and the reviewed launcher passed
its sandbox rehearsal 26 of 26, run 3 below.) Updating the everyday JARVIS is your decision
(`CLAUDE.md`). 1.0.17 build 2 (`1.0.17-0d38218c4e1d`) passed its Stage 7 check in the test VM today
(`STAGE_7_COMPLETE`, 29 of 29 checks, `docs/stage7-1.0.17-evidence/`), the first check made with the Setup. The
launcher for this update is a **new version** (the update is made by the Setup, as the approved own-app plan says);
it was rehearsed in a sandbox and independently reviewed (both below).

## In plain words

Your everyday JARVIS (1.0.16, installed at `%LOCALAPPDATA%\JARVIS` since 2026-10-06 evening) gets 1.0.17, "JARVIS as
his own app": the program is now `JARVIS.exe` with the Teague Industries badge, the Desktop and Startup shortcuts
point straight at it, JARVIS is listed in Settings > Apps > Installed apps, and from now on every update is one file,
`JARVIS-Setup-<version>.exe`. Your memories, conversations, personality, preferences and keys stay exactly where they
are: an update adds the new program beside the old one and switches to it. 1.0.16 stays installed beside it, so
going back is one step. Before anything changes, a fresh backup of your data is made and tested.

## What 1.0.17 brings

The 1.0.17 entry of `release-notes.json`, in short: JARVIS.exe and the Setup (the Installed-apps entry, the
shortcuts at JARVIS.exe, the PowerShell launcher no longer written); the three phone fixes (replies streamed to the
phone when your streaming setting is on, "remember that" saving the line before it, the action guard appending
instead of replacing); the music stop fix and the start-up song (Settings > Music); and everything JARVIS said he was
not allowed to do, each **off until you switch it on**: the two device ticks (tools, approvals from the phone),
screen analysis and location from the phone, Gmail and Calendar through three lines in the key file (Settings >
Connections), the release stamp on every saved thing, Settings > Routine with its nudges and notices, the home-network
list (Settings > Devices > On this network), 51 tools each with its switch. Not in 1.0.17: the Workshop (that is
1.0.18, built and reviewed in the repo, not yet through its checks).

## Three things only you can check before approving

1. **Your key file** needs no change: `JARVIS_PROVIDER` stays as it is. The new Gmail and Calendar lines are optional
   and come later, from `docs/GOOGLE-STEPS.md`. I never read or edit the key file.
2. **Space on C:.** 12 GB free at 18:30; 1.0.17 adds about 2.4 GB (1.2 GB for the release, 1.2 GB for the Setup's
   package folder, which stays because Settings > Apps uninstalls from it); the launcher refuses below 4 GB free.
   After the update five releases are installed (1.0.11, 1.0.14, 1.0.15, 1.0.16, 1.0.17); removing the old ones later
   is a separate step on your word, about 1.2 GB each.
3. **A leftover folder from the switch-over,** `%LOCALAPPDATA%\JARVIS-package` (1.2 GB, 2026-10-02: the copy of the
   first installed package). The Setup unpacks into a folder of that name, and the installer refuses a release
   folder holding files its manifest does not name, so step 1 **renames** the leftover to
   `%LOCALAPPDATA%\JARVIS-package-before-1.0.17-0d38218c4e1d` (nothing deleted, no space used) and records it. You
   may delete that renamed folder later, with the old releases.

## What is proven first

- On this PC: the build compared with 1.0.16 and with build 1 (the same program), the release regression run alone
  (776 Python, 60 desktop, 18 Intelligence, 26 scripts), the Setup, the zip install, the Setup rehearsal with your
  real shortcuts watched, and the whole Stage 7 pass in a sandbox with the version 4 scripts, all PASS
  (`docs/release-rehearsal-20261007-1017/README.md`).
- In the test VM (`docs/stage7-1.0.17-evidence/stage7-evaluation.json`): install from the Setup, the entry, the
  restart with automatic start, the uninstall through Settings > Apps and the reinstall from the Setup, the update
  from 1.0.16 while running, rollback, update again, one update through the Setup, an update killed mid-copy then
  rerun; 29 of 29. The first install in the VM took 601.5 s on the installer's own laps, 1.5 s over the 600-second
  bound, which the records show to be the VM's disk (the same files verified in 90 to 127 s later in the pass and in
  7 to 18 s on this PC): a VM limitation under your rule of 2026-10-06; the update itself took 369 s there and
  under 40 s on this PC.
- **Your data and a rollback.** 1.0.17 adds tables and columns for the new items (the device ticks, the routine, the
  notices, the mail and calendar settings, the release stamp) to the same database; every table 1.0.16 uses is
  unchanged. If you ever roll back, 1.0.16 runs on the same data and leaves the new tables and columns alone (the
  VM's rollback step did exactly that), its shortcuts and launcher come back as they were, and the Settings > Apps
  entry stays, still saying 1.0.17, until the next update (it still uninstalls the program with the data kept).
  What 1.0.16 does not know it does not enforce: the ticks, the routine, the notices, mail, calendar, the network
  list, the streamed replies.
- **The personality text** shipped with 1.0.17 is the same as 1.0.16's; nothing of yours is touched.
- **This launcher, version 2, rehearsed** (`docs/release-rehearsal-20261007-1017/rehearse-everyday-update-1017.ps1`,
  records in `update-rehearsal-3/`, 2026-10-07 18:49-18:54 local, the third run, on the reviewed launcher): 1.0.16 installed into a sandbox folder on D: and
  started once; a stale package folder planted; refused without approval; refused while JARVIS was running; step 1
  PASS (both hashes equal, the Setup's record checked, no entry before, the stale folder renamed aside, the package
  unpacked, 1.0.16 verified); step 2 PASS (backup made with 1.0.16's own backup code, 178 files, test restore passed,
  copy on D: hash-checked, program still verifies); step 3 PASS (the Setup silently in 98.7 s wall: the installer
  inside it verify package 12.7 s, copy 11.6 s, verify copy 27.6 s, stop 1.8 s, switch 0.1 s; verified; the entry
  "JARVIS (sandbox) 1.0.17, Teague Industries" with its uninstaller; no `JARVIS.ps1`; the database file byte-for-byte
  unchanged; JARVIS not started); 1.0.17 started on the same data through its own `JARVIS.exe` (only `JARVIS.exe`
  and `python.exe` running); a rerun changed nothing; rollback (only with its approval file) PASS, 1.0.16 verified
  and started again, the entry still saying 1.0.17 as this plan says; a rerun after the rollback changed nothing;
  the sandbox uninstalled through its own entry at the end; **26 of 26 checks** (the real Settings > Apps entry
  asserted absent at the start and at the end as well). Your real Desktop and Startup
  shortcuts carried the same hashes before, after every step and at the end; your real JARVIS was not running at
  the time (0 processes before and after) and was never addressed; the real Settings > Apps entry was never
  created; no sandbox process was left. The earlier runs: run 1 (18:22-18:26, `update-rehearsal/`), 24 of 24 on the
  launcher before its review; run 2 (18:44-18:48, `update-rehearsal-2/`), the first on the reviewed launcher: every
  launcher step passed and the harness itself stopped on two defects of its own (it looked for the Setup's log under
  its old name after review finding 9 gave the log a time stamp, and it read the sandbox Core's connection file in the
  instant the Core removed it at shutdown); both fixed in the harness, nothing in the launcher, and run 3 is the record.
- **Not rehearsable by me:** your real data (the sandbox database was new; the same backup code made and test-restored
  your real data at the 1.0.14, 1.0.15 and 1.0.16 updates, every count equal), your real install folder, your real
  shortcuts being rewritten (the sandbox Setup withholds them; the VM check wrote and checked them), and your real
  restart.
- **The launcher** (`tools/host/update-1.0.17/`): the 1.0.16 launcher with step 3 changed to the Setup and the checks
  above, step 1 with the Setup's hash and the rename, and the rollback record noting the entry; independently
  reviewed (section "Independent review" below) and rehearsed again after the review (run 3 above); sha256
  `66c8cce6e4b16e302a0201aff690158d43684eba8315d1b2a6b7e542bd84365b`, recorded in the approval record at approval
  (`update-step.cmd` is identical to 1.0.14's, 1.0.15's and 1.0.16's). The Setup: `JARVIS-Setup-1.0.17-0d38218c4e1d.exe`,
  406,936,706 bytes, sha256 `b7bb04d36180c99251e61a0458e77af5eb4a50aafea5812ff14525bdd63eeb7e`; the zip sha256
  `210b46235638e92bbef1634b853c53ae6838ed58e997543cab87ffa844bb01d9` (both in `D:\JARVIS-release-work\pkg-1.0.17`).

## The steps

You double-click one launcher, `D:\JARVIS-update-1.0.17\tools\update-step.cmd`, once per step, in your own account
(jonny), with JARVIS **quit** (right-click its icon near the clock > Quit JARVIS completely). Each step writes a
record and stops; you tell me "step N done" and I check the record before the next. No administrator rights; a UAC
prompt is a STOP. Nothing is deleted anywhere.

| # | Who | What happens | Undo |
|---|---|---|---|
| 1 | Launcher | Checks: the 1.0.17 zip and Setup against their hashes and the Setup's record; your JARVIS is 1.0.16 and every program file verifies; JARVIS is not running; no JARVIS entry in Settings > Apps yet; 4 GB free on C:. Renames the leftover `JARVIS-package` folder aside. Unpacks the zip to `D:\JARVIS-update-1.0.17\package` (for the checks and a rollback). Changes nothing in your JARVIS. | the rename: rename it back |
| 2 | Launcher | A fresh backup of your JARVIS with its own backup code (as Settings > Backups: "Create verified backup", then "Test restore"); the backup lands in `%LOCALAPPDATA%\JARVIS\data-backups` and a hash-checked copy in `D:\JARVIS-update-1.0.17\backup`. The program still verifies afterwards. | nothing changed |
| 3 | Launcher | Runs `JARVIS-Setup-1.0.17-0d38218c4e1d.exe` silently with its defaults (a line every half minute while it unpacks and installs; a few minutes). The installer inside it adds 1.0.17 beside 1.0.16, checks every file, switches your JARVIS to it, writes the Desktop and Startup shortcuts at the new `JARVIS.exe`, removes the old `JARVIS.ps1`, and registers JARVIS 1.0.17 in Settings > Apps. The launcher then checks all of that and that the database file is byte-for-byte the same. JARVIS is not started. | step R |
| 4 | You | Start JARVIS from its Desktop icon (the badge) and check (list below). | |
| 5 | You | Restart the PC once (Start > Power > Restart, jonny) and check JARVIS starts by itself after you sign in (for 1.0.16 it did, 5.7 minutes after sign-in). | |
| R | Launcher, **only on your word** | If anything is wrong in step 4 or 5: tell me; I record your word and one more double-click switches your JARVIS back to 1.0.16 (still installed); its shortcuts and launcher come back; the Settings > Apps entry stays. | update again later |

**Your check in step 4** (10 minutes): the Desktop icon is the badge and the window, the taskbar and the tray say
JARVIS; Settings > About shows `Version 1.0.17-0d38218c4e1d (installed)`; your memories and recent conversations are
there; ask something and JARVIS answers; say something and voice works; "stop the music" after "play ..." stops it;
Settings > Apps > Installed apps lists JARVIS 1.0.17, Teague Industries (do not press Uninstall); Settings > Devices
shows the two new ticks off for your phone; Settings > Routine and Settings > Connections open; then quit from the
icon near the clock: no "Core stopped" box. Not part of this check: Gmail, Calendar, the Workshop (1.0.18).

## Records

`D:\JARVIS-update-1.0.17\evidence\` (check.json, backup.json, update.json with the Setup's log, rollback.json if used);
I copy them to `docs/update-1.0.17-evidence/` with a manifest. The records hold hashes, counts per database table and
timings, never your messages or keys. I never read your key file or the contents of the backup.

## What you accept by approving

1. **The update runs on your real JARVIS** (owner-only), started by you, one step at a time, by the Setup.
2. **Your real shortcuts are rewritten by the installer** to point at `JARVIS.exe` (the 2026-10-07 incident was a
   test's rollback writing them by mistake; here it is the update's purpose, checked afterwards, and a rollback
   writes them back).
3. **The leftover `JARVIS-package` folder is renamed**, not deleted; the Setup's own package folder of 1.2 GB stays.
4. **Keys and provider stay as they are.** Every new access item stays off until you switch it on.
5. **A rollback to 1.0.16 keeps your data** but knows none of the new items; the Settings > Apps entry stays.
6. **Known limits that remain:** install under a non-administrator Windows account is untested (your account is an
   administrator; the update itself needs no administrator rights; a UAC prompt is a STOP); a program JARVIS opened
   should be closed before an update; the interactive Setup wizard (Next, Install) was not used: this update runs
   it silently with the same defaults the VM check used; the launch count in the VM was 4 processes where this PC
   shows 8 (noted, no check depends on it).
7. **Space:** about 2.4 GB more on C:; the old releases and the renamed folder stay until you say otherwise.

## After the update

1.0.18 (the Workshop) through the same chain; then whichever of the six capability proposals you choose
(`docs/CAPABILITY-SOURCES-20261007.md`); the C: cleanup on your word.

## Independent review (one reviewer agent, 2026-10-07 18:30 to 18:45: 1 high, 3 medium, 8 low; all applied, rehearsed again 26 of 26)

1. **High:** nothing tied `-InstallHome` and `-Staging` to the Setup's `/HOME` and `/DIR` switches, so a rehearsal
   called with inconsistent parameters could have reached the real installation through the defaults. Fixed: a
   rehearsal must name the same sandbox folders in every parameter and may not use the real folders; a real run takes
   no switch and the default folders only; otherwise the launcher stops before anything.
2. **Medium:** after a failed Setup the launcher asserted "the previous release is still installed" instead of
   reading the state. Fixed: every failure message in step 3 now reads and says what the installation is on, whether
   `JARVIS.ps1` is present and where the two shortcuts point; "still current" only when read.
3. **Medium:** the database hash was recorded, not checked. Fixed: a changed database file stops step 3 with the
   state said, before anything is recorded as passed.
4. **Medium:** the real-mode checks (the entry refusal, the shortcuts "written", the two targets, no `JARVIS.ps1`)
   are skipped in a sandbox and first run on the owner's PC. Said in this plan ("not rehearsable"); their failure
   messages now say that the update itself is in place and verified; the shortcut-target reading is the method the
   VM check proved. 5. **Low:** the stated reason for renaming the leftover folder was wrong (the Setup deletes a
   leftover's release folder itself; the rename is for the "nothing is deleted" rule and a clean answer file);
   corrected here and in the script. 6. The rename, the shortcut read and the Setup start are now caught and said as
   STOPPED lines. 7. Switch values with spaces are quoted and a trailing backslash trimmed (rehearsals only). 8. A
   package folder left by an earlier attempt of step 3 is told apart from a leftover. 9. The Setup's log carries a
   time stamp, never overwritten. 10. The PASSED line in a sandbox no longer claims the shortcuts; the final line
   after a rollback says the rollback stands and that the PowerShell shortcuts and launcher script came back. 11.
   Free space is checked again at step 3. 12. (harness) done before the re-rehearsal: the real entry asserted
   absent at the start and at the end; the cleanup runs even when a step throws.

## Approval

Reply in your own words, for example: "I approve the update of my everyday JARVIS to 1.0.17". I then record it, put
the launcher in `D:\JARVIS-update-1.0.17\tools\` with its hashes and `update-authorized.json` (version 2: the zip and
the Setup with their hashes), and you start with step 1.
