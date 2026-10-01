# Milestones 2–3 delivery

9 September 2026. Working in-process development mock; no physical Meta integration.

## Run it yourself

Double-click **Start Mock Glasses.cmd** in the existing JARVIS folder. This opens an interactive terminal, not the desktop JARVIS interface. It does not need JARVIS running.

Or, in PowerShell from the JARVIS folder:

```powershell
.\.venv\Scripts\python.exe -m wearables.demo --interactive
```

Type `look` to complete the simulated voice/vision/output turn. Use `status` to inspect simulated device/battery/camera state. Try:

```text
deny-camera
look
allow-camera
fail-ai
look
reset
look
disconnect
look
connect
revoke
look
pair
look
quit
```

Also available: `deny-mic`, `allow-mic`, `fail-network`, `fail-timeout`. `pair` renews the five-minute development session and resets its 100-request limit. No secret tokens are printed.

For a single turn, omit `--interactive`. Add `--play-tone` to hear a quiet synthetic Windows test tone after a successful turn. Default output is a virtual speaker sink. The audible option was not listened to during testing; it is NOT your JARVIS voice.

## What works

Device contract and explicit capabilities; synthetic PCM microphone and one-pixel PNG camera; bounded three-frame camera stream; permission checks; connection/disconnection; simulated battery; optional mock display/gesture output; eight shared JARVIS states and bounded asynchronous subscriptions; scoped expiring/revocable in-process authorization; replay rejection; sequential turns, cancellation, stale-result suppression and structured simulated timing.

Complete path: synthetic microphone -> fixture transcription -> explicit fixture capture -> canned mock vision reply -> generated test-tone PCM -> virtual speaker -> IDLE. Failures return safe error codes and permit subsequent turns. MockCore implements the CorePort boundary; it neither copies the live personality nor imports server/providers/Store. Production services remain untouched. Shared memory architecture remains the existing Store; this milestone creates NO second memory database and does not yet synchronize memories.

## Exact source changes

Created:

- `wearables/__init__.py`
- `wearables/contracts.py`
- `wearables/states.py`
- `wearables/core_port.py`
- `wearables/policy.py`
- `wearables/timing.py`
- `wearables/mock_device.py`
- `wearables/mock_core.py`
- `wearables/pipeline.py`
- `wearables/demo.py`
- `test_wearable_contracts.py`
- `test_wearable_mock.py`
- `Start Mock Glasses.cmd`
- `docs/glasses/MILESTONE-3-REVIEW.md`

Modified: `recovery.py`, `test_recovery.py`, `docs/glasses/ROADMAP.md`, `docs/glasses/SETUP.md`.

Implementation adjustments to the proposed file plan: small fixtures are embedded in mock_device.py instead of binary fixture files; state/policy tests are grouped in test_wearable_contracts.py; failure tests in test_wearable_mock.py. Added pipeline.py to keep orchestration separate from the device and core adapters.

Backup inventory now includes allowlisted source types from wearables, phone and docs/glasses, excluding .env files, build outputs and non-source keys/binaries. A temporary backup restore rehearsal tests this coverage. No new live-data backup was created in this milestone; no core refactor occurred.

## Verification

- Initial contracts: 5 passed.
- First mock loop plus contracts: 13 passed.
- Wearables plus backup regression after hardening: 23 passed.
- Full Python discovery at that point: 132 passed in 10.483 seconds.
- Desktop Node suite: 13 passed, including automated 13-panel inspection test.
- Final wearable suite after adding subscription/stream permission cases: 16 passed. The two additional cases were tested in the focused suite; full discovery was not repeated after that isolated addition.
- Single-turn CLI completed successfully.
- Interactive scripted sequence exercised success, denied camera, AI failure, disconnect/reconnect, revoked session and pairing recovery; exit 0.

Commands used: `python -m unittest discover -p 'test_*.py' -q`; `python -m unittest test_wearable_contracts test_wearable_mock -q`; `node --test desktop/test/*.test.cjs` (using the existing .venv Python and installed Node).

## Limits and next milestone

No real microphone capture, speech recognition, image recognition, JARVIS voice synthesis, phone installation, Meta SDK, Bluetooth, network gateway or physical glasses. Mock authorization is in-memory, NOT a production authentication service. Media checks bound bytes/formats but are not a secure real-image decoder. Timing values measure fixture code only; provider first token/network latency remain null. Futures must not treat these timings as real response-speed evidence.

No live API calls, credentials, production memory writes or firmware changes. No physical device performance/battery/privacy claims.

Recommended next: Milestone 4, a controlled adapter to the existing voice/core services plus authenticated device gateway hardening. Reuse existing personality, evidence guards and configured voice; begin with safe scoped requests and preserve desktop regression coverage. Physical Meta integration remains Milestone 7. Stop here for user review before proceeding.
