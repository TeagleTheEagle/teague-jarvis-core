# Round 4: the JARVIS button on the lock screen and in Control Center (owner: "build 1", 2026-10-07)

The owner asked how to make JARVIS come up when the side button is held. Apple keeps that press for Siri, so the
nearest thing iOS allows is a control: a button the owner places in Control Center or on the lock screen (in place
of the torch or camera button) that opens JARVIS listening with one press. This record says what was built and how
it is used. CLAUDE.md's rules apply: the button holds no key and no logic; the Core on the PC does everything.

## 1. What changes

| Where | Change |
|---|---|
| New target `JARVISControls` | A widget extension (`JARVISControls/JARVISControls.swift`; its `Config/JARVISControls-Info.plist` names the widget extension point and lives outside the synchronized folder, or Xcode would both copy and generate it) with one control, "Ask JARVIS": a `ControlWidgetButton` whose intent opens `jarvis://listen`. Embedded in the app (Embed Foundation Extensions); bundle id `com.teagueindustries.jarvis.controls`. |
| URL scheme `jarvis` | `Config/JARVIS-Info.plist`, merged into the app's generated Info.plist: `jarvis://listen` starts hands-free listening, `jarvis://stop` raises the emergency stop. The same links work from Back Tap (Accessibility) or a Shortcut's "Open URL". |
| `SessionModel` | `handle(url:)`; `requestHandsFree()` keeps the press and `startPendingHandsFreeIfReady()` is the one place listening starts: when the scene is active, the lock is off and the Core's hello has answered (so the microphone allowance is known), which may be at once, after the unlock, or after the hello; a press older than two minutes, or one left when the phone goes to the background, is dropped unstarted. Hands-free listening ends at a pause of 1.3 s after speech, at a tap on the microphone, or at the 30 s limit; with no speech for 4 s it is dropped, not sent ("Nothing was heard…"). Speech is a level three times the recording's quietest buffer and never below 0.08, so a soft voice counts and a steady noise does not pause. `handsFree` and `askRequested` published. A hello landing mid-recording no longer flips the screen to standing by; a recording that was running when the lock closed ends and starts again after the unlock. |
| Also | A press while a question runs cancels it; a press while a question is held is refused with the held notice; a press while the stop holds says so (no recording); unpaired shows "This phone is not paired with JARVIS yet."; an unknown jarvis:// link shows a fixed sentence; the first press asks iOS's microphone permission; a press with the Core unreachable (after an earlier hello) records and the recording is held by hold-and-send. The microphone permission text now names the button. The version numbers live at the project level so the app and the extension always match. |
| Ask screen | While listening hands-free the hint reads "Speak; a pause sends, or tap the microphone · N s of 30". |
| `MainTabs` | Switches to Ask when a button or link asks for it; `onOpenURL` on the root view. |

## 2. How the owner adds the button (once, on the phone)

- Control Center: open it, hold an empty area or tap the + at the top left, "Add a Control", search "JARVIS", tap
  "Ask JARVIS".
- Lock screen: hold the lock screen, Customise, Lock Screen, tap the minus on the torch or camera button at the
  bottom, tap the + there, search "JARVIS", "Ask JARVIS", Done.

## 2b. What the first install taught (2026-10-07, 02:10 to 02:30)

The owner added the control: it was listed and drawn correctly, and a press did nothing. The first design asked
iOS to open `jarvis://listen` from the control (an intent returning `OpenURLIntent`); Control Center does not
honour that route. The fallback the review had lined up is now the design: `OpenJarvisListeningIntent` lives in
`JARVISShared/` (a folder in both targets), carries `openAppWhenRun`, and the system opens the app and performs it
there; it leaves a time-stamped request and posts a notification, and the session starts hands-free listening
through the same funnel as before (in front, unlocked, hello answered; two-minute limit). **Checked by the owner at
02:31: "yes it did" (the button opens the app); and end to end at about 13:20: "all good" (Face ID, the orb green
with LISTENING, a spoken question, the orb amber with THINKING, the reply spoken with a short vibration, the screen
on throughout; RESULTS.md).** The `jarvis://` scheme stays for Back Tap and Shortcuts.

## 3. What happens on a press

iOS opens the app at `jarvis://listen`. If the JARVIS lock is on, Face ID first (the emergency stop stays on the
lock screen as before), then listening starts; otherwise it starts as soon as the app is in front and the Core's
hello has answered. The orb turns green, the hint says a pause sends. The words go to the Core as a question like
any other; the reply is shown and spoken. Nothing is recorded until the app is in front and unlocked, nothing is
sent before the pause or the tap, and a recording with no speech in it is dropped.

## 4. Left out, said plainly

- A "Stop JARVIS" control: `jarvis://stop` exists for Back Tap or a Shortcut, but a stop button on the lock screen
  is too easy to press by accident; "Hey Siri, stop JARVIS" and STOP ALL in the app remain the ways to stop. Said
  plainly: any app or link on this phone can open `jarvis://stop` without a prompt (Safari asks first); the
  direction is fail-safe, only RESUME on the PC lifts it, and a stop link also cancels a question in progress.
- Whether the control opens the app is the one thing this round cannot prove from the Mac: the plumbing (an intent
  in the extension returning an `OpenURLIntent`) is one of iOS 18's documented routes, and the owner's first press
  is the check. If it does not open the app, the fallback is to make the intent a member of both targets with
  `openAppWhenRun`.
- The side button itself: not possible for any app.

## 5. Checks for this round

Independent review of 2026-10-07: 3 high, 4 medium, 7 low, all applied (high: the press failed on a cold launch
because the microphone allowance was checked before the hello answered; a hello mid-recording flipped the screen to
standing by; a press with the lock on could record behind the lock screen; medium: the no-speech give-up sent the
recording; a fixed speech level; a pending press that never expired; the Controls plumbing unverifiable from the
Mac; low: the App ID registration, the stop link, the stopped guard, the echoed link, the microphone text, the
version settings, this record). The signed build with the extension is signed under the owner's team: automatic
signing registered the extension's bundle id (com.teagueindustries.jarvis.controls) in the owner's Apple developer
account on the first signed build of 2026-10-07 about 01:55 (disclosed to the owner; certificates and profiles are
owner-only in CLAUDE.md). Installed from the Mac; the owner adds the control and presses it: the app opens
listening, a spoken question is answered. Recorded in RESULTS.md on the owner's word or screenshot.
