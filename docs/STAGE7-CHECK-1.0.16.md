# Stage 7 check of 1.0.16 (plan for your approval)

Status: **READY FOR YOUR APPROVAL (2026-10-06, Claude Code). Rehearsed on this PC in a sandbox: all steps passed;
nothing has run in the VM.** Approving it lets Claude place the tools and create this check's record folders; every
VirtualBox step stays yours, as for 1.0.11, 1.0.14 and 1.0.15.

## What it is

The standard check every release passes before it reaches your everyday JARVIS (your Stage 7 decision of
2026-10-04), now for **1.0.16-fccde24e2cc6** ("the phone release", step 4 of the approved `docs/PHONE-PLAN.md`)
against **1.0.15-63362929d7ad** (your everyday JARVIS). The same pass as the approved `docs/STAGE7-PLAN.md`, in the
same VM: install, first launch, Windows restart with automatic start, uninstall, reinstall, 1.0.15 installed and
updated to 1.0.16 while running, rollback, update again, and an update killed mid-copy then run again, with test data
kept throughout. Updating your everyday JARVIS afterwards is a separate decision of yours (step 5 of the phone plan).

## The build

- **1.0.16-fccde24e2cc6** (commit fccde24): zip `D:\JARVIS-release-work\release\JARVIS-1.0.16-fccde24e2cc6.zip`,
  525,906,502 bytes, sha256 `58bba7423cf0668ff7684e9370865b9951e473eb1e0818c9437bf4287032d23a`.
- What is new since 1.0.15: everything in `release-notes.json` for 1.0.16, `docs/PHONE-CORE-1.0.16.md` and
  `docs/MUSIC.md`: the Private network switch in Settings > Devices (off until you turn it on; with it on and
  Tailscale running, a second door for paired devices only at this PC's Tailscale address); pairing limits per
  caller; device routes for a device's own conversations, the PC's health, an overview and a waiting events route;
  the per-device tick "May save memories and tasks"; and music from your own files (Settings > Music, "Jarvis, play
  <nickname>", the tool "Play music from your files" with its own permission switch; the emergency stop stops the
  music too).
- Previous build: **1.0.15-63362929d7ad** from its existing Stage 7 disc `JARVIS-STAGE7-1.0.15-63362929d7ad.iso`
  (sha256 `7ec1976380739a24f828794efbdd7c200a32e2fcb7360e71581461883ef846fb`, 527,106,048 bytes, in
  `D:\JARVIS-S6-FRESHVM\media`), which carries that build's zip and record at its root. 1.0.15 never had a package
  disc of its own; no new disc for it.

## Already done on this PC

Records: `docs/release-rehearsal-20261006-1016/README.md`.

- Compared with 1.0.15: the same pinned parts (Python, its packages, Electron, the models, the Windows runtime
  files); of the shipped source 14 files changed, 4 added and 0 removed,
  exactly the work since 1.0.15; the rest is compiled bytecode and the 29 pip launcher files that record
  the build folder.
- Release regression with the release's own Python and Electron: all pass (664 Python, 52
  desktop, 18 Intelligence, 24 interface scripts).
- Zip install in a sandbox: installed in 70 s, launched (8 processes, Core answering),
  verified, then uninstalled while running: all 10,675 program files removed, data kept, nothing left running.
