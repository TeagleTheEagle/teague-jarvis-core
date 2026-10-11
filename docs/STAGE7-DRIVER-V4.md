# Stage 7 check scripts, version 4 (for 1.0.17 and every release that is its own app)

Written 2026-10-07 for release 1.0.17 (`docs/OWN-APP-PLAN.md` section 3.6: "Stage 7 version 4 scripts"). The version
3 files (`tools/guest/stage7-v3/`, `tools/host/stage7-v3/`, `docs/STAGE7-DRIVER-V3.md`) stay unchanged: discs and two
approvals carry them and they are evidence. Version 4 is a copy of version 3 with the install and the uninstall done
the way the owner does them from 1.0.17 on. Nothing here has run in the VM; VirtualBox, the VM and every check in it
remain the owner's to start.

## 1. What changed, and why

From 1.0.17 the release is one file, `JARVIS-Setup-<id>.exe` (Inno Setup; `tools/setup/`), which unpacks the package
into `%LOCALAPPDATA%\JARVIS-package` and runs the package's own `installer.py`, and the program is `JARVIS.exe` with
shortcuts straight at it. The check must prove that path, not only the zip and `install.cmd` it proved so far.

**The guest checks, `tools/guest/stage7-v4/Invoke-Stage7.ps1`** (the version 3 file with these changes; every other
step is byte for byte the same logic):

- **I1 package:** as before the zip against its release record and every disc file against the payload manifest;
  new, the Setup beside the zip against its own record (`JARVIS-Setup-<id>.setup.json`: hash, release id) and that
  record against the release record (the package manifest the Setup was built from must be the zip's).
- **I2 setup-install** (replaces I2 extract and I3 install): the Setup run silently (`/VERYSILENT /SUPPRESSMSGBOXES
  /NORESTART /LOG=<this run's folder>`). On the VM nothing else: the home and the package folder are the Setup's
  defaults, exactly as the owner's double-click. In a sandbox on this PC (another home or staging folder, no
  shortcuts) `/HOME`, `/DIR` and `/NOSHORTCUTS` are added, and the installer itself withholds the real shortcuts from
  any home that is not the PC's own install home. Checked: the Setup's exit code, the installer's answer in
  `<staging>\setup-result.json` (installed, this release), the package it unpacked (this release's manifest,
  `installer.py`, the uninstaller `unins000.exe`).
- **I3 installed-apps** (new): the entry under this account's registry hive says JARVIS, this version, Teague
  Industries, and its uninstaller is the one in the package folder.
- **I4 verify:** as before the installed files against the manifest and both shortcuts present (VM) or deliberately
  absent (sandbox); new, the release has its `JARVIS.exe`, and on the VM both shortcuts point straight at it.
- **Launch** (every launch in every phase): the Desktop shortcut when there is one; otherwise, new, the current
  release's own `JARVIS.exe` started with no arguments as a double-click would; an older release (the previous build
  in the update phases has no program file) still its `JARVIS.ps1`, which the installer writes for it.
- **U1 uninstall:** through the entry's own uninstaller, silently (it runs the package's installer with `uninstall`:
  program removed, data kept; then removes the package folder and the entry). Checked as before (no program file
  left, no process, data and config kept, shortcuts gone on the VM) plus: the entry was there before and is gone,
  the package folder is gone, `current.json` and the launcher script are gone.
- **U2 reinstall:** from the Setup again (the package unpacked again, the entry written again), then JARVIS back
  with its data, verified.
