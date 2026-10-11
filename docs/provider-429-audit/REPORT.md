# OpenAI 429 / Ollama fallback audit

Eight offline characterization cases passed. This confirms the observations below, NOT completion of fallback requirements. No Core/App/Store instantiated, production configuration read, real provider called, or runtime module changed. Synthetic environment credentials only. Source hashes are in results.json.

| Requirement | Result |
|---|---|
| Detect HTTP 429 | Yes, but insufficient_quota and rate_limit_exceeded receive the same rate-limit label. |
| Bounded attempts/no key rotation | Each simulated 429 caused exactly one HTTP attempt, no assistant output and no key change. Source caller retries connection/stream errors only, not this 429. |
| Check local availability after 429 | No. Shadow health checks exist independently, but no fallback health probe occurs. |
| Ollama/Qwen fallback | Not implemented. Local adapter is a closed-schema classifier; shadow observer has no authority over responses. |
| Continue request | No; ProviderError propagates to server run.failed. |
| Final provider/model provenance | Missing: both successful OpenAI adapter paths discard upstream model metadata. Configured model is not per-answer provenance. |
| Answer last-provider question reliably | Not guaranteed: no durable per-answer provider/model linkage in inspected response persistence path. |
| Truthful failure | Error propagates and no answer is fabricated. Message does not explicitly explain that local fallback is unavailable/disabled. |

Chat Completions sets retry_after=30 despite simulated Retry-After=7. Responses leaves retry_after unset. Neither distinguishes quota exhaustion. This audit did not test a live desktop, live Ollama availability, real HTTP traffic, or tool continuation.

Evidence paths: providers.py request/chat; server.py work provider exception handling, run.failed and assistant message persistence; ollama_provider.py closed intent schema/health; ollama_shadow.py non-authoritative observer; store.py message persistence. results.json records exact source SHA-256s.

## Minimum proposal; implementation requires separate review

1. Preserve sanitized structured provider/status/error code and Retry-After; distinguish quota from transient rate limit without logging upstream bodies or secrets.
2. Add explicit opt-in Core-owned fallback policy, separate from shadow classification. One bounded local health/model check and at most one approved fallback attempt per eligible request, preserving cancellation/deadline. Initially limit to text-only requests with no dispatched tools or partial answer; refuse replay of side effects and unsupported vision/tool requests. No second Core, provider credentials rotation, or authority expansion by inference.
3. Persist and expose per-answer actual provider/model, request/attempt identity, fallback reason and completion status. Label deterministic local answers separately. Retain upstream returned model when available; distinguish requested model from verified returned model.
4. Report primary failure and disabled/unavailable/unsupported fallback explicitly.

Potential reviewed file scope: providers.py, server.py, a dedicated local text adapter rather than repurposing ollama_shadow.py, response-provenance persistence in store.py or a reviewed existing record mechanism, tool/UI exposure and isolated tests. Schema/UI/configuration scope must be agreed before implementation. Existing Phase 1 shadow-only approval does not authorize this activation.

Validation proposal: both 429 categories/endpoints; local offline/missing model/timeout/malformed response; cancellation/deadline; one fallback cap; no key rotation; no duplicated tool execution; partial-output refusal; truthful durable attribution and last-response retrieval across sessions; existing provider and Core regressions. No correction implemented. Stage 4 and production gates unchanged.
