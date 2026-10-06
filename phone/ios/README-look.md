# The look of 2026-10-06: your steps on the Mac (about five minutes)

This zip carries two changed Swift files, two pictures and the app icon. The app you built already stays; only
these parts change.

1. **The two pictures.** In Xcode's left pane click **Assets** (the blue folder icon `Assets`). In Finder open the
   unzipped folder `assets/` and drag **both** files, `TeagueBadge.png` and `JARVISBackground.jpeg`, into the list on
   the left of the Assets editor (the list that holds `AccentColor` and `AppIcon`). Xcode makes two image sets named
   `TeagueBadge` and `JARVISBackground`. The names must be exactly those: the code asks for them by name.
2. **The app icon**, if not done yet: click **AppIcon** in that list and drag `AppIcon-1024.png` onto the big empty
   square.
3. **The two Swift files.** In Finder open `JARVIS/` from the zip and drag `Theme.swift` and `PairingView.swift` onto
   the `JARVIS` group in Xcode's navigator (the yellow folder that holds the twelve files). Xcode asks whether to
   replace: **Replace**. If it offers a sheet instead, tick Copy items into destination and the JARVIS target.
4. Command-B, then Product > Run with the phone plugged in and unlocked.

What you should see: the badge in a ring at the top left of every screen, the space scene faint behind everything,
and a slowly turning orbital graphic on the pairing screen. If the badge does not show, the image set is not named
`TeagueBadge`; if the background does not show, it is not named `JARVISBackground` (the app runs all the same).

If the build fails, send a photo of the red lines in the issue navigator (the triangle icon, Command-5).