- **G7 update-through-setup** (new, after G6): back on the previous build (the package's rollback) and running with
  both memories, the Setup is run silently: it unpacks this package again and runs the package's installer, which
  updates while JARVIS runs. Checked like G4 and G6 (installed, this release over the previous one, nothing left
  running from the other release, verified, running with both memories, the final stop, current = this release) plus
  the entry present with this version. The machine ends on the build under acceptance, stopped, as after G6, so the
  Interrupt phase starts exactly as before.
- G1 to G6 and X0 to X3 (update, rollback, update again, the interrupted update) run on the package's installer
  exactly as in version 3; the Setup's log of each run goes into that run's record folder (`setup-<step>.log`).
- **From the review of 2026-10-07** (`docs/OWN-APP-1.0.17.md` section 7): while a Setup or the uninstaller runs,
  the driver says every half minute that it is still running and how many files the package folder holds (the
  unpack of 1.2 GB plus the installer's work can take a quarter of an hour in the VM, and the owner's rule is "15
  minutes without progress: tell Claude"); I2, U1, U2 and G7 require the installer's own word on the real shortcuts
  ("written" or "removed" on the VM, "withheld" in a sandbox) and, on the VM, that the Setup got no folder or
  shortcut switch; a sandbox run (another install home) looks for the entry "JARVIS (sandbox)" under the sandbox
  application id named in the Setup's record, never under the real JARVIS's; a missing Setup or uninstaller fails
  the step with a record; I4 also requires that no `JARVIS.ps1` was written for a release with its own program;
  G7 re-checks the shortcut targets; the Setup is hashed once.

Checks per pass: 29 (version 3: 27): E0 in each of the five phases, I1 to I8, R1, U1 to U3, G1 to G7, X0 to X3.

**The guest driver, `Invoke-Stage7Pass.ps1`:** the version 3 driver with its version number changed (every line of
the driver log says `driver 4`). The order of the phases is the same.

**The PC side, `tools/host/stage7-v4/`:** the launcher accepts only a version 4 approval file
(`jarvis-stage7-authorized-v4`; same fields as version 3), so an approval for one launcher cannot drive another;
`New-Stage7Disc.ps1` puts the Setup and its record on the disc beside the zip (checked against each other and the
release record first) with the version 4 guest scripts; and because zip and Setup together are about 930 MB, more
than the CD-sized image Windows' IMAPI2 makes by default (about 681 MB, which every earlier disc fitted), the disc is
built with a copy of the disc builder in that folder (`New-PackageIso.ps1`, one line added: a single-layer DVD,
`FreeMediaBlocks = 2295104`; the launcher folder placed on D: carries it as a seventh file, and when it is missing
there the repo's copy is used); the original `tools/New-PackageIso.ps1` is recorded by hash in the earlier approvals
and stays unchanged. `Start-Stage7Vm.ps1` is unchanged but for its version word: the previous build's disc is its own
Stage 7 disc (1.0.16's), as for the 1.0.15 and 1.0.16 checks.

## 2. Checked on this PC (2026-10-07)

- `tools/host/stage7-v4/test-stage7-step-v4.ps1`: the launcher's decision table in test mode against a fake tree
  (no VirtualBox): **19 cases pass** (the 18 of version 3 with a 1.0.17 name, 1.0.16 as the previous build and the
  1.0.11 and 1.0.16 records in the tree, plus one: a version 3 approval file is refused).
  Record `docs/release-rehearsal-20261007-1017/test-stage7-step-v4.output.json`.
- `tools/host/stage7-v4/test-stage7-pass-v4.ps1`: the guest driver's decisions against fake discs, no phase runs:
  **21 cases pass** (the version 3 cases: the target file, a wrong build, an unsafe folder name, the egress drive not
  connected yet, eleven restart decisions with this PC's real count of starts and System log among them, the
  rehearsal switch named in the log; every log line says driver 4).
  Record `docs/release-rehearsal-20261007-1017/test-stage7-pass-v4.output.json`.
- The DVD-sized disc builder built, mounted and read back a small test image (3 files) on this PC, so the added
  property is accepted; a disc of 930 MB is first built by the owner at the check (step 1 of the plan).
- The whole pass in a sandbox with the real 1.0.17 build and its Setup: `docs/release-rehearsal-20261007-1017/
  rehearse-stage7-release-v4.ps1` (the version 3 harness with the version 4 driver, the owner's real Desktop and
  Startup shortcuts recorded before, after every start of the driver and at the end and required unchanged, the
  Installed-apps entry required absent before, and a cleanup through the sandbox's own uninstaller at the end so no
  entry is left in the owner's registry). Its result is in `docs/release-rehearsal-20261007-1017/README.md`.

## 3. What a sandbox pass cannot show

The real shortcuts and the Startup launch (the sandbox withholds them); a real Windows restart (the restart check is
exercised with what Windows really says and with a file standing in for "one start later"); the Setup's own
defaults for the home and the package folder (the sandbox must override both); the disc. Those are what the VM
check proves.

## 4. Independent review

See `docs/OWN-APP-1.0.17.md` section 7: the version 4 scripts were reviewed together with item 3.4 (the Setup) by one
reviewer, findings applied.
