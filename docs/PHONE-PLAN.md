# JARVIS for iPhone: the plan (version 1)

Status: **PROPOSAL, READY FOR YOUR APPROVAL (2026-10-06, Claude Code, Fable 5.1).** Nothing in it has been built.
Written on your word "write the phone plan" (2026-10-06), from the decisions you took on 2026-10-06, the recommendation
you accepted ("go with your recommendation"), the three screens on the design canvas, the Devices and Speech parts
of release 1.0.15 (`docs/DEVICES.md`, `docs/SPEECH.md`), Phase 4 of the approved roadmap (`docs/ROADMAP.md`), and
sections 7, 8 and 18 of your master document (`docs/owner/JARVIS-MASTER-ARCHITECTURE.md`). The rules of `CLAUDE.md`
are unchanged by this plan.

## 1. In plain words

You get a JARVIS app on your iPhone 15 with three screens, Ask, Chats and Status, that talks to the one JARVIS Core
on your PC: at home on Wi-Fi and away on cellular, over a private network (Tailscale) that only your own devices
belong to. You type or hold to speak, JARVIS answers in text and in its voice, you can stop everything from the
phone, and the Status screen shows the real state of the PC. The phone holds no JARVIS of its own: one Core, one
memory, one identity. Nothing is opened to the public internet and nothing is changed on your router.

Two things have to happen before the phone can connect, in this order:

1. **A small Core release (1.0.16, "the phone release")** on the PC: a switch, off until you turn it on, that lets
   paired devices reach JARVIS over the private network; stronger pairing limits; and the few things the three
   screens need that a device cannot ask for today (its own list of chats, the PC's health numbers, a reply that
   arrives without constant asking). Tested, reviewed and checked like every release: the Stage 7 check in the VM and
   the update of your everyday JARVIS, each on your approval.
2. **The iPhone app itself**, written here as Swift files, built by you on your Mac in Xcode and installed through
   TestFlight (or by cable first).

Your part: install Tailscale on the PC and the iPhone from written steps, keep the PC awake, build the app on the Mac,
and pair the phone with a code read from Settings > Devices on the PC.

## 2. Decisions you already took (not reopened here)

| Decision | Your words or record |
|---|---|
| iPhone app only; no Mac software version | 2026-10-06 (`docs/CURRENT-STATUS.md`) |
| Works at home on Wi-Fi and away on cellular, so a private network (Tailscale), set up by you from written steps | 2026-10-06 |
| The PC stays awake for the first version; an always-on mini PC is a later decision of yours (it would change the "Core lives on the owner's PC" rule) | 2026-10-06 |
| You have a Mac with Xcode and an active Apple Developer membership; install through TestFlight internal testing | 2026-10-06 |
| The recommendation accepted: native SwiftUI app, three screens, pairing by code from Settings > Devices, voice through the Core's speech recognition, replies spoken in JARVIS's voice, emergency stop, Tailscale; version 2 later: camera, Siri shortcut, Dynamic Island, notifications, Halo glasses | "go with your recommendation", 2026-10-06 |
| Real data only on every screen: nothing invented, nothing JARVIS does not measure | design rule kept since the dashboard |
| The design: the canvas "JARVIS iPhone design" (claude.ai artifact `N7JboAbsdEFwPFhrFFdAcs`), three artboards at iPhone 15 size, your two hand edits of the Ask screen kept | 2026-10-06 |

## 3. What you get in version 1

### The three screens (from the canvas)

- **Ask.** The header says ONE CORE // PRIVATE NETWORK and whether the Core is online, with the Core version, whether
  the AI is ready, the PC's memory and CPU, the link, STOP and CLEAR. The holographic Core sits in the middle and
  shows what JARVIS is doing (ready, listening, thinking, speaking). Under it: TYPE, MICROPHONE (hold to speak) and
  the three tabs ASK, CHATS, STATUS. The ATTACH button of the design comes with the camera in version 2; version 1
  does not show a button that does nothing. The location line (SYD 33.87S 151.21E) is left out until it has a real
  use.
