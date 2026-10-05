# Stage 7 check scripts, version 3 (for every check after 1.0.14)

Written 2026-10-06. The check of 1.0.14 in the test VM passed, but its guest driver (version 2) stopped twice for
reasons that were defects of the driver, not of JARVIS. Both are recorded in `docs/stage7-1.0.14-evidence/`
(`incident-01-z-drive.json`, `incident-02-restart-check.json`), each with "fix in version 3". This is version 3.
The version 2 files stay unchanged: a disc carries them and they are evidence.

Nothing here has run in the VM. VirtualBox, the VM and every check in it remain the owner's to start.

## 1. What changed

Only the guest driver, `tools/guest/stage7-v3/Invoke-Stage7Pass.ps1` (the script `stage7.cmd` starts in the VM):

1. **The egress drive need not be connected yet (incident 01).** Version 2 built the path of its evidence folder on
   `Z:` with `Join-Path` before it connected `Z:`; PowerShell 5.1 refuses a drive that does not exist, so the first
   double-click ended with an error and the owner had to connect `Z:` by hand before every start. Version 3 puts the
   path together as text and then connects the drive, as version 1 did.
2. **A restart of Windows is recognised however late stage7 is started after it (incident 02).** Versions 1 and 2
   compared running times: "Windows has been running for a shorter time now than when the install step finished".
   When the owner started stage7 77 minutes after the restart, and Windows had run only 38 minutes at the install
   step, the check said "not restarted". Version 3 asks Windows which start this is: its own count of starts
   (`BootId`) and the number of the newest "The operating system started" entry of the System log. Neither changes
   while Windows runs and neither depends on the clock. The record made when the install step passes is
   `stage7-install-boot.json` (it replaces `stage7-install-uptime.json`).
   - A count or a log number that moved: restarted. Both there and neither moved: not restarted, whatever the
     running time says (a paused VM or a clock jump can make it look shorter).
   - Only when Windows offers neither does the running time decide, as before, and the message then says within how
     many minutes of the restart stage7 must be started.
   - No record, or nothing at all to compare: the pass stops for a decision. Version 2 skipped the check silently
     when the record was missing; the restarted phase is now never run unchecked.
   - Every decision is written to the driver log with both sets of values.
3. Two switches for rehearsals and tests only, never for the VM: `-WhatNext` (say which phase would run next and
   stop before running it) and `-BootIdentityFile` (read "which start is this" from a file). Any rehearsal-only
   switch that is used is named in every line of the driver log, so a record shows it.

`tools/guest/stage7-v3/Invoke-Stage7.ps1` (the checks themselves) and `stage7.cmd` are the version 2 files (one
comment line added). `tools/host/stage7-v3/` holds copies of the four version 2 PC-side scripts that put the
version 3 guest scripts on the disc; the launcher accepts only a version 3 approval file
(`jarvis-stage7-authorized-v3`), so an approval for one launcher cannot drive the other.

## 2. Checked on this PC

`tools/host/stage7-v3/test-stage7-pass-v3.ps1`: 21 decision cases, all pass. No phase runs in them and nothing is
installed (fake disc and egress folders in `D:\JARVIS-release-work\scratch`, removed afterwards). The 8 cases of
version 2 (the target file, a wrong build, an unsafe folder name, and so on); the egress folder on a drive letter
this PC does not have (stops with the plain message, no `Join-Path` error); eleven restart decisions, among them
incident 02 itself (restarted, stage7 started 77 minutes later: seen), no restart with a longer and with a shorter
running time (not seen), only one of the two sources available, neither available, no record (stops); two with this
PC's real count of starts and real System log (the record of this very start: asks for the restart; the record of
an earlier start: seen); the log line that names a rehearsal switch.

The same incident 01 case put to the version 2 driver fails with its original error ("Join-Path : Cannot find
drive"), so the case does test the defect.

**One slip while doing that comparison, recorded as it happened:** the restart cases were also put to the version 2
driver. Version 2 does not know `-WhatNext`, ignores it (PowerShell hands unknown switches to a plain script without
complaint), and so started its AfterRestart check for real, with the scratch folder as the install folder. That
check only waits for a JARVIS in that folder (there is none; it gave up after four minutes), counts processes
started from that folder (none) and writes its result into the scratch evidence folder (a FAIL, deleted with the
folder). It starts and stops nothing and did not touch the installed JARVIS, its data or any other folder. The
tests now refuse to run against a driver without `-WhatNext`.

## 3. Not checked

- **The VM.** Nothing here ran inside it. Whether the VM's Windows offers `BootId` and a readable System log is
  not known (this PC, Windows 11, offers both); if it offers neither, version 3 falls back to the old rule and
  says so on screen.
- The line that writes `stage7-install-boot.json` runs only after a real install step. It is first exercised by
  the sandbox Stage 7 rehearsal of 1.0.15 on this PC, which should then also start the driver once without a
  restart (expected: "has not been restarted") before it continues.
- The PC-side copies in `tools/host/stage7-v3` differ from version 2 only in names and words; they are used for
  the first time when the owner approves the check of 1.0.15.
