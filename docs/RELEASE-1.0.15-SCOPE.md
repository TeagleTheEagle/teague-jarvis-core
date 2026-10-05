# Release 1.0.15: what goes in (after the owner's instruction of 2026-10-05)

Owner, 2026-10-05, with the master architecture document (the PDF has the same text as
`docs/owner/JARVIS-MASTER-ARCHITECTURE.md`): **"implement everything that we havn't done into 1.0.15."**

This file is the working list for that instruction. It was written from the document itself and from two code
surveys of the same day (`docs/CAPABILITY-SURVEY-20261005.md`, `docs/DEVICE-SURVEY-20261005.md`). It is a status and
scope record, not an approval record: every item still reaches the everyday JARVIS only as a checked release that the
owner approves. The document's own standard applies to how it is built: "use the greatest useful depth and coverage
possible, but never increase scope past the point where clarity, precision or execution quality begins to drop". So
each item is finished, tested and independently reviewed before the next one starts.

**The owner can say "build 1.0.15 now" at any point:** whatever is finished and checked goes into the build, and the
rest moves to the next release. Until then 1.0.15 keeps growing down this list.

## A. Built for 1.0.15 on this PC (software only, can be tested here)

In this order. "Section" is the master document's section.

| # | What | Section | Today | State |
|---|---|---|---|---|
| 1 | **The right Qwen model for each job, and speed.** Settings > Answer speed: Deep (thinks before every answer, as today), Auto (quick answers, thinks first when asked), Economy (`qwen3.8-flash`). | 3 | One model for everything; Qwen thought before every answer (11.9 and 16.9 s against 5.8 and 6.2 s without, measured twice on the owner's account) | Built and reviewed 2026-10-05. **Open: the default.** It is Deep (nothing changes) until the owner says "auto default". |
| 2 | **OpenAI and Qwen as each other's backup.** When the chosen provider refuses or cannot be reached, the other one answers that question and the reply says so. Never after a tool has already run in that question, so nothing is done twice. A tick box in Settings > AI. | 3 | No fallback: on 2026-10-05 a billing block left JARVIS unable to answer | Built and reviewed 2026-10-05. **On by default on the owner's word ("backup on", 2026-10-05)**; the tick box switches it off. Only for a refusal or an unreachable provider, never for a missing key or model. |
| 3 | **Permissions in one place.** A table for every tool: reads only or changes something, can it be undone, does it ask first; enforced where every tool call passes. JARVIS's changes to its own personality and style ask first and never touch the installed program files. An emergency stop that holds (everything paused until the owner resumes) and is shown on screen. Audit rows name the run and the device. | 6, 18 | Policy is spread over five hard-coded lists; two files change with no approval; the stop is momentary | Built and tested 2026-10-05 (`docs/PERMISSIONS.md`; also Settings > Permissions with a switch for each tool: Allowed, Ask first, Off). Independent review: no high finding; its 2 medium and 14 low findings are applied (section 9 of that file says where; 2026-10-05, night) and that work was reviewed again by one reviewer (no high finding; 2 medium and 7 low, applied: section 10). To know: saying "Hey JARVIS" while JARVIS is thinking now interrupts that answer and listens, so that a spoken "emergency stop" is heard then. **Decision D1 settled by the owner on 2026-10-05: "ask first"** (earlier records authorised style and personality changes without a prompt; built and now decided is "ask first" for both). |
| 4 | **Devices the right way round.** A registry that survives a restart; a device has a name, a type and its own key; pairing by a code the owner reads from the PC; capabilities declared per device and allowed per device; revoke at any time; a Devices panel. A client can no longer declare itself "real". "Meta glasses" becomes Halo. | 5, 19 | In memory only; one shared token; no pairing, no revoke, no panel | Built, tested and reviewed 2026-10-06 (`docs/DEVICES.md`). Pairing with a code read from the PC, a key per device (bound to this installation), what a device declares against what the owner allows, revoke and remove, Settings > Devices, device names in the stop banner and the activity log, the test client always listed as simulated, "Halo" wording. Independent review: no high finding; 5 medium and 7 low, all applied. **It opens no port:** today only a program on this PC can pair; a phone or the glasses need the owner's networking decision (section B). |
| 5 | **Speech through Qwen as well.** Qwen speech recognition as the cloud choice behind one speech-to-text setting (local Whisper stays the default); an owner-run tool to enrol the cloned voice on the current Alibaba account and to check it. | 4 | Cloud transcription works with OpenAI only; no enrolment tool | Built, tested and reviewed 2026-10-06 (`docs/SPEECH.md`). Settings > AI > Speech recognition: on this PC (default) or by the chosen AI provider (Qwen `qwen3-asr-flash` or OpenAI); if the cloud cannot or takes more than 8 seconds, this PC does it. `tools/host/Test-QwenVoice.ps1` lists the cloned voices, makes a spoken test and, with `-Enroll`, creates a voice. Independent review: 2 high, 3 medium, 5 low, all applied. **Not tried against Alibaba from here: the owner's first run is the real test.** |
| 6 | **Automatic backups.** On a schedule, to a folder the owner chooses (for example the backup drive), each one verified, old ones thinned out. Off until the owner picks the folder. | 11 | Backups only by hand and on the same disk as the data; drive E: holds none | Built, tested and reviewed 2026-10-06 (`docs/AUTOMATIC-BACKUPS.md`). Settings > Backups > Automatic backups: a folder the owner types (off until then), every day or every week at a time of day; each backup made and checked like one made by hand; the newest seven and then one a week and one a month are kept, a backup made by hand is never touched; a question that arrives during a backup waits for it. One independent review: no high finding, 4 medium, 7 low, all applied. **The owner's step, once 1.0.15 is the everyday JARVIS: type a folder on the backup drive and press TURN ON.** |
| 7 | **Answers without the internet**, when a local model runtime (Ollama) is installed: a plain "offline" answer path with its limits said on screen. Installing Ollama is the owner's step. | 16 | A local model only labels commands for a log | Built, tested and reviewed 2026-10-06 (`docs/OFFLINE-ANSWERS.md`). When no AI provider can be reached (never for a refusal such as a bill or a key), the small local model on this PC answers and the reply says so; its words meet the same claim checks as a provider's; Stop ends it. **On by default, and it will be active on this PC, because Ollama with `qwen3:4b` is installed here** (Settings > AI > Offline answers switches it off). Asked of the real local model on this PC: an answer in about 8 seconds, no thinking shown, Stop effective after 2 seconds. One independent review: no high finding, 2 medium, 5 low, all applied. |
| 8 | **Replies that appear while they are written.** Needs the two checks that guard JARVIS's claims to work on a growing answer. The largest item; if it puts the rest at risk it is said so and moved, not rushed. | 3 | The reply appears only when complete | Built, tested and reviewed 2026-10-06 (`docs/REPLY-STREAM.md`). For Qwen, behind Settings > AI > "Show replies while they are written", **off by default**: the answer is received in pieces, and after each complete sentence the same claim checks as for a finished answer run on what is written so far; what they leave unchanged is shown as a draft, and the finished, checked answer replaces it. A claim without proof is never on screen. A broken stream is asked again in one piece; Stop works at once. Speech and other devices still get the finished reply only. One independent review: nothing serious, 5 lesser findings, all applied. **Not tried against the real Qwen service: the owner's first answer with the box ticked is the real test.** |

## B. Prepared on the Core side in 1.0.15, but not finishable without something from the owner

| What | Section | What it needs that Claude does not have |
|---|---|---|
| iPhone app | 8 | A Mac with Xcode, an Apple developer account and the iPhone; the Xcode project is not in the workspace (three Swift files are). Item A4 gives it the pairing and the phone-facing contract to connect to. |
| Reaching JARVIS away from the PC | 7 | The owner's networking decision (recorded 2026-10-01: the Core stays on this PC only until the owner decides) and a private network such as Tailscale installed and signed in by the owner. |
| Halo glasses | 9 | The glasses, and the iPhone app as their Bluetooth bridge. |
| Seeing devices on the Wi-Fi network | 5 | The owner's word, because it looks at the home network (it does not expose JARVIS). Read-only list, off by default; can be item A9 on a yes. |
| Tesla | 14 | The owner's Tesla account and developer access, and the car. Vehicle actions would be the strictest class in the item A3 table. |
| Mark I, ESP32, home systems | 5, 15 | The hardware or a Home Assistant installation. Item A4 is the contract they join through. |

## C. Already on the 1.0.15 list before this instruction

Done in the repo: the new look for the whole interface, the dashboard, formatted chat replies, the provider clean-up
(OpenAI and Qwen only), the screen label fix.

Still to do: which wins, a Windows variable or the key file (found 2026-10-05: Windows holds a `DASHSCOPE_API_KEY`
variable in the owner's account and JARVIS prefers it over the key file line. **The owner ran `Test-KeySources.ps1`
the same night: the two hold the SAME value, and 16 names are only in the key file. So JARVIS and the owner-run
checks use one Qwen key today and no decision is forced.** Left open, low priority: today a Windows variable would
silently win if the two ever differ; whether the key file should win instead is the owner's choice); plain messages
for HTTP 413 and `AccessDenied.Unpurchased` (**done 2026-10-05**: `providers.py`, two tests); a full-size connection
check in Settings (**done 2026-10-05**: Settings > Developer > Connections & action review > "Real-size question"
sends one question as JARVIS really sends it, without chats, saved facts or files; `App.full_question`); the
Alibaba "maintenance mode" check; three reviewer notes (**done 2026-10-05**: the fixed "CORE LINK NOMINAL" is gone,
the line shows the real state of the link; the Core answers "not found" for the missing `command-background.png`;
stale values when the connection is lost are covered by the strip "CORE NOT CONNECTED // WHAT YOU SEE MAY BE OUT OF
DATE" that every section shows); in Settings the SAVE button floats over the row beneath it (**done 2026-10-05**: the bar now has
a solid ground and sits at the bottom, and the rows under Settings > AI have their spacing; `static/horizon.css`,
checked in the sandbox at two window sizes); the new header checked in the desktop app itself; the version 3
Stage 7 guest driver (**done 2026-10-06**: `docs/STAGE7-DRIVER-V3.md`; the two incidents of the 1.0.14 check fixed,
21 decision cases pass on this PC, not yet run in the VM); the release notes. Added 2026-10-05: backups and the switch-over now carry the owner's own
style sheet (`owner-style.css`) beside the personality (`recovery.py`, `switch_over.py`, tests).

Then, as for every release: build, comparison with 1.0.14, regression, zip install, sandbox Stage 7, the VM check on
the owner's approval, and the update of the everyday JARVIS on the owner's approval.

## Not in the master document

The capability plan (`docs/CAPABILITY-PLAN.md`: measuring, memory, plans that last, bounded autonomy, self-improvement)
is a separate proposal waiting for the owner; only its decisions D1 and D2 overlap with item A3, where they are built
as the master document's section 6 asks (sensitive changes ask first). The installer (`JARVIS-Setup.exe`) stays
proposed as the release after 1.0.15 unless the owner wants 1.0.15 held for it.
