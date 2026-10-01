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

## Not covered (still needed before or during Stage 6)

- Desktop and Startup shortcuts (all runs used `--no-shortcuts`; creating them changes the
  owner's real Desktop and Startup folders).
- A clean Windows 11 machine (Gate 16R, owner only): no development tools, no Chrome.
- Real providers and audible voice (owner configuration; not part of this rehearsal).
