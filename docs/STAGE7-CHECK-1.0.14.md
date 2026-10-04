# Stage 7 check of 1.0.14 (plan for your approval)

Status: **READY FOR YOUR APPROVAL (2026-10-05, Claude Code). Rehearsed on this PC in a sandbox: all steps passed;
nothing has run in the VM.** Approving it
lets Claude place the tools and create this check's record folders; every VirtualBox step stays yours, as for 1.0.11.
It replaces the 1.0.12 draft (`docs/STAGE7-CHECK-1.0.12.md`): 1.0.12 and 1.0.13 were built but never offered.

## What it is

The standard check every release passes before it reaches your everyday JARVIS (your Stage 7 decision of
2026-10-04), now for **1.0.14-e03872680e1d** against **1.0.11-60d406fb6398** (your everyday JARVIS). The same pass
as the approved `docs/STAGE7-PLAN.md`, in the same VM: install, first launch, Windows restart with automatic start,
uninstall, reinstall, 1.0.11 installed and updated to 1.0.14 while running, rollback, update again, and an update
killed mid-copy then run again, with test data kept throughout. Updating your everyday JARVIS afterwards is a
separate decision of yours.

## The build

- **1.0.14-e03872680e1d** (commit e038726): zip `D:\JARVIS-release-work\release\JARVIS-1.0.14-e03872680e1d.zip`,
  525,633,503 bytes, sha256 `ceb7d9e1922cebbf650753c4028473c5962c558ed70ec9f4be20f9fdc740d8d3`.
- What is new since 1.0.11: the fixes in `docs/POST-CUTOVER-FIXES.md` items 1-6 (backup on a read-only disc, faster
  and safer stopping, no "Core stopped" box after a requested stop, version in Settings, clearer provider refusals,
  Gemini default model), and two found while checking the builds: the installer waits until every JARVIS program
  has really exited and refuses, changing nothing, if one keeps running (found by the 1.0.12 rehearsal); "Quit JARVIS
  completely" returns only when the Core has really exited (found by the 1.0.13 regression).
- Previous build: **1.0.11-60d406fb6398** from its existing package disc
  `JARVIS-PACKAGE-1.0.11-60d406fb6398.iso` (sha256 `02e6a79176b3...82af3`, the Stage 6 disc; no new one).

## Already done on this PC

Records: `docs/release-rehearsal-20261005-1014/README.md`.

- Compared with 1.0.11: the same 10,645 files; only the 14 JARVIS source files changed since 1.0.11 differ, plus
  compiled bytecode and the 29 pip launcher files that record the build folder. Python, Electron, the models and the
  Windows runtime files are identical.
- Release regression with the release's own Python and Electron: all pass (373 Python, 52 desktop, 18 Intelligence,
  17 interface scripts).
- Zip install in a sandbox: installed in 56 s, launched (8 processes, Core answering), verified, then uninstalled
  while running: all 10,645 program files removed, data kept, nothing left running.
- The whole Stage 7 pass 1.0.11 -> 1.0.14 in a sandbox with the version 2 scripts: **ALL STAGE 7 STEPS PASSED** (2026-10-05, 13.4 minutes): install; the restart check refusing without a restart; after-restart; uninstall (all 10,645 program files removed, data kept) and reinstall; update while running (64.8 s, stopping JARVIS 1.7 s), rollback (9.9 s), update again (33.1 s); and the interrupted update (installer killed after 3,300 of 10,645 files: 1.0.11 still current, verified and running with both memories; the rerun finished in 36.6 s). Your real JARVIS was not running and was never addressed. (The first attempt with 1.0.12 is why 1.0.12 was never offered.)

## Your steps (about 90 minutes, mostly waiting; the same as for 1.0.11)

One launcher on the PC, `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.14\stage7-step.cmd` (a new folder; the 1.0.11 tools
stay as they are), and one file inside the VM, `stage7` on the disc named `JARVIS_S7`.

| # | Where | What you do | What happens |
|---|---|---|---|
| 1 | PC, jonny | double-click `stage7-step` | builds the Stage 7 disc (a few minutes); tell Claude "disc built" |
| 2 | PC, jarvis-s6-val | double-click `stage7-step` | restores the clean snapshot, attaches the two discs, starts the VM |
| 3 | inside the VM | sign in (`jarvis-s6-guest` / `fresh-vm-2026`), open the `JARVIS_S7` disc, double-click `stage7` | installs 1.0.14 and tests it (about 25 minutes) |
| 4 | inside the VM | quit JARVIS from its icon near the clock, **Start > Power > Restart**, sign in, wait a minute, double-click `stage7` again | restart check; uninstall and reinstall; update, rollback, update again; the interrupted update (about 50 minutes) |
| 5 | inside the VM | when it says ALL STAGE 7 STEPS PASSED: Start > Power > Shut down | |
| 6 | PC, jarvis-s6-val | double-click `stage7-step` | takes the snapshot `STAGE7-PASS-1.0.14-e03872680e1d` |
| 7 | this chat | say "stage 7 done" | Claude checks every record and gives the result |

## What is checked

Exactly as in `docs/STAGE7-PLAN.md` ("What is checked"): install, first launch, version, a memory saved, second
launch joins, offline speech recognition, stop and start; JARVIS back by itself after the restart; uninstall and
reinstall with data kept; update, rollback, update again with both memories; the interrupted update. All met:
`STAGE_7_COMPLETE` for 1.0.14; anything not met: `STAGE_7_INCOMPLETE` with the exact step.

## Differences from the approved Stage 7 plan (`docs/STAGE7-PLAN.md`)

