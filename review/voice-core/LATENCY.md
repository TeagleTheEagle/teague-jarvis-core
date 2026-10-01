# Voice latency — first profiling pass

## Measured comparison

| Stage | BEFORE | AFTER | Evidence |
|---|---:|---:|---|
| Endpoint silence waiting | 2560 ms | 1280 ms | Deterministic 320 ms PCM-frame test |
| Speech recognition end-to-end | Not measured | Not measured | Needs live utterance |
| AI first token | Not measured for comparable question | Not measured | Provider duration is recorded separately |
| Voice start | Not measured | Not measured | TTS response and playback event timestamps added |
| Total to first audible word | Not measured | Not measured | Browser playing event is a proxy; hardware output delay is not measured |

The user supplied a report of model calls lasting 2616–8752 ms. Those calls are not identified as comparable questions and are not an end-to-end baseline. The largest overall bottleneck cannot yet be established.

## Findings and changes

The microphone endpoint waited for eight 320 ms silent frames. It now waits for four by default. Developer settings allow the old 2.56-second threshold for speakers who pause longer. No transcription model, beam settings, voice provider, personality, memory or evidence guard changed.

Transcription is local Whisper, batch-only in the existing implementation. The model is already cached after first use. Added model-load and inference durations separately. Streaming STT is not enabled: speculative repeat inference could duplicate CPU work and alter transcripts before a live baseline exists.

The LLM provider streams internally, but JARVIS holds output until final evidence/action guards approve it. Provider request and first token timings are separate from browser receipt. Unchecked tokens are not spoken. Safe clause-level guard design would be required before speaking a still-unverified answer.

TTS returns complete MP3 bytes, with an existing short-lived in-memory cache. Added server synthesis duration, client audio-ready and playback-start timestamps. Streaming/chunked TTS is not implemented in this pass; no measured TTS bottleneck or provider-specific streaming behavior was established. This avoids guessing at a high-impact optimization or changing the voice/prosody prematurely.

Timing data is kept in the page only (20 traces max), no text or audio. Settings > Developer > Voice latency lets the user refresh the report and disable recording. Timings use performance.now; backend provider/STT/TTS durations are distinct and not mixed with absolute client clock values. Speech end is the last detected voiced PCM frame, quantized to 320 ms and threshold-based, not exact phonetic end. UI long-task duration is recorded where the browser supports it. Hidden/offscreen cores skip rendering.

## Validation

105 Python tests passed after instrumentation. Endpoint simulation passes. Shared-core Web Audio tests pass. All 13 pages rendered with no JavaScript errors; responsive harness at 720,1280,1920,2560,3840 widths passes. These do not establish live speaker timing or answer quality on a representative conversation.

Next evidence needed: apply the update, ask several comparable spoken questions, then refresh the Developer timing report. Compare 2.56-second and 1.28-second modes for a live baseline and optimized endpoint sample. Use that evidence to select the next optimization.
