# Gates 17 to 20: execution plan in plain words (APPROVED)

Status: **APPROVED by the owner on 2026-10-04 in a direct chat message: "FINAL is 1.0.11 and I approve the Gates 17 to 20 plan".** Drafted by Claude Code the same day. It replaces the draft of 2026-10-01 and applies the
simplified acceptance you approved on 2026-10-02. Approving it issues no token. Gate 17 runs under the
`RESUME_STAGE6_FRESH_VM` you already issued; Gate 18 still needs your separate `RESUME_STAGE6_RECOVERY`.
Governing text: AMENDMENT-v2 section 9, runbook V1 Gates 17 to 20 and its COMPLETE RULE, AMENDMENT-v3 (D5 to D9).

## What this does

- **Gate 17** installs the FINAL JARVIS build in the fresh test VM and shows that it works there with nothing
  else installed.
- **Gate 19** (in the same VM sitting, right after Gate 17) shows that updating from the previous build, rolling
  back and updating again keep JARVIS and its data intact, and measures how long each takes.
- **Gate 18** shows that your real backup restores in the VM.
- **Gate 20** is the final review and the verdict `STAGE_6_COMPLETE` or `STAGE_6_INCOMPLETE`.

Nothing here changes your everyday JARVIS. Switching over to the new build and Stage 7 stay separate decisions.

## Your decisions before it starts

1. **FINAL selection.** Proposed: `1.0.11-60d406fb6398`. It is the only build that passed the full regression,
   the zip install, the backup/restore rehearsal and the Gate 17 rehearsal. The build before it, used for the
   update test, is `1.0.10-915e906516dc`.
2. **This plan.**

## How you run it

There is one launcher on the PC, `D:\JARVIS-S6-FRESHVM\tools\next-step.cmd`, and one file inside the VM, `gate`
on the package disc. Each works out what is next, does it, and tells you what to do afterwards. Neither skips
ahead, and neither repeats a step that failed.

| # | Where | What you do | What happens |
|---|---|---|---|
| 1 | PC, your account (jonny) | double-click `next-step` | builds the two package discs (a few minutes each) |
| 2 | PC, jarvis-s6-val | double-click `next-step` | checks and attaches both discs, starts the VM |
| 3 | inside the VM | sign in, open the `JARVIS_PKG` disc, double-click `gate` | installs JARVIS and tests it (about 10 minutes). Take one photo of the JARVIS window when it appears. |
| 4 | inside the VM | quit JARVIS from its icon near the clock, restart Windows, sign in, double-click `gate` again | checks JARVIS came back by itself, checks nothing else was installed, uninstalls and reinstalls, then runs the update and rollback test (about 20 minutes) |
| 5 | inside the VM | Start > Power > Shut down | |
| 6 | PC, jarvis-s6-val | double-click `next-step` | takes the snapshot `GATE17-19-PASS` |
| 7 | this chat | say "gate 17 done"; when I report, type `run P3` | I check every record; P3 confirms your old VM is untouched |

Records, not photographs: every step writes its results to the evidence folder and I read them there. You
photograph a window only when it says STOPPED, plus the one photo of the JARVIS window in step 3.

## What is checked

**Gate 17**, by the script on the disc, each check written as a record:

- the package on the disc is exactly the FINAL build (hashes against its release record);
- it installs with the same `install.cmd` a user would run, into your user folder, **without administrator
  rights**; the installed files verify; Desktop and Startup shortcuts exist;
- it starts from the Desktop shortcut; the running JARVIS reports the FINAL version; a memory is saved in the
  proper data folder; it runs with its own bundled Python and Electron from the install folder;
- starting it a second time joins the running JARVIS instead of starting another one;
- speech recognition works offline with the bundled model;
- it stops and starts again with its data and version intact;
- after the Windows restart it starts by itself and still has its data;
- with JARVIS installed, the cleanliness checks of the baseline are repeated: no Python, Node, Git or build
  tools appeared, the PATH is unchanged, nothing JARVIS-related exists outside its own folders, and the Windows
  build number is recorded again;
- uninstalling removes the program and shortcuts and keeps your data; reinstalling brings the data back.

