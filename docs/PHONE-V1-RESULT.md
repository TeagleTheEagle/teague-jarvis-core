# JARVIS for iPhone, version 1: the result record (docs/PHONE-PLAN.md step 10)

Status: **IN PROGRESS, 2026-10-06 evening. The phone is paired and talking to the one Core over the private network;
the plan's section 10 checks are partly done.** Everything here was done by the owner on the PC, the Mac and the
phone; Claude read records and process lists on the PC and the owner's screenshots. Networking (Tailscale, the
switch) was the owner's act throughout.

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

## 3. The plan's section 10 checks

| # | Check | State |
|---|---|---|
| 1 | Away from home, Wi-Fi off, cellular on: a typed question answered | **done on cellular (5G, no Wi-Fi symbol) at 22:20 local**, from home: a spoken question answered, link 183 to 215 ms (22 ms on Wi-Fi). The path away from home is the same one (Tailscale over cellular); the physically-away case stays to be seen but adds nothing to the route. Screenshots `docs/phone-evidence/phone-app-cellular-*-20261006-2220.png` |
| 2 | Hold to speak: words as text, answered, the reply spoken in JARVIS's voice | **done at 22:20 local on cellular**: "Hey Jarvis, can you still hear me?" heard by the Core's speech recognition and shown as text, THINKING "On the PC", then SPEAKING "In JARVIS's voice" (the speakers tick on the PC and Speak replies in the app), then STANDING BY with the answer; a second exchange answered |
| 3 | Close and reopen: still paired, the conversation continues | not yet |
| 4 | Chats lists the phone's conversations; search finds one | **done 22:23**: "1 CONVERSATIONS FROM THIS PHONE", the conversation ACTIVE with its last line, 11 messages, TODAY; opened, every message with its time, CONTINUE offered (`phone-app-chats-20261006-2223.png`, `phone-app-conversation-view-20261006-2223.png`). Search not tried |
| 5 | Status shows live CPU, memory, storage, Core version, round trip, stop state | **done 22:23**: THIS PHONE reached, PAIRED, 24 ms round trip, address `thegrizzlybear:8790`, Core 1.0.16-fccde24e2cc6, emergency stop not stopped, may save memories and tasks (ticked on the PC); SYSTEM HEALTH CPU 5 %, memory 27 %, storage 92 % (red: the PC's C: drive is that full), link 24 ms, Core up 1 h 42 min, last reply 3.9 s; OVERVIEW 4 open tasks, three projects, nothing upcoming; read at 22:23:53 (`phone-app-status-20261006-2223.png`) |
| 6 | STOP on the phone stops the PC's JARVIS; RESUME on the PC restores both | **done 22:24**: STOP ALL on the phone: EMERGENCY STOP, STOP ON, red ring, "Press RESUME on the PC"; after RESUME on the PC: STANDING BY, STOP CLEAR, the ring cyan (`phone-app-emergency-stop-20261006-2224.png`, `phone-app-after-resume-20261006-2224.png`). Whether the PC's banner named the phone was not photographed. **Defect:** after the resume the yellow note "Emergency stop is on ..." stayed on the Ask screen until the next action (section 2, item 7) |
| 7 | REVOKE on the PC: "pair again"; pairing again works | not yet |
| 8 | Switch off, or Tailscale off: "Core cannot be reached" | the message was seen while the door was still closed (before the switch was on); the deliberate test not yet |
| 9 | With the D2 tick, "remember ..." is known on the PC; without it, refused plainly | the tick is on (Status shows it); "remember ..." not yet tried |
| 10 | The desktop JARVIS works as before; the activity log and Settings > Devices name the phone | **Settings > Devices done 22:23**: the Private network line green "Open at 100.103.95.28:8790 (thegrizzlybear.tail806593.ts.net)"; DEVICES (1 PAIRED): This PC, the glasses test client, and `phone` PHONE Online "Last seen just now" with microphone, speakers, display and "May save memories and tasks" ticked, RENAME and REVOKE (`pc-devices-phone-paired-20261006-2223.jpg`). The desktop JARVIS answering as before and the activity log not photographed |
| 11 | Said plainly: cellular versus Wi-Fi, fix rounds on the Mac | the pairing and the first conversation on home Wi-Fi (22:15); checks 1 and 2 on cellular with Wi-Fi off (22:20), from home; fix rounds: the look (one zip), the icon fix (one zip), the Info entry (by hand) |

## 4. Next

The owner, when convenient: the ticks for microphone and speakers in the phone's row on the PC (and "May save
memories and tasks" if wanted), then checks 2 to 10 in any order, with a photo of each; check 1 away from home. Claude
then completes this record. The header layout (section 2, item 4) and the icon are the next fix round on the Mac.
