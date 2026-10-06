# Release 1.0.16: build and checks on this PC (2026-10-06)

Owner, 2026-10-06: "continue 1.0.16" (step 3 of the approved `docs/PHONE-PLAN.md`), later "fix it in 1.0.16" (the
Qwen cloned voice, below). This folder is the record. Two builds were made: **build 1 (`1.0.16-4e54fc946bc3`, commit
4e54fc9) is superseded**: it passed its release regression and zip install, but between those checks the owner's
Qwen cloned voice was found not to speak with the voice code it carries, and the owner chose to carry the fix in
1.0.16. **Build 2, `1.0.16-fccde24e2cc6` (commit fccde24), is the release under acceptance.** Build 1 was never
offered and never left this PC's sandboxes; its files stay in `D:\JARVIS-release-work\release` as evidence. The
number stays 1.0.16 although the program changed between the builds (so far a changed program got the next number:
1.0.12 and 1.0.13), because the approved phone plan names 1.0.16 and nothing of build 1 was offered; the owner's
decision is recorded in `docs/CURRENT-STATUS.md`.

Everything ran on this PC in folders on D:. The owner's installed JARVIS (`%LOCALAPPDATA%\JARVIS`, 1.0.15, running
with 8 processes throughout) was never addressed: every rehearsal counts processes by their program folder
and stops only those from its own sandbox folder. The check in the test VM (Stage 7) is a separate owner-approved
step: `docs/STAGE7-CHECK-1.0.16.md`.

## Before build 1

- Development suites at commit de8fbc1, the last code commit of the five items: **663 Python tests (219.9 s), 52
  desktop tests (49.9 s), 18 Intelligence tests and 24 interface scripts pass** (`dev-suites-de8fbc1.summary.json`;
  the runner is the same set of commands the release regression uses, with the development `.venv` and the PC's
  node).
- `release-notes.json`, entry 1.0.16: the counts corrected from "652 Python tests ... 23 interface scripts" (written
  before item 5 added its tests) to the measured 663 and 24; the music player's test basis stated; byte-exact edit,
  the file's mixed line endings unchanged. Commit 4e54fc9, with the decision-test records below.
- The two parts of 1.0.16 so far (items 1 to 4 of the phone plan as one change, the music as one) each had one
  independent review with the findings applied (`docs/PHONE-CORE-1.0.16.md` section 8, `docs/MUSIC.md`). The two
  new Settings panels were looked at in a sandbox window when they were built (`devices-panel/`, `music-panel/`;
  the Private network switch was never turned on).

## Build 1: `1.0.16-4e54fc946bc3` (commit 4e54fc9), superseded

- `build-1.0.16.log.txt`, `JARVIS-1.0.16-4e54fc946bc3.release.json`: 10,675 files, 1,178,122,900 bytes; zip
  525,910,031 bytes, sha256 `32e6b1d57cb0e3f7137a9f0f0de3d7f1ea010201f36bb847b82844ad7151a885`; built from the clean
  tree 16:00:43-16:02:20 local.
- `JARVIS-1.0.16-4e54fc946bc3.compare-1.0.15.json`: pinned inputs identical to 1.0.15; shipped source 13 files
  changed and 4 added (`music.py`, `remote_devices.py`, `static/music.css`, `static/music.js`), 0 removed: exactly
  the files of `git diff 6336292 4e54fc9` outside docs, tools and tests (the 8 other names in that diff are test
  files); the other differences are the 3,979 bytecode files (plus the 2 new ones) and the 29 pip launcher/RECORD
  files that record the build folder. The package's `installer.py` was byte-identical to `tools/installer.py`.
- **Release regression PASS** (`regression-1.0.16-4e54fc946bc3.output.txt`, `...desktop-log.txt`): 663 Python (1
  skipped, as always: the 8.3 short-name installer test; 916.6 s), 52 desktop (144.2 s; the interface-capture test
  140 s against its 240 s wait), 18 Intelligence, 24 interface scripts; 96 test files overlaid from 4e54fc9; 1,093 s
  in all (16:03-16:21).
- **Zip install PASS** (`zip_install_rehearsal-1.0.16-4e54fc946bc3.output.txt`): installed in 30 s, launched (8
  processes, Core answering), verified, uninstalled while running: 10,675 program files removed, data kept, 0 left.
- Not taken further: no sandbox Stage 7 pass for build 1.

## Between the builds: the Qwen cloned voice did not speak

