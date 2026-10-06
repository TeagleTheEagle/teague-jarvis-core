# Teague Industries — JARVIS iOS interface

A SwiftUI implementation of the supplied JARVIS pairing interface.

## Included
- Dark orbital/space visual language
- Teague Industries branding
- Animated holographic orbital graphic
- Tailscale address + port fields
- 8-digit pairing code field
- Pair button validation
- Privacy copy from the supplied design
- Supplied orbital background and Teague logo assets

## Open
Create a new iOS App project in Xcode using SwiftUI, then replace the generated Swift files with the files in `TeagueJARVIS/` and add the two image sets from `Assets.xcassets`.

The current `PAIR` action is UI-only. A production build should connect it to the JARVIS Core pairing endpoint, validate the returned credential, and store the resulting key in iOS Keychain.
