# Release 1.0.17, the access items: what was built (record)

The owner's decision of 2026-10-07 ("give jarvis all these permissions and make everything he said he didn't
have make him have it"; `docs/PHONE-ACCESS-PLAN.md`) built item by item in the Core. The phone's half of each item
is the Mac session's, against the exact routes in `docs/MAC-REQUESTS-20261007.md`. Every item: tests, one
independent reviewer, findings applied, committed by file list.

## 1. Item A: approve from the pocket, and this PC's tools for a paired device (2026-10-07)

### What a device can now be given (two ticks, off for every device)

Settings > Devices, on a paired device's row, beside "May save memories and tasks":

- **"May use this PC's tools"** (`devices.tools`): the device's questions are offered every tool the PC's own
  questions are, except the three only the PC's own window carries out (`permissions.WINDOW_TOOLS`: opening a
  section, starting an interface inspection, loading a video: refused with "This needs the JARVIS window on the
  PC."), under the owner's switches in Settings > Permissions: Allowed runs at once, Ask first waits (on
  the PC's Pending actions, and in the device's `approvals` list), Off is refused and not offered. The tools act on
  the PC the Core runs on. The tick includes saving: a device with it may save memories, notes, tasks and timers
  and its memory commands work, as with the 1.0.16 tick. Read again at every tool call (`App.device_tools`), so a
  tick taken back during a question stops the next tool of that question; a revoke clears it.
- **"May approve for JARVIS"** (`devices.approve`): the device may list what waits for the owner's approval and
  answer it: the same list and the same decision as the PC window (`App.approve`), whoever raised it (the PC's
  own question, this device's, or another device's). A revoke clears it.

Set only on the PC (`POST /api/devices {action: 'tools' | 'approve', id, allowed: bool}`, `DeviceBook.set_flag`,
`devices.FLAGS`); a device cannot tick itself (`hello` takes capabilities only). Each change writes an activity
row ("device may use this PC's tools: My phone: yes"). The two columns are added to an older database at start,
0 for every device; an older JARVIS after a rollback ignores them.

### The device routes (docs/MAC-REQUESTS-20261007.md)

- `hello` and `status` carry `tools`, `approve`, `waiting` (how many approvals wait; 0 unless the device may
  approve) and `notices` (0 until the Core keeps notices, item F); `writes` is true when either saving tick is on;
  the `scope` sentence says what the device may do.
- `approvals` `{}` lists the waiting items as a device sees them (`App.approval_rows`): `id`, `kind` (`tool`,
  `memory`, `self_change`, `draft`), `tool`, `label`, `detail` (the exact call in plain lines; for a change to
  JARVIS itself the reason and the difference, at most 20,000 characters), `created`, `expires`, `run_id`,
  `conversation`, `device` (the id, or `pc`) and `device_name` (the name, or "this PC").