All met: `CLEAN_WINDOWS_DEPLOYMENT_PASS`.

**Gate 19**, same script, same sitting:

- the previous build is installed over the kept data and a new memory is written;
- update to FINAL while JARVIS is running: version, files, data and both memories checked, no leftover
  programs, nothing running from the old version; the installer's seconds per phase are recorded;
- roll back to the previous build: the same checks;
- update again, so the VM ends on FINAL, stopped.

The interrupted-update tests (power cut at each step, and the real kill in the middle of copying) are **not**
repeated in the VM. They were run on this PC on 2026-10-01 and the installer has not changed since, so I
classify them STILL_APPLICABLE and cite them. The old timing failure of 2026-09-17 stays recorded as a failure.
All met: `UPDATE_ROLLBACK_RECONCILED`.

**Then:** snapshot `GATE17-19-PASS`, and checkpoint **P3** on your `run P3`.

## OWNER STOP #2, then Gate 18 (your real backup)

After P3 I stop. Before you issue `RESUME_STAGE6_RECOVERY` I give you the exact restore steps, already
rehearsed on this PC, to approve with the token. In outline, as you approved in AMENDMENT-v3 D8:

- you copy your backup from the backup drive `E:` yourself (read-only; `E:` is never written); its hash is
  recorded before and after;
- it goes into the VM on a read-only disc and is restored into a second, disposable JARVIS install;
- that install starts with your restored data, the counts match the backup, and your first install's data is
  untouched;
- checkpoint **P4** on your `run P4`. All met: `BACKUP_RESTORE_RECOVERY_PASS`.

From then on the VM holds personal data. It stays under `D:\JARVIS-S6-FRESHVM\`; keeping or destroying it is
your decision at Gate 20.

## Gate 20

I write a table with every Gate 20 requirement and one of PASS, APPROVED_DISPOSITION, FAIL or
NOT_APPLICABLE_WITH_EVIDENCE for each, citing its record. Checkpoint **P5** on your `run P5` (VirtualBox must
be the same version as at P0). The verdict is `STAGE_6_COMPLETE` only if nothing mandatory is open; otherwise
`STAGE_6_INCOMPLETE` with the exact blocker. Then I stop: no cutover, no Stage 7.

## Stop rules (unchanged)

- Any check that fails stops the gate. Nothing is repeated without your decision.
- A UAC or administrator prompt, on the PC or inside the VM: click No, tell me "UAC". It is a STOP.
- No progress for 15 minutes: reset the VM, start `gate rerun`; the rerun is recorded as a rerun.
- Every start of the VM goes through the launcher, which re-applies and proves the localhost setting.
- P3, P4 and P5 run only on your `run P3`, `run P4`, `run P5`.

## Where this plan differs from what you approved earlier

So that nothing is built differently from the words you approved, these are the differences. Approving this plan
approves them:

1. **Discs.** The 2026-10-02 text says the previous build comes "from a second package disc". It does, but both
   discs are attached before the VM starts: the previous build on drive port 1, **in place of the Windows
   installation disc**, and FINAL on port 2. The launcher attaches them with VirtualBox's command line in the
   jarvis-s6-val account, instead of you using the VM window's Devices menu.
2. **No separate tools disc.** The scripts travel on the FINAL package disc, and you double-click `gate` instead
   of typing a command.
3. **Snapshot name.** `GATE17-19-PASS` instead of `GATE17-PASS`, because Gate 19 is included.
4. **The VM's account is an administrator** (your decision of 2026-10-04). The script records that it runs
   without administrator rights and stops if it has them.
5. **What "the app works" covers.** The script exercises JARVIS through the same local interface the desktop
   window uses (read the state, save a memory, shut down) and you photograph the window once. No AI provider
   keys enter the VM (AMENDMENT-v3 D6), so an AI conversation is not part of this test.

## Not authorised by this plan

Switching your everyday JARVIS to the new build; Stage 7; any change to your everyday JARVIS; provider keys in
the VM; any VirtualBox operation under your own account; Experiment 5.

## Approval

Reply naming the FINAL build and approving this plan, for example: "FINAL is 1.0.11 and I approve the Gates 17
to 20 plan". I record both, and you start with step 1.
