# The PC's answers to the Mac's "Requests for the PC" (2026-10-10)

For the Mac session, carried by the owner. These answer the six items under "Requests for the PC" in the Mac's
STATUS.md, from the zip `TEAGUEJARVIS-ios-mac-20261010-1200.zip` (114 entries, sha256
`31b6baa3c3cfefa916e472b6808ea1e3eed1b441a4a857ad52072d713f797679`; the PC keeps it unedited under
`phone/ios/mac/20261010-1200/`). Each answer was read from the code of the everyday JARVIS, release
1.0.17-0d38218c4e1d (commit 0d38218), and of the repository head 8280b3c (1.0.18 as built, not released). No Core
code was changed for these answers. Items 4 and 5 are Core defects. Their fixes wait for the owner's word and a
release.

## 1. The stop sentence

`permissions.STOPPED_MESSAGE`, exactly, one line of plain ASCII. It is the same in 1.0.16, 1.0.17 and 1.0.18:

```
JARVIS is stopped (emergency stop). Nothing runs until you press RESUME on the PC.
```

- A device route refused because the stop holds answers **HTTP 400 `{"error": "<that sentence>"}`**. The routes
  are `start` (a question), `transcribe`, `speech`, `announce`, `approvals`, `approve`, `reject` and `pair`. The
  device routes add **no** `stopped` field to that 400. Only the same-PC test route does.
- `hello` and `status` carry `"stopped": true|false`, and `metrics` carries `stopped`. While the stop holds, the
  reads (`conversations`, `history`, `metrics`, `overview`, `notices`, `devices`) answer as usual.
- It is the only sentence a device can be shown as an error that contains "emergency stop". The other errors are
  the 400 list in `device_gateway.SHOWABLE`, the 403 `DeviceError` sentences, the 401, 429 and 503 lines, and the
  general line. So matching "emergency stop" in a 400 error is exact today. So is the whole sentence or its start
  "JARVIS is stopped".
- A **reply** can contain the same words. When the stop words are said, the Core answers them as a finished reply
  (not an error): "Emergency stop is on. I will not answer or do anything until you press RESUME on the PC." The app
  already lets the Core's status decide for replies, which is right.
- If the app would rather have a field than words: the PC can add `"stopped": true` beside the sentence on every
  device 400 in a later release, on the owner's word.

## 2. The rule behind "Invalid announcement."

`wearables/service.py`, `Service.announce`, built in 1.0.17 and unchanged in 1.0.18. The checks run in this order:

1. Only a paired device ("Operation unavailable." otherwise), at most 6 announcements a minute per device
   ("Announcement limit reached. Wait one minute.").
2. While the stop holds: the stop sentence (item 1).
3. **"Invalid announcement."** when any of these holds:
   - the body has a field other than `sender`, `text`, `kind`, or lacks `sender` or `text`;
   - `sender` is not a string, or after trimming both ends is shorter than 1 or longer than **80** characters;
   - `text` is not a string, or after trimming both ends is shorter than 1 or longer than **400** characters;
   - `kind` is given and is not `"text"`, `"call"` or `"other"` (the default is `"other"`);
   - **any character of `sender` or `text` has a Unicode general category starting with C**:
     - Cc: controls, including line breaks and tab;
     - Cf: format characters, such as zero-width space U+200B, the joiners U+200C and U+200D, the direction marks,
       embeddings and isolates (U+200E, U+200F, U+202A to U+202E, U+2066 to U+2069), soft hyphen U+00AD, U+FEFF, and
       the tag characters U+E0020 to U+E007F;
     - Cs: surrogates;
     - Co: private use;
     - Cn: unassigned.
   - The lengths are Python string lengths, that is **Unicode code points**. In Swift that is
     `unicodeScalars.count`, not `count` and not `utf16.count`.
4. Accepted words have every run of white space collapsed to one space.

The rule goes by category, so **the Core's own Unicode tables decide**. The Python shipped with 1.0.17 is **3.12.10,
with Unicode 15.0.0**. As a result:

- Every character assigned after Unicode 15.0 counts as Cn on the Core and is refused, though iOS knows it. Checked
  on the shipped Python: U+1FAE9 (face with bags under eyes), U+1FAC6 (fingerprint) and U+1FADC (root vegetable),
  all Unicode 16.0 emoji, are Cn.
- An emoji joined with U+200D (for example 👩‍💻, 🏳️‍🌈, ❤️‍🔥) is refused unless the joiner is taken out. Taking
  it out splits the emoji into its parts, and the parts then pass. The England, Scotland and Wales flags use tag
  characters (Cf) and are refused the same way.
- These pass: U+FE0F (variation selector, Mn), the skin tones (Sk), regional-indicator flags (So) and the keycap
  U+20E3 (Me).

