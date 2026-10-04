# Voice and memory

Enable the microphone, then say **“Hey Jarvis”**, followed by your command. Pause for about 1.3 seconds to send. The first use may take a little time to load the local model. Wait for **SAY “HEY JARVIS”**.

Say **“Hey Jarvis” during a reply** to interrupt and give another command. “Hey Jarvis, stop” cancels without submitting a new chat request. Mute, the Stop button, or Escape turns the microphone off. Always-on in Settings starts the microphone when this page opens; the page and local server must remain running, and browser microphone permission is required.

The microphone stays open using one audio stream. Wake detection runs locally through openWakeWord; the loopback server processes audio in memory without recording it to disk. After activation, a short rolling buffer and the command are sent to Groq for transcription. Silent activation expires after seven seconds, and commands are capped at thirty seconds. The wake phrase is **Hey Jarvis**, rather than bare Jarvis. Detection and speaker echo cancellation depend on microphone placement, accent, and background sound.

Only one JARVIS tab can own wake detection at a time. If another tab owns it, mute that tab first. A provider rate-limit cooldown blocks new voice commands while local wake listening remains available (a billing or credit refusal does not: waiting would not help). An interrupted provider request may need time to finish cancelling before the new command can run.

## Memory examples

- `Call me Alex` — saves and updates your preferred name.
- `Remember my favourite colour is cyan` — saves the fact; a later statement with the same “my … is” key updates it.
- `Project Website: finish the landing page next` — saves a named project in Memory Bank.
- `Update project Website: test the mobile layout next` — replaces that project's details.
- `Show projects` — lists saved projects.
- `Find memory for Website` — searches saved facts locally.
- `Replace memory: I like blue => I like cyan` — corrects one matching fact.
- `Forget memory: I like cyan` — deletes the exact saved fact.

Use Edit and Delete in Memory Bank for other corrections. Exact duplicate memories are merged. Relevant facts are selected by word matching, not semantic embeddings. General conversation is not automatically turned into durable memory. Deleting memory does not erase existing conversation history, which is stored separately. Project entries are saved summaries, not autonomous scheduled tasks.

Calendar and Spotify remain disconnected at your request.

## Installation and verification

The supplied `.venv` already has the wake dependency and the three models are in `data/wake-models`. For a fresh installation, install `requirements.txt` then run `python setup_wake.py`. The Windows launcher prefers `.venv/Scripts/python.exe`.

Run `python -m unittest -q` and `node test_voice.cjs` for offline regression checks. Synthetic speech verified the model separately; a live microphone check in your room is still needed.

Wake library: [openWakeWord](https://github.com/dscripka/openWakeWord), by David Scripka, Apache 2.0. Its pre-trained wake models are licensed CC BY-NC-SA 4.0; consult the linked project's model licensing for reuse.
