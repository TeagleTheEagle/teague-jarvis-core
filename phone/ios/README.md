# JARVIS for iPhone, version 1: building it on the Mac

The app is the folder `JARVIS/` beside this file: twelve Swift files, nothing else. It is a client of the one JARVIS
Core on the owner's PC (release 1.0.16 or later, with the Private network switch on, over Tailscale). It is not part
of the Windows release. There is no Swift compiler for iPhone apps on the PC, so the app is built on the Mac; expect
a fix round or two (section 5).

## 1. What you need

- A Mac with Xcode 16 or newer signed in with the Apple ID of your Apple Developer membership (Xcode > Settings >
  Accounts).
- The iPhone (iOS 18 or newer; yours is iOS 26), a cable, and "Developer Mode" on the phone (iPhone Settings >
  Privacy & Security > Developer Mode; the phone restarts).
- This folder on the Mac (the zip from `D:\JARVIS-release-work\phone\`, moved by AirDrop, a USB stick or iCloud
  Drive, then unzipped).

## 2. Make the project (about ten clicks)

1. Xcode > File > New > Project. Choose **iOS** > **App**, Next.
2. Product Name: `JARVIS`. Team: your team. Organization Identifier: something of yours, for example
   `com.teagueindustries` (the bundle identifier becomes `com.teagueindustries.JARVIS`; keep it, TestFlight needs the
   same one later). Interface: **SwiftUI**. Language: **Swift**. Testing System: None. Storage: None. Next, pick a
   folder, Create.
3. In the project navigator (left), delete the two files the template made inside the `JARVIS` group:
   `JARVISApp.swift` and `ContentView.swift` (Move to Trash). Keep `Assets.xcassets`.
4. In Finder, open the unzipped folder and select the twelve files inside `JARVIS/`. Drag them onto the `JARVIS`
   group in Xcode's navigator. In the sheet: tick **Copy items into destination**, tick the `JARVIS` target, Finish.
5. Select the project (the blue icon at the top of the navigator), then the `JARVIS` **target**, and set:
   - **General > Minimum Deployments:** iOS 18.0.
   - **General > Supported Destinations:** iPhone only (remove iPad and Mac if listed).
   - **Signing & Capabilities:** Automatically manage signing, your Team.
   - **Info** tab, Custom iOS Target Properties, add two rows with the + button:
     - `Privacy - Microphone Usage Description` (NSMicrophoneUsageDescription): `JARVIS records while you hold the
       microphone button and sends the recording to your own JARVIS PC.`
     - `App Transport Security Settings` (NSAppTransportSecurity), a dictionary; inside it `Allow Arbitrary Loads`
       (NSAllowsArbitraryLoads) = **YES**. (The Core's door is plain HTTP inside your Tailscale network, decision D1 of
       the phone plan; without this row iOS refuses the connection.)
   - **Build Settings** (All, not Basic; search by name). **These three are required, not optional:** the audio code
     calls back from the audio thread and is written for the classic rules.
     - `Swift Language Version` = **Swift 5**.
     - `Default Actor Isolation` = **nonisolated** (the setting is new in Xcode 26; its default there, MainActor,
       would make the audio code fail to build).
     - `Strict Concurrency Checking` = **Minimal**.
6. Product > Build (Command-B). It should build with warnings at most (an unused result or two). If it does not:
   section 5.

## 3. First run on the iPhone, by cable

1. Plug the phone in, unlock it, trust the Mac if asked. In Xcode's toolbar choose your iPhone as the destination.
2. Product > Run (Command-R). The first time, the phone shows "Untrusted Developer": iPhone Settings > General > VPN &
   Device Management > your Apple ID > Trust. Run again.
3. The app opens on its pairing screen. Before pairing, the PC side must be ready (docs/PHONE-TAILSCALE-STEPS.md):
   1.0.16 installed, Tailscale running on the PC and the phone, the Private network switch on in Settings > Devices.
4. On the PC: Settings > Devices, name `Jonny's iPhone`, kind phone, PAIR A DEVICE, read the eight digits. On the
   phone: the PC's Tailscale name (as the Devices panel shows it) or its 100.x address, port 8790, the code, PAIR.
   On the PC, tick microphone and speakers for the phone, and "May save memories and tasks" if you want that.

## 4. TestFlight (so the app stays on the phone without the cable)

1. appstoreconnect.apple.com > Apps > + > New App: platform iOS, name JARVIS (or any), primary language, bundle ID
   the one from step 2.2, SKU anything. Create.
2. Xcode: choose "Any iOS Device (arm64)" as the destination, Product > Archive. In the Organizer window: Distribute
   App > TestFlight Internal Only (or App Store Connect > Upload) > Upload.
3. App Store Connect > your app > TestFlight: when the build has processed (minutes), add yourself as an internal
   tester (Internal Testing > + group > add your Apple ID).
4. On the phone: install the TestFlight app from the App Store, open the invitation, Install. A build stays valid for
   90 days; a newer version is uploaded the same way and TestFlight updates it.

## 5. If it does not build, or something is wrong on the phone

Send me the error text (copy from Xcode's issue navigator, the triangle icon on the left) or a photo of it, and say
which file and line. I fix the file and you drag the new copy in (replace). This is the plan's known cost: two or
three rounds are normal for code written without a compiler.

Two things to look at on the phone and tell me about, because they cannot be judged from here: whether the tab bar
at the bottom shows in the app's dark colours on iOS 26 (its new glass look may override them; harmless, just
different), and whether the hold-to-speak button records on the first hold (the microphone question is asked when
the Ask screen first opens; answer Allow).

## 6. What the app does, in one paragraph

Ask: hold the microphone to speak (the recording goes to the PC, which turns it into text), or type; the answer comes
from the PC and is spoken in JARVIS's voice (made on the PC, played on the phone). Chats: the phone's own
conversations as the PC keeps them, searchable; one can be continued. Status: the pairing and the link, the PC's
health as the dashboard shows it, open tasks, projects and the day's reminders. STOP ALL on every screen raises the
emergency stop on the PC; only RESUME on the PC lifts it. The phone's key lives in its Keychain; the Core's address in
the app's settings; nothing else is stored on the phone.

## 7. The look of 2026-10-06 (badge logo, space background, orbital graphic)

On the owner's "apply the look" (2026-10-06), after the first build ran on the phone: the header logo is the Teague
Industries badge (image set `TeagueBadge`, from `phone/ios/assets/TeagueBadge.png`), every screen has the space scene
faint behind it (image set `JARVISBackground`, from `phone/ios/assets/JARVISBackground.jpeg`), and the pairing screen
shows a slowly turning orbital graphic. The two image sets are added in Xcode's Assets by hand (the asset catalog lives
in the Xcode project on the Mac, not in this folder); the app runs without them, with the drawn T mark and the plain
ground. The app icon is `phone/ios/AppIcon-1024.png` (Assets > AppIcon). Steps for the Mac: `README-look.md`.
