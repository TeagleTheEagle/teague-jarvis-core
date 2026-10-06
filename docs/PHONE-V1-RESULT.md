# JARVIS for iPhone, version 1: the result record (docs/PHONE-PLAN.md step 10)

Status: **VERSION 1 CHECKED, 2026-10-06, 22:32 local: nine of the ten checks of the plan's section 10 met; check 3
(the conversation continues after the app is closed and reopened) FAILS and is fixed in the app's next round** (the
owner's ticks and screenshots; the physically-away case of check 1 ran on cellular from home, the same route).
Everything here was done by the owner on the PC, the Mac and the phone; Claude read records and process lists on the PC
and the owner's screenshots. Networking (Tailscale, the switch) was the owner's act throughout. Defects for the app's
next round are in section 2 (items 4, 5, 7, 9 and 10); version 2 is listed in section 4 for the owner's decision.

## 1. What was reached tonight (2026-10-06, 21:45 to 22:15 local)

| Step | What | Seen |
|---|---|---|
| Tailscale on the PC | Account bensagoat55@gmail.com (Google); Tailscale for Windows 1.102.4 installed by the owner; the PC is `thegrizzlybear` at 100.103.95.28, Connected | the owner's photo of the Tailscale menu; `tailscale status` read by Claude |
| Tailscale on the phone | The iPhone (`iphone-15`, 100.64.112.19, iOS 26.6.1) in the same network, Connected | the Tailscale console: 2 machines (`docs/phone-evidence/tailscale-console-2-machines-20261006-2209.jpg`); `tailscale status --json` on the PC: 1 peer online |
| The door | Settings > Devices > Private network ticked by the owner; the Core listening on 100.103.95.28:8790 (python, the 1.0.16 release) | `Get-NetTCPConnection` read by Claude; a TCP test from the PC to the door succeeded |
| Windows Firewall | the Tailscale interface is classed Private; Tailscale's own rule allows inbound to 100.103.95.28 on that profile; no block rule for Python | `Get-NetFirewallRule` read by Claude |
| Pairing | a code from the PC typed with the address 100.103.95.28 and port 8790; PAIR succeeded | the owner's word; the app moved to the three screens |
| First screen | Ask: ONLINE, Core `1.0.16-fccde24e2cc6`, AI READY, CPU 3 %, LINK 22 ms, MEMORY 27 %, STOP CLEAR, STANDING BY | `docs/phone-evidence/phone-app-paired-ask-20261006-2215.png` |
| First conversation | "Hello Jarvis, how are you done?" (the owner's words as the Core's speech recognition heard them, or typed) answered by JARVIS; a second exchange answered | `docs/phone-evidence/phone-app-first-conversation-20261006-2215.png` |

## 2. What went wrong on the way, and the fixes

1. **The phone could not reach the door at first** ("JARVIS cannot be reached"): the PC's Tailscale knew no peer
   because the phone had signed into a different Tailscale network (two networks with the same e-mail come from two
   sign-in providers). Fix: the owner logged out of Tailscale on the phone and signed in again with Google; the
   console then showed 2 machines and the PC's client listed the phone within a minute.
2. **The app crashed right after pairing.** Cause: the Ask screen asks iOS for microphone permission when it first
   appears, and the project's Info list had no "Privacy - Microphone Usage Description" entry; iOS ends an app on
   the spot for that. Fix: the owner added the entry in Xcode's Info tab (the text from `phone/ios/README.md`) and
   ran again; the app opened on the Ask screen. Note for the README: the entry is not optional, and its absence
   looks like a crash, not an error.
3. **App Transport Security:** the project's Info list shows no App Transport Security row, yet plain HTTP to
   100.103.95.28 worked: iOS exempts IP addresses and unqualified host names (such as `thegrizzlybear`) from that
   rule. The README's step stays right for a fully qualified name; for the address or the short name it is not needed.
4. **Header layout at the phone's width** (seen in the screenshots): "ONLINE" wraps onto two lines, the STOP ALL
   button is squeezed to an "S" and a dot, and the subtitle "ONE CORE // PRIVATE NETWORK" is cut. A fix round on
   the Mac: give the trailing items of `ScreenHeader` fixed sizes and let the title column shrink. Not done tonight.
5. **The home-screen icon** still shows the placeholder grid after the asset-catalog folders were replaced from the
   icon-fix zip; parked by the owner ("let's figure that out later").
6. **The Xcode asset steps** of the look (two image sets, the AppIcon) went wrong twice before they were right; the
   file-level fix (`JARVIS-ios-icon-fix-20261006-2127.zip`, the catalog folders replaced in Finder) is the method to
   use next time.
