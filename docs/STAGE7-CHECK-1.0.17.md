# Stage 7 check of 1.0.17 (plan for your approval)

Status: **READY FOR YOUR APPROVAL (2026-10-07, 15:15 local, Claude Code): every check on this PC has passed for build 2
and is recorded in `docs/release-rehearsal-20261007-1017/README.md`.** Build 1 (`1.0.17-52342b46e48a`) is superseded and
was never offered: its release regression did not pass under the load of four checks at once (test defects and
timeouts, no product defect), the test fixes were committed, and build 2 is the same program built from that commit
(0 source files changed against build 1, the pinned inputs identical). Nothing has run in the VM. Approving it lets Claude place the tools and create this check's record folders; every VirtualBox step
stays yours, as for 1.0.11, 1.0.14, 1.0.15 and 1.0.16.

## What it is

The standard check every release passes before it reaches your everyday JARVIS (your Stage 7 decision of 2026-10-04),
now for **1.0.17-0d38218c4e1d** (build 2) ("JARVIS as his own app", the approved `docs/OWN-APP-PLAN.md`, with the access items of
`docs/PHONE-ACCESS-PLAN.md`, the three phone-check fixes, the music stop fix and the start-up song) against
**1.0.16-fccde24e2cc6** (your everyday JARVIS). The same pass as the approved `docs/STAGE7-PLAN.md`, in the same VM,
**with the version 4 scripts** (`docs/STAGE7-DRIVER-V4.md`), because this release installs differently: install from
`JARVIS-Setup-1.0.17-0d38218c4e1d.exe` (the one file you will use from now on), first launch, the entry in Settings > Apps,
Windows restart with automatic start, uninstall through that entry, reinstall from the Setup, 1.0.16 installed and
updated to 1.0.17 while running, rollback, update again, one update through the Setup, and an update killed mid-copy
then run again, with test data kept throughout. Updating your everyday JARVIS afterwards is a separate decision of
yours.

## The build

- **1.0.17-0d38218c4e1d** (commit 0d38218, build 2): zip `D:\JARVIS-release-work\release\JARVIS-1.0.17-0d38218c4e1d.zip`,
  533,361,567 bytes, sha256 `210b46235638e92bbef1634b853c53ae6838ed58e997543cab87ffa844bb01d9`; its Setup
  `D:\JARVIS-release-work\release\JARVIS-Setup-1.0.17-0d38218c4e1d.exe`, 406,936,706 bytes, sha256
  `b7bb04d36180c99251e61a0458e77af5eb4a50aafea5812ff14525bdd63eeb7e` (record `JARVIS-Setup-1.0.17-0d38218c4e1d.setup.json`
  beside it: built from this package's manifest; unsigned, decision D3). The same four files are in
  `D:\JARVIS-release-work\pkg-1.0.17`, the folder the disc is built from (hashes read back equal).
- What is new since 1.0.16: everything in `release-notes.json` for 1.0.17: JARVIS.exe with the Teague Industries badge
  and the Setup with the Installed-apps entry (`docs/OWN-APP-1.0.17.md`); replies streamed to the phone, "remember
  that", the action guard (`docs/PHONE-CORE-FIXES-20261007.md`); the access items A, C, D, G, E, F and H
  (`docs/PHONE-ACCESS-1.0.17.md`: device ticks and approvals from the phone, screen analysis and location from the
  phone, Gmail and Calendar, the memory release stamp, the routine's nudges and notices, the home-network list); the
  music stop fix and the start-up song (`docs/MUSIC.md`).
- Previous build: **1.0.16-fccde24e2cc6** from its existing Stage 7 disc `JARVIS-STAGE7-1.0.16-fccde24e2cc6.iso`
  (sha256 `dd3a1abedc602a5e767951a5350c3ef4c7425238520d3b1e99d0b86e159fab75`, 527,171,584 bytes, in
  `D:\JARVIS-S6-FRESHVM\media`; read again on 2026-10-07: equal to its record), which carries that build's zip and
  record at its root. No new disc for it.

## Already done on this PC

Records: `docs/release-rehearsal-20261007-1017/README.md`.

- Compared with 1.0.16: the same pinned parts (Python, its packages, the models, the Windows runtime files); of the
  shipped source 30 files changed, 86 added and 0 removed, exactly the work since 1.0.16; the only other difference
  is the planned program change: `JARVIS.exe` with its bootstrap is in, `electron.exe` is out. Compared with build 1:
  the same program (0 source files changed, the pinned inputs identical; only the bytecode and pip record files that
  carry the build folder and time differ).
- Release regression with the release's own Python and Electron (`JARVIS.exe`), run alone on the PC: **PASS**
  (776 Python tests OK with 7 skipped by their own conditions, 60 desktop, 18 Intelligence, 26 interface scripts;
  14:16-14:42; the release verified unchanged before and after).
- Zip install in a sandbox (nothing else running): installed in 47 s, launched through `JARVIS.exe` (the Core up in
  17.8 s, 8 processes), verified, then uninstalled: all 10,768 program files removed, data kept, nothing left running;
  the real shortcuts withheld, no launcher script.
- The Setup rehearsed in a sandbox with the owner's real Desktop and Startup shortcuts recorded before and after every
  step and required unchanged: on a rehearsal build of the same code (PASS, 13:11-13:15), on build 1's Setup (PASS,
  13:25-13:35) and on this build's own Setup (PASS, 14:50-14:53: silent install 90.4 s with the installer inside it at
  36 s, launch through `JARVIS.exe` in 18.8 s, reinstall 62.5 s, the uninstall through the entry's own uninstaller 10.4 s
  with all 10,768 program files removed and the data kept); the entry "JARVIS (sandbox)" under the sandbox id each
  time; the real shortcuts' hashes the same before and after; the installer's word "withheld" at every step.
