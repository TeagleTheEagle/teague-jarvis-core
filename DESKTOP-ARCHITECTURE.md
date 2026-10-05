# JARVIS Windows companion: inspection and implementation plan

Status: architecture inspection completed on 8 September 2026. Desktop implementation is proposed, not built or tested. No application code, credentials, startup behaviour or permissions changed during this inspection.

## Recommendation

Use Electron as a thin Windows shell around the existing Python service and HTML/JavaScript interface. Keep the browser launcher and configuration working independently. This is an engineering judgement based on reuse, not a measured performance comparison.

| Approach | Fit | Trade-offs |
| --- | --- | --- |
| Electron | Recommended | Reuses browser AudioWorklet, canvas, UI and JS routing with a bundled Chromium runtime. Provides desktop windows, tray, shortcuts and capture APIs. Larger runtime and responsibility for Chromium/Electron updates. |
| Tauri | Viable alternative | Reuses web UI and supports narrow capabilities, but introduces Rust integration plus Python packaging and depends on Windows WebView2. Audio and capture integration need separate validation. |
| Native Windows + WebView2 | Viable, more integration work | Strong Windows integration but needs a new native host and bridge, while retaining Python and web audio. A full native UI rewrite offers little benefit for this first version. |

Node is available in this session; npm, cargo and dotnet did not resolve on PATH. That is not proof they are absent from the machine. No desktop framework project was found in the inspected source.

## Current architecture and reusable components

- `server.py`: Python standard-library HTTP server bound to 127.0.0.1, background runs, event polling, cancellation, authenticated local requests, tool execution and upload handling.
- `static/index.html`, `app.js`, `pro.css`: existing interface, canvas hologram, voice controls, navigation and diagnostics. No UI framework rewrite required.
- `static/voice.js`, `mic-worklet.js`, `wake.py`, `local_stt.py`: browser microphone capture, local wake detection and local Whisper base.en CPU-int8 transcription. Reuse the pipeline rather than introducing a second microphone owner.
- `voice_engine.py`, `providers.py`: existing speech synthesis and model adapters. Actual destination depends on configured provider and selected speech profile; a configured flag is not a connectivity test.
- `actions.py`, `store.py`: bounded tools, approval support, SQLite conversation and application data. Screen observations already withhold tools and reject returned tool calls.
- `desktop_launcher.py`: currently launches Python and opens Edge with --app. It has no tray, native companion bridge or global emergency-stop implementation.
- `build/JARVIS.spec`: existing PyInstaller recipe has machine-specific absolute paths and needs a portable packaging review.
- Existing README contains descriptions older than the current code. Update documentation against tested behaviour, not those historical claims.

## Gaps to resolve

Credentials currently load from `.env`. They are not served as frontend files, but they are not Windows-backed encrypted storage. Browser configuration must remain intact; desktop credential import must be explicit and never delete the original automatically.

Uploaded images stay in an in-memory dictionary capped at ten entries, until eviction or service restart. This is not immediate deletion. Desktop single-shot captures must be released on completion, failure, cancellation and expiry, including unused uploads. Audio caching in the synthesis engine needs a separate retention review before declaring a no-retention policy.

The browser currently includes periodic screen observations. The first desktop version must not start or expose that timer: desktop mode will use one capture per explicit command. Preserve browser behaviour separately.

Allowlisted app launches run immediately under earlier authorisation. Do not describe the existing app as requiring approval for every tool. Add no new consequential action bypasses. (Until release 1.0.15 supported styling and personality changes also ran immediately; since 1.0.15 every change JARVIS makes to itself asks first, and what each tool may do is one table: `permissions.py`, `docs/PERMISSIONS.md`.)

## First-version architecture

Electron main owns the window, tray, emergency shortcut, source authorisation, one-shot capture and encrypted credential store. A sandboxed renderer retains the current JARVIS interface with Node integration disabled and context isolation enabled. A small preload bridge exposes named operations only: open Screen Vision, request source selection, capture the authorised source once, cancel, and read desktop state. No arbitrary IPC channels, shell commands, filesystem paths or network URLs.

Validate IPC sender frame and expected origin. Block in-app navigation to external pages and deny unexpected permission requests. Third-party pages stay in the ordinary browser without a privileged bridge.

Run Python as a standard-user child process with a per-launch authenticated desktop connection. Retain current browser auth/Origin/Host checks. Do not trust a service merely because it answers on port 8765, and never terminate an unrelated listener. Establish backend identity before enabling desktop actions; manage only owned processes.

Use Windows-backed encryption for desktop secrets (Electron safeStorage uses DPAPI on Windows). Main-process credentials may be delivered to the owned Python child through a private channel, not command-line arguments, the renderer or logs. Do not fall back silently to plaintext storage if encryption is unavailable. Windows user-account protection is not protection against every process running as that same user.

