# Stage 7 check of 1.0.12 (plan for the owner's approval)

**Superseded draft (2026-10-05): not for approval.** The sandbox Stage 7 rehearsal of 1.0.12 found an uninstall
defect (see `docs/release-rehearsal-20261004-1012/README.md`); 1.0.12 is not offered. 1.0.13 was superseded too (its
release regression found a shutdown race, `docs/release-rehearsal-20261005-1013/README.md`). The plan for approval
is `docs/STAGE7-CHECK-1.0.14.md`.

Draft, 2026-10-04. Nothing here has run in the VM. Approving it lets Claude place the tools and create the two
record folders; every VirtualBox step stays yours, as for 1.0.11.

## What it is

The standard check every release passes before it reaches your everyday JARVIS (Stage 7 owner decision, 2026-10-04),
now for **1.0.12-d28016b12efe** (the fixes in `docs/POST-CUTOVER-FIXES.md`) against **1.0.11-60d406fb6398** (your
everyday JARVIS). The same pass as `docs/STAGE7-PLAN.md`, in the same VM: install, first launch, Windows restart
with automatic start, uninstall, reinstall, 1.0.11 installed and updated to 1.0.12 while running, rollback, update
again, and an update killed mid-copy then run again, with your test data kept throughout.

## Already done on this PC

- Build 1.0.12-d28016b12efe: zip sha256 `744056508ab607bed8e7f89c14809e879b8320ea28df1eb9b8d60c25b6b3c991`.
  Compared with 1.0.11: the same 10,645 files; only the 14 JARVIS source files changed by the fixes differ, plus
  compiled bytecode and 29 pip launcher files that record the build folder (the same 29 differed between 1.0.10
  and 1.0.11). Python, Electron, the models and the Windows runtime files are identical.
- Release regression with the release's own Python and Electron: all pass (365 Python, 50 desktop, 18
  Intelligence, 17 interface scripts).
- Zip install, launch, verify and uninstall in a sandbox, and the whole Stage 7 pass 1.0.11 -> 1.0.12 run locally
  in a sandbox with the version 2 scripts (results in `docs/release-rehearsal-20261004-1012/README.md`).

## Differences from the approved 1.0.11 plan

1. **Version 2 scripts.** The 1.0.11 Stage 7 scripts only work once: their records sit in fixed places, so a second
   release would be refused or reported as "already done". New copies in `tools/guest/stage7-v2/` and
   `tools/host/stage7-v2/` (the 1.0.11 scripts stay unchanged as evidence) give each check its own label
   `1.0.12-d28016b12efe`, used for:
   - the disc `JARVIS-STAGE7-1.0.12-d28016b12efe.iso` (it also carries `stage7-target.json` naming this check's folder);
   - the PC records `D:\JARVIS-stage7\1.0.12-d28016b12efe\evidence`;
   - the VM records `D:\JARVIS-S6-FRESHVM\evidence\guest-egress-01\stage7-1.0.12-d28016b12efe`;
   - the final snapshot `STAGE7-PASS-1.0.12-d28016b12efe`;
   - the launcher `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.12\stage7-step.cmd` (a new folder; the 1.0.11 tools are not touched).
2. **Start point.** The VM is restored to FRESH-PREREQ from the current snapshot STAGE7-PASS (1.0.11 started from
   GATE18-PASS). New safeguard: the restore happens only if VirtualBox records no change since that snapshot.
   Every snapshot is kept, including GATE18-PASS with your data.
3. **Previous build disc:** the existing `JARVIS-PACKAGE-1.0.11-60d406fb6398.iso` (sha256 `02e6a791...`), no new one.
4. **Records:** each run's first record now also notes the Windows build (fix list item 7) and whether the
   account is in Administrators.
5. **Timings:** the installer now records re-checking an already installed release as `verify_installed`, so
   1.0.12's `stop` times are not comparable with the 95 s recorded at 1.0.11's G6.
6. **Expected sight:** during the update from 1.0.11, the running 1.0.11 window may still show its old "Core
   stopped" box; the check ends those windows anyway. From 1.0.12 on, a requested stop closes the window quietly.
7. **Windows Update in the VM** is paused until 2026-11-06. Run the check before then (or re-pause it yourself).
8. **Not covered:** install under a non-administrator Windows account stays untested (it would need a standard
   account created in the VM, which is your step and needs one administrator prompt).

## Your steps (the same as for 1.0.11)

1. **jonny account:** double-click `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.12\stage7-step.cmd` (builds the disc, a
   few minutes). Tell Claude "disc built".
2. **jarvis-s6-val account:** double-click the same file (restores FRESH-PREREQ, attaches both discs, starts the VM).
3. **Inside the VM** (sign in as jarvis-s6-guest): open the JARVIS_S7 disc and double-click `stage7`; follow what
   its window says (quit JARVIS from its icon, restart Windows, `stage7` again) until **ALL STAGE 7 STEPS PASSED**;
   then Start > Power > Shut down.
4. **jarvis-s6-val account:** double-click `stage7-step.cmd` again (snapshot). Tell Claude "stage 7 done".

Stop rules unchanged: any failed step stops everything and nothing is repeated without your decision; a UAC prompt
is a STOP; 15 minutes without progress: tell Claude before any reset.

## After the check

Claude checks the records and writes the result. Updating your everyday JARVIS to 1.0.12 is a separate decision
of yours afterwards.
