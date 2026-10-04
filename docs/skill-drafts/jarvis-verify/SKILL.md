---
name: jarvis-verify
description: Prove that a JARVIS change or build really works before it is called done. Use whenever work on the JARVIS Core (server.py and the Python modules), the desktop or Intelligence Electron apps, the installer or a release build is about to be reported as finished, fixed, working, passing or ready, and whenever the owner asks "does it work", "is it done" or "did you test it", even if nobody says "verify". Runs the real test suites and a real launch from this repo, and requires pasted command output as evidence.
allowed-tools: Read, Grep, Glob, Bash(git status *), Bash(git diff *), Bash(git log *)
---

# JARVIS verify

The owner cannot check the code, so "done" has to mean "seen working on this PC, with the output to show
for it". Several real defects in this project (config location, backup blocked by the Core lock) passed a
read of the source and were only found by running the thing. This skill is the routine for that.

Run every command from the repo root, `C:\Users\jonny\JARVIS-claude-workspace\repo`, in PowerShell 5.1
(no `&&`). Read "Gotchas for Claude" in `docs/CURRENT-STATUS.md` first; it lists traps that waste a run.

## 1. Choose the level

| What changed | Level |
|---|---|
| Python or JavaScript source, tests, tools | A |
| Anything that affects starting, the window, voice, the Core/desktop connection | A + B |
| `tools/build_release.py`, `tools/installer.py`, `runtime_paths.py`, packaging, or a build meant for the owner | A + B + C |

When unsure, go one level up. Docs-only changes need no run; say so.

## 2. Level A: the four test suites

```powershell
.venv\Scripts\python.exe -m unittest
cd desktop;      node --test test\*.test.cjs
cd intelligence; node --test test\*.test.cjs
Get-ChildItem test_*.cjs | ForEach-Object { node $_.Name }
```

Compare each total with the last totals recorded in `docs/CURRENT-STATUS.md`. A lower total is a finding
even when everything passes: tests that stopped being collected look exactly like success.

## 3. Level B: one real launch (Core plus desktop)

This is the project's first milestone: a real build of the Core and the desktop client running on this PC.

```powershell
Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
.\desktop\node_modules\electron\dist\electron.exe desktop --user-data-dir="$PWD\data\dev-electron-profile"
```

Always pass `--user-data-dir`: without it the workspace build shares a profile and single-instance lock
with the owner's everyday JARVIS. Then collect:

- `data\core-owner.json` (pid and port) and proof that the pid is alive;
- the listener: `Get-NetTCPConnection -State Listen -LocalPort <port>` must show `127.0.0.1` and nothing else;
- the last lines of `data\logs\core.log`, with no traceback;
- what the window actually showed (a screenshot if one can be taken), and the one behaviour the change was for.

Stop it cleanly with the tray's "Quit JARVIS completely". Do not call the API with the client token and do
not read `.env`: real provider keys are the owner's, so without them AI replies are expected not to work;
report that as "not verifiable here", never as a pass.

## 4. Level C: the packaged build

`build_release.py` builds from HEAD only and refuses a dirty tree, so commit first. C: is nearly full; use D:.

```powershell
.venv\Scripts\python.exe tools\build_release.py --version X.Y.Z --no-zip --out D:\JARVIS-release-work\release
.venv\Scripts\python.exe tools\release_regression.py --package D:\JARVIS-release-work\release\JARVIS-<id> --work D:\JARVIS-release-work\regression-<version>
```

Evidence is `regression-report.json` in the work folder. For an install check use a sandbox home only:
`release\python\python.exe installer.py install --package . --home <sandbox on D:> --no-shortcuts`, run with
the package's own Python. Never run `install.cmd` without `--home <sandbox>`; that would be the cutover.

## 5. Evidence rules

- Paste the command and the lines that carry the result (for example `Ran 325 tests ... OK`, `# pass 36`,
  `# fail 0`) from this session. A claim without output from this session is not evidence.
- Name what kind of proof each line is: read the source, test result, live run on this PC, packaged build.
  They are not interchangeable.
- A step that was not run is written `SKIPPED: <reason>`. A step that failed is written `FAILED` with its
  output. Never leave either out, and never describe a skipped step in words that sound like a pass.
- Keep the first failure. Fix the cause and run again as a new, recorded run; do not re-run until green and
  report only the green one.

## 6. Report

```
Verification of <change> at <commit, or "uncommitted">
| Check | Command | Result | Evidence |
|---|---|---|---|
| Python suite | .venv\Scripts\python.exe -m unittest | PASS | "Ran N tests in Ns / OK" |
| Desktop tests | node --test test\*.test.cjs | SKIPPED | reason |
Not verified: <list, or "nothing">
Verdict: VERIFIED / NOT VERIFIED / PARTLY VERIFIED (say which part)
```

Only "VERIFIED" lets the work be called done. Anything about Stage 6 gates, the VM, checkpoints, the live
installation or cutover is not verification work: stop and use the owner-gate check instead.
