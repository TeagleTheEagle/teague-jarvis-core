# Automatic backups (release 1.0.15, scope item 6)

Built 2026-10-06 in the repo only. Master document section 11: backups that happen by themselves, kept somewhere
other than the disk JARVIS lives on.

**Before:** a backup was made only when the owner pressed "Create verified backup", and it was written beside the
data, on the same disk. Drive E: (the owner's backup drive) holds no JARVIS data backup.

**Off until the owner chooses a folder.** Nothing is uploaded; JARVIS writes only into the folder the owner picks.

## 1. What the owner does

Settings > Backups > **Automatic backups**: type the folder (for example a folder on the backup drive), choose every
day or every week and a time of day, press TURN ON. From then on:

- The first automatic backup is made as soon as JARVIS is idle; after that one per day (or week) at the chosen
  time. A PC that was off at that time catches up when JARVIS next runs, and does not repeat it a few hours later.
- Backups go into a subfolder `JARVIS automatic backups` of the chosen folder.
- **Each one is made and checked exactly like a backup made by hand** (`recovery.Recovery.create`: the same files,
  the same verification of the archive and of the database inside it). API keys are never in a backup.
- **Thinning:** of the automatic backups JARVIS keeps the newest seven whatever their age, every one of the last 7
  days, then the newest of each week for 8 weeks, then the newest of each month up to a year; the others are
  removed. **Only backups this feature made are ever removed. A backup made by hand is never touched**, also in the
  same folder.
- TURN OFF stops the schedule and keeps the folder choice and every backup. BACK UP NOW makes one at once; while
  automatic backups are switched off it removes nothing old.
- **Another folder starts afresh:** the first backup there is made at the next idle moment. The backups in the old
  folder stay where they are; JARVIS no longer counts or thins them.

The line under the buttons says: on or off, where the backups go and whether that folder is reachable right now,
when the last one succeeded, when the next is planned (or that it waits for the emergency stop to be lifted), how
many are on record, the reason if the last try failed, and a plain warning when no automatic backup has succeeded
yet or for more than two periods.

## 2. Rules (`auto_backup.py`, connected in `server.py`)

- A backup is **started** only while JARVIS is idle (no question being answered) and **never while the emergency
  stop holds**. A missed one is made at the next chance. A backup that is already running when the stop is pressed
  is finished (a half-written backup helps nobody); nothing old is removed while the stop holds.
- **A question that arrives while a backup is being made waits for it.** While a backup copies the database nothing
  can be written to it: normally a few seconds, longer with much data or a slow drive (measured in the review: about
  2 s for 50 MB and 10 s for 300 MB of data that does not compress). The question waits up to a minute and is then
  turned away with "A backup of JARVIS is being made and has not finished. Ask again in a moment."; Stop ends the
  wait. Other things that save (a setting, a note typed in a panel) wait up to 10 seconds, as they do during a
  backup made by hand.
- What the owner changes while a backup is being made (TURN OFF, another schedule, another folder) stays as the
  owner set it.
- A failure (the drive is not connected or is full, the folder is gone, a file changed during the backup, another
  backup is running) is recorded with its reason and tried again an hour later, not every minute. **A full drive is
  said in plain words, and JARVIS does not remove backups it would otherwise keep to make room.**
- The folder must exist when the owner turns it on, must be given as a full path, must be writable, and may not lie
  inside JARVIS's own data or program folder.
- **A wrong PC clock does not cost backups or stop the schedule.** The newest seven are kept whatever the clock
  says, and a time recorded while the clock was ahead counts as "never", so the next backup is simply made.
- What a backup that never finished left behind in the automatic folder (the Core was closed meanwhile: a working
  folder `.building-…` and a half-written `….zip.publishing-…`, each a full backup in size) is removed after a
  day, before the next backup. Nothing else in that folder is ever removed.
- The owner's choice and the record of what was made are kept in the Core's database with the emergency stop and the
  switches (`control` table), out of reach of the settings page, the JSON export and a restored JSON backup. **A
  full backup restored over JARVIS brings the schedule and the folder back as they were when it was made.**
- The Core looks about once a minute whether one is due (`server.start_auto_backups`, started only by the real
  Core, two minutes after it starts). Activity rows: "automatic backups / on: day", "automatic backup / verified",
  "failed", or "its record could not be saved" (then nothing is tried for an hour).
- Owner's routes (the signed-in interface on the PC only): `GET /api/auto-backup` (the status),
  `POST /api/auto-backup` with `action` `configure` (`folder`, `every`, `at`), `off` or `run`.

## 3. What it does not do

- It does not choose a folder by itself and never writes to a drive the owner did not name.
- It does not encrypt: like every JARVIS backup, an automatic backup is an unencrypted archive that holds personal
  data. A backup drive that leaves the house carries that data with it.
- It does not copy backups to the internet, and it does not restore anything by itself.
- Restoring stays the owner's act. The backups in the automatic folder are listed in Settings > Backups with the
  others while that folder is reachable (those JARVIS made by the schedule marked "automatic", one made by hand in
  that folder marked as such), and can be test-restored and recovered to a separate folder like any backup.

## 4. Checked

`test_auto_backup.py` (26 tests: the schedule, catching up, a failure tried again an hour later, what is kept, a
missing drive, a backup made by hand never touched, and the review's cases of section 5), `test_auto_backup_core.py`
(13 tests in the Core: off until a folder is chosen; the first backup made, checked and recorded, and the choice
surviving a restart; waiting while JARVIS answers and while the emergency stop holds; turning off keeps everything;
what the owner may send; out of reach of settings, export and a restored JSON backup; the quiet clock, also when a
look fails; the owner's routes; an automatic backup listed and test-restored like any other; the review's cases).

In the sandbox window before the review (synthetic data, a folder on D: made for this, never drive E:): the block
shows under Settings > Backups; a folder that is not a full path is refused with the reason left on screen; TURN
ON; the first backup was made within the two minutes the clock waits after a start; the line then gave the time,
the next planned time and the count; List backups showed it marked "automatic"; "Test restore in temporary folder"
passed on it.

Not checked: a real backup drive being unplugged and plugged in again, or really full (a missing folder and the
"full" error are tested); a network folder; a week of real days (the schedule is tested with given times); thinning
on real archives older than a week (tested with records and small files).

## 5. Independent review (2026-10-06, one reviewer): no high finding, 4 medium, 7 low, all applied

The reviewer ran its own experiments in temporary folders. What it found and what was done:

| | Found | Done |
| --- | --- | --- |
| A1 medium | TURN OFF, or a new folder, during a running backup was undone when the backup finished (the backup wrote its old copy of the record back). | The record is read, changed and saved as one step everywhere; a finishing backup writes only its own result onto the record as it then is. |
| A2 medium | One backup made with the PC clock two years ahead removed all but one of ten older backups, and the schedule then stood still without a warning until that date. | The newest seven are always kept; a recorded time ahead of the clock counts as never. |
| A3 medium | A question arriving while a backup held the database for more than 10 seconds failed "internally", and a typed note was lost. | The question waits for the backup (up to a minute, Stop ends it); reading the state no longer waits. |
| A4 medium | A full backup drive was reported only as "OSError". | Plain words. JARVIS does not delete backups it would otherwise keep (the reviewer suggested thinning and trying again; within the keeping rules there is normally nothing left to thin). |
| A5 low | If the record could not be saved after a backup, a full backup was made every minute, unrecorded. | Remembered in the running Core too: nothing is tried for an hour. |
| A6 low | A folder inside JARVIS's own program folder was accepted (this record said it was refused). | Refused, before anything is created there. |
| A7 low | After a move to another folder, that folder stayed empty until the next planned time while the line counted the old backups. | Another folder starts afresh. |
| A8 low | A write-protected folder at TURN ON answered "Local operation failed". | A plain refusal. |
| A9 low | The weekly schedule slipped to the next weekday after a backup that ran a few seconds late. | The weekly gap is six and a half days. |
| A10 low | Words on screen not true to the Core: an error shown as "Off"; "more than two periods" after a first failed try; "as soon as JARVIS is idle" under an emergency stop; typed values replaced after a refusal; a backup made by hand in the automatic folder labelled "automatic". | Each corrected in `static/recovery.js`; the Core's status now says `never_succeeded`, `stop_holds`, `running` and which ids are on its record. |
| A11 low | Working files left by a Core closed during a backup; thinning under an emergency stop; BACK UP NOW after TURN OFF thinned; a restored full backup carries the schedule; a record row without an id; "+1:00" accepted as a time. | Swept after a day; no thinning under a stop or when switched off; said in section 2; odd rows ignored; the time must be two digits, a colon, two digits. |

The fixes were not reviewed again. In the sandbox window after them (empty data, a scratch folder, nothing able to
leave the PC): a folder that is not a full path was refused and the typed folder, "every week" and the time stayed
in the boxes; TURN ON; BACK UP NOW made one and the line said "1 automatic backup on record" and gave the next
weekly time; List backups showed it marked "automatic"; TURN OFF kept the folder and the backup.
