# Bounded provider fallback — isolated implementation / integration review gate

Status: OFFLINE ROUTER VALIDATED; END-TO-END CORE INTEGRATION INCOMPLETE.
Production remains unchanged. No provider calls, Core launches, credentials, or Stage 5. No acceptance commit.

## Implemented scope

- stage4_provider_fallback.py: TEST-only router with injected buffered transports; no App/Store/process/network/credential creation. One primary attempt, at most one health check and one local attempt. No retry or tool execution. Mode must be STAGE4_TEST.
- tests/test_stage4_provider_fallback.py: 22 offline checks. All passed on first run; full output tests.txt.
- This directory: evidence, pre-edit runtime snapshot and unactivated integration draft.
- stage4_runtime.py was experimentally wired to the router, then restored byte-for-byte from before/stage4_runtime.py when the integration boundary was identified. The draft is retained solely as review evidence and is NOT an active runtime module.

## Routing

Primary HTTPFailure distinguishes rate_limit_exceeded, insufficient_quota and other HTTP429. Temporary limits retain numeric/HTTP-date Retry-After; absent/invalid values remain unknown. 500/502/503/504 are eligible; authentication/other noneligible primary failures stop. No raw provider error bodies are exposed.

Fallback requires enabled policy, zero tool attempts, zero partial output, text-only messages, no tool requirement/history/tool calls, bounded context, ONLINE approved local model and remaining cancellation/deadline budget. A missing/wrong actual model, incomplete/empty response or tool output fails closed. Duplicate request IDs cannot execute providers again. Model and provider records distinguish configuration, attempts, returned actual model, fallback cause and generation status. All injected results explicitly carry simulated=true.

The deadline is checked before/after transport calls; transports must honor it themselves. No background workers are spawned to pretend a blocking call was cancelled. Live transport behavior has not been implemented or tested.

## Checks

A–D: OpenAI success and temporary/quota/other429. E–H: healthy/offline health and local success/failure. I–J: returned model provenance, configured versus actual model. K–L: zero-side-effect fallback and prior-tool refusal. M–P: no credential machinery, one attempt per provider, duplicate-request refusal, no Core construction (module-only tests). Additional cancellation, deadline, missing/wrong model, local tool output, vision/tool-required refusal, disabled policy, authentication failure, retry-date handling and returned status copy isolation.

These are router tests, not real authenticated Core/client acceptance. No real Ollama model was called. History persistence, last-response natural-language retrieval, session ownership integration and live provider cancellation remain unverified/unimplemented. No claim that JARVIS can now fall back.

## Integration boundary / minimum next review

The existing real TEST App supplies tool schemas for free-form chat. Conservatively, those requests are tool-capable and fallback is refused. Dropping the schemas automatically would silently downgrade capability. The router's requires_tools input must come from a trusted, explicit request contract, not a guessed text classifier or a renderer assertion that overrides Core authority.

Review a bounded text-only TEST request mode: default normal requests preserve their tools and refuse fallback; explicit text-only requests permit no tool actions on either provider and retain Core-authenticated ownership, cancellation and lifecycle registration. Extend the authenticated TEST request schema/client adapter only as needed to request this mode. Core must enforce it.

Also review linking final (not merely generated) provenance to the existing owner-checked response/history record, and exposing a deterministic last-response provenance query without sharing another client's private history. The router.status method alone is not authenticated history. The integration draft records provenance after App completion and does not yet solve atomic publication/final-response linkage or last-response retrieval; do not activate it.

Proposed subsequent files: stage4_runtime.py plus the reviewed TEST client request interface in stage4_client.cjs and applicable TEST renderers, isolated integration tests; any shared server.py hook needed to preserve an explicit no-tools contract must be gated and reviewed. No Store/schema modification is proposed here.

## Rollback and residual risks

Active runtime was restored. Remove only the two new router/test source files to discard this implementation; retain evidence. Do not revert unrelated changes or production configuration. Compare source hashes to hashes.json and runtime before/current hashes. No database migration or rollback operation is needed.

Residual limits: simulated transports only; no HTTP envelope adapter/live health; no authenticated durable history; transport deadline cooperation required; records are in-memory and duplicate protection is process-local; no guarantee across restart; no automatic handling of an already-generated but unpublished response. Production activation and Stage 5 remain blocked.
