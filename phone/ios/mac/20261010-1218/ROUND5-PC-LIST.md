# Round 5: the phone's half of "everything on the list" (owner: "build from MAC-REQUESTS-20261007.md", 2026-10-07)

The PC session wrote docs/MAC-REQUESTS-20261007.md (sha256 a40ead701efe6a9ae51cf9d9f9eb109de52a2ca8c951e21d48fd05633ac0f450):
the exact device routes the Core will serve in release 1.0.17 and the seven app items R1 to R7. This record says
what the app now does for each, how it behaves on today's Core (1.0.16, which serves none of it), and what the
owner does. CLAUDE.md's rules apply: the app calls exactly what the document specifies; a missing field reads as
false or zero; a 400 "Operation unavailable." reads as "not on this Core yet"; nothing invented on screen.

## 1. Item by item

| Item | Built | On today's Core (1.0.16) | After 1.0.17 is installed on the PC |
|---|---|---|---|
| R1 Approvals panel behind Face ID | `ApprovalsView` (a sheet from the Overview's APPROVALS panel and from the Ask screen's waiting line): the waiting list with kind, label, who raised it and when it expires, the detail (the diff for a self-change) in a monospaced scrollable box, REJECT (no Face ID) and APPROVE (Face ID or the passcode first, always; nothing sent on a failure or cancel; hidden while the emergency stop holds). The answer's sentence shows in place; after "applied" on this phone's own conversation the lines are re-read so the receipt shows on Ask. | the panel says "Approving from the phone comes with JARVIS release 1.0.17 on the PC"; nothing is asked of the Core | without the owner's tick: "Set on the PC"; with it: the list, live |
| R2 Ticks shown, waiting notice | THIS PHONE rows "PC's tools" and "Approving" as the Core reports them (read-only); the Ask screen shows "N approvals waiting · open" when the Core counts any; `status` is read every 10 s while Ask or Overview shows, for the counts | the rows read "Comes with Core 1.0.17" | the ticks and the count as set on the PC |
| R3 Location switch | Phone settings > "Send my location with questions" (off by default; iOS's "while using" permission asked when first turned on); while on, `start` carries the last fix no older than two minutes (`lat`, `lon`, `accuracy_m`), but only to a Core whose hello/status says `location: true` (since 2026-10-10, section 6; before: the 1.0.17 approval fields); the THIS PHONE panel says what is true right now (not sent, denied by iOS, waiting for the hello, this Core does not take it, no fix, sent); `LocationProvider.swift` | nothing is sent: a 1.0.16 Core refuses a question with an unknown field (core-reference/wearables-service.py: "Unknown fields."), so the app gates on the field as section 0 of the PC's document says, and the sheet says so under the switch | the model answers for where you are; directions start from here; nothing stored |
| R4 Notices and announcements | the Overview's NOTICES panel with the unread count and OPEN to `NoticesView` (newest first; reading marks them read); the App Intent "Announce to JARVIS" (From, Message, Kind) for a Shortcuts automation (section 2) | "Notices come with JARVIS release 1.0.17"; the intent answers "Announcements need JARVIS release 1.0.17 on the PC." | nudges, announcements, approvals and the Core's notes; the PC speaks "Mr Teague, Jack texted you: …" |
| R5 Calendar and mail in Upcoming | UPCOMING shows the calendar's next 24 hours above the reminders when `calendar_connected` is true (time or "All day", title, place), and "N unread in the inbox" when the Core sends a number | unchanged: reminders only | after the owner's Google sign-in on the PC |
| R6 Device ecosystem | the Overview's DEVICE ECOSYSTEM panel from `devices`: the PC (name, Core version, online), each paired device (kind, online, this phone marked, its allowances as words), the simulated client labelled "simulated"; read every 30 s with the overview | "This Core does not serve the device list yet. Nothing is invented here." (until 2026-10-10: "The device list comes with JARVIS release 1.0.17 on the PC. ..."; asked again only when the Core's version changes) | **not on 1.0.17 either** (the PC's brief of 2026-10-10: never built; the Core answers "Operation unavailable."); the PC adds it in a later release |
| R7 Screen analysis | nothing to build: with the tools tick on, "analyse my screen" is answered from the PC's screen | | |

## 2. The owner's Shortcuts automation for texts (R4), once per person

On the phone, in the Shortcuts app:

1. Automation tab > + (New Automation) > scroll to **Message**.
2. Sender: choose the person (for example Jack). Message Contains: leave empty. Choose **Run Immediately** and turn
   off "Notify When Run". Next.
3. New Blank Automation > search **Announce to JARVIS** (under the JARVIS app) and add it.
4. In its card: tap **From** and type the person's name (Jack); tap **Message** and choose the variable **Shortcut
   Input** (the message's text); Kind stays Text message. Done.

From then on, when Jack texts, the PC says "Mr Teague, Jack texted you: …" in JARVIS's voice (release 1.0.17 on
the PC and JARVIS running there), and the notice is listed on the phone. One automation per person you want named.

## 3. What the owner does (relayed from the PC's document)

- PC, today: Settings > Devices > the phone's row > tick "May save memories and tasks". After 1.0.17: the two new
  ticks on the same row, when wanted.
- PC, for R5: the Google sign-in in Settings > Connectors (steps come with the release).
- Phone, for R3: turn the location switch on only once 1.0.17 is on the PC.
- Phone, for R4: the automation above.

## 4. Requests back to the PC (none)

Everything the app needs is in the PC's document. The one open question (does a 1.0.16 Core refuse a `start` that
carries `location`?) is answered by the Core's own code in core-reference/: it refuses with "Unknown fields.", so
the app sends the field only to a Core that shows the 1.0.17 fields.

