# JARVIS: current status (living document)

**Read this first in every new Claude Code session, and update it at the end of each one.**
Last updated: 2026-10-05 (about 20:40 local) (STAGE_6_COMPLETE, SWITCH-OVER COMPLETE, STAGE_7_COMPLETE;
**the everyday JARVIS is 1.0.14-e03872680e1d: Stage 7 check of 1.0.14 complete, update EVERYDAY_UPDATE_COMPLETE,
automatic start at sign-in confirmed on this PC**).

- **Night of 2026-10-05, same session: the owner's speed run, and "implement everything that we havn't done into 1.0.15".**
  **Speed run (owner, `Test-AiSpeed.ps1`, real providers, one sample each):** the key file says `JARVIS is set to use: qwen`, so the everyday JARVIS is on Qwen. A 150-word answer: `gpt-6-astra` 7.2 s; `qwen3.8-max` as JARVIS asks it today 11.9 s (297 of 485 output tokens were thinking); `qwen3.8-max` with thinking off 5.8 s; `qwen3.8-flash` with thinking off 5.8 s. A tool question: 2.3 / 3.1 / 3.4 (that line was cold: thinking off is counted as a different request, 8,531 against 8,567 tokens) / 2.0 s. So the wait is mostly Qwen's default thinking; flash is cheaper, not faster.
  **Built on that (repo only, in review when this was written):** Settings > AI > "Answer speed (Qwen)": Auto (default: thinking off, on when the user's own words ask, e.g. "think hard about ..."), Deep (thinking before every answer; sends exactly the request 1.0.14 sent), Economy (`qwen3.8-flash`; pictures stay on the vision model; "think hard" still gets the main model). `providers.qwen_plan`, setting `answer_mode`, `test_answer_mode.py`; 383 Python, 52 desktop, 20 interface scripts pass; the setting was saved, reloaded and reset in the sandbox Core. The defaults are Claude's recommendation from the numbers (decision D3 of the capability plan); the owner may change them. `Test-AiSpeed.ps1` now warms every line and adds a picture question (with and without thinking), which is what will prove on the real account that "thinking off" also works with pictures: **the owner has not run that version yet.**
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
