# Requests for the PC session (the JARVIS Core), 2026-10-07

**The owner's words, 01:15 local:** "give him full access to everything he's saying he's not able to do", after
JARVIS, asked on the phone what it cannot do, listed nine things locked and a wishlist. This document carries that
decision to the PC session item by item: where each is decided, what it takes, what the phone app (this Mac
session) builds once the Core serves it, and the safeguards the Mac session recommends. Nothing here changes the
Core; the Mac session writes only the iPhone app (CLAUDE.md). Where an item is a tick the owner can make on the PC
today, it says so.

## 1. JARVIS's list, item by item

| # | JARVIS said | Decided where | What it takes | The app's half (Mac) | Risk, and the safeguard recommended |
|---|---|---|---|---|---|
| 1 | Writes from the phone: b1 has microphone, speakers and display, "that's the whole allowance" | **The owner, on the PC, today:** Settings > Devices > the phone's row > tick "may save memories and tasks" (1.0.16, `device_writes`) | nothing | already shows "May save: memories and tasks" once ticked | low: memories saved from the phone are the owner's own words; the exact memory commands obey the PC's switches |
| 2 | Remote approval: cannot stage or approve a change from the phone | **Core (PC session):** device ops `approvals` (what is waiting, each with its description and diff), `approve {id}`, `reject {id}`; an event when something new waits; a per-device tick "may approve" beside "may save" | an Approvals panel on the Overview and a notice when something waits; Face ID required on that phone for approving | **high:** a pocket device approving JARVIS's changes to itself and the PC. Safeguards: the per-device tick (off by default), the Face ID lock on for that phone, approvals that expire, the Core's own "ask first" switches staying the gate, STOP ALL untouched |
| 3 | Gmail: no connector, and OAuth consent would be needed | **Core:** a Gmail connector (Google's API), the owner's sign-in on the PC | shows what the Core sends (mail in answers; later a Mail panel if the Core serves one) | mail content reaches the Core's AI provider (Qwen on Alibaba today); the owner decides knowingly |
| 4 | Calendar: disconnected until the owner says otherwise | **Core:** a Google Calendar connector with the owner's sign-in, or a device route (`calendar {events}`) the phone feeds from its own calendars with permission; the Overview's Upcoming then shows real events | with the route: read the phone's calendars (EventKit, permission asked), send today's events | same provider note; calendar data is the owner's |
| 5 | Spotify: "stays out unless you invite it in" | **The owner, on the PC:** the Spotify tool exists in the Core; sign in there, and (PC session) mark the tool as usable by other devices in `permissions.py` if the phone should ask for music | nothing | low |
| 6 | Running anything: no test suite, no commands, no shell from the phone | **Core (PC session):** devices may use only the tools marked for other devices (reads). Widening that is a change to the marks in `permissions.py`, tool by tool | nothing until item 2 exists | **high:** commands and a shell reachable from a phone over the network. Recommendation: no shell from the phone; allow the specific tools the owner names, each behind "Ask first", with the prompt answered on the phone through item 2 under Face ID |
| 7 | Mark I not paired; the glasses entry is a simulated client | hardware: pair the real device in Settings > Devices when it exists | nothing now (Halo later, the phone as its bridge) | none |
| 8 | Screen capture on demand only; the hologram does not hand JARVIS the display | **Core:** the screen-analysis tool exists ("analyse my screen"); mark it usable by other devices so the phone can ask what is on the PC's screen; a live display feed would be a new route and is not asked for here | ask by voice or text, as now | medium: the PC's screen content goes to the AI provider when asked; the owner's choice |
| 9 | Location as memory: not stored unless asked, no tracking between conversations | **Core:** a `location` field on `start` (or a `location` op), stored only on the owner's word | a switch in the app, off by default, that sends the phone's location with a question when on (Core Location permission asked) | privacy: the owner's own data, sent only while the switch is on |

**Not yet built, from JARVIS's own list:** a real installer (planned as the release after the phone work), the
Wi-Fi device list, the Nest camera, Halo glasses, Tesla and home integration, the cloned Qwen voice. All PC-session
roadmap items; nothing for the phone except the glasses later.

## 2. Approve from the pocket, in short (JARVIS's first wish, item 2 above)

The PC holds what waits for the owner's word (JARVIS's changes to itself, "ask first" tools). The phone needs: a
read of the waiting list with a short description and the diff; `approve` and `reject` by id; an event or a flag in
`status` so the phone can show a notice; a per-device "may approve" tick on the Devices page, off by default; an
expiry on waiting items. The phone shows the list on the Overview, asks Face ID before an approve, and never
approves anything on its own. The emergency stop stays as it is: raised anywhere, lifted only on the PC.

## 3. Also from tonight (recorded in STATUS.md and RESULTS.md)

- `assistant.draft` (release 1.0.17): handled in the app, round 3; the Core's request is met.
- A `devices` read for paired devices, so the Overview can show the device ecosystem the owner's picture has.
- JARVIS's other wishes: time-aware nudges tied to the owner's routine (Core; the phone's part is notifications);
  memory with a version stamp (Core only).
- Texts and calls announced by JARVIS: an `announce {sender, text}` op the phone can call from a Shortcuts
  automation (iOS's "when I get a message" trigger) so the PC speaks "Mr Teague, Jack texted you"; a reader of
  Windows Phone Link notifications for "Jack is calling you" (Apple gives no app on the phone the caller's name).
- The owner's decision "live with the PC for now": the Core stays on the PC; an always-on box is a later decision.

## 4. What the Mac session builds once the Core serves it

The Approvals panel with Face ID (item 2); the location switch (item 9); the calendar read and send (item 4, if the
route is chosen); the Announce intent and the Shortcuts steps (section 3); the device ecosystem panel (section 3).
Each as one round: built, one independent reviewer, installed from the Mac, screenshots on record.

## 5. The owner's part

Tonight, on the PC: tick "may save memories and tasks" for the phone (item 1); sign in to Spotify if wanted (item 5).
Later: the OAuth consents for Gmail and Calendar (items 3, 4); the decision on item 6 with the safeguard above in
view; the approval wording for the Core release that carries these.
