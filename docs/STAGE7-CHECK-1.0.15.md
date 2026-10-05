# Stage 7 check of 1.0.15 (plan for your approval)

Status: **READY FOR YOUR APPROVAL (2026-10-06, Claude Code). Rehearsed on this PC in a sandbox: all steps passed;
nothing has run in the VM.** Approving it lets Claude place the tools and create this check's record folders; every
VirtualBox step stays yours, as for 1.0.11 and 1.0.14.

## What it is

The standard check every release passes before it reaches your everyday JARVIS (your Stage 7 decision of
2026-10-04), now for **1.0.15-63362929d7ad** against **1.0.14-e03872680e1d** (your everyday JARVIS). The same pass
as the approved `docs/STAGE7-PLAN.md`, in the same VM: install, first launch, Windows restart with automatic start,
uninstall, reinstall, 1.0.14 installed and updated to 1.0.15 while running, rollback, update again, and an update
killed mid-copy then run again, with test data kept throughout. Updating your everyday JARVIS afterwards is a
separate decision of yours.

## The build

- **1.0.15-63362929d7ad** (commit 6336292): zip `D:\JARVIS-release-work\release\JARVIS-1.0.15-63362929d7ad.zip`,
  525,847,763 bytes, sha256 `1019dce00702da4e15dac5ea8203a1a1034311fbbe30b352097517b16deec027`.
- What is new since 1.0.14: everything in `release-notes.json` for 1.0.15 and `docs/RELEASE-1.0.15-SCOPE.md`: the
  new look and the dashboard; OpenAI and Qwen only (Groq, Gemini and ElevenLabs removed); answer speed for Qwen;
  the backup provider; permissions in one place with an emergency stop that holds; devices with pairing and keys;
  speech recognition by the provider as a choice; automatic backups; answers without the internet; replies that
  appear while they are written (off by default); and the smaller fixes listed there.
- Previous build: **1.0.14-e03872680e1d** from its existing Stage 7 disc `JARVIS-STAGE7-1.0.14-e03872680e1d.iso`
  (sha256 `92b58b9a704856bb07302729a74bd903e4a1b54a17d47b9f55ce44a35752f6d7`), which carries that build's zip and
  record at its root. 1.0.14 never had a package disc of its own; no new disc for it.

## Already done on this PC

Records: `docs/release-rehearsal-20261006-1015/README.md`.

- Compared with 1.0.14: the same pinned parts (Python, its packages, Electron, the models, the Windows runtime
  files); of the shipped source 43 files changed, 19 added and 1 removed, exactly the work since 1.0.14; the rest
  is compiled bytecode and the 29 pip launcher files that record the build folder.
- Release regression with the release's own Python and Electron: all pass (634 Python, 52 desktop, 18 Intelligence,
  23 interface scripts). A first build of the same program files had failed one desktop test on a wait that was
  too short for an installed release; the wait was corrected and the release built again.
- Zip install in a sandbox: installed in 28 s, launched (8 processes, Core answering), verified, then uninstalled
  while running: all 10,669 program files removed, data kept, nothing left running.
- The whole Stage 7 pass 1.0.14 -> 1.0.15 in a sandbox with the version 3 scripts: **ALL STAGE 7 STEPS PASSED**
  (2026-10-06, 11.5 minutes): install; the restart check asking for the restart when there was none, and seeing
  one when told of one; after-restart; uninstall (all 10,669 program files removed, data kept) and reinstall;
  update while running (30 s, stopping JARVIS 1.2 s), rollback to 1.0.14 (9.6 s), update again (17 s); and the
  interrupted update (killed with 3,751 of 10,669 files copied; 1.0.14 untouched and running; the rerun 33 s). A
  first run of this rehearsal found a defect in the checks script (two runs in one folder, see difference 2) that
  was fixed and the rehearsal run again.
- The version 3 tools' decision tests: the launcher 18 cases, the guest driver 21 cases, all pass.

## Your steps (about 90 minutes, mostly waiting; the same as for 1.0.14)

One launcher on the PC, `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.15\stage7-step.cmd` (a new folder; the 1.0.11 and
1.0.14 tools stay as they are), and one file inside the VM, `stage7` on the disc named `JARVIS_S7`.

| # | Where | What you do | What happens |
|---|---|---|---|
| 1 | PC, jonny | double-click `stage7-step` | builds the Stage 7 disc (a few minutes); tell Claude "disc built" |
| 2 | PC, jarvis-s6-val | double-click `stage7-step` | restores the clean snapshot, attaches the two discs, starts the VM |
| 3 | inside the VM | sign in (`jarvis-s6-guest` / `fresh-vm-2026`), open the `JARVIS_S7` disc, double-click `stage7` | installs 1.0.15 and tests it (about 25 minutes). **New: Z: no longer needs connecting by hand first.** |
| 4 | inside the VM | quit JARVIS from its icon near the clock, **Start > Power > Restart**, sign in, wait a minute, double-click `stage7` again | restart check; uninstall and reinstall; update, rollback, update again; the interrupted update (about 50 minutes). **New: it does not matter how long after the restart you start it.** |
| 5 | inside the VM | when it says ALL STAGE 7 STEPS PASSED: Start > Power > Shut down | |
| 6 | PC, jarvis-s6-val | double-click `stage7-step` | takes the snapshot `STAGE7-PASS-1.0.15-63362929d7ad` |
| 7 | this chat | say "stage 7 done" | Claude checks every record and gives the result |

