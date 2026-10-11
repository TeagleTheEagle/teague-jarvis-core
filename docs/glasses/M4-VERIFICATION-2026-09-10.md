# Milestone 4 verification — 10 September 2026

**Verdict: PASSED — real image → running JARVIS Core → real response → existing TTS → audible PC output gate.**

The final response was confirmed audible in the established voice after the user reconnected the Sony headphones.

This verdict covers the requested mock-glasses/live-Core acceptance. It is not certification of physical glasses, live microphone recognition, all PC hardware, executable cross-device display handoff, or a production multi-device gateway.

## API availability

User reported US$23.99 positive billing balance; the balance itself was not independently inspected. A direct configured vision request returned HTTP 200 from https://api.openai.com/v1/responses using gpt-6-astra at 10:45:28 Sydney time. The old credit_balance_exhausted failure is resolved for the tested requests. Text and vision via the running Core also succeeded. No keys were rotated or exposed. No model or voice configuration changed.

## Test A — real vision

Question: “JARVIS, what am I looking at?” supplied as typed input to the virtual wearable.

Image: the user-supplied Windows System → About screenshot. It is a real screenshot, not a fixture image or physical-camera capture. Image SHA-256: `ee9e0c36da0556b9c50c6d9e36a40d4e1206ee6925c0c8fe356a4fcbc218dc2b`. The gateway used its existing image decoding/sanitization before the Core vision request. Exactly one camera-adapter call occurred.

Final answer:

> You’re looking at the System > About page, Mr. Teague. It shows an AMD Ryzen 7 3700X eight-core processor, 32 GB of RAM, an NVIDIA GeForce GTX 1660 Ti with 6 GB of graphics memory, and 2.04 TB of storage, with 98 GB used. This is a hardware summary, not a performance or health test.

The answer matches the visible CPU, RAM, GPU, storage and used-space fields. “Mr. Teague” and the caution about performance/health came from the existing Core. No alternate personality or AI was injected. Core uses existing shared context/memory code; no new personal memory was added or required for this screenshot question.

Observed state sequence:

`IDLE → LISTENING → THINKING → LOOKING → THINKING → SPEAKING → IDLE`

`OFFLINE` follows only when the virtual device disconnects during cleanup. The initial THINKING before LOOKING is the existing intent-routing transition, not a second assistant. LISTENING here is a workflow state; no actual microphone capture occurred.

## Voice and latency

Existing saved voice profile: `auto`; the harness invoked Core's existing VoiceEngine. Final audio: 581,171 bytes, audio/mpeg. Windows accepted playback and the player returned normally. The raw automated report deliberately keeps listener confirmation separate; see the listening record.

| Stage | Final vision run (ms) | Non-vision run (ms) |
|---|---:|---:|
| Intent routing | 0.28 | 0.27 |
| Camera file acquisition | 0.36 | NOT APPLICABLE |
| Core response, including vision | 3461.8 | 3892.8 |
| TTS to complete audio | 3927.32 | 2703.76 |
| Audio ready → Windows play accepted | 741.45 | 105.37 |
| Typed request → Windows play accepted | 8131.24 | 6702.21 |
| Windows play accepted → player complete | 24509.94 | 14578.39 |
| Entire interaction | 32641.22 | 21280.63 |


Core-reported provider duration: 3397 ms. Server TTS duration: 3909 ms. These are nested measurements and must not be added again to the table. The response callback is buffered: raw `first_token_ms` equals completed-response arrival and is NOT a real streamed first-token measurement.

Unmeasured: actual speech end, transcription, acoustic onset, true first generated token, separate vision-vs-reasoning time, exact decoded audio duration. Playback elapsed time above is measured player lifetime, not an audio-file metadata duration. The 8.13-second request-to-play measurement is from typed input and must not be labelled user-stops-speaking-to-first-word. Previous 575 ms TTS was a different, shorter sample; this is not an apples-to-apples regression.

## Test B — no camera

Asked “JARVIS, briefly explain why a backup restore test matters.” A real Core answer was generated and synthesized; camera_calls=0, camera_used=false. The player completed in software. The earlier non-vision playback has no separate human listening confirmation, so do not claim that individual audio trial was heard.

## ONE JARVIS and PC regression

