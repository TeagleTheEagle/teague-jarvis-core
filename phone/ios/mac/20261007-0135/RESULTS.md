# JARVIS for iPhone, round 2: the result record (STATUS.md open item 1)

Status: **ROUND 2 ON THE PHONE, 2026-10-07, 00:14 to 00:19 local: installed from the Mac; three of the nine checks
met and seen; six await the owner's hands** (sections 1 and 2). Everything in section 1 was done and seen from the
Mac session over the Mac-to-phone link (Apple's `devicectl`): a signed build, the install, the launch, the close and
reopen, and three screenshots of the phone's own screen. Nothing in section 2 is claimed: those checks need a finger
on the phone, a headset, Siri, or the RESUME button on the PC.

## 1. What was done and seen from the Mac

| Step | What | Seen |
|---|---|---|
| Sources | The thirteen Swift files from `JARVIS-ios-round2-20261006-2354.zip` (sha256 d6ba9671…ac77) in `JARVIS/`; every file equal to the PC's `sources-sha256.txt` | hash check, 13 of 13 ok |
| Project | App Icon set to `AppIcon` in Debug and Release (it was empty); `INFOPLIST_KEY_NSFaceIDUsageDescription` added beside the microphone key; "Theme 2.swift" and "PairingView 2.swift" removed | `project.pbxproj` diff: four lines |
| Compile check | `xcodebuild`, generic iOS device, signing off: BUILD SUCCEEDED, 0 errors, 4 warnings of one kind (Swift 6 concurrency notes at AudioPlayer.swift:20 and :24, SessionModel.swift:448 and :584; harmless in Swift 5 mode) | build log |
| Signed build | the same with `-allowProvisioningUpdates`: "Apple Development: Benjamin Teague", team Y89NN5A4T6, profile "iOS Team Provisioning Profile: *"; no keychain prompt | build log, `codesign -dv` |
| Built app | `CFBundleIconName = AppIcon`, the icon files in the bundle, `NSFaceIDUsageDescription` and `NSMicrophoneUsageDescription` in Info.plist, `Metadata.appintents` present (Siri), MinimumOSVersion 26.6 | `plutil -p` on the built Info.plist |
| Install | `devicectl device install app` on the paired iPhone 15 ("iphone 5 se", UDID 00008120-001824523CF1A01E), over the existing app, no deletion; then `process launch`; the process stayed alive | process list on the phone |
| Ask screen after install | ONLINE, Core `1.0.16-fccde24e2cc6`, AI READY, CPU 12 %, LINK 28 ms, MEMORY 28 %, STOP CLEAR, STANDING BY; a conversation of two lines on screen; the TYPE, MICROPHONE, VOICE ON and NEW CHAT buttons | `records/round2-20261007/01-ask-after-install.jpg` (phone clock 00:17) |
| Close and reopen | the process ended from the Mac (the same as swiping the app away), a new process launched, seven seconds later the screenshot | `02-ask-after-relaunch.jpg` (phone clock 00:18) |
| Home screen | the app closed again and the home screen captured, then the app relaunched | `03-home-screen-icon.jpg` (cropped to the icon rows) |

## 1b. The automated run from the Mac (2026-10-07, 00:45 to 00:47, `JARVISUITests`, the owner at the phone)

A UI test target drove the app on the phone (STATUS.md, "Records on this Mac"); the result bundle's screenshots
are the record (`records/round2-20261007/run-*.jpg`). Two earlier starts failed before any test: iOS asks on the
phone, with Face ID, whether a test runner may automate it, and cancelled when the phone was in another app. With
Settings > Developer > Enable UI Automation on, the run went through.

**During the whole run the Core was not reached from the phone** (every screen read NOT REACHED and "JARVIS
cannot be reached"), although the same phone had been ONLINE with Core 1.0.16 at 00:17 and 00:29. The cause is not
visible from the Mac (Tailscale on the phone or the PC, or JARVIS on the PC). So:

| What ran | Seen | Verdict |
|---|---|---|
| Header on Ask, Chats, Status | STOP ALL 105 pt wide and readable on all three; the state word NOT REACHED on one line (82 x 11 pt); **the title cut to "JA…"** beside that longer word on Ask and Status | layout holds for STOP ALL; a defect: the long word costs the title its room. Fixed in round 3: the header word is "Offline" (short, like "Online"), the sentence stays under the core |
| Voice button | VOICE ON became MUTED on a tap and VOICE ON again on the next | **PASS** (the button half of check 6) |
| A typed question | the type bar opened, the text was typed and sent, the question appeared as a line, then the not-reached sentence; no reply (Core not reached) | not a check of the app's answering; the test now fails plainly when the Core is not reached |
| Face ID lock | the switch was already ON (turned on by the owner); after the relaunch the system's Face ID prompt blocks automation ("Not authorized for performing UI testing actions") | the lock screen cannot be driven from the Mac; the owner's own eyes (check 7) |

## 2. The checks of README-round2.md section 5 and plan check 3

| # | Check | Result | What was seen, or what is needed |
|---|---|---|---|
| 1 | Plan check 3: the same conversation with its lines after the app is closed fully and reopened | **PASS** | `02-ask-after-relaunch.jpg` shows the same two lines as `01-ask-after-install.jpg` ("Hey Jarvis, do you think I would have time to do school work…" and the reply) after a true process end and relaunch |
| 2 | The header: ONLINE on one line, STOP ALL readable | **PASS on the Ask screen** | both Ask screenshots: ONLINE on one line with its green dot, STOP ALL in full in its red button, the menu button beside it. The subtitle reads "ONE CORE // P…": it is cut on purpose (Theme.swift, so ONLINE and STOP ALL keep their room). Chats and Status not seen from the Mac: the owner looks once |
| 3 | The stop note clears by itself after STOP ALL on the phone and RESUME on the PC | **OWNER** | needs STOP ALL pressed on the phone (it raises the emergency stop on the Core) and RESUME on the PC; the Mac cannot tap the phone and must not raise the stop |
| 4 | Headset: speak and hear the reply through a Bluetooth headset | **OWNER** | needs the headset and a spoken question |
| 5 | Screen awake while JARVIS thinks or speaks | **OWNER** | needs a question and a watch on the screen |
| 6 | Voice button mutes and unmutes the spoken reply; a short vibration when a reply arrives | **OWNER** (the button exists) | the VOICE ON button is beside the microphone in both Ask screenshots; its effect and the vibration need a hand on the phone |
| 7 | Face ID: "Lock with Face ID" on, close and reopen, Face ID then the screens; STOP ALL on the lock screen; nothing asked within a minute | **OWNER** | the Face ID Info entry is in the installed app (section 1), so the first Face ID prompt will not end the app; the switch is in the app's menu (the three-line button) on Ask or Status |
| 8 | Siri: "Hey Siri, ask JARVIS" and "Hey Siri, stop JARVIS" after a minute | **OWNER** | the Siri metadata is in the installed app (section 1); the phrases need a voice |
| icon | The badge on the home screen instead of the placeholder grid | **PASS** | `03-home-screen-icon.jpg`: JARVIS with the Teague Industries badge, second row; no delete of the old app was needed |

## 3. What the owner does next (on the phone, then one word here)

Open JARVIS on the phone. Then, in this order, and tell this chat which numbers passed:

1. Swipe to Chats and to Status: ONLINE on one line and STOP ALL readable on both (check 2, the rest of it).
2. STOP ALL on the phone; RESUME on the PC; the yellow line goes away within seconds (check 3).
3. With a Bluetooth headset connected, hold the microphone and ask something; the reply plays in the headset (check 4).
4. Watch the screen while JARVIS thinks and speaks: it does not dim (check 5).
5. Tap the speaker button: it reads VOICE OFF and the next reply is silent; tap again for VOICE ON; feel the short
   vibration when a reply arrives (check 6).
6. Menu button (three lines) on Ask or Status: turn "Lock with Face ID" on. Close the app, open it: Face ID, then the
   screens. STOP ALL is on the lock screen. Come back within a minute: nothing asked (check 7).
7. Wait a minute, then "Hey Siri, ask JARVIS", say a question; the app opens and answers. "Hey Siri, stop JARVIS"
   raises the stop; RESUME on the PC (check 8). If Siri does not know the phrase, open the Shortcuts app and run one
   of the two JARVIS shortcuts once.

## 4. Not in this round, said plainly

Replies appearing word by word need a Core change (STATUS.md). The six owner checks above are the only open items of
round 2; a defect found in any of them is fixed here (STATUS.md open item 2).

# Round 3, the command look: the result record (ROUND3-COMMAND-LOOK.md section 4)

Status: **ROUND 3 ON THE PHONE, 2026-10-07, 01:12 to 01:15 local: built, reviewed (2 high, 3 medium, 12 low, all
applied), installed from the Mac, and seen on the phone with the Core ONLINE.** App version 1.2 against Core
1.0.16-fccde24e2cc6. Records: `records/round3-20261007/`.

| What | Seen | Verdict |
|---|---|---|
| Header on Ask, Chats, Overview (UI test, two runs) | title JARVIS 64 pt wide on all three; ONLINE 44 x 11 pt (one line); STOP ALL 88 x 44 pt | **PASS** (the round 2 defect of the cut title is gone) |
| Ask | the orb (petals, arcs, ticks, crosshair, glowing nucleus) with the six real readouts around it: Core 1.0.16-fccde24e2cc6, AI READY, CPU 4 %, LINK 37 ms, MEMORY 28 %, STOP CLEAR; the conversation under it; tab bar Ask / Chats / Overview | `01-ask-orb.jpg` |
| Overview, top | strip: TEAGUE INDUSTRIES, the motto, the real clock 01:14 and WED, 7 OCT; JARVIS CORE panel: CORE ONLINE, the orb, "Core 1.0.16-fccde24e2cc6 · UP 2 H 9 MIN"; SYSTEM STATUS: ALL SYSTEMS NOMINAL, six rows, ring 6/6 | `02-overview-top.jpg` |
| Overview, middle | LIVE DIAGNOSTICS: four tiles with sparklines (STORAGE 92 % in red, LINK 36 ms), LAST REPLY 20.4 S, the note naming what is and is not measured; ACTIVE PROJECTS: 3 ACTIVE · 4 OPEN TASKS, Business, PHYSICS & JARVIS, Project Jarvis, each "none open" (the four open tasks are not linked to a project, as the Core reports); UPCOMING: NOTHING IN 24 H | `04-overview-middle.jpg` |
| Overview, bottom | THIS PHONE: Reached · 28 ms round trip, thegrizzlybear:8790, paired as b1, questions and reading only, device f51d…b9fe; footer TEAGUE INDUSTRIES OS · JARVIS for iPhone 1.2 · Core 1.0.16-…; the fixed VOICE INPUT panel: STANDING BY, the hold button, the flat baseline, "Hold to speak.", the conversation's last line | `05-overview-bottom.jpg` |
| Chats | unchanged apart from the header word rule | `03-chats.jpg` |

Not seen on the phone yet, for the owner: the waveform moving during a hold and the orb going green and widening with
the voice; the orb amber while JARVIS thinks; the sparklines filling over a few minutes on the Overview; the reply
being written (needs Core 1.0.17 with the PC's setting on). Noted after the run: the footer upper-cased the release
id (a caption); fixed in code for the next install.

# Hold-and-send: the result record (STATUS.md, "Hold-and-send")

Status: **CHECKED BY THE OWNER ON THE PHONE, 2026-10-07, about 01:35 local: "it worked".** Build 1.2 with
hold-and-send (commit ca3aeea, installed from the Mac at 01:32). The owner's steps were: JARVIS open, Tailscale off
on the phone, a question made (the amber "Held until the Core is back" box with DROP, the header OFFLINE), Tailscale
on again, the question sent by itself and answered. Recorded on the owner's word; no screenshot was asked for.
Independent review before the install: 0 high, 5 medium, 6 low, all applied (STATUS.md has the list).

## 5. Not in round 3, said plainly

The device ecosystem, the global network map and the GPU, temperature, power, network and AI-load tiles of the
owner's picture (ROUND3-COMMAND-LOOK.md section 3): no such data reaches a phone from the Core. The device list is a
fair request to the PC session.
