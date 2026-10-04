# Release 1.0.13: build and checks on this PC (2026-10-05), superseded

Release `1.0.13-6d4ff851cca4` (commit 6d4ff85): 1.0.12's fixes plus the installer change found by the 1.0.12 sandbox
Stage 7 rehearsal (eb620cd) and the findings of its independent review (6d4ff85). Everything below ran on this PC in
folders on D:; the owner's installed JARVIS (`%LOCALAPPDATA%\JARVIS`) was never addressed (it was not running).
**1.0.13 failed its release regression and is superseded (never offered); the next build is 1.0.14.**

## Before the build

- Independent review of the installer change (the earlier review was interrupted with the session that started it,
  2026-10-05 00:24, and returned nothing; run again): 2 medium and 6 low findings, applied in 6d4ff85 except one
  recorded limitation (a program the Core opened can keep an empty release folder after uninstall). The six new or
  changed installer tests fail on eb620cd's installer and pass on 6d4ff85's.
- Development suites at 6d4ff85: 373 Python, 50 desktop, 18 Intelligence, 17 interface scripts, all pass.

## Build and comparison with 1.0.11

- `build-1.0.13.log.txt`, `JARVIS-1.0.13-6d4ff851cca4.release.json`: 10,645 files, 1,177,430,753 bytes, built in 118 s;
  zip 525,632,584 bytes, sha256 `a663b838d3dc47d732db603f6a361c5cee8ee6e87f4106ee7ae81835029713e2`.
- `JARVIS-1.0.13-6d4ff851cca4.compare-1.0.11.json`: the same 10,645 paths; changed: the same 14 shipped source files
  as 1.0.12 (exactly `git diff 60d406f 6d4ff85` outside docs, tools and tests), 3,973 bytecode files and the 29 pip
  launcher/RECORD files; pinned inputs identical. The package's `installer.py` (outside the manifest) is
  byte-identical to `tools/installer.py` at 6d4ff85.
- `D:\JARVIS-release-work\pkg-1.0.13` created, zip hash equal to the record; `pkg-1.0.11`'s zip re-checked equal to
  FINAL's record (`19236511...`).

## Release regression: FAILED (desktop suite)

| Run | Folder | Result |
|---|---|---|
| 1 | `regression-1.0.13` | Python 373 OK (1 skipped), Intelligence 18, 17 scripts PASS; desktop 48 of 50: "shared background Core ..." (`backend.test.cjs:44`, Core still answering right after `shutdown()`) and "one authenticated job captures the actual 13 panels" (still running at its 100 s limit). `regression-1.0.13-run1-*` (report, desktop log) |
| 2 | `regression-1.0.13-run2` | stopped during the copy when the session was interrupted; no result |
| 3 | `regression-1.0.13-run3` | the PC idle (CPU 2-5 % before the start): desktop 49 of 50, the same "shared background Core" assertion. `regression-1.0.13-run3-*` |

The same test passed in 1.0.12's regression (6.2 s) and in the development runs, so it was not new code but a race.

**Cause, reproduced** (`debug-shared-core.cjs` run by `run_in_regression_env.py` in run 3's copy, which gives it the
regression's environment): after `/api/shutdown` the Core refuses new connections and removes
`core-connection.json`, but until its process exits, a few hundred milliseconds later, it can still answer a request
on a connection that was already open (HTTP keep-alive, `ThreadingHTTPServer` handler threads). The desktop app's
`shutdown()` ("Quit JARVIS completely") stopped waiting at the first failed probe, so it could return while the Core
still ran. Alone: 9 of 9 runs clean. With the desktop suite running alongside: 1 of 10 runs showed exactly that
(`pooled fetch alive=true`, fresh connection refused, file gone, process alive; gone 0.26 s later).

**Fix (for 1.0.14):** `desktop/backend.cjs` `shutdown()` waits (at most 10 s, as before) until the Core's process
has exited and it no longer answers. New tests in `desktop/test/shutdown-wait.test.cjs`: a stand-in Core that
removes its file and drops every connection but lives 1.5 s longer (fails on the old `backend.cjs`, passes on the
new), and quitting after a Core crash returns at once. An independent review of the fix found two low issues, both
applied: a first version also waited for the connection file to go, which made quitting after a crash wait the full
10 s (a crash leaves the file); and the test could have started a real Core had it read a half-written file. The panel-capture timeout of run 1 did not
recur in run 3; it is a 100 s limit on a slow machine and is watched in the next regression.

## Stage 7 tools, version 2

The final message of the guest driver (`tools/guest/stage7-v2/Invoke-Stage7Pass.ps1`) said "tell Claude: stage 7
done" right after the shutdown; the approved order is shutdown, then `stage7-step` in jarvis-s6-val (snapshot),
then "stage 7 done". Corrected before any disc carries it. `test-stage7-pass-v2.ps1` (copy with the 1.0.13 label):
8 cases PASS (`test-stage7-pass-v2.output.json`).

Not run on 1.0.13 (superseded first): zip install, the sandbox Stage 7 pass.
