# JARVIS for iPhone, round 2: the result record (STATUS.md open item 1)

Status: **ROUND 2 ON THE PHONE, 2026-10-07, 00:14 to 00:19 local: installed from the Mac; three of the nine checks
met and seen; six await the owner's hands** (sections 1 and 2). Everything in section 1 was done and seen from the
Mac session over the Mac-to-phone link (Apple's `devicectl`): a signed build, the install, the launch, the close and
reopen, and three screenshots of the phone's own screen. Nothing in section 2 is claimed: those checks need a finger
on the phone, a headset, Siri, or the RESUME button on the PC. Since then, on the owner's word (2026-10-07 about
13:20, through the round 4 button): check 5 met, checks 6 and 7 in part (section 2).

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
| 5 | Screen awake while JARVIS thinks or speaks | **PASS** (owner, about 13:20) | the screen stayed on while listening, thinking and speaking, for a question asked through the button (Round 4 below) |
| 6 | Voice button mutes and unmutes the spoken reply; a short vibration when a reply arrives | **PASS in part** | the button turns VOICE ON to MUTED and back (UI test, section 1b); the short vibration on a reply felt by the owner (about 13:20, Round 4 below); a muted reply staying silent not yet reported |
| 7 | Face ID: "Lock with Face ID" on, close and reopen, Face ID then the screens; STOP ALL on the lock screen; nothing asked within a minute | **PASS in part** | the lock is on (turned on by the owner); Face ID with the owner's face, then the screens, when the button opened the app (about 13:20, Round 4 below); STOP ALL on the lock screen and no second ask within a minute not yet reported |
| 8 | Siri: "Hey Siri, ask JARVIS" and "Hey Siri, stop JARVIS" after a minute | **OWNER** | the Siri metadata is in the installed app (section 1); the phrases need a voice |
| icon | The badge on the home screen instead of the placeholder grid | **PASS** | `03-home-screen-icon.jpg`: JARVIS with the Teague Industries badge, second row; no delete of the old app was needed |

## 3. What the owner does next (on the phone, then one word here)

Open JARVIS on the phone. Then, in this order, and tell this chat which numbers passed (step 4 and parts of steps 5
and 6 are met since 2026-10-07 about 13:20; STATUS.md lists what is still open):

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

