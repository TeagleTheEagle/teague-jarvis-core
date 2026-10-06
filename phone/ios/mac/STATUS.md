# JARVIS iPhone app: status (the Mac's living record)

**Read this first in every session in this folder; update it before a session ends.**
Last updated: 2026-10-07 (the handover from the PC; owner decision "app on the mac").

## Where the app stands

- **Version 1** (2026-10-06): built in Xcode at the first attempt, paired to the Core over Tailscale, 9 of the 10
  plan checks met (docs/PHONE-V1-RESULT.md). The look of 2026-10-06 applied (badge logo, space scene, orbital
  graphic).
- **Round 2** (written on the PC on 2026-10-06 late evening, placed here on 2026-10-07 from
  `JARVIS-ios-round2-20261006-2354.zip`, sha256 d6ba967120f84d01fdcb7e3c463c0e798e255ee394f03ae9174acece1877ac77):
  thirteen Swift files (`SiriIntents.swift` new); compiled here with a compile-only build (signing off); project
  settings changed by the Mac session: App Icon set to `AppIcon` in Debug and Release (it was empty, which is why the
  icon stayed the placeholder), `INFOPLIST_KEY_NSFaceIDUsageDescription` added beside the microphone key; the
  "Theme 2" and "PairingView 2" copies removed. **Not yet run on the phone:** the eight checks of
  `README-round2.md` section 5 and plan check 3 are open.
- What round 2 brings: the conversation's lines reloaded after a relaunch; the header at the phone's width; the stale
  stop note cleared; Bluetooth headsets and audio interruptions; the screen awake while listening, thinking, working
  or speaking; "Lock with Face ID" (off by default; STOP ALL on the lock screen); the Voice button with a vibration on
  the reply; Siri ("Hey Siri, ask JARVIS" opens the app with the question; "Hey Siri, stop JARVIS" raises the stop
  from the background). Independent review: docs/PHONE-APP.md section 8, every finding applied in these files.
- Not possible in the app alone: replies appearing word by word. The Core keeps a device's answer whole (server.py:
  "not for another device's question") and sends it finished. A Core change, on the owner's word, to the PC session.

## Open now, in order

1. Command-R on the phone (delete the old app first for the icon); the eight checks of README-round2.md section 5;
   plan check 3 (close and reopen mid-conversation). Record the results in RESULTS.md here (one table, what was seen,
   with the owner's screenshots named).
2. Any defect found: fix here, one reviewer, rebuild, record; a copy back to the PC at the end of the round.
3. TestFlight when the owner wants it (README.md section 4; the App Store Connect steps are the owner's).

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

## Copies back to the PC

At each milestone: zip `JARVIS/`, `Assets.xcassets`, `STATUS.md` and the records as
`JARVIS-ios-mac-<yyyyMMdd-HHmm>.zip`, print the sha256, and the owner carries it to the PC session. The PC keeps the
copy under `phone/ios` in its repository and does not edit it.