## What is checked

Exactly as in `docs/STAGE7-PLAN.md` ("What is checked"): install, first launch, version, a memory saved, second
launch joins, offline speech recognition, stop and start; JARVIS back by itself after the restart; uninstall and
reinstall with data kept; update, rollback, update again with both memories; the interrupted update. All met:
`STAGE_7_COMPLETE` for 1.0.15; anything not met: `STAGE_7_INCOMPLETE` with the exact step.

## Differences from the check of 1.0.14 (`docs/STAGE7-CHECK-1.0.14.md`)

1. **Builds:** 1.0.15 under acceptance, 1.0.14 as the previous build, from 1.0.14's own Stage 7 disc (see "The
   build"). The VM start script accepts a previous build's Stage 7 disc when it has no package disc.
2. **Version 3 scripts** (`tools/guest/stage7-v3/`, `tools/host/stage7-v3/`; `docs/STAGE7-DRIVER-V3.md`): the two
   stops of the 1.0.14 check are fixed. The driver no longer fails before connecting `Z:` (incident 01), and the
   restart check asks Windows which start this is instead of comparing running times (incident 02), so a restart is
   seen however late `stage7` is started after it, and no restart is never mistaken for one. Without a record of the
   install step's start, or if the VM's Windows offers nothing to compare, the pass stops for a decision instead of
   running the restarted phase unchecked. Every decision is written to the driver log. The checks script
   (`Invoke-Stage7.ps1`) has one change: a run never writes into another run's folder (found by this release's
   sandbox rehearsal; versions 1 and 2 had the defect without ever hitting it). The 1.0.14 scripts stay unchanged as
   evidence.
3. **Start point:** the VM is on the snapshot `STAGE7-PASS-1.0.14-e03872680e1d` (checked from its settings file on
   2026-10-06: no change recorded since the snapshot of 2026-10-05). The launcher restores FRESH-PREREQ only if the
   VM is on that snapshot (or already on FRESH-PREREQ) and VirtualBox records no change since; otherwise it stops and
   restores nothing. Every snapshot is kept.
4. **Names:** the disc `JARVIS-STAGE7-1.0.15-63362929d7ad.iso` with `stage7-target.json`; the PC records
   `D:\JARVIS-stage7\1.0.15-63362929d7ad\evidence`; the VM records
   `D:\JARVIS-S6-FRESHVM\evidence\guest-egress-01\stage7-1.0.15-63362929d7ad`; the final snapshot
   `STAGE7-PASS-1.0.15-63362929d7ad`.
5. **Expected sights:** the 1.0.14 window closes quietly on the update (1.0.14 already has the quiet stop). After the
   rollback to 1.0.14 inside the VM, the 1.0.14 program runs on data written by 1.0.15; the new tables it does not
   know are left alone (this is what the rollback step checks, with both memories; it passed in the sandbox).
6. **Windows Update in the VM** is paused until 2026-11-06 05:27 UTC (16:27 your time). Run the check before then,
   or re-pause it yourself first.

Unchanged from the plans: no checkpoints P0-P5; the Gate 17 cleanliness check is not repeated; not tested in the VM:
an AI conversation (no keys in the VM), a real microphone, install under a non-administrator account, and none of the
new 1.0.15 parts that need a provider, Ollama, another device or a backup drive. Stop rules: any failed step stops
everything and nothing is repeated without your decision; a UAC prompt is a STOP; 15 minutes without progress: tell
Claude before any reset; every VM start goes through the launcher; VirtualBox only in jarvis-s6-val.

## What Claude does on your approval

1. Records it in `../governance/STAGE7-1.0.15-APPROVAL-RECORD.json` with this plan's hash and the tool hashes below.
2. Creates `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.15\` with the four version 3 host files, `Start-FreshVm.ps1`,
   `Take-FreshVmSnapshot.ps1` and `stage7-authorized.json` (schema `jarvis-stage7-authorized-v3`; final
   1.0.15-63362929d7ad, previous 1.0.14-e03872680e1d, label 1.0.15-63362929d7ad, expected current snapshot
   STAGE7-PASS-1.0.14-e03872680e1d), each copy hash-checked.
3. Creates the two record folders named above (nothing else on D: changes).

Tool hashes (sha256, at the commit that records the checks on this PC):

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

Reply in your own words that you approve this check, for example: "I approve the Stage 7 check of 1.0.15".
