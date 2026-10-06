# JARVIS gets everything on its list: the access plan (build order for the Core)

Status: **OWNER DECISION, 2026-10-07 about 01:50 local**, in the PC session, with five phone screenshots of
JARVIS's own answers (`docs/phone-evidence/jarvis-locked-list-20261007-*.png`): "give jarvis all these permissions
and make everything he said he didn't have make him have it", then "and make a form for the mac so he can apply to
app as well". The same words were said to the Mac session at 01:15, which carried them here as
`phone/ios/mac/20261007-0135/PC-REQUESTS-20261007.md`. This document is the build order the PC session follows; the
Mac's half of each item is in `docs/MAC-REQUESTS-20261007.md` (the form the owner carries to the Mac).

Everything here is built in the repository, tested, independently reviewed, and reaches the everyday JARVIS only as
a release through the Stage 7 check and the everyday update, each on the owner's approval. Assumed placing: **added
to release 1.0.17** (the own-app release, items 3.1 to 3.4 already built), so one VM check and one everyday update
carry both; the owner can say "separate release" to ship the installer first, or "build 1.0.17 now" at any point to
ship what is done.

## 1. What JARVIS said, and where each thing is decided

From the screenshots (01:09 to 01:21 local). "Locked by your own hand":

| # | JARVIS said | What is true in the code today | Who unlocks it |
|---|---|---|---|
| 1 | Writes from the phone: b1 has microphone, speakers and display, "that's the whole allowance" | The tick "May save memories and tasks" exists on the phone's row in Settings > Devices (1.0.16, `devices.writes`); it is off for the phone | **The owner, on the PC, today.** Nothing to build. |
| 2 | Remote approval: cannot stage or approve a change from the phone | Waiting approvals live in the Core's memory and only the signed-in PC window can list or answer them (`/api/approvals/list`, `/api/approval`); nothing tells a device that something waits | **Core item A** |
| 3 | Gmail: no connector | No mail code of any kind | **Core item G**, after the owner's Google sign-in (section 3) |
| 4 | Calendar: disconnected | No calendar code of any kind; the briefing says "unavailable" | **Core item G**, same sign-in |
| 5 | Spotify: stays out unless invited | The Spotify tool exists (PKCE sign-in from Settings; tokens in memory until the next restart); not offered to devices | **The owner signs in on the PC; Core item B** lets the phone ask for it |
| 6 | Running anything: no test suite, no commands, no shell from the phone | `computer_run_tests` exists (runs the unit tests, a read). There is **no shell or command tool for JARVIS on the PC either**: "commands" on the PC are the typed command words the window answers. Devices may call only nine reading tools | **Core item B** gives the phone the same tools as the PC. A shell tool is not built (section 5) |
| 7 | Mark I not paired; the glasses entry is a simulated client | True: `wearables/` is the mock pipeline; the only real devices are paired ones | Hardware; the Mark I pairs like any device when it exists |
| 8 | Screen capture on demand only; the hologram does not hand JARVIS the display | "Analyse my screen" is an action the PC window carries out for its own question (capture, upload, a new question with the picture); a device's question cannot ask for it | **Core item C**: a phone question can ask the PC window for a capture |
| 9 | Location as memory: not stored unless asked, no tracking | True: `start` refuses any field but text, image and conversation; nothing stores a location | **Core item D**: the phone may send its location with a question; stored only on the owner's words |

JARVIS's wishes (01:09 and 01:12): approve from the pocket (item A); time-aware nudges tied to the owner's routine
(**item F**); memory with a version stamp so an older release's note stops arguing with today's build (**item E**);
the connectors (item G). "Not yet built, from your own wishlist": a real installer (release 1.0.17, items 3.1 to 3.4
built), the Wi-Fi device list (**item H**; the owner's word for it is this decision), the Nest camera (**item I**,
after the owner's Google steps), Halo glasses, Tesla and home integration (section 5), the cloned Qwen voice (fixed in
1.0.16; the owner selects it, section 3). At 01:21: no tool for the Wi-Fi part itself (item H).

## 2. The build order (Core, this session)

Each item: built in the repository, tested (`python -m unittest`), one independent reviewer, findings applied, a
record in `docs/`, committed by file list. Device routes are defined here and handed to the Mac in the form.

**A. Approve from the pocket** (items 2 and 6's gate; JARVIS's first wish)
- Two new ticks on a device's row in Settings > Devices, both off by default, saved like "May save memories and
  tasks": **"May use this PC's tools"** (`devices.tools`) and **"May approve for JARVIS"** (`devices.approve`). Revoke
  clears both. Pairing never grants them.
