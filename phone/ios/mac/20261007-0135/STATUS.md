# JARVIS iPhone app: status (the Mac's living record)

**Read this first in every session in this folder; update it before a session ends.**
Last updated: 2026-10-07, 00:25 local (round 2 installed on the phone from the Mac; checks begun, RESULTS.md).

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
  screen. **Open:** the six checks that need the owner's hands (stop note after RESUME, headset, screen awake, Voice
  button and vibration, Face ID, Siri) and the header on Chats and Status; RESULTS.md section 3 lists the steps.
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
  1.2. Left for the owner's eyes: the waveform and the green orb during a hold, the amber orb while JARVIS thinks,
  the sparklines filling over minutes. A footer case fix is in code for the next install.
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
- **Core request handled (release 1.0.17, relayed 2026-10-07):** the Core will send `assistant.draft` events for a
  phone's question while the reply is written (when the PC's "Show replies while they are written" setting is on);
  each carries the whole text so far, an empty text takes the draft away. `SessionModel.follow` keeps it as
  `writing`; the Ask screen shows it as a dashed JARVIS bubble marked "Writing…", the Overview's voice panel as its
  last line; the finished reply replaces it; only the finished reply is spoken; a failure, a cancel, a new question
  or an interruption clears it. Until 1.0.17 is installed the Core sends no drafts and the app behaves as before.
- Not possible in the app alone: replies appearing word by word. The Core keeps a device's answer whole (server.py:
  "not for another device's question") and sends it finished. A Core change, on the owner's word, to the PC session.

## Open now, in order

1. The owner's remaining checks on the phone: from round 2, the stop note after RESUME (3), the headset (4), the
   screen awake (5), the vibration (6), Face ID with their own face (7), Siri (8); from round 3, the hold on the
   Overview (waveform, green orb), the amber orb while thinking. The owner reports what passed; RESULTS.md is
   completed from that. (The header on every screen, the Voice button, the icon, the relaunch, the whole Overview
   and hold-and-send are seen or confirmed and recorded.)
1b. Next app-only rounds offered to the owner, each on their word: a JARVIS button on the lock screen and in
   Control Center (iOS Controls, a widget extension target) as the nearest thing to the side button; text size
   following the phone's setting (Dynamic Type).
2. The plan for the PC session, one document: the access requests (texts via an Announce intent and a Shortcuts
   automation, calls by name through Phone Link on the PC, mail and calendar through the Core, contacts), JARVIS's
   own wishlist of 2026-10-07 01:09 (approve from the pocket with a per-device "may approve" tick, time-aware
   nudges, memory with a version stamp), the device list for the Overview, and the always-on box as a later option.
3. Any defect found: fix here, one reviewer, rebuild, record; a copy back to the PC at each milestone (the round 3
   copy: see "Copies back to the PC").
4. TestFlight when the owner wants it (README.md section 4; the App Store Connect steps are the owner's).

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

App-only: notifications, the Dynamic Island, text size following the phone's setting (Dynamic Type), a Siri reply
spoken by Siri itself for short answers (the Core's answers usually take longer than Siri waits). Needing the Core
(a request to the PC session): the camera ("look at this", a device route for images already exists for wearables:
`start {text, image}`, see PHONE-CORE-1.0.16.md), pairing by QR code, the PC's chats on the phone (a privacy
decision), replies appearing as written, HTTPS inside Tailscale, the Halo glasses with the phone as their bridge.

## Known Core-side defects seen from the phone (recorded on the PC, not the app's to fix)

"Remember that" saves the word "that" (the exact memory command does not resolve "that"); the action guard replaces a
prose reply that sounds like a finished action ("No matching action result was recorded ..."). Asking again in other
words usually works.

## The contract and the PC

The app calls the Core's device routes exactly as docs/PHONE-CORE-1.0.16.md section 6 and docs/DEVICES.md section 3
describe them (`POST /api/device/<op>`, JSON, `X-Jarvis-Device: <id>.<key>`; 400/401/403/429 with the Core's
sentences). The everyday JARVIS on the PC is release 1.0.16 with the Private network switch on; the door is the PC's
Tailscale address on port 8790. Networking is the owner's.

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
