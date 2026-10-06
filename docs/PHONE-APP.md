# JARVIS for iPhone, version 1: what was built (step 7 of docs/PHONE-PLAN.md)

Status: **BUILT ON THE MAC AND RUNNING ON THE OWNER'S IPHONE, 2026-10-06.** Written and reviewed on this PC (no
Swift compiler here; `phone/ios/README.md` is the Mac guide). The owner built it in Xcode on the Mac: Build Succeeded
at the first attempt (18:46 local), no fix round. Xcode's prompt for an Objective-C bridging header after the drag was
answered "Don't Create" (the twelve files are Swift only). Signing automatic: team Benjamin Teague, Xcode managed
profile, Apple Development certificate, bundle id `com.teagueindustries.jarvis`. Product > Run installed the app on the
owner's iPhone (iOS 26) after Xcode's one-time "Copying OS library symbols"; at 19:00 local the app opened and showed
the pairing screen as designed (`docs/phone-evidence/phone-app-first-launch-20261006-1900.png`). Not yet paired: that
needs 1.0.16 as the everyday JARVIS, Tailscale on both and the private-network switch (plan steps 5 and 6).
Owner answers of 2026-10-06: the phone runs iOS 26; the September Xcode project is not reused ("make a new one from
scratch").

## 1. Where it is

`phone/ios/JARVIS/`, thirteen Swift files since round 2 (section 7; twelve in version 1), SwiftUI, iPhone only,
iOS 18 or later (decision D4; the owner's project sets iOS 26 as the minimum). The three September
files (`Domain.swift`, `SessionModel.swift`, `MockCoreClient.swift`) are kept beside it in `phone/ios/september-2026/`
as the record of the first attempt; nothing of them is in the project (their state names and their rule "the Core
decides, the phone shows" are kept in spirit). `phone/ios/README.md` is the Mac guide; `docs/PHONE-TAILSCALE-STEPS.md`
the owner's network steps. Not part of the Windows release: a release ships nothing of the phone.

**The zip for the Mac (decision D5):** `D:\JARVIS-release-work\phone\JARVIS-ios-v1-20261006-1810.zip`, 36,285 bytes,
sha256 `62d873f13b289b61d83563859644fdf9c5ce38cc1f23269be7cad30849ced78b`: the folder `JARVIS-ios-v1/` with the
twelve files under `JARVIS/`, this README and the Tailscale steps, written by Python's zipfile (standard entries,
forward slashes; PowerShell 5.1's own zip writer uses backslashes, which a Mac unpacks into wrongly named files).
The owner moves it to the Mac by AirDrop, a USB stick or iCloud Drive; nothing is uploaded by Claude.

| File | What it is |
|---|---|
| `JARVISApp.swift` | the app, the three tabs, the pairing screen before them, the lock screen (round 2); `hello` whenever the app comes to the front |
| `Theme.swift` | the brief's colours and the shared pieces: page ground, panel with corner marks, captions, header, STOP ALL |
| `Models.swift` | the Core's answers as Swift types, named as the Core names them (`device_id`, `run_id`, `core_version`...) |
| `CoreClient.swift` | the device routes: `POST /api/device/<op>`, JSON, `X-Jarvis-Device: <id>.<key>`, the Core's sentences shown as they are |
| `Keychain.swift` | the key in the iPhone Keychain (this device only); the address, the pairing's name, the conversation in progress, the speak-replies and Face ID choices and a Siri question in transit (round 2) in the app's settings |
| `SessionModel.swift` | what the phone is doing: pair, hello, a question (start, then events with a cursor until done), the reply spoken, hold to speak, STOP, new or continued conversation, the PC's health; round 2: the lines reloaded at launch, the lock, Siri's question, the vibrations, the screen kept awake |
| `AudioRecorder.swift` | hold to speak: the microphone as 16 kHz mono 16-bit PCM, at most 30 s (the Core's format); Bluetooth headsets and a headset change mid-hold (round 2) |
| `AudioPlayer.swift` | plays the reply's sound (MP3 or WAV, whichever voice the owner uses) and waits for its end; paused and resumed around a call, ended when a headset goes (round 2) |
| `AskView.swift` | screen 1: the Core ring with the state, the readouts, the state words, the last lines, TYPE, hold-to-speak MICROPHONE, the Voice button (round 2), cancel or new chat |
| `ChatsView.swift` | screen 2: this phone's conversations (`conversations`), search, one conversation (`history`), continue it |
| `StatusView.swift` | screen 3: this phone's pairing and link, SYSTEM HEALTH (`metrics`), OVERVIEW (`overview`), settings |
| `PairingView.swift` | the pairing screen (name or address, port, the eight-digit code) and the settings sheet (speak replies, lock with Face ID, forget this pairing, about) |
| `SiriIntents.swift` | round 2: "Hey Siri, ask JARVIS" (opens the app with the question) and "Hey Siri, stop JARVIS" (the emergency stop from the background); App Intents in the app target |

## 2. How it talks to the Core (docs/PHONE-CORE-1.0.16.md section 6, followed exactly)

- **Address:** `http://<Tailscale name or address>:<port>` (8790 by default), the private-network door of 1.0.16.
  Plain HTTP inside the tunnel (decision D1 A). URLSession sends the Host header the door checks.
- **Pair:** `pair {code, capabilities: [microphone, speakers, display]}`; the `credential` goes to the Keychain
  (`kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly`), the id and name to the app's settings. Shown once, never again.
- **Hello:** `hello {capabilities}` when the app starts or comes to the front: the name, what the owner allows, the
  tick, whether the stop holds. `status` for the Status screen's round trip. Since round 2, at a launch with a
  conversation restored, `history` follows the first hello to put that conversation's lines back on the Ask screen.
- **A question:** `start {text, conversation}` with a conversation id `device-<id>-<yyyyMMdd-HHmmss>` (every
  conversation of a device starts with its id; the Core refuses any other); then `events {run_id, after}` in a loop
  (the Core waits up to ten seconds for something new) until `done`. The reply is the text of `assistant.completed`
  (the joined `assistant.delta` pieces only if no completed text came); `tool.started` shows WORKING with the tool's
  name; `run.failed` shows the Core's message; `run.cancelled` ends quietly. Cancel: `cancel {run_id}`.
- **Hold to speak:** the recording as base64 in `transcribe {data}` (0.1 to 30 s, else nothing is sent); the text
  is then sent as a question. **Spoken reply:** `speech {text}` (up to 12,000 characters) and the returned sound
  played, when "Speak replies" is on and the owner allows the speakers.
- **STOP ALL** (every screen, with a confirmation): `stop {}`. The phone shows EMERGENCY STOP and "Press RESUME on
  the PC"; it cannot resume. While the stop holds, the Core's refusals are shown as they are. Since round 2 the same
  `stop {}` goes from the lock screen (with the confirmation) and from "Hey Siri, stop JARVIS" in the background
  (Siri's own confirmation, none in the app).
- **Chats:** `conversations {}` and `history {conversation, limit: 100}`; search filters on the phone.
- **Status:** `metrics {}` every 5 seconds while the Ask or the Status screen is open (12 of the 120 calls a minute
  allowed), `overview {}` every 30 seconds; the link time is the phone's own round trip of `status`/`hello`. Since
  round 2 a reading that says the stop has lifted also clears the stop note.
- **Refusals:** 401 means revoked or lost ("pair again"): the key is removed from the phone and the pairing screen
  returns with the address kept; 403 (a capability not ticked, or not allowed) and 400 (the Core's sentence) are
  shown under the state; 429 (locked out) likewise; a connection failure reads CORE NOT REACHED with the three things
  to check (Tailscale on both, the switch on).
- **Stored on the phone:** the key (Keychain), the address, the device id and name, the conversation in progress,
  the "speak replies" choice, the "lock with Face ID" choice (round 2) and a question Siri took that the app has
  not sent yet (round 2; cleared once sent). Nothing else: the lines on screen are the Core's record, read again
  from Chats (and, since round 2, read once more at launch for the conversation in progress).

## 3. The look (the canvas N7JboAbsdEFwPFhrFFdAcs, docs/PHONE-PLAN.md section 6)

The three screens of the canvas with their header (mark, JARVIS, subtitle, the cyan rule), panels with corner marks,
upper-case captions, the ring around the Core on Ask (cyan standing by, green listening, amber thinking or working,
red stopped, still when not reached), the readouts around it, TYPE and MICROPHONE (hold) and a third button that is
"New chat" or "Cancel", the conversation list with ACTIVE on the current one and TODAY/YESTERDAY/n DAYS, the Status
cards THIS PHONE, SYSTEM HEALTH (four rings: CPU, memory, storage of the data drive, link ms) and OVERVIEW (open tasks,
projects, the reminders of the next 24 hours). Colours exactly the brief's. Differences from the canvas, all on the
"real data only" rule: no ATTACH button (the camera is version 2); the canvas's "ACTIVE SYSTEMS" and "UPCOMING" panels
are one OVERVIEW panel fed by `overview`; the readouts show only what `metrics` carries; the standard iOS tab bar in
the brief's colours instead of the drawn one. Captions are larger than the canvas's 7-8 px (readable on a phone;
touch targets 44 pt or more).

## 4. Not checked here, and the owner's checks

Not built or run on this PC (no compiler); built and run on the Mac and the phone on 2026-10-06 (the status above).
Checked on this PC: that every route, field name and refusal the app uses is what
`device_gateway.py`, `wearables/service.py`, `devices.py` and `store.py` really send and expect (read on
2026-10-06), and an independent review of the twelve files (section 5). The checks that count are the plan's section
10, run by the owner with the app on the phone and 1.0.16 on the PC; the result record will be `docs/PHONE-V1-RESULT.md`.

Known limits of version 1 (as first built; round 2 in section 7 added Siri, headsets, Face ID and more): no camera,
no notifications, no Dynamic Island, no glasses (version 2, plan section 11); the reply is not streamed (decision
D3, and the Core keeps a device's answer whole: section 7, item 10); a recording longer than 30 seconds is cut at
30; the app shows the last six lines on Ask and the whole conversation in Chats; the text sizes are fixed (no
Dynamic Type); the tab bar's colours on iOS 26's new look are to be seen on the phone.

## 5. Independent review (one reviewer, 2026-10-06): no compile error found by reading; 1 high, 5 medium, 19 low, all applied

The reviewer read the twelve files against the iOS 26 SDK with iOS 18 as the target and against the Core's code,
and found every op, field, header, status code, body and cursor exactly as the Core expects. Applied:

- **High:** a quick tap, or the system's microphone question arriving mid-hold, could leave a tap on the audio bus
  and the next hold would install a second one, which ends the app. The recorder is now armed from the hold's start
  to its end, ignores a permission answer that arrives after the finger lifted, removes any tap before installing
  one, and the permission is asked when the Ask screen first opens.
- **Medium:** the sound player's stop and finish could race across threads (the player is now on the main actor
  with the finish resumed exactly once); a cancel while the question was on its way left the run orphaned on the PC
  so the next question was refused as "already running" (the question's task now learns the run id and sends the
  cancel itself); the emergency-stop state stuck after RESUME on the PC (cleared when the Core accepts a question;
  an unrequested cancel asks the Core what holds); a refused key met by Chats or the spoken reply did not send the
  phone back to pairing (one `report` path now does); the Status screen's "Stable" and "Active connection" and
  "Path: Private network" were words the app could not back (now "Reached · N ms round trip", measured on every
  health reading, and the address).
- **Low:** the events loop pauses 300 ms between pages while pieces of a streamed answer arrive; an answer the phone
  lost the link to (switched apps, no signal) is picked up when the app returns; the transcription waits up to 130 s
  for the Core's model to load; character limits count as the Core counts; an over-long typed question is kept and
  said so; the previous reply's sound stops when a new question or hold starts; a recording is dropped when the app
  leaves the front; VoiceOver gets a start/stop action for the hold button; the pulsing ring stops when the
  recording ends; the typed field is one line so Return sends; the Keychain write replaces an item it cannot update
  and the failure wording says to start the pairing again on the PC; "speak replies" is kept across launches; touch
  targets are 44 pt and no caption is under 9 pt; the conversations count uses the Core's own count when known;
  STOP ALL is also on the conversation screen; the iOS settings path and a button label corrected; the pairing
  footer says what is stored; the README marks the three build settings as required and names two things to look
  at on the phone.

## 6. The look applied (2026-10-06, the owner's "apply the look")

**What the owner supplied:** a zip `TeagueJARVIS-iOS.zip` (668,502 bytes, sha256 31906f3c982b92145d4d7d88c1d80c45c837b31b8055fa9ae09377f0d6dd9337)
holding a SwiftUI mock-up of our pairing screen made elsewhere from a picture of it: four Swift files (an app entry,
a theme, a spinning orbital graphic, a pairing view with our words copied and a PAIR button that only sets a flag) and
two pictures (the Teague Industries badge as a JPEG, a space-station scene with the Earth horizon). Its own README says
the pairing is UI-only and the Core connection, the credential and the Keychain are still to do. Applied as it was it
would have replaced the working app with one screen that cannot pair; reported to the owner, who chose the look only.
The supplied Swift files and README are kept as the design record in `docs/design/teague-ios-mock-20261006/`.

**What was taken (three things, all looks), built into our files, nothing underneath changed:**

1. The badge as the logo of every header (`JarvisMark` in `Theme.swift`): image set `TeagueBadge` in a cyan ring, 40 pt;
   the drawn T mark stands in when the image set is missing. The asset is `phone/ios/assets/TeagueBadge.png` (512 px,
   made from the owner's badge, sha256 0b205466fbad2a193c3b49c8b6899ad0edfb28bf4861dfb2e1bb2c1e3f2f95a5).
2. The space scene faint behind every screen (`PageBackground` in `Theme.swift`): image set `JARVISBackground` at
   12 percent under a vertical shade and the canvas's radial glow, so the text stays readable; the plain ground when
   the image set is missing. The asset is `phone/ios/assets/JARVISBackground.jpeg` (1536 x 864, the owner's file
   unchanged, sha256 190ff1c27c01c9124fe1964b215a6160630dcf13262ec5d7eeb974ce8eb98bf1).
3. A slowly turning orbital graphic on the pairing screen (`OrbitalGraphic` in `PairingView.swift`) in place of the
   still Core rings: built like the Ask screen's `CoreRing` (a `TimelineView`), in the brief's colours, still when the
   system's Reduce Motion is on. The Ask screen's state ring is unchanged.

Not taken: the mock's frosted-glass panels (the canvas's panels with corner marks stay), its progress bar, its app
entry and its pairing logic. The image sets are added by hand in Xcode's asset catalog on the Mac (`phone/ios/
README-look.md`); the app compiles and runs with or without them. A draft picture of the result was rendered on this
PC from an HTML mock (Edge via Playwright, 393 x 852 at 3x) and sent to the owner before the Swift was written; the
app's own look is to be seen on the phone.

**Independent review (one reviewer, 2026-10-06):** no compile error found by reading (every API already used in the
compiled files; `UIImage` reachable through SwiftUI on iOS; the `let t` arithmetic is `Double`; the overlay-and-clip
background cannot grow any layout; Reduce Motion handled); no high or medium finding; four low: (1) the core's glow
kept CoreRing's radius and was cut off in the smaller graphic, applied (end radius 40); (2) the background image was
not guarded like the badge and would log once per evaluation without its image set, applied (the same `UIImage(named:)`
guard); (3) the TimelineView ticks at 30 fps while the pairing screen exists, even with the graphic scrolled away,
accepted for a one-time screen that the app replaces once paired; (4) a non-square badge asset would overflow the
circle, noted, the shipped asset is square.

**Seen on the phone (2026-10-06, 21:12 local, the owner's screenshot `docs/phone-evidence/phone-app-look-20261006-2112.png`):**
built on the Mac at the first attempt after the two image sets and the AppIcon were added to the asset catalog by hand
(the first drag put the files into the file list instead, giving `PairingView 2` and `Theme 2` beside the old files
and the pictures as loose files; fixed by deleting the old Swift files and the loose pictures and dragging the pictures
into the Assets column; the "2" in the file names is harmless). The pairing screen shows the badge in a ring in the
header, the space scene faint behind the screen and the orbital graphic, as the draft picture showed. The home-screen
icon still showed iOS's placeholder grid right after the run: iOS keeps the icon of an app already installed; the owner
was told to delete the app from the phone and run it again from Xcode.

**Not checked here:** no compiler on this PC (as section 4). The owner builds the changed files on the Mac; the zip for
the Mac is named in `docs/CURRENT-STATUS.md`.

## 7. Round 2 (2026-10-06, late evening; the owner's "let's make some big moves on the app")

Status: **WRITTEN AND INDEPENDENTLY REVIEWED ON THIS PC, NOT YET BUILT ON THE MAC.** The zip for the Mac and the
owner's steps are named in `docs/CURRENT-STATUS.md` and `phone/ios/README-round2.md` (thirteen Swift files, twelve
replaced and one new, plus the icon's catalog folder). The agreed list came from the 22:55 handover (the four fixes of
`docs/PHONE-V1-RESULT.md` plus six additions); every item is below, including the one that could not be done.

1. **The conversation after a relaunch (check 3):** at the first hello after a launch with a restored conversation
   id, `SessionModel.reloadLines` reads the lines with `history {conversation, limit: 100}` (the route Chats uses)
   and keeps the last 80 on the Ask screen. Skipped when a question was typed before that hello (those earlier lines
   are then in Chats); not done after New chat, Continue or a new pairing, which set their own lines.
2. **The header at the phone's width:** `ScreenHeader` (Theme.swift) gives the right-hand items their full size
   (`fixedSize`, layout priority 1) and lets the subtitle shrink to three quarters and then truncate; "JARVIS" stays on
   one line; the Ask header's trailing spacing is 8 pt. The longest content (NOT REACHED, STOPPED, the menu icon)
   fits a 393 pt phone.
3. **The stale stop note:** the `stopped` property's observer clears a notice that mentions the emergency stop when
   a later hello, status or metrics reading says the stop has lifted.
4. **The icon:** the files are right (1024 x 1024 RGB, no transparency, the badge); what is left is on the Mac:
   README-round2 section 3 (the AppIcon slot filled, the target's App Icon set to AppIcon, Clean Build Folder, the app
   deleted from the phone before the run).
5. **Bluetooth headsets and interruptions:** the recorder and the player set the audio session with
   `allowBluetoothHFP` (named `allowBluetooth` before the iOS 26 SDK; `#if compiler(>=6.2)` picks the name the
   compiler knows) and `allowBluetoothA2DP`. With both set, iOS keeps a headset that has both profiles on HFP while it is
   connected (its microphone works; the reply is at call quality there, not stereo); headphones with A2DP only get
   stereo and the phone's own microphone records. `allowBluetoothHFP` is available from iOS 26, the project's
   minimum (review note: the compiler gate would not make the file build for an iOS 18 target). A headset
   coming or going mid-hold ends the hold with a sentence (`AVAudioEngineConfigurationChange`); a call or another
   app's sound ends a recording with a sentence and pauses the reply, which goes on when iOS says it may and ends
   otherwise; a headset that goes away ends the reply (nothing plays on from the speaker unasked).
6. **The screen stays awake** (`isIdleTimerDisabled`) while JARVIS listens, thinks, works or speaks; the phone's own
   timer otherwise.
7. **Face ID on open:** "Lock with Face ID" in the settings sheet, off until the owner turns it on; Face ID with the
   passcode as the fallback (`LAContext`, `.deviceOwnerAuthentication`); locked at every launch and after more than a
   minute in the background; the lock screen has UNLOCK and STOP ALL (the stop works without unlocking); a phone with
   neither Face ID nor a passcode turns the switch off again and says so. The Info entry
   `NSFaceIDUsageDescription` is the owner's Xcode step (README-round2 section 2) and the switch's own warning says so.
8. **The Voice button and the vibration:** a fourth round button on the Ask screen mutes or unmutes the spoken reply
   (the same setting as the sheet's switch); a short success vibration when a reply arrives, an error one when the
   Core says the request failed, a warning one when the emergency stop is raised, and a light impact when a hold
   takes.
9. **Siri** (`SiriIntents.swift`, App Intents in the app target): `AskJarvisIntent` opens the app with the question
   Siri took ("What should I ask JARVIS?"), stored in the app's settings and posted as a notification; the app sends
   it as if typed once it is in front and unlocked, interrupting a question in progress; unpaired, Siri says to pair
   first. `StopJarvisIntent` raises the emergency stop through the Core's `stop` route without opening the app and
   repeats the Core's sentence on a refusal. `JarvisShortcuts` registers the phrases "Ask JARVIS", "Ask JARVIS a
   question", "Talk to JARVIS", "Stop JARVIS", "JARVIS emergency stop", "Stop everything on JARVIS". Siri says only
   "Asking JARVIS."; the reply is the app's, in JARVIS's voice, because the Core's answers take longer than Siri
   waits for a spoken reply.
10. **Replies appearing as they are written: NOT DONE, and not possible in the app alone.** `server.py` decides
    streaming with `not getattr(run, 'wearable', False)` ("Not for another device's question (its client waits for
    the finished reply)"), and the pieces of a streamed answer go to the PC window's drafts, not into the run's
    events that the device route serves. The 22:55 handover's note that the Core sends `assistant.delta` to the phone
    when the PC's streaming setting is on was wrong: the phone gets one `assistant.delta` with the checked answer. A
    Core change (serve a device run's draft with `events`) is a candidate for a Core release on the owner's word.

Independent review (one reviewer, 2026-10-06 late evening): section 8, every finding applied.

Not checked here: no compiler on this PC; the owner builds on the Mac and runs the eight checks of README-round2
section 5; check 3 of the plan is then run again and `docs/PHONE-V1-RESULT.md` closed.

## 8. Independent review of round 2 (one reviewer, 2026-10-06 late evening): no compile error by reading; 1 high, 2 medium, 7 low, all applied

The reviewer read the thirteen files against the iOS 26 SDK (Swift 5 mode, nonisolated default, iOS 26 minimum) and
against `device_gateway.py` and `wearables/service.py`, and found every op, body, header and status code as the Core
serves them (the one new call, `history` from the Ask screen, is the route Chats used already) and the stop sentences
the app matches on real (`permissions.STOPPED_MESSAGE`, server.py's "Emergency stop is on"). Applied:

- **High:** the lock re-prompted on every inactive-to-active cycle of the scene (the control centre, a call banner,
  the Siri overlay, and the Face ID sheet itself), so "Not now" prompted again at once and the lock screen's STOP ALL
  could never be tapped; after a successful Face ID a second prompt could follow. Now only a stay in the background
  of more than a minute locks again, and the prompt comes from the lock screen alone (on appear and from UNLOCK).
- **Medium:** a Siri question was kept with no age and sent only after a successful hello, so with the Core
  unreachable it would have gone out hours later into whatever conversation was open; now it is sent at once,
  reached or not (the "cannot be reached" sentence shows under it), and one older than two minutes is dropped with a
  sentence. The "no passcode, so the lock is off" sentence was wiped by the next hello; a hello now clears only a
  failure's sentence.
- **Low:** nothing is spoken over the lock screen and a lost answer is picked up only once unlocked; the recorder's
  configuration-change handler runs on the main queue, where `stop()` also talks to the engine (not thread-safe);
  "JARVIS" in the header may shrink to 85 percent before truncating and the Status header's spacing now matches
  Ask's, so the longest trailing content fits; muting with the Voice button mid-reply stops the sound; the User-Agent
  says 1.1 and the pairing footer names the two new stored items; the headset wording corrected (section 7, item 5);
  sections 1 and 2 brought up to date. Noted, no change: an interruption whose end never arrives leaves the state at
  SPEAKING until the next action (nothing is blocked).

**The zip for the Mac:** `D:\JARVIS-release-work\phone\JARVIS-ios-round2-20261006-2354.zip` (957,413 bytes, sha256
d6ba967120f84d01fdcb7e3c463c0e798e255ee394f03ae9174acece1877ac77), sent to the owner in the chat. The 23:45 zip
(`JARVIS-ios-round2-20261006-2345.zip`, sha256 b8ba29eb…) went out before the review at the owner's request and is
superseded. The owner, on Claude Code on the Mac, was given a paste-ready brief for that session: verify the hash,
delete the "Theme 2" and "PairingView 2" copies of the look round, place the thirteen files and the icon folder, add
`INFOPLIST_KEY_NSFaceIDUsageDescription` beside the microphone key, `xcodebuild` for a device, then Xcode and
Command-R; errors come back here.