The owner ran `tools/host/Test-QwenVoice.ps1` (jonny account): one cloned voice on the Alibaba account, made
2026-09-18; the owner put its ID in the key file as `QWEN_TTS_VOICE`; the spoken test then failed with "the answer
held no usable sound link". A diagnostic line in the tool showed why: Alibaba answered with a plain `http://` link
to the finished sound on `dashscope-result-bj.oss-cn-beijing.aliyuncs.com`, and both the tool and
`providers.qwen_speech` accepted `https://` Alibaba links only, so JARVIS 1.0.15 and build 1 refuse it the same
way. **The fix (commit fccde24):** `providers.qwen_result_link` fetches a link to an Alibaba file server
(`*.aliyuncs.com`) over https at the same name whatever scheme the answer names (the server answers at the same name
over https and the link's signature does not depend on the scheme); anything not on `*.aliyuncs.com`, a scheme
other than http or https, an unusual port, or a value that is not a link is refused, and the download carries no
key. The tool got the same rule (`ResultLink`) and a refusal that names the address. Tests: `test_qwen_voice.py`
(9, with the http link, the refusals and the ports pinned); `tools/host/check_qwen_voice_tool.py` 38 of 38, now
probing the tool's function on its own. **Independent review (one reviewer): no high finding; 1 medium and 4 low,
all applied.** Record: `docs/SPEECH.md` section 2. Owner: "fix it in 1.0.16".

Development suites on the final tree (`dev-suites-build2.summary.json`, `dev-suites-build2-python-rerun.txt`):
**664 Python, 52 desktop, 18 Intelligence, 24 interface scripts pass.** The first run of the Python suite had one
failure under disk load: the automatic-backup thinning test (`test_auto_backup`) got "Backup snapshot timed out", the
20-second deadline of the database snapshot in `recovery.py`, while a 142,801-file copy by the owner and the C:
survey ran on the same disks; the test alone passed (26 of 26) and the whole suite passed again (664 in 186.5 s).

## Build 2: `1.0.16-fccde24e2cc6` (commit fccde24), the release under acceptance

- `build-1.0.16-build2.log.txt`, `JARVIS-1.0.16-fccde24e2cc6.release.json`: 10,675 files, 1,178,125,117 bytes; zip
  525,906,502 bytes, sha256 `58bba7423cf0668ff7684e9370865b9951e473eb1e0818c9437bf4287032d23a`; built from the
  clean tree 16:57:07-16:59:10 local. The copy in `D:\JARVIS-release-work\pkg-1.0.16` (zip and record; build 1's
  were removed from there) has the same hash.
- `JARVIS-1.0.16-fccde24e2cc6.compare-build1.json`: against build 1, 2 source files changed (`providers.py`,
  `release-notes.json`), 0 added, 0 removed; the rest is the 3,981 bytecode files and the 29 pip launcher/RECORD
  files that record the build folder and time.
- `JARVIS-1.0.16-fccde24e2cc6.compare-1.0.15.json`: pinned inputs identical to 1.0.15; shipped source 14 files
  changed (build 1's 13 plus `providers.py`), 4 added, 0 removed. `installer.py` byte-identical to
  `tools/installer.py`.

## Release regression of build 2: PASS (`regression-1.0.16-fccde24e2cc6.output.txt`)

With the release's own Python and Electron (no development environment, no system Node), 1,350 s
(16:59:15-17:21:45): 664 Python tests (1 skipped, as above; 1,103.9 s), 52 desktop (183.3 s), 18 Intelligence, 24
interface scripts; 96 test files overlaid from fccde24; the release verified unchanged before and after. The
interface-capture test took 175 s (`...desktop-log.txt`; wait 240 s). The owner's move of a 40 GB folder from C: to
D: ran during this regression, which is why it took longer than build 1's.

## Zip install of build 2: PASS (`zip_install_rehearsal-1.0.16-fccde24e2cc6.output.txt`)

Zip hash equals the record; Windows extraction gives `install.cmd`, `installer.py`, `release`; `install.cmd --home
<sandbox> --no-shortcuts` installed 1.0.16 in 70 s (the same folder move was running; build 1: 30 s); launched (8
processes, Core answering); verified after use; uninstall **with JARVIS running** removed all 10,675 program files,
kept data/config/profile, 0 processes left.

## Stage 7 pass in a sandbox, 1.0.15 -> 1.0.16 (build 2), version 3 scripts (`stage7-local/`)

`docs\release-rehearsal-20261006-1015\rehearse-stage7-release-v3.ps1 -Package D:\JARVIS-release-work\pkg-1.0.16
-PreviousPackage D:\JARVIS-release-work\pkg-1.0.15 -Base D:\JARVIS-release-work\stage7-local-1.0.16` (the 1.0.15
harness, unchanged; started from PowerShell by full path): version 3 guest scripts, sandbox home and staging, no
shortcuts, no provider key in the environment, 2026-10-06 17:26-17:42 (16 min).
**ALL STAGE 7 STEPS PASSED**, with the restart check exercised against what Windows really says:

| Start of the driver | Result |
|---|---|
| 1: Install | PASS (17:26:29-17:30:38): package, extract 126 s, install 27.6 s (verify package 8.0 s, copy 8.2 s, verify copy 9.9 s, switch 0.4 s), verify, launch (8 processes), duplicate Core refused, local speech recognition 4.3 s, the restart check's record written; then the driver asked for the Windows restart |
| 2: on the same start of Windows | "Windows has not been restarted since the install step" (the real record against the real Windows), as it must |
| 3: with a file saying "one start later" (`-BootIdentityFile`, standing in for the restart nobody performs here) | the restart seen; AfterRestart PASS (JARVIS up, both memories); Uninstall PASS (all 10,675 program files removed, data/config/profile kept) and reinstall; Update PASS: 1.0.15 extracted (134 s) and installed over the kept data (4 processes at its first launch, 8 at every later one, as in the 1.0.15 VM check), updated to 1.0.16 while running (134 s wall; the Core ready 19.7 s after the switch; 8 processes, both memories), rollback to 1.0.15 (11.6 s; both memories), update again (36.2 s); Interrupt PASS: installer killed after 11.4 s with 3,351 of 10,675 files copied, 1.0.15 still current, verified and running with both memories, no 1.0.16 folder in place; the rerun finished in 32.6 s, verified, started with both memories, stopped cleanly (17:30:39-17:42:24). The owner's 40 GB move from C: to D: ran throughout, which is why every copy took longer than in the 1.0.15 rehearsal |
| 4: nothing left to do | ALL STAGE 7 STEPS PASSED, no phase run (17:42:24-17:42:25) |

Live JARVIS processes before and after: 8 and 0 (the owner quit their everyday JARVIS by hand during the run: asked at 17:49, answer "yes i did"; the sandbox's records name no process outside its folder, its installer is byte-identical to 1.0.15's, and the 1.0.15 rehearsal with the same code left the live JARVIS at 8 and 8); sandbox processes after: 0.
Every run's first record (E0) notes the Windows build and the Administrators membership. Records: `stage7-local/`
(the harness log and summary, the driver log, every run's records; the Core logs are left in the work folder).

## Stage 7 tools, version 3: unchanged since the 1.0.15 approval, decision tests run again

- The ten tools' hashes equal the table of `docs/STAGE7-CHECK-1.0.15.md` and of its approval record (read again on
  2026-10-06; the same table is in `docs/STAGE7-CHECK-1.0.16.md`). No version 4: the two launcher follow-ups of the
  1.0.15 check are met by two notes in the 1.0.16 plan (leave the launcher window open during the VM's power-on; this
  check's disc is drive E:).
- `tools/host/stage7-v3/test-stage7-step-v3.ps1` (the launcher in test mode, fake tree, no VirtualBox): **18 cases
  PASS** (`test-stage7-step-v3.output.json`). `tools/host/stage7-v3/test-stage7-pass-v3.ps1` (the guest driver, fake
  discs, no phase runs): **21 cases PASS** (`test-stage7-pass-v3.output.json`; this PC's count of starts 61, newest
  "operating system started" entry 17330, one PC restart since the 1.0.15 run). Both test scripts still carry the
  1.0.15 names as their fake data: they test the tools' decisions, not a release.

## Not checked here

Anything in VirtualBox; a real Windows restart (the restart check was exercised with what Windows really says, and
with a file standing in for "one start later"); Desktop/Startup shortcuts; a non-administrator account; a real
Tailscale network, a real phone or glasses (the private-network door was tested with a second loopback address
standing in for the PC's Tailscale address; the switch was never turned on outside the tests); music through the
speakers from a file of the owner's (a generated two-second tone was played once on this PC on 2026-10-06, volume 25,
when the item was built); the Qwen voice against the real account with the fixed code (the owner-run tool carries the
same rule and is the owner's check; the test suites use stand-ins); and, as for 1.0.15, the parts that need a real
provider, Ollama, another device or a backup drive.
