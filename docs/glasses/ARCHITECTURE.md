# TEAGUE INDUSTRIES — JARVIS GLASSES

Milestone 1 audit • 9 September 2026 • Proposed architecture, not implemented

## Decision

Keep the existing JARVIS application as the authoritative brain and database. Add a wearable workstream inside this codebase; do not copy the brain into a second application. The native iPhone client becomes a gateway for glasses as well as a useful standalone device. No firmware changes are proposed.

```text
Mock device (Windows first)       Meta glasses (later)
           |                            |
WearableDevice contract      Native iPhone + Meta adapter
           +-------------+--------------+
                         |
               Authenticated device gateway
                 HTTPS; later WSS if needed
                         |
               JARVIS service facade
                         |
       Existing conversation / evidence / personality
       Existing STT / vision provider / VoiceEngine
       Existing Store / memory / workspaces / tool policy
                         |
                Existing desktop interface
```

The PC must be awake and reachable for PC-hosted intelligence. This proposal does not make glasses an independent AI computer.

## Inspected source map

| Component | Existing files and evidence | Reuse / required separation |
|---|---|---|
| Application orchestration | `server.py:83` App; `:143` start_run; `:378` work | Reuse context construction, guarded responses and conversation persistence. Extract behind a facade incrementally, with desktop parity tests. |
| AI and vision | `providers.py` chat (OpenAI); qwen_chat (Gemini removed in 1.0.15) | Keep provider selection server-side. OpenAI branches currently return complete responses; provider callback is not necessarily first-token timing. No live account check in this audit. |
| Personality and evidence | `personality.txt`, `conversation_context.py`, `answer_evidence.py`, `verified_status.py` | Preserve these; do not bypass guards by invoking provider directly from wearables. |
| Recognition | `local_stt.py:8`; `providers.py:334`; `wake.py`; `static/voice.js` | Local Whisper consumes bounded 16 kHz mono PCM16, 0.1–30 seconds. Browser capture, endpointing and wake lifecycle need a native equivalent. CPU model loading remains on PC initially. |
| Voice | `voice_engine.py:24`, `providers.py:314` | Reuse configured voice and in-memory synthesis cache. Native client plays returned audio. Cache lock currently spans synthesis, serializing requests. No streaming TTS implemented here. |
| Storage | `store.py:12`, `memory.py`, `workspaces.py` | One SQLite database, one connection per operation, WAL. Memory already has source/category/confidence and timestamps; image/location/device links need an explicit later migration. |
| Transport | `server.py:677–685` | Run events use JSON long polling, not WebSockets or SSE. Keep existing transport stable; no need to introduce WSS for the mock milestone. |
| Desktop API protection | `server.py:612`, `:930` | Loopback binding, Host/Origin/session checks. Preserve. Never publish all desktop routes to a phone. |
| Initial phone bridge | `phone_bridge.py` | Separate authenticated task-only HTTP service; TLS or loopback behind private HTTPS proxy. Hashes device tokens; supports revoke and idempotent task creation. Not a voice/vision gateway. |
| Frontend | `static/`, `desktop/main.cjs`, `desktop/preload.cjs` | Existing hologram and interface remain. Rendering/audio capture tied to browser/Electron; native client needs its own presentation binding. |
| PC-specific authority | `computer_tools.py`, `desktop_launcher.py`, `desktop/`, `development.py`, inspection modules | PowerShell/process launch, Electron IPC/screenshots/window/tray/global keys and source editing remain desktop adapters. Deny these to glasses by default. |
| Configuration | `server.py:26` load_env, `.env.example` | Configuration loads at module import. Avoid importing server just to obtain a wearable utility. No secret values read for this audit. |
| Backups | `recovery.py:inventory` | Current recursive source inventory covers static/desktop, not phone or proposed wearable/native/docs directories. Add safe explicit coverage and restore tests before claiming these new sources are backed up. |

## Integration hazards

1. `App.start_run` currently allows only one active run globally. Keep explicit BUSY initially; later schedule by conversation with bounded concurrency. Do not silently cancel a desktop turn for glasses.
2. `App.work` supplies desktop development guidance and broad tools. Introduce a server-created RequestContext (device, scopes, conversation, capture purpose); client claims cannot grant authority. Enforce tool policy before local fast paths AND model tools.
3. Screen observations are restricted through the attachment name `screen-capture.jpg`. Wearable vision needs a typed analysis-only capture purpose, not a filename workaround. Scene text is untrusted data, never authorization for actions.
4. Attachments/runs/approvals are currently App-owned. Bind wearable uploads, outputs and cancellation to the authenticated device/session. Do not expose arbitrary run or file IDs.
5. Existing phone keys are revocable but long-lived; no expiry/scopes/rate limiter. TLS handshake occurs in accept path, and retry receipts have no cleanup. Harden before extending beyond the task prototype.

## Target boundaries

`CoreFacade` delegates to the same application services. It is not a second brain. `MockCore` exists only in an explicit development profile, uses fixtures and a temporary database, and labels every output simulated. Production failures never switch silently to fake answers.

Use a scoped state event: schema version, device ID, conversation ID, turn ID, sequence, state, timestamp and reason code. Devices subscribe to their authorized turns; one global state would incorrectly make every device speak when only one is responding. Desktop translates these events into its existing richer visual states.

Keep initial scheduling bounded and sequential. Add streaming only after evidence checks, audio cancellation and timing semantics have regression coverage.

See [WEARABLES](WEARABLES.md), [META_INTEGRATION](META_INTEGRATION.md), [ROADMAP](ROADMAP.md), [SECURITY](SECURITY.md), [PRIVACY](PRIVACY.md), [SETUP](SETUP.md).
