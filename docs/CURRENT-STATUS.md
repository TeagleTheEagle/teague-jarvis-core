# JARVIS: current status (living document)

**Read this first in every new Claude Code session, and update it at the end of each one.**
Last updated: 2026-10-12 evening (the section "2026-10-12 evening" below is the newest: Serena fixed, no missing dependencies, VERONICA's five unlisted packages pinned, the new tool system_diagnostics, the ASI roadmap proposal, Phase 1 begun; before it, the section "2026-10-12": what other AI tools did on 2026-10-11, the repo back on claude/main, the workspace back at its recorded path, VERONICA in her own repo D:\VERONICA, one AI tool per project; before it, 2026-10-11 morning: the section "2026-10-10 late night" runs into 2026-10-11: release 1.0.18 = THE TIME FIX ONLY (owner: "keep friday as he is, 1.0.18 time fix only"), built as 1.0.18-cffb826de043, every check on this PC passed, docs/STAGE7-CHECK-1.0.18.md READY FOR THE OWNER'S APPROVAL; it corrects the section "2026-10-10 night"; before it, "2026-10-10 night": FRIDAY started, the Mac's round 6 copy kept; before it, "2026-10-10 late evening": the You page built and reviewed, findings not yet applied; the memory roadmap for approval; voice recognition researched) (STAGE_6_COMPLETE, SWITCH-OVER COMPLETE, STAGE_7_COMPLETE for 1.0.14, 1.0.15 AND 1.0.16;
**the everyday JARVIS is 1.0.17-0d38218c4e1d (EVERYDAY_UPDATE_COMPLETE, 2026-10-07 evening, the first update made by the release's own Setup: JARVIS.exe, the Installed-apps entry, the shortcuts at JARVIS.exe); 1.0.16, 1.0.15, 1.0.14 and 1.0.11 stay installed as rollback copies.
**CORE RELEASE 1.0.16 ("the phone release", now also with the Qwen voice link fix): BUILT AND CHECKED ON THIS PC as build 2 `1.0.16-fccde24e2cc6` (commit fccde24; comparison, release regression, zip install and sandbox Stage 7 all PASS; build 1 `1.0.16-4e54fc946bc3` superseded, never offered); `docs/STAGE7-CHECK-1.0.16.md` APPROVED BY THE OWNER ("I approve the Stage 7 check of 1.0.16", first clock reading 2026-10-06T06:50:25Z; record `../governance/STAGE7-1.0.16-APPROVAL-RECORD.json`, repo copy `docs/stage7-1.0.16-evidence/`); the tools are placed in `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.16\` and the record folders created; **THE VM CHECK OF 1.0.16 IS COMPLETE: `STAGE_7_COMPLETE`, 27 of 27 checks** (owner "stage 7 done" 2026-10-06 about 20:00 local; evaluation `docs/stage7-1.0.16-evidence/stage7-evaluation.json`, evaluated 09:02:54Z; snapshot STAGE7-PASS-1.0.16-fccde24e2cc6 c91c7f1a… taken 08:59:38Z after a clean shutdown, all eight snapshots kept; the first install's 646 s against the 600 s bound dispositioned as a VM limitation under the owner's rule of 2026-10-06, every update, rollback and stop inside the bound; no incident this time). **THE UPDATE OF THE EVERYDAY JARVIS TO 1.0.16 IS COMPLETE: `EVERYDAY_UPDATE_COMPLETE`** ("I approve the update of my everyday JARVIS to 1.0.16", 2026-10-06T09:11:04Z; record `../governance/UPDATE-1.0.16-APPROVAL-RECORD.json`; steps 1 to 5 run by the owner 20:16 to 20:40 local: check, backup 351 files with test restore, update 108.5 s with the database byte-for-byte unchanged, the owner's check, a PC restart with JARVIS 1.0.16 starting by itself 5.7 min after sign-in; evaluation and MANIFEST in `D:\JARVIS-update-1.0.16\evidence`, repo copy `docs/update-1.0.16-evidence/`; the Private network switch stays off until the owner sets up Tailscale). **THE PHONE IS PAIRED AND TALKING TO THE CORE OVER THE PRIVATE NETWORK (22:15 local):** Tailscale on the PC (`thegrizzlybear`, 100.103.95.28) and the phone (`iphone-15`), both set up by the owner; the Private network switch on; the door on 100.103.95.28:8790; PAIR with the address; the Ask screen ONLINE with Core 1.0.16, AI READY, link 22 ms; a conversation answered. Result record `docs/PHONE-V1-RESULT.md` (in progress: checks 1 and 2 DONE at 22:20 on cellular with Wi-Fi off, hold-to-speak heard, THINKING on the PC, SPEAKING in JARVIS's voice, link about 200 ms; checks 4, 5, 6 and 10 DONE at 22:23 to 22:24 (Chats with the conversation and its messages, Status with the readouts and the overview, STOP ALL from the phone and RESUME on the PC, the PC's Devices page showing the phone online with every tick); checks 7, 8 and 9 DONE at 22:28 to 22:31 (revoke then pair again, Tailscale off gives CORE NOT REACHED, "remember that" saved and shown on the PC's Memory page, though as the word "that"); check 3 FAILS (the owner: closing the app mid-conversation shows a fresh one; the id is kept but the lines are not reloaded); **VERSION 1: 9 of 10 checks met, the app's next round fixes check 3, the header at the phone's width, the stale stop note and the icon**; two fixes on the way: the phone had signed into a second Tailscale network, and the app crashed after pairing until the microphone usage entry was added to the Info list). **NEXT: the owner's remaining section 10 checks; a fix round for the header layout at the phone's width (ONLINE wraps, STOP ALL squeezed) and the icon; then release 1.0.17.** The check's course: step 1 done (disc `JARVIS-STAGE7-1.0.16-fccde24e2cc6.iso`, sha256 dd3a1abe…, built 06:55Z, checked by Claude), step 2 done (VM started on FRESH-PREREQ), step 3 PASS (the Install phase, all nine checks E0 and I1 to I8, 18:04:42 to 18:35:49 local; the install took 646 s against the 600 s Gate 20 bound, copy 301 s and verify 225 s, the VM's disk as in the 1.0.15 check, for the owner's disposition at the evaluation); step 4 (quit, restart, the second run of stage7, about 50 min) is the owner's next act; steps 5 to 7 pending ("stage 7 done" ends them), then the evaluation and the everyday-update plan. THE IPHONE APP (step 7 of the phone plan) IS WRITTEN under `phone/ios/`, independently reviewed with every finding applied (1 high, 5 medium, 19 low: `docs/PHONE-APP.md` section 5), and zipped for the Mac at `D:\JARVIS-release-work\phone\JARVIS-ios-v1-20261006-1810.zip` (sha256 62d873f1…); not built here (the owner builds it on the Mac, `phone/ios/README.md`, fix rounds expected). On the Mac the owner has created the Xcode project `JARVIS` (bundle id `com.teagueindustries.jarvis`, team Benjamin Teague, Display Name JARVIS, iOS 26 as the minimum by the owner's choice, the two Info keys, the three build settings); THE APP IS BUILT AND RUNNING ON THE OWNER'S IPHONE (19:00 local): the twelve files dragged in, Build Succeeded at the first attempt with no fix round (Xcode's bridging-header prompt answered Don't Create), installed by Product > Run after Xcode's one-time symbol copy, the pairing screen shown as designed (picture `docs/phone-evidence/phone-app-first-launch-20261006-1900.png`); not pairable until 1.0.16 is the everyday JARVIS and Tailscale is set up (plan steps 5 and 6). **`docs/OWN-APP-PLAN.md` IS APPROVED BY THE OWNER** ("I approve the own app plan can we make the app icon this image as well as the app icon for the ios app", then the exact "I approve the own-app plan"; first clock reading 2026-10-06T08:23:24Z; record `../governance/OWN-APP-PLAN-APPROVAL-RECORD.json`, repo copy `docs/own-app-evidence/`): release 1.0.17 after 1.0.16 and the phone: JARVIS.exe with the icon and name, no PowerShell step, JARVIS-Setup.exe built with Inno Setup (the owner installs it once), an Installed-apps entry, version 4 Stage 7 scripts; D1 to D4 and D6 as recommended; **D5 changed by the owner: the icon is the Teague Industries badge the owner supplied**, kept at `static/assets/branding/teague/teague-industries-badge.png` and rendered on approval into `desktop/jarvis.ico`, `desktop/tray.png` (the tray image the desktop code pointed at and the repo lacked) and `phone/ios/AppIcon-1024.png` (copy for the Mac `D:\JARVIS-release-work\phone\JARVIS-AppIcon-1024.png`; the owner drags it into Xcode's Assets > AppIcon). Nothing else of 1.0.17 is built. **THE LOOK APPLIED TO THE IPHONE APP** (owner: "apply the look", from a mock-up zip the owner supplied; `docs/PHONE-APP.md` section 6): the badge as the header logo, the space scene faint behind every screen, a turning orbital graphic on the pairing screen; `phone/ios/JARVIS/Theme.swift` and `PairingView.swift` changed, assets `phone/ios/assets/TeagueBadge.png` and `JARVISBackground.jpeg`, reviewed (no high or medium, 4 low, 2 applied); zip for the Mac `D:\JARVIS-release-work\phone\JARVIS-ios-look-20261006-1946.zip` (sha256 cc87bdab…), steps `phone/ios/README-look.md`; **BUILT AND SEEN ON THE PHONE at 21:12 local** (screenshot `docs/phone-evidence/phone-app-look-20261006-2112.png`; the home-screen icon needs one delete-and-reinstall of the app to refresh, told to the owner). The VM check's second run: AfterRestart, Uninstall and Update phases PASS (driver log 07:55, 08:07, 08:40Z), the interrupted-update phase started 19:40 local. Open for the owner: the voice tool run again after the fix (expected "qwen voice SPEAKS"), the approval, the C: cleanup steps (parked on the owner's word: "focus on the app"), later the Phone Link / contacts / Gmail idea**).

- **2026-10-07, about 14:30 local (Fable 5.1, same session, ended on the owner's "handoff"): THE 1.0.17 BUILD CHAIN RAN; BUILD 1 SUPERSEDED BY ITS REGRESSION; BUILD 2 BUILT AND ITS REGRESSION RUNNING ALONE AT THE HANDOFF; FRIDAY STARTED AS A SEPARATE PROJECT.** Records: `docs/release-rehearsal-20261007-1017/README.md`. The rehearsal build `1.0.17-b848d70e784d` and the version 2 Setup rehearsal on it: PASS (the real shortcuts unchanged, `withheld`, the entry "JARVIS (sandbox)", clean uninstall). **Build 1 `1.0.17-52342b46e48a`** (commit 52342b4): comparison with 1.0.16 as planned (30 source files changed, 86 added, the four planned program files), the Setup built (406,915,840 bytes), the zip install PASS (through `JARVIS.exe`; the new `zip_install_rehearsal_v2.py`), the Setup rehearsal v2 PASS, **the sandbox Stage 7 pass with the version 4 driver: ALL STAGE 7 STEPS PASSED** (29 checks, 13:35-14:09, G7 the update through the Setup included; the sandbox cleaned up through its own entry; records `stage7-local/`, the four 4 MB Setup logs left on D:), **but the release regression did not pass**: 2 failures and 11 errors in the Python suite (776 tests in 2,969 s under the load of the four other checks): three test modules need repo-only tools or a development checkout (`test_own_app.SetupScriptTests`, `test_tell_jarvis`, `test_memory_stamp`; fixed to skip where the tool is absent, or to assert the stamp the Core really uses, which in a release is the release id, the right behaviour of item E) and nine timeouts with the file-in-use errors that follow (`test_phone_access`, `test_phone_bridge`, `test_phone_core`; the same tests passed three times today in the development suite). Build 1 is superseded, never offered; the number stays 1.0.17 as for 1.0.16's two builds. **Build 2 `1.0.17-0d38218c4e1d`** (commit 0d38218): built 14:14-14:16 with the zip (533,361,567 bytes, sha256 `210b4623…`); against build 1, 0 source files changed, the pinned inputs identical (the same program); against 1.0.16 as build 1. **Its release regression, run ALONE 14:16-14:42: PASS** (776 Python tests OK with 7 skipped by their own conditions, 60 desktop, 18 Intelligence, 26 interface scripts; `docs/release-rehearsal-20261007-1017/regression-1.0.17-0d38218c4e1d.output.txt`; the nine timeouts of build 1 did not recur). Then, on build 2, one after another, never two at once: its Setup (`tools/setup/build_setup.py --package D:\JARVIS-release-work\release\JARVIS-1.0.17-0d38218c4e1d`), the zip rehearsal v2, the Setup rehearsal v2 (`-Base D:\JARVIS-release-work\setup-rehearsal-v2-1.0.17-build2`), the refresh of `D:\JARVIS-release-work\pkg-1.0.17` (it still holds build 1's four files: replace them with build 2's zip, record, Setup and Setup record), the sandbox Stage 7 pass (`rehearse-stage7-release-v4.ps1 ... -Base D:\JARVIS-release-work\stage7-local-1.0.17-build2`; the Setup rehearsal and this harness both refuse while the sandbox entry exists, so never together), the README sections, and `docs/STAGE7-CHECK-1.0.17.md` rewritten for build 2 (it is a DRAFT with build 1's ids, hashes and results; the tool-hash table is right); then the owner's approval. Lesson recorded: the regression runs alone; the other checks share the disk and cause timeouts. **The owner's new request, built in its own folder:** `C:\Users\jonny\JARVIS-claude-workspace\friday\` (not in the JARVIS repository; its own git repository, commit 930b56b, and its own `.venv` with pytest 9.1.1 and anthropic 1.11.0): FRIDAY, "the JARVIS Core's personal agent" (`jarvis.py`: tools, memory, the one door `respond()` that answers "Sir, we can't do that: it has not been programmed." for anything else and keeps the gap, `program()` for "okay, code it", a console), `test_jarvis.py` (60 tests, no network), `supervisor.py` (Try-Verify-Rollback: pytest, git commit on green, otherwise Claude's raw-Python fix over `jarvis.py`, five tries, `git checkout -- jarvis.py` on failure; `--program "..."` adds a capability and keeps it only when the tests pass and a fresh interpreter answers the request; `--dry-run` never calls the API; the key from the owner's environment or a git-ignored `.env`; model `claude-opus-5-5` because the requested `claude-3-5-sonnet-20241022` was retired on 2025-10-28; the server-side refusal fallback on). The dry run passed; no real API call was made (the owner has not set a key for it). **Owner-side:** set `ANTHROPIC_API_KEY` for FRIDAY if the live loop is wanted (never in the JARVIS repo); the earlier owner-side items unchanged.
- **2026-10-07, about 13:40 local (Fable 5.1, new session; it opened in the old OneDrive handover folder and was moved to the repo; the owner: "take the handoff ... continue with 1.0.17's release work", then three messages mid-work): THE VERSION 4 STAGE 7 SCRIPTS WRITTEN AND REVIEWED WITH ITEM 3.4; THE MUSIC STOP DEFECT FIXED; THE START-UP SONG BUILT; THE RELEASE-NOTES ENTRY WRITTEN. 1.0.17 IS COMPLETE IN THE REPOSITORY; THE BUILD IS NEXT.** No workflow was started (the pasted handover's "ultracode" switched multi-agent mode on by mistake; one reviewer agent per item, as the owner said). **Version 4 Stage 7 scripts** (`tools/guest/stage7-v4/`, `tools/host/stage7-v4/`, record `docs/STAGE7-DRIVER-V4.md`; the version 3 files untouched): the Install phase installs from `JARVIS-Setup-<id>.exe` silently and checks the Installed-apps entry (I3), the shortcuts must point at JARVIS.exe, a launch without a shortcut starts JARVIS.exe, the Uninstall phase goes through the entry's own uninstaller and reinstalls from the Setup, G7 adds one update through the Setup (29 checks per pass, 27 before); the disc carries the Setup beside the zip, so the disc builder copy in that folder makes a DVD-sized image (the original is CD-sized, which every earlier disc fitted); the launcher takes `jarvis-stage7-authorized-v4`. Decision tests: 19 launcher cases, 21 driver cases, all pass (records in `docs/release-rehearsal-20261007-1017/`). Two rehearsal scripts there: `rehearse-setup-v2.ps1` (the Setup in a sandbox with the owner's real Desktop and Startup `JARVIS.lnk` recorded before, after every step and at the end, stopping on any change; the installer's own word "withheld" and `--no-shortcuts` in the Setup's logged command required) and `rehearse-stage7-release-v4.ps1` (the sandbox pass with the version 4 driver, the same watch, a cleanup through the sandbox's own uninstaller that fails the run if the sandbox's entry survives). **Independent review of item 3.4 (the Setup) with the version 4 scripts** (one reviewer): no high, 8 medium, 9 low, all applied but one recorded (`docs/OWN-APP-1.0.17.md` section 7): among them a sandbox run (`/HOME`) now registers as "JARVIS (sandbox)" under a second application id so rehearsals never touch the real JARVIS's entry (and `/HOME` needs `/DIR`); a refused install removes the entry it wrote and says that nothing was installed (a silent Setup exits 0 either way: `setup-result.json` is the verdict); the uninstall asks before it removes the program; the guest driver prints progress every half minute while a Setup runs (a quarter of an hour of silence in the VM was possible) and requires the installer's own word on the real shortcuts; `tools/setup/JARVIS-Setup.iss.in` compiled again against a dummy package after the rewrite (`UsePreviousLanguage=no` was needed). **The owner's bug report** (screenshots: "Playing Daddy's Home." then "stop music." answered "Nothing was playing." while the song played on): reproduced on this PC with a tone and a copy of the owner's MP3 at 5 percent volume (the copy deleted); Windows ties a media-interface device to the thread that opened it and the Core answers each request on its own thread, so 1.0.16 cannot stop, pause or see a song from the request after the one that started it. Fixed in `music.Mci`: one long-lived thread of the player's own sends every command (10 s wait; a stalled interface is refused at once until it answers; `Player.stop(lock_timeout)` for the emergency stop and the Core's exit). `Library.resolve` also takes the exact file name, whatever its case. **The owner's request "when jarvis boots he says his morning hello message then the mp3 plays":** built as the start-up song (setting `music_startup`; Settings > Music "When JARVIS starts"; the window speaks the sign-in greeting, then asks the Core's `/api/music` action `startup`; silent in quiet hours and when nothing is set; the emergency stop holds; the owner's own setting is not bound by the tool's switch, like a click on PLAY; record `docs/MUSIC.md`, the last two sections; `API.md` rows). **Independent review of both music items** (one reviewer): no high, 3 medium, 12 low, applied but one recorded. **The owner also pasted JARVIS's "standing intent, always-present JARVIS":** kept verbatim as `docs/ALWAYS-PRESENT-JARVIS-BRIEF.md`, a brief only (nothing built or switched on; what exists today and what a watchdog would need), a plan for the owner's approval after 1.0.17. **Release notes:** the 1.0.17 entry inserted at the top of `release-notes.json` by a byte-exact edit (the counts are recorded in the checks' README at the build). **Tests at the commit:** the full Python suite 777 OK (259.8 s; three runs today: 764, 775, 777 as the items landed); 26 interface scripts; `test_music` 19 (one against the real media interface with a silent tone); `test_own_app` +3 for the Setup template; the installer tests' runner block moved to the end of the file (it sat before `OwnAppTests`). **Answered for the owner:** an iTunes purchase is an AAC file: convert it to MP3 in the Apple Music or iTunes app (Import Settings MP3 Encoder, File > Convert > Create MP3 Version), copy it into `%LOCALAPPDATA%\JARVIS\config\music`, give it a nickname in Settings > Music. **Next:** a rehearsal build from this commit (`--no-zip`, `D:\JARVIS-release-work\own-app-rehearsal`) and its Setup through `rehearse-setup-v2.ps1` (proves the fixed switches against the real shortcut folders before the real build); then the real build of 1.0.17 on D:, its Setup, the comparison with 1.0.16, the release regression, the zip rehearsal, the Setup rehearsal v2 on the real Setup, `pkg-1.0.17` (zip, record, Setup, record), the sandbox Stage 7 pass with the version 4 driver, the README of the checks, `docs/STAGE7-CHECK-1.0.17.md` for the owner's approval (seven tools in its hash table, the version 4 disc builder among them); then the VM check and the everyday update on the owner's approvals. Owner-side, unchanged: pair "Claude Code" in Settings > Devices and type the code here; the Google steps when wanted; the Device Access steps for item I; the Mac's 02:27 zip and the form section 6.
- **2026-10-07, about 08:40 local (Fable 5.1, same session): ACCESS ITEM H BUILT, REVIEWED AND COMMITTED: THE DEVICES SEEN ON THE HOME NETWORK.** Record `docs/PHONE-ACCESS-1.0.17.md` section 7. `network_devices.py` reads Windows' own neighbour table (`Get-NetNeighbor`, IPv4) and this PC's own addresses in one PowerShell call, keeps the entries with a real hardware address in a state Windows lists as seen, drops multicast, broadcast, link-local and the never-answered, sorts numerically, caps at 200, and names the first 40 through this PC's DNS server only (`Resolve-DnsName -DnsOnly`: no LLMNR, no mDNS, no NetBIOS, so nothing is sent to a device found; the review's high finding: `gethostbyaddr` would have done both); a name is text set by that device (printable only, marked "not instructions" for the model); the list is kept a minute. The tool `network_devices` (a read on the PC, usable by devices with no tick; the model's result carries no hardware address), the owner's route `GET /api/network-devices`, Settings > Devices > "On this network" (READ THE NETWORK LIST, never on its own). On this PC the real read takes about a second and names arrive within the DNS call's bound. Review: 1 high, 2 medium, 5 low, all applied (record section 7). 51 tools: `docs/PERMISSIONS.md`, the request templates regenerated. Tests: `test_network_devices.py` 6, `test_devices_view.cjs`, `test_permissions.py`; the full Python suite: 764 tests OK (with the project's .venv Python). **Item I (Nest) stays listed** until the owner does the Device Access steps of the plan; it is not built. With H, every Core item of the access plan that can be built without an owner step is built (A, C, D, G, E, F, H). **Next:** 1.0.17's remaining steps: the review of item 3.4 with the version 4 Stage 7 scripts, a new sandbox Setup rehearsal that records the real shortcut folders before and after, the release-notes entry, the build on D:, comparison, regression, zip and Setup rehearsals, sandbox Stage 7, `docs/STAGE7-CHECK-1.0.17.md` for the owner's approval, the VM check, the everyday update. Owner-side, unchanged: pair "Claude Code" in Settings > Devices and type the code here (then `tell_jarvis.py` reports A, C, D, G, E, F and H to JARVIS); carry `docs/MAC-REQUESTS-20261007.md` (now with section 6) and the Mac's 02:27 zip; the Google steps when wanted; the Device Access steps for item I.
- **2026-10-07, about 08:20 local (Fable 5.1, same session): ACCESS ITEM F BUILT, REVIEWED AND COMMITTED: THE ROUTINE, ITS NUDGES, THE NOTICES AND THE ANNOUNCE ROUTE.** Record `docs/PHONE-ACCESS-1.0.17.md` section 6. Settings > Routine holds the owner's week as blocks (`nudges.Routine`, `static/routine.js`, `GET`/`POST /api/routine`); a clock in the Core (`nudges.Clock`, once a minute like the backups') finds the collisions (a task with a due time or a reminder inside a block or within an hour after it, when the block is about to start or runs) and raises one nudge each, once ever (keyed), none in quiet hours or while stopped. Notices (`nudges.Notices`: nudge, announce, approval, system; the newest 500 of each kind) are shown on the PC as toasts (`state.notices`), listed to paired devices (`notices {after?}`, a read mark per device), and spoken on this PC in JARVIS's voice through Windows' own player (`speaker.py`, winmm, one queue and one thread, window open or not) when "Announce due reminders and routine nudges" is on, the voice is on and quiet hours are off. A paired device's `announce {sender, text, kind}` makes the PC say "<name>, Jack texted you: ..." (6 a minute, refused while stopped). The microphone guard (`App.speakable`): words carrying the wake word or a stop phrase are never read out near the PC's own microphone (announced only; the full text stays in the notice), and the window pauses its wake detection while the PC speaks (`state.speaking`). The automatic backups write a `system` notice. Review: 1 high (the guard), 3 medium (synthesis off the request thread, one playback queue, notices kept per kind), 13 low, all applied (record section 6). `API.md` has rows for the routes of items C and F; `docs/DEVICES.md` names the two ops. The form for the Mac (`docs/MAC-REQUESTS-20261007.md`) has a new section 6 with the changes since the copy the owner carried: **the owner carries it to the Mac again.** Tests: `test_nudges.py` 8, `test_routine_view.cjs`, the phone, device and inspection suites; the full Python suite with the project's `.venv` Python: 762 tests, 1 error: the item H route test (test_network_devices.CoreTests), which passes once H is wired; everything else OK. The tests must run with `.venv\Scripts\python.exe` (the system Python has no Pillow and answers 503 where the device route says 400). Not done: `tell_jarvis.py` cannot report the finished items until the owner pairs "Claude Code" and types the code here. **Next:** item H (the Wi-Fi device list: `network_devices.py` and `test_network_devices.py` are written and pass on their own, a real read of this PC's neighbour table takes about a second; the wiring into the Core, the Devices page section, the review and the commit follow), then item I only after the owner's Device Access steps, then 1.0.17's remaining steps (the review of item 3.4, the version 4 Stage 7 scripts, a new sandbox Setup rehearsal that records the real shortcut folders, the release-notes entry, build, comparison, regression, zip and Setup rehearsals, sandbox Stage 7, `docs/STAGE7-CHECK-1.0.17.md`, the VM check, the everyday update).
- **2026-10-07, about 07:40 local (Fable 5.1, same session): ACCESS ITEM E BUILT, REVIEWED AND COMMITTED: MEMORY WITH A RELEASE STAMP.** Record `docs/PHONE-ACCESS-1.0.17.md` section 5. Every saved thing (memory, note, task, project) records the release it was saved under (`items.release`, added to an older database at start; stamped by `Store.put` with `Store.release`, which the Core sets to the installed release id or "development <revision>"); every edit path re-stamps (the window, the exact memory commands, JARVIS's own memory tool, the preferred-name row); a restored backup keeps each row's stamp or marks "pre-1.0.17 backup". The model sees "<fact> [saved under <release>]" (`memory.stamped`) and, when a stamped fact is in the context, one rule (`memory.STAMP_NOTE`: an unstamped fact is the oldest; a "development" stamp is newer than any release; a fact about the owner holds; when two facts about JARVIS itself disagree the newer release wins and the older stays saved as out of date; ambiguous ones kept; stamps not read back unasked). The Memory page shows "saved under" or "saved before 1.0.17". Independent review (one reviewer): no high; 2 medium (JARVIS's own correction tool kept the old stamp; a development stamp could not be ordered) and 8 low, all applied (record section 5). Tests: `test_memory_stamp.py` 7; the memory, recall, recovery and review suites; the full Python suite at the commit: 750 tests OK (203.4 s). **NEXT: item F (routine nudges, notices, the announce route), then H (the Wi-Fi list); then 1.0.17's remaining steps.**
- **2026-10-07, about 07:18 local (Fable 5.1, same session): ACCESS ITEM G BUILT, REVIEWED AND COMMITTED: GMAIL AND GOOGLE CALENDAR.** Record `docs/PHONE-ACCESS-1.0.17.md` section 4; the owner's steps `docs/GOOGLE-STEPS.md`. Changed from the plan's first design: no Google sign-in screen (a personal account's OAuth app stays in testing status and its sign-in expires every seven days); Gmail over IMAP (read-only, every fetch a PEEK) and SMTP with an app password, the calendar from its secret iCal address, three lines in the key file (`GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `GOOGLE_CALENDAR_ICS`), nothing that expires, no Cloud project; adding a calendar event is not built ("calendar add" is the owner's separate decision). `mail.py` (search with Gmail's own words, read one mail with its text cut at 6,000 characters, send one plain mail after `check_send`; the two refusals said without the password), `calendar_feed.py` (the feed every ten minutes at most, iCalendar parsed and expanded for a window: DAILY, WEEKLY/BYDAY, MONTHLY, YEARLY, INTERVAL, COUNT, UNTIL, EXDATE, RECURRENCE-ID, cancelled; zones from zoneinfo, else the feed's own VTIMEZONE rules (this PC has no time zone database and the release pins its packages, so none was added), else the local zone with a note). Four tools (50 now): `mail_search`, `mail_read`, `calendar_events` as reads marked for other devices; `mail_send` always asks first (the draft kept as an approval, sent by the owner's approval on the PC or from a device that may approve; the receipt "sent"). The daily briefing's calendar section is real when configured (spoken "In your calendar for the next day: ..."). The device `overview` carries `calendar_connected`, `calendar` (next 24 h, epoch seconds, as the Mac form says) and `mail_unread`, read in the background by `server.Fresh` so the phone never waits on a feed or a mail server. `/api/state.capabilities` flags `mail_connected`/`calendar_connected`; Settings > Connections > Connectors (`static/connectors.js`, a TEST for each through `/api/connections/test` services `mail` and `calendar`); the integration list rows; the shipped personality says what mail and the calendar can do (hash added to `runtime_paths.SHIPPED_PERSONALITIES`); `tools/host/jarvis-request-*` regenerated (50 tools). Independent review (one reviewer): no build-breaking finding; 1 high (the owner's steps named the key file wrongly: it is `config\.env`), 6 medium (a "sent" claim uncaught by the guard; background reads during the stop and unaudited; old daily series lost; a reminder's title taken for the event's; a whole mail pulled and an unknown charset ending the question; a refused recipient called unreachable) and 16 low, all applied (record section 4). Tests: `test_mail.py` 7, `test_calendar_feed.py` 4, `test_connectors.py` 4, `test_connectors_view.cjs`; the interface scripts 25, desktop 60, Intelligence 18; the full Python suite at the commit: 743 tests OK (200.6 s). **Owner, when wanted:** the two parts of `docs/GOOGLE-STEPS.md`, then Settings > Connections > TEST. Still waiting for the "Claude Code" pairing code. **NEXT: item E (memory with a release stamp), then F (routine nudges, notices, announce), then H (the Wi-Fi list); then 1.0.17's remaining steps.**
- **2026-10-07, about 06:45 local (Fable 5.1, new session after the PC's restart, opened in the repo; owner: "continue the access items", then "can you launch jarvis" with a Desktop screenshot, "can we download the new proper app now" and "do this" for everything in 1.0.17, and "when you finish the task your on inform jarvis and then get jarvis to inform me when I ask him for updates"): ACCESS ITEMS C AND D BUILT, REVIEWED AND COMMITTED; THE OWNER'S SHORTCUTS, DELETED BY LAST NIGHT'S SETUP REHEARSAL, RESTORED AND THE CAUSE FIXED.** **Disclosure (`docs/OWN-APP-1.0.17.md` section 6, `docs/release-rehearsal-20261007-1017/INCIDENT-real-shortcuts-20261007.md`):** the owner's screenshot at 06:04 showed no JARVIS shortcut and JARVIS had not started at sign-in. The Setup's own logs on D: proved the cause: the item 3.4 sandbox rehearsal read its `/NOSHORTCUTS` switch with Inno's `{param:}`, which does not see a bare switch, so its install at 01:37:49 and reinstall at 01:39:22 ran the package's installer without `--no-shortcuts` (overwriting the owner's real Desktop and Startup `JARVIS.lnk` with links to the sandbox's 1.0.17 JARVIS.exe) and its uninstall at 01:39:47 removed them. Restored at 06:10 from this repository's `installer.write_shortcuts` with the 1.0.16 launcher values and read back; the installed JARVIS untouched (the owner started it by the shortcut; Core on 127.0.0.1:52882, the phone door on 100.103.95.28:8790). Fixes, reviewed (1 high: a brace inside the new Pascal comment; 2 medium; 6 low; all applied): `installer.py` writes or removes the real shortcuts only for this PC's own install home (`own_home`, the default of install, rollback and uninstall; the answer says `shortcuts: written | removed | skipped | withheld`); the Setup script reads the switch with `HasSwitch` (bare or `=value`); `test_installer.py` (36 OK); the fixed script compiled once from the rehearsal package into `D:\JARVIS-release-work\own-app-rehearsal\setup-compile-check\` (compile check only, never to be run). The 01:35 Setup on D: carries the old script and must not be run on this PC; the next sandbox rehearsal records the real shortcut folders before and after. **Items C and D** (record `docs/PHONE-ACCESS-1.0.17.md` sections 2 and 3): screen analysis from the phone (`App.device_control`: the window controls a device may ask for are reads, switching off and one capture, `server.DEVICE_CONTROLS`; `GET /api/control-requests` read by the window every 3 s; the capture uploaded, described by the model with no tools, kept nowhere; vision checked first; 45 s wait; "The PC's window is not open or did not answer, so this cannot be done from here.") and location with a question (`start.location`, `hello`/`status` `location: true`, `run.location` for that answer only and cleared after, `device_location` in the model's context with "never repeat the coordinates", `maps.directions(location=)` for "from here"). Independent review: no high, 2 medium, 8 low, all applied (section 3). Tests `test_phone_access.py` 21, the interface script tests 24, `test_maps`. The prepared scripts folder `docs/phone-access-work/` applied and removed. **Owner decisions:** "do this": everything stays in 1.0.17 and the installer arrives after the access items (about five to seven sessions). "inform jarvis": built `tools/host/tell_jarvis.py` (`test_tell_jarvis.py`, 2): Claude Code pairs as a device of the one Core (the owner: Settings > Devices > name "Claude Code", kind Computer, PAIR A DEVICE, the code to this session; then the tick "May save memories and tasks" for it), and each finished task is saved into JARVIS's memory through the device route as the owner's exact memory command ("remember that Claude Code reports: ..."), so the owner can ask JARVIS for updates; the device's key lives in `..\claude-device.json` beside the repository, never in git; the Core's port is found from the running JARVIS's socket. Not yet paired: the owner has to read the code. The Mac's 0227 zip is still not carried here. The full Python suite at the commit: 717 tests OK (272.7 s). **NEXT: pair "Claude Code" on the owner's code and tell JARVIS; then item G (Gmail and Calendar: `google_connect.py`, the owner's Google Cloud steps written first), then E, F, H; then 1.0.17's remaining steps (the review of item 3.4 with the version 4 Stage 7 scripts, a new sandbox Setup rehearsal that watches the real shortcut folders, the release-notes entry, the build and checks, `docs/STAGE7-CHECK-1.0.17.md`).**
- **2026-10-07, about 02:35 local (Fable 5.1, same session; the owner: "give jarvis all these permissions and make everything he said he didn't have make him have it", "and make a form for the mac so he can apply to app as well"): ACCESS ITEM A BUILT, REVIEWED AND COMMITTED: APPROVE FROM THE POCKET, AND THIS PC'S TOOLS FOR A PAIRED DEVICE.** Record `docs/PHONE-ACCESS-1.0.17.md` section 1. Two ticks on a device's row in Settings > Devices, off for every device and cleared by a revoke, set only on the PC: "May use this PC's tools" (`devices.tools`: the device's questions get every tool the PC's do except the three only the PC window carries out, under the owner's Permissions switches; includes saving; re-read at every tool call) and "May approve for JARVIS" (`devices.approve`). Device ops `approvals`, `approve {id}`, `reject {id}` (the same list and the same `App.approve` as the PC window; fixed shapes and sentences as in `docs/MAC-REQUESTS-20261007.md`; HTTP 403 "Approving is not allowed for this device." without the tick; the stopped sentence while the stop holds); `hello`/`status` carry `tools`, `approve`, `waiting`, `notices`. A waiting "ask first" call or draft lives 15 minutes (5 before; `server.APPROVAL_SECONDS`); approvals record `created` and `conversation`; an answer from a device writes "approved from <name>" rows and "Approved from <name>: ..." lines, the PC's own words unchanged. Independent review (one reviewer): no high, 1 medium (three window-only tools offered to a device: `permissions.WINDOW_TOOLS`, refused and not offered) and 8 low, all applied (record section 1). Tests: `test_phone_access.py` (11), `test_devices_view.cjs`; the device, permission and approval suites 187 OK; the full Python suite 703 OK before the review fixes and 704 OK after them, at the commit (261.7 s). Also: the Mac's `STATUS.md` of 02:31 received and kept (`phone/ios/mac/STATUS-20261007-0231.md`; `docs/PHONE-APP.md` 10.2): rounds 4 (lock-screen button) and 5 (the app's half of the form, R1 to R6) built there; the 0227 milestone zip not yet carried here (the owner asked for it); the corrected form sent to the owner again with its three changes. The owner then: "finish what your doing then shut down my pc": item A committed, the PC shut down from this session. Items C and D were already written as edit scripts and tests while item A was under review; they are kept, NOT applied and NOT reviewed, in `docs/phone-access-work/` (its README says how to apply them and that the folder is deleted afterwards). **NEXT ("continue 1.0.17" or "continue the access items"): apply, test, review and record items C and D from `docs/phone-access-work/`; then G, E, F, H in the plan's order; then 1.0.17's remaining steps (the review of item 3.4, the version 4 Stage 7 scripts, the release-notes entry, the build and checks, `docs/STAGE7-CHECK-1.0.17.md`). Owner: send the Mac's 0227 zip; the phone's "may save" tick on the PC.**
- **2026-10-07, about 01:55 local (Fable 5.1, new session; it opened in the old OneDrive handover folder and was moved to the repo; the owner pasted the all-time handover, then the Mac session's handoff with `JARVIS-ios-mac-20261007-0135.zip`, then five phone screenshots of JARVIS's own list of what it cannot do and the words "give jarvis all these permissions and make everything he said he didn't have make him have it"): THE MAC'S FIRST MILESTONE COPY RECEIVED AND KEPT; OWNER DECISION: JARVIS GETS EVERYTHING ON ITS LIST.** The repo at the start matched the 02:30 handoff (5ec7a0d, clean). The zip's sha256 d9b342bb… equals the Mac handoff's; the copy is kept unedited at `phone/ios/mac/20261007-0135/` (44 files) and the zip at `D:\JARVIS-release-work\phone\`; `docs/PHONE-APP.md` section 10 records what it holds (round 2 installed on the phone from the Mac, plan check 3 passing there; a UI test target that drives the app from the Mac; round 3 "the command look" with the Overview tab, the orb and the panel kit, reviewed on the Mac and seen on the phone; this session's `assistant.draft` request handled in the app as a dashed "Writing…" bubble; hold-and-send, owner-checked "it worked") and the file-by-file difference from the round-2 record (three new files, seven changed, `StatusView.swift` removed; app version 1.2). Carried in it: `PC-REQUESTS-20261007.md`, the Mac session's item-by-item reading of the owner's words to it at 01:15 local. JARVIS's list, from the screenshots (`docs/phone-evidence/jarvis-locked-list-20261007-*.png`): locked (1) writes from the phone, (2) remote approval, (3) Gmail, (4) Calendar, (5) Spotify, (6) running anything (tests, commands, a shell) from the phone, (7) Mark I, (8) screen capture on demand only, (9) location as memory; its wishes: approve from the pocket, time-aware nudges, memory with a version stamp, connectors; not built: a real installer (1.0.17), the Wi-Fi device list, the Nest camera, Halo glasses, Tesla and home integration, the cloned Qwen voice (fixed in 1.0.16, the owner's selection pending); and no tool for the Wi-Fi part itself. **The owner's decision is recorded as the build order in `docs/PHONE-ACCESS-PLAN.md`** (what the Core builds, what the Mac builds once served, what only the owner can do: the tick for the phone, sign-ins and consents, purchases, hardware; the safeguards: per-device ticks off by default, Face ID on the phone for approvals, the PC's Permissions switches as the one gate, the emergency stop unchanged). The owner also asked for "a form for the mac": `docs/MAC-REQUESTS-20261007.md` holds the exact device routes of 1.0.17 (approvals, approve, reject, notices, announce, devices, start.location, the new hello/status and overview fields) and the app's half item by item (R1 to R7); sent to the owner in the chat to carry to the Mac. The code map behind the design was gathered by one read-only survey agent (approvals are in memory and PC-only; Ask first exists for 12 tools; screen analysis is a window action; no mail, calendar, OAuth, location, nudge or LAN code exists; JARVIS has no shell tool on the PC either, so none is given to the phone: a separate decision). The full Python suite at 5ec7a0d: 693 tests OK in 200.6 s (the 1.0.17 item "run the full suite again after the review edits" is closed). No workflow started (the pasted handover's "Ultracode is off" switched multi-agent mode on by mistake). **NEXT: build the access items in the Core in the plan's order, each tested and independently reviewed; 1.0.17's remaining steps (the review of item 3.4, the version 4 Stage 7 scripts, the release-notes entry, the build and checks) follow once the access items are in, so one VM check and one everyday update carry both.**
- **2026-10-07, about 01:41 local (Fable 5.1, same session; owner: "start 1.0.17", then "find your next stopping point", "write a handoff"): RELEASE 1.0.17 (THE OWN-APP PLAN) UNDER WAY; ITEMS 3.1 TO 3.4 BUILT.** Record `docs/OWN-APP-1.0.17.md`. Commit 09fed5f: the build ships `release\electron\JARVIS.exe` (Electron renamed and stamped with the badge icon, the names and the version by rcedit 5.0.2 from npm via pnpm, pinned by hash) plus the bootstrap in `resources\app`; `desktop/install-paths.cjs` lets the app derive its folders from its own path and hand a stale start to the current release; `installer.py` writes shortcuts straight at JARVIS.exe (also on rollback), JARVIS.ps1 only for older releases; tests (`test_own_app.py`, `test_installer.py` OwnAppTests, `desktop/test/install-paths.test.cjs`). A rehearsal build `1.0.17-09fed5f54c31` (no zip, `D:\JARVIS-release-work\own-app-rehearsal`) and the sandbox rehearsal `docs/release-rehearsal-20261007-1017/` passed all five steps (JARVIS, Teague Industries, 1.0.17.0; a double-click starts JARVIS; the stale start handed over; clean uninstall). Independent review: 1 high (the release regression lacked the build script), 3 medium, 7 low, all applied (record section 2). Item 3.4: the owner installed Inno Setup 6.7.3 for their account; `tools/setup/build_setup.py` + `JARVIS-Setup.iss.in` built `JARVIS-Setup-1.0.17-09fed5f54c31.exe` (405 MB, 119 s) and its sandbox rehearsal passed (silent install 80 s, the Installed-apps entry, launch, reinstall, uninstall through the entry with data kept); not yet reviewed. **DISCLOSURE:** a test's default rollback rewrote the owner's real Desktop and Startup JARVIS shortcuts at 01:10; restored by hand within the minute to the 1.0.16 installer's values and read back; the tests can no longer reach the real folders (record section 5). The full Python suite passed before the review edits (693 tests); the installer, own-app and desktop modules pass after them; the full suite is to be run again. **NEXT: review of item 3.4; the version 4 Stage 7 scripts (designed, not written: the Install phase from the Setup silently with /DIR, /HOME and /NOSHORTCUTS in a sandbox, the Installed-apps entry checked, Launch through JARVIS.exe or JARVIS.ps1, the Uninstall phase through unins000.exe with the entry and the package folder gone, reinstall from the Setup, G7 one update through the Setup, the disc carrying the Setup and its record); the release-notes entry; then the real build of 1.0.17, comparison, regression, zip and Setup rehearsals, sandbox Stage 7, the check plan for the owner's approval.**
- **2026-10-07, about 00:53 local (Fable 5.1, same session; owner: "do the core items" after the order of value was agreed): THE THREE CORE ITEMS FROM THE PHONE CHECKS BUILT, TESTED AND REVIEWED, FOR RELEASE 1.0.17.** Record `docs/PHONE-CORE-FIXES-20261007.md`. (1) Replies streamed to the phone: `server.py` no longer excludes a device's question from streaming; a device run gets the same `assistant.draft` events through its `events` route (the whole draft so far, only what the claim checks passed), refreshed at most every half second (`DEVICE_DRAFT_SECONDS`), when the PC's "Show replies while they are written" setting is on and the provider is Qwen; the finished reply unchanged. The phone app shows nothing new until the Mac session handles `assistant.draft` (a request for the owner to carry). (2) "Remember that.": `memory.py` pointer command (spoken forms too) saving the line before it in the conversation, the owner's line as said, JARVIS's as "JARVIS said: ..."; other memory commands and JARVIS's confirmations skipped; the `save_item` switch and the activity row apply; with Ask first the line is found at once and carried in the approval (review finding 1); a credential refused as the answer; before, the local "remember <words>" rule saved "that.". (3) The action guard keeps the reply and appends the truth under it (the receipts, or the note that no action was carried out) instead of replacing it; the watched wording deliberately not narrowed (reasoned in the record). Independent review (one reviewer): 1 high, 2 medium, 5 low; all applied except the narrowing (section 5). Tests: four pinned the old behaviour and were re-pointed (`test_answer_evidence`, `test_reply_stream`, `test_offline_core`); new `test_phone_core_fixes.py` (18 tests); the full Python suite 682 tests OK (257 s; the desktop and interface suites untouched: no JavaScript changed). Records updated: PHONE-CORE-1.0.16.md section 6, DEVICES.md, REPLY-STREAM.md, OFFLINE-ANSWERS.md, PERMISSIONS.md. **NEXT: the Mac session's `assistant.draft` handling (request given to the owner); then release 1.0.17 (the own-app plan) carrying these three; its build, checks, VM check and everyday update on the owner's approvals.**
- **2026-10-07, about 00:16 local (Fable 5.1, same session; owner's photos of the Mac session, then "app on the mac"): THE APP'S ROUND 2 COMPILED ON THE MAC; THE APP MOVED TO THE MAC.** The owner's Claude Code session on the Mac, from the paste-ready brief, verified the 23:54 zip's hash, removed the "Theme 2"/"PairingView 2" copies, placed the thirteen files and the icon folder, found the project's App Icon setting EMPTY in Debug and Release (the cause of the placeholder icon) and set it to AppIcon, added the Face ID Info key beside the microphone key, and compiled the app with a compile-only build (signing off, a temp build folder; the sandbox allowed once for that command): Build succeeded, no fix round. Not yet run on the phone; the eight checks of README-round2 and plan check 3 are open. The owner asked whether to turn the Mac's sandbox off: told no (sandbox on, strict mode off is right). Then the owner decided "app on the mac": the Xcode project on the Mac is now the app's source of truth, written by the Mac session; this session keeps the Core, the desktop app, the releases and the device routes, and the repo's phone/ios becomes the record copy that receives the Mac's zips at milestones (`docs/PHONE-APP.md` section 9; one paragraph added to CLAUDE.md). Handover bundle sent in the chat: `JARVIS-ios-handover-20261007-0015.zip` (103,181 bytes, sha256 5cef740a…; the Mac's CLAUDE.md and STATUS.md, kept here under `phone/ios/mac/`, the reference documents, the Core's device code for reading, the design mock, the sources' hash list) with a paste-ready brief for the Mac session. **NEXT (the Mac session): the phone run and the checks; Core-side, on the owner's word: the device-run streaming change, "remember that", the action guard; then release 1.0.17 (the own-app plan).**
- **2026-10-06, about 23:56 local (Fable 5.1, same session; owner: "let's make some big moves on the app", "give me the zip here in the chat", "i am on claude code on mac"): THE IPHONE APP'S ROUND 2 WRITTEN, REVIEWED AND ZIPPED FOR THE MAC; NOT YET BUILT.** The agreed list built in `phone/ios/JARVIS/` (thirteen Swift files, `SiriIntents.swift` new): the conversation's lines reloaded after a relaunch (check 3), the header at the phone's width, the stale stop note cleared, the icon steps, Bluetooth headsets and interruptions, the screen awake while listening, thinking, working or speaking, "Lock with Face ID" (off by default; needs the Info entry NSFaceIDUsageDescription; STOP ALL on the lock screen), the Voice button with a vibration on the reply, and Siri ("Hey Siri, ask JARVIS" opens the app with the question; "Hey Siri, stop JARVIS" raises the stop from the background). NOT DONE and not possible app-only: replies appearing as written (the Core keeps a device's answer whole, server.py line 1052; the 22:55 handover's note that the Core sends the pieces to the phone was wrong; a Core change for a later release on the owner's word). Independent review (one reviewer): no compile error by reading, 1 high (the Face ID re-prompt loop), 2 medium, 7 low, all applied (`docs/PHONE-APP.md` section 8). Records: `docs/PHONE-APP.md` sections 7 and 8, `docs/PHONE-V1-RESULT.md` section 4 corrected, `phone/ios/README-round2.md` (the owner's Mac steps and eight checks). Zips sent to the owner in the chat, both in `D:\JARVIS-release-work\phone`: `JARVIS-ios-round2-20261006-2345.zip` (before the review, at the owner's request; superseded) and `JARVIS-ios-round2-20261006-2354.zip` (957,413 bytes, sha256 d6ba9671…; the one to use). The owner opened Claude Code on the Mac and was given a paste-ready brief for that session (Local, the Xcode project folder: verify the hash, delete the "Theme 2"/"PairingView 2" copies, place the files and the icon folder, add INFOPLIST_KEY_NSFaceIDUsageDescription beside the microphone key, xcodebuild for a device, then Command-R in Xcode); told that a Mac session knows nothing of the PC's sessions and that the Remote Control entries are the PC's folders. **NEXT: the owner builds on the Mac (errors come back here), runs the eight checks of README-round2 section 5 and check 3; then `docs/PHONE-V1-RESULT.md` closes; TestFlight when wanted; then release 1.0.17 (the own-app plan).**
- **2026-10-06, about 23:30 local (Fable 5.1, new session; it opened in the old OneDrive handover folder and was moved to the repo; the owner pasted the all-time handover, then asked "how can we make it so the app is the ONE JARVIS ONE CORE but can function without the need of the pc", then "keep pc on"): OWNER DECISION: THE PC STAYS ON; THE CORE STAYS ON THE PC.** Three ways that keep one Core were offered (a Windows mini PC at home, about $300 to $600 once, recommended; a Windows VM in the cloud, about $40 to $70 a month, data off-site; keep the desktop PC on, no cost and no code), and the two shortcuts excluded because they break ONE CORE ONE MEMORY (a Core on the phone; the app talking to Qwen directly when the Core is unreachable). Told what a move would need: a remote-Core mode in the desktop app (it starts its own Core today and talks only to 127.0.0.1; the Core would have to serve the desktop interface on the private-network address, networking owner-only), the PC's own abilities routed to the PC as a device (screen analysis already comes from the window; music through winmm, "open on this PC" and the CPU and memory readouts run on the Core's machine), the data moved by the backup and restore path, and the rule "the Core lives on the owner's PC" changed by the owner; a sleeping PC cannot be woken from the phone through Tailscale. The owner chose "keep pc on": no purchase, no Core change for hosting, the binding rule unchanged; the phone reaches JARVIS whenever the PC is on, signed in, running JARVIS with the switch on, and connected to Tailscale. Record and the owner's one-time steps: `docs/PHONE-ALWAYS-ON.md` (sleep off while plugged in by powercfg or the Settings page; Tailscale "Run unattended" and key expiry disabled in the admin console; Windows Update set to notify before a restart; lock with Win+L, never sign out; a check from the phone on cellular). Known gap recorded: after a restart JARVIS is off until the owner signs in (closers for a later owner decision: automatic sign-in, or a Core that starts at boot, a design of its own). Also this session: the OneDrive folder's memory note refreshed to the 1.0.16 state; no workflow started (the pasted text's "Ultracode is off" switched multi-agent mode on by mistake). **NEXT: unchanged: the app's next round on the owner's "continue the app"; then release 1.0.17.**
- **2026-10-06, about 22:20 local (Fable 5.1, same session; owner: "how do I connect it to the actual Jarvis?", then photos and "still not working", "it paired but the app just crashes"): THE PHONE PAIRED AND TALKING TO THE CORE.** Owner steps, Claude reading only: Tailscale account (Google) and the Windows client installed and connected (`thegrizzlybear` 100.103.95.28); the iPhone's Tailscale signed in; Settings > Devices > Private network ticked; a pairing code. First failure "JARVIS cannot be reached": Claude's read-only checks found the door listening on 100.103.95.28:8790 (python, the 1.0.16 release), a TCP test from the PC succeeding, the Tailscale interface classed Private with Tailscale's inbound rule allowing it, but the PC's Tailscale knowing 0 peers and the console showing 1 machine: the phone had signed into a different Tailscale network; the owner logged out on the phone and signed in again with Google; the console then showed 2 machines and the PC's client listed `localhost`/iphone-15 at 100.64.112.19 online. PAIR succeeded; the app then crashed at the Ask screen: the microphone permission request without a "Privacy - Microphone Usage Description" entry in the project's Info list (iOS ends the app); the owner added the entry and the app opened: ONLINE, Core 1.0.16-fccde24e2cc6, AI READY, CPU 3 %, LINK 22 ms, MEMORY 27 %, STOP CLEAR, STANDING BY, and two exchanges answered (screenshots in `docs/phone-evidence/`). Noted: no App Transport Security row in the Info list, yet plain HTTP to the address works (iOS exempts IP addresses and unqualified names); the header at the phone's width wraps ONLINE and squeezes STOP ALL (fix round); the icon still the placeholder (parked by the owner). `docs/PHONE-V1-RESULT.md` written as in progress with the section 10 table. At 22:20 the owner's three screenshots on 5G with Wi-Fi off: a held-microphone question heard and shown as text, THINKING "On the PC", SPEAKING "In JARVIS's voice", the answer, a second exchange; link 183 to 215 ms: checks 1 (cellular) and 2 (hold to speak, spoken reply) recorded as done (`docs/phone-evidence/phone-app-cellular-*-20261006-2220.png`). At 22:23 to 22:24 six more screenshots: the PC's Devices page (the door's green line with the full Tailscale name, the phone online, last seen just now, all four ticks), Chats (1 conversation, ACTIVE, 11 messages, opened with times and CONTINUE), Status (reached, 24 ms, Core 1.0.16, CPU 5 %, memory 27 %, storage 92 %, link 24 ms, Core up 1 h 42 min, 4 open tasks, three projects), STOP ALL from the phone (EMERGENCY STOP, STOP ON) and after RESUME on the PC (STANDING BY, STOP CLEAR): checks 4, 5, 6 and 10 recorded as done. Defect seen: the yellow stop note stays on the Ask screen after the resume until the next action (`docs/PHONE-V1-RESULT.md` section 2, item 7). Storage 92 % is the PC's C: drive. Then (22:28 to 22:32) the owner's last screenshots: REVOKE on the PC sent the app back to the pairing screen with "Device key invalid or revoked" and the address kept, paired again; Tailscale off on the phone gave NOT REACHED / CORE NOT REACHED with the last readouts kept; "Remember that." answered "Remembered: that." and the PC's Memory page shows the memory "that." at 22:30:34 (the exact memory command stores the words after "remember" and does not resolve "that", a Core-side improvement for later); and the owner's correction on check 3: closing the app mid-conversation shows a fresh one (the conversation id is restored, the lines are not reloaded; fix in the app's next round). `docs/PHONE-V1-RESULT.md` now reads VERSION 1 CHECKED, 9 of 10, with the defects list (items 4, 5, 7, 9, 10) and version 2 listed for the owner's decision. At 22:36 the owner's typed question on the phone ("list improvements/additions needed in the next build for the app") came back as "No matching action result was recorded for this request. Completion is not confirmed.": the Core's `answer_evidence.action_guard` replaced the reply because its wording claimed finished work with no action tool in the turn, a false positive on prose, the same on the PC (`docs/PHONE-V1-RESULT.md` section 2, item 11; a Core-release candidate: narrow the guard and append the caveat instead of replacing the reply). The owner asked what else to add to the app's next round; offered (app only, no Core change): replies appearing as written, Bluetooth headsets and interruptions, screen awake while listening or speaking, Face ID on open, the speak-replies button on Ask with a vibration, the Siri shortcut, text size; Core-side for 1.0.17 or later on the owner's word: the camera ("look at this"), "remember that", QR pairing, the PC's chats on the phone, the action guard. The owner then: "can we add siri to the next build": agreed. **THE APP'S NEXT ROUND IS AGREED AND NOT STARTED (no code written; the session ended on "handoff"):** the four fixes (the conversation lines reloaded after a relaunch, the header at the phone's width, the stale stop note, the icon) plus replies appearing as they are written (the Core sends `assistant.delta` only when the PC's streaming setting is on), Bluetooth headsets and audio interruptions, the screen awake while listening or speaking, Face ID on open (needs the Info entry "Privacy - Face ID Usage Description"), the speak-replies button on the Ask screen with a vibration on the reply, and "Hey Siri, ask JARVIS" through App Intents (one new Swift file, no extra Xcode target). The code read for it: SessionModel.swift (connect, checkStatus, refreshHealth, follow, holdToSpeak, stopEverything, open), AskView.swift, Theme.swift (ScreenHeader, Caption), AudioRecorder.swift, AudioPlayer.swift, Keychain.swift (AppSettings), CoreClient.swift signatures, Models.swift (ConversationHistory). **NEXT: build that round in the repo (one independent reviewer), zip it for the Mac with the steps, the owner builds and runs check 3 again; TestFlight when the owner wants it; then release 1.0.17.**
- **2026-10-06, about 21:15 local (Fable 5.1, same session; owner's Xcode screenshots and "what am i doing"): THE LOOK BUILT AND SEEN ON THE PHONE.** The owner's first drag put the two Swift files and the three pictures into Xcode's file list (giving `PairingView 2` and `Theme 2` beside the old files, the pictures as loose files); fixed by deleting the old Swift files and the loose pictures, dragging the two pictures into the Assets column and adding an AppIcon set with the 1024 PNG (the icon had first landed as an image set `AppIcon-1024`, removed). Build and run passed; the pairing screen shows the badge in a ring, the space scene faint behind it and the orbital graphic (screenshot kept in `docs/phone-evidence/`; `docs/PHONE-APP.md` section 6 updated). The home-screen icon still showed iOS's placeholder grid after the run (iOS keeps the icon of an installed app): the owner was told to delete the app from the phone and run it again from Xcode. **NEXT: unchanged (the owner's Tailscale steps and the pairing; then release 1.0.17).**
- **2026-10-06, about 20:55 local (Fable 5.1, same session; owner: "step 1 done" to "step 5 done"): THE EVERYDAY JARVIS UPDATED TO 1.0.16, `EVERYDAY_UPDATE_COMPLETE`.** Step 1 (09:16:28Z): jonny, not elevated, launcher hash equal, package hash equal, 1.0.15 current and verified, 0 processes, 15.7 GB free, unpack 15.6 s. Step 2 (09:17:20Z): backup 4134e30f… with 1.0.15's own code, 351 files, 3,171,478 bytes, verified, test restore passed with all 21 table counts equal (1,361 messages), copy on D: hash-equal, program still verified. Step 3 (09:19:48Z): 1.0.16 installed in 108.5 s wall (verify package 7.2, copy 89.9, verify copy 9.4, stop 0.7, switch 1.1), verified, current 1.0.16 with 1.0.15 previous, database byte-for-byte unchanged, shortcuts kept, JARVIS not started. Step 4 (owner-reported, 09:25:56Z, no photo): "step 4 done" after the seven-point list; Claude's read-only look: 0 processes after the quit, current.json on 1.0.16, four release folders, the config\music folder present. Step 5 (restart-check.json): boot 20:28:18, sign-in 20:34:35, JARVIS 1.0.16 started by itself at 20:40:19 with --login-launch, 5.7 min after sign-in, all 8 processes from the 1.0.16 release. Rollback not used; 1.0.15, 1.0.14 and 1.0.11 stay installed. `update-evaluation.json` and `MANIFEST.json` written in `D:\JARVIS-update-1.0.16\evidence`, repo copy `docs/update-1.0.16-evidence/` (every file checked against the manifest). Open: the Private network switch (off until Tailscale), removing 1.0.11 and 1.0.14 later (about 2.4 GB) on the owner's word, the Qwen voice choice. Also this session: the repo project's memory folder is the one loaded when the session opens in the repo (the OneDrive-folder memory is not); today's state written there. **NEXT: the owner's Tailscale steps and the pairing; the look on the Mac; then release 1.0.17 (own-app plan, approved).**
- **2026-10-06, about 20:15 local (Fable 5.1, same session; owner: "I approve the update of my everyday JARVIS to 1.0.16"): THE UPDATE APPROVED; THE LAUNCHER PLACED.** Recorded in `../governance/UPDATE-1.0.16-APPROVAL-RECORD.json` (issued 09:11:04Z; plan sha256 6d7e5e7b… as committed in 47cca56; builds, preconditions, tool hashes, places, effect). Placed: `D:\JARVIS-update-1.0.16\tools\Invoke-EverydayUpdate.ps1` (1abb0be5…) and `update-step.cmd` (9c469bd4…), both hash-equal to the repo, `update-authorized.json` (final 1.0.16-fccde24e2cc6, previous 1.0.15-63362929d7ad, the pkg-1.0.16 zip and its hash 58bba742…); `D:\JARVIS-update-1.0.16\evidence\prep-tools-hashes.txt`; repo copies in `docs/update-1.0.16-evidence/`. The owner was given step 1 (quit JARVIS completely, double-click update-step in the jonny account, say "step 1 done"). **NEXT: steps 1 to 5 with Claude checking each record; then the evaluation EVERYDAY_UPDATE_COMPLETE or not; then Tailscale and the pairing; then release 1.0.17.**
- **2026-10-06, about 20:20 local (Fable 5.1, same session, no new owner instruction): THE EVERYDAY-UPDATE PLAN FOR 1.0.16 WRITTEN AND ITS LAUNCHER REHEARSED.** `tools/host/update-1.0.16/Invoke-EverydayUpdate.ps1` is the 1.0.15 launcher with three lines changed (its header, the plan it names, the default folder `D:\JARVIS-update-1.0.16`; sha256 1abb0be5…), `update-step.cmd` byte for byte (9c469bd4…); the 1.0.14 and 1.0.15 files untouched. `docs/release-rehearsal-20261006-1016/rehearse-everyday-update-1016.ps1` is the 1.0.15 harness with the builds moved one release up (every changed line listed by the copying script). Rehearsal 20:06-20:09 local, 13 of 13 PASS: 1.0.15 installed into the sandbox home and started once; refused without approval and while JARVIS ran; step 1 (hash equal, verified, unpack 18.2 s); step 2 (backup 174 files with 1.0.15's own code, verified, test restore passed, copy hash equal); step 3 (update 28.5 s: verify package 8.1, copy 11.0, verify copy 7.8, stop 0.7, switch 0.7; database byte-for-byte unchanged); 1.0.16 on the same data; rerun nothing; rollback with its approval file PASS (7.4 s); rerun nothing; the owner's JARVIS not running (0 processes before and after), 0 sandbox processes left. `docs/UPDATE-EVERYDAY-1.0.16.md`: what 1.0.16 brings (the Private network switch off until the owner turns it on, pairing limits, device reads and the per-device tick, music from files, the Qwen voice link), the two owner checks (no key-file change needed; C: 15.7 GB free, about 1.2 GB more, four releases installed afterwards), what is proven (the PC checks, the VM check with the 646 s disposition, the data changes: table `music`, the devices column, the switch's state in `control`, the folder `config\music`; 1.0.15's personality text unchanged by 1.0.16), the five steps and the rollback, the step-4 check list (About 1.0.16, Devices switch off with the Tailscale line, Music panel, Voice preview with Qwen), six acceptances, the wording. **NEXT: the owner's approval; then the launcher placed in D:\JARVIS-update-1.0.16\tools with hashes and update-authorized.json, steps 1 to 5; then Tailscale and the pairing; then release 1.0.17.**
- **2026-10-06, about 20:10 local (Fable 5.1, same session; owner: "stage 7 done" after the photo ALL STAGE 7 STEPS PASSED): STAGE 7 CHECK OF 1.0.16 EVALUATED: `STAGE_7_COMPLETE`, 27 OF 27.** Read from D: only: the five guest runs (Install 9 checks 07:04:45 to 07:35:49Z; AfterRestart 2, restart proven by boot id 7 to 8, login launch seen after 16.9 s; Uninstall 4, 10,675 files removed, 0 left, reinstall and final stop; Update 7, the 1.0.15 zip hash equal, its package extracted in 1094.6 s, 1.0.15 installed and running with both memories, update while running 334.4 s wall, rollback 95.0 s, update again 191.5 s, all verified, 8 processes none from the other release, final stop 0; Interrupt 5, killed after 113.8 s at 3,278 of 10,675 files, 1.0.15 still current and answering, update again 222.8 s, incoming folder gone), the driver log (every phase passed, 'all phases passed' at 08:56:02Z), the host start records (this time the launcher's own start record exists: LocalhostReachable = 0 from VBox.log; FRESH-PREREQ restored from STAGE7-PASS-1.0.15 with both discs hash-checked) and the snapshot record (STAGE7-PASS-1.0.16-fccde24e2cc6, uuid c91c7f1a-24dc-4bff-80eb-a21fa62ea264, 08:59:38Z, poweroff, .vbox copy read: currentStateModified false). Timing: install 646.4 s outside the 600 s bound (copy 300.9 s, verify 224.9 s; the same files copied in 100.0 s and 35.4 s and verified in 127.4 s and 105.7 s later in the same pass; 27.6 s on this PC): a VM limitation under the owner's rule written into the plan, reported to the owner who may still ask for a re-measurement; update 334.4, rollback 95.0, update again 191.5, after interruption 222.8, stops at most 4.6 s. Deviations noted only: 4 processes at the first sign-in after the restart; the previous package's 18-minute extraction. Not covered: as for 1.0.15 plus the private-network door, a paired device, music through speakers, the Qwen voice. Records: `D:\JARVIS-stage7\1.0.16-fccde24e2cc6\evidence` (MANIFEST.json, 8 files, sha256 30879bf3…) and the guest folder (MANIFEST.json, 38 files, sha256 883ee05d…); repo copy `docs/stage7-1.0.16-evidence/` (every copied file checked against its manifest hash). The owner's everyday JARVIS was not running at Claude's one read-only process count (0 processes). **NEXT: the everyday-update plan `docs/UPDATE-EVERYDAY-1.0.16.md` (the 1.0.15 launcher copied for 1.0.16, rehearsed in a sandbox on D:) for the owner's approval; then Tailscale and the pairing; then release 1.0.17.**
- **2026-10-06, about 19:50 local (Fable 5.1, same session; owner: a zip `TeagueJARVIS-iOS.zip` and "can we apply this", then "apply the look", then "draft a visual"): THE LOOK APPLIED TO THE IPHONE APP, REVIEWED, ZIPPED FOR THE MAC.** The zip (668,502 bytes, sha256 31906f3c…) held a SwiftUI mock-up of our pairing screen made elsewhere from a picture: four Swift files (UI only, PAIR sets a flag, no Core, no Keychain, no other screens) and two pictures (the badge as JPEG, a space-station scene 1536 x 864); applied as it was it would have replaced the working app with one screen that cannot pair; reported, and the owner chose the look only (three things offered: badge logo, space background, orbital graphic). Kept as the design record in `docs/design/teague-ios-mock-20261006/` (its Swift files and README). Built into our files: `Theme.swift` (PageBackground layers image set `JARVISBackground` at 12 percent under a vertical shade and the radial glow, guarded by `UIImage(named:)`; `JarvisMark` shows image set `TeagueBadge` in a cyan ring at 40 pt, the drawn T when the set is missing) and `PairingView.swift` (`OrbitalGraphic`, a TimelineView like the Ask screen's CoreRing, still under Reduce Motion, in place of the idle CoreRing). Assets in the repo: `phone/ios/assets/TeagueBadge.png` (512 px from the owner's badge, sha256 0b205466…) and `JARVISBackground.jpeg` (the owner's file unchanged, sha256 190ff1c2…); the image sets are added by hand in Xcode's asset catalog. A draft picture was rendered first (HTML mock, Edge via Playwright, 393 x 852 at 3x) and sent to the owner. Independent review (one reviewer): no compile error found by reading, no high or medium, 4 low: the core glow's radius (applied: end radius 40) and the unguarded background image (applied: the same guard as the badge); the 30 fps TimelineView while the pairing screen exists (accepted) and a non-square badge overflowing the circle (noted). Zip for the Mac, made with Python's zipfile: `D:\JARVIS-release-work\phone\JARVIS-ios-look-20261006-1946.zip` (1,605,800 bytes, sha256 cc87bdab…: the two Swift files, the two assets, `AppIcon-1024.png`, `README-look.md`); `phone/ios/README.md` section 7 added. The owner's Mac steps: the two pictures into Assets (image sets named TeagueBadge and JARVISBackground), the icon into AppIcon, the two Swift files replaced, Command-B, Product > Run. The VM check meanwhile (guest driver log): AfterRestart PASS 07:55:30Z (restart proven by boot id 7 to 8), Uninstall PASS 08:07:39Z, Update PASS 08:40:44Z, the interrupted-update phase started 08:40:47Z (X0 written). **NEXT: the owner: the VM check's steps 5 to 7 ("stage 7 done"), the look on the Mac; Claude: the evaluation and the everyday-update plan; then Tailscale and the pairing; then release 1.0.17.**
- **2026-10-06, about 19:45 local (Fable 5.1, same session; owner: "I approve the own app plan can we make the app icon this image as well as the app icon for the ios app" with the Teague Industries badge attached, then "I approve the own-app plan"): THE OWN-APP PLAN APPROVED; THE ICON FILES MADE.** The first message differs from the plan's wording by the hyphen; reported to the owner, who typed the exact wording in the same turn; both recorded (`../governance/OWN-APP-PLAN-APPROVAL-RECORD.json`, plan sha256 7f2803a6… as committed in 487485a, issued 2026-10-06T08:23:24Z, recorded 08:24:51Z; repo copy `docs/own-app-evidence/`). Decisions: D1 Inno Setup (the owner installs it once), D2 yes, D3 later, D4 no, D6 dropped; D5 changed: the owner's badge (1254 x 1254 PNG, sha256 2e64494c…), kept byte for byte at `static/assets/branding/teague/teague-industries-badge.png`. Made from it with Pillow 12.3.0 and checked visually (the chrome T alone at 64, 48, 32, 24 and 16 px, the whole badge at 256 and 128 px): `desktop/jarvis.ico` (sha256 1c78eef2…), `desktop/tray.png` (32 px, sha256 e9192d20…), `phone/ios/AppIcon-1024.png` (1024 px RGB, sha256 bc6d2687…; copy `D:\JARVIS-release-work\phone\JARVIS-AppIcon-1024.png`). The plan's status line, icon paragraph (3.1) and D5 row updated; nothing else of 1.0.17 built (it starts after 1.0.16 and the phone, plan section 6). Owner steps given: AirDrop the 1024 PNG to the Mac, Xcode > Assets > AppIcon, drop it on the slot, Product > Run; install Inno Setup when convenient. **NEXT: unchanged (the 1.0.16 VM check's steps 4 to 7, the evaluation, the everyday-update plan, Tailscale and the pairing); then release 1.0.17.**
- **2026-10-06, about 19:35 local (Fable 5.1, same session; owner: "run tests and make sure everything is working", "also when can we make jarvis been his own app, launched by himself not electron", "so how can we make jarvis his own app", "write the own-app plan"): ALL DEVELOPMENT SUITES PASS AT d02ca32; THE OWN-APP PLAN WRITTEN.** Tests run at below-normal priority while the owner's VM check ran (19:08 to 19:12 local): Python 664 OK (199 s), desktop 52 pass, Intelligence 18 pass, 24 of 24 interface scripts PASS, nothing on any error stream (the runner lost the exit codes, a PowerShell 5.1 quirk; judged by the last line of each output and empty stderr). The VM check's second run seen in the owner's photos: AfterRestart PASS (18:55:11), Uninstall PASS (U1 to U3), Update started 19:07:39 with G1 PASS, unpacking the 1.0.15 zip at 19:08. `docs/OWN-APP-PLAN.md`: what is wrong today (shortcut > PowerShell > bare electron.exe; the tray image `desktop/tray.png` is missing from the repo; no Installed-apps entry), what the owner gets, how it is built (JARVIS.exe stamped with rcedit from npm and a `resources\app` bootstrap; the app derives home, data, config, models and profile from its own path and redirects a stale start through `current.json`; shortcuts straight at JARVIS.exe, rewritten also on rollback; JARVIS-Setup.exe built with Inno Setup around the unchanged installer.py engine, per user, silent switch, sandbox-home parameter, Installed-apps entry whose Uninstall keeps the data; version 4 Stage 7 scripts installing from the Setup.exe), outside the release (native shell, faster sign-in start, rollback button, signing), decisions D1 to D6, order and size (about two Claude sessions, then the owner's VM check and everyday update), risks (unsigned Setup.exe warns on other PCs; 500 MB; Inno Setup is a system-wide install by the owner). Facts checked for it: the Stage 7 driver recognises JARVIS processes by their path under `releases\` (not by the name electron.exe) and launches by the Desktop shortcut; rollback does not rewrite shortcuts today; no 7-Zip, Inno Setup, NSIS or PyInstaller on this PC, Pillow 12.3.0 in the venv. **NEXT: unchanged (the VM check's steps 4 to 7, the evaluation, the everyday-update plan, Tailscale and the pairing); the own-app plan waits for the owner's approval and is built after those.**
- **2026-10-06, about 19:05 local (Fable 5.1, new session opened from the pasted handover and moved to the repo; no owner instruction beyond the handover, questions and photos): THE VM CHECK'S STEP 3 PASSED; THE IPHONE APP BUILT AND RUNNING ON THE PHONE.** Step 3 (the Install phase) read from the guest folder `stage7-1.0.16-fccde24e2cc6\stage7-20261006-070445`: SUMMARY overall PASS, 18:04:42 to 18:35:49 local; E0 and I1 to I8 all PASS (the zip matches the record, 0 payload mismatches; extract 738 s; install 646 s = verify package 113 + copy 301 + verify copy 225 + switch 0.1, over the 600 s bound as in the 1.0.15 check with the same cause pointer, the owner's disposition rule of 2026-10-06 applies at the evaluation; first launch ready in 134 s with 8 processes and the memory saved; a second Core refused, pid unchanged; offline speech recognition 31.8 s cold and 2.1 s warm; stop on request, 0 processes, restart ready in 8.5 s with the memory kept); the driver log reads "phase passed" for Install, boot id 7. The host start record (`vm\stage7-start-20261006-065935.json`, `start-20261006-065935.json`): restored FRESH-PREREQ from STAGE7-PASS-1.0.15-63362929d7ad (currentStateModified false), the 1.0.15 disc on SATA port 1 and this check's disc on port 2 with the recorded hashes, LocalhostReachable = 0 from VBox.log, every snapshot kept. The owner was given step 4 (quit JARVIS completely, Start > Power > Restart, sign in, wait a minute, drive E:, stage7 again). **On the Mac:** the twelve files dragged in (Xcode's bridging-header prompt: Don't Create), Build Succeeded at the first attempt at 18:46, signing clean (automatic, team Benjamin Teague, managed profile, development certificate), destination the owner's iPhone, Product > Run after the one-time "Copying OS library symbols"; at 19:00 the app opened on the phone with the pairing screen exactly as designed (picture `docs/phone-evidence/phone-app-first-launch-20261006-1900.png`; `docs/PHONE-APP.md` status updated). Told the owner: nothing to type into the pairing screen yet (the PC's Tailscale name or 100. address, port 8790 and the eight-digit code come after 1.0.16 is the everyday JARVIS); Tailscale is the owner's own install (plan step 6, `docs/PHONE-TAILSCALE-STEPS.md`), best after the VM check has shut down. The pasted handover's "Ultracode is off" switched multi-agent mode on again by mistake; no workflow was started. **NEXT: the owner's steps 4 to 7 of the VM check ("stage 7 done"), then the evaluation and the everyday-update plan for approval; then Tailscale and the pairing; then the plan's section 10 checks and `docs/PHONE-V1-RESULT.md`.**
- **2026-10-06, about 18:00 local (Fable 5.1, new session opened from the pasted handover and moved to the repo; owner: "continue 1.0.16", "also I want to add the qwen voice", "fix it in 1.0.16", "let's focus on the app for now"): RELEASE 1.0.16 BUILT AND CHECKED ON THIS PC (BUILD 2), THE QWEN CLONED VOICE FIXED, THE STAGE 7 CHECK PLAN WRITTEN, THE IPHONE APP WRITTEN.** Record: `docs/release-rehearsal-20261006-1016/README.md`. Development suites at de8fbc1: 663 Python, 52 desktop, 18 Intelligence, 24 interface scripts; `release-notes.json` counts corrected (commit 4e54fc9); the version 3 Stage 7 tools unchanged (hashes equal to the 1.0.15 approval), their decision tests run again (18 and 21 cases, all pass). **Build 1 `1.0.16-4e54fc946bc3` (commit 4e54fc9):** comparison with 1.0.15 clean (pinned inputs identical; 13 source files changed, 4 added), release regression PASS, zip install PASS (30 s); superseded, never offered. **The Qwen voice:** the owner's Alibaba account has one cloned voice (made 2026-09-18); with its ID in the key file the owner-run tool said "no usable sound link": Alibaba hands out the finished sound as a plain `http://` link on `dashscope-result-bj.oss-cn-beijing.aliyuncs.com`, which `providers.qwen_speech` and the tool (https links only) refused. **Fix (commit fccde24):** `providers.qwen_result_link` fetches such a link over https from the same Alibaba server; anything not on `*.aliyuncs.com`, a scheme other than http or https, an unusual port or a value that is not a link is refused; the download carries no key. The tool's `ResultLink` is the same rule and a refusal names the address; `test_qwen_voice.py` (9), `check_qwen_voice_tool.py` 38 of 38; `docs/SPEECH.md` section 2 records it. Independent review: no high, 1 medium, 4 low, all applied. **Owner decision "fix it in 1.0.16":** the number stays 1.0.16 although the program changed between the builds (the convention gave 1.0.12 and 1.0.13 the next number) because the approved phone plan names 1.0.16 and nothing of build 1 was offered. Development suites on the final tree: 664 Python, 52 desktop, 18 Intelligence, 24 scripts (one load-related timeout of the automatic-backup thinning test in a first run, passed alone and in a second whole run). **Build 2 `1.0.16-fccde24e2cc6` (commit fccde24): zip 525,906,502 bytes, sha256 `58bba7423cf0668ff7684e9370865b9951e473eb1e0818c9437bf4287032d23a`; comparison with 1.0.15: pinned inputs identical, 14 changed, 4 added, 0 removed; against build 1 only `providers.py` and `release-notes.json`; release regression PASS (664 Python with 1 skipped as always, 52 desktop, 18 Intelligence, 24 scripts; 1,350 s with the disks busy); zip install PASS (70 s); sandbox Stage 7 pass 1.0.15 -> 1.0.16 with the version 3 scripts: ALL STAGE 7 STEPS PASSED** (16 min: install 27.6 s, update while running 134 s wall under the owner's 40 GB folder move, rollback 11.6 s, update again 36.2 s, the interrupted update killed at 3,351 of 10,675 files and rerun in 32.6 s; live JARVIS processes 8 before and 0 after because the owner quit their JARVIS by hand during the run, "yes i did"; sandbox processes 0). `D:\JARVIS-release-work\pkg-1.0.16` holds build 2 (build 1's files removed from it; both builds stay in `D:\JARVIS-release-work\release`). **`docs/STAGE7-CHECK-1.0.16.md` is READY FOR THE OWNER'S APPROVAL** ("I approve the Stage 7 check of 1.0.16"): the same version 3 tools; two notes meet the two launcher follow-ups of the 1.0.15 check (leave the launcher window open during the VM's power-on; this check's disc is drive E:, both discs being named JARVIS_S7); the Gate 20 bound stated with the owner's disposition rule of 2026-10-06; start point the snapshot STAGE7-PASS-1.0.15-63362929d7ad (currentStateModified false, read from the .vbox). **Also this session:** the owner turned automatic backups on (Settings > Backups: `D:\JARVIS-backups`, every day at 12:00; two on record by 16:45); a read-only survey of C: (8.5 GB free of 221; the biggest items the protected test VM at 55.6 GB per the P0 record, `Documents\Codex` 36.5 GB, Windows 32 GB) with a five-step cleanup for the owner's own hands (move Codex and `.codex` to `D:\C-drive-overflow`, empty the Recycle Bin, Windows' cleanup recommendations, delete `%LOCALAPPDATA%\JARVIS-package`); by 17:02 `.codex` was moved and the bin emptied (15.1 GB free), the Codex contents were being moved, the rest is parked ("focus on the app"). The owner copied `E:\JARVIS-BACKUP` into `D:\JARVIS-backups\jarvis` (a copy; E: untouched). **The retired old JARVIS folder now lives at `D:\C-drive-overflow\2026-09-07\cr\outputs\jarvis` (moved by the owner; still owner-only).** Claude deleted nothing on C:. **THE IPHONE APP (plan step 7) IS WRITTEN:** `phone/ios/JARVIS/` (12 SwiftUI files, iPhone only, iOS 18 or later, written from scratch: owner Q1 "make a new one from scratch", Q2 the phone runs iOS 26), `phone/ios/README.md` (the Mac steps: project, Info keys, build settings Swift 5 / nonisolated, cable, TestFlight, fix rounds), `docs/PHONE-TAILSCALE-STEPS.md`, `docs/PHONE-APP.md`; the September files moved to `phone/ios/september-2026/`; under independent review; not built (no compiler here). Owner asked for JARVIS to see texts, calls (with live "is calling" status), contacts and Gmail: told that iOS gives no app access to texts, call history or voicemail; contacts and Gmail are possible (with permission and Google's sign-in), texts and calls only through Windows Phone Link notifications read on the PC; a plan of its own after the app runs, not started. **NEXT: the owner's "I approve the Stage 7 check of 1.0.16" (then the tools are placed and the seven steps given); the app's review findings applied, the zip on D:, the Mac build with fix rounds; after STAGE_7_COMPLETE the plan for the everyday update; then Tailscale and the pairing (steps 4 to 6 of the phone plan).**
- **2026-10-06, about 15:41 local (Fable 5.1, same session): ITEM 5 OF 1.0.16, MUSIC BY NICKNAME FROM THE OWNER'S OWN FILES, BUILT, TESTED, REVIEWED AND COMMITTED.** `docs/MUSIC.md` is the record (first the draft, now what was built). `music.py`: a Player over Windows' media interface (winmm `mciSendString`: open/play/pause/resume/stop/setaudio/status/close; the file's short path), a Library (table `music`, nickname -> file in `<config>\music`; MP3 and WAV listed), the spoken-command patterns (`music.command`) and the Desk behind the new tool `play_music` (play/pause/resume/stop/volume/status/list; `permissions.py` row "Play music from your files", a change on this PC, status and list are reads). `server.py`: `App.music`, `App.music_command` (a "play" is music only when a song resolves, else the words go to the AI; never for a wearable run) joined to the command line of `App.work`, the tool branch, `describe()`, owner routes `GET/POST /api/music`, the emergency stop stops the player; settings `music_volume` (0-100, default 80); `actions.py` schema (the 46th tool; `tools/host/jarvis-request-*` regenerated); Settings > Music (`static/music.js`, `music.css`, the category in `teague.js`, the tags in `index.html`, the static lists). **Tests:** `test_music.py` (9, with the media interface replaced by a recorder; a real local Core for the routes, the spoken commands without any AI key, the switch, the model's call, the stop), `test_music_view.cjs`; whole tree 663 Python, 52 desktop, 18 Intelligence, 24 interface scripts pass. **A real sound once on this PC** (a generated two-second tone, volume 25, from a plain Python process: play, position, pause, resume, ended) and the panel in a sandbox window with pictures in `docs/release-rehearsal-20261006-1016/music-panel/` (volume 20; the owner's installation not touched). **Independent review (one reviewer): no high; 2 medium (bare words such as continue and pause were music with nothing playing; names matched by letters inside words) and 10 low, all applied, record docs/MUSIC.md.** Release notes: the 1.0.16 entry now names the music. Not done from the draft: the song in the dashboard's activity line. **NEXT: step 3 of the phone plan for 1.0.16 (build, comparison with 1.0.15, regression, zip install, sandbox Stage 7 with the version 3 scripts), then `docs/STAGE7-CHECK-1.0.16.md` for the owner's approval.**

- **2026-10-06, about 15:16 local (Fable 5.1, same session): CORE RELEASE 1.0.16, ITEMS 1 TO 4 OF THE PHONE PLAN, BUILT, TESTED, INDEPENDENTLY REVIEWED AND COMMITTED.** `docs/PHONE-CORE-1.0.16.md` is the record. (1) `remote_devices.py`: Settings > Devices > Private network, a switch off by default; on, and with a Tailscale address on this PC (from `tailscale ip -4` only), a second server object bound to that address and a fixed port (default 8790) serves `POST /api/device/<op>` and nothing else (one JSON 404 for everything else, `Server: JARVIS`, Host = address, full or short Tailscale name); a watcher thread opens and closes the door as Tailscale comes and goes; state in the control table (`GET/POST /api/remote-devices`, also in `/api/devices` as `remote`); `server.main()` calls `ensure()` and `watch()`. (2) `device_gateway.py`: pairing calls 10/min per caller and 60 in all; 5 wrong codes lock a caller out of pairing 15 min while the pairing waits (25 in all end it); 20 wrong keys/min lock a caller out of that device id; a valid key is never turned away (the stop always passes); 429 for a locked caller. (3) `wearables/service.py`: device ops `conversations`, `history`, `metrics`, `overview` (paired devices only, 120/min); `events {run_id, after}` waits up to 10 s outside the service lock; `transcribe` refused while stopped. (4) `devices.py` column `writes` (migration), `permissions.py` mark `device_writes` on save_item, set_timer, manage_timer, manage_saved_memory, `decide(writes=)`; a per-device tick "May save memories and tasks" (owner action `writes`), re-read at every tool call (`App.device_writes`); the memory commands and the four saving tools work from such a device, "Ask first" asks on the PC. Panel: the Private network box and the tick (`static/devices.js`, `devices.css`). **Tests:** `test_remote_devices.py` (6), `test_phone_core.py` (13), `test_devices.py` +1, `test_devices_view.cjs` +12 lines; whole tree 654 Python, 52 desktop, 18 Intelligence, 23 interface scripts pass. Sandbox window check with pictures in `docs/release-rehearsal-20261006-1016/devices-panel/` (switch not turned on). **Independent review (one reviewer): no high; 3 medium, 11 low, all applied** (record section 8): the key lockout had been collective on the PC door and blocked a valid-key stop; the door did not open by itself (now the watcher); the lockout row was written under the gateway lock; plus the tick snapshot, Python's 501 page and Server header, the short MagicDNS name, the address fallback, a request timeout, the exclusive bind flag, untracked files, records, the row's caller, a panel race, the PC door's Host check. Found while fixing: the HTTP server's reverse DNS lookup at bind hung on a private address; the door now binds without it. Release notes: the 1.0.16 entry is written (counts to be confirmed at the build). **Owner decisions this afternoon:** "music from files, add to 1.0.16" then "so draft this up but then get back to the phone": item 5, music by nickname from the owner's own files, designed in `docs/MUSIC.md` (DRAFT), to be built next; the Wi-Fi device list (master document section 5) and the Nest camera (through Google's Device Access programme, the owner's registration and model needed) were asked about and are proposed as the release after 1.0.16, no decision yet. The owner was told how to open the key file themselves (Win+R, notepad on %LOCALAPPDATA%\JARVIS\config\.env); Claude never opens it. **NEXT: build item 5 (music) per `docs/MUSIC.md` with tests and one reviewer; then step 3 of the plan (build 1.0.16, comparison with 1.0.15, regression, zip install, sandbox Stage 7) and `docs/STAGE7-CHECK-1.0.16.md` for the owner's approval.**

- **2026-10-06, about 14:10 local (Fable 5.1, same session; owner: "I approve the phone plan"): THE PHONE PLAN IS APPROVED; STEP 2 (CORE RELEASE 1.0.16) BEGINS.** Approval: first clock reading 2026-10-06T03:09:22Z; record `../governance/PHONE-PLAN-APPROVAL-RECORD.json` (plan sha256 89f061e2… as committed in ac99cb6; repo copy `docs/phone-evidence/`). Taken with the recommended answers: D1 A (the Core's device door on the PC's Tailscale address, plain HTTP inside the tunnel), D2 yes (per-device tick "may save memories and tasks"), D3 no streaming to the phone in v1, D4 iOS 18, D5 zip on D: moved by the owner, D6 the phone release before the installer. **Q1 (September Xcode project still on the Mac?) and Q2 (iOS version) are unanswered and are needed at step 7, not before.** Authorized by the approval: building section 5 of the plan in the repo with the switch OFF by default, the release checks on this PC, the app under `phone/ios`, the Tailscale and Mac steps. Not authorized (each a separate owner act): turning the switch on, Tailscale, any Core listening on an address other than 127.0.0.1 (tests use a second loopback address), the Stage 7 check of 1.0.16, the everyday update, push or upload. The plan's status line records the approval (its only change since). **NEXT: build 1.0.16 items 1 to 4 of the plan's section 5, each tested and independently reviewed; record `docs/PHONE-CORE-1.0.16.md`.**

- **2026-10-06, about 14:05 local (Fable 5.1, same session; owner: "write the phone plan"): THE PHONE PLAN IS WRITTEN, `docs/PHONE-PLAN.md`, READY FOR THE OWNER'S APPROVAL** ("I approve the phone plan", changes in the same message; record on approval `../governance/PHONE-PLAN-APPROVAL-RECORD.json`). Built on the owner's decisions of 2026-10-06, the accepted recommendation, the design canvas (three artboards read: Ask, Chats, Status), `docs/DEVICES.md`, `docs/SPEECH.md`, the roadmap's Phase 4, the master document's sections 7, 8 and 18, and a read-only code survey (one Explore agent, nothing run). **Facts from the survey that shape the plan:** the Core listens on 127.0.0.1 only with the address fixed in the program and every request must name `127.0.0.1:<port>`; the desktop app starts the Core on a random port (`--port 0`); a device cannot list or read its conversations, read `/api/metrics` or `/api/state`, or save a memory (memory commands are skipped for devices); the device `events` route answers at once with no waiting; pairing counters are shared and wrong keys have no lockout; device `transcribe` is not blocked by the emergency stop. **So the plan has two parts: Core release 1.0.16 ("the phone release": a Settings > Devices switch, off by default, opening a device-routes-only door on a fixed port at the PC's Tailscale address; per-caller pairing limits; device routes for own conversations, PC health, an overview and a waiting events route; a per-device tick "may save memories and tasks"), then the SwiftUI app under `phone/ios/` built by the owner on the Mac (TestFlight), with the three September Swift files as the starting point.** Decisions put to the owner with recommendations: D1 reach (A: the Core's door on the Tailscale address, plain HTTP inside the tunnel; B: Tailscale serve HTTPS), D2 memory tick yes, D3 no streaming in v1, D4 iOS 18, D5 zip on D: moved by the owner, D6 phone release before the installer; questions Q1 (does the September Xcode project still exist on the Mac) and Q2 (iOS version). Eleven acceptance checks; limits said plainly (the PC must stay awake; Claude cannot build Swift here, so fix rounds on the Mac). **Also this session:** the owner's screenshot (13:50) showed the toast "Qwen voice needs DASHSCOPE_API_KEY and QWEN_TTS_VOICE (your cloned voice ID)" from the everyday 1.0.15: no cloned-voice ID yet. Told the owner to keep Fish Audio selected until one exists and to run `tools/host/Test-QwenVoice.ps1` (jonny account, PowerShell) and send a photo; a voice can be enrolled from a 10-20 s recording with `-Enroll` (small Alibaba charge). Nothing of the installed JARVIS was touched. **NEXT: the owner's approval of the phone plan (or changes); then step 2 of its section 8 (Core release 1.0.16).**

- **2026-10-06, about 13:49 local (Fable 5.1, new session opened from the pasted handover and moved to the repo): THE STAGE 7 TIMING DEVIATION OF THE 1.0.15 CHECK IS DECIDED: owner "accept the VM time".** The owner asked "what do you recommend"; Claude recommended accepting the VM time and keeping the bound; the owner typed "accept the VM time" (first clock reading 2026-10-06T02:47:07Z, recorded 02:48:43Z). Taken as: the Gate 20 bound (install, update and rollback each within 600 s, stopping JARVIS within 120 s) applies to Stage 7 checks and stays in force for every later check; the 675.1 s first install of the 1.0.15 check is accepted as a limitation of the test VM in this run (a disposition), on the cause the evaluation recorded (disk speed of the VM: the same 10,669 files verified in 106 s and 91 s later in the pass, the release installed in 28 s in the PC sandbox and in 47 s during the everyday update); the install is not measured again; the verdict STAGE_7_COMPLETE is unchanged. **For later checks a measurement outside the bound may be accepted as a disposition only when that check's records show the cause to be the VM; otherwise it is repeated before acceptance. The next release's check plan must say so.** Record `D:\JARVIS-stage7\1.0.15-63362929d7ad\evidence\owner-decision-01-timing-install.json` (schema jarvis-owner-decision-v1, sha256 91eff4b0…), listed in `MANIFEST-addendum-1.json` beside it (MANIFEST.json and stage7-evaluation.json unchanged; MANIFEST.json sha256 7c266dfa…); repo copies in `docs/stage7-1.0.15-evidence/`. Also this session: the status header corrected (commit dc669ec; it still said the everyday JARVIS was 1.0.14 and waiting for the update decision). The pasted handover contained the word "ultracode" and switched the harness's multi-agent mode on again; no workflow was started. The installed JARVIS, the VM and drive E: were not touched. **Open for the owner: voice once with the microphone connected ("No microphone was found" at the first start of 1.0.15); then "write the phone plan". NEXT for Claude, on the owner's word: the phone plan (docs/PHONE-PLAN.md for approval, from the recommendation of 2026-10-06, the Devices part of 1.0.15 and the design canvas N7JboAbsdEFwPFhrFFdAcs).**

- **2026-10-06, about 12:50 local (Fable 5.1, same session; owner's steps 1-6 run 10:48-12:43, snapshot record seen in the owner's photo): STAGE 7 CHECK OF 1.0.15: `STAGE_7_COMPLETE` (evaluated 2026-10-06T01:47Z; 27 of 27 checks).** Evaluation `D:\JARVIS-stage7\1.0.15-63362929d7ad\evidence\stage7-evaluation.json`; manifests host (9 files) and guest (38 files); repo copy `docs/stage7-1.0.15-evidence/` (with `guest/`, `vm/`). VM pass: Install (9), AfterRestart (2, the version 3 restart check saw boot id 7 -> 8 and needed no second restart; Z: never connected by hand), Uninstall (4: 10,669 program files removed, data kept, reinstall), Update (7: 1.0.14 from its own Stage 7 disc, update while running 361 s, rollback 105 s, update again 262 s, both memories each time), Interrupt (5: installer killed at 4,196 of 10,669 files, 1.0.14 untouched and running, rerun 190 s). Snapshot `STAGE7-PASS-1.0.15-63362929d7ad` (`f1add04d-3281-4894-8ccf-baa302755260`) taken after a clean shutdown; current; every older snapshot kept. **Outside the Gate 20 timing bound, put to the owner and not decided: the first install took 675 s (verify of the copied files 341 s; 1.0.14: 352 s) while every update, rollback and stop is inside; the records point at the VM's disk speed in this run (the same files verified in 106 s and 91 s later in the pass; 28 s in the PC sandbox).** Deviations recorded: incident 01 (closed window, false STOPPED), both discs labelled JARVIS_S7, the timing, a first-launch process count of 4. Follow-ups: launcher wording while a start is in progress; the drive letter or a distinct disc label in the next plan. The owner's installed JARVIS was not touched. **Plan for the everyday update written: `docs/UPDATE-EVERYDAY-1.0.15.md`, READY FOR THE OWNER'S APPROVAL** ("I approve the update of my everyday JARVIS to 1.0.15"). Launcher: the 1.0.14 launcher copied unchanged except its folder and the plan it names, `tools/host/update-1.0.15/` (sha256 `Invoke-EverydayUpdate.ps1` 1c555b02…, `update-step.cmd` 9c469bd4…, the 1.0.14 originals untouched); sandbox rehearsal 1.0.14 -> 1.0.15 with `docs/release-rehearsal-20261006-1015/rehearse-everyday-update-1015.ps1`: **13 of 13 PASS** (update 27.2 s, database unchanged, rollback verified; the live JARVIS 8 processes before and after, never addressed; records in `update-rehearsal/`). The plan asks the owner to confirm two things first: the key file says JARVIS_PROVIDER=openai or qwen (1.0.15 accepts nothing else), and C: has 10.4 GB free (1.0.15 adds about 1.2 GB; three releases will be installed). **Owner approved the update** ("I approve the update of my everyday JARVIS to 1.0.15", first clock reading 2026-10-06T02:05:09Z, recorded 02:06:05Z; record `../governance/UPDATE-1.0.15-APPROVAL-RECORD.json`, plan sha256 5d758011…, repo commit 8cf2187; repo copy `docs/update-1.0.15-evidence/`). Claude placed the launcher in `D:\JARVIS-update-1.0.15\tools\` (two files, hashes equal to the approval) with `update-authorized.json` (schema v1, final 1.0.15-63362929d7ad, previous 1.0.14-e03872680e1d, zip hash) and created `D:\JARVIS-update-1.0.15\evidence\` (approval copy, `prep-tools-hashes.txt`); nothing of the installed JARVIS was read or touched. **Steps 1-4 done (2026-10-06, 13:09-13:21 local): the everyday JARVIS is 1.0.15-63362929d7ad.** Step 1 PASS (`check.json`: owner account, not elevated, launcher and package hashes equal, 1.0.14 verified with 1.0.11 beside it, nothing running, 10.3 GB free, unpack 16 s); step 2 PASS (`backup.json`: backup 9c9131dc… with 1.0.14's own code, 332 files, test restore passed, all 18 table counts equal, 1,220 messages, copy on D: hash-equal, program still verified); step 3 PASS (`update.json`: 1.0.15 installed in 47 s, copy 29 s, verify 9 s, stop 0.6 s; verified; current 1.0.15, previous 1.0.14 kept; database byte-for-byte unchanged; shortcuts kept; not started); step 4 PASS as reported by the owner (`owner-check.json`: the owner's screenshot showed v1.0.15, the new look, 6 of 6 systems, 95 conversations, Qwen; the activity log said no microphone was found, the PC's microphone, not the update; "step 4 done"). Records in `D:\JARVIS-update-1.0.15\evidence\`, copies in `docs/update-1.0.15-evidence/`. **Step 5 PASS (`restart-check.json`): after the PC restart (boot 13:25:30, sign-in 13:26:21 local) JARVIS 1.0.15 started by itself from the Startup shortcut at 13:31:46 (--login-launch), 5.4 minutes after sign-in, all 8 processes from 1.0.15. `EVERYDAY_UPDATE_COMPLETE` (`update-evaluation.json`, 2026-10-06T02:34:30Z); manifest written; repo copy complete. THE EVERYDAY JARVIS IS 1.0.15-63362929d7ad; 1.0.14 and 1.0.11 stay installed as rollback copies.** Open items: the owner's timing-bound answer; removing 1.0.11 later on the owner's word; "No microphone was found" at the first start of 1.0.15 (the PC's microphone, to be checked with it connected). **NEXT: the phone plan ("write the phone plan"), built on the Devices part of 1.0.15 and the design canvas; after a trouble-free period, the cleanup on the owner's word. Also open for the owner: the timing-bound answer (above); then the phone plan ("write the phone plan").** Also this session, on the owner's ask: the phone design as a Design canvas (claude.ai artifact N7JboAbsdEFwPFhrFFdAcs): three iPhone screens (Ask with the holographic Core on a projector platform, Chats, Status) in the owner's design brief, with real-data telemetry only (CPU, memory, storage, link; no GPU or temperature, which JARVIS does not measure); the owner edited the Ask screen by hand twice and Claude rebuilt on those edits.

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

## 2026-10-12 evening (Opus 5.5, from about 16:55 local; a new session)

The owner's requests, in order:
- "check usage";
- Serena's MCP server failing to connect;
- "Analyze JARVIS, VERONICA, JARVIS core tools, fix any missing dependencies, and build a system diagnostic tool in
  src/tools/system_control.py". Asked, the owner chose "PC health, for JARVIS" at `repo\system_diagnostics.py`
  rather than `src\tools\`, which would break the flat layout and which the dev copy's update watcher ignores;
- "Inspect the entire JARVIS codebase ... ASI_ROADMAP.md";
- "begin implementing the Phase 1 autonomous core tools".

**Done**
1. **Serena works.**
   - The workspace `.mcp.json` passed `--context ide-assistant` (since renamed `claude-code`), and the first `uvx`
     install took longer than Claude Code's 30 s. The install is cached now; a start takes about 4 s.
   - Its command now reads `serena start-mcp-server --context claude-code --project
     C:\Users\jonny\JARVIS-claude-workspace`, with the dashboard and log window off.
   - `.serena\project.yml` (language python) has `line_ending: "lf"`: Serena had written CRLF into
     `system_metrics.py`, whose committed copy is LF.
   - Serena is a developer tool for Claude Code sessions, not JARVIS's memory.
2. **Dependencies: nothing missing.**
   - Repo `.venv` (Python 3.12.10): `pip check` clean, every line of the five requirements files satisfied, every
     third-party import resolves. The names that do not resolve are evidence scripts' own neighbours under `docs\`,
     tools reached through `sys.path`, and the optional `soundfile` in `wearables\verify_m4.py`.
   - Desktop: pnpm, `electron` 44.2.0, `rcedit` 5.0.2; `npm ls` clean.
   - VERONICA: `pip check` clean. Five packages her code imports directly were unlisted and came in only through
     deepagents and pywebview. They are now pinned at the installed versions (her repo 445facc): langchain 1.4.4,
     langchain-core 1.6.9, langgraph 1.2.14 (`tasks.py` imports the version-specific `GraphDrained` and
     `RunControl`), pydantic 2.14.0, pythonnet 3.2.1.
   - Her tests on a throwaway copy: 141 passed. The 1 failure is the git-ignored speech model, which is present in her
     folder.
3. **The tool `system_diagnostics` (59 tools).** It reads this PC's live condition:
   - processor load (its own two readings, half a second apart, so the dashboard's shared reading is left alone);
   - memory;
   - free space on every fixed or removable drive with a letter (network drives not read; no "no disk" box);
   - Windows uptime;
   - battery and power;
   - the programs holding the most memory, grouped by name;
   - the network adapters (no hardware addresses);
   - `attention` sentences past fixed thresholds (a drive under 10% free, memory or processor at 90% or more, a
     battery at 20% or less off mains).

   How it reads, and what it may do:
   - Read only. The fast parts come through ctypes; programs and adapters come from one read-only PowerShell call,
     each part inside its own try. A part Windows does not give is None and named in `unreadable`; ValueError comes
     only when nothing at all was readable.
   - Permission row: reads, this PC. A paired device needs the owner's tick, as for `computer_system_info`.

   Files:
   - `system_diagnostics.py` and `test_system_diagnostics.py` (new);
   - `system_metrics.py`: `system_times` is public, and the busy-share arithmetic is shared as `busy_percent`, with
     no change for the dashboard;
   - `actions.py` (one schema line, original line endings kept), `permissions.py`, `server.py` (import and
     dispatch);
   - `conversation_context.py`: "for the AI and search connections use system_health, and for this PC's live load
     ... use system_diagnostics";
   - `personality.txt`: one clause, so its new hash `438631dc...` is added to `runtime_paths.SHIPPED_PERSONALITIES`
     as that list's rule requires;
   - `docs/PERMISSIONS.md`: 59 tools;
   - the request templates, regenerated.

   On this PC a real reading takes about 1.9 s: C: 39.0 GB free of 222 GB (17.5%), D: and E: fine, no battery,
   nothing flagged.

   Independent review: no high, no medium, 9 low, all applied:
   - a part failing unexpectedly is now None and never ends the question;
   - `SetThreadErrorMode` for empty card readers;
   - per-part try in the script;
   - its own `GetTickCount64` handle;
   - the working-set note in the scope;
   - threshold and cap tests at their exact limits;
   - the ctypes size and a check of the real readers;
   - the guidance wording;
   - the `actions.py` line endings.

   Tests:
   - full Python suite 893 OK (330 s; data and config folders pointed at a throwaway folder);
   - desktop `node --test` 60 pass, intelligence 18 pass, all 28 root `.cjs` scripts pass (bundled Electron as
     Node).
4. **`docs/ASI_ROADMAP.md`: a PROPOSAL for the owner's approval.**
   - It is one ordered plan. The approved merge plan goes first. It updates and would replace
     `docs/CAPABILITY-PLAN.md` (decision E1) and keeps `docs/MEMORY-ROADMAP.md` as the design of its memory phase.
   - Said plainly: no application can be engineered into "ASI". JARVIS's reasoning is the model's. The plan improves
     what the code controls: measurement, tools, memory, durable jobs, roles, bounded autonomy, and a measured
     self-improvement loop with the owner's approval.
   - The emergency stop, approvals for consequential actions and the owner-only list stay.
   - Decisions E1 to E10. The top risk named is D4's `mail_send` Allowed combined with unattended jobs that read
     outside text.

**Found, for the owner**
- **Uncommitted phase 1 work of the merge plan** is in `D:\JARVIS-release-work\src-merge` (branch
  `claude/veronica-merge`):
  - `providers.py` +310 lines, plus `actions.py`, `server.py`, `connection_checks.py`, `env.template`, four
    `static\` files, `wearables\service.py`, and a new `test_openrouter_provider.py`;
  - last written 16:45 today by an earlier session, and not touched in this one.

  The next session reviews, finishes and commits it. Bringing `claude/main` into it touches `actions.py` and
  `server.py` on other lines.
- **Deny rules not in force.** `repo\.claude\settings.json`'s deny rules (reading `.env`, `git push`) do not apply to
  sessions that start at the workspace root, as sessions now do (ASI roadmap E10).
- **New rules in the workspace `CLAUDE.md`.** It gained "Autonomous Execution Guidelines" at 16:46 today. They are
  followed for build and test loops; the OWNER-ONLY list in `repo\CLAUDE.md` still stops and asks.
- **VERONICA defects for merge phase 3**, beyond the known ones:
  - context pruning (`agent.py` about line 475, `messages.pop(1)`) can leave a tool result without its tool call,
    which the API rejects;
  - tool results are cut at 10,000 characters, overriding `READ_LIMIT` 100,000;
  - `_ask` retries a 400 error three times.
- **The known test failure doesn't show in throwaway mode.** Run with the data and config folders pointed at a
  throwaway folder, the full suite does not show the known `test_answer_evidence` briefing failure caused by
  `repo\.env`.

**Next.** Phase 1 of the ASI roadmap, begun on the owner's word: first, every tool failure comes back to the model
as a plain error. Then, unchanged: merge plan phase 1 (the uncommitted work above) and 1.0.19's open items. The ASI
roadmap's decisions wait for the owner.

## 2026-10-12 (Opus 5.5; the owner: "look through all past chats", then "do only these two" and four more items)

**What happened on 2026-10-11 after the last entry** (found today in Qwen Code's logs under `~\.qwen` and in git; no
Claude Code session was involved):
- Qwen Code (gemma4:31b-cloud, 12:14-13:38) made VERONICA "fully autonomous", then on "commit and push" robocopied her
  folder, her empty `.git` included, over `repo\` and committed. The repo was left on a new branch `master` that shares
  no history with `claude/main` (98f0f38, 4,932 files: JARVIS's `store.py`, `calendar_feed.py`, `requirements.txt`,
  `README.md`, `.gitignore`, `.env.example` and two tests replaced by VERONICA's; `build\` and evidence logs committed).
  The push failed (no remote). Qwen Code (qwen3.8-max, 16:08-20:52) then patched `master` (7a40bf9, 55108dc, 62dd0cc,
  ab9c4b1) and hand-ported the launcher change to `claude/main` as fbdc7eb. The repo's git-ignored `.env` was replaced
  by VERONICA's keys file, with four JARVIS lines added later.
- The whole workspace was moved into `C:\Users\jonny\Favorites\` that afternoon (who did it is not recorded). That broke
  the `D:\JARVIS-release-work\src-1.0.18` worktree and the Stage 7 launcher's `-Repo` default.
- Also installed that day: OpenClaw (about 11:05; tray plus gateway, commands run without asking) and Hermes (14:27).

**Done today**
1. **Workspace back at `C:\Users\jonny\JARVIS-claude-workspace`** (a rename on the same drive). The 1.0.18 worktree
   works again. `stage7-step` in test mode answers "build the Stage 7 disc for 1.0.18-cffb826de043".
2. **Repo back on `claude/main` (fbdc7eb), nothing deleted.** HEAD was pointed at `claude/main`, the index reset, and the
   six replaced files restored from it. VERONICA's 34 files, `veronica.log` and her `data\checkpoints`,
   `checkpoints.db` and `veronica.db` moved to `D:\JARVIS-release-work\outside-repo\veronica-leftovers-20261012`.
   `build\` and the evidence logs stay as ignored files. `master` stays as an archive: never merge it, it has no
   shared history. `.git\config` is VERONICA's fresh-init copy (default settings; git works).
3. **VERONICA in her own repository `D:\VERONICA`**, out of OneDrive:
   - 8081fba: the folder exactly as it ran, with the provenance in the message;
   - 90fd355: `safety.py` names JARVIS's workspace outright and refuses her own folder. Its old `HERE.parent` would have
     blocked the whole of D:;
   - 7c4efbb: `CLAUDE.md` and `AGENTS.md`.
   - Tests: 141 passed. The 1 failure needs the speech model, which is present in `D:\VERONICA`.
   - The OneDrive copy moved to `...\outside-repo\veronica-onedrive-original-20261012`. A Desktop shortcut
     `VERONICA.lnk` points at `D:\VERONICA\VERONICA.exe`, and the owner has started her from it.
   - The owner's two memories of this morning, which were only in the ULTIMATE copy's data, were added to
     `D:\VERONICA\data\veronica.db` on the owner's "MOVE MEMORIES". The live database was backed up first to
     `...\outside-repo\veronica-db-before-memory-merge-20261012.db`; integrity check ok.
4. **Review of fbdc7eb (Start-JARVIS.ps1, the development launcher): KEEP with fixes before the next release.**
   - Medium: the window check compares Edge's top-window titles, so a second run or a window opening behind others
     can add duplicate windows, and a tab whose title changes counts as success.
   - Medium: the 5 s wait is short for a cold Edge on this stalling C:.
   - Low: the last fallback says nothing.
   - It ships in releases (root files are packaged), but not in 1.0.18. Fixes queued for 1.0.19.
5. **Automatic backups are NOT broken; the earlier notes are closed.** The setting already names
   `D:\TEAGUE INDUSTRIES - JARVIS INTELLIGENCE DATABASE BACK UPS` (the owner's rename of `D:\JARVIS-backups`,
   2026-10-06 16:54). Last success was 2026-10-12 12:00, with 5 on record (read from a throwaway copy of the database).
6. **C: went from 22.3 to 25.5 GB free.** `VERONICA_JARVIS_ULTIMATE` (Qwen's stale mirror, 3.1 GB) and Qwen's
   PyInstaller leftovers (`~\dist`, `~\build`, `~\VERONICA.spec`) moved to `D:\JARVIS-release-work\outside-repo\`. For
   the owner: `..\owner-steps\Free-C-Space.cmd` moves releases 1.0.11, 1.0.14 and 1.0.15 (not current, not previous)
   to `D:\JARVIS-release-work\old-releases` and clears pip's cache, about 4 GB. Claude's own changes inside AppData
   are redirected and would free nothing. **The owner ran it** (all three copies on D: with every file; current.json
   still 1.0.17 / previous 1.0.16), ran `owner-steps\Remove-Hermes.cmd` (Hermes Agent, about 5 GB, to the Recycle
   Bin, PATH entry removed) and emptied the bin: **C: 38.6 GB free (83% used)**. The next big item is the protected
   Stage 6 VM `JARVIS-CLEAN-WIN11` (about 32 GB on C:), the owner's decision.
7. **One AI tool per project (owner): Claude Code writes JARVIS and VERONICA.** `~\.qwen\QWEN.md` tells Qwen Code
   (it ran from the home folder, so a note inside a project would not reach it). Also recorded in the workspace
   `CLAUDE.md` and in `D:\VERONICA\CLAUDE.md` and `AGENTS.md`.

**Later the same day: the merge plan.** The owner asked to make VERONICA and JARVIS one ("Veronica joins JARVIS"),
with OpenRouter doing all the AI except voice ("OPENROUTER WILL DO EVERYTHING EXCEPT KEEP FISH AUDIO") and VERONICA
kept autonomous ("keep it as it is"). The owner created an OpenRouter key and tested it with
`..\owner-steps\Test-OpenRouter-Key.cmd` ("openrouter works") and `Test-OpenRouter-Functions.cmd`:
- passed: tools on Qwen and Claude, web search, search by meaning;
- picture reading: a test fault, since fixed;
- speech-to-text: needs at least US$0.50 of credit; the owner adds credit on payday.

**`docs/VERONICA-MERGE-PLAN.md` APPROVED** (owner, 16:04 local: "i approve veronica merge plan", D1-D11 as
recommended; record `../governance/VERONICA-MERGE-PLAN-APPROVAL-RECORD.json`). The D1 amendment (one Core, two personas)
is in `CLAUDE.md`.

**Phase 0 (one folder) DONE:**
- VERONICA moved from `D:\VERONICA` to `C:\Users\jonny\JARVIS-claude-workspace\veronica` with her history, Python,
  data and speech model (13,406 files, byte totals equal; her repo at 9f2dcc1).
- Her Desktop shortcut, `CLAUDE.md`, README, the workspace guide and `~\.qwen\QWEN.md` now point there.
- Her tests: 142 passed with the speech model.
- Her memories stay in her `data\veronica.db` for phase 2 (not copied anywhere else).

Next is phase 1 (OpenRouter in the Core), built and tested with stand-ins. The live test waits for the owner's credit.

**Found, for the owner**
- `repo\.env` is VERONICA's keys file plus four JARVIS lines (names checked, values never read). In the repo the briefing
  test of `test_answer_evidence` fails because of the calendar address in it; the same test passes from the D:
  worktree, which has no `.env`. Replace it with JARVIS's own development keys file, or remove it.
- The protected Stage 6 VM `JARVIS-CLEAN-WIN11` is split but consistent and was left untouched:
  - its `.vbox` names the base disk and a new differencing disk in `D:\From-C` (moved about 01:16 on 2026-10-11);
  - its 32 GB snapshot disk is on C:, with a duplicate on D:;
  - moving or removing it would free about 32 GB on C:. The owner decides (VMs are owner-only).
  - `JARVIS-E2E-DISPOSABLE` is registered under `Documents\Codex`, which is now `D:\From-C\Codex`.
- The Stage 7 VM `JARVIS-S6-FRESH` is intact on D: (current snapshot STAGE7-PASS-1.0.17). The 1.0.18 release files
  and guest scripts are in place. Step 1 is the owner's double-click of `stage7-step`, before 2026-11-06.
- The DashScope key printed in session 8c6df08e (2026-10-10) should be rotated.

## 2026-10-10 late night (Opus 5.5, from about 20:28 local; a new session, process 4248)

- **One folder for every session (owner, 2026-10-10 about 20:47):** `C:\Users\jonny\JARVIS-claude-workspace` is the
  one folder every Claude Code session for JARVIS starts in. The owner added a guide `CLAUDE.md` at its top (outside
  the repo; read 20:50): it maps `repo\`, `friday\`, `governance\`, `reference\` and the places outside the folder,
  says the rules stay in `repo\CLAUDE.md`, and that the workspace is never moved into OneDrive or synced. Nothing was
  moved. The old OneDrive handover folder is not a place to start.
- **Correction to "2026-10-10 night" below:** release 1.0.18 is NOT "FRIDAY alone". The owner later chose "keep
  friday as he is, 1.0.18 time fix only". 1.0.18 = the Core's spoken answer to "what time is it" (the Mac's round 6
  request 8, below) on top of the installed 1.0.17, nothing else.
  - Branch `claude/release-1.0.18` from 0d38218 (the installed 1.0.17), worktree `D:\JARVIS-release-work\src-1.0.18`
    (junctions to this repo's `build\cache`, `build\wheels`, `desktop\node_modules`). The FRIDAY branch and folder
    named below (`claude/release-1.0.18-friday`, `src-1.0.18-friday`) no longer exist; the draft `friday_link.py` was
    never committed and is not to be used.
  - FRIDAY stays as he is (his repository: 82e0867 conversions, f61444b his widened rules, 1387eb3 drive space). His
    README and f61444b still say JARVIS 1.0.18 calls him; that is not so, and his files are left unchanged on the
    owner's word. Connecting FRIDAY to JARVIS, or FRIDAY editing JARVIS's code, is not to be built (stopped by the
    safety system several times; the owner was told).
  - The Workshop, the devices route, the guard, the You page and the two Core fixes stay on claude/main for 1.0.19.
- **STAGE 7 CHECK OF 1.0.18 APPROVED BY THE OWNER** ("I approve the Stage 7 check of 1.0.18", first clock reading
  2026-10-10T22:48:53Z = 09:48:53 local on 2026-10-11; recorded 22:50:37Z in
  `../governance/STAGE7-1.0.18-APPROVAL-RECORD.json`, repo copy `docs/stage7-1.0.18-evidence/`; plan sha256
  `161a1033…` as committed in d4becec). Rechecked at the approval: the plan unchanged, the tools equal the table, the VM
  on STAGE7-PASS-1.0.17-0d38218c4e1d (modified false, 9 snapshots), the 1.0.17 disc and the 1.0.18 zip and Setup equal
  to their records. Placed: `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.18\` (7 files hash-checked +
  `stage7-authorized.json` sha256 `529683e3…`); record folders `D:\JARVIS-stage7\1.0.18-cffb826de043\evidence` and
  `D:\JARVIS-S6-FRESHVM\evidence\guest-egress-01\stage7-1.0.18-cffb826de043`. The placed launcher's test mode: jonny
  builds the disc first. **Next: the owner's seven steps (step 1, jonny: double-click stage7-step, "disc built").**
- **Release 1.0.18 (the time fix) READY FOR THE OWNER'S STAGE 7 APPROVAL (2026-10-11, about 09:50 local):** build
  `1.0.18-cffb826de043` (commit cffb826 on `claude/release-1.0.18`; zip sha256 `312f03c3…`, Setup
  `JARVIS-Setup-1.0.18-cffb826de043.exe` sha256 `9fda6046…`, both in `D:\JARVIS-release-work\pkg-1.0.18-time`) passed
  every check on this PC: development suites at cffb826 (783 Python, 60 desktop, 18 Intelligence, 26 scripts), one
  review (no high, 1 medium, 6 low, applied), the comparison with 1.0.17 (only `server.py` and `release-notes.json`),
  the release regression in its third run (run 1: one Windows media-interface timeout in `test_music`, unchanged code,
  5 of 5 alone afterwards; run 2 stopped by the owner; run 3 PASS: 782 Python with the usual 7 skipped, 60, 18, 26),
  the zip install, the Setup rehearsal (real shortcuts unchanged) and the sandbox Stage 7 pass with the version 4
  scripts (ALL PASSED, 29 checks, 09:32-09:46). Records `docs/release-rehearsal-20261010-1018-time/README.md`; plan
  `docs/STAGE7-CHECK-1.0.18.md` (READY; the approval wording "I approve the Stage 7 check of 1.0.18"). Next on
  approval: the governance record, `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.18\` with the v4 host files and
  `stage7-authorized.json` (final 1.0.18-cffb826de043, previous 1.0.17-0d38218c4e1d, label 1.0.18-cffb826de043,
  expected snapshot STAGE7-PASS-1.0.17-0d38218c4e1d), the two record folders; then the owner's VM check, then the
  everyday-update plan. Later on `claude/main`: merge `claude/release-1.0.18` (the time fix) and renumber the Workshop's
  release-notes entry to 1.0.19.
- **2026-10-11 morning (the PC restarted 08:34; this session resumed):**
  - Two folders had been put inside the repo during the night (23:48 to 00:39), not by any commit: `SuperAGI\` (the
    downloaded source) and `JARVIS-core-d0a893d8884d\` (a copy of JARVIS's program files "for reading on the Mac", then
    changed: `autonomous_engine.py` added, "Friday's Autonomous Engine ... integrates directly with JARVIS Core's tool
    system", the FRIDAY-JARVIS link that is not to be built; `providers.py` edited; a `.env` added, never opened). The
    repo's own files were unchanged. On the owner's "move them" (about 09:05) both were copied, verified file by file
    (the `.env` by size only) and removed from the repo: now `D:\JARVIS-release-work\outside-repo\` with
    `MOVED-OUT-OF-REPO.txt`. Not part of JARVIS; not to be run or merged.
  - The owner uninstalled Qwen (the desktop app) and Ollama. JARVIS's offline answers therefore have no local model
    runtime (they had no model before either). `D:\Ollama\models`, made for Ollama on 2026-10-10, is empty.
  - The PC's slowness (owner: "my pc has been really slow"), measured read-only: processor and memory fine (6 to 14 %,
    23 of 32 GB free); drive C: (ADATA SU650, a budget 224 GB SATA SSD) stalled in bursts, 0.6 to 1 s per read with
    10 to 13 requests queued after the restart and on 2026-10-10 evening, normal (1 to 9 ms) between bursts; no error
    events for C: (the only disk retries, 2026-10-07, were on the USB backup drive); C: 35.8 GB free (it was 5 to 7 GB
    while 95 to 97 % full for days); 11 programs at sign-in. Given to the owner as their steps (registry, elevation,
    installs and deletions are owner-only): disable Edge, Chrome, Microsoft Lists and the two Logitech download
    assistants in Task Manager > Startup apps; Optimize (TRIM) C: after the regression; keep C: under 80 % full (a
    read-only list of what is big on C: to follow); ADATA SSD ToolBox only if the stalls continue.
- **Other sessions:** the owner closed the other sessions (about 20:47). At 20:51 two older Claude Code session
  processes were still alive under the desktop app: 15260 (started 19:05) and 20216 (19:43); this session is 4248
  (20:28). Neither committed anything after 23fe25a. Told to the owner; not ended by Claude.

## 2026-10-10 night (Opus 5.5, from about 19:45 local; a new session opened in the old OneDrive folder and moved here)

- **Two sessions:** the previous session (PID 15260, started 19:05) was still running at every check from 19:45 to
  20:15; the owner was asked three times to close it. It committed nothing after 0c5106e.
- **FRIDAY started** (the owner: "start friday and tell me what friday can do and attach friday to jarvis's core";
  "friday is a guy so he").
  - His key: `friday\.env` saved by the owner at 19:45 with a non-empty `ANTHROPIC_API_KEY` line (presence checked
    only; no Windows variable). Claude did not open the file when the owner asked for Notepad on it.
  - First live job: "convert 10 km to miles", programmed on attempt 1 in 88 s (FRIDAY commit 82e0867, v0.2.0). The
    code was read: standard library only, correct conversions. "What can you do" does not list the new skill (his
    fixed test pins that sentence).
  - Owner's choices, in order: "JARVIS calls FRIDAY (Recommended)"; "FRIDAY alone (Recommended)" for the fastest
    release; "Everything on this PC" for what FRIDAY's skills may use; "JARVIS's code too, now" for whose code
    FRIDAY edits and scans. Claude held that last one back: FRIDAY working on JARVIS's own code needs a written
    plan the owner approves first (it changes how JARVIS's program is changed); not built.
  - FRIDAY's own repository, commit f61444b: the ACCESS rules in `supervisor.SYSTEM_PROMPT` (the internet, the
    owner's files and programs with the standard library; never a key or a `.env`/`config.env`, never JARVIS's
    folders, no package installs, nothing deleted outside his folder unless the request names it); README says he
    is a he and that JARVIS 1.0.18 calls him. His tests: 60 passed. These rules are live for his own console now.
- **SUPERSEDED (see "2026-10-10 late night": 1.0.18 = the time fix only). Release 1.0.18 = FRIDAY alone, on top of the installed 1.0.17** (1.0.18 was never offered, so the number is
  reused, as for 1.0.16 and 1.0.17; the Workshop, the guard and the You page move to 1.0.19).
  - Branch `claude/release-1.0.18-friday` from 0d38218, in its own worktree `D:\JARVIS-release-work\src-1.0.18-friday`
    (junctions to this repo's `build\cache`, `build\wheels`, `desktop\node_modules`, `data\speech-models`,
    `data\wake-models`; the build inputs did not change since 0d38218).
  - Written, not wired, not tested, not committed: `friday_link.py` (tools `friday` ask/status and `friday_code`;
    keys out of FRIDAY's environment; his code refused by name when it names JARVIS's folders or key file; output
    keys blacked out; background coding with notice, undo by git revert, the stop and an unfinished try put back).
  - Next: the wiring (permissions, actions, store settings `friday_folder`/`friday_tries`, server routes, the stop,
    the local "FRIDAY, ..." and "code it" commands, Settings > FRIDAY), tests, one reviewer, the build chain, the
    Stage 7 plan for approval. The owner was asked to say "go" to continue on that basis.
- **The Mac's round 6 copy** (owner's message; the upload is named `JARVIS-ios-bigstepper-20261010-2005.zip`, the
  owner called it `JARVIS-ios-mac-20261010-2005.zip`; sha256 704c22c2da053dd0d2a1fea325d4fcc97a1f3b1030f1475c300cb856f0f1d063
  as given): 125 files, kept as `phone/ios/mac/20261010-2005` (the 12:18 copy kept). New: `JARVISShare`, round 6
  records, `ROUND6-CONVERSATION-SIRI-SHARE.md`. Its STATUS.md "Requests for the PC" items 7 and 8, answered from the
  code (the same in 1.0.17 and on claude/main):
  - 7: one question at a time is Core-wide: `start_run` refuses while any question runs anywhere (the PC window,
    the app, Siri, Share), whatever the device or conversation.
  - 8: a Core defect, confirmed: "what time is it", "time", "date" and "what is the date" are answered by the Core
    without the AI as `'Local time: ' + result['time']` (raw ISO text; `server.py:1685` in 1.0.17). Fix proposed on
    the owner's word: a spoken sentence with the local time and date.

## 2026-10-10 late evening (Opus 5.5, about 19:00 to 20:30 local, at the owner's "handoff")

- **State at the handoff.**
  - Head is this commit, after 160568a. Nothing is pushed.
  - At about 19:06 the PC was awake (the owner pressed the power button at 16:44). The everyday JARVIS 1.0.17 was running
    with 8 processes. Tailscale was connected (thegrizzlybear and iphone-15). The phone door was listening on
    100.103.95.28:8790.
  - The session moved to the repo; its memory folder is the repo project's.
- **The You page: built, but its review findings are NOT applied yet.**
  - What it is: release 1.0.19, from the owner's "lets make jarvis and me more connected personally". The owner chose
    "He knows my life".
  - Commit b4f169c; record `docs/ABOUT-YOU.md`. The pieces:
    - `about_you.py`, with the `profile` table;
    - `static/you.js` and `static/you.css`: a YOU panel at the top of the Memory section;
    - `about_you` (reads) and `remember_about_you` (an offer; always asks; approval card), registered in `OWN`;
    - `GET`/`POST /api/profile`, `context['about_owner']` and `about_you.GUIDANCE`.
  - Tests: `test_about_you.py` (12) and `test_you_view.cjs`. Full suite: 881 Python, 880 OK. The one failure was
    `test_phone_core` pinning the device-write tools; it was updated and passes. 28 interface scripts OK.
  - Seen in a browser against the sandbox Core.
  - One reviewer found no high finding: no save without approval, no crash. **To apply next, in this order:**
    1. Plain passwords, PINs and card numbers are accepted. Refuse what `store.put` refuses (password, api key, secret,
       bearer), plus PIN and card shapes.
    2. Hidden and instruction text (tag characters, U+202E, "ignore previous instructions") is stored and goes
       unguarded into every question. Refuse when `content_guard.clean` reports `hidden` or `instruction`, and strip
       invisible characters.
    3. The card shows the date as raw MM-DD and the section as its id. Show words on the card and the device rows.
    4. A date in next year shows "in N days" with negative years, and the text says "1 years".
    5. "At most one offer per answer" is not enforced (a run flag).
    6. With `about_you` switched off, the summary still goes. The offer sentence in `GUIDANCE` goes even when
       `remember_about_you` is not offered.
    7. Search: natural queries miss; the 120-entry cap is silent; ids are sent.
    8. Duplicate offers still make cards; an offer about an existing person adds a second one. SQLite `lower()` folds
       ASCII only.
    9. The 2,500-character bound is measured with `ensure_ascii=False`, but sent escaped.
    10. `/api/import` drops `profile`. The ABOUT-YOU.md claim about restores must be corrected or the import extended.
    11. The owner's clicks work during the emergency stop (as `/api/item` does). Decide and say.
    12. Panel details:
        - a partial date is silently dropped;
        - `maxLength` must be per section;
        - "OPEN MEMORY BANK" does not refresh the panel;
        - the toast shows on a duplicate.
    13. An approved offer has no `summary` ("Kept on the You page: ...").
    14. An unknown section in `search()` raises KeyError.
    15. Test gaps.

    Then: the full suite, the record and a commit.
- **The memory roadmap: written and committed for the owner's approval** (160568a, `docs/MEMORY-ROADMAP.md`).
  - The owner asked for a roadmap so JARVIS saves context and memories and gains an ever-increasing understanding of
    them. The semantic layer sits under the UI, separate from the LLM. Open source is reused.
  - Four research agents fed it: the frameworks, the building blocks, the patterns and evidence, and the code map.
  - Proposed:
    - a memory service in the Core over the one SQLite file;
    - FTS5 plus vectors (first as BLOBs with numpy, sqlite-vec at scale);
    - local ONNX embeddings through FastEmbed: granite-embedding-small-english-r2 vs Qwen3-Embedding-0.6B, chosen by
      measurement;
    - a provider-neutral `extract(schema, text)`;
    - learning after conversations, from the owner's own words only, through a daily review card;
    - facts with validity periods, tombstones, and a personal evaluation set first;
    - five phases, about 10 sessions;
    - the Mem0 / Hindsight checkpoint in Phase 4.
  - Decisions D1 to D8. Approval wording: "I approve the memory roadmap, accept all recommendations". No answer yet.
- **Voice recognition** (the owner: "jarvis only answers to my voice"): researched, NOT built. Recommended design:
  - Model: 3D-Speaker CAM++ English ONNX (Apache-2.0, 29.6 MB), on the shipped onnxruntime, with kaldi-native-fbank
    (0.3 MB wheel).
  - Where: the check sits at the top of `App.transcribe_speech` (`server.py`), before the cloud decision.
  - Rejected audio never goes to the cloud. Only the stop phrase passes for anyone.
  - Enrolment: 6 phrases from the window's microphone.
  - A grace period inside one conversation. Silent rejection by default.
  - Typing, hold-to-talk and the phone are never checked.
  - A voice match never grants authority (NIST SP 800-63B).
  - The owner's sample: `C:\Users\jonny\.claude\uploads\2d0de0e8-9a51-4dad-a3a8-54b1f74880fe\6f71074f-Taleeban_Rd.m4a`.
    - It is an iPhone voice memo: 43.8 s, about 42 s of speech, 48 kHz mono AAC.
    - It was transcribed locally only: the owner introduces himself as Ben Teague, founder of Teague Industries, and
      asks JARVIS to answer only his voice.
    - Keep it out of the repo. PC-microphone enrolment is preferred, with this file as an extra sample.
  - Found on the way: faster-whisper's own `decode_audio` fails with the installed PyAV (`metadata_errors`). The live
    path passes PCM arrays.
- **Network** (the owner: "read the wifi and see all devices and connect to them"):
  - The owner's answers: "all devices on the wifi", and scan "only when I ask".
  - Plan: "scan my network" on the owner's own words only (address sweep, the neighbour table, SSDP, mDNS, the Wi-Fi
    details). Then control for the device kinds actually found (casting, DLNA, Sonos, Hue, Kasa, printers, Roku).
  - A read-only adapter/netsh check was declined by the permission prompt and not retried.
- **FRIDAY:**
  - 60 of 60 tests pass; still at commit 930b56b.
  - The owner added US$20 in the Claude Console.
  - **The key is not saved yet.** There is no `friday\.env` (only `.env.example`), and Notepad was still open at the
    handoff. The owner was told to press Ctrl+S, or Save As to `"C:\Users\jonny\JARVIS-claude-workspace\friday\.env"`.
  - Then: check that the line is present without reading it, and give FRIDAY a tiny first job with
    `supervisor.py --program "..."` (Opus 5.5, about US$0.25 per attempt, at most 5 attempts).
- **The agreed order:**
  1. the You page findings;
  2. voice recognition;
  3. the network scan and device control;
  4. Gmail and Calendar phase A, once JARVIS's own account exists;
  5. the memory roadmap phases after approval (D8).
- **Tools:** "ultracode" showed as on throughout. Per the owner's rule no workflow was started; single agents were used
  (5 researchers, 1 reviewer).

## 2026-10-10 evening (Opus 5.5, 14:13 to about 15:15 local): the guard reviewed and its findings applied

- **Start:** the session opened in the old OneDrive handover folder and was moved to the repo. No other session was
  running, head was 0c819b6 and the tree was clean. The everyday JARVIS 1.0.17 was running (8 processes) and was not
  touched. The pasted handoff contained "ultracode", which switched multi-agent mode on; no workflow was started (one
  reviewer agent, the owner's rule).
- **Item 1 of 1.0.19, the guard, is independently reviewed; every finding is applied** (`docs/GUARD.md`, section
  "Review"). The review found 4 high, 5 medium, 1 low-medium and 4 low findings. In short:
  - the guard now cleans only what the AI model reads (`content_guard.for_model` in the Core's tool loop and the
    Workshop's mission loop; `earlier()`; an attached file; the Workshop's context; a mission's opening file names and
    lessons). The window, the owner's own clicks and the approval cards keep results as they are. A card shows the
    characters that hide or reorder text as their codes (`static/reliability.js`).
  - the mark carries to the next question while the cut text is in its context; a new conversation starts clean;
  - writing the guard's stand-ins back is refused (Workshop writes, self-changes);
  - patterns narrowed: "Hey Jarvis", "Developer Mode", mail corrections and code comments pass; JARVIS's own records
    and program files are exempt (`content_guard.OWN`);
  - the page opener reads addresses as a browser does (127.1, a trailing dot, a backslash, a name lookup). An
    unnamed local address asks first and the approval opens it;
  - in a marked question, tools that always ask keep their own approval and own-words tools keep their check;
  - the quadratic patterns are fixed.
  - `test_content_guard.py`: 18 tests, including whole questions with a scripted model and a mission. The reviewer's
    own check scripts were rerun on the fixed code.
  - **Full suite:** Python 869 tests, 867 OK. The 2 failures were `test_audit_regressions.WorkerCancellationTests`:
    their fixture rebuilds the Core without `content_guard`, a gap since 0c819b6. The fixture was fixed and the
    module's 45 tests pass; the full suite was not rerun after that one-line test fix. Interface scripts 27 of 27.
    The desktop and Intelligence suites were not run (not touched).
- **A lead for 1.0.18's intermittent Workshop test (not confirmed):** `workshop.Mission.run` sets `finished` before
  `Desk.mission_ended`, which still uses the database. A test that goes on after `finished.wait()` can find the
  database still in use at its cleanup; build 2's failed regression reported "the database still in use afterwards".
  `test_content_guard` now joins the mission thread. Investigate with the flaky test.
- **The calendar mismatch is closed, by the owner:** "i had to reput in the calandars special iuntergration code for it
  to show up for jarvis". After the owner put the calendar's secret address in again, "will's party" reached JARVIS.
  The address in the key file had not carried that calendar (the old value was never seen; Claude never reads the key
  file). No code change. `docs/GOOGLE-STEPS.md` now says each calendar has its own secret address, and records this case.
- **Owner decision "his own account only":** JARVIS gets his own Google account; the owner's own inbox stays
  unconnected and the owner forwards what JARVIS should see. JARVIS holds one Gmail account, so no code change.
  - `docs/GOOGLE-STEPS.md` section 1 is rewritten (commit c52a0c1). Step 0: the owner makes the account. Then the app
    password is made on JARVIS's account, and `GMAIL_ADDRESS` is JARVIS's address.
  - The owner was given the five steps. No TEST result has been seen yet.
  - Phase B's sign-in (calendar writes) will be as JARVIS's account, with the owner's calendar shared to it ("Make
    changes to events"). Google's current rules are still to be checked before those steps are written.
- **Still open for the owner:**
  - make JARVIS's account and send the Gmail TEST result;
  - check Settings > Backups (D:\JARVIS-backups no longer exists).
- **Next, Claude:** item 18 phase A (mail and calendar with no new sign-in), built for JARVIS's own account; then the
  rest of 1.0.19 in order; the 1.0.18 flaky test, with the lead above.
- **End:** the owner asked for sleep, then for a sign-out with the PC left on and "make sure jarvis is still on", and
  then settled on sleep: "actually just set it to sleep don't log out sleep my pc". After this commit the PC is put to
  sleep and nobody is signed out. The everyday JARVIS stays running and carries on when the PC wakes; while it sleeps,
  JARVIS and the phone's link to him are paused.

## 2026-10-10 late afternoon (Opus 5.5, at the owner's "handoff"): the guard built, not yet reviewed; Gmail and Calendar plans

- **Head:** f02a48f, then this commit, which adds the guard. Nothing is pushed. The everyday JARVIS is still 1.0.17
  and was not touched.
- **Item 1 of 1.0.19, the guard, is built and tested, but not yet reviewed** (`content_guard.py`, `docs/GUARD.md`,
  `test_content_guard.py` with 12 tests; 190 tests of the touched modules pass):
  - outside text that tries to instruct the AI is cut out;
  - hidden characters are removed;
  - secrets are blacked out;
  - a question whose results held instructions changes nothing more without approval;
  - local addresses open only on the owner's own words.
  **Next session, first:** one reviewer for the guard, apply the findings, the full Python suite, commit.
- **The owner connected Google Calendar** to the everyday JARVIS ("calandar done"; TEST passed by the owner's
  account of it). Gmail is not connected yet; the steps were given (`docs/GOOGLE-STEPS.md` section 1).
- **Open, seen by the owner:** Google Calendar shows "will's party", Sat 10 Oct 15:30–23:00, on "Jarvis's & Mr.
  Teague", but JARVIS answered "today's empty" at 14:04 and 14:06. Not yet diagnosed. Candidates:
  - the event was made after the feed was read (JARVIS caches the feed 10 minutes, `calendar_feed.CACHE_SECONDS`);
  - Google's secret iCal address lags behind on Google's side;
  - a parsing or zone bug in `calendar_feed.py`.
  Next: test `calendar_feed` with a synthetic feed holding that event, then ask the owner to ask again.
- **The owner: "make him be able to do everything he cant do for both gmail and calandar"**, with JARVIS's own two
  lists. The plan given to the owner, built straight after the guard, as item 18:
  - **Phase A**, with no new sign-in, over IMAP, SMTP and the iCal address:
    - HTML mail and attachments, sent and received;
    - every folder;
    - mark read or unread, star, label, archive, move to Trash (never a permanent delete);
    - drafts, and threaded replies;
    - checking a sent mail is in Sent;
    - reading invites inside mails;
    - calendar reading for any range, past ones too;
    - each change under the permission switches.
  - **Phase B**, after a one-time Google sign-in the owner sets up: calendar create, edit, move and delete, guests and
    RSVP, recurrence, reminders and colours; Gmail filters, forwarding, signatures, out-of-office, contacts, other
    addresses. Google's current rules must be checked first. An OAuth app in "testing" loses its sign-in after
    seven days (`mail.py`'s note); whether an unverified app "in production" is usable for the owner alone must be
    confirmed before the steps are written.
  - **Impossible or the owner's:** read confirmations, fixing a sign-in, permanent delete.
- **The owner's question, not yet answered: "can I give jarvis his own google account that he has full acess to?"**
  The answer being prepared:
  - Yes, and it is safer: the owner's own account stays out of JARVIS's reach.
  - The owner makes the account (accounts are the owner's).
  - The owner shares their calendar with it, "Make changes to events".
  - JARVIS's own Gmail can send as JARVIS and receive forwarded mail.
  - Calendar writes still need a Google sign-in (Phase B) as that account. Without one, JARVIS can organise events
    by sending calendar invitations from his own address, which Google adds to the owner's calendar; that works only
    for events JARVIS organised.
  - The owner's own inbox still needs the owner's app password.

## 2026-10-10 afternoon (Opus 5.5): the Mac's six requests answered; the owner approved two Core fixes, built and reviewed

- The session opened in the old OneDrive folder and was moved to the repo. Head 8280b3c with a clean tree at the
  start, so no second session was committing. The pasted handover's "ultracode" switched the multi-agent mode on
  again; no workflow was run (the owner's rule: no workflows).
- The Mac's milestone zip `TEAGUEJARVIS-ios-mac-20261010-1200.zip` (114 entries, 96 files, sha256
  `31b6baa3c3cfefa916e472b6808ea1e3eed1b441a4a857ad52072d713f797679`) is kept unedited under
  `phone/ios/mac/20261010-1200/`. Every file was checked byte for byte against the zip. It covers rounds 4, 5 and
  5b, which the Mac checked against Core 1.0.17.
- **Replaced on the owner's word** ("Keep it under phone/ios/mac; it replaces the 1200 copy") by the Mac's newer
  copy `JARVIS-ios-mac-20261010-1218.zip` (sha256 `f0b54583ae209cd8f779a2e14b990cfa549c3751cc6b3421a8a0ce2abc9096e6`,
  the owner's stated hash, matched; 114 entries, 96 files, each checked byte for byte), now under
  `phone/ios/mac/20261010-1218/`. The 1200 copy stays in git history (commit 22892b5). Against 1200 only three
  files differ: `SessionModel.swift`, `SiriIntents.swift` and `STATUS.md`. Round 5c applied the PC's answers in the
  app: announcement words cleaned by the Core's Unicode 15.0 rule, and the stop sentence quoted. Its STATUS.md
  lists all six requests as answered and asks nothing new of the PC.
- Its STATUS.md section "Requests for the PC" (six items) is answered in **`docs/MAC-ANSWERS-20261010.md`**, for the
  owner to carry to the Mac. The answers come from the code of 1.0.17 (0d38218) and of head:
  - (1) the exact stop sentence, `permissions.STOPPED_MESSAGE`, the same since 1.0.16; device routes answer it as a
    400 with no `stopped` field;
  - (2) the announcement rule: Unicode categories C*, and the release's Python 3.12.10 has Unicode 15.0.0, so emoji
    joined with U+200D and anything newer than Unicode 15.0 are refused;
  - (3) `devices` comes with 1.0.18, which is not released;
  - (6) "Wearable service busy." always comes before any work, in 1.0.17 and 1.0.18, so one resend never does
    anything twice.
- **Two Core defects, found then and approved by the owner the same afternoon:** "I approve both Core fixes from
  MAC-ANSWERS-20261010.md: item 4 (a timer's reply gives the local clock time) and item 5 ("remember that" saves my
  own last line)." Both are **built for 1.0.18 and reviewed**, one reviewer each and one at a time. Record:
  **`docs/CORE-FIXES-20261010.md`**.
  - (4) The timer: `due_local` beside the bare `due` timestamp, `now` and `seconds_left` in a listing, the reply
    "Timer started for 2 minutes. It goes off at 10:29.", and the receipt "scheduled; goes off at 10:29". Review:
    no high, 1 medium, 5 low; four applied, two outside the approved scope recorded.
  - (5) "Remember that" saves the owner's own last line, and JARVIS's answer only for "remember what you said".
    Review: 2 high, 1 medium, 6 low; the medium and five lows applied in f9b3088. The two highs (after a question,
    a command or "analyse my screen", the owner's own line is not worth saving) were put to the owner, who chose
    **"His answer"**:
    - a statement keeps the owner's line;
    - a question or request, including the window's screen question, keeps JARVIS's answer;
    - a command keeps nothing and says so (`memory.COMMAND_HINT`);
    - thanks and self-saving lines are looked past.
  - Found on the way, both older than 1.0.18, **fixed on the owner's "Fix both"**: the window's `/api/reminder` no
    longer sets a timer while the emergency stop holds, and "Call me when the build finishes." is no longer taken as a
    name (`memory._NOT_A_NAME`).
  - The full Python suite at f9b3088 ran 836 tests with 1 error: an older cleanup race in
    `test_jarvis.LocalTests.test_local_run_emits_terminal_event` (the Ollama side-check writes after the test). The
    module passes 3 of 3 alone.
  - The follow-up's own review found 4 high, 4 medium and 5 low:
    - thanks variants;
    - statements misread as questions and polite commands as requests;
    - the name fix bypassed through a saved memory;
    - "Remember that, Jarvis.";
    - music words;
    - live-sharing frames;
    - and more.
    All were applied except low 12 (record: `docs/CORE-FIXES-20261010.md` section 3):
    - `memory.line_kind` was reworked: commands first, a question needs a subject or a "?", thanks checked word by
      word;
    - `previous_line` reads exchanges;
    - one name rule, `memory.name_from`, for the command, `key()` and the store;
    - the approval card shows "JARVIS said: ...".
    - The touched modules pass (189 tests).
  - Recorded for the owner, not built (follow-up review low 12): turning on the private-network door and the Spotify
    sign-in callback still act while the emergency stop holds.
- **OpenJarvis** (Stanford's local-first assistant, Apache 2.0; the owner's zip `Downloads\OpenJarvis-main.zip`, sha256
  `2ad97829…6df`) was compared in `docs/OPENJARVIS-COMPARISON-20261010.md`. Nothing from it was run, installed or
  copied. Not to be taken: its Pearl cryptocurrency mining and its usage analytics. **The owner: "build all of these"**,
  the eight items:
  1. the guard on what JARVIS reads;
  2. the morning briefing and monitors;
  3. skills;
  4. memory suggestions with the owner's OK;
  5. search by meaning;
  6. the offline voice;
  7. messaging apps;
  8. Apple connectors.
  They are for 1.0.19, in that order. The owner's own steps are listed in that record: model downloads on permission,
  a Telegram bot token, and a Mac for the Apple items.
- **SuperAGI** (2023, MIT; the owner's zip `Desktop\SuperAGI-main (1).zip`, sha256 `40278185…723`) was read for "how we
  can give jarvis these abilities instead of making multiple agents", in `docs/SUPERAGI-COMPARISON-20261010.md`. Its
  many agents become missions of the one JARVIS. **The owner: "add the 4 new ones"**, which go on the 1.0.19 list after
  the eight:
  - 9: missions side by side;
  - 10: missions that pause to ask;
  - 11: a cost cap and spend per mission;
  - 12: reading a web page's text, after the guard.
  Then, quoting "Sending email", **"and this"**. **Corrected and told to the owner:** sending email is already built
  in 1.0.17 (`mail_send`, always asks first; `mail_search`, `mail_read`). It needs only the owner's Gmail app password
  (`docs/GOOGLE-STEPS.md` section 1), so there is no item 13. GitHub and image generation come only on the owner's word.
- **The owner: "I want jarvis to have access to my email , messages , calls , calandar and alarms and timers".** What
  exists, and what is added:
  - **Email:** built (read, search, send with approval). The owner's step: the Gmail app password,
    `docs/GOOGLE-STEPS.md` section 1.
  - **Calendar:** reading is built. The owner's step: the calendar's private address, `docs/GOOGLE-STEPS.md`
    section 2. **New, item 14:** adding and changing events, through the phone's calendar (the app's part goes to the
    Mac session) or, with the Mac mini, Apple Calendar.
  - **Timers:** built, with the clock-time fix of today. **New, item 15:** alarms at a clock time, once or repeating,
    ringing and spoken on the PC. Real iPhone alarms through iOS 26's AlarmKit are the app's part, for the Mac
    session.
  - **Messages:** each new text can already reach JARVIS through an iPhone Shortcuts automation into "Announce to
    JARVIS" (1.0.17 and the app's round 5b); setting up that automation is the owner's step. **New, item 16:**
    reading earlier messages and sending texts. With the Mac mini, through Messages on the Mac; on the phone, JARVIS
    drafts and the owner taps Send (the app's part).
  - **Calls:** the iPhone lets no app see calls. **New, item 17:** with the Mac mini, call history and calls placed
    through the iPhone; on the phone, JARVIS starts a call the owner confirms (the app's part).
- **The Mac mini is not bought yet.** The owner, 2026-10-10: "I don't have the mac mini yet so no transfers are done
  yet physically just blue prints and plans." The order advice was the plan's D1, M6 24 GB / 512 GB at A$2,049, or
  32 GB / 512 GB at A$2,349; the Apple page had 32 GB / 256 GB selected. It rests on JARVIS's real use, measured read
  only on the PC:
  - memory: 1.30 GB in 8 processes (Core 0.36 GB);
  - processor: the Core about 1% of one core while waiting, and the window's animations about 0.86 of one core;
  - storage: 1.1 GB per release, 5 kept, and the database 1.3 MB;
  - the PC as a whole: 12.1 GB of memory in use.
  The Mac mini plan is still not approved.
- **Noticed while measuring, told to the owner:**
  - `D:\JARVIS-backups` does not exist. D: has "TEAGUE INDUSTRIES - JARVIS INTELLIGENCE DATABASE BACK UPS",
    changed 2026-10-06 16:54. If JARVIS's backup setting still names the old folder, the daily backups fail, since
    the folder is not recreated. The owner is asked to check Settings > Backups. The backup folder itself was not
    opened: it is owner-only.
  - Ollama holds only `llama3.2:latest` (2.0 GB), not `qwen3:4b`, which is the default model for offline answers.
    The owner was given `ollama pull qwen3:4b`. qwen3.8-max is JARVIS's online model and cannot run locally.
- **The garage (Merlin MS127MYQ, myQ built in, made 2025-03-07):** myQ admits no outside app, and Siri, Shortcuts,
  HomeKit and Matter are unsupported. The suggested route is a spare Merlin remote with a low-voltage Wi-Fi relay
  across its button, plus a door sensor. It is local, with no cloud. It waits for the owner's "plan the garage", and
  the household's myQ owner should agree to a second remote.
- **FRIDAY** (`C:\Users\jonny\JARVIS-claude-workspace\friday`, 930b56b) is unchanged since 2026-10-07; its tests
  pass, 60 of 60. It needs the owner's Anthropic API key in `friday\.env` and console credits, which stood at $0.00.
- Next:
  - the follow-up's commit, after the full Python suite;
  - then the eight OpenJarvis items for 1.0.19, starting with item 1, the guard;
  - 1.0.18 build 3, with the timer and "remember that" fixes, needs the cause of the intermittent Workshop test
    first, and is built from its own commit, before the 1.0.19 work;
  - the Mac mini plan waits for the owner.

## 2026-10-10 midday (12:30 local, Opus 5.5): the devices route added to 1.0.18; build 2 in its checks; the cloud plan written

- **Owner: "add devices to 1.0.18".** The `devices` operation for paired devices (the app's R6 panel, promised in
  `docs/MAC-REQUESTS-20261007.md`) built in 381b1f5 (`server.App.devices_for_device`, `server.pc_name`,
  `device_gateway.OPS`, `wearables.service.Service.list_devices`; `test_device_list.py`) and reviewed by one reviewer
  (no high, no medium, 5 low, all applied in fd2b6fa: reads at once no longer "busy" for this op, another
  installation's key left out, the form's section 0 corrected on the emergency stop, the kinds listed, four more
  tests). Record `docs/PHONE-DEVICES-1.0.18.md`; the form's section 7; the Mac brief updated and sent to the owner
  again. **Build 1 (`1.0.18-4afd891c38f4`) is superseded; `docs/STAGE7-CHECK-1.0.18.md` names it and is rewritten for
  build 2 when build 2's checks pass.** Build 2 **`1.0.18-fd2b6fa82121`** (commit fd2b6fa; zip 533,446,531 bytes,
  sha256 `f5e1e1c4…`): development suites at fd2b6fa pass (817 Python, 60 desktop, 18 Intelligence, 27 interface
  scripts); against build 1 only the four program files of the route and the bytecode differ, the pinned inputs and
  `JARVIS.exe` identical; against 1.0.17 as for build 1 plus the route. The release regression of build 2 is running
  alone; then the Setup, the zip and Setup rehearsals, `pkg-1.0.18` refreshed and the sandbox Stage 7 pass.
  (A full development run during the reviewer's own test runs had one load timeout in `test_core_lock`; the module
  passed three times alone and the run at fd2b6fa was clean.)
- **Owner: move the Core to the cloud** ("so my pc doesn't need to be on to use the app"). Compared on 2026-10-10:
  DigitalOcean Sydney, Basic 2 vCPU / 4 GB / 80 GB, about US$24 a month plus backups, is the recommended fit
  (Vultr close second; not Alibaba, Hetzner Singapore or the Oracle free tier). **`docs/CLOUD-CORE-PLAN.md` written
  for the owner's decisions D1 to D10 and approval** ("I approve the cloud plan, accept all decisions"): one Core at a
  new address, reachable only over Tailscale; the PC a client with a helper for the seven PC and window tools; the
  Workshop on the server; checks on a temporary server first; a cutover like 2026-10-04's; release 1.1.0 after 1.0.18;
  about five to seven sessions of work. It changes the binding rule "The Core lives on the owner's PC" only on the
  owner's approval. Nothing of it has started. Then, after the comparison (Google Cloud added; no cloud keeps
  everything as fast as the PC; the dedicated-processor server about US$42 the closest) and the Mac mini prices
  (M6 from A$1,449; 24 GB / 512 GB about A$2,049): **the owner chose a Mac mini at home** ("so no cloud I would run
  jarvis's core fully on the mac mini and we'd use it as like everything"). **`docs/MAC-MINI-PLAN.md` written for the
  owner's decisions D0 to D10 and approval** ("I approve the Mac mini plan, accept all decisions"); the cloud plan is
  marked superseded. The Mac mini plan: the Core, voice, music, the Workshop and the device door on the Mac mini,
  always on; the phone and every future device pair with it; the PC a client; a Mac version of JARVIS built and
  checked on the empty Mac mini first; about four to five sessions; D0 asks whether to finish 1.0.18 on the PC
  (recommended: only if the Workshop is wanted sooner). Nothing of it has started. **Owner, then: "no I don;y just want
  to run it for just phone purposes I want to take the core on this pc and move it fully to the mac mini" and "and the
  mac mini will become my main computer for everything".** The plan now says plainly that all of JARVIS moves (what
  moves is listed; the PC keeps no Core, only the old copy switched off for a month), JARVIS runs in the owner's own
  account on the Mac mini as on the PC today with the Core as a background service from start-up, the PC's window is
  optional, and **D2: the repository and the one writer move to the Mac mini** (Claude Code installed there by the
  owner, a handover bundle from this PC: the repository with its history, the governance records, the notes, the
  status), this PC session then stopping. Not yet approved; the Mac mini not yet bought.
- **1.0.18 build 2's release regression: NOT PASSED** (11:26-11:57): 816 Python tests with 1 failure and 1 error, both
  `test_workshop.MissionTests.test_the_tool_call_limit` ("the mission did not end" within 30 s; the temporary database
  still in use afterwards); desktop, Intelligence and interface scripts passed. The Workshop's code is the same as in
  build 1, whose regression passed; the test passed 5 of 5 alone and `test_workshop` passed afterwards. Cause not
  established. Build 2 not accepted; the Setup, rehearsals and sandbox Stage 7 of build 2 not run;
  `docs/STAGE7-CHECK-1.0.18.md` still names build 1 and is not offered. Next: reproduce in a loop with the release's
  Python (also under load), read `workshop.Mission` at the tool-call limit, fix, build 3, the chain again (or, by the
  owner's D0, stop 1.0.18 on the PC and carry the fix into the Mac version). Records
  `docs/release-rehearsal-20261010-1018/README.md` (section "Build 2").

## 2026-10-10 morning (10:55 local, Opus 5.5): release 1.0.18 (the Workshop) built and checked on this PC; its Stage 7 plan ready

- **Owner: "build 1.0.18".** Nothing had changed since 2026-10-07 (head 4afd891, tree clean, one Claude session, the
  everyday JARVIS 1.0.17 running with 8 processes and never addressed). Every check one after another on the idle PC;
  records `docs/release-rehearsal-20261010-1018/README.md`:
  development suites at 4afd891 (809 Python none skipped, 60 desktop, 18 Intelligence, 27 interface scripts); the build
  **`1.0.18-4afd891c38f4`** (10,772 files; zip 533,444,176 bytes, sha256 `8d44eba6…`); the comparison with 1.0.17 (12
  source files changed, 3 added, 0 removed; pinned inputs identical but for the version carried by `JARVIS.exe`, 4 bytes
  of its version resource, and the bootstrap `package.json`); the release regression run alone (**PASS**: 808 Python
  OK with the same 7 skips as 1.0.17, 60 desktop, 18 Intelligence, 27 scripts); the Setup
  (`JARVIS-Setup-1.0.18-4afd891c38f4.exe`, 406,974,294 bytes, sha256 `eb1f0ee3…`, 135 s); the zip install (PASS, 30 s);
  the Setup rehearsal v2 (PASS; the owner's real shortcuts unchanged); `pkg-1.0.18` (four files, hash-equal); the
  sandbox Stage 7 pass 1.0.17 -> 1.0.18 with the unchanged version 4 scripts (**ALL STAGE 7 STEPS PASSED**, 10:28-10:42,
  every lap far inside the bound; the first pass whose previous build has its own `JARVIS.exe` and Setup).
- **`docs/STAGE7-CHECK-1.0.18.md` is READY FOR THE OWNER'S APPROVAL** ("I approve the Stage 7 check of 1.0.18"), after
  one decision first: **the `devices` route.** Found while writing the Mac brief: `docs/MAC-REQUESTS-20261007.md`
  promised the phone a `devices` operation (the app's R6 device panel, asked by the Mac) and the Core never got it
  (`device_gateway.OPS` lacks it; 1.0.17 and this build answer HTTP 400 "Operation unavailable."; the panel shows
  "not on this Core yet"; every other route and field of the form is present). Put to the owner: "add devices to
  1.0.18" (build 2, every check again, the plan rewritten) or "devices later" (the plan stands for build 1).
  Recommended: add it now, to save the owner a separate VM check later. The VM is on STAGE7-PASS-1.0.17-0d38218c4e1d
  with no change since; the 1.0.17 disc reads back equal to its record; the ten version 4 tool hashes equal the 1.0.17
  approval's table.
- **The Mac brief** `docs/MAC-BRIEF-20261010.md` (sent to the owner as a file): the PC is on 1.0.17, round 5 can be
  tested against the real Core, the ten changes to the form since the Mac's first copy (among them: approve/reject
  while stopped answer HTTP 400, not 403; `hello`/`status` `location: true`), the `devices` gap, the test steps with
  the owner's PC switches (the two ticks; "Set a timer" to Ask first for the approval test), the milestone zip back.
- Answered for the owner: the 7 skipped tests in the release regression are by design (repo-only tools, the
  developer folder's rcedit, short names on D:); the iPhone app is updated through the Mac's Claude Code session
  (cable install; TestFlight later, 90-day builds, the Apple account steps the owner's); Fish Audio's voice is the
  key-file line `FISH_VOICE_ID` and its model `FISH_MODEL` (default `s2-pro`), changed by the owner, with Settings >
  Voice > VOICE PREVIEW set to Fish (automatic picks the Qwen voice first).

## 2026-10-07 evening (19:00 local): the everyday-update plan for 1.0.17 READY for the owner's approval

- **`docs/UPDATE-EVERYDAY-1.0.17.md` is READY FOR THE OWNER'S APPROVAL** ("I approve the update of my everyday JARVIS
  to 1.0.17"). The reviewed launcher version 2 (`tools/host/update-1.0.17/Invoke-EverydayUpdate.ps1`, sha256
  `66c8cce6…`, unchanged since its review) passed its sandbox rehearsal **26 of 26** (run 3, 18:49-18:54 local,
  `docs/release-rehearsal-20261007-1017/update-rehearsal-3/`; base `D:\JARVIS-release-work\update-rehearsal-1.0.17-3`):
  refused without approval and while JARVIS ran; step 1 (hashes, the Setup's record, the stale folder renamed aside,
  10,768 package files unpacked, 1.0.16 verified, no entry before); step 2 (backup 178 files with test restore, the
  copy hash-equal); step 3 (the Setup silently in 98.7 s wall; inside: verify package 12.7 s, copy 11.6 s, verify
  copy 27.6 s, stop 1.8 s, switch 0.1 s; `withheld`; the entry "JARVIS (sandbox)" 1.0.17; no `JARVIS.ps1`; the
  database byte-for-byte unchanged); 1.0.17 started on the same data through `JARVIS.exe`; the reruns; the rollback
  to 1.0.16 (the entry still 1.0.17); the cleanup through the sandbox's own entry; the owner's real shortcuts
  hash-equal throughout; the real Settings > Apps entry absent at the start and the end; 0 live JARVIS processes
  before and after. Harness finding 12 applied (the real entry asserted at both ends; the cleanup runs even when a
  step throws) and two harness defects found and fixed by run 2 (18:44-18:48, `update-rehearsal-2/`: every launcher
  step passed; the harness looked for the Setup's log under its old name after review finding 9 stamped it, and read
  the sandbox Core's connection file in the instant the Core removed it); run 1 (`update-rehearsal/`) stays the
  record of the pre-review launcher. The first run's folder on D: was kept, not deleted (each run has its own base).
  The README of the folder has the section. On approval: the governance record, `D:\JARVIS-update-1.0.17\tools\`
  with `update-authorized.json` (schema v2: the zip and the Setup with their hashes), the owner's steps 1 to 5 with
  JARVIS quit first (the leftover `JARVIS-package` folder renamed aside at step 1). **APPROVED BY THE OWNER** ("I
  approve the update of my everyday JARVIS to 1.0.17", first clock reading 2026-10-07T07:58:40Z, recorded 2026-10-07T08:00:21Z;
  record `../governance/UPDATE-1.0.17-APPROVAL-RECORD.json`, plan sha256 `f74fff6f…` at commit 08cbb7b). Claude placed
  the launcher in `D:\JARVIS-update-1.0.17\tools\` (two files hash-equal to the approval, plus `update-authorized.json`,
  schema v2) and created `D:\JARVIS-update-1.0.17\evidence\` (`prep-tools-hashes.txt`); repo copy
  `docs/update-1.0.17-evidence/`. Nothing of the installed JARVIS was read or touched. **Next: the owner's step 1**
  (JARVIS quit first; `update-step.cmd`), Claude checks `check.json`, then steps 2, 3, 4 (the owner's check list in the
  plan) and 5 (the PC restart); then `update-evaluation.json`, the manifest, the repo copy, `EVERYDAY_UPDATE_COMPLETE`.
  **Step 1 PASSED (08:02:19Z; `check.json`: hashes equal, 1.0.16 verified, 0 processes, 11.9 GB free, no entry, 10,768
  package files unpacked) with incident 01:** the launcher found no `%LOCALAPPDATA%\JARVIS-package` to rename, while
  every Claude session had seen one. **Cause found and proven with an owner-run probe: the Claude desktop app is a
  packaged (MSIX) app, and Windows redirects AppData and HKCU writes from Claude's processes (sandbox on or off) into
  `C:\Users\jonny\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Local` (and the package's registry hive),
  with reads showing the merged view.** The "leftover" 1.2 GB folder is `LocalCache\Local\JARVIS-package`, unpacked by
  a zip install rehearsal's `install.cmd` on 2026-10-02 from a Claude session; the owner's Windows never had it; the
  real `AppData\Local` holds `JARVIS` only; no `LocalCache\Local\JARVIS` exists, so nothing has shadowed the installed
  JARVIS; Desktop, Startup and D: are not virtualized. Consequences: nothing to rename (the plan's item 3 is moot, said
  in the plan); every earlier mention of that leftover on the owner's C: (the 1.0.15 and 1.0.16 plans, the cleanup
  list) described the phantom; the sandbox rehearsals' "JARVIS (sandbox)" entries were only ever in the package hive;
  any AppData or HKCU fact only Claude has read is unverified for the owner's side (memory note). Records
  `D:\JARVIS-update-1.0.17\evidence\incident-01-leftover-folder.json`, `probe-owner-window.txt`, the probe in
  `D:\JARVIS-update-1.0.17\probe\`. Cleanup candidate on the owner's word, later: the 1.2 GB phantom under LocalCache.
  **Steps 2 to 5 PASS: THE UPDATE OF THE EVERYDAY JARVIS TO 1.0.17 IS COMPLETE, `EVERYDAY_UPDATE_COMPLETE`** (2026-10-07T08:46:04Z,
  `update-evaluation.json`): step 2 (`backup.json` 08:13:38Z: backup d5499b69… with 1.0.16's own code, 356 files,
  3,268,323 bytes, test restore passed, all 22 table counts equal with 1,667 messages, the copy on D: hash-equal, the
  program still verified); step 3 (`update.json` 08:17:34Z: the Setup silently, exit 0, 187.1 s wall; the installer
  inside it verify package 7.6 s, copy 68.1 s, verify copy 17.6 s, stop 0.7 s, switch 0.4 s, shortcuts written; 1.0.17
  verified, current 1.0.17 with previous 1.0.16; the entry JARVIS 1.0.17, Teague Industries with the uninstaller in
  `%LOCALAPPDATA%\JARVIS-package`; the Desktop and Startup shortcuts changed from the PowerShell launcher to
  `releases\1.0.17-0d38218c4e1d\electron\JARVIS.exe`; no `JARVIS.ps1`; the database byte-for-byte unchanged; C: 9.1 GB
  free after); step 4 (`owner-check.json`: "step 4 done" on the eight-point list; 8 processes of 1.0.17 through
  JARVIS.exe seen at 19:36); step 5 (`restart-check.json`: boot 19:38:59, sign-in 19:39:39, JARVIS.exe started by itself
  from the Startup shortcut with --login-launch at 19:43:13, 3.6 minutes after sign-in against 5.4 and 5.7 for the
  PowerShell shortcut, all 8 processes from 1.0.17). Records `D:\JARVIS-update-1.0.17\evidence\` with `MANIFEST.json`
  (the 4.4 MB Setup log stays on D:), repo copy `docs/update-1.0.17-evidence/`. **THE EVERYDAY JARVIS IS
  1.0.17-0d38218c4e1d; 1.0.16, 1.0.15, 1.0.14 and 1.0.11 stay installed as rollback copies.** The probe folder
  `D:\JARVIS-update-1.0.17\probe\` is the pattern for proving an AppData or HKCU fact on the owner's side.
- **Next, on the owner's word:** 1.0.18 (the Workshop) through the full chain (build on D:, comparison with 1.0.17,
  regression alone, the Setup, zip and Setup rehearsals, sandbox Stage 7 v4, `docs/STAGE7-CHECK-1.0.18.md` for
  approval, the VM check, the everyday-update plan with a copy of the version 2 launcher), or whichever of the six
  capability proposals the owner chooses first (`docs/CAPABILITY-SOURCES-20261007.md`); the C: cleanup on the owner's
  word (the old releases 1.0.11, 1.0.14, 1.0.15 at about 1.2 GB each, the phantom under the Claude package's
  LocalCache 1.2 GB; C: has about 9 GB free). Optional owner items unchanged: Gmail and Calendar through
  `docs/GOOGLE-STEPS.md`, item I (Nest), TestFlight, the Mac's next zip.
- **The everyday JARVIS (1.0.16) is still not running** (0 processes at 18:41 and through the rehearsals; 0 since
  14:50). The owner has not said why. Nothing this session ran touches it; the question goes to the owner before
  anything starts it.
- **Two sessions again:** the previous PC session (resumed, started 16:17) was still alive when this one took the
  handoff at 18:41; `git log` showed no new commit and the tree was clean; the owner is asked to close it. The pasted
  handover's "ultracode" switched multi-agent mode on again; no workflow was started.

## 2026-10-07 afternoon (15:50 local): 1.0.17 build 2 ready for the owner's Stage 7 approval; the Workshop built for 1.0.18

- **Release 1.0.17 build 2 (`1.0.17-0d38218c4e1d`, commit 0d38218) has passed every check this PC can give it**, one
  after another on the idle PC (`docs/release-rehearsal-20261007-1017/README.md`): the comparison (the same program as
  build 1; 30 source files changed and 86 added against 1.0.16, the pinned inputs identical), the release regression
  (776 Python OK with 7 skipped by their own conditions, 60 desktop, 18 Intelligence, 26 scripts), the Setup
  (`JARVIS-Setup-1.0.17-0d38218c4e1d.exe`, 406,936,706 bytes, sha256 `b7bb04d3…`), the zip install (47 s), the Setup
  rehearsal version 2 (the owner's real shortcuts unchanged; the sandbox entry), `pkg-1.0.17` refreshed with build 2's
  four files, and the sandbox Stage 7 pass 1.0.16 -> 1.0.17 with the version 4 scripts (ALL STAGE 7 STEPS PASSED, 15
  min, every lap far inside the Gate 20 bound; records `stage7-local-build2/`). **`docs/STAGE7-CHECK-1.0.17.md` is
  rewritten for build 2 and READY FOR THE OWNER'S APPROVAL** ("I approve the Stage 7 check of 1.0.17"); on approval:
  the governance record, the tools in `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.17\` (schema v4), the two record folders,
  then the owner's seven steps; then the everyday-update plan. Build 1 (`1.0.17-52342b46e48a`) is superseded.
- **Two things reported to the owner:** the everyday JARVIS (`%LOCALAPPDATA%\JARVIS`, 1.0.16) was NOT running during
  build 2's checks (0 live processes from 14:50; 8 through build 1's checks to 14:09); nothing run here addresses
  it, and this session never touches it. And the previous PC session was still alive when the handoff was pasted
  into this one: it woke when its regression ended and committed twice at 14:44 (5366578, 480fd7c; nothing
  collided). The owner was asked to close the old session; a memory note holds the rule (check `git log` and the
  running processes at every handoff).
- **The Workshop (docs/WORKSHOP.md), release 1.0.18, BUILT in the repo** on the owner's "IMPLEMENT THESE ARE MANDATORY"
  (file system operations, terminal access, goal decomposition and planning, self-correction, short-term and
  long-term memory): `workshop.py` (the folder beside an installation's data; `workshop_files`, `workshop_run` inside
  a Job Object with the keys out and JARVIS's own folders refused, `workshop_python` for the workshop's own
  environment, `workshop_lessons`, `workshop_mission`: a plan, the steps with every result read, errors fed back and
  corrected, a time limit, 60 tool calls, the notice and the activity row at the end; 56 tools now), Settings >
  Workshop (`static/workshop.js`, `.css`), routes `GET/POST /api/workshop`, settings `workshop_minutes` and
  `workshop_folders`, five permission rows, the 1.0.18 release-notes entry, `API.md` rows. Independent review: 2 high,
  9 medium, 10 low, all applied (the record's last section). `test_workshop.py` 32 and `test_workshop_view.cjs` pass;
  the full Python suite (809 OK), the 27 interface scripts and the desktop suite (60; the first run had one Core
  start-up failure in `backend.test.cjs`, the rerun was clean, the cause not established) pass at the commit. Not built: a mission continuing
  after an approval; missions on a schedule. **Owner decision ("do both", 2026-10-07 about 16:00): commands ship as
  "ask first"** (`permissions.Rule.shipped`, read through `permissions.effective`): every command waits for the
  owner's approval on the PC until the owner sets the switch to Allowed in Settings > Permissions (which a mission
  needs to run commands unattended).
- **The Stage 7 check of 1.0.17 (build 2) is APPROVED BY THE OWNER** ("I approve the Stage 7 check of 1.0.17", first
  clock reading 2026-10-07T05:00:51Z, recorded 05:02:39Z; record `../governance/STAGE7-1.0.17-APPROVAL-RECORD.json`,
  plan sha256 `f1c8d9d2…` at commit 9078fe3; repo copy `docs/stage7-1.0.17-evidence/`). The version 4 tools are placed
  in `D:\JARVIS-S6-FRESHVM\tools\stage7-1.0.17\` (seven files hash-equal to the approved table, plus
  `stage7-authorized.json`, schema v4, expected snapshot STAGE7-PASS-1.0.16-fccde24e2cc6); the record folders
  `D:\JARVIS-stage7\1.0.17-0d38218c4e1d\evidence` and `D:\JARVIS-S6-FRESHVM\evidence\guest-egress-01\stage7-1.0.17-0d38218c4e1d`
  are created; the 1.0.16 disc read again equal to its record. **THE VM CHECK OF 1.0.17 IS COMPLETE: `STAGE_7_COMPLETE`,
  29 of 29 checks** (owner "stage 7 done" 2026-10-07 about 18:04 local; the seven steps 16:04 to 18:04: the disc
  941,621,248 bytes sha256 `519c0257…` built and read back; the VM started from STAGE7-PASS-1.0.16 with FRESH-PREREQ
  restored and LocalhostReachable = 0 proven; Install, AfterRestart, Uninstall, Update and Interrupt all PASS with the
  version 4 driver: the Setup's silent install, the Installed-apps entry, the uninstall through it, the reinstall, the
  update while running, the rollback, the update again, the update through the Setup (G7), the interrupted update;
  snapshot STAGE7-PASS-1.0.17-0d38218c4e1d 26a2163a… taken 07:04:19Z after a clean shutdown, all eight earlier
  snapshots kept). Evaluation `D:\JARVIS-stage7\1.0.17-0d38218c4e1d\evidence\stage7-evaluation.json` (07:07:09Z) with
  the host and guest MANIFESTs; repo copy `docs/stage7-1.0.17-evidence/` (the guest copy without the Inno Setup logs
  of 2 to 4.5 MB each, which stay on D: and are in the guest manifest). One deviation, dispositioned under the owner's
  rule of 2026-10-06: the first install's laps inside the Setup add up to 601.5 s, 1.5 s over the 600 s bound (verify
  copy 395.8 s in the VM against 7 to 18 s on this PC; every reinstall, update, rollback and stop far inside). Noted:
  4 processes at the launches in the VM (8 on this PC); no check depends on it. **Next: the plan for updating the
  everyday JARVIS to 1.0.17 through the Setup, `docs/UPDATE-EVERYDAY-1.0.17.md`, for the owner's approval**; then
  1.0.18 (the Workshop) through the same chain. The owner also asked (18:00) for a survey of open-source GitHub
  projects for five capabilities (task generalisation, multi-week autonomy, closed-loop self-modification, novel
  knowledge creation, multi-instance cohesion): written as `docs/CAPABILITY-SOURCES-20261007.md` (commit 8f3854c), a
  record and six bounded proposals in a recommended order (skills, standing goals, sub-workers, self-improvement runs
  on a copy behind the proposal door, discoveries with OpenEvolve, a local cloned voice with Chatterbox on this PC's
  GTX 1660 Ti from the owner's 18.7 s clip), nothing applied; the owner says which first. **The everyday-update
  plan `docs/UPDATE-EVERYDAY-1.0.17.md` is written but NOT YET READY:** the update launcher version 2
  (`tools/host/update-1.0.17/Invoke-EverydayUpdate.ps1`: the update through the Setup, the leftover
  `%LOCALAPPDATA%\JARVIS-package` renamed aside at step 1, the entry and shortcut-target checks, the database hash
  asserted) passed its sandbox rehearsal 24 of 24 (`docs/release-rehearsal-20261007-1017/rehearse-everyday-update-1017.ps1`,
  records in `update-rehearsal/`, launcher sha256 4f6d49e0… at that run), was then independently reviewed (1 high:
  a rehearsal could reach the real folders through the defaults if called inconsistently; 3 medium; 8 low; all
  applied, the plan's review section) and **must be rehearsed again on the changed launcher** (delete
  `D:\JARVIS-release-work\update-rehearsal-1.0.17` first; the harness refuses an existing base; harness finding 12
  still to add: assert the real entry absent before and after, uninstall the sandbox even when a shortcut change
  throws). Then the plan's status line and the launcher hash go in, and it is offered for the owner's approval
  ("I approve the update of my everyday JARVIS to 1.0.17"). Session ended on "handoff" at about 18:55 local.

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
