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
| 3 | **Permissions in one place.** A table for every tool: reads only or changes something, can it be undone, does it ask first; enforced where every tool call passes. JARVIS's changes to its own personality and style ask first and never touch the installed program files. An emergency stop that holds (everything paused until the owner resumes) and is shown on screen. Audit rows name the run and the device. | 6, 18 | Policy is spread over five hard-coded lists; two files change with no approval; the stop is momentary | |
| 4 | **Devices the right way round.** A registry that survives a restart; a device has a name, a type and its own key; pairing by a code the owner reads from the PC; capabilities declared per device and allowed per device; revoke at any time; a Devices panel. A client can no longer declare itself "real". "Meta glasses" becomes Halo. | 5, 19 | In memory only; one shared token; no pairing, no revoke, no panel | |
| 5 | **Speech through Qwen as well.** Qwen speech recognition as the cloud choice behind one speech-to-text setting (local Whisper stays the default); an owner-run tool to enrol the cloned voice on the current Alibaba account and to check it. | 4 | Cloud transcription works with OpenAI only; no enrolment tool | |
| 6 | **Automatic backups.** On a schedule, to a folder the owner chooses (for example the backup drive), each one verified, old ones thinned out. Off until the owner picks the folder. | 11 | Backups only by hand and on the same disk as the data; drive E: holds none | |
| 7 | **Answers without the internet**, when a local model runtime (Ollama) is installed: a plain "offline" answer path with its limits said on screen. Installing Ollama is the owner's step. | 16 | A local model only labels commands for a log | |
| 8 | **Replies that appear while they are written.** Needs the two checks that guard JARVIS's claims to work on a growing answer. The largest item; if it puts the rest at risk it is said so and moved, not rushed. | 3 | The reply appears only when complete | |

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

Still to do: plain messages for HTTP 413 and `AccessDenied.Unpurchased`; a full-size connection check in Settings; the
Alibaba "maintenance mode" check; three reviewer notes (`static/teague.js:37` fixed "CORE LINK NOMINAL";
`command-background.png` missing; stale values when the connection is lost); in Settings the SAVE button floats
over the row beneath it (seen 2026-10-05; three tick boxes drawn away from their labels were fixed the same day);
the new header checked in the desktop app itself; the version 3 Stage 7 guest driver; the release notes.

Then, as for every release: build, comparison with 1.0.14, regression, zip install, sandbox Stage 7, the VM check on
the owner's approval, and the update of the everyday JARVIS on the owner's approval.

## Not in the master document

The capability plan (`docs/CAPABILITY-PLAN.md`: measuring, memory, plans that last, bounded autonomy, self-improvement)
is a separate proposal waiting for the owner; only its decisions D1 and D2 overlap with item A3, where they are built
as the master document's section 6 asks (sensitive changes ask first). The installer (`JARVIS-Setup.exe`) stays
proposed as the release after 1.0.15 unless the owner wants 1.0.15 held for it.
