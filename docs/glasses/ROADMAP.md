# Milestones and exact proposed changes

Milestone 4 implementation and the central registry are now documented in [MILESTONE-4-REVIEW.md](MILESTONE-4-REVIEW.md). Real-service acceptance remains blocked by HTTP 429. The user's latest milestone numbering makes physical Ray-Ban integration Milestone 5 after explicit approval; the earlier numbered plan below is historical. [ONE-JARVIS.md](ONE-JARVIS.md) governs all integrations.

## Delivery update — 9 September 2026

Milestones 2–3 were approved and implemented. See [MILESTONE-3-REVIEW.md](MILESTONE-3-REVIEW.md) for actual files, tests, run instructions and limitations. The original plan below is retained as design history; its earlier approval-pending statements no longer apply to Milestones 2–3. No later milestone has begun.

## Milestone 1 — completed audit

Created only `docs/glasses/ARCHITECTURE.md`, `WEARABLES.md`, `META_INTEGRATION.md`, `SECURITY.md`, `PRIVACY.md`, `SETUP.md`, and this `ROADMAP.md`. Existing runtime untouched. Major implementation awaits user approval as requested in the brief.

## Milestone 2 — contracts and isolation

Create inside existing JARVIS root:

```text
wearables/__init__.py
wearables/contracts.py          # capability, media and envelope validation
wearables/states.py             # scoped transitions, sequence and cancellation
wearables/core_port.py          # service interface; no server import side effects
wearables/policy.py             # device scopes and operation allowlist
wearables/timing.py             # clock-safe timing records
test_wearable_contracts.py
test_wearable_states.py
test_wearable_policy.py
```

Keep existing desktop code intact at this stage. Establish tests for malformed messages, denied permissions, unsupported features, cross-device IDs, disconnect/cancel and stale events. Acceptance: contracts have no Meta/Electron dependency and do not load provider credentials; state/policy tests pass.

## Milestone 3 — Windows mock glasses

Create:

```text
wearables/mock_device.py        # deterministic faults/media/device events
wearables/mock_core.py          # labelled canned answer, no network
wearables/demo.py               # executable fixture-driven demo
wearables/fixtures/             # small synthetic PCM/image fixtures
test_wearable_mock.py
test_wearable_failures.py
```

Run the complete simulated capture -> request -> fake answer -> audio sink loop without API calls. Test disconnect/reconnect, revoked authorization, permission denial, provider quota/timeout, malformed media and late playback. Simulate future HUD separately; do not present it as Meta compatibility. Acceptance: repeatable demo, no production DB writes, recoverable failures, all simulated outputs labelled. Native Meta Mock Device Kit follows when Mac build access exists; it is not executable as a Windows SDK.

Modify `recovery.py` and `test_recovery.py` to include explicit new source/fixture/document folders while excluding secrets, build outputs and downloaded dependencies. Review `phone/` coverage at the same time. Do not rename existing bridge/database tables merely for naming consistency.

## Later milestones — not authorized for immediate implementation

4. Real voice: add `core_facade.py`, `device_gateway.py` and native `clients/ios/JarvisWearable/`; incrementally adapt `server.py`, reuse `local_stt.py`/`voice_engine.py`. Harden device sessions and transport first; retain task bridge compatibility. Tests must prove desktop parity and current voice preservation.
5. Vision: typed deliberate capture, server-owned upload association and analysis-only tool scope; adapt `server.py` attachment dispatch. Reuse provider vision and evidence guards.
6. Shared memory: additive metadata/deletion migration in `store.py`/`memory.py`, shared-store two-device tests; explicit save and retention controls.
7. Meta adapter: native Swift `WearableDevice.swift`, `MetaWearableAdapter.swift`, `MockWearableAdapter.swift`, `AudioRouteController.swift`, `GatewayClient.swift`, `SecureSessionStore.swift`; pin verified SDK, follow registration/permission docs and physical test matrix.
8. Continuous conversation: measured concurrency/streaming, safe evidence boundary, route interruptions, clock-correct first-audio measurements. Do not interpret full-response callback as first-token latency.
9. Minimal capability-gated HUD; physical Display validation.
10. Custom hardware feasibility: optics, power/thermal budgets, processor/connectivity and regulatory/product constraints after interaction loop works.

## Blockers and approval decision

No API credit or glasses required for Milestones 2–3. Real inference needs a working provider; authentic voice tests need the current voice service. Native builds need Mac access. Meta developer registration, detailed documentation, exact hardware/firmware/region eligibility, audio routing and background behavior remain integration gates. No promise of a custom wake-word takeover or independent operation away from the PC.

Recommended next approval: implement Milestones 2–3 only, keep desktop runtime untouched except separately tested backup inventory coverage. This proves the abstraction before a major core refactor or hardware purchase.
