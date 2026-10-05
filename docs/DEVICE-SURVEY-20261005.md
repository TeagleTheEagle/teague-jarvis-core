# What JARVIS already has for devices, pairing, speech, backup, offline answers and fallback (survey, 2026-10-05)

Why this exists: on 2026-10-05 the owner sent the master architecture document again and said "implement everything
that we havn't done into 1.0.15". Before scoping that (`docs/RELEASE-1.0.15-SCOPE.md`), one read-only survey agent
went through the code for the parts the earlier survey (`docs/CAPABILITY-SURVEY-20261005.md`) did not cover. This file
is its report, shortened. **Nothing was run; behaviour is from reading the code at the working tree of that evening.**
It is the agent's reading and was not checked line by line afterwards.

Tags: WIRED = reached by the running Core, from the interface, the AI model or a client. API-ONLY = a Core route or
function exists but nothing calls it. TEST/CLI-ONLY = a script or a fixture. ABSENT = not in the code.

## 1. Device registry (master document sections 5 and 19)

- `device_registry.py:6-53`, WIRED, **in memory only** (lost at restart). A record holds free-text capabilities, which
  of them are ready, an expiry (at most 3,600 s) and a "simulated" flag. No name, type, key, trust level or permissions.
- Presence is "not expired", kept alive by a heartbeat. `plan()` is TEST-ONLY and always answers "not executable".
- The Core registers `pc` at start (`server.py:108`); the wearable service registers one simulated client at every start
  (`wearables/service.py:20`). Registering grants nothing.
- `/api/state` lists devices (`server.py:147`); the model has a `device_registry` tool. The dashboard shows three fixed
  places (this PC, phone, glasses); there is no device management panel.
- Network discovery (mDNS, ARP, hostnames, Bluetooth): ABSENT.

## 2. Pairing and device authentication

- The Core listens on `127.0.0.1:8765` only and checks the Host header. Sign-in is a session cookie made at each start,
  plus one shared desktop token for a background Core. There is no identity per client.
- Wearable routes `/api/wearable/<op>` are WIRED and use one token made at each start, written to the config folder
  and deleted at shutdown. No pairing code, per-device key, expiry or revocation.
- `phone_bridge.py` is TEST/CLI-ONLY, a separate process that nothing starts: `pair` issues a token whose hash is kept
  in the Core database, `revoke` removes it, `serve` binds `127.0.0.1:9443` and offers tasks only. Paired phones never
  appear in the registry or the interface.
- `deployment_test/enrollment.py` is TEST-ONLY (the Stage 4 harness): per-client keys, scopes including an emergency
  scope, signed owner requests that expire, versioned revoke and replace. It is the fullest pairing design in the repo
  and is not on the production path.

## 3. iPhone and glasses

- `ios/JARVIS/` holds three Swift files (a client protocol, a mock, and a client that throws "live not implemented").
  No Xcode project, no networking, no Bluetooth. Not shipped in releases.
- Halo or Brilliant: ABSENT in code. The interface still says "Meta glasses (future)" (`static/teague.js:98`).
- What a phone or glasses client could use today is the same-PC wearable bridge: register, registry, disconnect, status,
  start, events, cancel, transcribe, speech; one call at a time, 20 a minute, 3 MB bodies, nine read tools, no tools
  with a picture, no memory commands.

## 4. Permissions and operator control (section 6)

- Emergency stop is WIRED but momentary: `POST /api/cancel-all` (Ctrl+Alt+Shift+X, tray "Stop activity", companion
  STOP ALL) cancels every run and refuses their pending approvals. Nothing stays paused; new requests are accepted at
  once.
- Per-tool metadata (read-only or changing, reversible, needs approval, limits): ABSENT. Policy is spread over
  hard-coded sets in `server.py`, `answer_evidence.py`, `store.py` and `development.py`.
- Revoking one device or one capability, an operator or diagnostic mode: ABSENT. Audit rows hold action, status and
  time; no device or run.
- Natural home: a table keyed by tool name beside `TOOLS` in `actions.py` (not inside the tool descriptions, which go
  to the AI providers as they are), enforced in `App.tool`, the one place every path passes.

## 5. Speech (section 4)

- Speech to text: local Whisper behind `/api/voice-lab/transcribe`, WIRED; the interface always uses it. Cloud
  transcription exists for OpenAI only and is API-ONLY; there is no setting and no common dispatcher. Qwen speech
  recognition: ABSENT.
- Text to speech: `VoiceEngine.synthesize` calls `providers.speech` with profiles auto, fish, openai, qwen. The Qwen
  cloned voice is WIRED and needs a voice ID; no enrolment code exists.

## 6. Backup (section 11)

- `recovery.py` creates, verifies, rehearses and restores into a new folder; WIRED to Settings > Backups. Backups are
  written beside the data folder, so on the same disk. `switch_over.py` is command line only.
- Scheduled or automatic backups, retention, a copy on another disk: ABSENT.

## 7. Local and offline AI (section 16)

- The local Ollama code only classifies a command into eight intents and writes a log. A local model cannot answer a
  chat today: with a key and no network the Core retries once and fails; with no key it gives fixed text.
- Missing for offline answers: a chat adapter, model install and health checks, a smaller prompt, a decision about
  tools, a trigger, a "which model answered" note, and offline speech output.

## 8. Fallback and replies appearing while written (section 3)

- No automatic fallback between OpenAI and Qwen, confirmed. A fallback could sit in `providers.chat`, or in the loop in
  `App.work` where it is known whether a tool has already acted (the Stage 4 test router refuses a fallback after tool
  work).
- No streaming: both adapters ask for one complete answer, the Core shows the reply only after its two claim checks
  (`verified_status.guard`, `answer_evidence.action_guard`), which read and may replace the whole answer; speech uses
  the final text.

## Surprises and contradictions the survey reported

1. `docs/owner/ARCHITECTURE-ALIGNMENT.md` (2026-10-01) is out of date: Qwen chat, vision and voice exist; the installer
   and release builder exist; it has no rows for sections 6, 11 and 16.
2. `docs/ROADMAP.md` says Qwen plus one local model with OpenAI retired; the code defaults to OpenAI and has no local
   chat model.
3. A wearable client can declare itself "not simulated", and the dashboard would then count it as a real online device.
4. Wearable routes skip the desktop-token check.
5. The wearable speech reply is labelled MP3, but the Qwen voice can return WAV (effect not determined).
6. Phone token hashes are in the Core database, so backups carry them and a restore brings old keys back; a `.env`
   key file placed in the data folder makes backup creation fail.
7. The master document's emergency stop is owner-only and can revoke; the code's needs only the normal session and
   cancels runs.
8. Networking, exposing JARVIS on the local network and widening `phone_bridge --host` are owner-only in `CLAUDE.md`;
   master document sections 5, 7, 8 and 9 need those decisions before real devices can connect.