- The whole Stage 7 pass 1.0.16 -> 1.0.17 in a sandbox with the version 4 scripts, on build 2 with nothing else
  running: **ALL STAGE 7 STEPS PASSED** (2026-10-07, 14:54-15:08, 29 checks; build 1 passed the same harness under
  load, 13:35-14:09): install from the Setup (67.3 s wall; the installer inside it: verify package 7.2 s, copy 11.1 s,
  verify copy 7.1 s, switch 0.1 s), the sandbox entry, the files verified, no `JARVIS.ps1`, launch through `JARVIS.exe`
  (8 processes); the restart check asking for the restart when there was none and seeing one when told of one;
  after-restart; uninstall through the entry's own uninstaller (10 s; all 10,768 program files removed, the entry and
  the package folder gone, data kept) and reinstall from the Setup (71.3 s wall); update while running (58.5 s wall;
  inside: verify package 18.2 s, copy 13.0 s, verify copy 24.5 s, stop 2.1 s, switch 0.6 s), rollback to 1.0.16
  (10.8 s), update again (33.1 s wall), one update through the Setup (69.2 s wall; stop 1.8 s, switch 0.9 s); and the
  interrupted update (the installer killed mid-copy; 1.0.16 untouched and running; the rerun 30.7 s wall). Every lap far
  inside the Gate 20 bound. The owner's real shortcuts unchanged throughout; the sandbox cleaned up through its own
  entry at the end. Records: `docs/release-rehearsal-20261007-1017/stage7-local-build2/`.
- The version 4 tools' decision tests: the launcher 19 cases, the guest driver 21 cases, all pass; the tools were
  reviewed with item 3.4 (no high finding; 8 medium and 9 low applied, `docs/OWN-APP-1.0.17.md` section 7).

## Your steps (about two hours, mostly waiting; the same seven as for 1.0.16, with three notes)

One launcher on the PC, `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.17\stage7-step.cmd` (a new folder; the earlier tools stay
as they are), and one file inside the VM, `stage7` on this check's disc (drive E:).

| # | Where | What you do | What happens |
|---|---|---|---|
| 1 | PC, jonny | double-click `stage7-step` | builds the Stage 7 disc. **Note 1:** this disc is about 940 MB (the zip and the Setup); building and checking it takes up to ten minutes; tell Claude "disc built" |
| 2 | PC, jarvis-s6-val | double-click `stage7-step` and **leave its window open until it closes by itself** | restores the clean snapshot, attaches the two discs, starts the VM. The VM's power-on can take two to three minutes while the window says "Waiting for VM to power on": do not close the window and do not start the launcher a second time during that wait |
| 3 | inside the VM | sign in (`jarvis-s6-guest` / `fresh-vm-2026`), open **drive E:**, check that the files on it say **1.0.17**, double-click `stage7` | installs 1.0.17 from the Setup and tests it (about 30 minutes). **Note 2:** both discs are named `JARVIS_S7`: drive D: is the 1.0.16 disc, drive E: this check's. **Note 3:** while the Setup unpacks and installs, the window prints one line every half minute ("the Setup (install) still running: ... s, ... files in the package folder"); that is progress, not a hang. Wait for "The install step PASSED" |
| 4 | inside the VM | quit JARVIS from its icon near the clock, **Start > Power > Restart**, sign in, wait a minute, open drive E: again, double-click `stage7` again | restart check; uninstall through Settings > Apps' own uninstaller and reinstall from the Setup; update, rollback, update again, one update through the Setup; the interrupted update (about 70 minutes; the Setup runs three more times, each with the half-minute lines). It does not matter how long after the restart you start it |
| 5 | inside the VM | when it says ALL STAGE 7 STEPS PASSED: Start > Power > Shut down | |
| 6 | PC, jarvis-s6-val | double-click `stage7-step` | takes the snapshot `STAGE7-PASS-1.0.17-0d38218c4e1d` |
| 7 | this chat | say "stage 7 done" | Claude checks every record and gives the result |