- Device ops `approvals` (the waiting list: id, kind, label, detail or diff, when it expires, which run and device
  raised it), `approve {id}` and `reject {id}`, allowed only with the approve tick; the answer carries the result the
  PC window would have shown (applied with its receipt, denied, expired, or refused while the emergency stop holds).
  `hello` and `status` gain `tools`, `approve` and `waiting` (how many approvals wait). The same list and the same
  `App.approve` as the PC window: one path, one audit row naming the device that answered.
- A waiting approval lives 15 minutes instead of 5 (JARVIS's changes to itself keep 30), so a pocket answer is
  possible; still single use, still dropped by the emergency stop.
- **Safeguards kept:** the emergency stop refuses every approval; a device without the tick gets a fixed refusal;
  the phone asks Face ID before approving (the Mac's half); the PC's Settings > Permissions switches stay the gate for
  what asks at all; nothing can be approved twice.

**B. The phone gets the PC's tools** (items 5, 6 and the rest of 2)
- With "May use this PC's tools" ticked, a device's question is offered every tool the PC's question is, under the
  same Settings > Permissions switches: Allowed runs at once, Ask first waits (answerable on the phone through A or
  on the PC), Off is refused. The tools that need the owner's own words (timers, saved memories, the window's
  controls) read them from the phone's question. JARVIS's changes to itself keep asking first (decision D1).
  Without the tick, nothing changes: the nine reading tools, plus the four saving tools with the save tick.
- This includes `spotify`, `play_music`, `open_app`, `computer_open_page`, `create_file`, `computer_run_tests` and
  the rest. Recommended to the owner (their choice on the Permissions page): set `create_file`, `open_app`,
  `computer_open_page` and `inspection_link_change` to Ask first, so the phone can only propose them.
- Not built: a shell or command runner for JARVIS (none exists on the PC today; a separate decision, section 5).

**C. Screen analysis from the phone** (item 8)
- "Analyse my screen" from a device with the tools tick: the Core asks the open PC window for a capture (the same
  30 s request the window answers today, now also for a device's question), runs the vision step on the picture,
  and answers on the phone. If no window is open: "The PC's window is not open or did not answer, so this cannot be
  done from here." The picture is not kept beyond the answer. Nothing streams the display, and nothing starts
  sharing, the microphone or the hologram from the phone: only reads, switching off, and one capture.

**D. Location with a question** (item 9)
- `start` accepts `location {lat, lon, accuracy_m, label}` from a device. It is given to the AI model for that answer
  ("the phone reports ...") and to `get_directions` as the starting point. The Core stores nothing unless the
  owner's words ask it to remember (the save tick and the memory commands apply, as for any memory). No history.

**E. Memory with a release stamp** (JARVIS's third wish)
- Every saved memory records the release it was saved under (`items.release`, a schema step with a migration for old
  rows). The Memory page shows it; the model sees it ("saved under 1.0.11") with one standing rule: when two memories
  about JARVIS itself disagree, the newer release's wins. Nothing is deleted by itself.

**F. Time-aware nudges** (JARVIS's second wish)
- Settings > Routine: the owner's week as blocks (days, start, end, a label: work, gym, school). A Core thread (like
  the backup thread, once a minute) looks for a collision: an open task or reminder due inside or right after a
  block. One nudge per collision, never repeated, none in quiet hours. On the PC: a notice and a spoken line when
  "proactive" is on. On the phone: `status.notices` counts and a `notices` op lists them (the Mac shows them).

**G. Google: Gmail and Calendar** (items 3 and 4, after the owner's steps in section 3). **Built 2026-10-07, changed
from the first design:** no Google sign-in screen (a personal account's OAuth app stays in testing status and its
sign-in expires every seven days); instead an app password for Gmail over IMAP and SMTP, and the calendar's secret
iCal address, both lines in the key file (`docs/GOOGLE-STEPS.md`; record `docs/PHONE-ACCESS-1.0.17.md` section 4).
- `mail.py` and `calendar_feed.py`; Settings > Connections > Connectors with a TEST for each.
- Tools: `mail_search` and `mail_read` (reads), `mail_send` (a change that always asks first: the draft waits for
  the owner's approval on the PC or on a device that may approve), `calendar_events` (a read). The daily briefing
  gets a real calendar section. The phone's `overview` gets the next 24 hours of events and the unread count.
  Adding a calendar event is not built: it needs the sign-in screen (the owner's separate decision, "calendar add").
- Plainly: anything JARVIS reads from mail or the calendar goes to the AI provider (Qwen on Alibaba) with the
  question, as every question does.

**H. The Wi-Fi device list** (owner's wishlist; "no tool for the Wi-Fi part")
- Read-only: what the PC's own neighbour table and adapters know (addresses, names where the network resolves them,
  the Core's own machine), as a tool `network_devices` (a read, usable by devices) and a section "On this network" in
  Settings > Devices. No probing, no sending to the devices found, nothing paired by it: seeing a device never means
  touching it (JARVIS's own boundary, 01:21). Built last of the Core items because it reaches into the home network.

**I. The Nest camera** (owner's wishlist; after G and the owner's Device Access registration)
- Through Google's Smart Device Management API on the same Google sign-in: list the home's Nest devices and their
  state, and a camera's live-stream link where the model supports it. Which camera model the owner has decides what
  is possible; the owner's steps are in section 3. Built when those steps are done; otherwise it stays listed.

Then release 1.0.17's remaining steps: the review of item 3.4, the version 4 Stage 7 scripts, the release-notes
entry, the build, comparison, regression, zip and Setup rehearsals, the sandbox Stage 7, `docs/STAGE7-CHECK-1.0.17.md`
for the owner's approval, the VM check, the everyday update.

Rough size, told to the owner: A to D one to two sessions; E and F one; G one to two; H half a session; then the
release work one to two. About five to seven long sessions before the VM check.

## 3. The owner's steps (only the owner can do these)

| When | Step |
|---|---|
| Today | On the PC, JARVIS window: Settings > Devices > the phone's row > tick "May save memories and tasks" (item 1). After 1.0.17 is installed, the two new ticks on the same row. |
| Today, if wanted | Settings > Spotify > sign in (the sign-in lasts until JARVIS restarts; a lasting sign-in is a later item). |
| Before item G is usable | `docs/GOOGLE-STEPS.md`: an app password for Gmail (2-Step Verification on, then myaccount.google.com/apppasswords) and the calendar's secret address in iCal format, as three lines in the key file (`GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `GOOGLE_CALENDAR_ICS`; Claude never sees them); start JARVIS again; Settings > Connections > TEST. No Google Cloud project, nothing that expires. |
| Before item I is usable | Google's Device Access programme: the one-time US$5 registration, a Google Cloud project with an OAuth client (the Nest API has no app-password path, so this one does need the sign-in screen, re-done every seven days while the app is in testing status), and the Nest devices' home shared with it; the project id goes into the key file as `GOOGLE_DEVICE_ACCESS_PROJECT`. Also: which Nest camera model. |
| No hurry | Run `tools/host/Test-QwenVoice.ps1` (jonny account) and send the photo; when it says SPEAKS, Settings > Voice > VOICE PREVIEW > Qwen (the cloned voice; fixed in 1.0.16). |
| When the release is ready | "I approve the Stage 7 check of 1.0.17", then "I approve the update of my everyday JARVIS to 1.0.17" (each after its plan). |

## 4. The Mac's half (carried in `docs/MAC-REQUESTS-20261007.md`)

An Approvals panel behind Face ID (A); the tools tick shown and the "waiting" notice (A, B); the location switch
(D); notices (F); the Upcoming panel from `overview.calendar` (G); the device ecosystem panel from `devices`; the
Announce intent with a Shortcuts automation for texts (`announce` op, built with the notices in F). Each one is built
on the Mac once the Core serves it, against the exact bodies in the form.

## 5. Not built here, and why (each is one decision away)

- **A shell or command runner for JARVIS.** None exists on the PC today, so the phone cannot be given one. If the
  owner wants JARVIS to run commands on the PC, it is a new tool with its own risks (anything JARVIS is told to run,
  runs); say "command tool" and it is designed with limits first.
- **Mark I, Halo glasses:** hardware. They pair as devices when they exist; the Mark I's abilities are its own.
- **Tesla:** Tesla's Fleet API needs a developer registration, a public key hosted on a domain the owner owns, and
  the car's virtual key pairing; the owner's accounts, before any Core code. Say "tesla" with what car it is.
- **Home integration:** the owner names the devices (lights, thermostat, locks, which brand); each brand is its own
  connector. The Nest thermostat rides on item I if there is one.
- **Phone Link for calls:** Windows Phone Link shows "X is calling" as a notification on the PC; a reader of those
  notifications is a Windows change (notification access) and is listed, not built, until the owner says so.
- **Texts announced on the PC** need the Shortcuts automation on the phone (the Mac's half) and the `announce` op
  (built with F). iOS gives no app the text's content otherwise.

## 6. Decisions the owner may still change

- "separate release": installer first (1.0.17 as approved), the access items as 1.0.18.
- The two new ticks' names, and whether "May approve for JARVIS" should also cover JARVIS's changes to itself (built:
  yes, with Face ID on the phone; the owner can say "self-changes on the PC only").
- The waiting time of an approval (built: 15 minutes).
- Which tools the owner sets to Ask first on the Permissions page (the recommendation in item B).
