# Release rehearsal evidence, 2026-10-01

Local, non-elevated rehearsal of the per-user release (docs/RELEASE-DESIGN.md) on the
owner's PC, before any Stage 6 VM work. Everything ran in sandbox install folders on D:
(`D:\JARVIS-release-work\`) with `--no-shortcuts` and synthetic data only. The live JARVIS
installation, backups, protected paths and the Stage 6 evidence folders were not touched.
No VM, no elevation, no network exposure, no provider keys.

Releases were built with `tools/build_release.py --no-zip --out D:\JARVIS-release-work\release`
(C: had about 5 GB free). The distributable zip and `install.cmd` from an extracted zip were
**not** exercised here; see "Not covered".

## Releases

| Release | Commit | Notes |
|---|---|---|
| 1.0.2-3dc1a2016c6b | 3dc1a20 | first byte-identical release (unchecked-hash bytecode) |
| 1.0.3-f3f8e4b2c30e | f3f8e4b | builder options only |
| 1.0.4-5eb1df88bf4a | 5eb1df8 | installer: crash-safe launcher/current.json, damaged-release repair |
| 1.0.5-4838941b3037 | 4838941 | inspection renders with Edge instead of a hidden Chrome dependency |
| 1.0.6-c31cccf9ee1a | c31cccf | inspection retries a failed first browser start; failures logged to core.log |
| 1.0.7-6c356bf982de | 6c356bf | same sources as 1.0.6; built with the distributable zip |

Release records (`*.release.json`) for 1.0.2, 1.0.3, 1.0.4, 1.0.6 and 1.0.7 are in this folder.

## 1. Lifecycle rehearsal, 1.0.2 → 1.0.3 (superseded by section 4)

`lifecycle_rehearsal_d.py`, output `lifecycle_rehearsal_d.output.txt`. Fresh install 1.0.2,
memory saved, update to 1.0.3 **while JARVIS was running**, verify after use, rollback,
uninstall (21,290 program files removed, `data`/`config`/`profile` kept, 0 leftover program
files), reinstall (memory restored), verify. Every step passed.

## 2. Interrupted update: crash at each step

Unit level (`test_installer.py`, commit 5eb1df8): a fault injected at each update step:
part-way through copying, before the release folder is renamed into place, while stopping
the running JARVIS, while writing the launcher, while switching `current.json`, while
writing shortcuts. After each: the current release is intact and verifies, the launcher is
intact, data is untouched, and rerunning the installer completes the update with no debris.
Two gaps were found and fixed before these tests passed: the launcher and `current.json`
were not written atomically with a flush, and a damaged installed release blocked every
later install instead of being repaired.

Real process (`interrupted_update_rehearsal.py`, output
`interrupted_update_rehearsal.output.txt`): with JARVIS 1.0.3 running, the 1.0.4 installer
was force-killed after copying 3,502 of 10,645 files. JARVIS 1.0.3 kept running (8
processes, Core answering), memory was kept, 1.0.3 still verified, no 1.0.4 folder
existed. Rerunning the installer completed the update (previous = 1.0.3, no leftover
`.incoming` folder), 1.0.4 launched and verified after use.

Not simulated: a real power cut (the flush-and-rename writes are the protection; covered at
unit level only).

## 3. Release regression on 1.0.6

`tools/release_regression.py`, report `regression-1.0.6-report.json`. The release is
verified, copied, the copy verified again, and only the copy gets the tests from the
release's own commit. Every suite runs with the release's bundled Python and Electron
(Electron as node): no development `.venv`, no system node. Data, config and the Windows
account folders point at a fresh scratch account; the release is re-verified unchanged
afterwards.

| Suite | Result |
|---|---|
| Python unittest | 316 tests, all pass |
| desktop `node --test` | 34 tests, all pass |
| intelligence `node --test` | 18 tests, all pass |
| 16 root JS scripts (voice, wake, navigation, screen, timer) | all pass |

Found and fixed on the way (1.0.4 and 1.0.5 runs):

- Interface inspection launched installed **Google Chrome**, which a fresh Windows 11 PC
  does not have (a hidden development-machine dependency, Gate 17). It now uses Microsoft
  Edge, then Chrome; each gets a second launch attempt.
- Inspection failures were discarded; they are now written to `data\logs\core.log`.
- The harness itself: the shipped installer was not copied for `test_installer.py`, and a
  test account with profile, AppData and Temp in one folder made browsers refuse to start
  (not a product defect; 4 of 4 runs pass with a realistic fresh account layout).

## 4. Final lifecycle rehearsal, 1.0.4 → 1.0.6

`lifecycle_rehearsal_final.py`, output `lifecycle_rehearsal_final.output.txt`, new sandbox
`D:\JARVIS-release-work\sandbox-home-final`. Both releases carry the installer fixes.

Every step passed:

| Step | Result |
|---|---|
| Fresh install 1.0.4, launch, save a memory | installed; 8 processes; memory saved |
| Verify 1.0.4 while in use | verified |
| Update to 1.0.6 while JARVIS is running | installed; previous = 1.0.4; 0 stale 1.0.4 processes; memory kept |
| Launch 1.0.6, verify after use | 8 processes from 1.0.6, none from 1.0.4; verified |
| Rollback to 1.0.4, launch | rolled back; 0 stale 1.0.6 processes; memory kept; 8 processes from 1.0.4 |
| Uninstall | 21,290 program files removed; `config`, `data`, `profile` kept; 0 JARVIS processes; 0 leftover program files; memory kept |
| Reinstall 1.0.6 | installed; memory restored |
| Verify installed files | verified |

## 5. Distributable zip, 1.0.7

1.0.7-6c356bf982de was built **with** its zip (`build_release.py --version 1.0.7 --out ...`),
from commit 6c356bf (this evidence; application sources identical to 1.0.6). Zip:
525,590,739 bytes, SHA-256 `024c6166866a505700019d25f95e1e8f99dc34ab2f0fa011c81be6bbd4995396`.

`zip_install_rehearsal.py`, output `zip_install_rehearsal.output.txt`: the zip matches the
hash in its release record; Windows `Expand-Archive` extracts `install.cmd`, `installer.py`
and `release\`; `install.cmd --home <sandbox> --no-shortcuts` installs in 27 s (exit 0);
JARVIS launches (8 processes, Core answering); verify after use passes; uninstall removes
10,645 program files, keeps `data`/`config`/`profile`, leaves 0 processes and 0 program files.

Full regression on 1.0.7 itself (`regression-1.0.7-report.json`): 316 Python, 34 desktop,
18 Intelligence and 16 JS scripts, all pass. It was rerun rather than inherited from 1.0.6
because build-time files that record the build folder (bytecode, pip console-script
launchers and their RECORD files) differ between releases; the sources do not.

## 6. Backup/restore and Gate 17 preparation: releases 1.0.8 to 1.0.10 (later on 2026-10-01)

| Release | Commit | Change |
|---|---|---|
| 1.0.8-d326428391cc | d326428 | regression tests for the main-desktop header and delete/admission defects (15a1ad1) |
| 1.0.9-37eb838823dc | 37eb838 | backup/restore from an installed release; installer phase timings |
| 1.0.10-915e906516dc | 915e906 | owner-config location follows the installation; offline voice check uses the bundled model; zip 525,619,975 bytes, SHA-256 `a945b38a3aff733d3228d617812c8ab7f85f0f8b09c66b2aaed5212c2ec771d4` |
| 1.0.11-60d406fb6398 | 60d406f | backup works while the Core runs; Core state, logs and session token never saved; zip 525,622,280 bytes, SHA-256 `1923651176dd3095e84b0628a5c7a90608b6db57fe06986670e0ea8246225a58` |

**1.0.8 regression:** 318 Python, 36 desktop, 18 Intelligence, 16 JS scripts, all pass
(`regression-1.0.8-report.json`).

**1.0.9 regression:** desktop 36, Intelligence 18 and the 16 scripts pass; **1 Python
failure** (`test_personal_config_only_when_asked`): with the suite running inside an
installed layout, `switch_over` wrote a synthetic installation's personality into the
process's own config folder. A real semantics defect in that day's change (the config
location followed the process environment, not the installation being operated on), caught
only because the packaged regression runs the suite with `JARVIS_*` set. Fixed in 1.0.10
(`runtime_paths.config_dir_for`); the affected tests now run both normally and under an
installed-style environment.

Defects in the packaged layout found while designing the Gate 18 rehearsal, all fixed
with tests before 1.0.10 (commits 37eb838, f033546, and the config-location fix):

1. `recovery.py` / `switch_over.py` command lines looked for data beside the program;
   the installed release keeps it in `<home>\data`. An installed release is now recognised
   from its own layout, so the documented commands work without the launcher's environment.
2. Backups of an installed release left out the owner's `personality.txt` and
   `preferences.json` (they live in `config\`, not beside the code).
3. `switch_over --include-personal-config` wrote into the release's program files, which
   would have broken verification; it writes to `config\` now.
4. `check_voice_offline.py` loaded Whisper from a development path (`app\data\...`) and
   would have failed on the VM; it now uses the Core's own model location.
5. The config-location semantics defect above.
6. Found by the Gate 18 rehearsal against 1.0.10 (step 2 failed, HTTP 400 "PermissionError
   13"): a backup could not be made while the Core was running, because the backup read
   `data\core.lock`, which the one-Core lock (added the same day) holds open. The backup
   inventory now skips the live Core files, `data\logs` (the documentation already said
   logs are excluded; the code did not) and `.jarvis-session.json`, which carries the Core
   token and must never be in a backup. Fixed in 1.0.11 with a test that holds a real lock.

The Core now reports `installed_release` (from the release manifest) in `/api/state`,
and the installer reports per-phase seconds, for the Gate 17–19 identity and timing evidence.

**1.0.10 regression** (`regression-1.0.10-report.json`): 324 Python, 36 desktop, 18
Intelligence, 16 JS scripts, all pass.

**1.0.10 zip install** (`zip_install_rehearsal-1.0.10.output.txt`): hash matches the
record; `install.cmd` installs in 41 s; launch (8 processes, Core answering); verify after
use; uninstall removes 10,645 program files, keeps `data`/`config`/`profile`, 0 processes,
0 leftover program files. The running Core reported `installed_release`
`1.0.10-915e906516dc` and `source_revision e9c5a87060d78190` (Gate 18 step 1).

**1.0.11 regression** (`regression-1.0.11-report.json`): 325 Python, 36 desktop, 18
Intelligence, 16 JS scripts, all pass.

**1.0.11 zip install** (`zip_install_rehearsal-1.0.11.output.txt`): hash matches the
record; `install.cmd` installs in 31 s; launch (8 processes, Core answering); verify after
use; uninstall removes 10,645 program files, keeps `data`/`config`/`profile`, 0 processes,
0 leftover program files.

**Gate 18 rehearsal, 1.0.8 → 1.0.10 and 1.0.8 → 1.0.11** (`gate18_rehearsal.py`, output
`gate18_rehearsal-1.0.10.output.txt`): install A (1.0.10), owner personality in `config\`,
memories saved; backup through the Core, hash recorded, rehearsal verified, the shipped
command line verifies it with no environment; owner configuration present in the backup;
disposable target B (1.0.8 then 1.0.10, so a rollback exists); switch-over dry run and
import with personal config; restored data and config before launch, program files still
verify; startup on restored data with identity, duplicate-Core fencing (a second launch
joins the same Core), shutdown; rollback with the restored data in place; backup source
unchanged. Against 1.0.10 the run **failed at step 2** (defect 6 above); rerun against
1.0.11 (`gate18_rehearsal-1.0.11.output.txt`): **every step passed.**

| Step | Result |
|---|---|
| Source install A (1.0.11), memories, identity | installed; Core reports `installed_release 1.0.11-60d406fb6398`; 2 memories saved |
| Backup through the Core while running | `backup_verified`, 403,932 bytes, SHA-256 `1d0b214d…`; restore rehearsal passed; archive in `data-backups`, outside program files |
| Shipped command line, no environment | `recovery.py verify` found the install's own data folder: `backup_verified`, 156 files |
| Owner configuration in backup | personality and preferences present (see harness note below) |
| Shutdown A | Core stopped on request; 7 shell processes ended by the harness; 0 left |
| Disposable target B: 1.0.8 then 1.0.11 | installed, previous = 1.0.8 (rollback available) |
| Switch-over dry run, then import with personal config | 2 files imported; database counts match the backup; personality and preferences written to `config\` |
| Restored state before launch | memories restored; personality in `config\`; program files still verify |
| Startup on restored data | 8 processes; identity equals A's; 2 memories via the API; a second launch joined the same Core |
| Rollback to 1.0.8 with restored data | rolled back; memories kept; 8 processes |
| Backup source unchanged | SHA-256 unchanged after everything |
(Harness note: the 1.0.11 run's line "owner configuration in backup: personality_txt false"
is a comparison mistake in the rehearsal script, not a product defect: the archive holds the
owner's personality byte-for-byte as written to disk, with `\r\n` endings, and the script
compared it with the `\n` string in memory; verified by reading the archive directly. The
script compares line-ending-neutrally now.)

**Gate 17 guest script, local rehearsal** (`tools/guest/Invoke-Gate17.ps1`, output
`gate17_local_rehearsal-1.0.10.output.txt`; sandbox home on D:, `-NoShortcuts`,
`-SkipBaseline` because this is a development PC). Against 1.0.10 (evidence folder
`gate17-20261001-134026`): package identity, extract, `install.cmd` (shortcuts off), verify,
launch (identity `1.0.10-915e906516dc` from the running Core, memory in the canonical
folder, no process image outside the install), duplicate-Core fencing, **offline speech
recognition with the bundled model (the defect-4 fix confirmed in the packaged release)**,
and stop/verify/restart all PASS; **U1-uninstall FAIL** was a harness defect: the script ran
maintenance commands with the installed release's Python, and `uninstall` first stops every
process running from the install folder, so it stopped its own interpreter before removing
anything (no output, 10,646 files untouched). Documented usage runs `installer.py` with the
package's Python beside `release\`, which is what the script does now. Follow-up noted, not
done: `installer.stop_running_jarvis` could exclude its own process defensively.
Rerun against 1.0.11 (`gate17_local_rehearsal-1.0.11.output.txt`, evidence folder
`gate17-20261001-140105/`): **PASS on every step.** Package identity (zip hash matches the
record); extract; `install.cmd` (shortcuts off); verify; launch in 13 s with
`installed_release 1.0.11-60d406fb6398` from the running Core, memory saved in the
canonical data folder, no process image outside the install; duplicate-Core fencing (a
second launch joined the same Core); offline speech recognition with the bundled model
("The meeting starts at 9 tomorrow morning", 4.5 s including model load); stop, verify
after use, restart with memory and identity intact; uninstall (10,645 program files
removed, `data`/`config`/`profile` kept, 0 leftover files, 0 processes); reinstall from the
extracted package with memory restored and files verified; final stop.

**Candidate for FINAL selection (owner act): 1.0.11-60d406fb6398.** Everything above
passed on it: regression, zip install, Gate 18 rehearsal, Gate 17 rehearsal.

Limitation recorded for both rehearsals: "clean shutdown" is scripted through
`/api/shutdown` (the Core stops on request and releases its lock); the desktop shell then
shows "Core stopped" and is ended by the harness. The owner's tray "Quit JARVIS completely"
path is not scriptable and is a manual step on the VM.

## Not covered (still needed before or during Stage 6)

- Desktop and Startup shortcuts (all runs used `--no-shortcuts`; creating them changes the
  owner's real Desktop and Startup folders).
- A clean Windows 11 machine (Gate 16R, owner only): no development tools, no Chrome.
- Real providers and audible voice (owner configuration; not part of this rehearsal).
