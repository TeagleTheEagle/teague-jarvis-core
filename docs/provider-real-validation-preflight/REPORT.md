# Real local fallback validation preflight

BLOCKED: live TEST transport is not implemented. Prior offline integration passes remain valid only for simulated generation.

Read-only local GETs to 127.0.0.1:11434/api/version, /api/tags and /api/ps succeeded. Ollama version 0.34.0; qwen3:4b installed, 4.0B, Q4_K_M, digest 359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7. Installed file size 2,497,293,931 bytes is model storage, not runtime RAM/VRAM consumption. No models loaded at observation.

stage4_runtime.py selects offline_router and its audit hook denies socket.connect. stage4_provider_fallback.py has injected/deterministic envelopes only and marks all records simulated=true. ollama_provider.py implements closed-schema shadow classification, not general text response generation. It cannot be substituted without implementing the response contract. Calling Ollama outside the Core would not prove the requested path.

No real generation, final response, live provenance, Electron fallback, latency/throughput/load-time/resource-use measurements or cancellation/drain validation was performed. No Core launched. No OpenAI calls, physical voice, source/configuration/database changes or Stage 5. No regressions rerun because no implementation changed. Preflight JSON contains exact API observations and source hashes.

## Minimum implementation scope requiring review

Add a TEST-only loopback text-generation transport, fixed to 127.0.0.1:11434 and approved qwen3:4b, with bounded health/chat endpoints, response size/context/token/time limits, cancellation, no tools, no redirects, no remote hosts, no model pull/start/install and no credentials. Wire it through the existing text-only router. Keep OpenAI failure injected/offline.

Permit that exact loopback connection in the isolated TEST runtime only under explicit trusted-parent opt-in, retaining all other network/process denials. Preserve generation-vs-delivery distinction and record mixed provenance honestly: simulated OpenAI attempt, real Ollama response, returned model identity. Do not leave a blanket simulated=true or falsely relabel the OpenAI attempt as real.

Proposed files: new stage4_ollama_transport.py, minimal stage4_runtime.py and stage4_provider_fallback.py integration/provenance changes, isolated transport and request/client validation tests. No production provider/Store/authentication/ownership changes.

Validate rejection of remote/unsupported destinations, absent model, invalid output, cancellation and deadlines before one real text-only request. Then verify persisted owner-scoped attribution, duplicate prevention and existing lifecycle shutdown. Use the current authenticated TEST client only if safely supported. Preserve all failures. Rollback only new TEST hunks/files after verified TEST cleanup; never alter production or delete evidence.

Stopped for implementation review; this is not a Qwen generation failure and not a successful real fallback validation.
