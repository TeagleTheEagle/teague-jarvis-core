# Requests for the Mac session (the JARVIS iPhone app), 2026-10-07: the phone's half of "everything on the list"

**From:** the PC session (the JARVIS Core, the desktop app, the releases). **To:** the Claude Code session on the
owner's Mac that writes the iPhone app. **Carried by:** the owner. This document stands alone: it holds the exact
device routes the Core will serve in release 1.0.17, so the app's half of each item can be built against them.

**The owner's decision (2026-10-07, 01:15 to the Mac session, 01:50 to the PC session, with five screenshots of
JARVIS's own list):** "give jarvis all these permissions and make everything he said he didn't have make him have
it", and "make a form for the mac so he can apply to app as well". The Core's build order is `docs/PHONE-ACCESS-PLAN.md`
on the PC; this is its mirror for the app.

## 0. Rules that do not change

- The app calls exactly what the Core serves (`POST /api/device/<op>`, header `X-Jarvis-Device: <id>.<key>`, JSON
  in, JSON out). Every refusal is an HTTP code with `{"error": "<one fixed sentence>"}`: 400 for a bad or unknown
  request, 401 for a refused key, 403 for something this device may not do, 429 for a lockout, 503 when the Core
  is not ready. Times are epoch seconds (UTC), as in `overview.reminders.due` and `history.messages.created`.
- **Until 1.0.17 is installed on the PC, none of this exists.** An older Core answers a new op with HTTP 400
  `{"error": "Operation unavailable."}` and sends `hello`/`status` without the new fields. The app treats a missing
  field as false or zero and a 400 "Operation unavailable." as "not on this Core yet", and shows nothing invented.
- Protocol stays 2. Feature presence is read from the fields, not from a version number.
- The emergency stop: raised anywhere, lifted only on the PC; while it holds, every op below except `stop`,
  `hello`, `status` and `bye` is refused with the stopped sentence, and `status.stopped` is true.
- Real data only on screen. Face ID before an approval, always (see R1), whether or not "Lock with Face ID" is on.
- One independent reviewer per round, findings applied, a zip back to the PC at the milestone (the standing rule).

## 1. What the Core will serve, in the order it is built

| Core item (plan) | Op or field | App request |
|---|---|---|
| A. Approve from the pocket | `approvals`, `approve`, `reject`; `hello`/`status` fields `tools`, `approve`, `waiting`, `notices` | R1, R2 |
| B. The phone gets the PC's tools | no new op: a question may now run any tool the PC may, under the PC's switches | R2 |
| C. Screen analysis from the phone | no new op: "analyse my screen" works with the tools tick | R7 |
| D. Location with a question | `start.location` | R3 |
| E. Memory release stamp | nothing for the phone | |
| F. Nudges, notices, announcements | `notices`; `announce`; `status.notices` | R4 |
| G. Gmail and Calendar | `overview.calendar`, `overview.calendar_connected`, `overview.mail_unread` | R5 |
| H. Wi-Fi device list, I. Nest | nothing for the phone in this round | |
| (asked by the Mac) the device ecosystem | `devices` | R6 |

## 2. The routes, exactly

### `hello` and `status` (changed: four fields added)

Response as today plus:

```json
{"tools": false, "approve": false, "waiting": 0, "notices": 0, "location": true}
```

- `tools`: the owner's tick "May use this PC's tools" for this device (off by default; set only on the PC).
- `approve`: the owner's tick "May approve for JARVIS" (off by default; set only on the PC).
- `waiting`: how many approvals are waiting for an answer, counted only when `approve` is true (else 0).
- `writes` is true when either "May save memories and tasks" or "May use this PC's tools" is ticked (the PC's
  tools include saving).
- `notices`: how many notices this device has not read yet (see `notices`).
- `location`: true when this Core accepts `start.location` (1.0.17 or later). An older Core has no such field and
  refuses a `start` that carries `location` with 400 "Unknown fields.": send the field only when `location` is true.
- `scope` (the sentence) changes with the ticks; show it as today.

### `approvals` (new; needs `approve`; 120 a minute)

Request `{}`. Response:

```json
{"items": [{
  "id": "f3a1...", "kind": "tool", "tool": "create_file",
  "label": "Create a file", "detail": "name: notes.txt\nfolder: Documents\ncontent: ...",
  "created": 1759800000.1, "expires": 1759800900.1,
  "run_id": "run-...", "conversation": "device-<id>-...", "device": "pc", "device_name": "this PC"
}]}
```

