# Stage 7 check of 1.0.19 (plan for your approval)

Status: **READY FOR YOUR APPROVAL (2026-10-13, about 17:25 local, Hermes Agent).** Every check on this PC has passed
for `1.0.19-629bb5621d34` and is recorded in `docs/release-rehearsal-20261013-1019/README.md`. Nothing has run in the
VM. Approving lets Hermes place the tools and create this check's record folders; every VirtualBox step stays yours, as
for 1.0.11, 1.0.14, 1.0.15, 1.0.16 and 1.0.17.

This check **replaces the approved check of 1.0.18** (`docs/STAGE7-CHECK-1.0.18.md`, approved 2026-10-10, never run in
the VM, never installed): 1.0.19 is built on 1.0.18 and carries its time fix. The 1.0.18 tools folder and record folders
stay as they are, unused.

## What it is

The standard check every release passes before it reaches your everyday JARVIS (your Stage 7 decision of 2026-10-04),
now for **1.0.19-629bb5621d34** (one AI service, OpenRouter, with Qwen models only, and Fish Audio for the voice; OpenAI,
Qwen through Alibaba Cloud and Brave removed; plus 1.0.18's time sentence; `release-notes.json`, the 1.0.19 entry)
against **1.0.17-0d38218c4e1d** (your everyday JARVIS). The same pass as for 1.0.17, in the same VM, **with the same
version 4 scripts, unchanged** (`docs/STAGE7-DRIVER-V4.md`): install from `JARVIS-Setup-1.0.19-629bb5621d34.exe`, first
launch, the entry in Settings > Apps, Windows restart with automatic start, uninstall through that entry, reinstall from
the Setup, 1.0.17 installed and updated to 1.0.19 while running, rollback, update again, one update through the Setup,
and an update killed mid-copy then run again, with test data kept throughout. Updating your everyday JARVIS afterwards is
a separate decision of yours.

## The build

- **1.0.19-629bb5621d34** (commit 629bb56 on branch `claude/release-1.0.19`, which starts from 1.0.18's commit cffb826):
  zip `D:\JARVIS-release-work\release\JARVIS-1.0.19-629bb5621d34.zip`, 533,398,008 bytes, sha256
  `838371836d31758082d191738ebc3b41d0e34fe4b6598af6153d970ab8b21541`; its Setup
  `D:\JARVIS-release-work\release\JARVIS-Setup-1.0.19-629bb5621d34.exe`, 406,914,757 bytes, sha256
  `8e5bb3dceef85fc486f3d03b3864dfa3479c8833ffe471646cdd33dbcc36092f` (record `JARVIS-Setup-1.0.19-629bb5621d34.setup.json`
  beside it: built from this package's manifest; unsigned, decision D3). The same four files are in
  `D:\JARVIS-release-work\pkg-1.0.19`, the folder the disc is built from (hashes read back equal).
- What is new since 1.0.17: the time sentence (1.0.18, `server.py`) and the provider change (19 shipped source files, one
  removed; the list is in the rehearsal record). Python, its packages, the models and Electron are the same pinned parts.
  Four Microsoft C++ runtime files are the newer version Windows now holds on this PC (14.51; a runtime update of 11
  October), copied by the build as always; the regression ran on them.
- Previous build: **1.0.17-0d38218c4e1d** from its existing Stage 7 disc `JARVIS-STAGE7-1.0.17-0d38218c4e1d.iso`
  (sha256 `519c0257e32127f87b46e6658bac5b5f5d418cff16238e90e056a23d8ab16a19`, 941,621,248 bytes, in
  `D:\JARVIS-S6-FRESHVM\media`), which carries that build's zip, Setup and records at its root. No new disc for it.

## Already done on this PC

Records: `docs/release-rehearsal-20261013-1019/README.md`.

- Development suites at the release commit, and one independent review of the provider removal: no high finding,
  1 medium and 7 low, all applied (commit 629bb56).
- Compared with 1.0.18: the same pinned parts (Python, its packages, the models, Electron); of the shipped source 19
  files changed, none added, one removed (the old OpenAI diagnostic); `JARVIS.exe` and its bootstrap differ only in the
  version they carry.
- Release regression with the release's own Python and Electron (`JARVIS.exe`), run alone on the PC: **PASS**
  (2026-10-13, 16:12-16:37: 750 Python tests OK with 7 skipped by their own conditions, the same 7 as for 1.0.18; 60
  desktop, 18 Intelligence, 26 interface scripts; the release verified unchanged before and after). Two earlier starts
  were cut off when the chat was interrupted and gave no result; the build was not changed between them.
- Zip install in a sandbox: installed, launched through `JARVIS.exe` (the Core up in 18.7 s, 8 processes), verified,
  then uninstalled: all 10,766 program files removed, data kept, nothing left running.
- The Setup rehearsed in a sandbox with your real Desktop and Startup shortcuts recorded before and after every step
  and required unchanged: PASS (silent install 83.8 s, launch through `JARVIS.exe` in 21 s, reinstall 66.6 s, the
  uninstall through the entry's own uninstaller 12.2 s with all program files removed and the data kept); your real
  shortcuts' hashes the same before and after; your running JARVIS untouched.
- The whole Stage 7 pass 1.0.17 -> 1.0.19 in a sandbox with the version 4 scripts: **ALL STAGE 7 STEPS PASSED**
  (2026-10-13, 16:58-17:14, 56 PASS check records): install from the Setup (71.5 s wall), the sandbox entry, launch
  through `JARVIS.exe`; the restart check; uninstall through the entry (12 s) and reinstall from the Setup (71.1 s wall);
  1.0.17 installed and updated to 1.0.19 while running (73.2 s wall), rollback to 1.0.17 (13 s), update again (33.8 s
  wall), one update through the Setup (67.3 s wall); and the interrupted update (the rerun 34.1 s wall). Every lap far
  inside the Gate 20 bound. The driver needed no change; your real shortcuts and your running JARVIS were untouched.

## Your steps (about two hours, mostly waiting; the same seven as for 1.0.17 and 1.0.18)

One launcher on the PC, `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.19\stage7-step.cmd` (a new folder; the earlier tools stay
as they are), and one file inside the VM, `stage7` on this check's disc (drive E:).

| # | Where | What you do | What happens |
|---|---|---|---|
| 1 | PC, jonny | double-click `stage7-step` | builds the Stage 7 disc (about 940 MB; building and checking it takes up to ten minutes); tell Hermes "disc built" |
| 2 | PC, jarvis-s6-val | double-click `stage7-step` and **leave its window open until it closes by itself** | restores the clean snapshot, attaches the two discs, starts the VM. The VM's power-on can take two to three minutes while the window says "Waiting for VM to power on": do not close the window and do not start the launcher a second time during that wait |
| 3 | inside the VM | sign in (`jarvis-s6-guest` / `fresh-vm-2026`), open **drive E:**, check that the files on it say **1.0.19**, double-click `stage7` | installs 1.0.19 from the Setup and tests it (about 30 minutes). Both discs are named `JARVIS_S7`: drive D: is the 1.0.17 disc, drive E: this check's. While the Setup runs, the window prints one line every half minute; that is progress, not a hang |
| 4 | inside the VM | quit JARVIS from its icon near the clock, **Start > Power > Restart**, sign in, wait a minute, open drive E: again, double-click `stage7` again | restart check; uninstall through Settings > Apps' own uninstaller and reinstall from the Setup; update, rollback, update again, one update through the Setup; the interrupted update (about 70 minutes). It does not matter how long after the restart you start it |
| 5 | inside the VM | when it says ALL STAGE 7 STEPS PASSED: Start > Power > Shut down | |
| 6 | PC, jarvis-s6-val | double-click `stage7-step` | takes the snapshot `STAGE7-PASS-1.0.19-629bb5621d34` |
| 7 | this chat | say "stage 7 done" | Hermes checks every record and gives the result |

## What is checked

Exactly as for 1.0.17 (`docs/STAGE7-CHECK-1.0.17.md`, "What is checked"): 29 checks. All met: `STAGE_7_COMPLETE` for
1.0.19; anything not met: `STAGE_7_INCOMPLETE` with the exact step.

**Timing bound (your decision of 2026-10-06, "accept the VM time"):** install, update and rollback each within 600 s,
stopping JARVIS within 120 s, measured on the installer's own seconds inside the Setup (not on the Setup's unpacking,
recorded as its own wall time). A measurement outside the bound is accepted as a disposition only when this check's
own records show the cause to be the VM; otherwise the step is repeated before acceptance, and only on your decision.
The verdict on what is tested does not depend on the timings.

## Differences from the check of 1.0.17

1. **Builds:** 1.0.19 under acceptance, 1.0.17 as the previous build, from 1.0.17's own Stage 7 disc. 1.0.18 is skipped
   (never installed; its fix is inside 1.0.19).
2. **Scripts: the same version 4 files you approved for 1.0.17 and 1.0.18, byte for byte** (the hash table below, read
   again on 2026-10-13 at the release commit: unchanged). No new tool.
3. **The previous build has its own program and Setup**, as for 1.0.18's plan: in the update steps the VM's 1.0.17 runs
   through its own `JARVIS.exe`, and after the rollback its shortcuts point at 1.0.17's `JARVIS.exe`. The sandbox pass
   shows the driver handles this without change.
4. **Start point:** the VM is on the snapshot `STAGE7-PASS-1.0.17-0d38218c4e1d` (uuid
   `26a2163a-8d6b-4892-ae97-6f10e9bfb676`; read from its settings file on 2026-10-13 at about 17:20: currentStateModified
   false, last state change 2026-10-07T07:04:19Z, nothing changed since; nine snapshots kept). The launcher restores
   FRESH-PREREQ only if the VM is on that snapshot (or already on FRESH-PREREQ) and VirtualBox records no change since;
   otherwise it stops and restores nothing.
5. **Names:** the disc `JARVIS-STAGE7-1.0.19-629bb5621d34.iso` with `stage7-target.json`; the PC records
   `D:\JARVIS-stage7\1.0.19-629bb5621d34\evidence`; the VM records
   `D:\JARVIS-S6-FRESHVM\evidence\guest-egress-01\stage7-1.0.19-629bb5621d34`; the final snapshot
   `STAGE7-PASS-1.0.19-629bb5621d34`; the launcher folder `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.19`. None of these
   exists yet (checked 2026-10-13, 17:20).
6. **Expected sights:** the same as for 1.0.17, with "1.0.19" in the Installed-apps entry. After the rollback inside
   the VM, 1.0.17 runs on data written by 1.0.19. 1.0.19 adds no setting, table or data format (the existing backup
   switch now means OpenRouter's own backup model), so nothing in the data differs.
7. **Not tested in the VM, new with 1.0.19:** the AI answers themselves (no keys in the VM, as always). They are covered
   by the regression (the OpenRouter provider tests with stand-in answers) and by the live test of 2026-10-13 on this PC
   (6 of 6 through OpenRouter with the owner's key, recorded in `docs/CURRENT-STATUS.md` on the merge branch, section
   "2026-10-13", "OpenRouter credit and the live function test"). The time sentence
   is covered by `test_time_reply.py` in the regression.
8. **Windows Update in the VM** is still paused until 2026-11-06 05:27 UTC (16:27 your time). Run the check before
   then, or re-pause it yourself first.

Unchanged from the plans: no checkpoints P0-P5; the Gate 17 cleanliness check is not repeated; not tested in the VM:
an AI conversation (no keys in the VM), a real microphone, install under a non-administrator account, and none of the
parts that need a provider, Ollama, another device, a backup drive or a private network. Stop rules: any failed step
stops everything and nothing is repeated without your decision; a UAC prompt is a STOP; 15 minutes without progress
(the half-minute lines count as progress): tell Hermes before any reset; every VM start goes through the launcher;
VirtualBox only in jarvis-s6-val.

## What Hermes does on your approval

1. Records it in `../governance/STAGE7-1.0.19-APPROVAL-RECORD.json` with this plan's hash and the tool hashes below.
2. Creates `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.19\` with the five version 4 host files (the four launcher scripts and
   the disc builder), `Start-FreshVm.ps1`, `Take-FreshVmSnapshot.ps1` and `stage7-authorized.json` (schema
   `jarvis-stage7-authorized-v4`; final 1.0.19-629bb5621d34, previous 1.0.17-0d38218c4e1d, label 1.0.19-629bb5621d34,
   expected current snapshot STAGE7-PASS-1.0.17-0d38218c4e1d), each copy hash-checked.
3. Creates the two record folders named above (nothing else on D: changes).

Tool hashes (sha256, read on 2026-10-13 at commit 629bb56; equal to the table you approved for 1.0.17 and 1.0.18):

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

Reply in your own words that you approve this check, for example: "I approve the Stage 7 check of 1.0.19".
