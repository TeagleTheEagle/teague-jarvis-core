# Bounded TEST-only Ollama transport — review required

Overall acceptance: **INCOMPLETE / NOT ACCEPTED**. Real generation and authenticated delivery to the Electron main process succeeded, but final-answer cleanliness and visible renderer delivery failed independent review. No production activation or Stage 5.

## Implementation and boundary

- `stage4_ollama_transport.py`: numeric AF_INET/SOCK_STREAM connection exclusively to 127.0.0.1:11434; no DNS/proxy/redirect/retry; GET /api/tags and POST /api/chat only. Fixed qwen3:4b, 4096 context, 256 output tokens, buffered response, think:false. 20-second maximum router deadline, 2-second health deadline, 64-KiB request and 128-KiB response bounds. Cancellation/deadline watcher interrupts the socket; bounded watcher join and response cleanup. No model pull, shell, tools or credentials.
- `stage4_runtime.py`: trusted isolated TEST parent must explicitly opt in. Existing disposable-process audit hook permits only that endpoint and still denies DNS, other connections, sendto and external process execution. Core text-only admission and normal tool path remain separate.
- `stage4_provider_fallback.py`: distinguish simulated primary/no network from actual local generation in attempts and final provenance; preserve actual model and observed generation metrics. Primary remains a fixed simulated 429; no paid OpenAI event occurred.
- `stage4_client.cjs`: fixed trusted TEST-parent action invokes authenticated text-only admission, status, cancellation and last-provider query. No added renderer credential/native/lifecycle access. Its attempted display in a prepended pre element was not visible in the captured image; this display gate remains failed.
- Tests added: `tests/test_stage4_ollama_transport.py`, `tests/ollama_audit_boundary.py`, `tests/real_ollama_validation.py`, and its deterministic scaffolding generator `tests/build_real_ollama_probe.py`.

## Preserved real trials

1. `real-ollama-electron-c0836089e06748188cbf9334cf02f50d.json`: sky explanation reached local generation, rejected as invalid/incomplete; no successful response persisted. Detailed response-shape diagnosis was not present yet.
2. `real-ollama-electron-28148512edc84e6f96abf4f91c3d27b7.json`: instrumented separate trial confirmed matching model, done:true, done_reason:length, no structured thinking or tools, 1233 content characters. The 256-token cap was retained; truncated completion rejected.
3. `real-ollama-electron-fc4c82a589a7455c9a4b79f832ca07f3.json`: separate arithmetic request reached natural completion, returned a final 4 with unwanted reasoning and a closing think tag in content. The 23 automatic checks passed, but they were insufficient to establish answer cleanliness or screenshot visibility. Independent review records both failures in acceptance-review.json. Do not read “23 PASS” as end-to-end acceptance.

Every live trial used one new disposable namespace sequentially, with exactly one App/Store/Voice/Wake recorded. Every TEST Core/client exited normally with exit code 0. No replacement production Core, production database, production configuration, or production lifecycle was touched. The separate existing production Core was never a test target.

## Provenance and lifecycle evidence

The completed arithmetic response persisted owner teague, session, response ID, request_mode:text-only, final_status:COMPLETED, actual provider Ollama, actual model qwen3:4b, fallback:true, temporary_rate_limit. The attempted OpenAI entry explicitly says simulated:true/network_request:false; Ollama says simulated:false/network_request:true. The deterministic last-provider query returned the saved values. Reopened authenticated client and a fresh history-reading process obtained the same record. Existing fresh TEST App restart regression also passed.

The duplicate operation returned the original response ID without starting another worker/generation. Cancellation produced run.cancelled, no assistant.completed, and did not overwrite the last successful provenance. There were no tool events. The client closed/reopened while the same TEST Core retained ownership. Authorized shutdown completed within the probe's 8-second wait and released its lifetime lock.

Cancellation of a local socket is NOT proof of zero Ollama resource consumption or immediate server-side inference cessation. The real cancellation test was immediate; it does not establish mid-generation Ollama compute termination. Deadline interruption is covered offline. Shutdown while real inference remains active has not been independently measured here; idle/after-cancellation shutdown passed.

## Validation

| Check | Result / evidence |
|---|---|
| A/B endpoint boundary | 13 transport tests plus 9 actual TEST audit-hook event checks; fixed opt-in endpoint accepted, other hosts/ports/DNS/UDP denied. Synthetic audit events do not make unauthorized connections. |
| C/D real Qwen and Core receipt | PASS for arithmetic; earlier truncated trials preserved. |
| E TEST client receipt/visible display | Main process receipt PASS; screenshot visible answer FAIL. |
| F/G persistent provenance/query | PASS, including correct simulated/real distinction. |
| H/I tools/duplicates | PASS in integration and real request event records. |
| J cancellation | PASS for Core outcome and bounded client return; server compute cessation unverified. |
| K shutdown/drain | Normal authorized shutdown after cancellation PASS; active-inference drain not separately measured. |
| L–O unavailable/timeout/malformed/generation errors | Offline transport and router cases PASS; Ollama was not stopped to force a real outage. |
| P persistence | Same data in new authenticated session, fresh history process, plus 4 existing fresh TEST App checks PASS. |
| Q router regressions | 22 PASS. |
| R Python/desktop | 212 Python and 29 desktop PASS. |
| Core text-only integration | 12 PASS. |

The initial Electron-as-Node regression command produced an empty output file; it is NOT counted as test evidence. The subsequent host Node run has the explicit 29-test summary. No Stage 1–3 suite rerun was claimed for this transport-only task. Physical voice remained unavailable. JavaScript syntax and Python source compilation were checked separately.

## Observed performance and model

Ollama 0.34.0; qwen3:4b digest 359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7. Read-only /api/show identifies Qwen3-4B-Thinking-2507, Q4_K_M. Its template appends an opening think tag. This supports the observed thinking-in-content behavior despite think:false; no model/template was modified.

Completed trial: 7.187 seconds full trusted-driver request; 6.407 seconds transport wall time; Ollama reported 6.388 seconds total, 2.929 seconds load, 221 generated tokens, 3.123 seconds evaluation, 70.776 evaluation tokens/sec. This is one sample, not a throughput benchmark. TTFT unavailable because response is buffered. CPU/RAM/GPU/VRAM utilization not sampled during generation. Later /api/ps returned an empty list; it does not establish peak usage.

## Minimum proposed follow-up for review — not implemented

1. Resolve this installed Thinking model's output contract: use an explicitly supported thinking-aware response mode and accept only a complete, separately identified final answer; reject missing/ambiguous separation. Do not strip arbitrary text heuristically or accept truncation. Validate against the exact installed model; any larger token/deadline budget or model replacement requires review.
2. Render the TEST result in the existing visible `#messages` / `.execution .empty` container, then check actual text visibility and capture the result. Preserve the ordinary renderer/preload boundary.
3. Add final-answer/visibility assertions to the acceptance probe; repeat successful delivery, mid-generation cancellation and active-inference drain after the output contract is reviewed.

## Rollback and limitations

Before-images of the three edited modules and the unchanged response-history module are preserved in before/. To roll back this task, compare the saved baseline with the current files and revert ONLY this task's diff; do not use git reset or overwrite later work. Disable the trusted real_local_ollama TEST opt-in and remove references to the new transport. New tests/evidence can remain as review records. No production rollback or database migration is required. No acceptance commit was created. Production remains blocked; Stage 5 unauthorized.