1. **Builds:** 1.0.14 under acceptance, 1.0.11 as the previous build (the plan: 1.0.11 and 1.0.10).
2. **Version 2 scripts.** The 1.0.11 scripts work for one pass only (their records sit in fixed places). Copies in
   `tools/guest/stage7-v2/` and `tools/host/stage7-v2/` (the 1.0.11 scripts stay unchanged as evidence) name
   everything after this check's label `1.0.14-e03872680e1d`:
   - the disc `JARVIS-STAGE7-1.0.14-e03872680e1d.iso`, which also carries `stage7-target.json` naming this check's
     folder;
   - the PC records `D:\JARVIS-stage7\1.0.14-e03872680e1d\evidence`;
   - the VM records `D:\JARVIS-S6-FRESHVM\evidence\guest-egress-01\stage7-1.0.14-e03872680e1d`;
   - the final snapshot `STAGE7-PASS-1.0.14-e03872680e1d` (1.0.11's was `STAGE7-PASS`).
3. **Start point and a new safeguard.** The VM is now on snapshot STAGE7-PASS (checked from its settings file on
   2026-10-05: no change recorded since). The launcher restores FRESH-PREREQ only if the VM is on STAGE7-PASS (or
   already on FRESH-PREREQ) **and** VirtualBox records no change since that snapshot; otherwise it stops and restores
   nothing. (1.0.11 started from GATE18-PASS.) Every snapshot is kept, including GATE18-PASS with your data.
4. **One new disc only:** the Stage 7 disc. The previous build comes from the existing 1.0.11 package disc.
5. **Records:** each run's first record (E0) now also notes the Windows build and whether the account is in
   Administrators (fix list item 7); error output of a program is recorded as part of the step instead of ending it.
6. **Stopping JARVIS now waits for it.** The installer waits until every JARVIS program has exited (up to five
   rounds) and refuses if one keeps running; a refusal inside the VM is a failed step (STOP). Re-checking an already
   installed release is timed as `verify_installed`, so the `stop` times are not comparable with the 95 s recorded
   at 1.0.11's G6.
7. **Expected sight:** during the update from 1.0.11, the running 1.0.11 window may still show its old "Core
   stopped" box; the check ends those windows anyway. From 1.0.14 on a requested stop closes the window quietly.
8. **The last message inside the VM** now names step 6 (snapshot in jarvis-s6-val) before "stage 7 done"; 1.0.11's
   message went straight to "stage 7 done".
9. **Windows Update in the VM** is paused until 2026-11-06 05:27 UTC (16:27 your time). Run the check before then,
   or re-pause it yourself first.

Unchanged from the plan: no checkpoints P0-P5; the Gate 17 cleanliness check is not repeated; not tested in the VM:
an AI conversation (no keys in the VM), a real microphone, install under a non-administrator account. Stop rules:
any failed step stops everything and nothing is repeated without your decision; a UAC prompt is a STOP; 15 minutes
without progress: tell Claude before any reset; every VM start goes through the launcher; VirtualBox only in
jarvis-s6-val.

## What Claude does on your approval

1. Records it in `../governance/STAGE7-1.0.14-APPROVAL-RECORD.json` with this plan's hash and the tool hashes below.
2. Creates `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.14\` with the four version 2 host files, `Start-FreshVm.ps1`,
   `Take-FreshVmSnapshot.ps1` and `stage7-authorized.json` (final 1.0.14-e03872680e1d, previous 1.0.11-60d406fb6398,
   label 1.0.14-e03872680e1d, expected current snapshot STAGE7-PASS), each copy hash-checked.
3. Creates the two record folders named above (nothing else on D: changes).

Tool hashes (sha256, commit e038726):

| File | sha256 |
|---|---|
| tools/guest/stage7-v2/Invoke-Stage7Pass.ps1 | `a88776736f9b6ccfe336962081c20c7baa1087100a14b1e3419800caf9e59fa5` |
| tools/guest/stage7-v2/Invoke-Stage7.ps1 | `8e20013d2bfe5814046153a5fbde8bcbb995781f487a3d67858f6a398d02053f` |
| tools/guest/stage7-v2/stage7.cmd | `7b992f854b9c35fd501880baf8cb6fb6a67ae0ba092639585c23cac7d290fd5a` |
| tools/host/stage7-v2/Invoke-Stage7Step.ps1 | `a6830df8cfe5e6a7af7bf7e763599bdf1534f836ecb101ba5768b9347cc8abae` |
| tools/host/stage7-v2/New-Stage7Disc.ps1 | `ad5566b0761ea04725efef584c7a4c50349e451f5b756308b2adfebd07913edc` |
| tools/host/stage7-v2/Start-Stage7Vm.ps1 | `6f027e36a47f801275526290d0335282e001bd381a78203a3e39fd2841382430` |
| tools/host/stage7-v2/stage7-step.cmd | `876c97ab3d00b469d4bf9bf47e3710ea09b8bb053f37a3db2d582abc3950399c` |
| tools/host/Start-FreshVm.ps1 | `d456da091c335e74c2f057068409cb5fe1a44ef3dcc156d780a83f16868a59a2` |
| tools/host/Take-FreshVmSnapshot.ps1 | `f4065b26a4abecf0bc71e6b219ee423832775ce822bde3588a764608bca3cad8` |
| tools/New-PackageIso.ps1 | `16df7178a9dea5a84829c225f76f421e379e86d3bc1c5c695cf1ab81f7b9ce60` |

## Approval

Reply in your own words that you approve this check, for example: "I approve the Stage 7 check of 1.0.14".