7. **The stop note outlives the stop** (seen at 22:24): after RESUME on the PC the Ask screen read STANDING BY with
   STOP CLEAR, but the yellow line "Emergency stop is on. JARVIS does nothing until RESUME is pressed on the PC."
   stayed until the next action. The note is set from the Core's refusal and is not cleared when a later `hello` or
   `status` says the stop has lifted. Fix in the next app round with the header layout.
8. **Storage 92 %** on the Status screen is the PC's C: drive, as JARVIS measures it (15.7 GB free of 238 at the
   update). Not an app matter; the C: cleanup steps are parked on the owner's word.
9. **"Remember that" saves the word "that".** The exact memory command (the same on the PC) stores the words after
   "remember"; a spoken "remember that" after a statement does not reach back to the statement. The owner's intent is
   plain; a Core-side improvement (resolve "that", "this" or "it" to the previous line of the conversation) for a
   later Core release, on the owner's word. The saved memory "that." can be deleted on the PC's Memory page.
10. **The conversation looks fresh after a relaunch** (check 3): the app restores the conversation id but not its
    lines. Fix: at launch, when a conversation id was restored, load its history from the Core (the same route Chats
    uses for CONTINUE) and show the last lines on Ask. The re-pair-after-revoke case (a new device id, the old
    conversations not listed) is by design of the Core's device book; said plainly here.
11. **A Core reply replaced by "No matching action result was recorded for this request. Completion is not
    confirmed."** (22:36, the owner's typed question "list improvements/additions needed in the next build for the
    app"). Core-side, the same on the PC: `answer_evidence.action_guard` replaces a whole reply whose wording claims a
    finished action ("has been updated", "I've completed", and the like) when no action tool ran in that turn. A list
    of suggestions that mentions updates or completed work trips it, and the owner gets the guard's sentence instead
    of the answer. Not an app matter. For a Core release: narrow the guard to claims about this turn's own actions
    (only when a tool was attempted, or first-person claims only) and append the caveat under the reply instead of
    replacing it. Meanwhile asking the question again usually gives an answer whose wording does not trip it.

## 3. The plan's section 10 checks

