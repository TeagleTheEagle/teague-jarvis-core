# Gate 18: restoring your real backup in the test VM (the exact steps)

Status: **prepared 2026-10-04 by Claude Code for OWNER STOP #2. Nothing here has been run on your backup.**

**Changed 2026-10-04 after incident 01 (owner decision "A"):** the backup drive E: turned out to hold a folder
copy of the old project, not a JARVIS backup, and the first copy script picked a wrong file. Step 2 now uses a
fresh backup made by your everyday JARVIS itself and the corrected copy script `Copy-BackupForGate18-v2.ps1`.
E: is no longer used. Records: `evidence\gate18\incident-01-backup-copy.json`, `incident-01-addendum-1.json`.
Gate 18 starts only when you issue `RESUME_STAGE6_RECOVERY`. This page is the "exact restore steps, already
rehearsed" that the approved Gates 17 to 20 plan promised you before that decision.

## What Gate 18 proves

That the backup of your everyday JARVIS restores into the FINAL build: the data arrives complete and intact,
JARVIS starts on it, and nothing else is disturbed. It is the same import the cutover will later do on this PC,
tried first in the disposable VM.

## What happens to your backup

- You make it in your everyday JARVIS and copy it yourself, with one command. The backup is only read; the
  command hashes the file before and after to show it did not change.
- The copy goes onto a read-only disc and into the VM. From then on **the VM holds your personal data**. It
  stays under `D:\JARVIS-S6-FRESHVM\`; keeping or destroying the VM is your decision at Gate 20.
- The records I read contain only counts, hashes and pass/fail, never the content of your memories or
  conversations. Backups never include your AI keys, and the script stops if it finds a key file anyway.

## Your steps

| # | Where | What you do | What happens |
|---|---|---|---|
| 1 | this chat | send `RESUME_STAGE6_RECOVERY` | I record it and switch the Gate 18 launcher on |
| 2 | PC, jonny | paste the backup command I give you into PowerShell (`New-OldJarvisBackup.ps1`; proposed after incident 02, needs your approval) | your everyday JARVIS's own backup code makes a fresh backup and tests its restore (the same code as the Settings buttons, run with the new build's Python because its own Python is gone); then the backup is checked (test passed, database present, no key file), copied to `D:\JARVIS-S6-FRESHVM\media`, and proven unchanged |
| 3 | PC, jonny | double-click `gate18-step` in `D:\JARVIS-S6-FRESHVM\tools` | builds the recovery disc |
| 4 | PC, jarvis-s6-val | double-click `gate18-step` | checks and attaches the disc, starts the VM |
| 5 | inside the VM | sign in, open the `JARVIS_RECOVERY` disc, double-click `gate18` | the restore and its checks (a few minutes plus one install, about 5 minutes) |
| 6 | inside the VM | Start > Power > Shut down | |
| 7 | PC, jarvis-s6-val | double-click `gate18-step` | takes the snapshot `GATE18-PASS` |
| 8 | this chat | say "gate 18 done"; when I report, type `run P4` | I check the records; P4 confirms your old VM is untouched |

## What the script checks inside the VM

1. It runs without administrator rights.
2. The backup on the disc is byte-for-byte the file you copied (hash), has a manifest and a database, and holds
   no key file.
3. The Gate 17 install is present, stopped and intact; its data is fingerprinted.
4. A second, disposable install of FINAL is made beside it (no shortcuts).
5. Dry run: the shipped restore tool verifies every file hash in the backup and the database, and lists what
   would be imported. Nothing changes.
6. Import, including your personality and preferences. The tool compares the database counts with the backup
   and undoes everything if anything differs.
7. JARVIS starts on your restored data, reports the FINAL version, and a second start joins the same JARVIS.
   The first install stays stopped.
8. Clean shutdown.
9. Both installs still verify, and the first install's data is unchanged.
10. The backup file is unchanged.

All met: `BACKUP_RESTORE_RECOVERY_PASS`, then P4.

## Rehearsed, and not rehearsed

- **Rehearsed on this PC (2026-10-04):** the whole in-VM script, all ten checks, against a made-up backup created
  by the FINAL build, plus the launcher's decisions (`docs/release-rehearsal-20261004/`).
- **Not rehearsed, and what Gate 18 is for:** a backup made by your *old* everyday JARVIS going into FINAL. If the
  formats disagree, step 5 above stops before anything is imported.
- **Not rehearsed:** the copy from the backup drive (I never touch that drive), the disc build with your real
  file, and the VirtualBox steps.

## Things that would stop it early (and are fine to hit)

- The v2 copy command expects the backups in `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis-backups`
  (where the everyday JARVIS saves them by default). If the "Folder:" line in Settings names another folder,
  tell me before running it. If anything is missing it says STOPPED and copies nothing.
- The disc builder is only proven for discs up to about 600 MB. If your backup is larger it stops and I adjust
  it first.
- Any failed check stops the gate. It is not repeated without your decision; the clean way to repeat is to go
  back to the snapshot `GATE17-19-PASS`.
- A UAC or administrator prompt anywhere: click No and tell me.

## Not authorised by Gate 18

Switching your everyday JARVIS, Stage 7, any change to your everyday JARVIS or the backup drive, AI keys in the
VM, VirtualBox under your own account.
