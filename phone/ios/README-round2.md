# Round 2 of 2026-10-06: your steps on the Mac (about ten minutes)

This zip carries all thirteen Swift files of the app (twelve replaced, one new: `SiriIntents.swift`) and the app
icon's catalog folder. What is new on the phone afterwards: the conversation comes back after a relaunch, the header
fits the phone's width, the stop note clears after RESUME, Bluetooth headsets work for the microphone and the reply,
the screen stays awake while JARVIS listens, thinks or speaks, a Voice button on the Ask screen, a short vibration
when the reply is in, "Lock with Face ID" in the phone settings, and Siri: "Hey Siri, ask JARVIS" and "Hey Siri,
stop JARVIS".

## 1. The Swift files (the same drag as before, plus one new file)

1. In Finder open the unzipped folder `JARVIS-ios-round2/JARVIS/` and select **all thirteen** files.
2. Drag them onto the yellow `JARVIS` group in Xcode's navigator (the group that holds the app's Swift files, not
   onto Assets).
3. Xcode asks about the twelve that exist already: choose **Replace** (for each, or "Apply to all"). For the new file
   `SiriIntents.swift` it may show the sheet instead: tick **Copy items into destination** and the `JARVIS` target,
   Finish.
4. Check the navigator: exactly one `SiriIntents.swift`, and no file named like `SessionModel 2.swift`. (If a "2"
   copy appeared, delete the one without the "2" and rename the "2" one, or delete the "2" and drag again with
   Replace.)

## 2. The Face ID entry (required before the lock is switched on)

Select the project (blue icon), the `JARVIS` **target**, the **Info** tab, Custom iOS Target Properties, the + button:

- `Privacy - Face ID Usage Description` (NSFaceIDUsageDescription): `JARVIS can lock its screens behind Face ID.`

Without this entry iOS ends the app at the first Face ID prompt, the same way the missing microphone entry did on
2026-10-06. The lock is **off** until you turn it on in the app (Ask screen > the menu icon > "Lock with Face ID"), so
the app runs either way; just add the entry first.

## 3. The app icon (still the placeholder grid on the phone)

The picture is right (1024 x 1024, no transparency); what is left is one of these three, in order:

1. In Xcode's navigator click **Assets**, then **AppIcon** in the list. The big square must show the badge. If it is
   empty, drag `AppIcon.appiconset/AppIcon-1024.png` from the zip onto that square.
2. Select the `JARVIS` target > **General** > "App Icons and Launch Screen" > **App Icon** must say `AppIcon`.
3. **Product > Clean Build Folder** (Shift-Command-K). On the phone, hold the JARVIS icon > Remove App > **Delete
   App**. Then Product > Run again from Xcode. iOS keeps the icon of an installed app, so the delete is the step that
   usually does it.

## 4. Build and run

Product > Build (Command-B): warnings at most. Plug the phone in, unlock it, Product > Run (Command-R). If anything is
red, send a photo of the issue navigator (the triangle icon, Command-5) with the file name and line.

## 5. What to check on the phone (tell me what you see)

1. **Check 3 again:** ask something, close the app fully (swipe it away), open it: the same conversation with its
   lines, not a fresh one.
2. **The header:** ONLINE on one line, STOP ALL readable, on every screen.
3. **The stop note:** STOP ALL on the phone, RESUME on the PC: the yellow line goes away by itself within seconds.
4. **Headset:** with AirPods or another Bluetooth headset connected, hold the microphone and speak; the reply plays in
   the headset. A headset with a microphone is kept on its call profile while it is connected, so the reply is at
   call quality there (iOS's rule when an app can record); headphones without a microphone get stereo.
5. **Screen awake:** while JARVIS thinks or speaks the screen does not dim.
6. **Voice button:** the speaker icon beside the microphone mutes and unmutes the spoken reply; a short vibration when
   each reply arrives.
7. **Face ID:** after step 2, turn "Lock with Face ID" on in the phone settings (menu icon on Ask or Status). Close the
   app, open it: Face ID, then the screens. STOP ALL is on the lock screen without unlocking. Coming back within a
   minute asks nothing.
8. **Siri:** wait a minute after the first run (Siri learns the phrases when the app is installed), then say
   "Hey Siri, ask JARVIS". Siri asks "What should I ask JARVIS?"; say the question; the app opens and sends it; the reply
   is shown and spoken by the app in JARVIS's voice (not by Siri: the Core's answers take longer than Siri waits).
   "Hey Siri, stop JARVIS" raises the emergency stop without opening the app; RESUME is on the PC as always. If Siri
   does not know the phrase, open the Shortcuts app: the two JARVIS shortcuts are listed under the app; running one
   there once also teaches Siri.

## 6. Not in this round, said plainly

Replies appearing word by word as they are written cannot be done in the app alone: the Core keeps a device's answer
whole and sends it checked and finished (server.py, "not for another device's question"). It needs a Core release;
listed for the owner's decision.