- **Chats.** Your conversations from this phone, newest first, with the last line of each and a search box. In
  version 1 these are the phone's own conversations (each device's conversations are its own, `docs/DEVICES.md`
  section 3). The chats you had on the PC are not listed on the phone yet (version 2, section 11), but JARVIS knows
  them when it answers you: its search of saved chats covers all of them.
- **Status.** This phone (paired, its id), the connection (stable or not, the path "Private network", the measured
  round trip), the Core version, the emergency stop state, system health from the PC (CPU, memory, storage; no GPU
  or temperature, which JARVIS does not measure), your projects with open tasks, and today's reminders. Panels with
  no data on the PC are hidden, not filled.

### What the phone can do

- **Ask by text or voice.** Hold to speak: the phone records, the PC turns the recording into text (the Core's own
  speech recognition on the PC, as for every device), JARVIS answers. The whole reply appears when it is ready (see
  decision D3), and is spoken in the voice your PC uses (Fish Audio or the Qwen cloned voice, whichever you have
  chosen on the PC). JARVIS may use its reading tools for you (search, news, your lists, projects and saved chats,
  the time, the device list), as any paired device may today.
- **Remember things, if you tick it** (decision D2): with the tick, "remember the garage code" from the phone saves
  the memory on the PC, and tasks and reminders you ask for from the phone are written there too. Without the
  tick the phone only reads, like every other device.
- **Stop everything.** STOP on the phone is the emergency stop that holds: the PC's JARVIS stops, the banner on the
  PC says from which device, and the phone cannot resume. Only RESUME on the PC resumes (`docs/PERMISSIONS.md`).
- **Stay paired.** The phone keeps its key in the iPhone Keychain; closing and reopening the app needs no new
  pairing. REVOKE on the PC locks the phone out from its next request on.
- **Say plainly when the Core cannot be reached** (PC off, JARVIS not started, Tailscale off on either side). Nothing
  else answers: no second JARVIS on the phone, no fallback.

### Not in version 1

Camera and photos; Siri; notifications; the Dynamic Island; the Halo glasses; the PC's chats listed on the phone;
changing settings from the phone; choosing the voice from the phone; resuming from the phone (by design).

## 4. What stays the same

- **ONE CORE, ONE JARVIS, ONE IDENTITY, ONE MEMORY, MANY DEVICES.** The Core lives on your PC. The phone is a client:
  it holds no memory, no AI, no personality of its own. Registering or pairing a device grants no authority.
- **The Core's own routes stay on the PC only.** Everything you do in the desktop app (settings, permissions, resume,
  shutdown, the key file) remains reachable only from the PC. The private network reaches the device routes and
  nothing else (section 5).
- **Your decision of 2026-10-01** that the Core stays on this PC only: it still does. It becomes reachable by your
  own signed-in devices through your private network, and only when you turn the switch on.
- **Owner-only acts stay owner-only** (`CLAUDE.md`): Tailscale (a network), the switch (turning it on is your act),
  keys and passwords, your Apple account, pushing or copying code anywhere, the VM, your everyday installation.

## 5. The PC side: Core release 1.0.16, "the phone release"

Why a release is needed first, as the code stands at 1.0.15 (read-only survey of 2026-10-06, nothing run):

- The Core listens on `127.0.0.1` only, the address is fixed in the program, and every request must name exactly
  `127.0.0.1:<port>`; anything else is refused. A phone on the private network could not get an answer.
- The desktop app starts the Core on a random port at every start. A phone needs a fixed address.
- A device may pair, say hello, ask, read its answer, cancel, have its recording turned into text, have a text
  spoken, stop, and say goodbye (`docs/DEVICES.md` section 3). It cannot list or read its conversations, read the
  PC's health numbers or the Core version, or save a memory. The answer to a question has to be asked for again and
  again until it is there (every tenth of a second in the test client), which is wasteful on cellular.
