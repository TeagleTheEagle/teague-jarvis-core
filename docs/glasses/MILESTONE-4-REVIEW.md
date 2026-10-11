# Milestone 4 + one-Core architecture review

9 September 2026. Implementation delivered; live vision-to-speech acceptance BLOCKED by OpenAI HTTP 429. No physical integration begun.

## One central JARVIS

The production adapter connects to the already-running PC App over a restricted same-PC bridge. It calls App.start_run, the existing context/personality/memory/evidence path, LocalSTT and VoiceEngine. It does not start a second App or Store. `device_registry.py` is owned by that App and is available through a read-only Core tool. See [ONE-JARVIS.md](ONE-JARVIS.md) and root AGENTS.md for the binding invariant.

One central database; wearable-local is a conversation ID, not a separate identity. Existing PC tool capabilities remain; the wearable allowlist is intentionally narrower. Scene analysis cannot execute tools. Temporary App instances in tests and the explicitly opt-in live probe are isolated test fixtures only.

## Run the demo

First apply the JARVIS backend update or fully quit/reopen JARVIS from its tray. Closing its window may only hide it. Startup publishes a local discovery credential in `.env.wearable-connection.json`. It contains no AI keys; do not share it. The adapter reads it automatically. No fixed port guessing or phone network setup is needed.

In PowerShell, from the existing JARVIS folder:

```powershell
# Offline fixture mode, no network or existing Core required:
.\.venv\Scripts\python.exe -m wearables.demo_real

# Real existing JARVIS, real selected image, configured voice, PC speaker output:
.\.venv\Scripts\python.exe -m wearables.demo_real --ai real --vision real --voice real --image "C:\path\to\your-image.jpg" --text "JARVIS, what am I looking at?" --play

# Real text request; no camera:
.\.venv\Scripts\python.exe -m wearables.demo_real --ai real --voice real --text "JARVIS, what time is it?" --play

# Five-second PC microphone recording through existing local STT:
.\.venv\Scripts\python.exe -m wearables.demo_real --ai real --vision real --voice real --mic live --image "C:\path\to\your-image.jpg" --play
```

Use your actual image path. Real vision sends the selected image through the configured vision provider. A successful text answer remains printed even if TTS fails. Omit `--play` to generate real voice audio into the virtual output sink without audible playback. Existing `python -m wearables.demo --interactive` still works unchanged.

Environment equivalents: AI_MODE=mock/real, VOICE_MODE=mock/real, MIC_MODE=fixture/live, VISION_MODE=mock/real. CLI options override these. Defaults are mock/fixture. REAL_JARVIS is represented by `--ai real --voice real`; real scene interpretation additionally needs `--vision real`. Real vision requires real AI; a real-AI/mock-vision scene request is deliberately answered by the labelled vision mock, not fabricated real inference.

Optional sounddevice 0.5.6 was installed into the existing virtual environment; `requirements-wearables.txt` reproduces that dependency range. Actual microphone capture and audible Windows playback were not exercised in this session. No always-on microphone, physical camera or glasses connection exists. The local image remains the development camera.

## Built and changed

Created: `device_registry.py`, `AGENTS.md`, `requirements-wearables.txt`, `test_device_registry.py`, `test_wearable_real.py`; `wearables/service.py`, `real_core.py`, `output.py`, `local_device.py`, `config.py`, `intent.py`, `interaction.py`, `demo_real.py`, `probe.py`; `docs/glasses/ONE-JARVIS.md` and this report.

Modified: `server.py` (narrow bridge dispatch, scoped wearable runs, shared registry), `actions.py` (read-only registry tool), `recovery.py` (optional dependency manifest backup), `.gitignore` (local discovery credential exclusion), `wearables/core_port.py`, `wearables/mock_core.py`, and the setup/roadmap documentation.

The original provider, memory, personality and voice synthesis implementations/configuration were not rewritten. Audio playback supports the existing MP3 output, rather than trying to interpret MP3 as mock PCM. Real playback uses a short-lived temporary MP3 deleted after playback; virtual playback retains bytes in memory only.

## Tests and measurements

Before edits: backup bd5bc6fa8a68493482c30304deb1afe6 created and restore rehearsal passed.

- Initial real-adapter tests: 9 passed.
- HTTP adapter test added: focused real-adapter suite 10 passed. Actual HTTP requests check bad credentials, bad Origin and the real local time path without cloud calls.
- Registry plus wearable focused suite: 29 passed.
- Full Python discovery after registry/tool integration: 147 passed in 11.204 seconds.
- Desktop Node suite: 13 passed (after bridge integration; registry was added later and covered by Python tests).
- Final CorePort/mock respond adjustment: focused wearable suites rerun; see final response for result.
- Offline CLI without camera: successful, exit 0.

Live probes used a synthetic blue PNG and temporary conversation storage, existing provider configuration, and a read-only copy of the saved voice profile. No personal image or live memory write was involved. First probe reached a Core failure after 2816.83 ms; independent real TTS produced 45,138 bytes in 823 ms. One repeat with redacted diagnostics identified HTTP 429/quota-or-rate-limit; it failed after 1341.81 ms, and independent TTS produced 45,138 bytes in 575 ms. No further live retries were made.

Therefore no successful real vision answer, speech-to-text measurement, model first-token measurement or total first-spoken-word measurement is claimed. The network/vision service's quota or rate limit must be resolved before the primary success test can pass. Voice generation is verified; audible playback is unverified.

Latency reports use one local monotonic clock. Separate vision inference and AI first-token are null because the existing Core combines vision in the model call and buffers responses. TTS reports time to complete generated audio, not streamed first bytes. Playback-command acceptance is not acoustic onset. Typed input correctly has null capture/STT fields. Failed stages never receive invented successful durations.

## Remaining architecture limitations

The bridge is loopback HTTP for same-PC development only. It is not a phone/glasses network service and must not be forwarded publicly. Its random local token has process lifetime; server restart rotates it. A future HTTPS/WSS remote gateway needs per-device short-lived sessions, revocation, media decoding limits and separate permissions. Local users with access to the JARVIS source directory can read the local credential; it is not a boundary against another process running as the same OS user.

Registry capability planning is non-executable. Actual PC audio/display readiness and physical device permissions remain unverified until device adapters report them. Single active run globally is retained; concurrent devices receive busy behavior rather than corrupting a conversation. Existing provider buffering and TTS serialization remain; no latency optimization was attempted.

The existing Core still contains desktop-oriented guidance, but wearable tool filtering and server-side enforcement prevent desktop actions through this route. Future orchestration should separate capability-specific instructions while preserving the shared identity and evidence policy.

Next gate: restore working API access, restart the existing JARVIS backend, run the image/voice command above and verify microphone/playback on the actual PC. Physical Ray-Ban Meta integration is NOT ready to claim. Per the latest instruction, physical integration is the next separately approved milestone (Milestone 5), not an automatic continuation.