## 5. To do before the milestone, ticked as done

- [x] Compiled.
- [x] One independent reviewer (2026-10-07: 1 high, 3 medium, 12 low), findings applied: the location gated on the
  1.0.17 fields (the high one); the polling status read keeps its failures off the Ask screen; the approval receipts
  are an ordered list of five with the item's label and an icon per outcome; the unused notices time stamp removed
  and the pairing sentence names the location choice; calendar rows show start to end and the weekday when not
  today; the approvals sheet follows the Core's count and the hello; an unknown status is said as such; the sheet
  redraws when iOS denies location; the THIS PHONE row says what is true of the location; announcements count
  characters as the Core does and a photo-only message is not sent; notices gated on their own field; the stop
  learned from a 403 too; the PC tile keeps the release id's case; this record's wording; the waiting count read
  with a reply that may wait for approval.
- [x] The signed build installed from the Mac (02:30). The owner's screenshot of 02:24 (the build before the fix,
  with the location switch on) showed the defect the high finding describes; the fix is in the installed build.
- [ ] Screenshots of the Overview on today's Core ("not on this Core yet" on every new panel) in
  records/round5-20261007/.
- [ ] The real checks of R1 to R6 after the owner installs 1.0.17 on the PC, recorded then.

## 6. Round 5b: the PC's brief of 2026-10-10 (docs/PC-BRIEF-20261010.md)

Core 1.0.17-0d38218c4e1d is the everyday JARVIS on the PC since 2026-10-07 evening. The brief lists what changed in
the form since the Mac's copy of docs/MAC-REQUESTS-20261007.md (sha256 a40ead70..., the 02:06 version). The app's
answer to each item:

| Brief item | What the app does now |
|---|---|
| 1. `location: true` in hello/status | `DeviceInfo.locationField` / `takesLocation`; `start.location` only when it is true (`SessionModel.run`); the THIS PHONE row and the Phone settings note follow the same field and say "waiting for the Core's hello" before one has come |
| 2. `writes` with either tick | the "May save" row says "Memories and tasks (allowed on the PC)" (it no longer claims which tick) |
| 3. `self_change` and `memory` details | shown as sent; a detail now wraps (vertical scroll), a self-change's difference keeps its lines (two-way scroll) |
| 4. `failed` sentence | shown alone ("Refused or failed on the PC; nothing was changed."), not after "Failed." |
| 5. the stop on approve/reject as HTTP 400 | `SessionModel.isStopRefusal` (400 or 403 with "emergency stop") and `learnStop()` in fail(), approvals, approve/reject, notices, devices and speech; the stop empties the waiting list; the receipt says "Not answered: the emergency stop was on and dropped this item."; both sheets read again after RESUME |
| 6. "Approved from ..." line | re-read at once, or at the end of the question running at that moment |
| 7. no `location: null` | the field is left out without a fix; a fix iOS marks invalid is no fix |
| 8. `notices` reading | unchanged (read without `after`; reading marks what came as read) |
| 9. `announce` and invisible characters | `AnnounceToJarvisIntent.announceable`: line breaks and other separators become one space; format, invisible (default-ignorable), variation-selector, private-use and unassigned characters and the attachment marker U+FFFC are taken out; the 80/400 cut is trimmed; the `spoken: false` dialog says the PC kept it as a notice and did not say it aloud. New: an App Shortcut "Announce to JARVIS" (Siri, or the tile in the Shortcuts app) |
| 10. tools only the PC's window can carry out | nothing to build; the Core's sentence shows as the reply |
| R6 `devices` not on 1.0.17 | the panel keeps "Not on this Core yet" with version-neutral wording; no banner, no retry loop |

Also in this round: the location provider sends every fix (no 50 m distance filter, no automatic pause), so a phone
sitting still keeps a fix younger than two minutes; a reply's words no longer raise STOPPED on the phone (the Core's
status decides); two places that could shrink text under 9 pt (the header subtitle, the device tile's line) now cut
it instead; the pairing fields and FORGET THIS PAIRING are 44 pt tall.

Independent review (one reviewer, 2026-10-10): 0 high, 3 medium, 12 low; 14 applied as suggested. Low finding 7
(match the stop sentence by its beginning) was not applied as suggested: the exact text of the Core's stop sentence
is not on this Mac, so a prefix match could miss the real stop; the app keeps matching "emergency stop" in the Core's
fixed error sentences, and the exact sentence is asked of the PC (STATUS.md, "Requests for the PC").
