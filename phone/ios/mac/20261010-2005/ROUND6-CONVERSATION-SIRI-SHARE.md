# Round 6: conversation, Siri without the app, photos, the widget and Share to JARVIS

Owner's words, 2026-10-10: "build round 6 with 1 to 5 and 7 to 10, and 11 and 12, I OK the Apple account change",
"make it look exactly like this" (two pictures), and the same afternoon "continue round 6, Apple account OK" and
"can we also implement that I can use jarvis and no require to be in the app to use it" (item 13). Item 6 (bigger
text) is deferred to its own round. Everything here is the app's: the Core on the PC is unchanged, and the app
sends it nothing it does not already take (`start` with `text`, `conversation`, `image`, and `location` only when
hello says `location: true`; `status`; `events`; `history`; `stop`).

## 1. Item by item

| Item | What the app does | Where |
|---|---|---|
| 1 Hands-free conversation | A tap on the microphone starts it (a hold is still one question). JARVIS listens, sends at a pause, answers, and listens again once its voice has finished (the microphone is off while it speaks, and a reply's voice is never played into a recording). It ends on "thank you Jarvis", "thanks Jarvis", "stop listening", "that's all", "goodbye/bye Jarvis" (said alone, or after "okay", "no", "please" and the like: not sent); a request that ends with them ("lights off, thank you Jarvis") is sent and the conversation ends after its reply. It also ends on a tap, 20 s of silence, three turns in a row with nothing understood, the app leaving the front or locking, the stop, a lost link, a held question, a failure, and at the first turn after ten minutes. A tap while JARVIS speaks skips to the owner's turn. | SessionModel, AskView |
| 2 "Hey Siri, talk to JARVIS" | Opens the app in a conversation (as the lock-screen button and jarvis://listen do); if Siri's sheet going away makes the app inactive within 2 s, the conversation starts again once. | SiriIntents (TalkToJarvisIntent), SessionModel |
| 3 Look at this | Camera or Photos, a question, `start.image` as a JPEG under 2 MB and 1600 px, prepared off the screen's thread (a Photos picture is read at size, never decoded whole); the question sheet opens after the camera has closed. Needs the camera ticked for this phone on the PC (the phone now declares the camera). | PhotoQuestion, JARVISShared/PhotoPrep |
| 4 Heads-up | When the waiting or unread count rises while the app is open: a banner under the header (clear of STOP ALL above and the microphone below), OPEN or the cross, gone after 6 s. | JARVISApp (MainTabs), SessionModel |
| 5, 7 Hear again, copy, share | A tap on a reply reads it again (even when replies are muted); press and hold any line: Hear again, Copy, Share. | AskView |
| 8 Quick asks | Look at this, What's on today?, Analyse my screen, Any notices? (opens the list), How's the PC? | AskView |
| 9 Share a conversation | From an open chat in Chats, as text (its last 100 lines). Search already existed. | ChatsView |
| 10 What can I say? | Every phrase, button and set-up, from Phone settings; worded to match the code. | HelpView |
| 11 Home Screen widget | Small and medium: Online or Stopped (or Offline, Not paired, Open JARVIS, No reading), the approvals waiting (only with "May approve for JARVIS") and the unread notices, and the time it checked. The widget asks the Core itself (`status`, with the key from the shared Keychain group); iPhone refreshes it now and then (about every 15 minutes at best); the app asks for a fresh drawing when the stop or a count changes, and so do "Hey Siri, stop JARVIS" and Share's STOP ALL. On the medium size a tap on a count opens that list (jarvis://approvals, jarvis://notices). Nothing invented: when the Core is not reached it says Offline with no counts. | JARVISControls/JarvisStatusWidget |
| 12 Share to JARVIS | A new share extension (`JARVISShare`, com.teagueindustries.jarvis.share) for one web page, link, text or picture. From Safari the page's title, address, selected words and visible text (Config/PageText.js) go with the question, cut to fit 12,000 characters and marked as material to read, not instructions to follow. A picture is read from its file at the size sent. The reply shows in the sheet (up to 120 s; later it is in Chats), follow-up questions in the same sheet, STOP ALL from the first moment, the app's Face ID lock when it is on. Each share is a conversation of its own in Chats. | JARVISShare/ |
| 13 Siri without the app | "Hey Siri, ask JARVIS": Siri asks what to ask, the question goes to the Core, and Siri shows and says the reply (as plain words, about 1,200 characters at most; the rest is in the app) without opening the app, within about 24 s in all. Only on an unlocked iPhone, and not while "Lock with Face ID" is on in the app (Siri says so). The question and reply go into the Ask screen's conversation, which reads them at the next hello. Also a Shortcuts action whose value is the reply (for Dictate Text > Ask JARVIS > Speak Text, and Back Tap). The old way (Siri opening the app with the question) is gone. | SiriIntents (AskJarvisIntent), JARVISShared/OneQuestion |
| The new look | Readout plates around the orb, the Earth's horizon under it (cut from the owner's picture), stars and planet rims behind every screen, brighter panel edges. | Hud, AskView, JARVISShared/Theme |
| STOP ALL on every sheet | Approvals, Notices, What can I say?, Phone settings, Look at this and Share to JARVIS now carry it (the binding rule; before, only the main screens and the lock screen had it). Apple's own camera view has none. | JARVISApp (SheetStopButton) |

## 2. The project and the Apple account (disclosed)

- New target JARVISShare (hand-made ids 0000000000000004xxxxxxxx in project.pbxproj), embedded in the app; it shares
  JARVISShared/ except OpenJarvisListeningIntent.swift (a synchronized-folder exception); its Info entries in
  Config/JARVISShare-Info.plist; PageText.js in its Resources; its own small copy of the badge (256 px). The widget
  lives in the existing JARVISControls extension, with a 96 px badge copy.
- App Group `group.com.teagueindustries.jarvis` for the app, JARVISControls and JARVISShare (Config/*.entitlements).
  The signed build of 2026-10-10 about 13:42 (`-allowProvisioningUpdates`, on the owner's "Apple account OK") made
  Xcode set this up in the owner's Apple developer account: the App Group, the App Groups capability on
  com.teagueindustries.jarvis and com.teagueindustries.jarvis.controls, and a new App ID
  com.teagueindustries.jarvis.share, each with a development profile ("iOS Team Provisioning Profile: …"). Seen:
  the three profiles in the build log, the group in all three signatures (`codesign -d --entitlements`) and in the
  share extension's profile.
- At the app's first start the device key moves from the app's own keychain group into the App Group's (the old copy
  goes only after the new one reads back the same), and the Core's address, the pairing's id and name and the lock
  choice are mirrored into the App Group's settings. The key never leaves the Keychain. **Rollback:** once this build
  has run, an older build finds no pairing (it cannot see the App Group's keychain group); pairing from an older
  build would make a second device on the PC. Seen on the phone at 14:21: the pairing came through the move (ONLINE,
  Core 1.0.17-0d38218c4e1d).

## 3. The review (one independent reviewer agent, three passes)

- **First pass** of the whole round (`d6feddc..0b909de`): 1 high, 3 medium, 13 low, all applied in 754afe1. High:
  a reply's voice could play into a recording and be sent back as the owner's next question. Medium: a conversation
  could stay on with nothing listening; Siri could run past its time; Siri answered past the app's Face ID lock.
  Low: Siri's exchange not shown after "still working"; big pictures in the share extension's memory; STOP ALL
  disabled while a share was read; two widget sentences not backed by the Core and "Not paired" for a phone that is;
  the heads-up over the microphone; a lost press after an interrupted one; help wording; Markdown in Siri's value;
  the photo work on the screen's thread and a sheet that could fail to open after the camera; the widget badge's
  size; STOP ALL missing on the sheets and a stale widget after a stop raised elsewhere; Keychain write robustness;
  share sheet completion, conversation ids with seconds only, a cleared notice, the Siri conversation's re-arm.
- **Check of the fixes** (`0b909de..754afe1`): 14 right as made, three incomplete or introducing something new;
  7 new defects (1 medium: Siri's exchange missed when the app came back after five minutes; 6 low: the heads-up over
  an open conversation's STOP ALL, closing words sent as questions, a cancelled skip leaving a conversation on, a
  voice dropped by a state check, a re-arm kept across the background, the share preview overstating a page's text
  beside a long selection), all applied in 655575b.
- **Found on the phone, missed by the review:** the Ask screen was wider than the phone (the Earth picture, 489 pt
  wide at 170 pt high, widened the whole screen; the header, badge, settings button and plates were cut at both
  edges, screenshot 14:21). Fixed in 655575b (the picture laid over a box of the screen's width; the CPU/Link plate
  keeps its room), seen fixed at 14:24 and 14:32.
- **Last check** of 655575b: everything right but one low-medium defect, partly of the reviewer's own earlier
  suggestion: "Yes please, thank you Jarvis" (an answer to JARVIS's own question) ended the conversation without
  being sent. Applied in 0a29200: only thanks, goodbyes and fillers before an end phrase end it unsent; any other
  word, above all one that accepts or asks, is sent first and the conversation ends once it is answered. Checked on
  17 sentences with the code itself (Swift on the Mac).

## 4. Questions for the PC (carried by the owner)

- "A request is already running. Stop it or wait for completion.": is it per device or per conversation? Siri's and
  Share's questions go into conversations of their own when the app's own question is running; if the Core allows
  one question per device at a time, they are refused with that sentence while the app's question runs (said
  plainly on the phone).
- Nothing else is needed from the PC for this round.