- The pairing limits were written for a Core reachable from this PC only (`docs/DEVICES.md` section 2, "known
  limit"): there is no lockout for wrong keys, and the attempt counters are shared, not per caller.

What 1.0.16 adds (all in the repo, tested with the same kind of tests as item 4 of 1.0.15: a real local Core in
the tests, a second loopback address standing in for the private network):

1. **Settings > Devices: "Reach JARVIS from paired devices over the private network", off by default.** When on,
   the Core opens a second door on a **fixed port** of its own (settable, with a default) at the PC's Tailscale
   address only (decision D1). Through that door only the device routes are served: no settings, no state, no
   files, no owner route, no page. Requests naming the PC's Tailscale name or address are accepted there; the
   PC-only door is unchanged. If Tailscale is not running on the PC, the switch says so and opens nothing. The
   panel shows the address and name to type into the phone. **Turning the switch on is your act**; the release
   ships with it off.
2. **Pairing limits for a reachable Core:** wrong keys and wrong codes are counted per caller, with a lockout; the
   ten-attempts-a-minute counter is per caller; a pairing can no longer be ended by someone else's wrong codes; the
   code is accepted through the private-network door only while the switch is on and a pairing you started is
   waiting (five minutes, one use, as today).
3. **Four device routes the screens need:** its own conversations (list, and read one of its own; never another
   device's and never the PC's in version 1); the PC's health (CPU, memory, storage, Core version, uptime, whether
   the AI is ready, whether the stop holds; the same numbers the dashboard shows, nothing new measured); an
   overview (your projects with open tasks, today's reminders); and the answer route waits up to ten seconds for
   something new instead of answering "nothing yet" at once (as the PC window's route does today).
4. **A tick per device: "may save memories and tasks"** (decision D2), off for every new device. With it, that
   device's questions run the memory commands and the writing tools you have allowed in Settings > Permissions
   for devices with the tick; a tool set to "Ask first" asks on the PC and the phone waits for your answer there.
   Changes JARVIS makes to itself, settings, resume and everything else owner-only stay out of reach whatever the
   tick says.
5. **Records and release work as for every release:** `docs/PHONE-CORE-1.0.16.md` as the record of what was built;
   one independent reviewer per item with the findings applied; release notes; build, comparison with 1.0.15,
   regression, zip install, sandbox Stage 7; then `docs/STAGE7-CHECK-1.0.16.md` for your approval (it will name the
   disc's drive letter and say that the Gate 20 bound applies with a disposition only when the records show the
   cause to be the VM, as you decided on 2026-10-06); after `STAGE_7_COMPLETE`, the plan for the update of your
   everyday JARVIS for your approval, as for 1.0.15.

The installer (`JARVIS-Setup.exe`) was proposed as the release after 1.0.15. This plan puts the phone release first
and the installer after it, unless you say otherwise (section 9).

## 6. The phone side: the app

- **Native SwiftUI, iPhone only, iOS 18 or later** (decision D4). Three tabs as on the canvas, plus a pairing screen
  (the Core's name or address, then the eight-digit code) and a small settings sheet (forget this pairing, about).
  The colours of the canvas: cyan `#00D9FF` (the main accent) and `#39BFFF`, grounds `#061522` and `#02070D`, text
  `#EAF7FF` and `#7EA6BB`, green `#39F5B5` for good states, amber `#FFC857` for warnings; the brief's red `#FF3B3B`
  is kept for the stop state and errors (the canvas does not use it yet).
- **Starting point:** the three Swift files already in the repo (`ios/JARVIS/Domain.swift`, `SessionModel.swift`,
  `MockCoreClient.swift`, from September). Their client protocol and session model are kept and trimmed to what the
  Core accepts (the Core knows microphone, camera, speakers and display; the files also list haptics and
  notifications, which go). A real client replaces the mock: it speaks the device routes of section 5 exactly, with
  the header the Core expects, the 3 MB body limit, and the Core's error sentences shown as they are.
- **Voice in:** hold to speak records 16 kHz mono (the Core's format), at most 30 seconds, and sends it to the Core,
  which turns it into text on the PC. **Voice out:** the finished reply is sent to the Core's speech route and the
  returned sound (MP3 or WAV, whichever voice you use) is played on the phone.
- **The key** lives in the iPhone Keychain; the Core's address in the app's settings; nothing else is stored on the
  phone except what is on screen. Switching apps and coming back keeps the conversation.
- **Where the code lives:** `phone/ios/` in the repo (the three old files move there). Not part of the Windows
  release; a release ships nothing of the phone.
- **What I can and cannot check here.** There is no Swift compiler for iPhone apps on this PC: I cannot build or run
  the app. I will check the Core side completely on the PC (a stand-in phone in the tests exercises every route the
  app uses) and write the app with plain, long-standing Apple interfaces. **Expect two or three fix rounds on the
  Mac:** you build, send me the errors or a photo, I fix. This is the plan's main cost in time.
- **Getting the code to the Mac** (decision D5): a zip I write to `D:\JARVIS-release-work\phone\` that you move to
  the Mac (AirDrop from a USB stick or iCloud Drive), or a private GitHub repository you create and push to yourself.
  I never push or upload (`CLAUDE.md`).

## 7. Your part

Everything here is yours to do; I write the exact steps for each one when its turn comes, with the account and
window named, and you send a photo when it is done.

1. **Tailscale** (a private network of your own devices, encrypted between them, no port opened on your router):
   create an account on tailscale.com (the Personal plan is free for personal use; check the current terms when you
   sign up), install Tailscale on the PC and sign in, install the Tailscale app on the iPhone from the App Store
   and sign in with the same account, note the PC's name shown in Tailscale. Steps: `docs/PHONE-TAILSCALE-STEPS.md`,
   written with the 1.0.16 release.
2. **Keep the PC awake** (Windows Settings > System > Power: sleep "Never" when plugged in). JARVIS still starts
   about five minutes after you sign in (seen on 2026-10-06); a faster start is a separate decision of yours.
3. **Turn the switch on** in Settings > Devices once 1.0.16 is your everyday JARVIS and Tailscale runs on the PC.
4. **The Mac:** Xcode signed in with the Apple ID of your developer membership. Either the Xcode project you started
   in September (question Q1) or a new one from Xcode's App template, following my steps (about ten clicks: name,
   bundle identifier, SwiftUI, then drag the folder of files in). Build to your iPhone by cable first.
5. **TestFlight:** create the app record in App Store Connect with the same bundle identifier, upload the archive
   from Xcode, add yourself as an internal tester, install the TestFlight app on the iPhone and accept. Internal
   testing needs no Apple review; a build stays valid for 90 days, so later versions are uploaded the same way.
6. **Pair:** on the PC, Settings > Devices, name "Jonny's iPhone" (or what you like), kind phone, PAIR A DEVICE, read
   the code; on the phone, type the PC's Tailscale name and the code. Tick microphone and speakers; tick "may save
   memories and tasks" if you approve D2.

## 8. The steps in order

| # | Who | What | Done when |
|---|---|---|---|
| 1 | You | Approve this plan (section 13) | the approval record is written |
| 2 | Claude | Build 1.0.16 items 1 to 4 of section 5, tests, one reviewer per item, findings applied, release notes, `docs/PHONE-CORE-1.0.16.md` | committed |
| 3 | Claude | Build, comparison with 1.0.15, regression, zip install, sandbox Stage 7 with the version 3 scripts | all PASS, recorded |
| 4 | You | Approve the Stage 7 check of 1.0.16 (`docs/STAGE7-CHECK-1.0.16.md`), run it in the VM as for 1.0.15 | `STAGE_7_COMPLETE` |
| 5 | You | Approve and run the update of your everyday JARVIS to 1.0.16 (plan as for 1.0.15) | `EVERYDAY_UPDATE_COMPLETE` |
| 6 | You | Tailscale on the PC and the iPhone (section 7, step 1); PC kept awake; the switch on | a photo of Settings > Devices showing the address |
| 7 | Claude | The app: `phone/ios/`, one reviewer, the zip on D: (or the folder for your repository), the Mac steps | committed; zip hash recorded |
| 8 | You | Build on the Mac, fix rounds with me, install by cable, then TestFlight | the app opens on the iPhone |
| 9 | You | Pair (section 7, step 6) and run the checks of section 10, at home and away | all checks seen |
| 10 | Claude | Record the result (`docs/PHONE-V1-RESULT.md`), update the status, list version 2 for your decision | committed |

Steps 2 to 3 and step 7 can overlap: the app can be written while the release waits for your VM time. Nothing of
step 7 can be tried against your JARVIS before step 5 and step 6.

**Time, roughly:** the Core release two long sessions plus the checks; the app three to four sessions including
the fix rounds; your parts a few hours spread over the days (the VM check about two hours, the update about half an
hour, Tailscale and the Mac an hour or two). Said plainly: about a week if we both have the time, longer if not.

## 9. Decisions for you, with my recommendation

Approving the plan accepts the recommended answers unless you write otherwise.

- **D1. How the phone reaches the Core.** *Recommended: A.*
  - **A. The Core's device door on the PC's Tailscale address.** Tailscale encrypts everything between your two
    devices; inside that tunnel the Core speaks plain HTTP, as it does on the PC today. The phone app carries one
    line that allows plain HTTP to your PC's Tailscale name and nothing else. Fewest moving parts.
  - **B. The device door stays on the PC only, and Tailscale publishes it.** One Tailscale command on the PC
    ("serve") shows the door to your other devices as HTTPS with a real certificate. A padlock on the phone and
    nothing listening outside the PC itself, at the price of one more thing to set up and keep running (HTTPS
    enabled in the Tailscale admin page, the serve command on the PC). Can be moved to later.
- **D2. Your phone may save memories and tasks.** *Recommended: yes*, as a tick you set for your own phone (off for
  every new device). Without it, "remember this" from the phone is not remembered, which contradicts ONE MEMORY
  for your own device. Everything owner-only stays out of reach either way.
- **D3. Replies appear while being written, on the phone.** *Recommended: no in version 1.* Whole replies, spoken
  when complete. The PC's own streaming is off by default and untested with the real provider
  (`docs/REPLY-STREAM.md`); on cellular it also costs more. Version 2 if you want it.
- **D4. Minimum iOS: 18.** *Recommended.* Your iPhone 15 runs the current iOS; 18 keeps the app on well-trodden
  interfaces. (Question Q2 confirms your version.)
- **D5. How the code reaches the Mac.** *Recommended: the zip on D: moved by you* (AirDrop or iCloud Drive). A private
  GitHub repository you create and push to yourself works too, and becomes the better path if there are many
  rounds; your call at any time.
- **D6. Order of releases.** *Recommended:* the phone release 1.0.16 first, the installer (`JARVIS-Setup.exe`) after
  it.
- **Q1.** Does the Xcode project you started in September (app name JARVIS, Teague Industries bundle identifier,
  master document section 8) still exist on your Mac? Yes: I write the files for it. No or unsure: I give the steps
  for a new one.
- **Q2.** Which iOS version is on your iPhone? (Settings > General > About > iOS Version.)

## 10. Version 1 is done when (checks you see, recorded by me)

1. Away from home, Wi-Fi off, cellular on: a typed question is answered.
2. Hold to speak: your words appear as text, are answered, and the reply is spoken in JARVIS's voice.
3. Close and reopen the app: still paired; the conversation continues.
4. Chats lists the phone's conversations with their last lines; search finds one.
5. Status shows live CPU, memory and storage from the PC, Core version 1.0.16, the measured round trip, and the
   emergency stop state.
6. STOP on the phone: the PC's JARVIS stops and its banner names the phone; the phone cannot resume; RESUME on the PC
   restores both.
7. REVOKE on the PC: the phone's next request is refused with "pair again"; pairing again works.
8. The switch off on the PC, or Tailscale off on the phone: the phone says the Core cannot be reached; nothing else
   answers.
9. With the D2 tick: "remember ..." from the phone is known on the PC; without the tick it is refused with a plain
   sentence.
10. Throughout: the desktop JARVIS works as before, the activity log on the PC names the phone, and Settings > Devices
    shows it as connected with its last-seen time.
11. Said plainly in the result record: what was checked on cellular, what only on Wi-Fi, and any fix round on the Mac.

## 11. Version 2 (later, each on your word)

Camera and photos ("look at this"), the PC's chats on the phone, replies appearing while written, Siri shortcut,
notifications, the Dynamic Island, pairing by QR code, HTTPS through Tailscale (D1 option B), the Halo glasses with
the phone as their bridge, a faster start of JARVIS at sign-in, the always-on mini PC question.

## 12. Limits, risks and costs

- **The PC must be on, awake and signed in**, with JARVIS running. Away from home that is the whole risk of version 1:
  if the PC sleeps, restarts or JARVIS stops, the phone says the Core cannot be reached. A mini PC later would change
  that (your decision).
- **The phone's speech recognition runs on the PC** (Whisper), as for every device; your cloud choice in Settings >
  AI applies to the PC's microphone only (`docs/SPEECH.md`). Speech recognition for a device is not blocked by the
  emergency stop today; the question that follows is. 1.0.16 will refuse it too while the stop holds.
- **Data on cellular, roughly:** a 20-second voice command about 1 MB; a spoken reply a few hundred kilobytes; a
  text question a few kilobytes. The Core's limit per request is 3 MB and 30 seconds of speech.
- **Costs:** none new. Tailscale's Personal plan is free for personal use (check the current terms); your Apple
  Developer membership is paid; AI and voice usage is the same as from the PC.
- **I cannot build the app here**; the fix rounds on the Mac are the main uncertainty in time. The Core side is
  fully tested on the PC.
- **A phone that is lost or stolen:** REVOKE on the PC (or REMOVE FROM LIST) locks it out at once; the key is in the
  iPhone Keychain behind the phone's lock; Tailscale lets you remove the phone from your network too.
- **What Tailscale sees:** who is in your network and that your devices talk, not what they say (the connection is
  encrypted between your PC and your phone). Their service is not JARVIS's provider and gets no question or answer.
- **Security in one paragraph.** Only devices signed into your Tailscale account can reach the PC's private address.
  On that address the Core answers only the device routes, and each request needs the phone's own key, which the
  PC can refuse at any time. Your own routes (settings, permissions, resume, keys) are reachable from the PC alone.
  The emergency stop reaches everything and resume reaches nothing from the phone. Nothing of this is on the public
  internet and no port is forwarded on your router.

## 13. Approval

What you accept by approving: the plan as written, the recommended answers of section 9 unless you write others,
and that Claude builds section 5 in the repo (the switch off) and writes the app under standing authority. You do not
accept, and Claude does not do: turning the switch on, installing Tailscale, any Stage 7 check, any update of your
everyday JARVIS, any push or upload, or anything else in the owner-only list; each of those stays a separate act of
yours, as before.

Record on approval: `../governance/PHONE-PLAN-APPROVAL-RECORD.json` (your exact words, the clock time, the sha256 of
this file, the repo commit), and a line in `docs/CURRENT-STATUS.md`.

To approve, type exactly:

```
I approve the phone plan
```

With changes: write them in the same message (for example "I approve the phone plan, D1 is B, Q1 yes, Q2 iOS 26").