- `approve {id}` and `reject {id}` answer one item through `App.approve_from_device`: `applied` with `result` (the
  receipt in plain words), `denied`, `failed` (one fixed sentence: "Refused or failed on the PC; nothing was
  changed."), `expired`, `unknown`. The Core's own error text never crosses.
- Without the approve tick: HTTP 403 `{"error": "Approving is not allowed for this device."}`. While the emergency
  stop holds: HTTP 400 with the stopped sentence (and the stop has dropped every approval anyway, as before).
- All three ops count against the device's 120 light reads a minute, like `overview`.

### What changed for everyone

- A waiting "ask first" call or a draft now lives **15 minutes** (`server.APPROVAL_SECONDS`; 5 before), so an
  answer from the owner's pocket is possible; a change to JARVIS itself keeps 30. Still single use, still dropped
  by the emergency stop. Every approval now records `created` and the `conversation` it belongs to.
- An approval answered from a device writes the activity row "approved from <device name>" (or "denied from"),
  and the line in the raising conversation reads "Approved from <device name>: <label>. Result: <receipt>."; the
  PC's own answers keep their words ("Approved on screen: ...").
- The instructions of a device question with the tools tick say what that means (the tools act on the PC; a tool
  set to ask first waits, say so).

### Safeguards, and what did not change

The emergency stop refuses every approval and every tool as before, and only the PC resumes. A device without
the ticks behaves exactly as in 1.0.16. An approved call passes `permissions.decide` again with the device's ticks
as they stand at that moment: a tick taken back between the question and the answer refuses the call (`failed`).
A device still sees only its own conversations. The owner's buttons on the PC, `/api/approvals/list` and
`/api/approval`, are unchanged.

### Checked

- `test_phone_access.py` (10 tests): the ticks (off by default, set only on the PC, revoke clears them, the
  columns added to an older database); a changing tool refused without the tick and run with it, Off refused,
  the model offered the PC's tools with the instructions; the tick taken back mid-question; the waiting list and
  the answer from the device for a PC question (reject, approve, single use, the activity rows and the
  conversation line), for the device's own question (and the tick taken back before the answer: `failed`), a
  memory command (`memory`) and a draft (`draft`), a change to JARVIS itself (`self_change`, its difference, a
  broken one `failed`), expired, unknown, and while stopped.
- `test_devices_view.cjs`: the words of the ticks on the Devices page.
- The device, permission, approval and development suites (190 tests) and the full Python suite (see the status
  record for the count at the commit).

### Independent review (one reviewer, 2026-10-07): no high finding; 1 medium and 8 low, all applied

1. Medium: with the tools tick a device was offered three tools whose result only the asking PC window carries
   out (opening a section, an interface inspection, a YouTube video), so the model got a receipt for a request no
   window would see. Fixed: `permissions.WINDOW_TOOLS`, refused for a device with one fixed sentence and left out
   of the offered tools; the model's instructions say so; a test.
2. Low: an approval answered from a device ran the approved tool under the device's service lock, so a `status`
   poll meanwhile was "busy". Fixed: counted under the lock, carried out outside it (`Service.answer_approval`).
3. Low: the device's name was read without the guard the Core has for a busy database. Fixed: `App.device_name`
   and a guarded read in `approval_rows`.
4. Low: an item answered a moment earlier (on the PC or from another device) was reported `expired`. Fixed: `unknown`.
5. Low: the activity row or the conversation line failing after a done call turned it into "failed; nothing was
   changed". Fixed: `App.note_done` writes them without failing the call.
6. Low: every memory item was labelled "Save a memory", also a forget or a correction. Fixed: the tool's own
   label ("Save a note, a task or a fact", "Change or delete a saved fact"), the command in `detail`.
7. Low: the Devices page never said the tools tick includes saving, and `accessText` was not shown. Fixed: one
   line under the ticks with the Core's words and the Ask-first advice.
8. Low: wording (API.md's 5 minutes; the window's legacy "Expires in 2 minutes"; the instructions' "on the device";
   the form's `detail` for a self change and the memory line's shape). Fixed.
9. Low: test gaps. Added: a real 1.0.16 database gaining the columns with its tick kept; `waiting` 0 without the
   approve tick while something waits; `reject` expired and unknown; a cancelled question's item; the PC answering
   a device's item ("Approved on screen" in the device's conversation, the list emptied); the same-PC test client
   refused; the window's tools refused.

## 2. Item C: screen analysis from the phone (2026-10-07)

"Analyse my screen" (or "take a screenshot") from a paired device with the tools tick now works, and nothing
streams the display:

- The device's question calls `assistant_control(analyse_screen)` as the PC's own would (the owner's own words are
  still required: `Controls.request` checks them). For a device's question `App.device_control` allows only the
  window controls in `server.DEVICE_CONTROLS`: reads of the window's state (`hologram_status`, `screen_status`,
  `microphone_status`), what switches something off (`mute`, `stop_speaking`, `stop_sharing`, `hide_hologram`), and
  `analyse_screen`. Starting sharing, the microphone or the hologram from another device is refused with "This
  needs the JARVIS window on the PC." before anything reaches the window.
- The Core lists a device's request at the new owner route `GET /api/control-requests` (`Controls.for_window`: id,
  run, action, the device's name), and the PC window reads that list every three seconds (`static/app.js`, also
  while the window is hidden; not during an inspection, not before the first state), does what is asked (the same
  list, checked again there), and answers through `/api/control-result` as it answers its own question's
  `control.requested` events. A device's request waits 45 s (`Controls.DEVICE_TIMEOUT`) instead of the window's 30.
- For `analyse_screen` the Core first checks that a vision model is configured ("No vision model is configured on
  the PC." otherwise, before any capture). The window captures one picture the way its own CAPTURE button does
  (the authorised display on the desktop app, or the shared screen in a browser), after discarding any earlier
  preview, uploads it as `screen-capture.jpg`, answers with the upload's id (`result.attachment`, accepted by
  `Controls.acknowledge`), and discards the preview again. The Core takes that picture out of the uploads only if
  it is the window's own capture (`screen-capture.jpg`, an image; a picture waiting in the PC's chat is left where it
  is), asks the AI model to describe it with no tools (`App.describe_picture`), and returns the description as the
  tool's result (`App.device_control_result`); the model then answers the phone. The picture is kept nowhere: a
  capture whose request is gone (cancelled, timed out, answered already) is dropped by `/api/control-result` and by
  the window (`/api/upload/discard`).