## What is checked

Exactly as in `docs/STAGE7-PLAN.md` ("What is checked"), with what version 4 adds: the Setup against its own record and
against the zip's manifest; the install from the Setup silently with no folder or shortcut switch (your double-click's
defaults); the Installed-apps entry "JARVIS 1.0.17, Teague Industries" pointing at the package folder's uninstaller;
no `JARVIS.ps1` written; both shortcuts pointing straight at this release's `JARVIS.exe`; the installer's own word
"written" (and "removed" at the uninstall) on the shortcuts; the uninstall through the entry's uninstaller with the
entry and the package folder gone and the data kept; the reinstall from the Setup with the entry back; after the update
and rollback steps of before, one update through the Setup from 1.0.16 running (G7), checked like the others with the
entry present; then the interrupted update as before. 29 checks (27 for 1.0.16). All met: `STAGE_7_COMPLETE` for
1.0.17; anything not met: `STAGE_7_INCOMPLETE` with the exact step.

**Timing bound (your decision of 2026-10-06, "accept the VM time"):** the Gate 20 bound applies to this check as to
every Stage 7 check: install, update and rollback each within 600 s, stopping JARVIS within 120 s. **New with the
Setup:** the bound is measured on the installer's own seconds inside the Setup (its answer `setup-result.json`:
verify package, copy, verify copy, switch; the same laps as before), not on the Setup's unpacking of 1.2 GB that comes
before them, which is recorded as its own wall time and is not an install step the bound names. A measurement outside
the bound is accepted as a disposition only when this check's own records show the cause to be the VM; otherwise the
step is repeated before acceptance, and only on your decision. The verdict on what is tested does not depend on the
timings.

## Differences from the check of 1.0.16 (`docs/STAGE7-CHECK-1.0.16.md`)

1. **Builds:** 1.0.17 under acceptance, 1.0.16 as the previous build, from 1.0.16's own Stage 7 disc.
2. **Scripts: version 4** (`tools/guest/stage7-v4/`, `tools/host/stage7-v4/`; `docs/STAGE7-DRIVER-V4.md`), copies of
   the version 3 scripts with the install from the Setup, the Installed-apps entry, the uninstall through it, the
   reinstall from the Setup, G7, the shortcut-target checks, progress lines while a Setup runs, and the sandbox id for
   rehearsals; the version 3 files are untouched. Reviewed with item 3.4; decision tests pass; rehearsed in a sandbox on
   this PC (above). The launcher accepts only a version 4 approval file.
3. **The disc** carries the Setup and its record beside the zip and the record (about 940 MB), so it is built with the
   version 4 copy of the disc builder (`tools/host/stage7-v4/New-PackageIso.ps1`: a DVD-sized image; the original is
   CD-sized and unchanged) and takes longer (Note 1). The VM reads it as a file, as every disc so far. The previous
   build's disc is 1.0.16's Stage 7 disc, as 1.0.15's was for the 1.0.16 check.
4. **Start point:** the VM is on the snapshot `STAGE7-PASS-1.0.16-fccde24e2cc6` (uuid
   `c91c7f1a-24dc-4bff-80eb-a21fa62ea264`; checked from its settings file on 2026-10-07: currentStateModified false,
   last state change 2026-10-06T08:59:37Z, no change recorded since that snapshot). The launcher restores FRESH-PREREQ
   only if the VM is on that snapshot (or already on FRESH-PREREQ) and VirtualBox records no change since; otherwise it
   stops and restores nothing. Every snapshot is kept (eight now).
5. **Names:** the disc `JARVIS-STAGE7-1.0.17-0d38218c4e1d.iso` with `stage7-target.json`; the PC records
   `D:\JARVIS-stage7\1.0.17-0d38218c4e1d\evidence`; the VM records
   `D:\JARVIS-S6-FRESHVM\evidence\guest-egress-01\stage7-1.0.17-0d38218c4e1d`; the final snapshot
   `STAGE7-PASS-1.0.17-0d38218c4e1d`; the launcher folder `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.17` with one file more
   than before (the version 4 disc builder).
