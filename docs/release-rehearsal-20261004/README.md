# Rehearsal of the Gates 17 and 19 tooling, 2026-10-04

Run by Claude Code on the owner's PC, owner account, not elevated, in sandbox folders under
`D:\JARVIS-release-work\gate19-local\`. Builds: `1.0.11-60d406fb6398` (proposed FINAL) and
`1.0.10-915e906516dc` (previous), from `D:\JARVIS-release-work\pkg-1.0.11` and `pkg-1.0.10`.
No shortcuts were created (`-NoShortcuts`), VirtualBox was not involved, and nothing was written under
`%APPDATA%\jarvis-desktop` during the runs (checked).

## What was rehearsed, and the result

| What | How | Result |
|---|---|---|
| `Invoke-Gate17.ps1` phases Install and Uninstall after the changes | `-Phase All -SkipBaseline -NoShortcuts`, 03:20Z to 03:26Z | PASS, all 12 checks (`gate17-all-phases.output.txt`) |
| The one-command driver `Invoke-Gate.ps1`, three starts | fresh sandbox, `-NoRestartCheck -SkipPhases AfterRestart,Cleanliness` | start 1 ran Install and stopped with the restart instructions; start 2 ran Uninstall then Update (Gate 19); start 3 found nothing left to do (`gate-driver-rehearsal.output.txt`, `gate-driver-log.jsonl`) |
| Gate 19 phase Update | inside start 2, 03:31Z to 03:35Z | PASS: previous build installed over kept data, update while running, rollback, update again, final stop (`gate19-records/`) |
| Driver stop rules | made-up records (`test-gate-driver-stops.ps1`) | a failed phase is not run again, also not with `rerun`; a missing Windows restart is asked for; an unfinished run stops and names `rerun`; a different build stops |
| Cleanliness phase | profile, AppData, Program Files, account and computer names pointed into a sandbox, `cmdkey` replaced by a stub (`rehearse-cleanliness.ps1`, `rehearse-cleanliness-2.ps1`) | behaves as intended: `.env` files inside the install and package folders are not reported, a stray `.env` and a stray JARVIS folder are; FAIL on this PC is expected (OneDrive is signed in here) |
| `Invoke-NextStep.ps1` decisions | fake folder tree, test mode (`test-next-step.ps1`) | 13 cases, each gives the intended step or message; VirtualBox is never called outside the jarvis-s6-val session |

Measured on this PC (Gate 19 records): update 31.8 s wall (verify package 8.2, copy 10.3, verify copy 11.3,
stop 1.1, switch 0.7); rollback 9.0 s; second update 17.2 s. The VM will be slower; its own measurements set
the bound (AMENDMENT-v3 D9).

Note on versions: the Install and Uninstall phases ran from the script as it was at 03:20Z to 03:30Z; the Update
phase ran from the final file. The only later edits are inside the Update block and one console message, so the
Install and Uninstall code that ran is the code in the final file (sha256
`fd2c34e288aa426b69a1fbb7aca3105e0656eea7a13d869165c5e74a3341b2a9`).

## Gate 18 tooling (same day, after Gates 17 and 19 passed in the VM)

| What | How | Result |
|---|---|---|
| A made-up backup | `make_synthetic_backup.py`: FINAL installed into a new sandbox, a made-up personality and two made-up memories, backup created and rehearsed through the running Core | backup_verified, restore_rehearsal_passed; laid out as a "disc" folder with `BACKUP-RECORD.json` |
| `tools/guest/Invoke-Gate18.ps1` (sha256 `cf0fe657…`) | run against that disc folder with the sandbox left by the Gates 17/19 driver rehearsal standing in for the VM (FINAL installed and stopped, package extracted) | PASS, all ten checks K0 to K9 (`gate18-rehearsal.output.txt`, `gate18-records/`); a second start is refused |
| `tools/host/Invoke-Gate18Step.ps1` decisions | fake folder tree, test mode (`test-gate18-step.ps1`) | 16 cases, each gives the intended step or message; refuses until the authorisation file exists; never touches the backup drive or VirtualBox outside the jarvis-s6-val session |

Not rehearsed for Gate 18: the owner's real backup (made by the old everyday JARVIS; whether FINAL accepts it
is what the gate tests), the copy from the backup drive, `New-Gate18RecoveryDisc.ps1` and `Start-Gate18Vm.ps1`
(disc build and VirtualBox), and double-clicking `gate18.cmd` from the disc.

## What could not be rehearsed here

- **Anything that calls VirtualBox**: `Start-Gate17Vm.ps1` (attaching the two discs, then the proven
  `Start-FreshVm.ps1`) and the snapshot step of `Invoke-NextStep.ps1` (the proven `Take-FreshVmSnapshot.ps1`).
  Claude never runs VirtualBox. The `storageattach` lines use the same syntax as `New-FreshVm.ps1`, which worked
  at Gate 16R step 6.
- **Building the package discs** (`New-Gate17PackageDisc.ps1`): the image builder `New-PackageIso.ps1` is
  unchanged and has built every disc so far, but only small ones (about 1 MB). A 526 MB payload is expected to
  fit its default size limit (about 681 MB) but has not been built yet.
- **AfterRestart** (JARVIS starting by itself from the Startup shortcut after a Windows restart) and the real
  **Desktop and Startup shortcuts**: these exist only on the VM and are part of what Gate 17 tests.
- **Double-clicking `gate.cmd` from a disc inside the VM**, and finding the second disc by drive type.
- The `rerun` path for a run that never finished was tested only up to the point where it stops and asks for the
  word; actually repeating a phase after a reset was not exercised.
