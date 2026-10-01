# JARVIS Desktop — screen assistance

Run `../Start-Desktop.ps1` or double-click `../Start JARVIS Desktop.cmd` in File Explorer. This preview uses the existing Python environment and web interface. The browser version remains available.

## Everyday use
1. Enable Mic and say “Hey Jarvis”.
2. Switch to the app you want help with on your primary display.
3. Say “analyse my screen” or “take a screenshot, Jarvis”. JARVIS captures one image, submits it for analysis, and puts the text response in Communications.
4. Say “show hologram” for the floating companion, or use FLOAT JARVIS / the tray Floating JARVIS control. The companion renders the hologram locally with requestAnimationFrame, receiving compact measured speech-level, waveform and status updates every 50 ms; it has Analyse Screen, microphone, Open and Stop All controls.
5. Say “thank you Jarvis” to end the conversation. A new wake word starts another conversation.

Use Screen Vision → Start Live Screen Sharing for a local primary-display session. JARVIS samples changed frames at a controlled rate and sends only those submitted frames to the configured vision provider. Capture Only remains available for a local preview with no model submission. Text responses are saved in Communications, not automatically added as permanent memory.

Minimising leaves the microphone available. Closing to tray stops activity. Tray Quit shuts down only the desktop's owned Python backend. Avoid enabling both browser and desktop microphones simultaneously.

## Permission and stop controls
At the user's explicit request, `requestedPrimaryDisplayScreenshots` is enabled in `preferences.json`. This means an explicit screenshot command uses the primary display without repeated source selection. It does not start continuous capture, at launch or any other time. Uncheck “Use my primary display…” in Screen Vision to choose a display manually. The preference is persisted; the selected display and screenshots are not.

Stop & Discard or “stop sharing” cancels pending capture/analysis and clears the preview. Stop All or the tray Stop activity also cancels assistant requests, stops speech and disables the microphone. The default global emergency shortcut is Ctrl+Alt+Shift+X; change `emergencyStopShortcut` in preferences.json and restart to customise it. If registration fails, the app reports that failure and the tray stop control remains available. A new explicit screenshot request can enable requested capture again using the saved preference.

A monitor removal or scaling change revokes the current source. A fresh request re-establishes it. The bridge checks the sender and main frame, exposes only defined actions, and never exposes Node.js or credentials to the renderer.

## Privacy and limitations
Capture uses Electron desktopCapturer. Windows display thumbnails may be generated in local memory for all displays; only the requested display's image is returned to the interface. The companion hides during capture. Images are limited to a 1920×1080 bounding box and preserve aspect ratio. Protected windows may produce black or unavailable content.

Live sharing is a local preview with sampled analysis, not unrestricted computer control. JARVIS does not click, type, or execute instructions found on screen. Analysis uses the configured vision provider; the UI identifies that provider when submitting. Provider retention policies apply. Existing speech provider calls are unchanged.

Screenshot previews and upload-cache entries are discarded after analysis or Stop. Submitted screenshot attachments are single-use; image content is not written to conversation history or local image files. Ordinary conversation text and analysis notes follow existing JARVIS retention. A request already sent to an external provider cannot be recalled.

No arbitrary clicking, shell bridge, or unrestricted file/account access has been added. Existing assistant tools and their approval rules remain. Instructions inside screenshots remain untrusted; screenshot analysis cannot execute tools. Credentials still use the existing server configuration; Windows secure storage migration remains outstanding. Run `..\Install-JARVIS-Shortcuts.ps1` to create a desktop shortcut and an optional Windows login shortcut; remove those two `.lnk` files to roll that back. This is a source-mode preview, not a signed installer with updates.

## Validation and remaining live checks
- `node --test desktop/test/*.test.cjs`: backend authentication, native-import preparation regression, shutdown, capture authority, stop/cancellation, overlapping requests, display topology/scaling changes and recoverable capture errors. Hardware variations in these unit tests are simulated.
- `node test_screen_vision.cjs` and `node test_screen_intent.cjs`: browser capture regression and command routing.
- `.venv/Scripts/python.exe -m unittest test_screen_observation.py`: image submission with mocked provider, single-use cleanup, text-only history and rejecting tools from screenshot analysis.
- `electron . --smoke-test` in this folder: actual Windows screenshot to memory, renderer preview/discard, isolated preload, floating companion and lifecycle. Saves only metadata to smoke-result.json and an image of the companion UI to companion-test.png; it never submits screen images to a cloud model.

Actual microphone/wake/conversation/end phrase was confirmed by the user before this change. Real Windows capture, floating state mirroring and Stop were checked during development. Live AI screenshot analysis, voice screenshot commands from another app, physical emergency-key activation, multiple physical monitors and non-default Windows scaling still need user validation. No resource-use or API-cost benchmarks are claimed.

## Setup and rollback
Pinned Electron: 44.2.0. With Node and pnpm available, run `pnpm install --frozen-lockfile` here, then `node node_modules/electron/install.js` if dependency build scripts were disabled. Launch with ELECTRON_RUN_AS_NODE unset (the supplied launcher handles this).

Quit Desktop and use the existing browser launcher for rollback. To uninstall this source preview, quit first, then remove the desktop folder and the two desktop launchers. Preserve the main JARVIS data and configuration. Electron may create a jarvis-desktop application-cache folder in the user profile; inspect before removing it. There is no startup registration, installer or updater to unregister.

## Floating animation performance
The former PNG mirror updated at 4 Hz. It has been replaced with local canvas animation and compact numeric updates. A roughly two-second Windows test with the main window minimised measured 54.3 drawn frames per second. This is a short local measurement, not a guaranteed frame rate. Reduced-motion preferences are respected; stale speech data decays to silence. `electron . --animation-test` checks this without screen capture or microphone access and records animation-result.json.
