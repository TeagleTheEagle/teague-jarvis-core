# JARVIS

Local personal assistant with a cyan command centre inspired by your two reference images. OpenRouter supplies AI conversation, vision and web search, with Qwen models only (the owner's rule); Fish Audio supplies speech. Groq, Gemini and ElevenLabs were removed in 1.0.15; OpenAI, Qwen through Alibaba Cloud and Brave Search on 2026-10-13.

## Launch

Double-click **Start JARVIS.cmd**. Open **http://127.0.0.1:8765** if a window is already running. Double-click **Stop JARVIS.cmd** to stop the backend. Closing the browser alone leaves the backend running.

The launcher prefers `.venv/Scripts/python.exe`, then this computer's bundled Codex Python, then `python` on PATH. It opens a desktop-style Edge window when available. This is a Python/browser app, not a packaged Electron executable.

For another Windows computer, use **Python 3.12 x64** (validated: 3.12.10
in the clean VM and 3.12.14 on the existing host). Python 3.11.9 reproduced
a wearable cancellation failure; it is not a supported Windows validation
baseline. Use the explicit setup path below, not a developer-machine runtime:

```powershell
.\Setup-Windows.ps1 -LocalVoice -Tests -CheckOnly
.\Setup-Windows.ps1 -LocalVoice -Tests
```

Node.js 24.x is required for JS-backed regressions and desktop source tooling;
packaged Electron includes its own Node runtime. Local STT additionally requires
Microsoft Visual C++ x64 Redistributable and the pinned local-voice requirements.
Test dependencies are separate in `requirements-test.txt`; omit `-Tests` on a
runtime-only setup. Setup never starts JARVIS or reads/copies `.env`.
See [Windows deployment prerequisites](docs/WINDOWS-DEPLOYMENT-PREREQUISITES.md)
for prerequisites, model provisioning, validation and packaged-release limits.

## API configuration

Your supplied credentials are saved in **.env**, ignored by Git and never served to the browser. Do not share this file or your `data/` directory. The `.env.example` file contains placeholders only. Restart JARVIS after changing configuration.

| Service | Status |
|---|---|
| AI chat and vision | OpenRouter (`OPENROUTER_API_KEY`); optional `OPENROUTER_MODEL` and related lines, Qwen models only |
| Fish Audio | Connected; audio generation succeeded after API credit was added |
| Speech recognition | Local Whisper on this PC; no key needed; recording requires microphone permission. Optionally OpenRouter instead, when `OPENROUTER_STT_MODEL` names a Qwen speech model (Settings > AI > Speech recognition; docs/SPEECH.md) |
| Spotify | Optional; needs Client ID and browser sign-in |
| YouTube search | Optional; needs YouTube API key; pasted URLs need no key |
| Web search | OpenRouter web search with `OPENROUTER_API_KEY`; otherwise SerpApi (`SERPAPI_API_KEY`) or best-effort DuckDuckGo results |

Fish voice reference: `14129c3e320149449d6bada6862f7338`. The synthesis model is `s2-pro`. Fish Audio is the only cloud voice; without it the browser's own voice speaks. A configured badge indicates credentials are present, not guaranteed connectivity or quota.

## Controls

- Type into Communications; Enter sends, Shift+Enter inserts a newline.
- Click **VOICE OFF** to turn spoken replies on. Text remains visible if speech fails.
- Click **ENABLE MIC** or press F4 to begin listening; grant browser permission. Escape stops the interaction.
- Always-on listening starts on page load. Say **Hey Jarvis**, followed by your command, then pause. Wake detection and transcription run locally; only the transcribed text of an activated command goes to the AI provider. (Since 1.0.15 you can choose, in Settings > AI > Speech recognition, to have the chosen AI provider turn your speech into text instead; then the recording of each command is sent to that company. Off unless you choose it; wake detection always stays local.) Say **Hey Jarvis** during a reply to interrupt. Mute, Stop, or Escape turns the mic off. Browser microphone permission is required.
- Commands end after about 1.3 seconds of silence and are capped at 30 seconds. An empty wake activation expires after seven seconds. See [Voice and memory](VOICE-AND-MEMORY.md) for setup, memory commands, and limitations.
- Use Memory to add/edit/delete saved facts and notes. No automatic extraction of personal facts occurs.
- Use Files to upload documents and create PDF, Word, Markdown or text files. Generated files stay under `data/generated/` and never silently overwrite another file.
- Share my screen captures one browser-approved screen/window frame, stops screen sharing immediately, and attaches it for your next question.
- App launching is limited to Calculator, Notepad and Paint and requires a two-minute, single-use approval. No arbitrary shell or mouse/keyboard automation is exposed.
- YouTube URLs load an embedded player. Use its own play/pause/volume controls. Some videos disallow embedding.
- Spotify uses PKCE, so no client secret is needed. Register the exact callback in `.env.example`, add `SPOTIFY_CLIENT_ID`, restart, and connect from Settings. Tokens stay in RAM; reconnect after restarting. Playback needs an eligible account and active device.

Try these commands:

```text
Remember I prefer short answers.
Note: review the prototype tomorrow.
Add task test the microphone.
Set a timer for 5 minutes.
What time is it?
Search for the latest space news.
Open calculator.
Create a PDF with a checklist for my next project.
Spotify pause.
```

## Persistence and limits

SQLite stores conversations, memory, notes, tasks, one-time timers and preferences under `data/`. Timers become due when the app polls while the backend runs; overdue timers appear after restart. Alerts remain until dismissed and can reappear on a new browser session. Recurring calendar reminders and operating-system notifications are not included.

Chat context uses up to 12 recent messages / 12,000 characters and selects relevant saved facts locally. Older messages remain in the database. The current version deliberately avoids silent automatic memory extraction and external embeddings; those can be added later with explicit privacy controls.

Uploads: 8 MB, 30,000 extracted characters, first 80 PDF pages. Scanned PDFs require OCR, not included. Images are resized to 1600 pixels. Attachments remain in memory (at most ten), persist across follow-up questions in the current interface, and expire when the backend restarts. Remove an attachment to stop supplying it as context.

One run executes at a time. Tool loops are bounded. Cancellation prevents subsequent actions, but an in-flight provider request can take up to its network timeout to return, and completed external effects cannot be undone.

## Source and verification

- `server.py`: authenticated loopback API, runs, approvals, uploads/downloads.
- `providers.py`: OpenRouter, Fish, Spotify PKCE.
- `actions.py`: tool schemas, commands, document handling, search and YouTube.
- `store.py`: transactional SQLite, initial schema migration version 1.
- `personality.txt`: editable assistant behavior.
- `static/`: interface, no build step.
- `test_jarvis.py`: offline tests.

Run `python -m unittest -v`. The test suite covers persistence, approval expiry/replay/denial, cancellation, credential non-disclosure, cross-origin access, file confinement and document round-trips. External services and real application launches are mocked.

Original build (before 1.0.15 removed Groq): live Groq text and Fish audio generation were tested. The browser rendered and completed a real chat response without console errors. Vision testing returned HTTP 429. Microphone device capture, Spotify and YouTube playback still depend on browser/device/account permissions.

The PDFs were reference material. Fragile recipes were replaced with structured document parsing, explicit microphone/screen consent, scoped launches, transactional storage and a single Groq key. No additional accounts, quota-evading key rotation, antivirus changes, or guide-suggested plugin installations were performed. Activity rings represent assistant state, not CPU/network telemetry.

This app binds only to localhost and is intended for one local user. Do not publish it as a public service without additional hardening.

Provider references: [OpenRouter API](https://openrouter.ai/docs/api-reference/overview), [Fish Audio](https://docs.fish.audio/api-reference/endpoint/openapi-v1/text-to-speech), [Spotify PKCE](https://developer.spotify.com/documentation/web-api/tutorials/code-pkce-flow).

Provider 429 handling: a temporary rate limit is reported as temporary, and for OpenRouter it pauses voice commands for 30 seconds. A billing or credit refusal (OpenRouter's HTTP 402) is reported as such, names the provider and sets no pause, because waiting will not help. Identical tool calls cannot repeat within one run. This does not increase your provider quota.
# Backup and recovery

Use **Settings → Backup & recovery** for verified local backups and restoration into a separate folder. This preserves the complete saved database and saved data folders; the older export/import flow is not a full recovery mechanism. See [RECOVERY.md](RECOVERY.md) for exclusions, CLI recovery and validation limits.
