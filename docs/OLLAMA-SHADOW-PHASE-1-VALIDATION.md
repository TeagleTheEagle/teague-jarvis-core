# Phase 1 completion and real-world validation

2026-09-11; follows commit 1aac6f2. Phase 2 remains disabled.

## Acceptance

**OLLAMA / QWEN3 LOCAL PROVIDER — PHASE 1: ACCEPTED (2026-09-11).** The user confirmed the production desktop time response and supplied a screenshot. The corresponding 09:27:02 +10:00 shadow record (9d6e57d94e66425fba22bc694f5dd260) is valid and matches time_now. See phase1-final-acceptance-evidence.json for final totals. The sections below preserve the earlier validation history; previous pending UI references are superseded by this acceptance. This does not claim every PC feature or live voice playback was retested.

## Final acceptance telemetry

5 evaluations; 4 valid comparisons; 4 matches; 0 mismatches (100% of valid comparisons); 0 schema failures; 1 deliberate interruption health timeout; 1 provider error total. Average successful classification 2967.536 ms; P50 3594.041 ms; P95 3848.791 ms; cold mean 3709.962 ms; warm mean 740.259 ms. Manual request: cold 3594.041 ms, ONLINE, schema valid. The supplied screenshot shows the authoritative local-time reply and a 33 ms UI completion indicator, separate from shadow latency. This is user-supplied evidence, not a new agent timing measurement.

Acceptance changes documentation only. ONE Core, OpenAI/current routing, memory ownership and authorization remain unchanged. Qwen remains SHADOW with zero execution authority. Prior 168 Python / 13 desktop / 16 JavaScript passes remain the regression evidence; no rerun for this documentation-only acceptance. Limitations: small time-only sample, constrained eligibility, rotation/cooldown sampling, no new audible-voice or all-feature verification. Collect at least 500 eligible real-world evaluations across seven or more days, at least 100 per proposed read-only intent, and review the gates below before Phase 2 approval. No Phase 2 work started.

## Four JavaScript failures

All four reproduced before shadow mode; 1aac6f2 changed none of the affected voice/frontend paths. Each was a test-fixture compatibility issue, not evidence of a Qwen routing regression. Severity: medium for test reliability; no demonstrated production fault from these failures. They blocked an all-green regression gate until corrected.

| Test | Error | Root cause and smallest correction |
| --- | --- | --- |
| test_conversation_voice.cjs | commands 1 != 0 | Four 320 ms silence frames reach the existing default 1.28 s endpoint. Test a short 960 ms pause instead; explicit finish and session assertions remain. |
| test_timer_fast_path.cjs | cloud 0 != 1 | Extracted speech routine lacks JarvisLatency in VM, so fails before fetch. Add a no-op instrumentation stub; configured-provider and cancellation assertions stay. |
| test_voice.cjs | resolve is not a function; 131074000 != 16000 | Modern command transport is raw PCM, not WAV. Check MIME, PCM block length and samples; separately check the WAV utility. Drain asynchronous completion and end the persistent conversation before testing a pending wake cancelled by mute. Preserve two legitimate wake/arm callbacks and reject the cancelled third. |
| test_voice_cancellation.cjs | undefined pending entry/aborted; cwd ENOENT | Same missing latency stub plus a cwd-dependent source path. Add stub and resolve from __dirname; retain abort ownership and silent cancellation assertions. |

No production voice, authorization, Core, provider or UI implementation was modified in this follow-up.

## Production evidence

Canonical Start-Desktop.ps1 invoked unchanged. Existing single-instance desktop reused. Process inspection showed one desktop parent (18488), venv Python launcher (3492) and its runtime child (12756), not two independent Core servers. Existing authenticated session origin remained http://127.0.0.1:52559 through all checks. Session credentials remained in memory and were never printed or copied. The normal root response supplies the required session cookie; both authentication layers remained enforced (a request without the cookie correctly returned 401).

The actual desktop window was inspected and Communications navigation exercised. Windows input focus automation was unreliable; a user confirmation request for typing `what time is it` is pending. Consequently all records below explicitly say production desktop Core API, not UI typing. No microphone or screen-capture control was enabled, no screenshot was uploaded to an AI service, and audible voice is not claimed verified.

Authenticated read-only time requests used the existing Core. Online request 0c045b68d55e4ca7bf84954cf3edf42f completed in 319.667 ms (observed polling time); Qwen independently agreed. For interruption, verified Ollama app/server processes 16888/17076 were stopped, and the exact local Ollama app restored in finally. Request c6a17a2c75a5494ab1022b8dcfd60c35 completed in 324.248 ms despite a 1014.295 ms shadow health timeout. This is observed provider unavailability, not a claim of connection-refused behavior. Subsequent recovered and warm evaluations succeeded on the same Core. Memory content hashes compared equal before/after every probe; conversation records intentionally contain these harmless test requests.