- The whole Stage 7 pass 1.0.15 -> 1.0.16 in a sandbox with the version 3 scripts: **ALL STAGE 7 STEPS PASSED**
  (2026-10-06, 16 minutes): install; the restart check asking for the restart when there was none, and
  seeing one when told of one; after-restart; uninstall (all 10,675 program files removed, data kept) and
  reinstall; update while running (134 s, with the disk busy with a 40 GB folder move of the owner's at the time; the Core ready 19.7 s after the switch), rollback to 1.0.15 (11.6 s), update
  again (36 s); and the interrupted update (killed with 3,351 of 10,675 files copied; 1.0.15
  untouched and running; the rerun 32.6 s).
- The version 3 tools are byte-identical to the ones approved and used for 1.0.15 (hashes below); their decision
  tests run again today: the launcher 18 cases, the guest driver 21 cases, all pass.

## Your steps (about 90 minutes, mostly waiting; the same as for 1.0.15, with two notes)

One launcher on the PC, `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.16\stage7-step.cmd` (a new folder; the 1.0.11,
1.0.14 and 1.0.15 tools stay as they are), and one file inside the VM, `stage7` on this check's disc (drive E:).

| # | Where | What you do | What happens |
|---|---|---|---|
| 1 | PC, jonny | double-click `stage7-step` | builds the Stage 7 disc (a few minutes); tell Claude "disc built" |
| 2 | PC, jarvis-s6-val | double-click `stage7-step` and **leave its window open until it closes by itself** | restores the clean snapshot, attaches the two discs, starts the VM. **Note 1:** the VM's power-on can take two to three minutes while the window says "Waiting for VM to power on". Do not close the window and do not start the launcher a second time during that wait: a second start then prints a STOPPED message that is wrong (the 1.0.15 check, incident 01). Wait for the VM window. |
| 3 | inside the VM | sign in (`jarvis-s6-guest` / `fresh-vm-2026`), open **drive E:**, check that the zip on it says **1.0.16**, double-click `stage7` | installs 1.0.16 and tests it (about 25 minutes). **Note 2:** both discs are named `JARVIS_S7`. Drive D: is the 1.0.15 disc (the previous build), drive E: is this check's disc. |
| 4 | inside the VM | quit JARVIS from its icon near the clock, **Start > Power > Restart**, sign in, wait a minute, open drive E: again, double-click `stage7` again | restart check; uninstall and reinstall; update, rollback, update again; the interrupted update (about 50 minutes). It does not matter how long after the restart you start it. |
| 5 | inside the VM | when it says ALL STAGE 7 STEPS PASSED: Start > Power > Shut down | |
| 6 | PC, jarvis-s6-val | double-click `stage7-step` | takes the snapshot `STAGE7-PASS-1.0.16-fccde24e2cc6` |
| 7 | this chat | say "stage 7 done" | Claude checks every record and gives the result |

## What is checked

Exactly as in `docs/STAGE7-PLAN.md` ("What is checked"): install, first launch, version, a memory saved, second
launch joins, offline speech recognition, stop and start; JARVIS back by itself after the restart; uninstall and
reinstall with data kept; update, rollback, update again with both memories; the interrupted update. All met:
`STAGE_7_COMPLETE` for 1.0.16; anything not met: `STAGE_7_INCOMPLETE` with the exact step.

**Timing bound (your decision of 2026-10-06, "accept the VM time"):** the Gate 20 bound applies to this check as to
every Stage 7 check: install, update and rollback each within 600 s, stopping JARVIS within 120 s. A measurement
outside the bound is accepted as a disposition only when this check's own records show the cause to be the VM (as
the 675 s first install of the 1.0.15 check did: the same files verified three times faster later in the same pass
and the install took 28 s on this PC); otherwise the step is repeated before acceptance, and only on your decision,
as nothing is repeated without it. The verdict on what is tested does not depend on the timings.

## Differences from the check of 1.0.15 (`docs/STAGE7-CHECK-1.0.15.md`)

1. **Builds:** 1.0.16 under acceptance, 1.0.15 as the previous build, from 1.0.15's own Stage 7 disc (see "The
   build"). The VM start script accepts a previous build's Stage 7 disc when it has no package disc (as for 1.0.14
   in the 1.0.15 check).
2. **Scripts unchanged:** the version 3 scripts (`tools/guest/stage7-v3/`, `tools/host/stage7-v3/`;
   `docs/STAGE7-DRIVER-V3.md`) exactly as approved and used for 1.0.15, byte for byte (hashes below). No version 4.
   The two follow-ups the 1.0.15 check recorded for the launcher are met by this plan's two notes instead of a tool
   change: the launcher's wrong STOPPED message during a slow power-on (incident 01 of 1.0.15) is avoided by leaving
   its window open and not starting it twice; the two discs with the same name `JARVIS_S7` are told apart by drive
   letter (E: is this check's disc, D: the previous build's).
3. **Start point:** the VM is on the snapshot `STAGE7-PASS-1.0.15-63362929d7ad` (uuid
   `f1add04d-3281-4894-8ccf-baa302755260`; checked from its settings file on 2026-10-06: currentStateModified false,
   last state change 2026-10-06T01:43:48Z, no change recorded since that snapshot). The launcher restores FRESH-PREREQ
   only if the VM is on that snapshot (or already on FRESH-PREREQ) and VirtualBox records no change since; otherwise
   it stops and restores nothing. Every snapshot is kept (seven now).
4. **Names:** the disc `JARVIS-STAGE7-1.0.16-fccde24e2cc6.iso` with `stage7-target.json`; the PC records
   `D:\JARVIS-stage7\1.0.16-fccde24e2cc6\evidence`; the VM records
   `D:\JARVIS-S6-FRESHVM\evidence\guest-egress-01\stage7-1.0.16-fccde24e2cc6`; the final snapshot
   `STAGE7-PASS-1.0.16-fccde24e2cc6`.
