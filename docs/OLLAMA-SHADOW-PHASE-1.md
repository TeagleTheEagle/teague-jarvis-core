# Ollama/Qwen3 shadow mode â€” Phase 1

Follow-up: see `OLLAMA-SHADOW-PHASE-1-VALIDATION.md`. All regression blockers below are now resolved through test-fixture corrections. Production desktop-Core API online/interruption/recovery checks passed; the manual UI-typed request was confirmed by the user on 2026-09-11 and its shadow record matched. PHASE 1 IS ACCEPTED. See phase1-final-acceptance-evidence.json for final totals. Historical measurements below are preserved.

Date: 2026-09-11. Scope: additive classification telemetry, no authoritative routing.

## Result

Scoped implementation and live fixture checks passed. Full Phase 1 acceptance remains blocked by four pre-existing JavaScript regression failures. Do not promote Ollama to authoritative routing. Production desktop operation with this hook has not been manually verified or restarted during this task.

## Read-only audit and selected seam

The observed provider abstraction is functions in `providers.py`, including chat, request, capabilities and speech. There is no ProviderManager to extend. Existing provider selection supports OpenAI/Groq/Gemini; it remains untouched.

`server.App.work` uses existing memory/context handling, deterministic `actions.local_command`, answer-evidence and verified-status handling before tool or cloud processing. `App.tool`, existing action validation, authorization and result verification remain authoritative. The narrow seam observes an eligible deterministic command immediately before the existing `self.tool` call. A daemon worker compares Qwen output; no return value enters the execution path. Earlier memory answers and cloud-only requests are excluded.

The five added server lines import/create the observer, expose cached status through the existing authenticated state response, and submit eligible commands. No new listener, Core, database, registry, voice owner, credentials or service manager is created. Temporary App instances in tests/probes are isolated integration fixtures, not production services.

## Files

- Modified: `server.py` (five additive lines).
- Added: `ollama_provider.py` (transport, schema, health, classification).
- Added: `ollama_shadow.py` (eligibility, bounded worker, comparison records).
- Added: `test_ollama_shadow.py` (19 deterministic tests).
- Added: `probe_ollama_shadow.py` (explicit live fixture probe).
- Added: this report, `OLLAMA-SHADOW-LIVE-2026-09-11.json`, `ollama-shadow-python-check.txt` in docs.

Pre-existing desktop, frontend and branding changes are excluded from this repair's commit. No UI, startup launcher, memory, voice, provider selection or security configuration was changed.

## Configuration and schema

Fixed loopback endpoint `http://127.0.0.1:11434`, model `qwen3:4b`; think=false, stream=false, temperature=0, num_predict=160, num_ctx=2048, keep_alive=30 seconds. No dependencies or models were installed. The service was observed listening on 127.0.0.1:11434. No LAN binding or firewall change was made.

Shadow mode defaults enabled on the next normal Core startup. `JARVIS_OLLAMA_SHADOW=0` disables submission on restart; no .env was edited. Cached status is available at `capabilities.ollama_shadow` through the existing state interface, explicitly non-authoritative. Initial unchecked status is distinguishable by checked=false; health is sampled per evaluation, not continuously polled.

Required JSON fields: intent, target, action, parameters; unknown fields rejected. Intent enum reuses canonical names: open_app, system_health, service_status, device_registry, project_catalog, web_search, time_now, plus none. Targets are calculator/notepad/paint/unspecified. Action must be classify; parameters must be an empty object. App targets only accompany open_app. Exact types, duplicate fields, unexpected thinking/tool calls, incomplete generation and oversized responses are rejected locally as well as constrained by Ollama's schema.

Only short, closed-grammar commands for opening those three apps, reading time/date, diagnostics and project listing are eligible. Even these require a matching existing deterministic classification and reaching the hook. Attachments and wearable requests are excluded. Notes, arbitrary research, conversation history and freeform text are not copied. Close-application and volume are not forced into invented contracts. Schema coverage does not imply live evaluation coverage for every listed intent.

## Failure, lifecycle and observability

Health requests have one-second socket budgets each. Cold classification uses 20 seconds; warm uses 8 seconds, with bounded response reading and a 64 KiB cap. One worker, no queue, no retries; overlapping requests are skipped. Cooldown is five seconds after success and 60 after failure. Submission and worker failures are isolated from Core. Client timeout does not guarantee cancellation of inference inside Ollama; finite keep_alive limits requested residency, subject to other Ollama clients.