6. **Timing bound:** as above, with the new sentence on the Setup's unpacking.
7. **Expected sights:** the install step is longer and shows only the half-minute lines while the Setup runs; in the
   VM's Settings > Apps > Installed apps the entry "JARVIS 1.0.17" appears after the install and vanishes at the
   uninstall step (the pass reinstalls it); after the install the shortcuts point at `JARVIS.exe` (its icon is the
   badge); after the rollback to 1.0.16 inside the VM, the 1.0.16 program runs on data written by 1.0.17 (the new
   tables and columns are left alone; 1.0.16 knows none of the new routes, ticks, routine, notices, mail, calendar or
   network list, and its shortcuts point at PowerShell again, as they did); the Setup's three later runs (reinstall,
   update through the Setup) each unpack the package again (the half-minute lines again).
8. **Not tested in the VM, new with 1.0.17:** Gmail and the calendar (no accounts in the VM); a paired device and the
   phone's half of every access item (no phone); the home-network list (not run in the VM; its tool is a read on request);
   the Nest camera (not built); the start-up song and the music through the VM's speakers (the VM has no audio device; the
   music stop fix was tested on this PC against the real media interface, and the sign-in greeting and the song after
   it need a voice provider the VM does not have); the owner's real shortcuts (the VM has its own).
9. **Windows Update in the VM** is still paused until 2026-11-06 05:27 UTC (16:27 your time). Run the check before
   then, or re-pause it yourself first.

Unchanged from the plans: no checkpoints P0-P5; the Gate 17 cleanliness check is not repeated; not tested in the VM:
an AI conversation (no keys in the VM), a real microphone, install under a non-administrator account, and none of the
parts that need a provider, Ollama, another device, a backup drive or a private network. Stop rules: any failed step
stops everything and nothing is repeated without your decision; a UAC prompt is a STOP; 15 minutes without progress
(the half-minute lines count as progress): tell Claude before any reset; every VM start goes through the launcher;
VirtualBox only in jarvis-s6-val.

## What Claude does on your approval

1. Records it in `../governance/STAGE7-1.0.17-APPROVAL-RECORD.json` with this plan's hash and the tool hashes below.
2. Creates `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.17\` with the five version 4 host files (the four launcher scripts and
   the disc builder), `Start-FreshVm.ps1`, `Take-FreshVmSnapshot.ps1` and `stage7-authorized.json` (schema
   `jarvis-stage7-authorized-v4`; final 1.0.17-0d38218c4e1d, previous 1.0.16-fccde24e2cc6, label 1.0.17-0d38218c4e1d,
   expected current snapshot STAGE7-PASS-1.0.16-fccde24e2cc6), each copy hash-checked.
3. Creates the two record folders named above (nothing else on D: changes).

Tool hashes (sha256, read on 2026-10-07 at commit 52342b4 and read again at 15:10 after build 2's pass, unchanged; the
version 4 files as reviewed and rehearsed on both builds; the two VM helpers unchanged since the 1.0.15 approval):

| File | sha256 |
|---|---|
| tools/guest/stage7-v4/Invoke-Stage7Pass.ps1 | `99085e0c5d31324d575ba6a04cc335f68e1b919667b37b6dea98f18c463396c9` |
| tools/guest/stage7-v4/Invoke-Stage7.ps1 | `d2c8257e09f58b682bf9cbff667cd48e1ce0f743e908d00c83e53cc301b60e89` |
| tools/guest/stage7-v4/stage7.cmd | `a72b44d5a22a3273bf33f0607c3dd930af0bbd1b76ac3fa33a8793e2fc49c3fb` |
| tools/host/stage7-v4/Invoke-Stage7Step.ps1 | `2f0f5631bb43bc63fe0ac539bdd08bf31ab66335eb7eed43f714db9fc47f69cb` |
| tools/host/stage7-v4/New-Stage7Disc.ps1 | `76921cc433b999bd1e0c47f8da2eb78ecf055a52caefbe3afb6714d721f97e73` |
| tools/host/stage7-v4/Start-Stage7Vm.ps1 | `a5fea2db7db308562598599a2bf34f2491f93c700d752f642701c5c7d6a7140b` |
| tools/host/stage7-v4/stage7-step.cmd | `5576c2232ae861a4b2e572319d86041cdef742419e8caa7f6a1367a68c4e6ad6` |
| tools/host/stage7-v4/New-PackageIso.ps1 | `cc5962c6a61f82539c178aa58c238b3691a44b559e73f34fcf3303a9ffec8961` |
| tools/host/Start-FreshVm.ps1 | `d456da091c335e74c2f057068409cb5fe1a44ef3dcc156d780a83f16868a59a2` |
| tools/host/Take-FreshVmSnapshot.ps1 | `f4065b26a4abecf0bc71e6b219ee423832775ce822bde3588a764608bca3cad8` |

## Approval

Ready. Reply in your own words that you approve this check, for example: "I approve the Stage 7 check of 1.0.17".
The approval names build 2, `1.0.17-0d38218c4e1d`; build 1 is superseded and no record of this check will name it.