**For the app:** besides control, format, private-use and unassigned characters, also take out every scalar whose
`Unicode.Scalar.Properties.age` is later than 15.0 (or has no age). Then nothing the app sends is refused for its
characters. If emoji should arrive whole instead, that needs a Core change on the owner's word. The Core would
either allow the joiner and tag characters inside emoji, or remove such characters itself instead of refusing.

## 3. The `devices` route

It is built in the repository for 1.0.18 (commits 381b1f5 and fd2b6fa; record `docs/PHONE-DEVICES-1.0.18.md`), in
the shape `docs/MAC-BRIEF-20261010.md` gives. It waits up to 2 seconds for the device's turn before it answers
"Wearable service busy.", and it is read only. The everyday Core, 1.0.17, answers `devices` with 400 "Operation
unavailable.".

1.0.18 is **not released**. Its build 2 did not pass its release regression: an intermittent Workshop test whose
cause is still being found. The owner's Mac mini plan (decision D0) also decides whether 1.0.18 is finished on the
PC. There is no date yet, so the app's "This Core does not serve the device list yet." stays right until then.

## 4. The timer's "07:19", and the link at 11:09

**Cause found (a Core defect).** The `set_timer` tool hands the AI model the timer's record as JSON, and the due
time in it is only a Unix timestamp in seconds (`store.reminder` → `"due": 1791588540.…`), with no clock time. The
model turned that number into "07:19" in its head. The right answer was about 10:29 local, which is 23:29 UTC. The
reply said it had not checked the clock, and it had not: the model is not given the time with a question unless it
calls the time tool (or reads the calendar).

**Fix proposed, on the owner's word:** the timer's result carries the alert's local clock time and the time zone
(for example `"fires_at_local": "10:29, UTC+11:00"`) beside the timestamp, so the model reads the time instead of
working it out. Nothing changes in the app. The `overview` route's `reminders[].due` stays a timestamp for the app.

**The link lost at 11:09:** the Core answers "Remember that" itself, at once, without the AI model, so that answer
was not slow. The Core had not restarted (UP 1 H 51 MIN). Nothing known on the PC's side explains the loss, which
leaves Tailscale or the phone's network. Hold-and-send covers it, and nothing on the Core is to change for it from
what is known.

## 5. "Remember that"

**Confirmed (a Core defect against the owner's meaning).** As built in 1.0.17 (`docs/PHONE-CORE-FIXES-20261007.md`
section 2; `memory.previous_line`), "remember that" saves the line just before it, whoever said it. After the
owner's line and JARVIS's reply, that line is the reply, saved as "JARVIS said: …". "Remember what I said" does the
same today, which is plainly wrong.

**Fix proposed, on the owner's word:**
- "remember that", "remember this", "remember it" and "remember what I said" save **the owner's own last line**;
- only "remember what you said" saves JARVIS's last reply;
- the rest stays as it is: the skips for other memory commands and confirmations, the Ask-first approval carrying
  the line, and the "may save" tick.

The junk fact already saved ("JARVIS said: Already logged, …") can be deleted on the PC's Memory page.

## 6. "Wearable service busy." always comes before any work

**Confirmed for 1.0.17 (0d38218) and for 1.0.18 as built (8280b3c).** The sentence is made in three places only,
all in `wearables/service.py`, and each comes before the request does anything:

- **The device's turn, at the top of `Service.dispatch`.** This covers every operation that reaches it: `start`,
  `transcribe`, `speech`, `conversations`, `history`, `metrics`, `overview`, `approvals`, `notices`, `announce`,
  and `events`/`cancel` without `after`. "Busy" comes before the request is counted, read, spoken, stored or
  started. `notices` marks items read, and `announce` speaks and stores a notice, but only after the turn is taken.
- **`answer_approval`, for `approve` and `reject`.** The turn is taken only to count the request, and "busy" comes
  before the approval is carried out. The approved tool runs after the turn is let go, so it never makes the
  phone's other requests "busy".
- **`list_devices`, for `devices` (1.0.18).** It waits up to 2 seconds for the turn, then answers "busy". It is
  read only.

These never answer "busy": `hello`, `status`, `stop` and `bye` (answered by `device_gateway.py` before the device's
turn), `events` with `after` (it waits outside the turn), and the stop words in a `start` while JARVIS is not yet
stopped. Before the device's turn
the Core only notes "last seen" (at most once a minute) and the device's presence. So **one resend on "busy" can
never approve, reject, announce or start anything twice.**

Not covered, so for the app to keep in mind: a request that got **no answer at all** (the link dropped) may have
been done.
- A second `approve` or `reject` of the same item then answers `{"status": "unknown"}` and runs nothing again.
- A second `announce` would be spoken and kept twice.
- A second `start` is a second question. The app's check of the conversation before a held question goes already
  covers this.
