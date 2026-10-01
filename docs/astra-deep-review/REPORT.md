# Astra DEEP REVIEW — offline TEST milestone

Status: offline implementation/contract validation PASS. Live Astra capability, paid A/B quality comparison and production activation are NOT validated or enabled. Stage 5 not started.

## Exact routing and implementation

An authenticated TEST client must send operation `deep-review` with `review.mode=DEEP_REVIEW`, an idempotency operation ID, task, focused evidence packet and `effort=medium`. Ordinary chat never escalates automatically. Trusted TEST setup must explicitly enable `deep_review_fixture`; otherwise the endpoint refuses the request. The existing App/Core owns admission, owner/session identity, lifecycle worker, cancellation and persistent response history. No second production App or independent provider owner was created.

`stage4_deep_review.py` builds Responses API payloads for exactly `gpt-6-astra`, with `reasoning.effort=medium`, store:false, stream:false. No temperature/top_p/top_logprobs/logprobs or logprob include fields. A single function, read_evidence(id), reads only the in-memory packet admitted with this request. It has no filesystem, memory-store, network, shell, device, repair or consequential action access. Evidence instructions cannot add tools. Existing general tools are denied for deep-review runs.

Limits: 1–4 uniquely named evidence records, each text <=1500 UTF-8 bytes, title <=100 bytes, task <=1000 bytes, serialized review <=8000 bytes. Per provider call <=16000 serialized bytes, max_output_tokens=1024, two provider calls maximum, one packet read maximum, final answer <=12000 bytes, total estimated-token reservations <=40000. The transport is given a 20-second absolute deadline; late responses are rejected. Higher effort is refused in this initial milestone rather than inferred from ordinary requests. Enabling higher effort requires a separate explicit bounded policy.

Important elapsed-time boundary: offline fixture calls return promptly. The engine checks cancellation/deadline before dispatch and after each return. A future real transport must enforce the supplied deadline during network I/O. It is not safe to plug in a non-cooperative blocking callback and claim it can be forcibly stopped; existing Core lifecycle retains ownership if safe worker termination is unconfirmed. No remote transport or TEST network exception was added in this milestone.

## Provenance and credentials

Uses the existing stage4_response_provenance table and JSON field; no schema/Store change. Records explicit routing reason, requested provider/model, returned provider/model and Responses ID, reasoning effort, per-attempt token counts, aggregate usage, elapsed time, estimated token reservations/cost, simulation label and final status. Only status:completed plus complete assistant content can be published. Failed/cancelled responses have no actual final provider/model and do not replace the last successful response.

Owner-scoped `response-provider(response_id)` queries persist across a fresh TEST App process; the existing last-response-provider query remains supported. No owner can use the endpoint to read another owner's record. Duplicate request IDs/operations do not cause another provider execution; restart preserves idempotency.

Credential reuse authorization is recorded as user approval only. This implementation did not read, copy, rotate, log, archive or transmit the existing OpenAI key. The TEST Core still sanitizes environment and denies production .env/network access. Real Responses transport/credential attachment is intentionally not wired through those boundaries. Before live validation, review a bounded use of the existing authoritative credential holder and grant a paid-call budget; do not copy the key into TEST configuration to bypass isolation.

## Validation performed

- 24 offline boundary/unit tests PASS: explicit mode, evidence bounds, medium effort, no unsupported parameters, completed status required, returned model/ID and usage required, tool allowlist, foreign evidence denied, duplicate argument rejection, iteration limit, cancellation/timeout uncertainty, no retry, output/usage limits and reasoning not exposed in provenance.
- 14 real isolated TEST App/dispatcher integration checks PASS: owner/session enforcement, provenance, packet-only tool, general-tool denial, duplicate suppression, cancellation, normal tools unchanged, history reopen and one App/Store/Voice/Wake.
- 8 authenticated named-pipe probe checks PASS, including Stage 1 reconciliation, one TEST instance, completed review, by-ID provenance, duplicate suppression and authorized shutdown/lifetime-lock release. The inherited harness console says “Electron checks”; no Electron window was used in this particular probe.
- 4 fresh TEST App restart checks PASS: provenance by ID, owner isolation, no duplicate execution and one TEST composition.
- Regressions: 212 Python, 29 desktop, 22 fallback-router, 12 existing fallback integration checks PASS.
- Python sources compiled in memory; no production imports or writes for compilation. No Stage 1–3 full-suite rerun is claimed for this request.

All test data is synthetic. No production database/configuration/lifecycle change; protected production source hashes were verified unchanged. No acceptance commit was created.

## Fixed comparison and cost evidence

integration.json records the same synthetic incident/task on ordinary TEST chat and explicit DEEP REVIEW. The rubric is fixed: accurate evidence IDs, findings versus hypotheses, no unsupported historical causation, missing original traceback/native error identified, and read-only next step without invented execution. Both provider outputs are fixtures. No model quality score or superiority conclusion is justified; actual latency/token usage/cost fields for model comparison remain null.

The Responses fixture reported 200 input + 80 output tokens across two calls. These are synthetic contract values, NOT measured Astra usage. At the documented standard input/output rates this gives a hypothetical $0.006 usage estimate. The byte-based pre-dispatch reservation was 5420 estimated tokens and $0.13612; this is deliberately separate from reported usage. Estimates are not invoices or hard billing guarantees and do not fully model cache-write/other processing tiers. Actual paid requests made: zero. Cancellation or timeout after real dispatch would be POTENTIALLY_BILLABLE_UNCERTAIN, never automatically refunded as zero.

Official references consulted on 2026-09-12:
- https://developers.openai.com/api/docs/guides/latest-model — Responses tool calling, medium reasoning, unsupported parameters.
- https://developers.openai.com/api/docs/models/gpt-6-astra — model ID and standard $10/M input, $50/M output pricing.
- https://developers.openai.com/api/reference/python/resources/responses/methods/create — response ID/model/status/output/usage contract.

## Exact files changed and rollback

Edited: stage4_runtime.py; stage4_response_history.py.
Added: stage4_deep_review.py; tests/test_stage4_deep_review.py; tests/astra_deep_review_integration.py; tests/astra_restart_probe.py; tests/build_astra_pipe_probe.py; generated tests/astra_pipe_probe.py. Reports/source snapshots/hashes are under docs/astra-deep-review.

Before-images of the two edited files are in before/. Roll back only this task's diff after comparing current source with those snapshots; do not reset unrelated working-tree changes. Disable deep_review_fixture and remove the TEST deep-review/response-provider dispatch additions and deep-review tool guard branch as a single reviewed rollback. Existing provenance data need not be deleted. No production data rollback is required.

Residual gates: real existing-credential attachment, paid model/account access and A/B evaluation, real provider timing/usage and active-I/O cancellation/drain, and any future renderer exposure. Production remains blocked. STOP FOR REVIEW.