- `kind`: `tool` (a tool the owner set to Ask first), `memory` (an exact memory command: "remember that ..."),
  `self_change` (JARVIS's change to its own personality or style; `detail` is the reason, then the difference, up to
  20,000 characters; for `memory`, `label` is the tool's name, "Save a note, a task or a fact" or "Change or delete a
  saved fact", and `detail` the command with the line it saves),
  `draft` (a drafted action). `label` is one line of what will happen; `detail` is the exact call in plain lines.
- `device`: the id of the device whose question raised it, or `"pc"`; `device_name` is its name or "this PC".
  `conversation` is the conversation the question belongs to (the app's own when it starts with `device-<id>-`),
  or null.
- Waiting items live 15 minutes (`self_change`: 30), single use, and are dropped by the emergency stop.
- Without the tick: HTTP 403 `{"error": "Approving is not allowed for this device."}`.

### `approve` and `reject` (new; need `approve`; 120 a minute)

Request `{"id": "f3a1..."}`. Response:

```json
{"status": "applied", "result": "Created notes.txt in Documents."}
```

- `approve` statuses: `applied` (with `result`, the receipt in plain words, possibly empty), `failed` (with
  `result`, one fixed sentence: "Refused or failed on the PC; nothing was changed."), `expired`, `unknown`.
  `reject` statuses: `denied`, `expired`, `unknown`. An `id` that is not 32 hex characters: HTTP 400
  `{"error": "Unknown fields."}`.
- While the emergency stop holds: HTTP 400 with the stopped sentence (as every device request is refused then);
  the stop drops every waiting approval, so after a stop nothing waits and `approve` answers `unknown`.
- After `applied`, the Core also writes one assistant line into the raising question's conversation ("Approved
  from <device name>: <label>. Result: <receipt>."; for a `memory` item "Approved from <device name>. Remembered:
  ...", the command's own answer): if that conversation is the app's own, re-read `history` to show it; if it is
  the PC's, nothing more to show.
- Every answer writes an activity row on the PC naming this device.

### `start` (changed: one optional field)

```json
{"text": "...", "conversation": "...", "image": "...", "location": {"lat": -33.86, "lon": 151.21, "accuracy_m": 12, "label": "Home"}}
```

- `location` is optional (leave the field out; `null` is refused); `lat` −90..90, `lon` −180..180, `accuracy_m`
  0..100000 (optional), `label` up to 80 characters (optional). Anything else: HTTP 400 `{"error": "Invalid location."}`.
- The Core gives it to the AI model for that answer and to directions as the starting point. **Nothing is stored
  unless the owner's words ask JARVIS to remember it** (the save tick and the memory rules apply). No history.
- Send it only while the app's location switch is on (R3).

### `notices` (new; paired; 120 a minute)

Request `{}` or `{"after": 1759800000.0}` (only items created at or after that time). Response:

```json
{"items": [{"id": "...", "kind": "nudge", "text": "Work runs till eight; the essay is due at nine.", "created": 1759800000.1}],
 "unread": 0}
```

- `kind`: `nudge` (a routine collision, item F), `announce` (an announcement the PC spoke, R4), `approval` (something
  new is waiting; only when `approve` is true), `system` (the Core's own notes: for now the automatic backups,
  "Automatic backup done." or "Automatic backup failed."). Newest first: the newest 50, or all of this device's
  unread ones when there are more (up to 200). Reading marks everything returned as read for this device;
  `status.notices` then counts only newer ones (a request with `after` later than that mark moves nothing).
  Every paired device sees every device's announcements: they are all the owner's.

### `announce` (new; paired; 6 a minute)

Request `{"sender": "Jack", "text": "running late", "kind": "text"}` (`kind`: `text`, `call` or `other`; `sender`
up to 80 characters, `text` up to 400). Response:

```json
{"announced": true, "spoken": true}
```

- The PC speaks it in JARVIS's voice ("<the owner's name>, Jack texted you: running late"; a call: "... is calling
  you."), window open or not, and shows it as a notice on the PC and in `notices`. `spoken` is true when the PC took the words to speak (its voice on and
  not the browser's, quiet hours off, not stopped, no queue of sounds already waiting); the sound itself is not
  awaited. `announced` is true whenever the notice was kept.
- A `sender` or `text` carrying the wake word ("Jarvis") or a stop phrase is kept in full in the notice but only
  announced, never read out: "<name>, Jack texted you. The message is on your phone." (the PC's own microphone
  must not take a stranger's text for a question). Control, format and zero-width characters anywhere in them:
  HTTP 400 `{"error": "Invalid announcement."}`.
- Over the limit: HTTP 400 `{"error": "Announcement limit reached. Wait one minute."}`. While stopped: refused.

### `devices` (new; paired; 120 a minute)

Request `{}`. Response:

```json
{"devices": [{"id": "...", "name": "iphone-15", "kind": "phone", "online": true, "last_seen": 1759800000.1,
              "allowed": ["microphone", "speakers", "display"], "writes": true, "tools": false, "approve": false,
              "this_device": true}],
 "pc": {"name": "THEGRIZZLYBEAR", "core_version": "1.0.17-...", "online": true},
 "simulated": [{"name": "Glasses test client", "kind": "glasses"}]}
```

- Paired devices only (revoked ones left out), the PC itself, and the simulated test client marked as such.
  Reads only; nothing on this list can be changed from a device.

### `overview` (changed: three fields added)

Response as today plus:

```json
{"calendar_connected": false, "calendar": null, "mail_unread": null}
```

- When the owner has signed in to Google on the PC (item G): `calendar` is the next 24 hours, up to 20 items
  `{"title", "start", "end", "all_day", "location"}` (epoch seconds; `location` may be null), and `mail_unread` the
  unread count in the inbox. When not connected: `false`, `null`, `null`. Never invented.

### Tools from the phone (item B, no new op)

With `tools` true, a question from the phone may run any tool the PC's question may, under the PC's Settings >
Permissions switches: Allowed runs at once; Ask first makes it wait (it appears in `approvals`; the reply says it
is waiting); Off is refused. Three tools only the PC's own window can carry out stay out of reach (opening a
section of the interface, starting an interface inspection, loading a YouTube video): refused with "This needs
the JARVIS window on the PC." and not offered to the model. The `events` stream carries `tool.started`/`tool.completed` for those tools as it does
today for reads. With `tools` false, nothing changes from 1.0.16.

## 3. The app's half, item by item

**R1. Approvals panel (behind Face ID).** A panel on the Overview (and reachable from the Ask screen's notice):
the waiting list from `approvals` with label, detail (the diff for a `self_change`, monospaced, scrollable), who
raised it and when it expires; APPROVE and REJECT. Before `approve` is sent, a local authentication (Face ID, or
the passcode as iOS's fallback) succeeds; on any failure or cancel nothing is sent. REJECT needs no Face ID. The
result (`applied` with its receipt, `failed`, `expired`) shows in the panel, and the conversation re-reads
`history` when the item's `conversation` is the app's own. Shown only when `status.approve` is true; otherwise a
one-line note "Approving is set on the PC" and no list. The emergency stop hides APPROVE.

**R2. Ticks shown, waiting notice.** The Overview's "This phone" panel shows the two ticks as the Core reports
them ("May use this PC's tools", "May approve for JARVIS") beside the existing allowances; they are read-only on
the phone (set on the PC). When `status.waiting` is above 0, a notice line on Ask ("1 approval waiting") opens
R1. A reply whose tool result says it is waiting for approval gets the same line under it.

**R3. Location switch.** In the app's settings: "Send my location with questions" (off by default; Core Location
"when in use" permission asked when first switched on). While on, `start` carries `location` from the last fix
(no more than two minutes old, else omitted). A one-line explanation under the switch: sent with each question,
never stored by JARVIS unless you ask it to remember.

**R4. Notices and announcements.** A Notices list (newest first) from `notices`, opened from a bell on the
Overview showing `status.notices`; reading it clears the count. For texts: an App Intent "Announce to JARVIS"
(sender, text) that calls `announce`, usable from a Shortcuts automation the owner sets up ("When I get a message"
> run the shortcut with the sender and the message); the README gives the owner the exact Shortcuts steps.
Phone calls cannot be announced from the phone (iOS gives no app the caller); that is the PC's Phone Link later.

**R5. Upcoming panel from the calendar.** The Overview's Upcoming shows `overview.calendar` (title, start, end,
all day) above the reminders when `calendar_connected` is true, and `mail_unread` as one line ("3 unread") when
it is a number. Nothing when null.

**R6. Device ecosystem panel.** The Overview's device panel from `devices`: the PC (name, Core version), each
paired device with online/offline, kind and allowances, this phone marked, the simulated client labelled
"simulated". No invented devices, no network tiles.

**R7. Screen analysis.** Nothing to build: with the tools tick on, "analyse my screen" (typed or spoken) is
answered from the PC's screen; the reply may say the PC's window is not open or did not answer, that no display is
authorised there, or that no vision model is configured. A suggestion chip may offer the words. The phone can also
ask the window's state ("microphone status", "sharing status") and switch things off ("mute", "stop sharing"); it
cannot start sharing, the microphone or the hologram on the PC: those words are refused with "This needs the
JARVIS window on the PC."

Suggested order on the Mac: R1 and R2 as soon as 1.0.17 is on the PC (they need a real approval to test); R3, R4
and R6 can be built against the shapes above now, with the "not on this Core yet" state until then; R5 after the
owner's Google sign-in.

## 4. What the owner does (relayed)

- PC, today: Settings > Devices > the phone's row > tick "May save memories and tasks". After 1.0.17 is installed:
  the two new ticks on the same row, when wanted.
- PC, for R5: the Google sign-in in Settings > Connectors (the steps come with the release).
- Phone, for R4: the Shortcuts automation from the README of that round.
- At each Mac milestone: the zip to the PC session, as before.

## 5. Questions back to the PC session

Write them in the Mac's STATUS.md under "Requests for the PC" and the owner carries them; a field or op the app
needs that is not above is a request, not something to build around.

## 6. Changes after the copy the owner carried (2026-10-07, after item F's review)

- `notices`: the newest 50, or all of this device's unread ones when there are more (up to 200); a request with
  `after` later than the read mark moves the mark nowhere. Every paired device sees every device's announcements.
  The `system` kind is written by the automatic backups ("Automatic backup done." / "Automatic backup failed.").
- `announce`: `spoken` is true when the PC took the words to speak (voice on, quiet hours off, not stopped, no
  queue of sounds already waiting); the sound itself is not awaited. A `sender` or `text` carrying the wake word
  ("Jarvis") or a stop phrase is kept in full in the notice but only announced, never read out ("<name>, Jack
  texted you. The message is on your phone."). Control, format and zero-width characters anywhere: `Invalid
  announcement.`