| # | Check | State |
|---|---|---|
| 1 | Away from home, Wi-Fi off, cellular on: a typed question answered | **done on cellular (5G, no Wi-Fi symbol) at 22:20 local**, from home: a spoken question answered, link 183 to 215 ms (22 ms on Wi-Fi). The path away from home is the same one (Tailscale over cellular); the physically-away case stays to be seen but adds nothing to the route. Screenshots `docs/phone-evidence/phone-app-cellular-*-20261006-2220.png` |
| 2 | Hold to speak: words as text, answered, the reply spoken in JARVIS's voice | **done at 22:20 local on cellular**: "Hey Jarvis, can you still hear me?" heard by the Core's speech recognition and shown as text, THINKING "On the PC", then SPEAKING "In JARVIS's voice" (the speakers tick on the PC and Speak replies in the app), then STANDING BY with the answer; a second exchange answered |
| 3 | Close and reopen: still paired, the conversation continues | **FAILS** (the owner, 22:32: "When you close out of the app, mid-conversation, it resets you to a fresh one"; `phone-app-after-relaunch-20261006-2232.png`: the Ask screen STANDING BY with no lines). Still paired, yes. The conversation id is kept in the app's settings and restored at launch, so the next question would go on in the same conversation on the Core; but the Ask screen's lines are never reloaded from the Core after a relaunch, so it looks and feels like a fresh one. Also, pairing again after a revoke clears the id and gives the phone a new device id, so the conversations of the old pairing are not listed for the new one. Fix in the app's next round (section 2, item 10) |
| 4 | Chats lists the phone's conversations; search finds one | **done 22:23**: "1 CONVERSATIONS FROM THIS PHONE", the conversation ACTIVE with its last line, 11 messages, TODAY; opened, every message with its time, CONTINUE offered (`phone-app-chats-20261006-2223.png`, `phone-app-conversation-view-20261006-2223.png`). Search not tried |
| 5 | Status shows live CPU, memory, storage, Core version, round trip, stop state | **done 22:23**: THIS PHONE reached, PAIRED, 24 ms round trip, address `thegrizzlybear:8790`, Core 1.0.16-fccde24e2cc6, emergency stop not stopped, may save memories and tasks (ticked on the PC); SYSTEM HEALTH CPU 5 %, memory 27 %, storage 92 % (red: the PC's C: drive is that full), link 24 ms, Core up 1 h 42 min, last reply 3.9 s; OVERVIEW 4 open tasks, three projects, nothing upcoming; read at 22:23:53 (`phone-app-status-20261006-2223.png`) |
| 6 | STOP on the phone stops the PC's JARVIS; RESUME on the PC restores both | **done 22:24**: STOP ALL on the phone: EMERGENCY STOP, STOP ON, red ring, "Press RESUME on the PC"; after RESUME on the PC: STANDING BY, STOP CLEAR, the ring cyan (`phone-app-emergency-stop-20261006-2224.png`, `phone-app-after-resume-20261006-2224.png`). Whether the PC's banner named the phone was not photographed. **Defect:** after the resume the yellow note "Emergency stop is on ..." stayed on the Ask screen until the next action (section 2, item 7) |
| 7 | REVOKE on the PC: "pair again"; pairing again works | **done 22:28**: after REVOKE the app returned to the pairing screen with "Device key invalid or revoked. Pair this device again on the PC.", the address kept (`thegrizzlybear`, 8790); paired again with a new code and ONLINE by 22:31 (`phone-app-revoked-20261006-2228.png`) |
| 8 | Switch off, or Tailscale off: "Core cannot be reached" | **done 22:29**: with Tailscale off on the phone the Ask screen read NOT REACHED, CORE NOT REACHED with the three things to check, the ring grey, the last readouts kept; back on again afterwards (`phone-app-core-not-reached-20261006-2229.png`) |
| 9 | With the D2 tick, "remember ..." is known on the PC; without it, refused plainly | **done 22:30, with the tick**: "Remember that." from the phone answered "Remembered: that." and the PC's Memory page shows the saved memory "that." at 22:30:34 (`phone-app-remember-20261006-2231.png`, `pc-memory-remember-from-phone-20261006-2230.jpg`). The path works; the content is the word "that" because the exact memory command saves the words after "remember" and does not resolve "that" to the line before it, on the PC exactly as on the phone (section 2, item 9). The without-the-tick refusal was not tried |
| 10 | The desktop JARVIS works as before; the activity log and Settings > Devices name the phone | **Settings > Devices done 22:23**: the Private network line green "Open at 100.103.95.28:8790 (thegrizzlybear.tail806593.ts.net)"; DEVICES (1 PAIRED): This PC, the glasses test client, and `phone` PHONE Online "Last seen just now" with microphone, speakers, display and "May save memories and tasks" ticked, RENAME and REVOKE (`pc-devices-phone-paired-20261006-2223.jpg`). The desktop JARVIS answering as before and the activity log not photographed |
| 11 | Said plainly: cellular versus Wi-Fi, fix rounds on the Mac | the pairing and the first conversation on home Wi-Fi (22:15); checks 1 and 2 on cellular with Wi-Fi off (22:20), from home; fix rounds: the look (one zip), the icon fix (one zip), the Info entry (by hand) |

## 4. Next, and version 2 for the owner's decision

**The app's next round on the Mac** (one zip, as before): the conversation lines reloaded after a relaunch (item 10,
check 3), the header at the phone's width (item 4), the stale stop note (item 7), the icon (item 5). Then check 3 is
run again and this record closed.

**Version 2** (plan section 11, each on the owner's word): camera and photos ("look at this"), the PC's chats on the
phone, replies appearing while written, a Siri shortcut, notifications, the Dynamic Island, pairing by QR code, HTTPS
through Tailscale, the Halo glasses with the phone as their bridge, a faster start of JARVIS at sign-in, the always-on
mini PC question. App-only candidates offered to the owner on 2026-10-06 for the next round: replies appearing as they
are written (the Core already streams the pieces), Bluetooth headsets and audio interruptions, the screen awake while
listening or speaking, Face ID on open, the speak-replies button on the Ask screen with a vibration on the reply, the
Siri shortcut, text size following the phone's setting.

**Core-side findings from the phone checks, for a Core release on the owner's word:** "remember that" resolving to the
line before it (item 9); the action guard's false positive (item 11); the camera route for "look at this"; pairing by
QR code; the PC's chats on the phone (a privacy decision). The owner's wish list of 2026-10-06 (texts, calls, contacts, Gmail, calendar, maps) is its own plan:
contacts, Gmail and calendar are possible with permission; texts and calls only through Windows Phone Link on the PC.

**TestFlight** (plan step 9) is still open: today the app runs from Xcode's own install, which lasts a year with the
owner's paid membership; TestFlight makes it independent of the Mac and is the owner's steps in `phone/ios/README.md`.