New deterministic integration subcases explicitly test offline, timeout, invalid schema and unknown intent: existing time tool called once, existing answer retained, memory unchanged, shadow result ignored. Existing mismatch test returns open_app/paint from Qwen yet proves only time_now executes. Offline/no-retry, transport timeout, and unknown intent validation also retain their adapter tests. No malformed response was injected into the production server.

## Telemetry snapshot

Source: retained production data/provider-shadow.jsonl only; four deliberate validation requests, not organic usage. Initial temporary fixture evidence is separate and excluded. See phase1-production-*.json for correlated records.

| Metric | Value |
| --- | --- |
| Total shadow evaluations | 4 |
| Valid comparisons | 3 |
| Matches / mismatches | 3 / 0 |
| Agreement among valid comparisons | 100% (3/3) |
| Schema failures | 0 |
| Timeouts | 1 (health check, deliberately interrupted service) |
| All provider errors | 1 (includes that timeout) |
| Average successful classification latency | 2758.701 ms |
| P50 / P95, nearest rank | 3687.053 / 3848.791 ms |
| Mean cold / warm classification | 3767.922 / 740.259 ms |

Timeouts are excluded from successful-classification latency and agreement; their health/worker durations remain in the source records. Zero valid comparisons yields null agreement, never 100%. P95 with three successes is simply the maximum, not reliable tail evidence. No universal accuracy claim follows from these deliberate time-only checks.

Use `.\.venv\Scripts\python.exe shadow_report.py data/provider-shadow.jsonl` for fresh read-only metrics; include `data/provider-shadow.previous.jsonl` as another argument if present. It reports retained history only, not lifetime totals; rotation and skipped cooldown/busy requests limit coverage. It prints aggregates, not prompts or secrets. Per-request telemetry already contains IDs, timestamps, labels, match, health, schema status, errors and cold/warm timing. No expanded eligibility or sensitive content collection was added.

## Regression

- Original pre-shadow baseline: 147 Python tests passed; baseline desktop run had one timeout, subsequent 13/13 passed.
- This follow-up: 168/168 Python tests passed (40.554 s), including 21 shadow/report tests; 13/13 desktop tests passed (26.665 s); all 16 broader JavaScript test files passed.
- Python compilation, JavaScript syntax checks and git whitespace checks passed. Only normal CRLF conversion warnings reported.
- Deterministic suites use mock providers / disable live shadow calls. Real service experiments are separate. No real OpenAI invocation required for these checks.

## Recommended Phase 2 evidence gates

These are proposed engineering gates, not proven thresholds or authorization to proceed:

1. Completed: actual desktop UI-typed request confirmed by the user and correlated by timestamp to a valid matching shadow record.
2. Collect at least 500 eligible real-world evaluations across at least seven days, with at least 100 examples per proposed low-risk read-only intent. Deliberate test probes must be tagged/separated in analysis. Review the sampling bias from eligibility and cooldown. Keep data local and minimized.
3. Require at least 99% independently reviewed intent accuracy and 99% Core agreement per proposed intent, 99.5% schema validity, and zero unsafe/tool-authority violations. Review every mismatch and maintain a separate negative/ambiguous-input set (at least 100 cases). Core agreement alone is insufficient ground truth.
4. Require warm P95 <= 2 seconds, cold P95 <= 20 seconds, and no material Core response slowdown under representative GPU load. Measure rather than assuming these goals hold. Demonstrate failure and reconnect behavior repeatedly.
5. Review all regressions and privacy/security boundaries, and obtain explicit Phase 2 approval. Initial routing must be restricted to selected read-only intents. Side-effecting actions retain existing authorization and verification; no Qwen execution or memory ownership. No automatic cloud failover is authorized.

## Changed files and rollback

Modified four JS test fixtures, test_ollama_shadow.py and the original Phase 1 report. Added shadow_report.py, test_shadow_report.py, probe_desktop_shadow.py, this report and phase1-* evidence files. No production code changes in this follow-up. Existing unrelated desktop/frontend/branding working-tree changes are preserved and excluded from the commit.

Rollback the discrete validation commit to undo the follow-up; 1aac6f2 remains the separate shadow implementation rollback. JARVIS and restored Ollama remain running. No new service, port, routing, memory owner or security configuration was introduced. STOP before Phase 2.
