# Stage 7 plan: acceptance of the packaged JARVIS app

Status: **READY FOR YOUR APPROVAL (2026-10-04, Claude Code). Rehearsed in a sandbox; nothing has run in the VM.** You said "start stage 7"
and decided "A AND A" (`D:\JARVIS-stage7\evidence\owner-decision-01.json`): reuse the Stage 6 test VM from its
clean snapshot, and test the existing builds 1.0.10 -> 1.0.11.

## What Stage 7 proves

Your master document (section 10) defines it: **install, first launch, update from one version to the next,
recovery from an interrupted update, rollback, uninstall, reinstall, and your data surviving all of it**, with
hash-verified packages and kept evidence. Most of this passed once already inside Stage 6 (Gates 17 and 19).
Stage 7 runs it as one pass of its own and adds the one test never done in the VM: **an update killed while it
is copying, then run again.**

## The builds and the machine

- Build under acceptance: `1.0.11-60d406fb6398` (your everyday JARVIS since the switch-over). Previous build:
  `1.0.10-915e906516dc`. Both zips are checked against their hashes on the PC and again inside the VM.
- Machine: the test VM `JARVIS-S6-FRESH`, started from its clean snapshot `FRESH-PREREQ` (fresh Windows, no
  JARVIS, none of your data). Your snapshot with personal data (`GATE18-PASS`) is kept untouched; nothing of
  yours enters the VM in Stage 7. No AI keys enter the VM.

## Your steps (about 90 minutes, mostly waiting)

One launcher on the PC, `D:\JARVIS-S6-FRESHVM\tools\stage7-step.cmd`, and one file inside the VM, `stage7` on
the disc named `JARVIS_S7`. Each works out what is next, does it, and tells you what to do afterwards.

| # | Where | What you do | What happens |
|---|---|---|---|
| 1 | PC, jonny | double-click `stage7-step` | builds the Stage 7 disc (a few minutes); tell me "disc built" |
| 2 | PC, jarvis-s6-val | double-click `stage7-step` | restores the clean snapshot, attaches the two discs, starts the VM |
| 3 | inside the VM | sign in (`jarvis-s6-guest` / `fresh-vm-2026`), open the `JARVIS_S7` disc, double-click `stage7` | installs JARVIS and tests it (about 25 minutes; unpacking alone is about 15). Take one photo of the JARVIS window when it appears |
| 4 | inside the VM | quit JARVIS from its icon near the clock, **Start > Power > Restart**, sign in, wait a minute, double-click `stage7` again | checks JARVIS came back by itself; uninstall and reinstall; update, rollback, update again; then the interrupted update (about 50 minutes) |
| 5 | inside the VM | when it says ALL STAGE 7 STEPS PASSED: Start > Power > Shut down | |
| 6 | PC, jarvis-s6-val | double-click `stage7-step` | takes the snapshot `STAGE7-PASS` |
| 7 | this chat | say "stage 7 done" | I check every record and give the result |

## What is checked (each check writes a record)

- **Install:** package hash; install with `install.cmd` without administrator rights; files verified; Desktop and
  Startup shortcuts; first launch from the Desktop shortcut; version reported; a memory saved; second launch joins
  the running JARVIS; offline speech recognition; stop and start again with data intact.
- **After the Windows restart:** JARVIS started by itself and still has its data.
- **Uninstall and reinstall:** program and shortcuts removed, data kept; reinstall brings the data back.
- **Update, rollback, update:** previous build installed over the kept data, a second memory written; update while
  running; rollback; update again. Version, files, both memories and "nothing left running from the other
  version" checked each time; seconds per step recorded.
- **Interrupted update (new):** the previous build is installed fresh and running; the update is started and the
  installer is killed when about a third of the new files are copied. Then: the installed version is still the
  previous one and verifies; the running JARVIS still answers and has both memories; no half-installed new
  version is in place. The update is run again and must finish, verify, start with both memories, and stop.

All met: **`STAGE_7_COMPLETE`**. Anything not met: `STAGE_7_INCOMPLETE` with the exact step.

## Stop rules (as in Stage 6)

- A check that fails stops the pass. Nothing is repeated without your decision.
- A UAC or administrator prompt, on the PC or in the VM: click No, tell me "UAC". It is a STOP.
- No progress for 15 minutes: tell me before resetting anything.
- Every start of the VM goes through the launcher (network setting re-applied and proven).
- VirtualBox runs only in the jarvis-s6-val account, never in yours.

## Rehearsed, and not rehearsed

- **Rehearsed on this PC in a sandbox (2026-10-04, `docs/release-rehearsal-20261004/rehearse-stage7.ps1`):** the
  whole pass with the real 1.0.11 and 1.0.10 packages, sandbox folders and no shortcuts. All five phases PASS
  (13 minutes on this PC): Install (9 checks), the restart check refusing without a restart, AfterRestart,
  Uninstall and reinstall, Update (update, rollback, update again), and the interrupted update: installer
  killed after 3,726 of 10,645 files; the running 1.0.10 unharmed with both memories and still verified; no
  half-installed 1.0.11; the update run again finished in 33 s, verified, started with both memories, stopped
  cleanly. A first run stopped at the uninstall check because it looked at your real Desktop shortcut (which
  exists since the switch-over); fixed for rehearsal mode only, the VM check is unchanged. Your real JARVIS kept
  running untouched throughout. The PC-side launcher's decisions were tested in 16 situations.
- **Not rehearsable by me:** everything VirtualBox (restoring the snapshot is a new command for this route:
  `VBoxManage snapshot ... restore FRESH-PREREQ`; attaching discs and starting are the same as at Gate 17), the
  disc build, the Windows restart inside the VM, the Desktop and Startup shortcuts.

## Where this differs from Stage 6, and what you accept

1. **The VM is reused** although the Stage 6 rules called it "Stage 6 only" (your ruling of 2026-10-04).
2. **No preservation checkpoints P0 to P5.** Those belonged to Stage 6. Your old VM stays protected the same way
   as before (separate account, separate VirtualBox folder). If you want one extra check of the old VM after
   Stage 7, say so and I add it (on your typed go-ahead, like P5).
3. **The cleanliness check of Gate 17 is not repeated** (no Python, Node or Git on the machine): it was a Stage 6
   requirement and passed there.
4. **Scripts:** the Stage 7 scripts are copies of the Gate 17/19 scripts with the interrupted-update phase added
   and the restart check fixed (it now measures uptime, so the slow VM clock cannot fool it). The Stage 6
   originals are evidence and are not changed.
5. **Not tested in the VM, as in Stage 6:** an AI conversation (no keys in the VM), a real microphone (the VM has
   no audio device; speech recognition is checked offline), install under a non-administrator account. On your
   real PC the AI conversation and voice were confirmed by you at the switch-over.
6. **Known behaviour:** stopping JARVIS in the VM can take about 95 seconds; that is slow, not a failure, and is
   on the fix list (`docs/POST-CUTOVER-FIXES.md`).

## After Stage 7

The same disc method and script become the standard check for every new release before it is offered to your
everyday JARVIS, starting with 1.0.12 (the fixes collected so far).

## Approval

Reply in your own words that you approve this Stage 7 plan, for example: "I approve the Stage 7 plan".
I then record it, put the launcher in place with its hashes, and you start with step 1.
