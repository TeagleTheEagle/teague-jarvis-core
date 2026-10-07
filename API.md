# Local API contract

Base: `http://127.0.0.1:8765`. Load `/` first for a random process-scoped HttpOnly SameSite session cookie. Keep cookies on API requests. POST bodies are JSON. Other hosts/origins are rejected. Serve a replacement interface from the same origin.

| Method | Route | Body/result |
|---|---|---|
| GET | `/api/state` | Capabilities, settings, items, timers, log, conversations, uptime; never keys |
| GET | `/api/history?conversation=ID` | Up to 100 chronological stored messages |
| POST | `/api/chat` | `{text, conversation, attachment?: uploadId}` returns `{run_id}` |
| GET | `/api/runs/ID/events?after=-1` | `{events, done}`, waits up to 10 seconds for new events |
| POST | `/api/cancel` | `{run_id}` |
| POST | `/api/settings` | Subset of `{name, voice, continuous, response_length, answer_mode, provider_backup, speech_recognition, offline_answers, reply_stream, tone, humor, speech_rate, wake_sensitivity, quiet_hours, briefing_time, proactive, voice_profile, music_volume, music_startup}` (music_startup: the nickname or file name of the song played after the greeting at a sign-in start, empty for none) |
| GET | `/api/music` | The music folder, its files, the nicknames, what is playing, the volume, and the start-up song (`startup`, `startup_present`) |
| POST | `/api/music` | `{action}` with `add {nickname, file}`, `remove {nickname}`, `play {query}`, `pause`, `resume`, `stop`, `volume {volume}`, `status`, or `startup` (the window's request after the sign-in greeting; answers `{played, message}`: silent when no song is set or in quiet hours, a message when the file is gone or the emergency stop holds) |
| GET | `/api/workshop` | The Workshop (docs/WORKSHOP.md): the folder, the recycle folder, the other folders allowed (`extra_folders`, `folders_setting`), the mission time limit (`minutes`), which Python can run a script (`interpreters`), whether a mission runs (`running`), the last ten missions (state, plan, log, result, chat, tool calls) and the lessons |
| POST | `/api/workshop` | `{action}` with `start {goal}` (a mission in the background; refused while one runs, without a provider key, or while the emergency stop holds), `stop`, or `delete_lesson {id}`; the two settings `workshop_minutes` (1 to 180) and `workshop_folders` (full paths separated by semicolons) go through `/api/settings` |
| POST | `/api/item` | `{kind: memory|note|task, body, id?: existingId}` |
| POST | `/api/item/delete` | `{kind, id}` |
| POST | `/api/reminder` | `{title, seconds}` |
| POST | `/api/reminder/dismiss` | `{id}`, also cancels pending timers |
| POST | `/api/upload` | `{name, data: base64}` returns ID/type/character count/truncation |
| POST | `/api/tool` | `{name, args}`; schemas in actions.py |
| POST | `/api/approval` | `{id, approved: boolean}`; single-use; expires after 15 minutes (a draft or an "ask first" tool; 5 before 1.0.17) or 30 minutes (a change to JARVIS itself); refused while the emergency stop holds |
| GET | `/api/permissions` | The table of every tool (`permissions.py`) with the owner's switch for each, and the emergency stop state |
| POST | `/api/permissions` | `{tool, mode: default\|ask\|off}`; only positions the table offers for that tool |
| POST | `/api/emergency-stop` | `{reason?}`; cancels everything, drops waiting approvals and holds until resumed; returns `{stopped, since, device, reason, saved}` |
| POST | `/api/resume` | `{}`; ends the emergency stop (only the signed-in interface on the PC reaches it) |
| POST | `/api/cancel-all` | `{}`; cancels what runs now and nothing more |
| GET | `/api/routine` | The owner's week as blocks for the nudges (1.0.17): `{blocks, days}` |
| POST | `/api/routine` | `{action: add, days: "MO,WE", start: "18:00", end: "19:00", label}` or `{action: remove, id}`; at most 40 blocks; returns `{blocks, days}` |
| GET | `/api/notices` | The newest 50 things JARVIS said on its own (1.0.17): nudges, announcements a device asked for, approval waits; `/api/state` carries the newest 20 |
| GET | `/api/control-requests` | The window controls a paired device asked for, waiting for the PC's answer (1.0.17); only the signed-in interface on the PC reaches it |
| GET | `/api/network-devices` | The devices this PC has seen on its networks (1.0.17; its own neighbour table, passive, kept a minute): `{devices, count, read_at, scope}` |
| GET | `/owner-style.css` | The owner's own style sheet from the config folder; empty until a style change is approved |
| POST | `/api/speech` | `{text}` returns `audio/mpeg` |
| POST | `/api/speech-to-text` | `{data: base64}` (16 kHz mono PCM16, at most 30 s) returns the transcript for the window's microphone: made on this PC, or by the chosen AI provider when the owner chose that in Settings (docs/SPEECH.md) |
| GET | `/api/files/NAME` | Download from generated folder |
| GET | `/api/export` | Download local messages, items, timers and settings as JSON |
| POST | `/api/conversation/delete` | `{id}`; rejected for an active run |
| POST | `/api/spotify/connect` | `{}` returns OAuth URL |
| GET | `/api/spotify/callback` | PKCE callback; validates single-use state |
| POST | `/api/spotify/disconnect` | `{}` clears tokens |
| POST | `/api/shutdown` | `{}` stops backend |

The AI provider (OpenAI or Qwen) returns each answer complete; the browser receives deltas via cursor-based long polling, not SSE/WebSocket. With the setting `reply_stream` (off by default; Qwen only; `docs/REPLY-STREAM.md`) the Core receives the answer in pieces and emits `assistant.draft` (`{text}`: the whole draft so far, complete sentences that passed the claim checks; an empty text takes the draft away). A draft is for display only: `assistant.delta` and `assistant.completed` still carry the finished, checked answer and replace it. Each event is `{id, run_id, event, data}`. IDs start at zero. Pass the last consumed ID as `after` to reconnect without replaying consumed events. Event history is in RAM and pruned after 30 minutes on new requests; a backend restart loses active runs.

Events: `run.started`, `assistant.delta` (`{text}`), `tool.started` (`{name}`), `tool.completed` (`{name,result}`), `assistant.completed` (`{text}`), and terminal `run.completed`, `run.cancelled`, or `run.failed` (`{message, retry_after, provider, limit}`: `retry_after` is the seconds to pause voice commands after a temporary rate limit, otherwise 0; `limit` is `rate`, `billing` or null). Tool results can contain an approval, file URL, search results, or video ID. No hidden reasoning is emitted. `provider.backup` (`{from, to, reason}`) is emitted once when the backup provider takes over a question (Settings > AI, off by default); the reply text then ends with a bracketed line saying so.

Errors are JSON `{error}` with an appropriate non-2xx status. Render text as text nodes; do not inject untrusted HTML. File uploads accept PDFs, DOCX, UTF-8 text/MD/JSON/CSV, JPG/PNG/WEBP. Speech recording accepts WebM, Ogg, MP4 or WAV.

```javascript
const response = await fetch('/api/chat', {
  method: 'POST', headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({text: 'What time is it?', conversation: crypto.randomUUID()})
});
const {run_id} = await response.json();
let cursor = -1, done = false;
while (!done) {
  const batch = await fetch(`/api/runs/${run_id}/events?after=${cursor}`).then(r => r.json());
  for (const event of batch.events) {
    cursor = event.id;
    if (event.event === 'assistant.delta') console.log(event.data.text);
  }
  done = batch.done;
}
```

Local wake detection: POST `/api/wake` with `{client, data}`. `data` is base64 PCM16 little-endian, 16 kHz mono, exactly 5120 samples (320 ms). Returns `{detected, score}`. Uses the existing session cookie and local-origin checks; audio is processed in memory. A microphone session owns the detector until it stops sending frames for two seconds.
