# JARVIS: current status (living document)

**Read this first in every new Claude Code session, and update it at the end of each one.**
Last updated: 2026-10-04 (Gates 16R, 17 and 19 and P3 passed on FINAL 1.0.11; the owner issued RESUME_STAGE6_RECOVERY: Gate 18 in execution, waiting for the owner's backup copy).
Newest handover summary for a fresh session: `docs/HANDOVER-20261004-2.md` (the earlier
`HANDOVER-20261002.md` and `HANDOVER-20261004.md` are out of date).

Rules and authority are in `CLAUDE.md` and `../governance/OWNER-DELEGATION.md`; this file
only records where the work stands. Historical handover context: `docs/PROJECT-CONTEXT.md`.

## Where we are

- **Stage 6: INCOMPLETE.** Fresh-VM route active. **Gate pointer: GATE 18 in execution
  (since the owner's `RESUME_STAGE6_RECOVERY`, 2026-10-04, first clock reading 05:41:52Z).**
  Passed on FINAL 1.0.11: Gate 16R, Gate 17, Gate 19 and checkpoints P0 to P3. Not done:
  Gate 18, P4, Gate 20, P5. `RESUME_STAGE6_FRESH_VM` was issued 2026-10-02. Details under
  "Next steps".
  Earlier: P0 PASS (2026-09-30, sealed); owner created `jarvis-s6-val`. Experiment 5
  unconsumed, its budget frozen at 4/5 (that is the experiment budget, **not** a count of
  Stage 6 attempts). Stage 7 not started. Production cutover not authorized.
- **Owner chose option B and approved amendment v3 on 2026-10-01** ("i approve everything"):
  the two unprovable isolation cases are dispositioned with a stated limitation, D1–D9 are
  settled at their recommended selections, Claude Code is the executor. Record:
  `../governance/STAGE6-AMENDMENT-v3-RECORD.json` (text `STAGE6-AMENDMENT-v3.md`, sha256
  5f4d3b63…). (On that day the gate pointer was still OWNER STOP #1R and no token had been
  issued; see the first bullet for today's pointer.)
- **FINAL: 1.0.11-60d406fb6398, selected by the owner on 2026-10-04**
  (`../governance/STAGE6-FINAL-SELECTION-RECORD.json`; built from 60d406f; zip 525,622,280 bytes,
  SHA-256 `19236511…`, in `D:\JARVIS-release-work\release\`). Full regression (325/36/18/16),
  zip install, the Gate 18 backup/restore rehearsal and the local Gate 17 rehearsal **all
  pass on it** (`docs/release-rehearsal-20261001/README.md` section 6); Gates 17 and 19 then
  passed on it in the VM. 1.0.10 failed the Gate 18 rehearsal (backup
  blocked by the Core lock, fixed in 1.0.11); 1.0.9 exposed a config-location defect fixed
  in 1.0.10. Earlier fully rehearsed build, now superseded: **1.0.7-6c356bf982de**, with its
  distributable zip:
  `D:\JARVIS-release-work\release\JARVIS-1.0.7-6c356bf982de.zip`
  (525,590,739 bytes, SHA-256 `024c6166866a505700019d25f95e1e8f99dc34ab2f0fa011c81be6bbd4995396`).
  Full regression, zip install, lifecycle and interrupted-update evidence:
  `docs/release-rehearsal-20261001/README.md`.

## Approved direction (2026-10-02)

- **Roadmap** `docs/ROADMAP.md` and **simplified acceptance** `docs/stage6-freshvm/
  SIMPLIFIED-ACCEPTANCE-PROPOSAL.md`: both approved by the owner ("Both Approved"), record
  `../governance/STAGE6-SIMPLIFIED-ACCEPTANCE-RECORD.json`. Simplified acceptance applies from
  Gate 17 (records not photos, one command per gate, one next-step launcher, 15-minute hang
  rule, Gate 19 with Gate 17, batched decisions). Roadmap order: finish Stage 6 on the frozen
  build, cutover, lean Stage 7, codebase clean-up and provider pruning, automatic backups,
  device pairing and phone client, glasses. No source change until cutover.

## Next steps

Owner only (Claude must stop and ask, never infer or pre-stage tokens):

1. ~~Confirm the release design choices~~ **Done: approved by the owner 2026-10-01**
   (recorded in `docs/RELEASE-DESIGN.md`, "Owner decision").
2. ~~Choose A/B/C and settle D1–D9~~ **Done 2026-10-01 (option B, amendment v3).**
   ~~Approve the Gate 16R execution prompt~~ **Done 2026-10-02 ("approved"; record
   `../governance/STAGE6-GATE16R-PROMPT-APPROVAL.json`, frozen text sha256 922302aa…).**
   Step 0 of the prompt is complete: Windows 11 26H2 ISO downloaded with the owner's
   permission and hash-verified against Microsoft; answer-file and tools discs built with
   hashes (`D:\JARVIS-release-work\stage6-media\`); support scripts committed; evidence
   folder `D:\JARVIS-S6-FRESHVM\evidence\gate16r-20261002\` holds the step-0 records. Not
   done by Claude: the freeze/capacity check (declined twice in chat; D: free space recorded separately, 1610 GiB; the P0 checkpoint records the VirtualBox version, hash and process census itself).
   ~~The owner issues `RESUME_STAGE6_FRESH_VM`~~ **Issued 2026-10-02T01:15:45Z** (record
   `../governance/STAGE6-RESUME-FRESH-VM-RECORD.json`). **Gate pointer: GATE 16R in
   execution.** Step 1 **P0 PASS** (run `p0-20261002-012032`, 2026-10-02T01:20:32Z: 12 files /
   59,665,402,098 bytes, three control hashes equal the reference, VirtualBox 7.2.18.175117;
   an earlier run `p0-20261002-011703` stopped on a script defect after the reads and is
   kept). Step 2 **§7(b) PASS** (A3 applied; `VBOX_USER_HOME` set in step 4). Step 3
   **§7(e) PASS** (A1, A2 applied; run 2 of the check after a harness classification fix,
   run 1 kept; postflight PASS). Step 4 **§7(c),(d) PASS** (2026-10-02T02:43Z: `vbox-home`,
   `machines`, `media` created as new objects with the jarvis-s6-val Modify grant, four discs
   copied and hash-verified, `VBOX_USER_HOME` set user-scoped in the validation session and
   the account check re-run PASS). The first step-4a run was closed by accident mid-copy;
   Claude's byte comparison showed a partial copy, not corruption; the owner removed the three
   unfinished folders by hand and re-ran the unchanged script (`step4-run1-incident.json`).
   Step 5 **P1 PASS** (run `p1-20261002-025102`, 2026-10-02T02:51:02Z, on the owner's "run
   p1": 12 files / 59,665,402,098 bytes, control hashes, inventories and DACLs equal to P0,
   VirtualBox 7.2.18.175117 unchanged, empty process census). Step 6a done (owner created
   `evidence\guest-egress-01` with the validation account's Modify grant). Step 6 **VM
   created** (`JARVIS-S6-FRESH`, uuid 4ef16bdd…, 2026-10-02T03:41Z, validation session,
   registered only in `vbox-home`; verified against the spec from the `.vbox` and
   `VirtualBox.xml`; audio adapter corrected at 6b, 03:52Z; never started). **Step 6 PASS**
   with a recorded deviation: VirtualBox 7.2.18 does not persist NAT `localhost-reachable=off`
   (saved as the empty default, read back as on; proven by the before/after `.vbox` diff).
   Owner chose option 1 (2026-10-02T04:12Z, `step6-owner-decision-nat.json`): every start of
   the VM goes through `step7-start-vm.cmd` / `Start-FreshVm.ps1`, which re-applies "off" and
   records the running VM's `VBox.log` value; no host UAC prompt occurred. Step 7
   **PASS** (Windows 11 Home 26H2 build 26300.9457 from the answer file on the second
   attempt, local account `jarvis-s6-guest`, Guest Additions 7.2.18, Windows Update paused
   until 2026-11-06, egress mounted by hand non-persistent; boot list reset and disc prompt
   answered from the host, all recorded). Step 8 **PASS** (2026-10-04; baseline record =
   run 5 `guest-egress-01\gate17-20261004-022130`, tools disc v4, full §6(f) list; runs 1 and 3
   were harness false positives, kept; owner approved two dispositions: the two
   Windows-generated credential entries, and LocalhostReachable proven from VBox.log
   instead of the `.vbox`). Step 9 **PASS** (2026-10-04T02:40:17Z: snapshot
   `FRESH-CLEAN-BASELINE`, uuid 0da943df-12e5-4eac-93bf-727c03dd5d94, taken by the owner with
   the VM powered off and not started since baseline run 5; `.vbox` sha256 8647a9ec… after
   the snapshot; manifest `FRESH-CLEAN-BASELINE-manifest.json` written by
   `tools/host/snapshot_manifest.py`; `step9-evaluation.json`). The saved settings still
   hold NAT localhost-reachable "true" (the known defect), so every start after restoring a
   snapshot also goes through `step7-start-vm.cmd`. Step 10 **P2 PASS** (run
   `p2-20261004-030308`, 2026-10-04T03:03:08Z, on the owner's "RUN P2": inventories, control
   hashes and DACLs byte-identical to P1, VirtualBox 7.2.18.175117 unchanged, empty process
   census; `step10-evaluation.json`). Step 11 **PASS** (2026-10-04T03:04:55Z: snapshot
   `FRESH-PREREQ`, uuid 9f1d7bec-e410-4ed0-bc2f-4966125329ad, child of FRESH-CLEAN-BASELINE,
   VM not started in between; `.vbox` sha256 03ce709e…; `FRESH-PREREQ-manifest.json`,
   `fresh-vm-identity.json` (section 6(i)), `step11-evaluation.json`). Step 12:
   **`FRESH_VM_QUALIFICATION_PASS`** (2026-10-04; `step12-evaluation.json`). Two wording
   differences found during the check were put to the owner (`step12-open-items.json`) and
   accepted as recorded ("I accept and approve all your recommendations";
   `step12-owner-dispositions.json`): (A) the guest account `jarvis-s6-guest` is in the
   guest's Administrators group where v3 D3 and the approved prompt say "standard"
   (**condition for Gate 17: install and run recorded as non-elevated; any UAC or
   administrator prompt is a STOP**; non-administrator install stays untested); (B)
   VirtualBox's default-machine-folder property left at its default. Evidence
   `MANIFEST.json`: 116 files, sha256 38d487a6… (`tools/host/evidence_manifest.py`; covers
   gate16r-20261002 and guest-egress-01, never the sealed `evidence\P0`). **Gate 16R is
   complete.** **FINAL = 1.0.11-60d406fb6398 and the Gates 17–20 plan APPROVED by the
   owner on 2026-10-04** ("FINAL is 1.0.11 and I approve the Gates 17 to 20 plan";
   `../governance/STAGE6-FINAL-SELECTION-RECORD.json`,
   `STAGE6-GATES17-20-PROMPT-APPROVAL.json`, approved text
   `STAGE6-GATES17-20-EXECUTION-PROMPT.md` sha256 b3fbade4…; previous build for Gate 19:
   1.0.10-915e906516dc). Tooling rehearsed (`docs/release-rehearsal-20261004/README.md`,
   which lists what could not be rehearsed: everything VirtualBox, the 526 MB disc build,
   the in-VM restart step) and installed in `D:\JARVIS-S6-FRESHVM\tools\` with
   `gate17-plan.json` (hashes appended to `evidence\gate17\prep-tools-hashes.txt`).
   **Gate 17: `CLEAN_WINDOWS_DEPLOYMENT_PASS`; Gate 19: `UPDATE_ROLLBACK_RECONCILED`**
   (2026-10-04; `evidence\gate17\gate17-evaluation.json`, `gate19-evaluation.json`; repo copy
   `docs/stage6-freshvm/gate17-evidence/`). Both discs built by the owner, VM started once
   (LocalhostReachable 0), all guest phases PASS (Install, AfterRestart, Cleanliness,
   Uninstall, Update), snapshot `GATE17-19-PASS` 3023e9a7-0f60-42ed-bac0-8b7f0ff06368 taken
   05:05:41Z. Recorded deviations: the owner reset the VM once before sign-in; the driver's
   restart check gave a false negative (guest clock about 3 min slow after boot), continued
   with `E:\gate -NoRestartCheck`; one Windows credential entry fewer than at the baseline.
   VM stop times were slow in the VM (about 95 s). **P3 PASS** (run
   `evidence\gate17\checkpoints\p3-20261004-051026`, 05:10:26Z, on the owner's "run P3":
   byte-identical to P2, VirtualBox unchanged, empty census; `p3-evaluation.json`).
   Manifests: `evidence\gate17\MANIFEST.json` (23 files, sha256 53ac88ff…) and
   `MANIFEST-guest-egress-01.json` (55 files, aa3e8a30…). P4 will reference the P3 folder.
   **Now at OWNER STOP #2.** Gate 18 tooling is written and rehearsed with a made-up
   backup (`docs/release-rehearsal-20261004/README.md`): `tools/guest/Invoke-Gate18.ps1` +
   `gate18.cmd` (checks K0–K9), `tools/host/New-Gate18RecoveryDisc.ps1`,
   `Start-Gate18Vm.ps1`, `Invoke-Gate18Step.ps1` + `gate18-step.cmd`. The exact steps for
   the owner are in `docs/stage6-freshvm/GATE18-STEPS.md`. **The owner issued
   `RESUME_STAGE6_RECOVERY` on 2026-10-04 (first clock reading 05:41:52Z; record
   `../governance/STAGE6-RESUME-RECOVERY-RECORD.json`). Gate 18 IN EXECUTION.** Steps 1 and 2
   below done 05:42–05:43Z (tools copied, `gate18-authorized.json`, hashes in
   `evidence\gate18\prep-tools-hashes.txt`; launcher dry run as jonny points to the owner's copy
   command). **Gate 18 STOPPED at the backup copy (incident 01, 05:46Z;
   `evidence\gate18\incident-01-backup-copy.json`, repo copy in `gate18-evidence/`):** the copy
   script's `.zip` filter is ignored by PowerShell 5.1 with `-LiteralPath` and it copied a 2 KB
   report file; and `E:\JARVIS-BACKUP` turned out to hold a file-by-file copy of the old project
   (newest 2026-09-17), not a JARVIS data backup. E: unchanged (hash before = after). Launcher
   suspended (`gate18-authorized.json` renamed `.SUSPENDED-incident-01.json`). **Owner decision
   required: where Gate 18's backup comes from** (options in the incident note). **Owner chose "A"
   (05:50Z, `owner-decision-01.json`):** a fresh backup made by the everyday JARVIS (Settings >
   Backups > Create verified backup + Test restore; saved by default in `...\outputs\jarvis-backups`,
   found read-only from baseline e6fc40b). Copy script v2 (`tools/host/Copy-BackupForGate18-v2.ps1`,
   tested on the synthetic rehearsal backup incl. six refusal cases) placed in the D: tools folder;
   incident run's record renamed `backup-copy-run1-incident01.json`; `GATE18-STEPS.md` step 2 changed
   to 2a/2b; `incident-01-addendum-1.json`. Launcher still suspended. **Incident 02 (06:11Z,
   `incident-02-everyday-jarvis-cannot-start.json`): the everyday JARVIS cannot start: its `.venv`
   is based on Codex's Python runtime (`C:\Users\jonny\.cache\codex-runtimes\...`), which no longer
   exists.** Rehearsed alternative: the old JARVIS's own `recovery.py create/rehearse` run with
   FINAL's Python; `Invoke-Gate18.ps1` on such an old-format backup K0–K9 PASS in a sandbox. New
   helper `tools/host/New-OldJarvisBackup.ps1` (makes, tests, records, then runs copy v2), placed on
   D:. **Next: owner approves the helper route; owner runs it; Claude checks the records and
   re-enables the launcher.** Repairing the everyday JARVIS is a separate owner decision.
   The plan on the token was:
   (1) writes `../governance/STAGE6-RESUME-RECOVERY-RECORD.json`; (2) copies
   `gate18-step.cmd`, `Invoke-Gate18Step.ps1`, `New-Gate18RecoveryDisc.ps1`,
   `Start-Gate18Vm.ps1` to `D:\JARVIS-S6-FRESHVM\tools\` and writes
   `gate18-authorized.json` there (hashes to `evidence\gate18\prep-tools-hashes.txt`);
   (3) gives the owner the copy command for the jonny account:
   `powershell -ExecutionPolicy Bypass -File D:\JARVIS-S6-FRESHVM\tools\Copy-BackupForGate18.ps1`
   (the owner runs it; no launcher for the E: copy, and Claude never touches E:);
   (4) then `gate18-step` in jonny (disc), in jarvis-s6-val (start), `gate18` in the VM,
   shut down, `gate18-step` (snapshot GATE18-PASS), evaluation, P4 on "run P4" (reference
   `evidence\gate17\checkpoints\p3-20261004-051026`), Gate 20 with P5. Do not edit
   `tools/guest/Invoke-Gate18.ps1` after the recovery disc is built. Before reuse, fix `Invoke-Gate.ps1`'s restart
   check (use uptime, not wall-clock) on a NEW disc; the discs already built are evidence.
   A cutover blueprint draft exists (`docs/CUTOVER-BLUEPRINT.md`; not approved).
   P3 will reference `checkpoints\p2-20261004-030308`. Every VM start, including after
   restoring `FRESH-PREREQ`, goes through `step7-start-vm.cmd`. The owner runs every
   launcher in `D:\JARVIS-S6-FRESHVM\tools\` (ACL/VirtualBox work is owner-only); Claude
   reads the JSON results from the evidence folder. Evidence:
   `D:\JARVIS-S6-FRESHVM\evidence\gate16r-20261002\`.
3. `RESUME_STAGE6_RECOVERY` before Gate 18 (**this is where the work stands**).
4. After Stage 6 passes: switching the everyday JARVIS over (cutover), then Stage 7. (FINAL
   selection is done: 1.0.11, 2026-10-04.)
   The owner's freeze from P0 still applies: keep VirtualBox closed under the owner account
   and do not install, upgrade or repair it until Gate 20.

Claude's local preparation (no approval needed) is listed in section 9 of that plan.

Not yet tested anywhere: Desktop and Startup shortcuts (all rehearsals used `--no-shortcuts`,
because creating them changes the owner's real Desktop/Startup folders). Check on the VM.

## What exists (built 2026-10-01)

- One shared background Core per data folder (`core_lock.py`); desktop app joins it.
- Providers: Qwen (Alibaba Cloud Model Studio) brain and cloned JARVIS voice; local voice
  (Whisper base.en, openWakeWord). Keys are owner-placed in `config\.env`, never read.
- `switch_over.py`: imports a verified backup's data into a new install (owner-run).
- Release: `runtime_paths.py` (data/config/models from `JARVIS_*` env vars),
  `tools/build_release.py` (pinned inputs, manifest of every file),
  `tools/installer.py` (per-user install, update, rollback, uninstall, verify; crash-safe),
  `tools/release_regression.py` (all suites against a built release with its own runtimes).
- Test totals on the packaged release: 316 Python, 34 desktop, 18 Intelligence, 16 JS scripts.

## This PC: disks and folders

- **C: is nearly full** (about 20 GB free). Build and rehearse on **D:**:
  `D:\JARVIS-release-work\` holds `release\` (builds 1.0.2 to 1.0.7), `regression-*`,
  `sandbox-home*` (test installs, synthetic data only) and `evidence\`.
- **E: (JARVIS BACK UP) is the backup drive. Never write to it.**
- `D:\C-drive-overflow\`: large files moved off C: on 2026-10-01 at the owner's request
  (Windows ISO, installers, `Documents\Codex\2026-09-12`); its README lists the original paths.
- The live JARVIS is not in `%LOCALAPPDATA%\JARVIS`; see `../governance/LIVE-INSTALLATION-MAP.md`.
  Never run `install.cmd` without `--home <sandbox>` until cutover is authorized.

## Commands

```powershell
.venv\Scripts\python.exe -m unittest                                    # dev Python suite
.venv\Scripts\python.exe tools\build_release.py --version X.Y.Z --out D:\JARVIS-release-work\release [--no-zip]
.venv\Scripts\python.exe tools\release_regression.py --package D:\JARVIS-release-work\release\JARVIS-<id> --work D:\JARVIS-release-work\regression-<version>
```

## Gotchas for Claude

- Bash heredocs and inline Python mangle backslashes (`\r`, `\b`, `\n` in Windows paths and
  strings). Use the Edit/Write tools for any text containing backslashes.
- Releases ship unchecked-hash bytecode: editing a `.py` inside a built or installed release
  has no effect unless its `__pycache__` file is removed. Debug in the repo instead.
- A test "fresh account" must use a realistic layout (profile, `AppData\Local`,
  `AppData\Roaming`, `AppData\Local\Temp`); one shared folder makes browsers refuse to start.
- Some docs use CRLF line endings; check before rewriting files with scripts.
- The packaged regression runs the test suite with `JARVIS_DATA_DIR/CONFIG_DIR/MODELS_DIR`
  set. Tests and tools must not assume the process environment describes the installation
  under test (use `runtime_paths.config_dir_for(root)`); run suspect modules under an
  installed-style environment before building.
- `tools/build_release.py` refuses to build from a dirty tree ("a release is built from HEAD
  only"): commit everything before starting a build chain, or the whole chain cascades.
- Maintenance commands (`installer.py uninstall/rollback/install`) must run with the
  package's Python beside `release\`, never the installed release's own Python: they stop
  every process running from the install folder, including that interpreter.
- `$Home` and `$args` are PowerShell automatic variables: never use them as parameter or
  variable names in scripts (`$HOME` is read-only).
- Timestamps written into evidence records come from the clock (`Get-Date` in the same
  command, or the marker `@@NOW@@` filled by `tools/host/stamp_record.py`), never from an
  estimate. Keep tool commands short: one long command that read, wrote and ran a tool at
  once was refused by the permission check on 2026-10-04; split into small steps instead. Seven Gate 16R records of 2026-10-04 carry estimated
  `utc` fields; `gate16r-evidence/timestamp-correction-20261004.json` lists the true times.
- When something is built from an approved text, compare the two at build time and put any
  difference to the owner then. Two differences (guest account group, default machine folder)
  were only found at the Gate 16R result check and needed a late owner decision.
- PowerShell 5.1 breaks a `git commit -m` message that contains double quotes; keep them out.
- `Invoke-Gate17.ps1` field `process_images_outside_install` (step I5) can never be non-empty
  (it filters the same list it was built from). Do not cite it as evidence; the Cleanliness
  phase (no other Python or Node on the machine) is the evidence for "no hidden dependency".
- Do not read the sealed P0 evidence folder `D:\JARVIS-S6-FRESHVM\evidence\P0\` or the
  protected VirtualBox paths; both are owner-only. (This session read two files from the
  P0 folder, read-only, before noticing the rule; disclosed to the owner.)

## Session log

- **2026-10-01, release readiness.** Moved builds to D: (C: full). Fixed installer crash
  safety (launcher/current.json writes, damaged-release repair) with fault tests at every
  update step; real kill-mid-copy test passed. Wrote the release regression tool; it found
  that interface inspection depended on Google Chrome (absent on a clean Windows 11), now
  Edge with a retry and failures logged to core.log. Lifecycle 1.0.4 → 1.0.6, zip install of
  1.0.7, and full regression of 1.0.6 and 1.0.7 all pass. Freed C: from 5 GB to 20 GB by
  moving files to D:. Nothing pushed or synced.
- **2026-10-01, later.** Owner approved the release design (recorded, e5daefc). Added the
  missing regression tests for two of the three defects from the preparation review
  (15a1ad1; all three were already fixed in 60c89f1). Read the Stage 6 governing records:
  corrected the "4/5" misreading, found P0 already passed and the account created, and that
  the VirtualBox isolation proof (§7(b)/(e)) is unresolved. Wrote the completion plan.
- **2026-10-01, later still (Fable 5.1).** Designing the Gate 18 rehearsal against the
  packaged layout found five defects (command-line data path, owner config missing from
  backups, restore writing into program files, voice check on a development path, config
  location following the process environment), all fixed with tests; the Core reports
  `installed_release`; the installer reports phase timings. New tools: package-ISO builder
  (`tools/New-PackageIso.ps1`, exercised), Gate 17 guest script draft
  (`tools/guest/Invoke-Gate17.ps1`), P0–P5 checkpoint draft (`tools/host/`, dry mode only).
  1.0.8 regression passed; 1.0.9 had the config-location failure; 1.0.10 built with the fix,
  rehearsals pending at the time of writing. Nothing pushed or synced.
- **2026-10-01/02, Stage 6 decisions and 1.0.11.** Owner chose option B and approved
  amendment v3 (recorded in `../governance/`). Gate 18 rehearsal of 1.0.10 found the backup
  blocked by the Core lock (defect 6); fixed in 1.0.11, which then passed regression, zip
  install, Gate 18 and the local Gate 17 rehearsal. Drafted the Gate 16R execution prompt
  and its support files (answer file, validation-account check, VM creation, isolation
  fixtures and check; owner-account half rehearsed in a scratch folder). Next: the owner
  approves the 16R prompt, then issues `RESUME_STAGE6_FRESH_VM`. Nothing pushed or synced.
- **2026-10-02, Gate 16R in execution (Fable 5.1).** Owner approved the 16R prompt and issued
  `RESUME_STAGE6_FRESH_VM`. Step 0 media built and hashed; step 1 P0 PASS; step 2 §7(b) PASS
  (A3); step 3 §7(e) PASS (A1, A2; harness classification fix, run 1 kept); step 4 §7(c),(d)
  PASS after a documented re-run (first run closed mid-copy; partial copy, not corruption);
  step 5 P1 PASS; step 6a egress folder created by the owner.
  All owner-run work goes through one-click launchers in `D:\JARVIS-S6-FRESHVM\tools\`;
  evidence copied under `docs/stage6-freshvm/gate16r-evidence/`. Nothing pushed or synced.
- **2026-10-02 to 04, Gate 16R steps 6–8 (Fable 5.1).** VM created and verified; audio
  adapter corrected; found that VirtualBox 7.2.18 does not persist NAT localhost-reachable
  off (every start now goes through the start launcher, owner option 1). Windows installed on
  the second attempt (first stalled at 42%); baseline recorded in five runs (two harness
  false positives fixed with new tools discs v2–v4; the check now covers the full §6(f)
  list). Owner approved the roadmap and the simplified acceptance (from Gate 17) and two
  wording dispositions. Lessons: test guest-script changes with the VM's account and
  computer names; never run the Baseline phase on the host; Windows applies staged updates
  at shutdown, so re-record before a snapshot. Next: step 9 snapshot, P2, step 11, step 12.
  Nothing pushed or synced.
- **2026-10-04, Gate 16R step 9 (Fable 5.1, new session from the handover summary).**
  Checked the step 9 launcher against its recorded hashes, the owner took snapshot
  FRESH-CLEAN-BASELINE, Claude verified the record, the `.vbox` copy, the disk lineage and
  the VM log, and wrote the section 6(h)1 manifest with a small reusable tool
  (`tools/host/snapshot_manifest.py`). Then P2 PASS on the owner's "RUN P2", snapshot
  FRESH-PREREQ, identity record, and the step 12 check of every section 6(k) item, which
  found two undispositioned wording differences (guest account group; default machine
  folder property); the owner accepted both; **FRESH_VM_QUALIFICATION_PASS**, evidence
  manifest written. Lesson: compare what was built with the approved wording when it is
  built, not at the end. Then the Gates 17–20 plan rewritten in plain words and its tooling
  built and rehearsed in D: sandboxes: `Invoke-Gate17.ps1` gained an elevation guard, a
  Cleanliness phase and the Gate 19 Update phase; new `tools/guest/Invoke-Gate.ps1` +
  `gate.cmd` (one double-click inside the VM), `tools/host/Invoke-NextStep.ps1` +
  `next-step.cmd`, `Start-Gate17Vm.ps1`, and `New-Gate17PackageDisc.ps1` now builds both
  discs. Seven record timestamps typed by estimate were corrected by a separate note.
  Next: the owner's FINAL selection and plan approval. Nothing pushed or synced.
- **2026-10-04, skill drafts (side task, requested through another Claude session).** Three
  Claude Code skills drafted in `docs/skill-drafts/` (jarvis-verify, jarvis-owner-gate,
  jarvis-codex-review-brief). **Not active**: nothing in `.claude/skills/`, no hook, no
  settings change. Activation is an owner decision; `docs/skill-drafts/README.md` lists what
  to approve and what was not confirmed. Stage 6 state untouched.