## Capture and interaction contract

1. Opening Screen Vision does not authorise capture.
2. User selects and authorises one display or window in desktop setup/session UI, including permission to submit individual screenshots to the named configured vision provider.
3. “Analyse my screen” can request a one-shot capture through the native bridge while authorisation is valid. Verify the source still exists; never substitute another monitor silently.
4. Capture, upload accepted, processing and answer received are separate states. A displayed screenshot is not proof of model receipt. Invalid/blank capture is a failure, not an analysis result.
5. Drop image references after completion/cancellation; do not save screenshots to disk by default. Retain conversation text under the existing history policy, with an explicit deletion control and explanation of provider-side retention.
6. Stop revokes active capture authorisation, cancels pending work and stops speech/microphone processing. It cannot recall bytes already transmitted. Hotkey registration failure must be visible; tray/window stop controls remain usable.
7. No capture on restart or silent source restoration. Remembered preferences are not active authorisation. Changing monitors or restarting can require user selection again. Protected Windows screens and platform-mandated prompts remain respected.
8. One microphone owner. Closing the main window to tray must visibly communicate whether the mic remains enabled; quitting stops it. A question from JARVIS can invite an answer without a new wake word, but the end-conversation phrase remains effective.

## Reviewable phases and affected files

### 1. Desktop shell and ownership
New `desktop/package.json`, lockfile, `desktop/main.cjs`, `desktop/preload.cjs`, tray assets and launcher. Add a feature-detected desktop adapter in `static/desktop.js` and register it in the static file allowlist if served by Python. Add server desktop handshake/lifecycle support only as necessary. Window, tray, show/hide, quit, safe external links and startup-at-login OFF. No capture yet.

Validate bridge schema/sender rejection, unknown-origin navigation rejection, service identity, port conflict, crash/quit cleanup and browser regression tests.

### 2. Voice and emergency stop
Reuse `static/voice.js` and existing transcription/TTS. Add desktop state coordination and configurable global stop shortcut. Preserve mic selection and PTT; do not open a second mic in the hologram window.

Validate missing/denied/disconnected microphone, interruption, end phrase, sleep recovery, shortcut collision and stop during processing/speech. Separate provider playback events from user-confirmed audible sound.

### 3. Authorised single-shot vision
New `desktop/capture.cjs`; narrow capture commands in preload and desktop adapter. Modify `server.py` attachment lifecycle for desktop one-shot expiry and release. Make desktop routes exclude browser continuous-observation code. Show actual configured provider before submission. Retain existing no-tools screen analysis restriction.

Validate no capture before authorisation, source change/disconnect, cancellation at each stage, expired images, provider errors/missing vision model and denied permission. Synthetic tests are not proof of real Windows capture.

### 4. Secure storage, packaging and handoff
New desktop credential storage module and Python desktop credential-loading path. Explicit import workflow preserving browser `.env`. Pin dependencies; revise portable Python build recipe, document setup, rollback and uninstall. No unattended public auto-updater in the prototype.

Before public distribution: Windows code signing, trusted release publishing, signed-update verification, failure/rollback tests and a maintained Electron update policy.

## Validation and measurements

Run existing relevant Node/Python tests and new desktop tests for routing, IPC, authorisation, capture lifecycle and cancellation. Test on Windows as a standard user with the SteelSeries/Realtek input actually selected by the user.

Hardware checks: multiple monitors, unplug/reconnect, 100/125/150/200 percent scaling where available, negative monitor coordinates, minimised windows, sleep/lock and protected/blank frames. Mark unavailable hardware scenarios untested.

Measure capture-to-image, upload acknowledgement, model response and speech-start timings independently. Measure idle, listening and one-capture CPU/memory over documented intervals. Record input/output usage when the provider returns it; calculate cost only using verified applicable pricing and distinguish estimates from billed usage. No latency, resource or cost benchmarks were performed for this architecture report.

Rollback: launch the preserved browser version, remove the desktop package, and retain user data. Clean uninstall removes app binaries, shortcuts, tray registration, optional login entry and desktop encrypted secrets; ask separately before deleting conversation history or browser data. Document local/provider retention boundaries.

## Official references

- Electron security: https://www.electronjs.org/docs/latest/tutorial/security
- Electron desktop capture: https://www.electronjs.org/docs/latest/api/desktop-capturer
- Electron Windows secure storage: https://www.electronjs.org/docs/latest/api/safe-storage
- Electron updates: https://www.electronjs.org/docs/latest/tutorial/updates
- Tauri process model: https://v2.tauri.app/concept/process-model/
- Tauri capabilities: https://v2.tauri.app/security/capabilities/
- Windows screen capture: https://learn.microsoft.com/en-us/windows/apps/develop/media-authoring-processing/screen-capture