The harness uses `RealCore` to the already-running PC process. It never constructs App/Store, copies personality or provider configuration, or creates a device-specific memory database. A dedicated wearable conversation ID keeps test chat separate within the SAME Core store. The adapter is explicitly registered simulated.

After each device disconnect, the registry shows PC connected and the virtual wearable disconnected. No PC capability was removed. The live status endpoint remains available; the user also reported hearing PC JARVIS after reconnecting headphones. Regression tests passed, including the authenticated desktop backend and capture of all 13 panels. This is evidence of preserved tested PC behavior, not proof every microphone, device, service and desktop action was physically retested.

Multi-device plan test: one request routes camera to glasses, display to PC and voice to glasses; it remains non-executable and subject to authorization. This is simulated planning, not real cross-device display execution. Shared-memory/context injection, saved voice profile, restricted tools and rejected unexpected vision tools passed their integration tests. Wearable memory writes remain deferred.

## Failures and recovery retained

1. Sandboxed direct API probe captured no HTTP response. Permitted network retry returned 200; not a billing failure.
2. First real Core vision/TTS run reached audio generation but failed Windows playback with AUDIO_PLAYBACK_FAILED under the sandbox. Answer was preserved; states recovered ERROR → IDLE.
3. Desktop-permitted run completed software playback, but the user heard nothing. The user was using the selected Sony headphones. Endpoint volume was 72%, unmuted; the actual cause is not proven.
4. User power-cycled headphones and reported hearing JARVIS perfectly. No software volume or voice setting was changed.
5. The first post-reconnection request was rejected at start in 34.29 ms with JARVIS_SERVICE_UNAVAILABLE; Core status still succeeded. No AI measurement was produced. Busy/invalid/other rejection cannot be distinguished by the current generic bridge error. We do not claim a new API outage.
6. One further attempt completed the final full vision/voice flow. Human confirmation is recorded separately.

Mock/integration recovery tests additionally exercised disconnect/reconnect, permission revocation, denied camera access, offline/device faults, TTS failure retaining the answer, cancellation and stale generations. These were deterministic simulations, not deliberate outages of the live PC.

## Regression results

- Python: 147 passed, zero failures, 14.502 seconds.
- Desktop: 13 passed, zero failures, 47.065 seconds wall time.
- Focused wearable/registry: 29 passed, zero failures, 1.390 seconds; overlaps Python total.

No live OpenAI dependency was introduced into deterministic tests. Application code was not restarted or restructured. Changes for this verification: additive intent/events/playback timing in `wearables/interaction.py`; optional dated output in `wearables/diagnose_openai.py`; new opt-in `wearables/verify_m4.py` acceptance harness; evidence/documentation files. The three partial Swift source files created before the user switched priorities remain paused and are not an iOS build or feature release.

## Evidence

- [OPENAI-RECHECK-2026-09-10.json](<C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/glasses/OPENAI-RECHECK-2026-09-10.json>)
- [OPENAI-RECHECK-2026-09-10-NETWORK.json](<C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/glasses/OPENAI-RECHECK-2026-09-10-NETWORK.json>)
- [M4-VISION-2026-09-10.json](<C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/glasses/M4-VISION-2026-09-10.json>)
- [M4-VISION-2026-09-10-DESKTOP.json](<C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/glasses/M4-VISION-2026-09-10-DESKTOP.json>)
- [M4-NONVISION-2026-09-10.json](<C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/glasses/M4-NONVISION-2026-09-10.json>)
- [M4-VISION-2026-09-10-FINAL.json](<C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/glasses/M4-VISION-2026-09-10-FINAL.json>)
- [M4-VISION-2026-09-10-RECONNECTED.json](<C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/glasses/M4-VISION-2026-09-10-RECONNECTED.json>)
- [M4-TEST-RESULTS-2026-09-10.json](<C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/glasses/M4-TEST-RESULTS-2026-09-10.json>)
- [M4-LISTENING-2026-09-10.json](<C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/glasses/M4-LISTENING-2026-09-10.json>)

## Stop point

No physical Meta integration, Core 2.0, further iOS work or additional device development performed. Physical compatibility research and executable cross-device handoff remain separate gates. Keep the generic start-error limitation and headphone recovery observation for future diagnostics.