- No display authorised on the PC: the window answers `unavailable` with the sentence to show; no screen shared in a
  browser: likewise; nothing pops up on the PC by itself. No window, or no answer within the wait: "The PC's window
  is not open or did not answer, so this cannot be done from here." A busy window: `failed` ("The PC window is busy.").

Checked: `test_phone_access.py` `ScreenTests` and `ReviewTests` (a window thread that reads the list, uploads a
capture and answers; the description reaching the phone with the capture taken from the uploads; without the tools
tick refused; no window: the sentence after the wait; no vision model: said before any capture; an answer without
a capture: `failed`; a non-capture upload named as the capture: `failed` and left in place; a malformed id: HTTP 400;
a PC question's own control not listed and not rewritten; a late answer refused and its capture dropped; starting
sharing, the microphone or the hologram refused; the route needs the owner's session). The interface script tests
(24) pass with the window change.

## 3. Item D: location with a question (2026-10-07)

- `start` accepts `location {lat, lon, accuracy_m?, label?}` from a paired device (`wearables.service._location`:
  lat −90..90, lon −180..180, accuracy 0..100,000 m, label up to 80 characters; anything else, `null` included, is
  HTTP 400 `{"error": "Invalid location."}`). `hello` and `status` say `location: true` so the app sends the field
  only to a Core that takes it (an older Core refuses the whole question with "Unknown fields."). The phone sends it
  only while its own location switch is on (the Mac's half).
- The position is kept on the question in memory only (`run.location`, cleared when the question is answered) and
  given to the AI model in that answer's context as `device_location` with the note that it is current, not stored
  and not tracked, to be named by its label or in words and never repeated as coordinates; and to `get_directions` as
  the starting point when the owner says "from here" / "current location" / "my location" (`maps.directions(location=)`:
  the route starts at the coordinates, the result names the label or "your location", the Maps link carries the
  coordinates, which is the one place they can reach a reply). Without a position "from here" still asks the owner to
  use the Maps page, as before.
- Nowhere else: not in the conversation, the saved things, the activity rows, the tool evidence or the question's
  events (pinned by a test). A memory of a place is saved only on the owner's own words, through the memory commands
  and the save tick as for any memory.

Checked: `test_phone_access.py` `LocationTests` and `ReviewTests` (eight bad shapes and `null` refused; a minimal
position accepted; the position in the context of that answer only and in nothing kept, and gone from the question
afterwards; directions from "here" starting at the position, both in `maps.directions` and through a device's
question, and asking the owner without one).

### Independent review of items C and D (one reviewer, 2026-10-07): no high finding; 2 medium and 8 low, all applied

1. Medium: every window control was carried to the PC window for a device's question, so "start screen sharing" or
   "unmute" from the phone could start sharing or the PC's microphone, against the plan's "nothing streams the
   display". Fixed: `server.DEVICE_CONTROLS` (reads, switching off, one capture) in the Core and the same list in the
   window; the rest refused with "This needs the JARVIS window on the PC."; a test.
2. Medium: a capture whose acknowledgement was refused (the request cancelled, timed out or answered already) stayed
   in the Core's uploads for its lifetime. Fixed: `/api/control-result` drops a named capture when it refuses the
   answer; the window discards its upload when the answer fails; a test.
3. Low: the Core took whatever image the window named. Fixed: only an image named `screen-capture.jpg`; otherwise
   `failed` and the upload left in place; a test.
4. Low: the window could upload an earlier preview as "right now", toast on the PC when nothing was shared, and leave
   the capture in the Screen Vision dialog. Fixed: the preview is discarded before and after; a browser with no shared
   screen answers `unavailable` without calling the capture.
5. Low: "not open" could be false for a window that did not answer in time. Fixed: "not open or did not answer".
6. Low: vision was not checked before the capture. Fixed: "No vision model is configured on the PC." before anything
   is asked of the window; a test.
7. Low: `run.location` stayed on the finished question in memory for up to 30 minutes. Fixed: cleared when answered.
8. Low: the model would quote the coordinates in the Maps link. Fixed in the note (label or words, never the
   coordinates); the link itself keeps them, as the form says.
9. Low: wording (the plan's sentence; a comment pointing at sections not yet written; an item F sentence in the
   gateway's list; no "not on this Core yet" signal for the location field; `null`). Fixed: the sentence, the list,
   `hello`/`status` `location: true`, the form.
10. Low: test gaps. Added: the minimal position, directions from "here" through a device's question, the tool
    evidence in the "kept nowhere" check, the non-capture upload, the malformed id, the PC question's own control, the
    late answer, the refused controls.
