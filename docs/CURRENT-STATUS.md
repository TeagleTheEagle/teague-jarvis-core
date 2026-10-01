# JARVIS: current status (living document)

**Read this first in every new Claude Code session, and update it at the end of each one.**
Last updated: 2026-10-01 (end of the release-readiness session).

Rules and authority are in `CLAUDE.md` and `../governance/OWNER-DELEGATION.md`; this file
only records where the work stands. Historical handover context: `docs/PROJECT-CONTEXT.md`.

## Where we are

- **Stage 6: INCOMPLETE.** Fresh-VM route active, gate pointer OWNER STOP #1R. P0 PASS
  (2026-09-30, sealed); owner created `jarvis-s6-val`. Experiment 5 unconsumed, its budget
  frozen at 4/5 (that is the experiment budget, **not** a count of Stage 6 attempts).
  Stage 7 not started. Production cutover not authorized.
- **The VM isolation proof is the blocker**, not the package. Read
  `docs/stage6-freshvm/STAGE6-COMPLETION-PLAN.md`: options A/B/C and decisions D1–D9 await
  the owner (Claude recommends option B).
- **Release candidate:** 1.0.8 (next build after 15a1ad1) once it passes regression and the
  zip rehearsal. Previous fully rehearsed build, superseded only by 15a1ad1's
  `desktop/main.cjs` change: **1.0.7-6c356bf982de**, with its distributable zip:
  `D:\JARVIS-release-work\release\JARVIS-1.0.7-6c356bf982de.zip`
  (525,590,739 bytes, SHA-256 `024c6166866a505700019d25f95e1e8f99dc34ab2f0fa011c81be6bbd4995396`).
  Full regression, zip install, lifecycle and interrupted-update evidence:
  `docs/release-rehearsal-20261001/README.md`.

## Next steps

Owner only (Claude must stop and ask, never infer or pre-stage tokens):

1. ~~Confirm the release design choices~~ **Done: approved by the owner 2026-10-01**
   (recorded in `docs/RELEASE-DESIGN.md`, "Owner decision").
2. Choose a way forward in `docs/stage6-freshvm/STAGE6-COMPLETION-PLAN.md` (A, B or C)
   and settle D1–D9. Only then an execution prompt for Gate 16R can be drafted for approval.
3. `RESUME_STAGE6_FRESH_VM` with that approved prompt; `RESUME_STAGE6_RECOVERY` before Gate 18.
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
