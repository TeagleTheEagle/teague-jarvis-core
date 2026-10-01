# Gates 17–20 execution prompt: DRAFT for owner approval (after Gate 16R passes)

Status: **DRAFT 2026-10-01 (Claude Code), not approved.** To be approved only after
`FRESH_VM_QUALIFICATION_PASS` and the owner's FINAL selection. It issues no token: Gate 17
follows 16R under the already-issued `RESUME_STAGE6_FRESH_VM`; Gate 18 needs the owner's
separate `RESUME_STAGE6_RECOVERY` at OWNER STOP #2. Governing text: AMENDMENT-v2 §9,
runbook V1 Gates 17–20 and the STAGE 6 COMPLETE RULE, AMENDMENT-v3 (D5–D9).

## In plain words

Gate 17 installs the FINAL JARVIS build in the fresh VM and proves it works there with
nothing else installed. Gate 18 proves your backup restores there. Gate 19 checks the
update/rollback evidence against the FINAL build. Gate 20 is the final review and the
STAGE_6_COMPLETE / INCOMPLETE verdict. Even if complete, nothing changes on your everyday
JARVIS: cutover and Stage 7 are later owner decisions. About one day of your time.

## Owner act first: FINAL selection

Reply naming the FINAL build (proposed: `1.0.11-60d406fb6398`, which passed the full
regression, the zip-install, Gate 18 and Gate 17 rehearsals on 2026-10-01). Claude then
records it, builds `JARVIS-PACKAGE.iso` (the zip, its release record, `install.cmd`
instructions, the tools disc contents) with `New-PackageIso.ps1`, and records every hash.

## Gate 17: clean Windows deployment / functional acceptance (owner in the VM; Claude verifies)

Start from snapshot FRESH-PREREQ. Attach `JARVIS-PACKAGE.iso`; mount the egress folder.

17.1 `Invoke-Gate17.ps1 -Phase Install -Package <disc> -Evidence <egress>` (shortcuts ON this
     time): package identity against the disc manifest and release record; extract;
     `install.cmd` to `%LOCALAPPDATA%\JARVIS`; verify; Desktop and Startup shortcuts present;
     launch via the Desktop shortcut; runtime identity (`installed_release` equals the
     package); memory saved in the canonical data folder; no process image outside the
     install; duplicate-Core fencing; offline speech with the bundled model; stop, verify
     after use, restart. Any FAIL: STOP (`OWNER_APPROVAL_REQUIRED_UAC` if a UAC prompt
     appeared; otherwise owner decision).
17.2 Owner: quit JARVIS from the tray ("Quit JARVIS completely"); confirm 0 JARVIS processes
     (`Invoke-Gate17.ps1` records this in the next phase); restart Windows.
17.3 After sign-in: `-Phase AfterRestart`: JARVIS started by the Startup shortcut, Core
     reachable, memory and identity intact.
17.4 Cleanliness after install (v3 D1): re-run `-Phase Baseline` with JARVIS installed and
     expect the same negative results except the JARVIS install itself (no Python, Node,
     Git or build tools appeared; PATH unchanged). This is the "absence of hidden
     development-machine dependency" evidence.
17.5 `-Phase Uninstall`: uninstall (program files removed, shortcuts gone, data and config
     kept, 0 processes), reinstall from the extracted package with memory restored and files
     verified, final stop.
17.6 Claude checks the egress evidence against the Gate 17 list (prerequisites: none needed,
     shown by 17.4; install/bootstrap; runtime identity; authentication: the Core's
     per-session token and cookie, exercised by every API call; canonical data; Core startup;
     required UI/local commands: the API surface used by the desktop; voice/STT; restart;
     version identity; duplicate-Core fencing; no hidden dependency). All met:
     `CLEAN_WINDOWS_DEPLOYMENT_PASS`.
17.7 Snapshot `GATE17-PASS`. **P3 checkpoint** (Claude, owner's "run P3").

## OWNER STOP #2: `RESUME_STAGE6_RECOVERY`

Claude presents the exact recovery procedure below and waits for the token.

## Gate 18: backup / restore / recovery (owner; Claude verifies)

v3 D8: the owner's real verified backup. Before the token, the owner copies the backup zip
from E: to `D:\JARVIS-S6-FRESHVM\media\` (read-only copy; E: never written); Claude records
its SHA-256 (backup identity) and includes it on `JARVIS-RECOVERY.iso`.

18.1 In the VM (JARVIS from 17.5 installed, stopped): install a second disposable target
     with `installer.py install --home %LOCALAPPDATA%\JARVIS-restore --no-shortcuts`.
18.2 `switch_over.py --archive <backup on disc>` dry run, then `--apply --include-personal-config`
     into the restore target's data folder (the shipped command finds its own data and
     config folders; nothing else is touched).
18.3 Launch the restore target (`JARVIS-restore\JARVIS.ps1`): startup; database integrity and
     counts equal the backup manifest; configuration (personality, preferences) restored into
     `config\`; version identity; no duplicate Core (the first install stays stopped; a
     second launch joins the running Core); clean shutdown from the tray.
18.4 Rollback readiness: `installer.py status` and `verify` on both installs; the first
     install's data untouched by the restore.
18.5 Backup source unchanged: SHA-256 of the backup on E: (owner, read-only) and of the disc
     copy equal the recorded value. Protected original: **P4 checkpoint**.
18.6 All met: `BACKUP_RESTORE_RECOVERY_PASS`. The VM is now personal-data-bearing: its storage
     stays under `D:\JARVIS-S6-FRESHVM\`; disposal is the Gate 20 owner decision.

## Gate 19: update / interruption / rollback reconciliation (Claude; owner confirms)

Classify the 2026-10-01 local evidence (`docs/release-rehearsal-20261001/`) against FINAL:
- Interrupted update at each step (unit level) and the real kill-mid-copy run: installer
  code unchanged since 1.0.8 except timing output → STILL_APPLICABLE.
- Lifecycle A→B→A (1.0.4→1.0.6, 1.0.8→1.0.11 in Gate 18 rehearsal): REQUIRES_RERUN on the
  VM for the FINAL build: update from the previous build to FINAL inside the VM
  (`installer.py install` from a second package disc), verify, rollback, verify; per-phase
  seconds recorded (v3 D9: the bound is set from these measurements).
- Historical 09-17 timing FAIL: preserved, not re-graded.
Require: correct version identity, intact data/config, no mixed installation, no stale
processes, interruption recovery, rollback integrity, package provenance. All met:
`UPDATE_ROLLBACK_RECONCILED`.

## Gate 20: final review (Claude drafts; owner decides)

Requirement-by-requirement table with one of PASS / APPROVED_DISPOSITION / FAIL /
NOT_APPLICABLE_WITH_EVIDENCE for every V1 Gate 20 item, citing the record for each
(v2 §4 dispositions, v3 A1–A5, 16R evidence, P0–P5, Gates 17–19). **P5 checkpoint** (same
VirtualBox version as P0). No item may be missing. Verdict: `STAGE_6_COMPLETE` only if the
COMPLETE RULE holds (every mandatory gate PASS or owner-dispositioned; identities bound;
preservation PASS; protected original unchanged; deployment, recovery and rollback
readiness PASS; zero mandatory unresolved items); otherwise `STAGE_6_INCOMPLETE` with the
exact blocker. Then STOP: `PRODUCTION_CUTOVER_NOT_AUTHORIZED`, `STAGE_7_NOT_STARTED`.

## Not authorised by this prompt

Production cutover; Stage 7; any change to the everyday JARVIS; provider credentials in the
VM; any VirtualBox operation under the owner account; Experiment 5.