Not seen on the phone yet, for the owner: the waveform moving during a hold on the Overview, and the orb widening
with the voice; the sparklines filling over a few minutes on the Overview; the reply being written (needs Core
1.0.17 with the PC's setting on). Seen since, on the owner's word: the orb green while listening and amber while
JARVIS thinks (2026-10-07 about 13:20, through the button; Round 4 below). Noted after the run: the footer
upper-cased the release id (a caption); fixed in code for the next install.

## 5. Not in round 3, said plainly

The device ecosystem, the global network map and the GPU, temperature, power, network and AI-load tiles of the
owner's picture (ROUND3-COMMAND-LOOK.md section 3): no such data reaches a phone from the Core. The device list is a
fair request to the PC session.

# Hold-and-send: the result record (STATUS.md, "Hold-and-send")

Status: **CHECKED BY THE OWNER ON THE PHONE, 2026-10-07, about 01:35 local: "it worked".** Build 1.2 with
hold-and-send (commit ca3aeea, installed from the Mac at 01:32). The owner's steps were: JARVIS open, Tailscale off
on the phone, a question made (the amber "Held until the Core is back" box with DROP, the header OFFLINE), Tailscale
on again, the question sent by itself and answered. Recorded on the owner's word; no screenshot was asked for.
Independent review before the install: 0 high, 5 medium, 6 low, all applied (STATUS.md has the list).

# Round 4, the JARVIS button: the result record (ROUND4-LOCK-SCREEN-BUTTON.md)

Status: **CHECKED BY THE OWNER ON THE PHONE, END TO END, 2026-10-07 about 13:20 local: "all good".** Build 1.2 as
installed from the Mac at 02:30 (the round 5 fixes; no app file has changed since). Recorded on the owner's word; no
screenshot was asked for.

| When | What the owner did and saw | Verdict |
|---|---|---|
| 02:31 | the "Ask JARVIS" control pressed in Control Center: the app opened ("yes it did") | **PASS** (the first design, the control opening a link, had done nothing; the fallback with `openAppWhenRun` is the design) |
| about 13:20 | the control pressed again; Face ID; on Ask the orb green with LISTENING; a question spoken, then a pause; the orb amber with THINKING; the reply spoken with a short vibration; the screen on throughout | **PASS** ("all good" to the five steps the Mac session gave at about 13:16) |

The same press also met round 3's green and amber orb, round 2's check 5 (the screen awake), the vibration of check
6 and Face ID with the owner's face in check 7 (section 2 above).

# Round 5, the PC's list: defects found and the state on today's Core

- **Defect found by the owner, 2026-10-07 02:24:** with "Send my location with questions" turned on, every question
  went red ("NOT ANSWERED · Unknown fields."). Cause: the location field is new in Core 1.0.17 and today's 1.0.16
  refuses a question with an unknown field. The reviewer had caught the same thing minutes earlier (the high finding
  of the round 5 review). Fix installed at 02:30: the location goes only to a Core that shows the 1.0.17 fields, and
  the sheet and the Overview say so. The owner had turned the switch off meanwhile.
- The rest of round 5 waits for 1.0.17 on the PC; on today's Core every new panel reads "not on this Core yet".

# Round 5 against Core 1.0.17: the result record (ROUND5-PC-LIST.md; docs/PC-BRIEF-20261010.md, docs/MAC-BRIEF-20261010.md)

Status: **2026-10-10, 10:14 to 11:59 local: R1, R2, R3, R4 and R6 met against Core 1.0.17-0d38218c4e1d; R7
answered as the PC is set up; R5 skipped (no Google sign-in); one app defect found, fixed and checked on the phone
(the restored conversation: 3 of 3 relaunches after the fix), two Core-side findings sent to the PC.** App 1.2 with round 5b (commit 4618d55 and the review fixes after it),
installed by `xcodebuild test` at 11:04 and 11:16. Evidence: the owner's screenshots, the Mac's screenshots
(`devicectl`) and the phone test `JARVISUITests` (test5 to test8); pictures in `records/round5-20261010/` (runN- =
the test run, owner- = the owner's own pictures). The owner gave Face ID at every launch and pressed APPROVE by hand
three times (11:22, 11:43, 11:48), each time on a timer the test's own question had raised.

| Item | What was seen | Verdict |
|---|---|---|
| R2 ticks | THIS PHONE: "May use this PC's tools (ticked on the PC)", "May approve for JARVIS (ticked on the PC)" (10:16); Phone settings, Scope: "Questions, reading, saving, and this PC's tools under the owner's switches. May approve what waits for the owner." (11:05, 11:17) | **PASS** |
| R1 the panel and the sheet | APPROVALS "None waiting", the sheet "Nothing is waiting." (10:18, 10:24) | **PASS** |
| R1 a waiting approval | "Set a timer for one minute called phone test." → "One minute, "phone test," is waiting for your approval on screen, Sir. Nothing's ticking yet — approve it and it starts." (11:22); the line "1 approval waiting · open"; the sheet "A tool set to ask first · Expires in 14 min · Set a timer · From b1 · 11:22 · title: phone test / seconds: 60 · REJECT · APPROVE" | **PASS** |
| R1 APPROVE with Face ID | pressed by the owner (11:22, 11:43, 11:48); Face ID's tick, the receipt "Set a timer — Applied. scheduled" (11:48); the Core's line in the conversation, read back at once: "Approved from b1: Set a timer. Result: scheduled." (11:43, and after the relaunch at 11:48) | **PASS** |
| R1 REJECT | "Set a timer for one minute called reject test." → "It's on the screen waiting for your approval, Mr. Teague — one minute, "reject test." Nothing is counting down yet; reject it and nothing will be scheduled."; item "Set a timer · From b1 · 11:53"; REJECT → "Rejected."; no "Approved from" line (run 7) | **PASS** |
| R3 location | switch on; THIS PHONE "Sent with questions" (11:06, 11:17, still at 11:20 with the phone lying still); "your device places you in Greenwich, on the lower North Shore. The nearest station is St Leonards, about 3.8 km away" (11:07); "You're in Longueville ... The nearest station is Artarmon, about 3.8 kilometres away" (11:18) | **PASS** (the position reached the Core and was used; the two fixes named neighbouring suburbs) |
| R4 notices | the list: "From the Core · 10 Oct 2026 at 09:27 · Automatic backup done." (owner, 10:24); after the announcement NOTICES "1 UNREAD" and the list "Announcement · 11:41 · Mr. Teague, I have to be on texted you: Test" above the backup | **PASS** |
| R4 announce | Siri, driven from the Mac with the words as text: "Announce to JARVIS" → (Siri took the sender from what it heard in the room: "I have to be on") → "What does it say?" → "Test" → **"Announced by JARVIS."** (`spoken` true: the PC took the words to say aloud) | **PASS** (the intent and the Core; the sender was Siri's hearing, not the app) |
| R5 calendar and mail | skipped: no Google sign-in on the PC | — |
| R6 devices | "This Core does not serve the device list yet. Nothing is invented here." (11:06, 11:20): 1.0.17 answers "Operation unavailable."; the route comes with 1.0.18 | **as designed** |
| R7 screen | "No frame came through, Mr. Teague — Screen Vision has no authorised display on the PC right now ... Open JARVIS on the PC, go to Communications → Screen Vision, authorise a display, and ask me again." (11:19) | one of the brief's answers; an analysis itself needs a display authorised on the PC |
| "Remember that" | after "Phone check note: the round 5 tests ran from the Mac on 10 October 2026." the first "Remember that" (11:09) saved the line (the next run's reply: "Already logged ... is saved as a fact"); the second (11:20) answered "Remembered: JARVIS said: Already logged, Mr. Teague — ..." | the word "that" is no longer saved, but "Remember that" saves the line before it even when that is JARVIS's reply: a junk fact on the PC (STATUS.md, Requests for the PC, 5) |
| Replies while written | "reply written live false" in every run | not seen (the PC's setting off, as far as the phone can tell) |
| Action guard | not triggered | not seen |

**Found on the way:**

- **The link**: at about 11:09 the phone lost the Core while JARVIS answered "Remember that" (CORE NOT REACHED; the
  test's next question was held on the phone and dropped when the run was stopped). The Core had not restarted
  (UP 1 H 51 MIN at 11:16); the owner saw ONLINE again by 11:14.
- **App defect, fixed in code**: after a relaunch the Ask screen came up empty in two of three relaunches (11:41 and
  11:53; the conversation came back at 11:48), where plan check 3 had passed with 1.0.16. The one read of the
  restored conversation at the start was not tried again when it failed; now it is tried at every status and health
  reading until one succeeds (`SessionModel.reloadLinesIfPending`; given up only when the Core refuses the
  conversation, or after five failed reads). **Checked on the phone after the install: three relaunches in a row,
  each with the owner's Face ID, the last conversation's lines back each time** (`test9_RelaunchRestoresLines`,
  `run8-relaunch-1..3.jpg`).
- **A two-minute timer at 10:27** (before Ask first was set): the reply said it "should fire around 07:19"; asked
  where 07:19 came from, JARVIS said it had not checked the clock (STATUS.md, Requests for the PC, 4).
- **Test mistakes**, owned: the first run's screenshots showed only the top of the Ask screen (the test now scrolls
  and records each reply's words); one run stopped on a search form the phone does not accept (`label.length`,
  fixed); the reviewer's check found that the first approval test could have approved another waiting item with
  the owner's face (the run was stopped before APPROVE; the test now answers only a timer raised by this phone's
  own question when it is the one item waiting).
- **Timers on the PC from these checks**: phone test (11:22), phone test two (11:43 and 11:48), each one minute,
  approved by the owner; reject test (11:53) not set. "Set a timer" is to go back on the PC to what it was before the test (owner).


# Round 6: the result record (ROUND6-CONVERSATION-SIRI-SHARE.md)

Status: **on the owner's phone since 2026-10-10 about 14:35 (commit 0a29200); items 11 and 13 seen working by the
owner at 14:36, item 12 at 14:45, items 1 and 2 by about 20:04; the other checks pending.** Screenshots in `records/round6-20261010/` (the owner's home-screen
pictures cut down to the widget and Siri's card).

| Check | Seen | Record |
|---|---|---|
| The pairing through the key's move into the App Group | the first start of the new build (14:21): ONLINE, Core 1.0.17-0d38218c4e1d, AI READY, from the Mac's screenshot | 04-ask-too-wide-1421.jpg |
| The Ask screen fits the phone | at 14:21 it did not (the header, badge, settings button and plates cut at both edges: the Earth picture widened the screen); fixed, seen at 14:24 and 14:32 (LINK "34 ms" whole) | 04-ask-too-wide-1421.jpg, 05-ask-fits-1432.jpg |
| 13 "Hey Siri, ask JARVIS" without the app | the owner, 14:36: "What time is it"; Siri's card over the home screen showed JARVIS's reply "Local time: 2026-10-10T14:36:17.893246+11:00"; the app did not open | 03-siri-answer-in-place-1436.jpg |
| 13 Siri's exchange on Ask | the owner's screenshot, 14:36: "What time is it" and the reply as the Ask screen's last two lines | 01-ask-after-siri-1436.jpg |
| 11 The widget, medium | the owner, 14:36: JARVIS, ONLINE, 0 APPROVALS, 0 NOTICES, "Checked 14:36" (14:35 in the picture under Siri's card) | 02-widget-medium-1436.jpg |
| 12 Share to JARVIS from Safari | the owner, 14:45: a Guardian article shared to JARVIS; the sheet showed WEB PAGE with the page's title, its site and "The page's text (7,788 characters) goes with your question.", then YOU "Summarise this page" and JARVIS's summary of the article, then ASK MORE ABOUT IT; STOP ALL at the top | 06-share-safari-page-1445.jpg |
| 12 Share to JARVIS from Photos or Notes, a follow-up question, the Face ID lock in the sheet | pending | |
| 1 A conversation | on the owner's word at about 20:03, "conversation ok": a tap on the microphone, a question, JARVIS's answer, "thank you Jarvis" (the steps given at 14:47) | the owner's word |
| Away from home | the owner's report at about 20:03: from a club in the middle of Sydney, about 10 km from the PC, the app was connected to the Core on the PC (over the private network) and conversations ran through it; replies took about 30 seconds at most | the owner's word |
| 2 "Hey Siri, talk to JARVIS" | on the owner's word at about 20:04, "talk ok": the app opened in a conversation | the owner's word |
| 3, 4 and the rest | pending (Look at this and a picture shared from Photos, after the camera tick on the PC; the heads-up) | |

Two automated starts from the Mac (the header on every screen, Siri) stopped before any test at iOS's "Enter iPhone
Passcode for XCTest, Enable UI Automation" (14:26): the owner's passcode, not typed; the owner checked Siri by hand
instead.

Siri's answer in place waits about 24 s in all (item 13); with replies of up to about 30 s away from home, the
slowest would come as "JARVIS is still working on that. The reply will be in the app." rather than in Siri's voice.

For the PC (not the app's): "What time is it" was answered with the clock tool's raw reading, "Local time:
2026-10-10T14:36:17.893246+11:00", not a sentence; Siri showed and read it as it is.