5. **Timing bound:** stated above with the disposition rule from your decision of 2026-10-06; the 1.0.15 plan had no
   such paragraph (the bound's application to Stage 7 was decided after that check).
6. **Expected sights:** the 1.0.15 window closes quietly on the update. After the rollback to 1.0.15 inside the VM,
   the 1.0.15 program runs on data written by 1.0.16: the new music table and the devices table's new column are
   left alone, and 1.0.15 knows neither the Private network switch, the device tick nor the music commands (this is
   what the rollback step checks, with both memories; it passed in the sandbox).
7. **Not tested in the VM, new with 1.0.16:** the private-network door (no Tailscale in the VM; the switch stays off,
   as it is off by default), a paired device (no phone), and music through the VM's speakers (the VM has no audio
   device; the music parts were tested on this PC with a generated tone and in the test suites).
8. **Windows Update in the VM** is still paused until 2026-11-06 05:27 UTC (16:27 your time). Run the check before
   then, or re-pause it yourself first.

Unchanged from the plans: no checkpoints P0-P5; the Gate 17 cleanliness check is not repeated; not tested in the VM:
an AI conversation (no keys in the VM), a real microphone, install under a non-administrator account, and none of the
1.0.15 or 1.0.16 parts that need a provider, Ollama, another device, a backup drive or a private network. Stop rules:
any failed step stops everything and nothing is repeated without your decision; a UAC prompt is a STOP; 15 minutes
without progress: tell Claude before any reset; every VM start goes through the launcher; VirtualBox only in
jarvis-s6-val.

## What Claude does on your approval

1. Records it in `../governance/STAGE7-1.0.16-APPROVAL-RECORD.json` with this plan's hash and the tool hashes below.
2. Creates `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.16\` with the four version 3 host files, `Start-FreshVm.ps1`,
   `Take-FreshVmSnapshot.ps1` and `stage7-authorized.json` (schema `jarvis-stage7-authorized-v3`; final
   1.0.16-fccde24e2cc6, previous 1.0.15-63362929d7ad, label 1.0.16-fccde24e2cc6, expected current snapshot
   STAGE7-PASS-1.0.15-63362929d7ad), each copy hash-checked.
3. Creates the two record folders named above (nothing else on D: changes).

Tool hashes (sha256, unchanged since the 1.0.15 approval; read again on 2026-10-06 at the commit that records the
checks on this PC):

| File | sha256 |
|---|---|
| tools/guest/stage7-v3/Invoke-Stage7Pass.ps1 | `a9dce034e045712967073a4c891e153a4dc056ee60f3b1524fc36c504f2f0ff7` |
| tools/guest/stage7-v3/Invoke-Stage7.ps1 | `18fdc2380f6d37f033d106c6ff6d574ff377d5a2385be1ac8358d528119dd832` |
| tools/guest/stage7-v3/stage7.cmd | `7b992f854b9c35fd501880baf8cb6fb6a67ae0ba092639585c23cac7d290fd5a` |
| tools/host/stage7-v3/Invoke-Stage7Step.ps1 | `25f636f52c6823d1aba8ad79617967aec46b4013b8f20b2615581c886765b7e9` |
| tools/host/stage7-v3/New-Stage7Disc.ps1 | `2128827d54d979aa25cb760f25c46fbe2e4075636fa9a69af792100255a6df98` |
| tools/host/stage7-v3/Start-Stage7Vm.ps1 | `71bec341feaf332d332905ae622a02fc2befc1427db27f89bda3a39a0d60f15d` |
| tools/host/stage7-v3/stage7-step.cmd | `c10f0b213a37635b547ae8e1ac6766e5ec3ee422829d91928e8217430cac7a34` |
| tools/host/Start-FreshVm.ps1 | `d456da091c335e74c2f057068409cb5fe1a44ef3dcc156d780a83f16868a59a2` |
| tools/host/Take-FreshVmSnapshot.ps1 | `f4065b26a4abecf0bc71e6b219ee423832775ce822bde3588a764608bca3cad8` |
| tools/New-PackageIso.ps1 | `16df7178a9dea5a84829c225f76f421e379e86d3bc1c5c695cf1ab81f7b9ce60` |

## Approval

Reply in your own words that you approve this check, for example: "I approve the Stage 7 check of 1.0.16".
