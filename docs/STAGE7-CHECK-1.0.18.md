# Stage 7 check of 1.0.18 (plan for your approval)

Status: **READY FOR YOUR APPROVAL (2026-10-10, 10:50 local, Claude Code), with one decision of yours first: whether the
missing `devices` route for the phone goes into 1.0.18 (see "Before you approve").** Every check on this PC has passed
for `1.0.18-4afd891c38f4` and is recorded in `docs/release-rehearsal-20261010-1018/README.md`. Nothing has run in the
VM. Approving lets Claude place the tools and create this check's record folders; every VirtualBox step stays yours, as
for 1.0.11, 1.0.14, 1.0.15, 1.0.16 and 1.0.17.

## Before you approve: the `devices` route

The phone app's device panel (the Mac's R6) asks the PC for a list of your devices. That route was promised to the Mac
in `docs/MAC-REQUESTS-20261007.md` but never built into the Core: 1.0.17 and this build answer "Operation unavailable."
and the panel shows "not on this Core yet". Nothing else is affected. Two ways:

- **"add devices to 1.0.18":** Claude builds the route (read only: your paired devices, the PC, the test client
  marked as simulated), tests it, has it reviewed, builds 1.0.18 again (build 2) and runs every check above again;
  this plan is then rewritten for build 2 and offered again. About two hours of Claude's time, none of yours.
- **"devices later":** this plan stands as written for build 1; the route comes in a later release.

## What it is

The standard check every release passes before it reaches your everyday JARVIS (your Stage 7 decision of 2026-10-04),
now for **1.0.18-4afd891c38f4** (the Workshop, `docs/WORKSHOP.md`: JARVIS working with files, commands, his own Python
environment, lessons and missions in his own folder on this PC; commands ship as "ask first") against
**1.0.17-0d38218c4e1d** (your everyday JARVIS). The same pass as for 1.0.17, in the same VM, **with the same version 4
scripts, unchanged** (`docs/STAGE7-DRIVER-V4.md`): install from `JARVIS-Setup-1.0.18-4afd891c38f4.exe`, first launch,
the entry in Settings > Apps, Windows restart with automatic start, uninstall through that entry, reinstall from the
Setup, 1.0.17 installed and updated to 1.0.18 while running, rollback, update again, one update through the Setup, and
an update killed mid-copy then run again, with test data kept throughout. Updating your everyday JARVIS afterwards is a
separate decision of yours.

## The build

