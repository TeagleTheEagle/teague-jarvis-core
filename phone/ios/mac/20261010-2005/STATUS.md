# JARVIS iPhone app: status (the Mac's living record)

**Read this first in every session in this folder; update it before a session ends.**
Last updated: 2026-10-10, about 20:06 local (round 6 on the phone and mostly checked: see "Round 6, ON THE PHONE"); earlier: 14:40 (round 6 installed), 13:25 (round 6 in progress), 12:20
(the PC's answers to the six requests; round 5c installed) and 12:00 local (Core 1.0.17 is on the PC; the PC's briefs of today applied as round 5b,
reviewed, installed and checked against the real Core: R1 to R4 and R6 met, R7 answered, one app defect fixed).

## Where the app stands

- **Version 1** (2026-10-06): built in Xcode at the first attempt, paired to the Core over Tailscale, 9 of the 10
  plan checks met (docs/PHONE-V1-RESULT.md). The look of 2026-10-06 applied (badge logo, space scene, orbital
  graphic).
- **Round 2** (written on the PC on 2026-10-06 late evening, placed here on 2026-10-07 from
  `JARVIS-ios-round2-20261006-2354.zip`, sha256 d6ba967120f84d01fdcb7e3c463c0e798e255ee394f03ae9174acece1877ac77):
  thirteen Swift files (`SiriIntents.swift` new); compiled here with a compile-only build (signing off); project
  settings changed by the Mac session: App Icon set to `AppIcon` in Debug and Release (it was empty, which is why the
  icon stayed the placeholder), `INFOPLIST_KEY_NSFaceIDUsageDescription` added beside the microphone key; the
  "Theme 2" and "PairingView 2" copies removed. **On the phone since 2026-10-07 00:14:** a signed build installed and
  launched from the Mac over the Mac-to-phone link (no delete of the old app). Seen from the Mac (RESULTS.md,
  `records/round2-20261007/`): plan check 3 PASSES (the conversation's lines are back after a true close and reopen),
  the header PASSES on the Ask screen (ONLINE on one line, STOP ALL readable), the badge icon shows on the home
  screen. Met since: the header on every screen (round 3's UI test), and on the owner's word at about 13:20 the
  screen awake, the vibration on a reply and Face ID with their face (RESULTS.md). **Open:** the stop note after
  RESUME, the headset, Siri, STOP ALL on the lock screen, a muted reply staying silent.
- What round 2 brings: the conversation's lines reloaded after a relaunch; the header at the phone's width; the stale
  stop note cleared; Bluetooth headsets and audio interruptions; the screen awake while listening, thinking, working
  or speaking; "Lock with Face ID" (off by default; STOP ALL on the lock screen); the Voice button with a vibration on
  the reply; Siri ("Hey Siri, ask JARVIS" opens the app with the question; "Hey Siri, stop JARVIS" raises the stop
  from the background). Independent review: docs/PHONE-APP.md section 8, every finding applied in these files.
- **Round 3, the command look** (owner: "build the command look", 2026-10-07; record ROUND3-COMMAND-LOOK.md):
  **built, reviewed (2 high, 3 medium, 12 low, all applied), installed from the Mac at 01:14 and seen on the phone
  with the Core ONLINE** (RESULTS.md, round 3 table; `records/round3-20261007/`). The third tab is now Overview
  (`OverviewView.swift`: brand strip and clock, the core, six systems with a ring, live diagnostics with sparklines,
  voice input with a waveform, projects, upcoming, this phone); the glowing `CoreOrb` replaces the Ask screen's
  rings; `Hud.swift` holds the panel kit; the session keeps health samples and the microphone level; the header
  word is "Offline" instead of "Not reached" (the long word cut the title to "JA…" in the round 2 run). App version
  1.2. The green orb while listening and the amber orb while thinking: seen by the owner at about 13:20. Left for
  the owner's eyes: the waveform on the Overview during a hold, the sparklines filling over minutes. The footer case
  fix (commit 5e8de67) is on the phone since the hold-and-send install of 01:32.
- **Hold-and-send** (app only, 2026-10-07, after the owner's "live with the PC for now"): a question typed or
  spoken while the Core cannot be reached is kept on the phone (`SessionModel.held`: the words, or the recording
  not yet transcribed) and sent at the next hello, status or health reading that reaches the Core (within 5 s on
  Ask or Overview; on Chats at the next tab or scene change), within 15 minutes of the first hold; later it is
  dropped and said so. Before typed words go, the conversation on the Core is read: a question whose request got
  through just before the link dropped is not sent twice (its reply is shown instead). One question at most, a
  second is refused with the typed words kept; the question's bubble comes off the screen and the dashed amber box
  with DROP carries the words; DROP, NEW CHAT, opening a chat, the emergency stop and a forgotten pairing drop it;
  nothing goes out over the lock screen; the phone never answers it itself. Known limit: a request that reached the
  Core but whose message is not yet stored when the check runs would still be sent twice. Independent review: 0 high,
  5 medium, 6 low, all applied. **On the phone and checked by the owner** (2026-10-07 about 01:35, "it worked":
  Tailscale off, a question held, Tailscale on, the question sent and answered; RESULTS.md).
- **Round 4, the lock-screen and Control Center button** (owner: "build 1", 2026-10-07; record
  ROUND4-LOCK-SCREEN-BUTTON.md): a widget extension target `JARVISControls` with one control, "Ask JARVIS", that
  opens `jarvis://listen`; the app's new URL scheme (`Config/JARVIS-Info.plist`); hands-free listening that ends at
  a pause after speech, at a tap on the microphone or at the 30 s limit, dropped with no speech; `jarvis://stop` for
  Back Tap or Shortcuts. Independent review 3 high, 4 medium, 7 low, all applied. The first signed build registered
  the extension's bundle id in the owner's Apple developer account (disclosed). The first design (the control opening
  a link) did nothing from Control Center; the fallback (the intent performed in the app with `openAppWhenRun`,
  shared by both targets) is the design now. **Checked by the owner: the button opens the app (02:31, "yes it
  did"), and end to end at about 13:20 ("all good"): Face ID, the orb green with LISTENING, a spoken question, the
  orb amber with THINKING, the reply spoken with a short vibration, the screen on throughout.**
- **Round 5, the PC's list** (owner: "build from MAC-REQUESTS-20261007.md", 2026-10-07; the PC's document is
  docs/MAC-REQUESTS-20261007.md; record ROUND5-PC-LIST.md): the app's half of approvals behind Face ID (R1), the
  ticks and the waiting line (R2), the location switch (R3), notices and the "Announce to JARVIS" intent for a
  Shortcuts automation (R4), calendar and mail in Upcoming (R5), the device ecosystem panel (R6); every piece reads
  "not on this Core yet" against today's 1.0.16 and shows nothing invented. Independent review 1 high, 3 medium,
  12 low, all applied; the high one (the location field sent to a 1.0.16 Core, which refuses every question with
  "Unknown fields.") was also found by the owner on the phone at 02:24 before the fixed build landed at 02:30.
  **Real checks against Core 1.0.17-0d38218c4e1d since 2026-10-10** (RESULTS.md, "Round 5 against Core 1.0.17").
- **Round 5b, the PC's brief of 2026-10-10** (docs/PC-BRIEF-20261010.md, kept verbatim; record ROUND5-PC-LIST.md
  section 6): 1.0.17 is the everyday JARVIS on the PC; the brief lists ten changes to the form and says `devices`
  was never built on the PC. Changes in the app, one per brief item: `start.location` only when hello/status says
  `location: true` (not on the approval fields any more); "May save" says "allowed on the PC" (`writes` is true with
  either tick); details wrap except a self-change's difference; a `failed` answer shows the Core's sentence alone;
  the stop answered as HTTP 400 on approve/reject (and every other route) is learned at once (`isStopRefusal`,
  `learnStop`), empties the waiting list and says "Not answered: the emergency stop was on and dropped this item.";
  the "Approved from ..." line is re-read, also when a question was running; no `location: null`, no invalid fix;
  announcements are cleaned of line breaks and invisible characters the Core refuses ("Invalid announcement.") and
  an App Shortcut "Announce to JARVIS" runs the intent by Siri or from the Shortcuts app; the devices panel says
  "This Core does not serve the device list yet." Also: every location fix (no distance filter), a reply's words no
  longer raise STOPPED (the Core's status decides), a sheet's failed first read is said in the sheet, the header
  subtitle and the device tile's line are cut instead of shrunk under 9 pt, the pairing fields and FORGET THIS
  PAIRING are 44 pt. Independent review: 0 high, 3 medium, 12 low; 14 applied as suggested, 1 (match the stop
  sentence by its start) kept as it was with the reviewer's agreement and asked of the PC; its check of the fixes
  found 1 medium and 4 low in the new phone test and the App Shortcut (applied; the App Shortcut's two questions put
  to the owner). The phone tests (scheme JARVIS-PhoneChecks): `test5_Round5WithoutApproval` (R2, R3, R6, R7,
  "remember that"), `test6_Round5Approve` / `test7_Round5Reject` (R1; they answer only a timer raised by this phone's
  own question when it is the one item waiting), `test8_Round5ReadbackAndAnnounce` (the waiting list, the notices,
  R4 through Siri), `test9_RelaunchRestoresLines` (plan check 3, three times); the owner gives Face ID only.
- **The corrected brief** (docs/MAC-BRIEF-20261010.md, the PC's file of the same day, sha256 c2ce4d2c...): while the
  stop holds, notices, devices and the other reads answer as usual (the Notices sheet no longer says otherwise);
  "Wearable service busy." means another request of this phone held its turn: every request is sent once more on
  it, a busy polling read shows nothing, a busy question puts the words back in the type box; `devices` comes with
  1.0.18 (simulated items carry `online`, kinds phone/glasses/computer/other). Checked in the same round by the same
  reviewer (four more checks; every finding applied; one medium about reading the phone's name was disproved by the
  run's own log and the code made to accept both forms anyway).
- **Round 5 checked against Core 1.0.17 on 2026-10-10** (RESULTS.md): R1 (waiting, APPROVE with Face ID three times
  by the owner's hand, the "Approved from b1: Set a timer. Result: scheduled." line, REJECT "Rejected."), R2, R3,
  R4 (notices; an announcement through Siri, "Announced by JARVIS.", "1 unread"), R6 ("not on this Core yet") met;
  R7 answered that no display is authorised on the PC; R5 skipped. App defect found and fixed: the restored
  conversation came back in one relaunch of three; now three of three.
- **Round 5c, after the PC's answers** (docs/MAC-ANSWERS-20261010.md): the announcement's words follow the Core's
  exact rule (general category C* by its Unicode 15.0 tables): characters newer than Unicode 15.0 are taken out,
  variation selectors are kept (the emoji style); checked on the Mac with thirteen sample texts (line breaks, a
  joined emoji, a Unicode 16 emoji, a tag flag, accents, skin tone, keycap, the photo marker); the stop sentence
  quoted in the code. Reviewed by the round's reviewer (nothing wrong; one low finding in older code applied: the
  phone's own stop note "JARVIS is stopped. Press RESUME on the PC to continue." now also goes when RESUME is
  pressed on the PC, round 2 check 3). Built and installed on the phone at 12:17 (install only, the app not opened).
- **Core request handled (release 1.0.17, relayed 2026-10-07):** the Core will send `assistant.draft` events for a
  phone's question while the reply is written (when the PC's "Show replies while they are written" setting is on);
  each carries the whole text so far, an empty text takes the draft away. `SessionModel.follow` keeps it as
  `writing`; the Ask screen shows it as a dashed JARVIS bubble marked "Writing…", the Overview's voice panel as its
  last line; the finished reply replaces it; only the finished reply is spoken; a failure, a cancel, a new question
  or an interruption clears it. Until 1.0.17 is installed the Core sends no drafts and the app behaves as before.
- Not possible in the app alone: replies appearing word by word. The Core keeps a device's answer whole (server.py:
  "not for another device's question") and sends it finished. A Core change, on the owner's word, to the PC session.

## Round 6, ON THE PHONE (the owner's "build round 6 with 1 to 5 and 7 to 10, and 11 and 12, I OK the Apple account change", "continue round 6, Apple account OK" and "can we also implement that I can use jarvis and no require to be in the app to use it", 2026-10-10)

**Built, reviewed and on the owner's phone since 2026-10-10 about 14:35 (commit 0a29200). Seen working by the
owner: Siri answering without the app and the widget (14:36), Share to JARVIS from Safari (14:45), a conversation
and "Hey Siri, talk to JARVIS" (by 20:04), and the app in use from the middle of Sydney, about 10 km from the PC
(replies up to about 30 s). Still to check: Look at this and a picture shared from Photos (after the camera tick on
the PC), the heads-up.** Record: ROUND6-CONVERSATION-SIRI-SHARE.md (what each item does, the project and Apple account change, the
review, the questions for the PC). In short:
- Items 1 to 10 and the new look (hands-free conversation, "Hey Siri, talk to JARVIS", Look at this, the heads-up,
  hear again / copy / share, quick asks, sharing a chat, "What can I say?").
- **11, the Home Screen widget** (in JARVISControls): Online or Stopped, approvals waiting and unread notices, read
  from the Core by the widget itself; Offline with no counts when not reached.
- **12, Share to JARVIS** (new target JARVISShare): a page (with Safari's page text), link, text or picture, a
  question, the reply in the sheet and in Chats; STOP ALL; the app's Face ID lock.
- **13, Siri without the app:** "Hey Siri, ask JARVIS" answers in place (unlocked phone, Lock with Face ID off),
  about 24 s at most, into the Ask screen's conversation; also a Shortcuts action (Back Tap).
- App Group group.com.teagueindustries.jarvis for all three targets, set up in the owner's Apple developer account
  by the signed build of about 13:42 (the App Group, its capability on the two existing App IDs, the new App ID
  com.teagueindustries.jarvis.share), as the owner OK'd. The device key moved into the App Group's keychain group at
  the first start (seen: the pairing kept, ONLINE). An older build would no longer see this pairing (rollback note).
- One independent reviewer, three passes: 1 high, 3 medium, 13 low; then 7 low/medium in the fixes; then 1; all
  applied. Found on the phone and fixed: the Ask screen was wider than the phone (the Earth picture).
- STOP ALL is now on every sheet too.

**Owner's checks still to do on the phone** (RESULTS.md, round 6): on the PC first, Settings > Devices > the phone >
tick camera; then Look at this (take or choose a photo, ask about it) and a picture shared from Photos to JARVIS;
the heads-up under the header when an approval or a notice arrives while the app is open.

## Requests for the PC (carried by the owner)

**All six answered by the PC on 2026-10-10** (docs/MAC-ANSWERS-20261010.md, kept verbatim; read from the code of
1.0.17-0d38218 and of 1.0.18 as built; no Core code changed for them):

1. The stop sentence is exactly "JARVIS is stopped (emergency stop). Nothing runs until you press RESUME on the PC."
   (the same in 1.0.16 to 1.0.18; HTTP 400 on start, transcribe, speech, announce, approvals, approve, reject and
   pair; no `stopped` field on device 400s; the only device error with "emergency stop" in it). The app's match is
   exact; nothing to change. A `stopped` field beside it is possible in a later Core release, on the owner's word.
2. "Invalid announcement.": any character of a general category C* by the Core's tables (Python 3.12.10, Unicode
   15.0.0), lengths in code points. **Done in the app on 2026-10-10:** every character newer than Unicode 15.0 is
   taken out too, and the variation selectors the Core accepts are kept (round 5c below).
3. `devices`: built for 1.0.18, which is not released (build 2 failed an intermittent Workshop test; the owner's
   "Mac mini plan", decision D0, also decides where 1.0.18 is finished). "This Core does not serve the device list
   yet." stays right until then.
4. The "07:19": a Core defect, cause found (the timer's result gives the model only a Unix timestamp); fix proposed
   on the owner's word (the alert's local clock time beside it). The 11:09 link loss: nothing on the PC explains it
   (Tailscale or the phone's network); hold-and-send covers it.
5. "Remember that": a Core defect, confirmed; fix proposed on the owner's word ("remember that / this / it / what I
   said" save the owner's own last line; only "remember what you said" saves JARVIS's reply).
6. "Wearable service busy." always comes before any work, in 1.0.17 and 1.0.18 as built: one resend can never do
   anything twice. Not covered: a request with no answer at all (the link dropped) may have been done; the app sends
   none of those again by itself (an approve again would answer `unknown`; a held question is checked against the
   conversation first; an announcement is not resent).

**New for the PC from round 6 (2026-10-10, ROUND6-CONVERSATION-SIRI-SHARE.md section 4 and RESULTS.md):**

7. "A request is already running. Stop it or wait for completion.": per device or per conversation? Siri's and
   Share's questions go into conversations of their own while the app's own question runs; if the Core allows one
   question per device at a time, they are refused with that sentence then (shown plainly on the phone).
8. "What time is it" (Siri, 14:36) was answered with the clock tool's raw reading, "Local time:
   2026-10-10T14:36:17.893246+11:00", not a sentence; Siri read it out as it is. A Core matter, like item 4.

## Open now, in order

0. **Round 6:** the copy for the PC (below, "Copies back to the PC"); then, with the camera ticked on the PC, Look at
   this and a picture shared from Photos; the heads-up when it comes.
1. ~~The restored-conversation fix on the phone~~: done 2026-10-10, three relaunches, the lines back each time.
2. **The owner's word to the PC session**, if wanted: the two Core fixes the PC proposes (a timer's reply with the
   local clock time; "remember that" saving the owner's own last line), docs/MAC-ANSWERS-20261010.md items 4 and 5.
   **The owner on the PC:** "Set a timer" back to what it was before the test (Settings > Permissions); if wanted,
   delete the two test facts on the Memory page (the round 5 phone check note, and "JARVIS said: Already logged,
   ..."); "Show replies while they are written" (Settings > AI) only if wanted.
3. **The milestone zip for the PC** after the fix is checked (see "Copies back to the PC"), with the requests above.
4. When the owner installs 1.0.18 on the PC: R6 against the real device list (the PC, this phone marked, the other
   paired devices, the test client as simulated); a Workshop mission's end arrives as an `announce` notice.
5. Still open from earlier rounds, the owner's checks on the phone, none urgent: round 2's Siri (8), the headset
   (4), the stop note after STOP ALL and RESUME on the PC (3), STOP ALL on the lock screen and no second Face ID
   within a minute (7), a muted reply staying silent (6); round 3's waveform on the Overview during a hold.
6. Not yet seen against 1.0.17: replies appearing while written (the PC's setting), the action guard's note, an
   analysis of the PC's screen (needs a display authorised in Screen Vision on the PC), R5 (needs the owner's Google
   sign-in on the PC).
7. Offered: the garage door (the owner's
   question of 2026-10-10: the opener is a Merlin Commander Extreme II, model MS127MYQ, made 07-03-2025, with myQ
   and the Merlin Wireless Beam System, seen in the owner's photos. myQ admits no outside app since 2023 and, per
   Merlin, has no HomeKit, Google or Amazon link in Australia; the way for JARVIS is a small local controller on the
   opener that the Core drives on the home network (a Security+ 2.0 bridge such as ratgdo or Konnected's GDO blaQ if
   the opener has the wired wall-button terminals, or a retrofit controller on a push-button input if it has one),
   which needs the opener's manual to decide; opening behind Ask first, so the phone asks Face ID; a Core tool, the
   PC session's work, on the owner's word). Not chosen: Dynamic Type; a Mac version.
8. TestFlight when the owner wants it (docs/phone-readmes/README.md section 4; the App Store Connect steps are the
   owner's).

## The PC side, as relayed by the owner

**2026-10-10 (the PC's brief, docs/PC-BRIEF-20261010.md):** the everyday JARVIS is 1.0.17-0d38218c4e1d since
2026-10-07 evening (VM check 29 of 29, database kept byte for byte, the phone's pairing unchanged). 1.0.18 (the
Workshop) is in its checks on the PC: no new device route or field; a Workshop mission's end arrives in `notices`
as kind `announce`. Nothing to build for it.

**Earlier (PC handoff of 2026-10-07 02:30):** the everyday JARVIS was 1.0.16 on Qwen. Release 1.0.17 was in progress: device runs stream `assistant.draft`
every 0.5 s when the PC's "Show replies while they are written" setting is on (handled here); "remember that" saves
the line before it; the action guard appends instead of replacing; JARVIS.exe and a Setup.exe (Inno Setup) with
version 4 Stage 7 scripts to come. The PC never edits the app again and receives the Mac's zips at milestones under
phone/ios/mac. Its list still showed the round 2 phone checks and the draft handling as pending on the Mac: the
draft handling is done, and all but the owner's hands-on checks are recorded here.

For the PC, outside the app: `~/Downloads/shoot-to-thrill.mp3` (160 kbps, 5:20, sha256
0c070325760299329c600edde10ea4d422ef95f57de1fe69bf68796aaa819d65) for JARVIS's music folder; playing it when JARVIS
starts is a Core matter for the PC session.

## Owner decisions of 2026-10-07

- **"Live with the PC for now":** the Core stays on the owner's PC and the phone reaches it over Tailscale; the
  phone never answers anything itself. Making the PC dependable is settings (never sleep, Tailscale unattended,
  JARVIS at sign-in). An always-on mini PC as the Core's home, or a cloud machine, are later decisions with the PC
  session. Candidate for the app: hold-and-send, a question kept on the phone while the Core is unreachable and
  sent when the link is back.
- Access to texts, calls, mail and calendar: see the conversation of 2026-10-07; a plan with the exact requests
  for the PC session is to be written after round 3 (texts via a Shortcuts automation into an "Announce" intent;
  calls by name only through Phone Link on the PC; mail through a Core connector; calendar through a device route or
  a Core connector; contacts with permission for "call X").

## Version 2 candidates (each on the owner's word)

App-only: a hands-free conversation on the phone (the owner's wish of 2026-10-10, asked of JARVIS itself: tap once,
JARVIS listens, sends at a pause, speaks the reply and listens again until "thank you Jarvis" or a tap; the round 4
hands-free listening is the start of it; offered as round 6), notifications, the Dynamic Island, text size following the phone's setting (Dynamic Type), a Siri reply
spoken by Siri itself for short answers (the Core's answers usually take longer than Siri waits). Needing the Core
(a request to the PC session): the camera ("look at this", a device route for images already exists for wearables:
`start {text, image}`, see PHONE-CORE-1.0.16.md), pairing by QR code, the PC's chats on the phone (a privacy
decision), replies appearing as written, HTTPS inside Tailscale, the Halo glasses with the phone as their bridge.

## Known Core-side defects seen from the phone (recorded on the PC, not the app's to fix)

Checked against 1.0.17 on 2026-10-10: "Remember that" no longer saves the word "that", but it saves JARVIS's last
reply instead of the owner's line (Requests for the PC, item 5: confirmed by the PC, fix proposed on the owner's
word). A timer's reply may name a wrong clock time (item 4: cause found, fix proposed on the owner's word). The action guard (it now adds its note under the
reply) was not triggered in the phone's checks, so it is neither confirmed nor ruled out. Until 1.0.17: "Remember
that" saved the word "that"; the action guard replaced a prose reply that sounded like a finished action.

## The contract and the PC

The app calls the Core's device routes exactly as docs/PHONE-CORE-1.0.16.md section 6 and docs/DEVICES.md section 3
describe them (`POST /api/device/<op>`, JSON, `X-Jarvis-Device: <id>.<key>`; 400/401/403/429 with the Core's
sentences), and since 2026-10-10 the 1.0.17 form as docs/MAC-REQUESTS-20261007.md plus docs/PC-BRIEF-20261010.md
section 2 give it. The everyday JARVIS on the PC is release 1.0.17 with the Private network switch on; the door is the
PC's Tailscale address on port 8790. Networking is the owner's.

## Records on this Mac

This folder is a local git repository since 2026-10-07 (first commit 942cc41, "Handover from the PC"; no remote,
never pushed). Result records: RESULTS.md and `records/<round>/` (reduced phone screenshots). The Mac can build,
install, launch, end and relaunch the app on the paired phone and capture its screen (`xcrun devicectl`); it cannot
tap, speak or press buttons, so those checks are the owner's. For taps and typing there is the UI test target
`JARVISUITests` (scheme `JARVIS-PhoneChecks`, file `JARVISUITests/PhoneChecksUITests.swift`): it runs on the paired
phone through `xcodebuild test`, drives the app's own controls (tabs, Voice button, type field, settings sheet),
never presses STOP ALL, and leaves full-screen screenshots in the result bundle. Its Face ID test turns the lock on
and leaves it on, so it runs only on the owner's word.

## Copies back to the PC

At each milestone: zip `JARVIS/`, `Assets.xcassets`, `STATUS.md` and the records as
`JARVIS-ios-mac-<yyyyMMdd-HHmm>.zip`, print the sha256, and the owner carries it to the PC session. The PC keeps the
copy under `phone/ios` in its repository and does not edit it.

- **Round 3 copy:** `~/Downloads/JARVIS-ios-mac-20261007-0118.zip`, sha256
  d6509e946b0f8d8d1de027da0a797dffce29a0e9dd8d9e731d6bf1a3f6785a50 (the sources, the UI tests, the project file and
  scheme, STATUS.md, RESULTS.md, ROUND3-COMMAND-LOOK.md, PC-REQUESTS-20261007.md, CLAUDE.md, records/). Made at
  commit 5e8de67.
- **Hold-and-send copy (supersedes the round 3 copy):** `~/Downloads/JARVIS-ios-mac-20261007-0135.zip`, sha256
  d9b342bb2d9fd7508dcd2a5b71664b29326d99f330beb322fdcfd978bb47f0ee, same contents at commit 23f3c30.
- **Rounds 4 and 5 copy (supersedes the earlier copies):** `~/Downloads/JARVIS-ios-mac-20261007-0227.zip`, sha256
  d19b0583428419d359e30e34386fe2ed02ce54d0a18f121203d3cab082ee3679, at commit 93162f5; now also JARVISControls/,
  JARVISShared/, Config/ and the round 4 and 5 records.
- **Round 4 checked copy (supersedes the 0227 copy):** `~/Downloads/JARVIS-ios-mac-20261007-1323.zip`, sha256
  c81165662fc4224ef6d41536842dc451476c75a9a786d8d0b5919f92f9f308e8, at commit 727fb7f; the same 52 files as the
  0227 copy, the app files byte for byte the same, only STATUS.md, RESULTS.md and ROUND4-LOCK-SCREEN-BUTTON.md
  changed (the owner's "all good" of about 13:20).
- **Round 5 checked against Core 1.0.17 (supersedes the 1323 copy):** `~/Downloads/JARVIS-ios-mac-20261010-1200.zip`,
  sha256 31b6baa3c3cfefa916e472b6808ea1e3eed1b441a4a857ad52072d713f797679, 7,275,241 bytes, 114 entries, made with
  `git archive` at commit 7e050f1: the sources with Assets.xcassets, the UI tests, the extension, Config/, the
  project file and shared scheme, STATUS.md, RESULTS.md, the round records, PC-REQUESTS-20261007.md, CLAUDE.md and
  records/ (now with round5-20261010/). For the PC: STATUS.md "Requests for the PC" items 1 to 6.
- **Round 5c copy (supersedes the 1200 copy):** `~/Downloads/JARVIS-ios-mac-20261010-1218.zip`, sha256
  f0b54583ae209cd8f779a2e14b990cfa549c3751cc6b3421a8a0ce2abc9096e6, 7,276,231 bytes, 114 entries, `git archive` at
  commit 20662d3: the same files as the 1200 copy with round 5c (the announcement rule, the stop note) and the PC's
  answers recorded in STATUS.md.

