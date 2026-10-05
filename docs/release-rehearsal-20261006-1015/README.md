# Release 1.0.15: build and checks on this PC (started 2026-10-06, not finished)

Owner, 2026-10-06: "build 1.0.15 now". This folder is the record. **State when the session stopped (the owner asked
for the PC to be shut down at a stopping point): one build made and compared, its release regression run with one
test over its own time limit, the cause measured, the test corrected. The build is NOT offered. Next: build again
from the commit with the corrected test, then all checks from the top.**

Everything ran on this PC in folders on D:. The owner's installed JARVIS (`%LOCALAPPDATA%\JARVIS`, 1.0.14, running
with 8 processes the whole time) was never addressed.

## Before the build

- The three open points of the list (`docs/RELEASE-1.0.15-SCOPE.md` section C): the Alibaba maintenance notice
  looked at (nothing to change); the new header looked at in a test desktop window (`header-check/`: the app's own
  Electron and window options, its own profile, a sandbox Core; one width rule fixed, all eight sections show from
  1280 to full width); the release notes written.
- Development suites at the build commit 02ae75e: 634 Python, 52 desktop, 18 Intelligence tests and 23 interface
  scripts pass.
- Every one of the eight parts of the list had one independent review; all findings applied (their records are in
  `docs/`).

## Build 1: `1.0.15-02ae75ed0374` (commit 02ae75e)

- `build-1.0.15.log.txt`, `JARVIS-1.0.15-02ae75ed0374.release.json`: 10,669 files, 1,177,965,355 bytes; zip
  525,845,944 bytes, sha256 `a0a507bb4798f40dcf0aa88ea4146fb6212573948ac5d3af9c5cc97e1a0efc98` (the copy in
  `D:\JARVIS-release-work\pkg-1.0.15` has the same hash).
- `JARVIS-1.0.15-02ae75ed0374.compare-1.0.14.json`: pinned inputs (Python, packages, Electron, models, runtime DLLs)
  identical to 1.0.14. Shipped source: 43 files changed, 19 added, 1 removed (`configure_gemini.py`); these are
  exactly the files of `git diff e038726 02ae75e` outside docs, tools and tests (the 33 other names in that diff are
  test files, which do not ship). 3,972 bytecode files and the 29 pip launcher/RECORD files that record the build
  folder differ, as in every build. The package's `installer.py` is byte-identical to `tools/installer.py`.

## Release regression of build 1: NOT PASSED (one desktop test over its time limit)

`regression-1.0.15-02ae75ed0374.output.txt`, with the release's own Python and Electron: 634 Python tests pass (1
skipped, the 8.3 short-name installer test, as for 1.0.14; 772 s), 18 Intelligence, all 23 interface scripts, and
**51 of 52 desktop tests**. The release verified unchanged before and after.

The one failure (`regression-1.0.15-02ae75ed0374.desktop-log.txt`): "one authenticated job captures the actual 13
panels with no external submission" (`desktop/test/inspection-job.test.cjs`). The test starts the interface
inspection job and waits up to 100 seconds for it to end; after 100 seconds the job was still running.

**Measured afterwards in the same regression copy** (the same job, waited for up to 280 seconds; a temporary test
file that was removed again): the job ended correctly after **113 seconds**, all 13 panels captured, nothing
submitted, the result the test expects. A panel takes about 9 seconds there. The same test took 98 seconds in the
regression of 1.0.12 and 89 seconds in that of 1.0.14, so the 100-second wait had almost no room left, and the
heavier pages of 1.0.15 used it up. In the development tree the job takes 40 to 60 seconds. This is the test's
wait being too short for the job in an installed release, not a wrong result of the job.

**Done:** the test now waits up to 240 seconds (commit after 02ae75e; tests do not ship, so the program files of the
next build are the same as build 1's). Not done: why a panel takes about twice as long in the release layout as in
the development tree was not looked into (the job starts a fresh browser profile under a scratch home for every
panel).

## Not done yet (for the next build)

The release regression carries the tests of the release's own commit, so a clean report needs a build from the
commit with the corrected test. Build 1 is therefore superseded and was not taken further:

1. Build again (`tools/build_release.py --version 1.0.15 --out D:\JARVIS-release-work\release`), compare with 1.0.14
   and with build 1 (the program files must be identical).
2. Release regression.
3. Zip install (`docs/release-rehearsal-20261001/zip_install_rehearsal.py <id>`).
4. Stage 7 pass in a sandbox, 1.0.14 -> 1.0.15, with the version 3 guest scripts:
   `rehearse-stage7-release-v3.ps1` in this folder (written, not run yet). It also exercises the new restart check
   with what Windows really says.
5. The decision tests of the version 3 launcher (the version 2 ones exist; version 3 only has the guest driver's 21
   cases so far).
6. Then the plan for the check in the test VM, for the owner's approval.

Note for these steps: while the owner's JARVIS is running, a sandbox JARVIS that starts beside it cannot register the
emergency-stop key combination and shows a warning box about that. The box belongs to the sandbox copy.