- **1.0.18-4afd891c38f4** (commit 4afd891): zip `D:\JARVIS-release-work\release\JARVIS-1.0.18-4afd891c38f4.zip`,
  533,444,176 bytes, sha256 `8d44eba680bacf2e9a7e0c0a0cabd29c243412639ecf5a51154b56c10b845bc4`; its Setup
  `D:\JARVIS-release-work\release\JARVIS-Setup-1.0.18-4afd891c38f4.exe`, 406,974,294 bytes, sha256
  `eb1f0ee38c5672e506e73d7b3692a077ce776153ab9c248b21baf7f313fd3d05` (record `JARVIS-Setup-1.0.18-4afd891c38f4.setup.json`
  beside it: built from this package's manifest; unsigned, decision D3). The same four files are in
  `D:\JARVIS-release-work\pkg-1.0.18`, the folder the disc is built from (hashes read back equal).
- What is new since 1.0.17: the Workshop, the 1.0.18 entry of `release-notes.json` (`workshop.py`, Settings > Workshop,
  five permission rows, routes `GET/POST /api/workshop`, the settings `workshop_minutes` and `workshop_folders`; 56
  tools). Nothing else changed in the program.
- Previous build: **1.0.17-0d38218c4e1d** from its existing Stage 7 disc `JARVIS-STAGE7-1.0.17-0d38218c4e1d.iso`
  (sha256 `519c0257e32127f87b46e6658bac5b5f5d418cff16238e90e056a23d8ab16a19`, 941,621,248 bytes, in
  `D:\JARVIS-S6-FRESHVM\media`; read again on 2026-10-10: equal to its record), which carries that build's zip, Setup
  and records at its root. No new disc for it.

## Already done on this PC

Records: `docs/release-rehearsal-20261010-1018/README.md`.

- Development suites at the release commit: 809 Python (none skipped), 60 desktop, 18 Intelligence, 27 interface
  scripts.
- Compared with 1.0.17: the same pinned parts (Python, its packages, the models, Electron, the Windows runtime files);
  of the shipped source 12 files changed, 3 added and 0 removed, exactly the Workshop's work; `JARVIS.exe` and its
  bootstrap differ only in the version number they carry (4 bytes of the program's version stamp, one line of the
  bootstrap).
- Release regression with the release's own Python and Electron (`JARVIS.exe`), run alone on the PC: **PASS**
  (808 Python tests OK with 7 skipped by their own conditions, the same 7 as for 1.0.17; 60 desktop, 18 Intelligence,
  27 interface scripts; the release verified unchanged before and after).
- Zip install in a sandbox: installed in 30 s, launched through `JARVIS.exe` (the Core up in 23.1 s, 8 processes),
  verified, then uninstalled: all 10,772 program files removed, data kept, nothing left running.
- The Setup rehearsed in a sandbox with your real Desktop and Startup shortcuts recorded before and after every step
  and required unchanged: PASS (silent install 82.7 s, launch through `JARVIS.exe` in 20.7 s, reinstall 59.5 s, the
  uninstall through the entry's own uninstaller 10.2 s with all program files removed and the data kept); your real
  shortcuts' hashes the same before and after; your running JARVIS untouched (8 processes before and after).
- The whole Stage 7 pass 1.0.17 -> 1.0.18 in a sandbox with the version 4 scripts: **ALL STAGE 7 STEPS PASSED**
  (2026-10-10, 10:28-10:42, 29 checks): install from the Setup (71.1 s wall; the installer inside it: verify package
  7.5 s, copy 14.0 s, verify copy 7.8 s, switch 1.1 s), the sandbox entry, launch through `JARVIS.exe` (8 processes);
  the restart check; uninstall through the entry (10 s) and reinstall from the Setup (69.2 s wall); 1.0.17 installed
  and updated to 1.0.18 while running (31 s wall), rollback to 1.0.17 (10.4 s), update again (18.6 s wall), one update
  through the Setup (67 s wall); and the interrupted update (the rerun 28.8 s wall). Every lap far inside the Gate 20
  bound. The first pass whose previous build has its own `JARVIS.exe` and Setup: the driver needed no change.

## Your steps (about two hours, mostly waiting; the same seven as for 1.0.17)

One launcher on the PC, `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.18\stage7-step.cmd` (a new folder; the earlier tools stay
as they are), and one file inside the VM, `stage7` on this check's disc (drive E:).

| # | Where | What you do | What happens |
|---|---|---|---|
| 1 | PC, jonny | double-click `stage7-step` | builds the Stage 7 disc (about 940 MB; building and checking it takes up to ten minutes); tell Claude "disc built" |
| 2 | PC, jarvis-s6-val | double-click `stage7-step` and **leave its window open until it closes by itself** | restores the clean snapshot, attaches the two discs, starts the VM. The VM's power-on can take two to three minutes while the window says "Waiting for VM to power on": do not close the window and do not start the launcher a second time during that wait |
| 3 | inside the VM | sign in (`jarvis-s6-guest` / `fresh-vm-2026`), open **drive E:**, check that the files on it say **1.0.18**, double-click `stage7` | installs 1.0.18 from the Setup and tests it (about 30 minutes). Both discs are named `JARVIS_S7`: drive D: is the 1.0.17 disc, drive E: this check's. While the Setup runs, the window prints one line every half minute; that is progress, not a hang. Wait for "The install step PASSED" |
| 4 | inside the VM | quit JARVIS from its icon near the clock, **Start > Power > Restart**, sign in, wait a minute, open drive E: again, double-click `stage7` again | restart check; uninstall through Settings > Apps' own uninstaller and reinstall from the Setup; update, rollback, update again, one update through the Setup; the interrupted update (about 70 minutes). It does not matter how long after the restart you start it |
| 5 | inside the VM | when it says ALL STAGE 7 STEPS PASSED: Start > Power > Shut down | |
| 6 | PC, jarvis-s6-val | double-click `stage7-step` | takes the snapshot `STAGE7-PASS-1.0.18-4afd891c38f4` |
| 7 | this chat | say "stage 7 done" | Claude checks every record and gives the result |

## What is checked

Exactly as for 1.0.17 (`docs/STAGE7-CHECK-1.0.17.md`, "What is checked"): 29 checks. All met: `STAGE_7_COMPLETE` for
1.0.18; anything not met: `STAGE_7_INCOMPLETE` with the exact step.

**Timing bound (your decision of 2026-10-06, "accept the VM time"):** install, update and rollback each within 600 s,
stopping JARVIS within 120 s, measured on the installer's own seconds inside the Setup (not on the Setup's unpacking,
recorded as its own wall time). A measurement outside the bound is accepted as a disposition only when this check's
own records show the cause to be the VM; otherwise the step is repeated before acceptance, and only on your decision.
The verdict on what is tested does not depend on the timings.

## Differences from the check of 1.0.17

1. **Builds:** 1.0.18 under acceptance, 1.0.17 as the previous build, from 1.0.17's own Stage 7 disc.
2. **Scripts: the same version 4 files you approved for 1.0.17, byte for byte** (the hash table below is that
   approval's table, read again on 2026-10-10 at commit 4afd891: unchanged). No new tool.
3. **The previous build now has its own program and Setup.** In the update steps the VM's 1.0.17 runs through its
   own `JARVIS.exe`, and after the rollback to 1.0.17 its shortcuts point at 1.0.17's `JARVIS.exe` (for 1.0.17's check
   they pointed at PowerShell after the rollback). The sandbox pass shows the driver handles this without change.
4. **Start point:** the VM is on the snapshot `STAGE7-PASS-1.0.17-0d38218c4e1d` (uuid
   `26a2163a-8d6b-4892-ae97-6f10e9bfb676`; read from its settings file on 2026-10-10: currentStateModified false, last
   state change 2026-10-07T07:04:19Z, nothing changed since). The launcher restores FRESH-PREREQ only if the VM is on
   that snapshot (or already on FRESH-PREREQ) and VirtualBox records no change since; otherwise it stops and restores
   nothing. Every snapshot is kept (nine now).
5. **Names:** the disc `JARVIS-STAGE7-1.0.18-4afd891c38f4.iso` with `stage7-target.json`; the PC records
   `D:\JARVIS-stage7\1.0.18-4afd891c38f4\evidence`; the VM records
   `D:\JARVIS-S6-FRESHVM\evidence\guest-egress-01\stage7-1.0.18-4afd891c38f4`; the final snapshot
   `STAGE7-PASS-1.0.18-4afd891c38f4`; the launcher folder `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.18`.
6. **Expected sights:** the same as for 1.0.17, with "1.0.18" in the Installed-apps entry; after the rollback inside
   the VM, 1.0.17 runs on data written by 1.0.18 (the Workshop's new tables are left alone; 1.0.17 has no Workshop).
7. **Not tested in the VM, new with 1.0.18:** the Workshop's missions and its commands run by JARVIS, because they need
   an AI provider and the VM has no keys. The Workshop's own code is covered by the regression (`test_workshop.py`
   runs real `cmd.exe` commands and the test Python in a temporary workshop, and the mission loop with a stand-in
   model); its Settings panel by `test_workshop_view.cjs`.
8. **Windows Update in the VM** is still paused until 2026-11-06 05:27 UTC (16:27 your time). Run the check before
   then, or re-pause it yourself first.

Unchanged from the plans: no checkpoints P0-P5; the Gate 17 cleanliness check is not repeated; not tested in the VM:
an AI conversation (no keys in the VM), a real microphone, install under a non-administrator account, and none of the
parts that need a provider, Ollama, another device, a backup drive or a private network. Stop rules: any failed step
stops everything and nothing is repeated without your decision; a UAC prompt is a STOP; 15 minutes without progress
(the half-minute lines count as progress): tell Claude before any reset; every VM start goes through the launcher;
VirtualBox only in jarvis-s6-val.

## What Claude does on your approval

1. Records it in `../governance/STAGE7-1.0.18-APPROVAL-RECORD.json` with this plan's hash and the tool hashes below.
2. Creates `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.18\` with the five version 4 host files (the four launcher scripts and
   the disc builder), `Start-FreshVm.ps1`, `Take-FreshVmSnapshot.ps1` and `stage7-authorized.json` (schema
   `jarvis-stage7-authorized-v4`; final 1.0.18-4afd891c38f4, previous 1.0.17-0d38218c4e1d, label 1.0.18-4afd891c38f4,
   expected current snapshot STAGE7-PASS-1.0.17-0d38218c4e1d), each copy hash-checked.
3. Creates the two record folders named above (nothing else on D: changes).

Tool hashes (sha256, read on 2026-10-10 at commit 4afd891; equal to the table you approved for 1.0.17):

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

After your choice on the `devices` route ("devices later" keeps this plan as it is), reply in your own words that you
approve this check, for example: "I approve the Stage 7 check of 1.0.18".
