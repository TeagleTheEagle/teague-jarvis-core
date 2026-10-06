"""Record sections for items C and D, appended to docs/PHONE-ACCESS-1.0.17.md (LF)."""
import pathlib

p = pathlib.Path(r"C:\Users\jonny\JARVIS-claude-workspace\repo\docs\PHONE-ACCESS-1.0.17.md")
text = p.read_bytes().decode("utf-8")
assert "\r" not in text
assert "## 2. Item C" not in text
section = """
## 2. Item C: screen analysis from the phone (2026-10-07)

"Analyse my screen" (or "take a screenshot") from a paired device with the tools tick now works, and nothing
streams the display:

- The device's question calls `assistant_control(analyse_screen)` as the PC's own would (the owner's own words are
  still required: `Controls.request` checks them). The Core lists the request at the new owner route
  `GET /api/control-requests` (`Controls.for_window`: id, run, action, the device's name), and the PC window reads
  that list every three seconds (`static/app.js`, also while the window is hidden), does what is asked, and answers
  through `/api/control-result` as it answers its own question's `control.requested` events. A device's request
  waits 45 s (`Controls.DEVICE_TIMEOUT`) instead of the window's 30.
- For `analyse_screen` the window captures one picture the way its own CAPTURE button does (the authorised display
  on the desktop app, or the shared screen in a browser), uploads it as `screen-capture.jpg`, and answers with the
  upload's id (`result.attachment`, accepted by `Controls.acknowledge`). The Core takes that picture out of the
  uploads, asks the AI model to describe it with no tools (`App.describe_picture`), and returns the description as
  the tool's result (`App.device_control_result`); the model then answers the phone. The picture is kept nowhere.
- No display authorised on the PC: the window answers `unavailable` with the sentence to show ("No display is
  authorised on the PC. Open JARVIS there, Communications > Screen Vision, and authorise a display."); nothing pops
  up on the PC by itself. No window open at all: after the wait the device is told "The PC's window is not open,
  so this cannot be done from here." A window that is busy answers `failed` ("The PC window is busy.").
- The other window controls (mute, the hologram, screen sharing) go the same way when asked from a device with the
  tools tick; the window performs them with `performAssistantControl` and the result comes back to the phone.

Checked: `test_phone_access.py` `ScreenTests` (a window thread that reads the list, uploads a capture and answers;
the description reaching the phone with the capture taken from the uploads; without the tools tick refused; no
window: the sentence after the wait; an answer without a capture: `failed`; the route needs the owner's session).

## 3. Item D: location with a question (2026-10-07)

- `start` accepts `location {lat, lon, accuracy_m?, label?}` from a paired device (`wearables.service._location`:
  lat −90..90, lon −180..180, accuracy 0..100,000 m, label up to 80 characters; anything else is HTTP 400
  `{"error": "Invalid location."}`). The phone sends it only while its own location switch is on (the Mac's half).
- The position is kept on the question in memory only (`run.location`) and given to the AI model in that answer's
  context as `device_location` with the note that it is current, not stored and not tracked; and to
  `get_directions` as the starting point when the owner says "from here" / "current location" / "my location"
  (`maps.directions(location=...)`: the route starts at the coordinates, the result names the label or "your
  location", the Maps link carries the coordinates). Without a position "from here" still asks the owner to use
  the Maps page, as before.
- Nowhere else: not in the conversation, the saved things, the activity rows or the question's events (pinned by a
  test). A memory of a place is saved only on the owner's own words, through the memory commands and the save
  tick as for any memory.

Checked: `test_phone_access.py` `LocationTests` (eight bad shapes refused; the position in the context of that
answer only and in nothing kept; directions from "here" starting at the position, and asking the owner without one).
"""
p.write_bytes((text.rstrip("\n") + "\n" + section).encode("utf-8"))
print("record: items C and D appended")