Records go to `provider-shadow.jsonl` under the existing Store root, rotated at approximately 1 MiB with one previous file. They contain IDs, normalized closed-enum classifications, match, schema validity, timings, model, sampled health and sanitized error codes. They contain no original command text, credentials, reasoning or memory. Disk failures are contained and surfaced as logging_error. Agreement is measurable over successful evaluations only; null comparisons and skipped requests must not count as matches. Agreement with a deterministic label is not proof of semantic correctness or successful tool execution.

## Verification actually performed

- Before changes: Python 147/147 passed (11.462 seconds).
- Final Python: 166/166 passed (12.693 seconds), including 19 new tests. Compilation and git diff whitespace checks passed.
- Desktop: 13/13 passed on post-change run. The initial baseline run had one inspection-job timeout/cancellation before this implementation.
- Broader root JavaScript suite: 12/16 test files passed. Four failures also reproduced against pre-change HEAD: test_conversation_voice.cjs (short-pause command count), test_timer_fast_path.cjs (cloud-call count), test_voice.cjs (callback/sample-rate checks), test_voice_cancellation.cjs (undefined pending cancellation entry). These are unresolved baseline failures, not claimed passes.
- New deterministic tests cover online/offline/missing model/timeout, strict schema and unknown intent, successful prediction, match/mismatch, busy worker/cooldown, disabled mode, sensitive-command exclusion, logging failure, fixed loopback transport and response limits, cold/warm budgets, unchanged cloud mock path and no tool execution from a conflicting Qwen prediction.
- Unit/regression tests disable live shadow traffic; new tests use fakes. Live service checks are separate.

## Live results

See the adjacent JSON for request IDs and full records. These used the real local service and existing Core work path with temporary storage; no production desktop session was launched.

| Fixture request | Core completed | Evaluation | Classification latency | Load duration | Health latency |
| --- | --- | --- | --- | --- | --- |
| what time is it | yes | cold, valid, time_now match | 3380.327 ms | 2302.012 ms | 27.961 ms |
| show my projects | yes | excluded: earlier memory path | n/a | n/a | n/a |
| what is the date | yes | warm, valid, time_now match | 866.779 ms | 1.546 ms | 2.630 ms |

Two valid evaluations, two agreements. This tiny sample does not establish broad accuracy. Total worker latency was 3408.335 / 869.443 ms; it is not user-response latency. An earlier cold attempt timed out at about 8.02 seconds without preventing Core completion. That evidence motivated the explicit 20-second cold budget; no retry loop was introduced.

## Run and rollback

From the canonical jarvis folder, `.\.venv\Scripts\python.exe probe_ollama_shadow.py` explicitly runs the live temporary fixture. It needs the existing local Ollama service and model. `.\.venv\Scripts\python.exe -m unittest test_ollama_shadow` runs deterministic adapter tests. Normal desktop activation waits for the user's next normal restart; microphone and screen sharing were not enabled for verification.

The discrete commit titled `Add loopback Ollama classification shadow observer` is the rollback point. Revert that commit to remove only these changes; retain unrelated pre-existing UI work. The environment switch provides a quicker reversible disable. Logs are diagnostic files, never a second canonical memory.

## Remaining limits and Phase 2 gate

Before any Phase 2: resolve/review the four baseline JS failures; manually verify the real desktop with unchanged voice and security settings; collect a larger privacy-approved representative shadow dataset, including mismatches and load contention; define accuracy, coverage and latency thresholds; review eligibility expansion, failure cancellation and GPU impact; review and explicitly authorize routing/authorization design. No automatic failover, execution authority or memory ownership is implemented or approved by this phase.

Risks include GPU contention, biased eligibility, cached health staleness and inference continuing after client timeout. No real cloud call, audible playback, long-running desktop session, universal classification accuracy, or revised Milestone 4 verification is claimed here.

Official API references: [Ollama chat](https://docs.ollama.com/api/chat) and [structured outputs](https://docs.ollama.com/capabilities/structured-outputs). These document format/schema, think, stream, lifecycle and timing controls used here.
