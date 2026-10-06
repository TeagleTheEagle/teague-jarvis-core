# JARVIS: current status (living document)

**Read this first in every new Claude Code session, and update it at the end of each one.**
Last updated: 2026-10-06 (about 12:50 local) (STAGE_6_COMPLETE, SWITCH-OVER COMPLETE, STAGE_7_COMPLETE for 1.0.14 and for 1.0.15;
**the everyday JARVIS is still 1.0.14-e03872680e1d; release 1.0.15-63362929d7ad has passed its Stage 7 check in the VM and waits
for the owner's decision on updating the everyday JARVIS**).

- **2026-10-06, about 12:50 local (Fable 5.1, same session; owner's steps 1-6 run 10:48-12:43, snapshot record seen in the owner's photo): STAGE 7 CHECK OF 1.0.15: `STAGE_7_COMPLETE` (evaluated 2026-10-06T01:47Z; 27 of 27 checks).** Evaluation `D:\JARVIS-stage7\1.0.15-63362929d7ad\evidence\stage7-evaluation.json`; manifests host (9 files) and guest (38 files); repo copy `docs/stage7-1.0.15-evidence/` (with `guest/`, `vm/`). VM pass: Install (9), AfterRestart (2, the version 3 restart check saw boot id 7 -> 8 and needed no second restart; Z: never connected by hand), Uninstall (4: 10,669 program files removed, data kept, reinstall), Update (7: 1.0.14 from its own Stage 7 disc, update while running 361 s, rollback 105 s, update again 262 s, both memories each time), Interrupt (5: installer killed at 4,196 of 10,669 files, 1.0.14 untouched and running, rerun 190 s). Snapshot `STAGE7-PASS-1.0.15-63362929d7ad` (`f1add04d-3281-4894-8ccf-baa302755260`) taken after a clean shutdown; current; every older snapshot kept. **Outside the Gate 20 timing bound, put to the owner and not decided: the first install took 675 s (verify of the copied files 341 s; 1.0.14: 352 s) while every update, rollback and stop is inside; the records point at the VM's disk speed in this run (the same files verified in 106 s and 91 s later in the pass; 28 s in the PC sandbox).** Deviations recorded: incident 01 (closed window, false STOPPED), both discs labelled JARVIS_S7, the timing, a first-launch process count of 4. Follow-ups: launcher wording while a start is in progress; the drive letter or a distinct disc label in the next plan. The owner's installed JARVIS was not touched. **NEXT: the plan for updating the everyday JARVIS to 1.0.15, for the owner's approval; the owner's answer on the timing bound; then the phone plan ("write the phone plan").** Also this session, on the owner's ask: the phone design as a Design canvas (claude.ai artifact N7JboAbsdEFwPFhrFFdAcs): three iPhone screens (Ask with the holographic Core on a projector platform, Chats, Status) in the owner's design brief, with real-data telemetry only (CPU, memory, storage, link; no GPU or temperature, which JARVIS does not measure); the owner edited the Ask screen by hand twice and Claude rebuilt on those edits.

- **2026-10-06, about 10:48 local (Fable 5.1, new session; owner: "I approve the Stage 7 check of 1.0.15"): THE STAGE 7 CHECK OF 1.0.15 IS APPROVED AND THE TOOLS ARE PLACED; NEXT ARE THE OWNER'S SEVEN STEPS (STEP 1: THE DISC BUILD IN THE JONNY ACCOUNT).** Approval: first clock reading 2026-10-05T23:44:15Z, recorded 2026-10-05T23:46:59Z; record `../governance/STAGE7-1.0.15-APPROVAL-RECORD.json` (plan sha256 ff0eb131…, repo commit 8a410ed; repo copy `docs/stage7-1.0.15-evidence/`). Checked before placing: the ten tool hashes re-read and equal to the plan; the VM's settings file still shows `STAGE7-PASS-1.0.14-e03872680e1d` current with no change recorded since; the 1.0.15 zip and release record and the hash record beside the 1.0.14 disc are where the scripts look. Claude placed the six host files in `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.15\` (each copy hash-checked) with `stage7-authorized.json` (schema v3, expected current snapshot STAGE7-PASS-1.0.14-e03872680e1d), created `D:\JARVIS-stage7\1.0.15-63362929d7ad\evidence` (approval copy, `prep-tools-hashes.txt`) and the empty guest folder `guest-egress-01\stage7-1.0.15-63362929d7ad`; launcher dry run in test mode: jonny -> build the disc, jarvis-s6-val -> "next step is in jonny". Nothing has run in the VM; the 1.0.11 and 1.0.14 tool folders, discs and records are untouched. (A pasted handover containing the word "ultracode" switched the harness's multi-agent mode on again; no workflow was started.) **NEXT: the owner's steps 1-7 of `docs/STAGE7-CHECK-1.0.15.md` (step 1: jonny account, double-click `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.15\stage7-step.cmd`, then "disc built"; the VM's Windows Update pause ends 2026-11-06). On "stage 7 done" Claude reads every record, writes `stage7-evaluation.json` (STAGE_7_COMPLETE or STAGE_7_INCOMPLETE with the exact step), the manifests and the repo copies. After STAGE_7_COMPLETE: the plan for the update of the everyday JARVIS, for the owner's approval.**
  **Progress of the check (same session, about 11:55 local):** disc built by the owner and checked (iso `7ec19763…`, the zip and the three version 3 guest files on it hash as the approval says; record `stage7-disc-1.0.15-63362929d7ad.json`). Step 2 recorded in `vm\stage7-start-20261005-235205.json` (restored FRESH-PREREQ from STAGE7-PASS-1.0.14-e03872680e1d, no change since, six snapshots kept, discs on ports 1 and 2). **Incident 01** (`incident-01-vm-start-record.json`, `owner-note-01-first-window-closed.json`): the VM's power-on took 2.5 minutes of VirtualBox start-up checks; the owner closed the first launcher window during that wait (so `vm\start-<utc>.json` was never written; LocalhostReachable = 0 is proven from the VM's own VBox.log instead) and double-clicked the launcher again, which printed a false STOPPED ("already started ... and is now off") because VBoxManage still reported poweroff; it ran nothing. Launcher defect in wording only; a later version should say a start may be in progress while VBoxManage.exe runs. Also found: **both discs in the VM are labelled JARVIS_S7** (1.0.14's Stage 7 disc as the previous build has the same label), so the owner was told to open drive E: (port 2) and check for the 1.0.15 zip; the plan should name the drive letter next time. Inside the VM: **Install phase PASS (E0, I1-I8; 10:59-11:33 local; extract 704 s, install about 11 min, local STT correct, restart with memory kept), AfterRestart PASS (restart seen by boot_id 7 -> 8: the version 3 fix works), Uninstall PASS (U1-U3, 11:42-11:51); Update phase started 11:52.** No step failed; nothing repeated.
  **Owner decisions for the phone, taken this session (for the phone plan after the everyday update):** iPhone app only (no Mac software version); it must work at home on Wi-Fi and away on cellular, so devices reach the PC over a private network (Tailscale), set up by the owner from written steps; the PC stays awake for the first phone version (Windows sleep off; a mini PC as an always-on home for the Core considered later, which would change the "Core lives on the owner's PC" rule and is the owner's decision); the owner has a Mac with Xcode and an active Apple Developer membership; install path recommended: TestFlight internal testing. Order unchanged: Stage 7 result, the everyday update plan, then the phone plan for approval.

- **2026-10-06, about 10:40 local (Fable 5.1, new session after the restart; owner: "continue 1.0.15"): RELEASE 1.0.15 BUILT AND CHECKED ON THIS PC; THE PLAN FOR THE VM CHECK WAITS FOR THE OWNER'S APPROVAL.** Records: `docs/release-rehearsal-20261006-1015/README.md`; the plan: `docs/STAGE7-CHECK-1.0.15.md`.
  **Build 2 is the release under acceptance: `1.0.15-63362929d7ad`** (commit 6336292; zip sha256 `1019dce00702da4e15dac5ea8203a1a1034311fbbe30b352097517b16deec027`; in `D:\JARVIS-release-work\release` and `pkg-1.0.15`). Its program files are identical to build 1's (only the test wait changed); against 1.0.14 the same 43 changed, 19 added and 1 removed source files, pinned parts identical. **Release regression PASS** (634 Python with 1 skipped as always, 52 desktop, 18 Intelligence, 23 interface scripts; the capture test took 180 s this time, inside its new 240-second wait). **Zip install PASS** (28 s; launched with 8 processes; verified; uninstalled while running, 10,669 files removed, data kept). **Sandbox Stage 7 pass 1.0.14 -> 1.0.15 with the version 3 scripts: ALL STAGE 7 STEPS PASSED** (11.5 min; the restart check exercised with what Windows really says: asked for the restart when there was none, saw one when told of one by a file). Live JARVIS processes 8 before and after every rehearsal, sandbox processes 0 after.
  **Found and fixed by the first run of that rehearsal: two runs in one folder.** The checks script named each run's folder by its start second; the after-restart run took under a second and the uninstall run got the same folder and replaced its records, so the driver ran the after-restart phase again. The defect was in versions 1 and 2 too, never hit (8 s and 2 s between those runs in 1.0.14's check and rehearsal). Fixed in `tools/guest/stage7-v3/Invoke-Stage7.ps1` (a run waits for a free second); the rehearsal was run again and passed (`docs/STAGE7-DRIVER-V3.md` section 4). Also for version 3: `Start-Stage7Vm.ps1` takes the previous build's own Stage 7 disc when it has no package disc (1.0.14 never had one); the launcher's decision tests (18 cases) and the driver's (21 cases) pass.
  **Plan for the VM check written: `docs/STAGE7-CHECK-1.0.15.md`, READY FOR THE OWNER'S APPROVAL.** 1.0.15-63362929d7ad against 1.0.14-e03872680e1d; the VM is on `STAGE7-PASS-1.0.14-e03872680e1d` with no change recorded since; the previous build's disc is 1.0.14's Stage 7 disc. **Nothing has run in the VM. NEXT: the owner's approval ("I approve the Stage 7 check of 1.0.15"); then Claude records it, places the version 3 tools in `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.15\` with hashes and creates the two record folders; then the owner's seven steps.** After STAGE_7_COMPLETE: the plan for the update of the everyday JARVIS, for the owner's approval. The owner's direction for after the launch (the iPhone app and a Mac version, one Core) stands as recorded in the entry below.

- **2026-10-06, about 03:24 local (Fable 5.1, same session): WHERE THE SESSION STOPPED. Owner: "build 1.0.15 now", then "when you get to a stopping point, stop and shut down my pc". Release 1.0.15 was built once and is NOT finished checking; the PC was shut down by Claude at the owner's request (a normal shutdown, not forced).** Record: `docs/release-rehearsal-20261006-1015/README.md`.
  **Done before the build:** the Alibaba maintenance notice looked at (it names the Beijing address; JARVIS uses the Singapore one, which answered on 2026-10-05; nothing to change); the new header looked at in a test desktop window (the app's Electron and window options, its own profile, a sandbox Core): one width rule fixed, all eight sections show from 1280 wide to full width and nothing sits under the Windows buttons; the release notes for 1.0.15 written (`release-notes.json`, with the key-file line to change for a removed provider and what a rollback to 1.0.14 does not enforce). Development suites at the build commit 02ae75e: 634 Python, 52 desktop, 18 Intelligence, 23 interface scripts pass.
  **Build 1: `1.0.15-02ae75ed0374`** (in `D:\JARVIS-release-work\release` and `pkg-1.0.15`): 10,669 files; pinned inputs identical to 1.0.14; the changed source files are exactly those of the commits since 1.0.14.
  **Release regression of build 1: NOT PASSED.** 634 Python (1 skipped as before), 18 Intelligence, 23 interface scripts and 51 of 52 desktop tests pass. The one failure is the interface-capture test (`desktop/test/inspection-job.test.cjs`): it waits 100 seconds for a job that, measured afterwards in the same copy, ends correctly after 113 seconds (98 s for 1.0.12, 89 s for 1.0.14: the wait had almost no room, and the heavier pages used it up). A test wait that is too short, not a wrong result. **The test now waits 240 seconds (committed).** Because the regression carries the tests of the release's own commit, a clean report needs a new build: **build 1 is superseded and was not taken further; it is not offered.**
  **NEXT, in this order (nothing here needs the owner until step 6):** (1) build 1.0.15 again from the current commit (`.venv\Scripts\python.exe tools\build_release.py --version 1.0.15 --out D:\JARVIS-release-work\release`), compare with 1.0.14 and with build 1 (the program files must be identical: only a test changed); (2) release regression; (3) zip install; (4) sandbox Stage 7 pass 1.0.14 -> 1.0.15 with `docs/release-rehearsal-20261006-1015/rehearse-stage7-release-v3.ps1` (written, not run); (5) decision tests of the version 3 launcher; (6) the plan for the check in the test VM, for the owner's approval; then the update of the everyday JARVIS on the owner's approval. Remove the release-notes sentence about tests only if the counts change. While the owner's JARVIS runs, a sandbox JARVIS started beside it shows a warning box about the emergency-stop key combination: that box belongs to the sandbox copy.
  **Owner's direction for after the launch (2026-10-06, during the build): "so after the launch of the app we should start the ios app and mac software version ONE JARVIS ONE CORE".** Recorded, not started. What it needs that is not in the workspace (scope list section B): for the iPhone app a Mac with Xcode, an Apple developer account and the iPhone (the Xcode project is not in the workspace; three Swift files are); for both the iPhone and a Mac version, the owner's decision on how a device reaches the one Core on this PC (today the Core listens on this PC only; opening it to the home network or beyond is the owner's decision, recorded 2026-10-01). A Mac version under ONE CORE is a client of this PC's Core, like the phone: no second Core, Store or AI stack on the Mac. The pairing and the device contract of item 4 (`docs/DEVICES.md`) are what both would connect through. First questions for the owner next time: is there a Mac to build on, and how should the devices reach the PC (home Wi-Fi only, or a private network such as Tailscale).

- **2026-10-06, about 02:45 local (Fable 5.1, same session): version 3 of the Stage 7 check scripts written and committed** (`docs/STAGE7-DRIVER-V3.md`; `tools/guest/stage7-v3`, `tools/host/stage7-v3`). It fixes the two incidents of the 1.0.14 check, both defects of the version 2 driver and not of JARVIS: (1) the driver built a path on `Z:` before connecting `Z:`, so the owner had to connect it by hand before every start; (2) the restart check compared running times and said "not restarted" when stage7 was started later after the restart than Windows had been running at the install step. Version 3 puts the path together as text, and asks Windows which start this is (its own count of starts and the newest "operating system started" entry of the System log) instead of comparing running times; without a record of the install step's start it stops for a decision instead of skipping the check. The version 2 files are unchanged (evidence). **21 decision cases pass on this PC; no phase runs in them and nothing is installed. Nothing here has run in the VM**, and it is first used when the owner approves the check of 1.0.15.
  **One slip, recorded in section 2 of that record:** to show that the new cases catch the old defects I also put them to the version 2 driver. It ignores the test switch it does not know and started its AfterRestart check for real, with a scratch folder as the install folder. That check only waits (four minutes) for a JARVIS in that folder, counts processes started from it and writes a FAIL into the scratch evidence folder, which was deleted. It starts and stops nothing; the installed JARVIS, its data and every other folder were not touched. The tests now refuse a driver without that switch.
  **Still open on the 1.0.15 list before a build:** the Alibaba "maintenance mode" note, the new header checked in the desktop app itself, the release notes. The owner can say "build 1.0.15 now" at any point.

- **2026-10-06, about 02:40 local (Fable 5.1, same session): scope item 8 (replies that appear while they are written) built, reviewed and committed. THE LIST OF EIGHT IS DONE: 8 of 8.** `docs/REPLY-STREAM.md` is the record. For Qwen, behind a tick box that is **off by default** (Settings > AI > "Show replies while they are written"): the Core asks for the answer in pieces, and each time a sentence is complete it runs the same claim checks as for a finished answer on everything written so far; while they leave the text unchanged it is shown as a draft, from the first change nothing more is shown early, and the finished, checked answer replaces the draft. So "I have saved the note" without a receipt is never on screen, not even for a moment, and not even the beginning of a "who answered" line. A model's thinking, words that come with a tool request and a daily briefing are never shown early. Speech starts when the answer is complete, other devices get the finished reply only, OpenAI is unchanged. A stream that breaks is asked again in one piece, once; an unpaid bill or a wrong key is not asked twice; an answer still arriving after 120 seconds ends as it does without the setting. Stop takes the unfinished reply off the screen at once, also while the provider is silent.
  **Independent review (one reviewer, on a separate copy of the tree): nothing serious, 5 lesser findings, all applied** (section 7 of the record). It ran 20 answers made to break the rule at 9 piece sizes through the real answer path: 201 drafts, every one a beginning of the answer that the checks leave unchanged. The fixes were not reviewed again.
  **Found by trying it over a real connection on this PC:** on Windows a reader waiting for the provider is not woken by shutting the connection down, only by closing the socket itself; with shutdown alone Stop took 25 seconds. `providers.cut_connection` does both (Stop then took 0.5 seconds), and the Stop of an offline answer (item 7) uses the same.
  **Seen in the sandbox window** (a stand-in provider on this PC that writes slowly; nothing able to leave the PC), before and after the review: sentence by sentence, the first after about 1 second; a claim never shown; a forged "who answered" line never shown; words before a tool request taken away; a broken stream replaced by the complete answer; Stop on a silent provider answered "Stopped." within a tenth of a second.
  **NOT tried against the real Qwen service** (no request left this PC; the shape of its stream is from Alibaba's published description), and not over an encrypted connection. If the real stream differs, the question is asked again in one piece. The owner's first answer with the box ticked is the real test.
  **Tests on the development tree: 634 Python, 52 desktop, 18 Intelligence, 23 interface scripts pass.**
  **What the owner should know about 1.0.15 so far:** (1) "Hey JARVIS" now also interrupts a JARVIS that is thinking. (2) Offline answers will be ON by default on this PC because Ollama with `qwen3:4b` is installed; Settings > AI switches them off. (3) Off by default and untested against the real providers: replies shown while written (this item) and cloud speech recognition (item 5). (4) Automatic backups do nothing until a folder is chosen in Settings > Backups. (5) Whether a Qwen cloned voice exists on the account: `powershell -ExecutionPolicy Bypass -File C:\Users\jonny\JARVIS-claude-workspace\repo\tools\host\Test-QwenVoice.ps1` in the jonny account.
  **Next on the 1.0.15 list** (`docs/RELEASE-1.0.15-SCOPE.md` section C): the version 3 VM check driver (in the tree, its own commit follows), the Alibaba "maintenance mode" note, the new header checked in the desktop app itself, the release notes; then, as for every release, build, comparison with 1.0.14, regression, zip install, sandbox Stage 7, and the VM check and the update of the everyday JARVIS each on the owner's approval. **The owner can say "build 1.0.15 now" at any point.**

- **2026-10-06, about 02:30 local (Fable 5.1, same session): scope items 6 (automatic backups) and 7 (answers without the internet) built, reviewed and committed.** Records: `docs/AUTOMATIC-BACKUPS.md`, `docs/OFFLINE-ANSWERS.md`. Both are in the repo for 1.0.15 only; the everyday JARVIS (1.0.14) has neither.
  **Automatic backups (item 6):** Settings > Backups > Automatic backups. Off until the owner types a folder (for example on the backup drive) and presses TURN ON; then one backup a day or a week at the chosen time, made and checked exactly like a backup made by hand, into a subfolder `JARVIS automatic backups`. A PC that was off catches up. Kept: the newest seven, every one of the last 7 days, one a week for 8 weeks, one a month for a year; a backup made by hand is never removed. Started only while JARVIS is idle and never under an emergency stop; a question that arrives during a backup waits for it (up to a minute). A full or missing drive is said in plain words and tried again an hour later. Nothing is uploaded; the Core opens nothing.
  **Answers without the internet (item 7):** when no AI provider can be reached at all (never for a refusal: a bill, a key, a limit) and the backup provider cannot be reached either, the small local model in Ollama on this PC answers, and the reply ends with a line only the Core can write that says so and what the local model cannot do. No tools, no pictures, no files; nothing leaves the PC. **On by default, and it will be active on this PC because Ollama with `qwen3:4b` is installed here**; Settings > AI > Offline answers switches it off. The local model's words meet the same claim checks as a provider's ("I saved it" without a receipt is replaced), and Stop ends a local answer at once.
  **Independent review (one reviewer, both items): no high finding, 6 medium, 12 low, all applied** (section 5 and section 6 of the two records). Medium: TURN OFF during a running backup was undone when it finished; one backup made with the PC clock far ahead removed nearly all older ones and stalled the schedule; a question arriving during a long backup failed "internally" and lost a typed note; a full drive was reported as "OSError"; Stop did not end a local answer (up to 90 seconds); the claim checks were not applied to the local model's text. The fixes were not reviewed again.
  **Seen for real on this PC:** the Backups block in the sandbox window before and after the review (a refused folder keeps what was typed; TURN ON; BACK UP NOW; listed as "automatic"; test restore passed before the review); the real local model `qwen3:4b` asked through the changed code: a clean answer in 7.5 seconds with no thinking shown, and a second question stopped after 2.0 seconds. **Not tried:** a real backup drive unplugged or full; a real loss of the internet with the real key; speech for an offline answer.
  **Tests on the development tree: 610 Python, 52 desktop, 18 Intelligence, 23 interface scripts pass** (8 of the Python tests belong to item 8's first file, which is in the tree but not in this commit).
  **Count: 7 of 8.** Item 8 (replies that appear while they are written; Qwen; a setting that is off by default) is built in a separate copy of the tree: its 24 tests and the whole Python set pass there, it was watched in the sandbox window with a stand-in provider (sentence by sentence; an unproven claim never on screen; a broken stream asked again in one piece; Stop clears it), and its independent review is running. It goes into the repo when that review is applied. `reply_drafts.py` and `test_reply_drafts.py` are in the tree already and belong to it.
  **Also in the tree, not in this commit:** version 3 of the VM check driver (`tools/guest/stage7-v3`, `tools/host/stage7-v3`) for the two incidents of the 1.0.14 check (the Z: drive, the restart check), with its decision tests. It gets its own commit and entry.

- **2026-10-06, about 02:00 local (Fable 5.1, same session): scope item 5 (speech through Qwen as well) built, reviewed and committed.** `docs/SPEECH.md` is the record. **One setting, Settings > AI > Speech recognition:** on this PC (the default, unchanged) or in the cloud by the chosen AI provider (Qwen `qwen3-asr-flash`, or OpenAI). With the cloud choice the recording of each command goes to that provider; if it refuses, cannot be reached, answers something that is not text or takes more than 8 seconds, this PC does it and the microphone diagnostics say why. Never the cloud while the emergency stop holds, never for another device, and the voice lab page is always this PC. The window's microphone uses the new route `POST /api/speech-to-text`; the older `POST /api/transcribe` (it sent any recording to the cloud whatever the setting) is removed. **Owner-run tool `tools/host/Test-QwenVoice.ps1`:** without a switch it lists the cloned voices on the Alibaba account of the key file, says which one the key file names and makes a short spoken test saved as a sound file; with `-Enroll <recording>` it creates a cloned voice (after the owner types YES: Alibaba charges a small amount) and prints the `QWEN_TTS_VOICE=...` line. It says so when a Windows variable holds a different key than the key file.
  **Independent review (one reviewer): 2 high, 3 medium, 5 low, all applied** (section 4 of the record). High: the voice lab page would have sent recordings to the cloud while saying it did not; a slow provider would have blocked voice (no wake word, no spoken stop) for one to two minutes. Also from the review, older than this item: **a provider request that carries a key is now ended by a redirect answer instead of being sent on, key included, to the address it names** (`providers._KeysStayPut`). The fixes were not reviewed again.
  **Nothing here was tried against Alibaba or OpenAI** (no request left this PC; the request shapes are from Alibaba's help pages, read through a summary). Not known: how well Qwen recognises the owner's voice next to the local recognition, which is told the name "Jarvis" in advance. The owner's first run of the voice tool and the first spoken command with the cloud choice are the real test.
  **Tests on the development tree: 555 Python, 52 desktop, 18 Intelligence, 23 interface scripts pass;** the voice tool passes 37 of 37 checks against a local stand-in with a made-up key (`tools/host/check_qwen_voice_tool.py`).
  **One test error, once:** in one full run a test's request ended as a broken connection (WinError 10053) and the run reported 1 error; the same tree passed on the rerun and the suspected tests passed 12 times in a row. The likely cause on Windows: the Core refused a POST and closed the connection with the request's body still unread. A refused POST now has its unread body thrown away first (`Handler.discard_body`, also at the device and wearable doors), so the client can read the refusal. Which test it was is not known (the output was cut), so that this was the cause is not proven.
  **Count: 5 of 8.** Next: item 6 (automatic backups; the wiring and its tests are prepared), 7 (answers without the internet; prepared), 8 (replies that appear while written: the largest; planned behind a setting that is off by default, for Qwen first).
  **For the owner, when wanted (jonny account, PowerShell):** `powershell -ExecutionPolicy Bypass -File C:\Users\jonny\JARVIS-claude-workspace\repo\tools\host\Test-QwenVoice.ps1` shows whether a Qwen voice exists on the account.

- **2026-10-06, after midnight (Fable 5.1, same session): scope item 4 (devices) built, reviewed and committed.** `docs/DEVICES.md` is the record. A device pairs with an eight-digit code the owner reads from the PC (Settings > Devices > PAIR A DEVICE; good for five minutes and one use), gets a key of its own (only a keyed hash is stored, bound to this installation by a secret in the config folder, `.env.device-secret`), says what it has (microphone, camera, speakers, display) and may use only what the owner ticks. A paired device asks questions and reads; it changes nothing saved; any paired device can stop everything and none can resume. REVOKE refuses its key from the next request on and cancels what it was running; revoked devices are also remembered beside the secret, so an older copy of the database does not bring one back. The routes are `POST /api/device/<op>` (`device_gateway.py`), the owner's are `GET/POST /api/devices`. The same-PC test client (`/api/wearable/`) is always listed as simulated: a client can no longer declare itself real. The dashboard's three places are filled by kind; the stop banner and the activity log name the device; "Meta glasses" reads "Halo glasses". **It opens no port: the Core still listens on 127.0.0.1 only, so today only a program on this PC can pair.**
  **Independent review (one reviewer): no high finding; 5 medium and 7 low, all applied** (section 8 of the record). The medium ones: a device's stop could be turned away (now handled before anything else); the panel froze after RENAME; an older database copy revived a revoked device; the check of a proposed style sheet (from the previous commit) could be got around, so it was tightened (every number in a known unit and range, variables hold colours only, no attribute selectors; `docs/PERMISSIONS.md` section 4) and Undo is never refused; the glasses test client refused a WAV voice. The fixes were not reviewed again.
  **Tests on the development tree: 539 Python, 52 desktop, 18 Intelligence, 23 interface scripts pass.** Seen working in the sandbox window (synthetic data, blank provider keys): pairing with the code, tick boxes, a device's stop with its name in the banner, the device's name in the activity log, RENAME with CANCEL and SAVE, a double click on REVOKE not revoking, REMOVE FROM LIST. Not checked: a real phone or glasses, real audio from the glasses test client, the panel at full window size, the desktop app.
  **Prepared for the next items and NOT committed with item 4:** `tools/host/Test-QwenVoice.ps1` (owner-run: lists the cloned voices on the Alibaba account, makes a spoken test, and with `-Enroll <recording>` creates a voice; checked against a local stand-in with a made-up key by `tools/host/check_qwen_voice_tool.py`, 27 of 27; never run against Alibaba). Committed with item 4, because it only tests a draft that was already in the repo: `test_offline_answers.py` (10 tests of `offline_answers.py`, which nothing calls yet).
  **Count: 4 of 8.** Next: item 5 (Qwen speech recognition behind one setting, plus the voice tool above), then 6, 7, 8.

- **Night of 2026-10-05 into 2026-10-06 (Fable 5.1): scope item 3 finished and committed; owner decision D1.** (The session opened in the old OneDrive handover folder and was moved to the repo. The owner pasted all handover summaries; their word "ultracode" again switched multi-agent mode on by mistake; no workflow was started. Single reviewer agents were used.) Release 1.0.15 is still not built; the everyday JARVIS was not touched; nothing pushed.
  **Owner decision D1: "ask first"** (the owner's words, 2026-10-05 23:40 local, after asking "what do you recommend"): every change JARVIS makes to its own personality or style asks first. That is how it was already built; recorded in `docs/PERMISSIONS.md` section 6, `docs/CAPABILITY-PLAN.md` and the scope list. It settles D1 only; the capability plan is still a proposal.
  **Item 3 (permissions in one place): the 16 findings of the first review are applied, that work was reviewed again by one reviewer (no high finding, 2 medium, 7 low), and those are applied too.** `docs/PERMISSIONS.md` sections 9 and 10 say where each one was fixed. What changed for the owner: the stop words work from the dashboard's ask box while JARVIS is busy and ignore capitals and punctuation (but "stop all 3" is not a stop); **the wake word stays alive while JARVIS works on an answer, so "Hey JARVIS" now interrupts a thinking JARVIS and a spoken "emergency stop" is heard then** (logic tested; not tried with a real microphone); the commands the window answers by itself ("open settings", the microphone words, "inspect the settings page") obey the Off and Ask first switches and the stop; while stopped the interface's own internet buttons are refused, nothing can be stored for approval and no question can slip in; a wearable's stop words are never turned away; the tray's Emergency stop and Resume say so when the Core did not answer; **a style change JARVIS proposes may set only colours, fonts, text size, spacing, borders and shadows** (this limits a style change, it is not a guarantee: said so in the record); **an installation that still holds the untouched personality text of an earlier release gets the running release's wording** (`runtime_paths.SHIPPED_PERSONALITIES`: add the new hash whenever `personality.txt` changes, a test fails until then), so the everyday JARVIS will get the "changes to itself ask first" wording with the update while a personality the owner really changed stays.
  **Also done:** the real-size connection test is offered (Settings > Developer > Connections & action review > "Real-size question", `App.full_question`: the full instructions and every tool, no chats, saved facts or files); a named page file that is missing answers "not found" instead of "500"; the fixed "CORE LINK NOMINAL" is gone (the line shows the real link state). The third old reviewer note (stale values when the connection is lost) is covered by the strip every section shows. `tools/host/jarvis-request-*` regenerated (the `open_app` description and the paragraph about `owner-style.css` changed).
  **Tests on the development tree: 512 Python, 52 desktop, 18 Intelligence, 23 interface scripts pass.** Sandbox preview Core (synthetic data, both provider keys blank) used for: a section command going to the Core when its switch is Off, the stop controls staying visible under a style sheet written to hide them, the internet routes refused while stopped, the new test card. Not checked: the running desktop app (tray dialogs), anything through a real microphone, the Settings layout at full window size (only element sizes in the small preview pane).
  **For the release notes and the update plan of 1.0.15:** after a rollback to 1.0.14 the emergency stop and the switches are not enforced (that program does not know the two tables); "Hey JARVIS" interrupts a thinking JARVIS.
  **Next, in this order (item 4 is done since: see the entry above):** (1) ~~item 4, devices~~; (2) items 5, 6, 7, 8, each built, tested and reviewed; (3) regenerate `tools/host/jarvis-request-*` after any change to the tools or the instructions; (4) the version 3 Stage 7 guest driver, release notes, build and checks. Tell the owner when it is 8 out of 8. Still open on the old list: the Alibaba "maintenance mode" check; the new header checked in the desktop app itself.
  **Other JARVIS chats are still open and idle on this PC** (seen in the session list); the owner was asked to keep JARVIS work in one chat so that two chats do not change the same files.

- **Late night of 2026-10-05 (Fable 5.1). Stopped on the owner's word: "commit all chnages now and come to a stop".** Release 1.0.15 is still not built; the everyday JARVIS was not touched; nothing pushed. (The session opened in the old OneDrive handover folder and was moved to the repo. The owner pasted all handover summaries; their word "ultracode" again switched multi-agent mode on by mistake; no workflow was started. One reviewer agent was used.)
  **Owner's instruction for the 1.0.15 list: "let me know when it's 8 out of 8".** Where the eight items of `docs/RELEASE-1.0.15-SCOPE.md` stand: 1 and 2 built and reviewed (earlier); **3 built, tested and reviewed, review findings NOT applied** (applied since: see the entry above); 4, 6 and 7 started in files that nothing loads; 5 and 8 not started.
  **Owner's key-source run (`Test-KeySources.ps1`): the Windows variable `DASHSCOPE_API_KEY` and the key-file line hold the SAME value**; 16 names are only in the key file. JARVIS and the owner-run checks use one Qwen key; no decision is forced.
  **Scope item 3, permissions in one place (`docs/PERMISSIONS.md`):** one table of all 45 tools (`permissions.py`: reads or changes, what it reaches, undo, asks first, done-twice, wearable) and one decision in `server.App.tool`; the four lists other modules kept are read from it. The owner's switch for each tool in a new Settings > Permissions category (Allowed, Ask first, Off; saved in the database, out of reach of settings, export and import). **The emergency stop now holds**: `POST /api/emergency-stop` cancels everything, drops waiting approvals, is saved (survives a Core restart) and refuses questions, tools and approvals until `POST /api/resume` from the signed-in interface on the PC; shown as a red banner in every section and on the dashboard; STOP ALL under the header; the tray (Emergency stop, Resume JARVIS), the shortcut and the floating JARVIS's STOP ALL use it; the words "emergency stop" / "stop everything" / "stop all" / "kill switch" as a whole message stop from any device. `POST /api/cancel-all` is unchanged (momentary). **JARVIS changing itself:** every change asks first, the personality and the style included; the owner's two files (`personality.txt`, new `owner-style.css` served at `/owner-style.css` and loaded last) live in the config folder; an installed JARVIS never writes its program files (a change to one is saved as a proposal only); proposals are kept with the data. Activity rows carry the question and the device (`audit.run_id`, `audit.device`); the activity log shows them. The exact memory commands of `memory.py` obey the same switches. The instructions the model gets and the shipped `personality.txt` no longer say style and personality apply without approval; `tools/host/jarvis-request-*` regenerated (`make_request_template.py` now takes the paragraph from `development.guidance`).
  **Independent review of item 3 (one reviewer, stopped early on the owner's word): no high finding; 2 medium and 14 low, NOT applied.** Medium: (1) the stop words are not accepted by the dashboard's ask box while JARVIS is busy, and a spoken "emergency stop" is not heard while JARVIS is working on an answer; (2) commands the window answers by itself ("inspect the settings page", microphone and hologram words, "open settings") are outside the Off and Ask first switches. All findings with their fixes: `docs/PERMISSIONS.md` section 9.
  **One contradiction for the owner (decision D1 of the capability plan; decided since, "ask first": see the entry above):** the shipped `personality.txt`, `DESKTOP-ARCHITECTURE.md` and `test_automatic_actions.py` recorded that style and personality changes apply WITHOUT a prompt, "as authorized by Mr. Teague"; the master document and the 1.0.15 list say such changes ask first. Built: ask first for both. If style changes should apply at once again, that is a small change.
  **Also done:** plain messages for HTTP 413 and `AccessDenied.Unpurchased` (`providers.py`); the Settings Save bar no longer floats over a row and the rows under Settings > AI are spaced (`static/horizon.css`); a real-size connection test in the Core (`connection_checks.check('full', ...)`, not yet offered in Settings); backups and the switch-over carry `owner-style.css`.
  **Started and NOT connected (the files are inert until wired):** item 4 `devices.py` (7 tests), `device_gateway.py` (calls `wearables.service.Service` with arguments that class does not take yet), `static/devices.js`, `static/devices.css`, `test_devices_view.cjs`; item 6 `auto_backup.py` (14 tests); item 7 `offline_answers.py` (no tests).
  **Tests on the development tree: 487 Python, 52 desktop, 22 interface scripts pass.** Sandbox preview (synthetic data; `.claude/launch.json` now blanks both provider keys) was used for the stop, the banner, an ask-first approval and the Settings pictures; it is stopped. Pictures: `docs/design/permissions-preview-*.png`.
  **Next, in this order:** (1) apply the review findings of item 3, the two medium ones first; (2) offer the real-size connection test in Settings, answer "not found" instead of "500" for the missing `command-background.png`, replace the fixed "CORE LINK NOMINAL"; (3) finish item 4 (connect the device book and the device routes in `server.py` and `wearables/service.py`, the Devices category in `static/teague.js`, "Halo" wording, tests of the whole path, review); then items 5, 6, 7, 8, each built, tested and reviewed; (4) regenerate `tools/host/jarvis-request-*` after any change to the tools or the instructions; (5) the version 3 Stage 7 guest driver, release notes, build and checks. Tell the owner when it is 8 out of 8.
  **Found while working (for the next session):** the byte-exact edit helper used here gave every line of a replaced block the line ending of the block's first line (four existing lines of `store.py` changed style); `static/teague.js` groups Settings into categories, so a new panel needs its category in that list; the Browser pane shrinks the page, so real pictures were taken with Playwright and Edge; the Core must be opened at `127.0.0.1`, not `localhost`.

- **Night of 2026-10-05, same session: the owner's speed run, and "implement everything that we havn't done into 1.0.15".**
  **Speed run (owner, `Test-AiSpeed.ps1`, real providers, one sample each):** the key file says `JARVIS is set to use: qwen`, so the everyday JARVIS is on Qwen. A 150-word answer: `gpt-6-astra` 7.2 s; `qwen3.8-max` as JARVIS asks it today 11.9 s (297 of 485 output tokens were thinking); `qwen3.8-max` with thinking off 5.8 s; `qwen3.8-flash` with thinking off 5.8 s. A tool question: 2.3 / 3.1 / 3.4 (that line was cold: thinking off is counted as a different request, 8,531 against 8,567 tokens) / 2.0 s. So the wait is mostly Qwen's default thinking; flash is cheaper, not faster.
  **Built on that (repo only):** Settings > AI > "Answer speed (Qwen)": Deep (thinking before every answer; sends exactly the request 1.0.14 sent), Auto (thinking off, on when the user's own words ask, e.g. "think hard about ..."), Economy (`qwen3.8-flash` for everything except pictures; "think hard" still gets the main model). `providers.qwen_plan`, setting `answer_mode`, `test_answer_mode.py`; 393 Python, 52 desktop, 20 interface scripts pass; the setting was saved, reloaded and reset in the sandbox Core. Independent review (one reviewer): no high finding, 3 medium, 4 low, all applied: **the default is Deep, that is unchanged behaviour, until the owner says yes to Auto (decision D3; asked, not yet answered; the exact words offered were "auto default")**; labels, the health check and the Settings chat test name and test the model that answers in the saved mode; an empty `QWEN_FAST_MODEL` line, an unknown stored value and the JSON backup are handled; wider and negation-aware "think hard" wording; three tick boxes in Settings that were drawn large and away from their labels now sit beside them.
  **Second speed run (owner, the version with a picture, all lines warm):** written answer `gpt-6-astra` 8.7 s, `qwen3.8-max` with thinking 16.9 s (604 of 795 output tokens thinking), without 6.2 s, `qwen3.8-flash` 7.2 s; tool question 2.9 / 3.4 / 3.0 / 7.3 s; **picture: `gpt-6-astra` 3.9 s, `qwen3.8-max` with thinking 7.1 s, with thinking off 5.6 s, so Alibaba accepts "thinking off" together with an image on this account** (`providers.QWEN_PICTURES_WITHOUT_THINKING = True`; Auto and Economy use it for pictures).
  **Scope item 2, built the same night (repo only):** a backup provider. Setting `provider_backup` (Settings > AI, a tick box): when the chosen provider refuses a question or cannot be reached, and no tool has run in the question yet, the other provider (OpenAI or Qwen, if its key is in place) answers it, the reply ends with a bracketed note saying who answered and why, and the rest of that question stays with the backup. **On by default on the owner's word: "backup on" (2026-10-05).** `providers.backup_provider`, `backup_worthy`, `chat(..., use=)`, `test_provider_backup.py` (28 tests); 421 Python, 52 desktop, 20 interface scripts pass. Independent review (one reviewer): 1 high (after a provider that hung for most of the question's 120 seconds, the backup could run a tool and then be cut off as "time limit exceeded", so the owner would repeat a question whose action had already happened: the backup now gets its own 120 seconds), 3 medium (the note was sent back to the model on later questions and could be imitated: it is now removed from what a model receives and from what a model writes; a missing key or picture model or a reply cut short no longer triggers the backup; a failure after the takeover now says the backup had taken over) and 6 low, all applied except a shorter spoken form of the note. The tick box says that the question, recent conversation, saved facts and any picture then go to the other company, and shows whether a backup is available; a restored JSON backup cannot change the setting.
  **Found while checking that tick box: Windows holds a user-level environment variable `DASHSCOPE_API_KEY` in the owner's account (presence checked only, never the value; no such variable for OpenAI or `JARVIS_PROVIDER`).** `server.load_env` keeps what is already set (`os.environ.setdefault`), so **that Windows variable wins over the `DASHSCOPE_API_KEY` line in the key file**, in the everyday JARVIS as well as in the sandbox preview Core (which the records called "no keys": it inherits this one; no AI request was sent from it, its provider is OpenAI without a key). `Test-AiKeys.ps1` and `Test-AiSpeed.ps1` read the key file, so they may test a different key from the one JARVIS uses. Whether the two keys are the same is not known and Claude cannot look. Put to the owner with a new owner-run check, `tools/host/Test-KeySources.ps1` (names and the words SAME or DIFFERENT only, never a value; tested with a made-up key file on every branch; not independently reviewed). **Waiting for the owner's run.** If it says DIFFERENT, JARVIS has been answering with another key than the one the owner edits and the check scripts test; which one should win, and whether the key file should win in 1.0.15, is then the owner's decision.
  **Owner, with the master architecture PDF (same text as `docs/owner/JARVIS-MASTER-ARCHITECTURE.md`): "implement everything that we havn't done into 1.0.15."** The working list is `docs/RELEASE-1.0.15-SCOPE.md`: eight items buildable on this PC in order (1 Qwen roles and speed, built; 2 OpenAI and Qwen as each other's backup; 3 permissions in one place with the self-editing fix and an emergency stop that holds; 4 device registry, pairing, revoke and a Devices panel; 5 Qwen speech recognition and a voice enrolment tool; 6 automatic backups; 7 offline answers when Ollama is installed; 8 replies that appear while written), what cannot be finished without the owner (iPhone app, remote access, Halo, Wi-Fi discovery, Tesla, hardware), and the earlier 1.0.15 list. The owner can say "build 1.0.15 now" at any point. The code survey behind it is `docs/DEVICE-SURVEY-20261005.md`. The owner was also sent five pictures of the current interface (sandbox Core); a layout fault seen in Settings (three tick boxes drawn large and away from their labels) is on the list.
- **Late evening of 2026-10-05 (Fable 5.1; the session opened in the old OneDrive handover folder and was moved to the repo; the owner's pasted summaries again contained the word "ultracode", which switched on multi-agent mode by mistake; no workflow was started).** Three things, all in the repo only; release 1.0.15 is still not built and the everyday JARVIS was not touched.
  (1) **Owner: "read all these chats"** (the eight earlier chats, about 10,400 messages). Read in full by eight single reader agents; what they contain that the records had lost is in `docs/CHAT-REVIEW-20261005.md` (open owner questions, work that dropped out of the handoffs, corrections such as: drive E: holds no JARVIS data backup; the old JARVIS was not left wholly untouched; Claude's own advice of 2026-10-02 about Codex's runtime folder was wrong).
  (2) **The capability plan the owner asked for ("plan") is written: `docs/CAPABILITY-PLAN.md`, a PROPOSAL waiting for the owner** (seven stages with stage 1 in detail, the installer as the release after 1.0.15, six decisions D1 to D6; approval wording "I approve the capability plan").
  (3) **Owner, with a screenshot of a slow screen analysis: can OpenAI and Qwen work together, and "the qwen api doesn't just offer the qwen 3.8 max it has others lets use them".** Found: JARVIS uses one provider and one model for everything with no fallback; Alibaba lists `qwen3.8-max` and `qwen3.8-flash` as thinking by default and JARVIS's Qwen adapter never sets `enable_thinking`, so every Qwen answer thinks first; replies are shown only when complete; `qwen3.8-flash` costs about a thirteenth of max (0.15 / 0.47 against 2.00 / 6.00 USD per million). Proposal in section 3 of the plan (fast Qwen for everyday questions, max with thinking for hard ones, OpenAI as the backup when Qwen refuses, one visible Fast / Auto / Deep setting), to be settled with numbers. **New owner-run tool `tools/host/Test-AiSpeed.ps1`** (same key handling as Test-AiKeys; times the same full JARVIS question on OpenAI, Qwen as JARVIS asks today, Qwen with thinking off, and `qwen3.8-flash`; about 11 requests, well under one US dollar). Tested against a local stand-in with made-up keys (normal run, a refused model with a key echoed in the error, a failed first request, a request that never answers, a cut-short answer, one provider only, no keys, no file, five addresses that must be refused); the real providers are untested until the owner runs it. Independent review (one reviewer): no high finding, 3 medium (an `http://` Model Studio address was accepted, so the Qwen key could have gone out unencrypted, the same gap in `Test-AiKeys.ps1`; one failed warm-up dropped the "thinking off" line; reused connections and an `Expect` header made the times unlike JARVIS's) and 7 low; all applied to both scripts the same evening except one recorded and left (any `*.aliyuncs.com` host is accepted, the same rule as `providers.py`). **Waiting for the owner's run and a photo of the window.** Whether the everyday JARVIS is on Qwen now is not confirmed (the owner's question suggests it).
  **Added to the 1.0.15 list from the chat review:** plain messages for HTTP 413 and `AccessDenied.Unpurchased`; a full-size connection check in Settings; whether Alibaba's "maintenance mode" notice touches `dashscope-intl`; three reviewer notes never acted on (`static/teague.js:37` prints a fixed "CORE LINK NOMINAL"; `command-background.png` is named in the code but missing from the repo; other sections keep old values when the connection is lost).

- **Where the evening session of 2026-10-05 stopped (owner: "Stop when your done with what your doing").** Release 1.0.15 is not built yet. In the repo since the bullet below: the graphics pass (df0bbfa: rings around the core that carry the six system states, a day-and-night world map, a device network picture, a performance graph, a day line), formatted chat replies and the new section names by voice (83446f3), and the fixes for the independent review of 5f2ed59 (no high finding, 14 medium and low; `docs/design/NEW-LOOK.md` lists each). What may be claimed on screen is now one tested file, `static/dashboard-model.js`. **Owner's Test-AiKeys run (photo, same evening): `openai HANDLES IT` and `qwen HANDLES IT` (qwen3.8-max, 8,567 prompt tokens): Qwen works; the owner was given the two key-file lines to switch (`JARVIS_PROVIDER=qwen`, `QWEN_VISION_MODEL=qwen3.8-max`); whether the switch was made is not known.** The owner's plan limits changed during the session (weekly Fable 81% -> 5% used), which fits an upgrade to the larger plan.
  **Asked for by the owner and not started:** (1) "plan": a staged capability plan (measure, memory, dependable tools, lasting plans, bounded autonomy, sandboxed self-improvement, resources kept manual) as a new document for approval; the survey of what exists is saved in `docs/CAPABILITY-SURVEY-20261005.md`, with two findings to put to the owner first (JARVIS can change `personality.txt` and `static/pro.css` with no approval, and those tools act on the installed release folder). (2) A real installer, `JARVIS-Setup.exe`, proposed as the release after 1.0.15. (3) A start-up song: the owner asked how; offered a file version (`startup song`) or a Spotify version (`spotify song`, needs Premium and a remembered sign-in); no choice made yet.
  **Still to do for 1.0.15:** the version 3 Stage 7 guest driver (incidents 01-02), the release-notes entry (tell owners on groq to change the line; the new look; formatted replies), a look at the new header in the desktop app itself (drag area, eight sections at 1280), build, comparison, regression, zip install, sandbox Stage 7, then the VM check and the everyday update (each on the owner's approval). The sandbox preview Core (port 8799, synthetic data) may still be running as a background command of that session.
- **New look for the whole interface, and the ten review fixes (2026-10-05, evening).** Owner, with four pictures: "both and use this as a guide I want the whole interface to have this new design and be more organised". Built in 5f2ed59: a shell for every section (`static/horizon.js`, `horizon.css`: new JARVIS mark, one-row header, sections grouped as eight everyday ones plus More, command search, version strip, stars and Earth horizon), the dashboard's second layout (`static/command-dashboard.*`: greeting, recent activity, performance rings, core with mode lights and systems list, suggestion chips, ask bar, core overview, projects, schedule, quick tools), and all ten review findings fixed (two in the Core: `completed` recorded with each reply timing; the inspection renderer serves every file the page loads, with a test). Real data only: no weather, world map or mail counts. Record with every panel's source and where each finding was fixed: `docs/design/NEW-LOOK.md` (the owner's four pictures and preview screenshots are beside it). Checked in the sandbox Core at four window sizes; 370 Python, 52 desktop, 17 interface scripts pass. The owner has been sent three preview pictures. The independent review of 5f2ed59 finished and its findings are applied (bullet above).
- **Command dashboard for 1.0.15 (2026-10-05), first layout (superseded by the bullet above).** Owner: "can we apply this new and improved version of jarvis's interface into the application" (concept `docs/design/command-dashboard-concept-20261005.jpg`), decisions "Same look, real data only" and "In 1.0.15". Built in 39901c5 (`/api/metrics`, `system_metrics.py`) and 5d0c96d (`static/command-dashboard.css/.js`, devices in `/api/state`); design and as-built notes `docs/design/COMMAND-DASHBOARD.md`; checked in a sandbox Core (`D:\JARVIS-release-work\dashboard-preview`, synthetic data, no keys, port 8799, `.claude/launch.json`) at three window sizes; 369 Python tests and 17 interface scripts pass. Owner has seen the 1920x1080 preview screenshot; on the owner's "get rid of this" the centre title was removed (f7776df). **Independent review finished: ten findings, not yet applied** (listed in `docs/design/COMMAND-DASHBOARD.md`). **The owner then showed four images of a new look** ("I want it to have this look"; seen, not started; the images are not saved in the repo). **Waiting for the owner's choice: apply the review fixes, start the new look, or both.** The sandbox preview Core (port 8799, synthetic data in `D:\JARVIS-release-work\dashboard-preview`) was still running at the start of the next session (left running for the dashboard work; started by the earlier session, so `preview_stop` in a new session does not list it). New session 2026-10-05 (Fable 5.1, opened in the old OneDrive handover folder and moved to the repo; the owner's pasted summaries again contained "Ultracode is off", which switched on multi-agent mode by mistake; no workflow was started).
- **Release 1.0.15 in progress (2026-10-05).** Owner: "let's get rid of any api's that aren't fish audio , openai or gwen", then chose "Groq, Gemini, ElevenLabs" (search, YouTube, Maps and Spotify stay). Done in 402ecef: JARVIS_PROVIDER is `openai` (default) or `qwen`, anything else refused with a plain message; Groq streaming and cooldown, the Gemini adapter and setup helper, ElevenLabs speech removed; an old ElevenLabs voice choice reads as automatic; a Qwen-only key file no longer falls into local command mode; status panel shows QWEN VOICE, "not configured" no longer shows CONFIGURED; Test-AiKeys checks OpenAI gpt-6 with a full JARVIS question (Responses API) and no longer overstates what one question proves; 362 Python tests pass. Independent review: no high findings, 1 medium (an unsupported provider with only its own key fell into local command mode) and 7 low, applied in ee60dd6 (364 Python tests pass; `.env.example` still lists the removed names: reading it is blocked by the workspace read rules, it is not shipped). The owner's Test-AiKeys run: `openai HANDLES IT` (gpt-6-astra, 6,358 prompt tokens); Qwen still `Arrearage` at 17:31; Alibaba ticket 00654718FGN opened 17:41 (first reply: billing sync delay, wait, then ask for an engineer). **The everyday JARVIS (1.0.14) now answers on OpenAI** (owner's screenshots, 17:45: a long answer with tool evidence and the spoken reply starting). Seen there: answers show raw Markdown markers (`**bold**`, numbered lists) because the conversation panel prints plain text; a candidate fix, not started. "Analyse my screen" also works on OpenAI (17:49, 7.2 s); its screen label showed three broken characters since the original baseline, fixed in 2c152ff (52 desktop tests pass). Alibaba's AI assistant could not resolve the ticket; the owner was told to use "Transfer to a human". Still to do for 1.0.15: a version 3 Stage 7 guest driver (incidents 01-02), the release-notes entry, build, comparison, regression, zip install, sandbox Stage 7, then the VM check and the everyday update (each on the owner's approval). **Owner's key file:** JARVIS_PROVIDER must say `openai` or `qwen` before the update to 1.0.15; the Groq, Gemini, ElevenLabs and Anthropic lines can go once OpenAI works (owner deletes them; Claude never edits the key file). OpenAI credit balance $36.34, auto-reload off (owner's screenshot).
- **AI provider (2026-10-05): owner decision "i want qwen to be the api we use" (and "let's not minimise or make jarvis less").** After the update JARVIS answered with Groq HTTP 413: one JARVIS question is about 12,000-13,000 tokens (instructions plus 45 tools), Groq's free tier allows 8,000 per minute and 200,000 per day; OpenAI has no credits, Gemini's prepay is used up, Qwen refused with AccessDenied.Unpurchased because the Alibaba account has an **overdue September bill of 25.08 USD**. Plan docs/AI-PROVIDER-PLAN.md: qwen3.8-max for thinking, tools and vision (about $28 a month at 50 questions a day with the cache), Fish Audio voice and local Whisper unchanged; Token Plan ruled out (coding tools only), and no other subscription is worth it (Savings Plan from USD 150 a month; small prepaid plans give no discount). `tools/host/Test-AiKeys.ps1` now sends each provider an exact JARVIS request (instructions, 45 tools, JARVIS's settings; `tools/host/jarvis-request-*` from make_request_template.py). **The owner paid the overdue bill (2026-10-05, repaid 13:17 console time; console shows available credit 0.00 USD, account valid); about 30 minutes later Qwen still answered `Arrearage` (wait, then an Alibaba ticket).** Stopgap (owner, same afternoon): **OpenAI until Qwen works** ("i'll just use the openai one then when qwen is up i'll fully switch to qwen"; Claude and OpenRouter were considered and dropped, see the plan). The owner also wants the Qwen cloned voice instead of Fish (needs a voice ID on the current Alibaba account). Fix in 1.0.15: Test-AiKeys says a provider "handles a full JARVIS request" from one request without history (misleading for Groq's free tier). **Next, owner:** set a budget alert, run Test-AiKeys; then Claude gives the two key-file lines (`JARVIS_PROVIDER=qwen`, `QWEN_VISION_MODEL=qwen3.8-max`). Next release (1.0.15): plain messages for HTTP 413 and AccessDenied.Unpurchased; full-size connection check in Settings.
- **Everyday JARVIS updated to 1.0.14 (2026-10-05, `EVERYDAY_UPDATE_COMPLETE`).** Steps 1-5 of
  `docs/UPDATE-EVERYDAY-1.0.14.md` all PASS, every step run by the owner: check; backup de3c17ea… (331 files, 1,150
  messages, test restore passed, copy on D:); update in 130 s with the database byte-for-byte unchanged; the owner's
  check (version, memories, AI, voice, quiet quit); and after a PC restart JARVIS started by itself from the Startup
  shortcut, about 6.5 minutes after sign-in (Windows' scheduling of Startup-folder apps; a faster start would need a
  Run key or logon task, an owner decision). 1.0.11 stays installed as the rollback copy. Records
  `D:\JARVIS-update-1.0.14\evidence\` (manifest d75e96e0…), repo copy `docs/update-1.0.14-evidence/`. **Next, each on
  the owner's word:** a version 3 Stage 7 guest driver fixing incidents 01-02 (before the next release check);
  after a trouble-free period, the cleanup (test VM, data copies on D:, old folder and Codex, the 1.0.11 release
  folder, `%LOCALAPPDATA%\JARVIS-package`); then the roadmap (`docs/ROADMAP.md`).

- **Release 1.0.14 (2026-10-05, owner: "use this session go"; 1.0.12 and 1.0.13 superseded, never offered).**
  Build **`1.0.14-e03872680e1d`** (commit e038726; `D:\JARVIS-release-work\release\`, zip sha256 `ceb7d9e1...d8d3`,
  525,633,503 bytes; package folder `D:\JARVIS-release-work\pkg-1.0.14`). On this PC: compared with 1.0.11 (the same
  10,645 files, 14 source files changed, pinned inputs identical); release regression PASS (373 Python with 1
  expected skip, 52 desktop, 18 Intelligence, 17 scripts); zip install PASS (uninstall while running: all files
  removed, nothing left running); **the sandbox Stage 7 pass 1.0.11 -> 1.0.14 ALL PASS** (13.4 min, incl. the
  interrupted update). Records: `docs/release-rehearsal-20261005-1014/README.md`. On the way: the installer change of
  eb620cd got its independent review (the one started before the session restart had been interrupted; rerun here):
  2 medium + 6 low findings, applied in 6d4ff85 except one recorded limit. 1.0.13 (6d4ff85) then failed its release
  regression twice on a real race: "Quit JARVIS completely" could return while the Core process still ran and still
  answered on an open keep-alive connection (reproduced; fixed in e038726, reviewed, new tests
  `desktop/test/shutdown-wait.test.cjs`; records `docs/release-rehearsal-20261005-1013/README.md`). Version 2 Stage 7
  scripts: the guest's last message now names the snapshot step before "stage 7 done"; decision tests 17 + 8 PASS with
  the 1.0.14 label. **Owner approved the check** ("I approve the Stage 7 check of 1.0.14", first clock reading
  2026-10-04T14:59:02Z; record `../governance/STAGE7-1.0.14-APPROVAL-RECORD.json`, plan sha256 913988c1..., repo copy
  `docs/stage7-1.0.14-evidence/`). Claude placed the tools in `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.14\` (six files,
  each hash equal to the approval) with `stage7-authorized.json` (schema v2, expected current snapshot STAGE7-PASS) and
  created `D:\JARVIS-stage7\1.0.14-e03872680e1d\evidence` (approval copy, `prep-tools-hashes.txt`) and the empty guest
  folder `guest-egress-01\stage7-1.0.14-e03872680e1d`; launcher dry run: jonny -> build the disc, jarvis-s6-val -> "next
  step is in jonny". **Stage 7 check of 1.0.14: `STAGE_7_COMPLETE` (2026-10-05T03:35Z; 27 of 27 checks)** — disc built by
  the owner and checked (iso 92b58b9a…); VM pass Install, AfterRestart, Uninstall, Update, Interrupt all PASS; timings
  inside the Gate 20 bounds (max 352 s, stops about 3 s); snapshot STAGE7-PASS-1.0.14-e03872680e1d `0b7c12fa…`
  (current, every older snapshot kept). Two script defects of the version 2 guest driver, each recorded with the
  owner's way forward: incident 01 (Z: used before it is mounted; owner decision A: `net use` by hand before each
  start) and incident 02 (uptime restart check refused a real restart made 77 minutes earlier; restarted again and
  started at once). The VM was also suspended overnight by the host's sleep between Install and the restart step (no
  effect). Result `D:\JARVIS-stage7\1.0.14-e03872680e1d\evidence\stage7-evaluation.json`, manifests 93a71864… (PC) and
  df9e417d… (guest), repo copy `docs/stage7-1.0.14-evidence/`. Fix both defects in a version 3 copy before the next
  release check. **Next:** the update of the everyday JARVIS to 1.0.14, plan `docs/UPDATE-EVERYDAY-1.0.14.md` with
  launcher `tools/host/Invoke-EverydayUpdate.ps1` + `update-step.cmd` (check, backup with its own backup code, update,
  rollback only on the owner's word); sandbox rehearsal 13 of 13 PASS (`docs/release-rehearsal-20261005-1014/update-rehearsal/`); plan **approved by the owner** ("I approve the update of my everyday JARVIS to 1.0.14", first clock reading 2026-10-05T03:39:06Z; record `../governance/UPDATE-1.0.14-APPROVAL-RECORD.json`, plan sha256 9eddc20c…); launcher placed in `D:\JARVIS-update-1.0.14\tools\` with `update-authorized.json` (hashes equal the approval; repo copy `docs/update-1.0.14-evidence/`). **Steps 1-3 PASS (2026-10-05, 03:42-03:48Z): the everyday JARVIS is 1.0.14-e03872680e1d** (backup de3c17ea… 331 files, 1,150 messages, test restore passed; update 130 s, verified, database byte-for-byte unchanged, 1.0.11 kept as rollback). Step 4: the owner reported "all checks passed no core stopped box popped up" (`owner-check.json`). Step 5 PASS: after a PC restart JARVIS started by itself (`restart-check.json`). **`EVERYDAY_UPDATE_COMPLETE`** (`update-evaluation.json`). Owner: will use the
  everyday JARVIS again once it is on 1.0.14.
- **Release 1.0.12 (2026-10-04, on the owner's "next move" / "now do the next move"; superseded, see above).** The fix list
  `docs/POST-CUTOVER-FIXES.md` items 1-6 fixed (status table at the end of that file; item 7 partly, 8 open,
  9 nothing to do). Each fix was designed and challenged by an independent check first, and the finished diff was
  reviewed by independent checks (9 findings, all applied). Commit d28016b. **Build `1.0.12-d28016b12efe`**
  (`D:\JARVIS-release-work\release\`, zip sha256 `74405650...c991`, 525,629,601 bytes): same 10,645 files as 1.0.11,
  pinned inputs identical (`docs/release-rehearsal-20261004-1012/compare_manifests.py`); release regression PASS
  (365 Python, 50 desktop, 18 Intelligence, 17 interface scripts). Sandbox results:
  `docs/release-rehearsal-20261004-1012/README.md`. **Found while preparing the VM check:** the 1.0.11 Stage 7
  scripts work for one pass only (records in fixed places), so the sentence below "a new release needs a new disc
  and a new approval file" was wrong; version 2 copies (`tools/guest/stage7-v2/`, `tools/host/stage7-v2/`, the
  1.0.11 scripts unchanged as evidence) give each check its own label, folders and snapshot (decision tests: 17
  launcher cases, 8 guest cases, all PASS). **Found by the sandbox Stage 7 rehearsal of 1.0.12:** an uninstall run
  while JARVIS was open could start deleting program files while a closing JARVIS window still ran (it stopped at
  `electron\electron.exe`, leaving a half-removed release). Fixed in `tools/installer.py` (the process-ending step
  waits until programs have exited, looks again and refuses before any change; uninstall removes the launcher
  first and retries a file in use for 10 s); 23 installer tests pass, one ending real stand-in programs (copies of
  PING.EXE) in a test folder. **1.0.12 is superseded** (never offered to the everyday JARVIS); what followed is in
  the 1.0.14 bullet above.
- **Stage 7: `STAGE_7_COMPLETE` (2026-10-04T11:00Z).** On the owner's "start stage 7", decisions "A AND A"
  and "I approve the Stage 7 plan" (`../governance/STAGE7-APPROVAL-RECORD.json`; plan `docs/STAGE7-PLAN.md`,
  hash recorded, do not edit). One pass in the Stage 6 VM restored to FRESH-PREREQ (no personal data, no
  keys), builds 1.0.10 -> 1.0.11: install, first launch, second launch joins, offline speech, stop/start,
  Windows restart with automatic start, uninstall, reinstall, update, rollback, update again, and an update
  killed after 3,512 of 10,645 files then run again: every check PASS, data kept throughout, all timings
  inside the Gate 20 bounds. Snapshot **STAGE7-PASS `2503a110-bd71-49d8-8ff1-3193c2c20cd3`** (child of
  FRESH-PREREQ; GATE18-PASS with the owner's data kept). Result `D:\JARVIS-stage7\evidence\stage7-evaluation.json`;
  manifests `D:\JARVIS-stage7\evidence\MANIFEST.json` (69f04661…) and
  `D:\JARVIS-S6-FRESHVM\evidence\guest-egress-01\stage7\MANIFEST.json` (06627a14…); repo copy
  `docs/stage7-evidence/`. The Stage 7 disc method and scripts (`tools/guest/Invoke-Stage7*.ps1`,
  `stage7.cmd`, `tools/host/*Stage7*`) are the standard check for every later release before it is offered
  to the everyday JARVIS; a new release needs a new disc (`New-Stage7Disc.ps1 -ReleaseId`) and a new approval
  file naming both builds. (Corrected 2026-10-04: that is not enough, the scripts work for one pass only; later
  checks use the version 2 copies, see the 1.0.12 bullet above.) **Next, each on the owner's word:** 1.0.12 with `docs/POST-CUTOVER-FIXES.md`
  (then the Stage 7 check 1.0.11 -> 1.0.12, then an update of the everyday JARVIS); after a trouble-free
  period, deleting the test VM and data copies and retiring the old folder and Codex.

Newest handover summary for a fresh session: `docs/HANDOVER-20261004-3.md` (after Stage 7). The earlier
`HANDOVER-20261002.md`, `HANDOVER-20261004.md` and `HANDOVER-20261004-2.md` are out of date; this file is the
current record.

Rules and authority are in `CLAUDE.md` and `../governance/OWNER-DELEGATION.md`; this file
only records where the work stands. Historical handover context: `docs/PROJECT-CONTEXT.md`.

## Where we are

- **SWITCH-OVER COMPLETE (2026-10-04T08:45Z).** (Since 2026-10-05 the everyday JARVIS is 1.0.14, see the first
  bullet; automatic start at sign-in is confirmed.) The owner's everyday JARVIS became the installed
  build **1.0.11-60d406fb6398 at `%LOCALAPPDATA%\JARVIS`** (data, preferences and keys carried
  over; Desktop and Startup shortcut "JARVIS"; AI provider Groq for now). **That folder is the
  live installation: Claude does not modify it (owner-only); updates reach it only as a tested
  release on the owner's word.** Approval `../governance/CUTOVER-APPROVAL-RECORD.json`; records
  `D:\JARVIS-cutover\evidence\` (`cutover-evaluation.json`, manifest 82ff8be6…; repo copy
  `docs/cutover-evidence/`). The old folder `...\outputs\jarvis` is retired but kept untouched (it
  cannot start: its Codex Python is gone); its three shortcuts are in
  `D:\JARVIS-cutover\old-shortcuts\`. Not yet confirmed: JARVIS starting by itself at the owner's
  next sign-in. **Next, each on the owner's word:** lean Stage 7; the first release after the
  switch-over (`docs/POST-CUTOVER-FIXES.md`); after a trouble-free period, deleting the test VM
  and data copies and retiring the old folder and Codex. Source changes are no longer frozen,
  but nothing has been changed yet.
- **Stage 6: `STAGE_6_COMPLETE` (2026-10-04T08:10Z, Gate 20).** (At that time `STAGE_7_NOT_STARTED`; Stage 7
  is now complete, see above.) Passed on FINAL 1.0.11: Gates 16R, 17, 19, 18, 20 and checkpoints P0 to
  P5 (P5 `evidence\gate20\checkpoints\p5-20261004-080906`, on the owner's "run P5"; VirtualBox
  version equal to P0). Verdict and limitations: `evidence\gate20\gate20-evaluation.json`; owner's
  four Gate 20 decisions: `gate20-owner-decisions.json` ("accept all"); index of everything:
  `docs/EVIDENCE-INDEX.md`. The VM (snapshot GATE18-PASS) and the backup copies on D: hold the
  owner's personal data and are kept until the switch-over has run well (owner decision).
  Known: the owner's new Alibaba account is refused `qwen3.8-max` until its identity check
  completes; OpenAI has no credits; the Gemini model in the key file is retired
  (`tools/host/Test-AiKeys.ps1`, owner-run, shows which providers work).
  The long "Next steps" item 2 below is the history of how Stage 6 got here.
  Earlier: P0 PASS (2026-09-30, sealed); owner created `jarvis-s6-val`. Experiment 5
  unconsumed, its budget frozen at 4/5 (that is the experiment budget, **not** a count of
  Stage 6 attempts). (History: at that point Stage 7 was not started and production cutover was not authorized;
  both have since happened, see the bullets above.)
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
   D:. Owner approved the helper route (06:20Z, `owner-decision-02.json`) and ran it: backup
   `bcc2753f736f43ba946ec3f342b35c3a.zip` (4,659,473 bytes, 398 files, real data, test restore
   passed, copied and hash-verified; the live `recovery.py` equals baseline e6fc40b);
   `backup-evaluation.json` PASS (06:21Z); launcher re-enabled. Recovery disc built by the owner
   06:46Z (`recovery-disc.json`: `JARVIS-RECOVERY.iso` 5,898,240 bytes, sha256 1189ac01…, both
   copies re-hashed equal, guest files equal the repo's, backup inside equals the copy record).
   VM started by the owner 06:47Z (disc on port 2, snapshot GATE17-19-PASS, LocalhostReachable 0).
   **Incident 03 (`incident-03-k2-jarvis-running.json`): guest run `gate18-20261004-065046` K0, K1
   PASS, K2 FAIL** because the first install was running (8 processes): the Gate 17 install's
   Startup shortcut starts JARVIS at sign-in, and the prepared steps lacked "quit JARVIS first".
   Nothing was changed in the VM by Gate 18. **Owner decision required to repeat:** quit JARVIS in
   the VM (tray > Quit JARVIS completely), Claude moves the failed run folder unchanged to
   `guest-egress-01\incident-03-run1\`, owner double-clicks `gate18` again (rerun). Owner approved
   ("approve", `owner-decision-03.json`); rerun `gate18-20261004-072308`: K0–K3 PASS, then
   **incident 04 (`incident-04-k4-hang-read-only-disc.json`): K4 hangs.** FINAL's
   `recovery.verify()` makes its temporary folder beside the archive; on the read-only disc
   Python 3.12's `mkdtemp` retries forever on Windows (shown on the host with FINAL's Python).
   Tooling gap (restore from a writable copy) and a FINAL limitation to list at Gate 20 (backup on
   read-only media hangs; fix after cutover). Nothing imported. **Owner decision required for
   rerun 2:** close the stuck window, `xcopy E:\ C:\g18\`, run the unchanged script from `C:\g18`
   with `-RestoreHome C:\g18home`; Claude first moves the stuck run folder to
   `guest-egress-01\incident-04-run2\`. Owner approved (`owner-decision-04.json`). **Run 3
   `gate18-20261004-074554`: K0–K9 ALL PASS** (old-format real backup verified by FINAL, 176 files
   imported, counts equal for all 18 tables, Core ready on the restored data in 58.1 s, clean stop,
   both installs verify, first install's data and the backup unchanged). Snapshot **GATE18-PASS
   `5dcbb9f0-0d6c-4311-8b57-7ba329290edf`** (07:55:13Z, VM off, `.vbox` sha256 342781d1…).
   **`gate18-evaluation.json`: `BACKUP_RESTORE_RECOVERY_PASS`** for the restore, with six recorded
   deviations and owner decisions 01–04; findings for Gate 20 listed there (FINAL hangs on a
   backup on read-only media; `memory_items_visible` 3 vs 6 item rows to explain; guest script
   fixes before reuse). **P4 PASS** (run `evidence\gate18\checkpoints\p4-20261004-075914`,
   07:59:14Z, on the owner's "run p4": byte-identical to P3, VirtualBox 7.2.18.175117 unchanged,
   empty census; `p4-evaluation.json`). Manifests: `evidence\gate18\MANIFEST.json` (31 files,
   sha256 603605cf…) and `MANIFEST-guest-egress-01.json` (74 files, c42af0f1…). **Gate 18 is
   complete: `BACKUP_RESTORE_RECOVERY_PASS`.** **Gate 20 IN PROGRESS (08:06Z):** draft requirement
   table `evidence\gate20\gate20-requirements-draft.json` and plain version
   `docs/stage6-freshvm/GATE20-REVIEW.md`. Nothing FAIL. **Waiting for the owner's four Gate 20
   decisions** (1 build/UBR not recorded by the Gate 18 script, host-side value 26300.9457;
   2 D9 bound: install/update/rollback 600 s, stop 120 s, and the reading that the four collector
   deadlines of §9(g) did not apply; 3 FINAL's read-only-media hang as a known limitation;
   4 keep or delete the VM and the personal-data copies), **then P5 on the owner's own "run P5"**
   (reference `evidence\gate18\checkpoints\p4-20261004-075914`; create `evidence\gate20\checkpoints`),
   then the final table, manifest, `docs/EVIDENCE-INDEX.md`, verdict, STOP. Original plan text: **Next: Gate 20** (Claude: read the V1 runbook
   Gate 20 list and COMPLETE RULE in `../reference`, requirement table with PASS /
   APPROVED_DISPOSITION / FAIL / NOT_APPLICABLE_WITH_EVIDENCE, D9 timing bound, the Gate 18
   findings put to the owner; P5 only on the owner's own "run P5", reference the P4 folder;
   verdict; `docs/EVIDENCE-INDEX.md`; STOP). The VM and
   `D:\JARVIS-S6-FRESHVM\media`, `D:\JARVIS-release-work\stage6-media\JARVIS-RECOVERY.iso` and
   `D:\JARVIS-release-work\recovery-payload` now hold the owner's personal data. Repairing the everyday JARVIS is a
   separate owner decision.
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
3. `RESUME_STAGE6_RECOVERY` before Gate 18 (done 2026-10-04; this list is history).
4. After Stage 6 passes: switching the everyday JARVIS over (cutover), then Stage 7. (FINAL
   selection is done: 1.0.11, 2026-10-04. Cutover and Stage 7 are done, 2026-10-04.)
   The owner's freeze from P0 (keep VirtualBox closed under the owner account and do not install, upgrade or
   repair it until Gate 20) ended with Gate 20; VirtualBox work stays owner-only.

Claude's local preparation (no approval needed) is listed in section 9 of that plan.

Desktop and Startup shortcuts: never tested on this PC (rehearsals use `--no-shortcuts`, because creating them
changes the owner's real folders); tested in the VM at Gate 17 and Stage 7 (automatic start after a restart).

## What exists (built 2026-10-01)

- One shared background Core per data folder (`core_lock.py`); desktop app joins it.
- Providers: Qwen (Alibaba Cloud Model Studio) brain and cloned JARVIS voice; local voice
  (Whisper base.en, openWakeWord). Keys are owner-placed in `config\.env`, never read.
- `switch_over.py`: imports a verified backup's data into a new install (owner-run).
- Release: `runtime_paths.py` (data/config/models from `JARVIS_*` env vars),
  `tools/build_release.py` (pinned inputs, manifest of every file),
  `tools/installer.py` (per-user install, update, rollback, uninstall, verify; crash-safe),
  `tools/release_regression.py` (all suites against a built release with its own runtimes).
- Test totals on the packaged release: 316 Python, 34 desktop, 18 Intelligence, 16 JS scripts (2026-10-01);
  1.0.11: 325/36/18/16; 1.0.12: 365/50/18/17; 1.0.14: 373/52/18/17.

## This PC: disks and folders

- **C: is nearly full** (about 20 GB free). Build and rehearse on **D:**:
  `D:\JARVIS-release-work\` holds `release\` (builds 1.0.2 to 1.0.7), `regression-*`,
  `sandbox-home*` (test installs, synthetic data only) and `evidence\`.
- **E: (JARVIS BACK UP) is the backup drive. Never write to it.**
- `D:\C-drive-overflow\`: large files moved off C: on 2026-10-01 at the owner's request
  (Windows ISO, installers, `Documents\Codex\2026-09-12`); its README lists the original paths.
- **Since the switch-over of 2026-10-04 the live JARVIS IS `%LOCALAPPDATA%\JARVIS`** (the older
  `../governance/LIVE-INSTALLATION-MAP.md` describes the retired folder). Never run `install.cmd`
  or `installer.py` without `--home <sandbox>`: without it they act on the owner's live
  installation. Never start, stop or edit the live installation; never read `config\.env`.

## Commands

```powershell
.venv\Scripts\python.exe -m unittest                                    # dev Python suite
.venv\Scripts\python.exe tools\build_release.py --version X.Y.Z --out D:\JARVIS-release-work\release [--no-zip]
.venv\Scripts\python.exe tools\release_regression.py --package D:\JARVIS-release-work\release\JARVIS-<id> --work D:\JARVIS-release-work\regression-<version>
```

## Gotchas for Claude

- Bash heredocs and inline Python mangle backslashes (`\r`, `\b`, `\n` in Windows paths and
  strings). Use the Edit/Write tools for any text containing backslashes.
- The Edit tool rewrites a file with MIXED line endings to one style (whole-file diff). Mixed files include
  `static/app.js`, `static/teague.js`, `README.md`, `release-notes.json`, `desktop/test/backend.test.cjs`
  (`git ls-files --eol` shows `i/mixed`). Change those with a small byte-exact script (old bytes -> new bytes,
  anchor must match once) and check `git diff --stat` after every edit.
- Never edit `tools/guest/*` (or a host tool whose hash an approval records) once a disc or approval carries it:
  make a new version beside it (precedent: Stage 7 copies of the Gate 17 scripts; `tools/*/stage7-v2/`).
- Passing a list to a script started with `powershell -File` gives one string, not a list (`-SkipPhases a,b`
  arrives as "a,b"); use `-Command "& 'script' -SkipPhases a,b"` when a list matters.
- `git commit -F -` with a PowerShell here-string does not read stdin; write the message to a file and use
  `git commit -F <file>`.
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
- **2026-10-04, Gate 18, P4, Gate 20, P5: STAGE_6_COMPLETE (Opus 5.5, then Fable 5.1; new session
  from the second handover summary).** Owner issued `RESUME_STAGE6_RECOVERY`. Four incidents on the
  way, each recorded with an owner decision: the backup drive held a folder copy, not a backup, and
  copy script v1 picked a wrong file (PowerShell 5.1 ignores `-Include` with `-LiteralPath`); the
  everyday JARVIS cannot start (Codex Python gone), so its own `recovery.py` was run with FINAL's
  Python; the guest run stopped at K2 because the installed JARVIS auto-starts at sign-in; the dry
  run hung because FINAL verifies a backup with a temp folder beside the archive and the archive was
  on the read-only disc. Third guest run from a writable copy: K0 to K9 PASS on the real backup
  (1,133 messages, counts equal). Snapshot GATE18-PASS, P4 PASS, Gate 20 table, four owner decisions,
  P5 PASS, verdict. Lessons: rehearse with a real read-only disc image and with the Startup shortcut
  present; never filter files with `-Include` on `-LiteralPath`; an owner-run tool that reads an
  untested location needs refusal checks for what it expects to find. Also written: an owner-run
  Qwen key check (`tools/host/Test-QwenKey.ps1`). Nothing pushed or synced.
- **2026-10-04, switch-over (Fable 5.1, same session).** On the owner's word: plan finished and
  rehearsed in a sandbox (one launcher defect found there: the zip has a top folder), approved, then
  run by the owner step by step: check, install, dry run, import (176 files, counts equal), keys
  copied by the owner, first start. OpenAI had no credits; the owner-run provider check showed Groq
  working and the owner switched the provider line. The owner confirmed memories, conversations and
  voice, then "make the switch": three old shortcuts moved aside, nothing deleted. A requested
  all-in-one launcher that would import without the owner seeing the dry-run list was refused by the
  session's safety check and not built. Mistake to avoid: I told the owner the version shows in
  Settings; it does not (now item 4 of docs/POST-CUTOVER-FIXES.md). Shell heredocs and sed mangled
  backslash paths in this file twice; use the Edit tool for any path. Nothing pushed or synced.
- **2026-10-04, Stage 7 (Fable 5.1 for the preparation, Opus 5.5 for the VM pass and the result).**
  Owner: "start stage 7"; Claude reported the conflict between AMENDMENT-v2 6(j) (VM Stage 6 only) and the
  roadmap (Stage 7 on the same VM); owner chose "A AND A" (reuse the VM from FRESH-PREREQ; builds 1.0.10 ->
  1.0.11). Stage 7 scripts are copies of the Gate 17/19 scripts with an Interrupt phase (installer killed
  mid-copy, then rerun) and an uptime-based restart check; the Stage 6 originals stay unchanged as evidence.
  Sandbox rehearsal run 1 stopped on the uninstall shortcut check (it saw the owner's real JARVIS.lnk);
  fixed for local runs only; run 2 ALL PASS. Owner approved the plan, built the disc, started the VM, ran the
  pass: every phase PASS, snapshot STAGE7-PASS, STAGE_7_COMPLETE. The uptime-based restart check proved
  itself: the guest clock fell about 9.5 minutes behind after the restart. Lesson: when a launcher path has
  to be typed by the owner, give the exact name (they typed stage-7-step). Nothing pushed or synced.
- **2026-10-04/05, releases 1.0.12 to 1.0.14 (Opus 5.5; the night session, then a new session from the handover
  summary, opened in the old OneDrive handover folder and moved to the repo).** 1.0.12 (fix list items 1-6) built
  and checked; its sandbox Stage 7 rehearsal found the uninstall race (installer fix eb620cd). The review of that fix
  was interrupted with its session at 00:24 and returned nothing; rerun with one reviewer (applied in 6d4ff85). 1.0.13
  built; its release regression failed twice on the desktop "shared background Core" test: reproduced as a real race
  (the Core answers on an open keep-alive connection until its process exits), fixed in e038726 with a reviewed
  change and tests. 1.0.14 built: comparison, regression, zip install and the sandbox Stage 7 pass all PASS; plan
  `docs/STAGE7-CHECK-1.0.14.md` ready for approval. Lessons: a regression failure that passed before is not "load"
  until reproduced (run 3 on an idle PC settled it); a reviewer can find that a new wait condition hurts the crash
  path. The owner's pasted summary contained "Ultracode is off", which switched on multi-agent mode by mistake; no
  workflow was started (two single reviewer agents instead). Then, same session: the owner approved and ran the Stage 7 check of 1.0.14 in the VM (two driver defects found and worked around with the owner, both recorded; `STAGE_7_COMPLETE`, 27 of 27), approved the update of the everyday JARVIS (plan and launcher written and rehearsed 13 of 13 in a sandbox) and ran it: `EVERYDAY_UPDATE_COMPLETE`, automatic start at sign-in confirmed after a PC restart (about 6.5 min after sign-in). Lessons: decision tests must also run the guest driver with the egress drive unmounted and with a long wait after a restart; the owner cannot always tell the VM window from the PC (check the prompt shows jarvis-s6-guest); Claude cannot operate the VM (owner-only and another account's screen). Nothing pushed or synced.
