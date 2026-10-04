# JARVIS: current status (living document)

**Read this first in every new Claude Code session, and update it at the end of each one.**
Last updated: 2026-10-04 (Gate 16R steps 0–9 PASS; step 10, P2, waits for the owner's "run P2").
Newest handover summary for a fresh session: `docs/HANDOVER-20261004.md`.

Rules and authority are in `CLAUDE.md` and `../governance/OWNER-DELEGATION.md`; this file
only records where the work stands. Historical handover context: `docs/PROJECT-CONTEXT.md`.

## Where we are

- **Stage 6: INCOMPLETE.** Fresh-VM route active, gate pointer OWNER STOP #1R. P0 PASS
  (2026-09-30, sealed); owner created `jarvis-s6-val`. Experiment 5 unconsumed, its budget
  frozen at 4/5 (that is the experiment budget, **not** a count of Stage 6 attempts).
  Stage 7 not started. Production cutover not authorized.
- **Owner chose option B and approved amendment v3 on 2026-10-01** ("i approve everything"):
  the two unprovable isolation cases are dispositioned with a stated limitation, D1–D9 are
  settled at their recommended selections, Claude Code is the executor. Record:
  `../governance/STAGE6-AMENDMENT-v3-RECORD.json` (text `STAGE6-AMENDMENT-v3.md`, sha256
  5f4d3b63…). Gate pointer still OWNER STOP #1R; no token issued; nothing executed.
- **Release candidate: 1.0.11-60d406fb6398** (built from 60d406f; zip 525,622,280 bytes,
  SHA-256 `19236511…`, in `D:\JARVIS-release-work\release\`). Full regression (325/36/18/16),
  zip install, the Gate 18 backup/restore rehearsal and the local Gate 17 rehearsal **all
  pass on it** (`docs/release-rehearsal-20261001/README.md` section 6). It is the candidate
  for the owner's FINAL selection. 1.0.10 failed Gate 18 (backup
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
   snapshot also goes through `step7-start-vm.cmd`. **Step 10 pending:** P2 on the owner's
   "run P2" (reference `checkpoints\p1-20261002-025102`). Then `step11-snapshot-prereq.cmd`
   (owner, validation session, VM stays off; reuse `snapshot_manifest.py` with
   `--snapshot FRESH-PREREQ` and the v3 D1 statement) and the step 12 qualification
   record. The owner runs every
   launcher in `D:\JARVIS-S6-FRESHVM\tools\` (ACL/VirtualBox work is owner-only); Claude
   reads the JSON results from the evidence folder. Evidence:
   `D:\JARVIS-S6-FRESHVM\evidence\gate16r-20261002\`.
3. `RESUME_STAGE6_RECOVERY` before Gate 18.
4. After Stage 6 passes: FINAL selection, switching the everyday JARVIS over, Stage 7.
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
  (`tools/host/snapshot_manifest.py`). Next: P2 on "run P2", step 11, step 12. Nothing
  pushed or synced.
