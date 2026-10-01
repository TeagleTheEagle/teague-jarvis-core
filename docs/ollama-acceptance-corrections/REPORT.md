# Two TEST-only Ollama acceptance corrections

Status: PASS for the two approved corrections. STOP FOR REVIEW. This is not production activation or full Stage 4 acceptance. No Stage 5 work or paid OpenAI/Astra request was performed.

## Exact changes

- `stage4_ollama_transport.py`: the bounded loopback qwen3:4b request now uses `think:true`. Only structured `message.content` is returned, unchanged. Separate thinking is not forwarded. Missing/empty final content, malformed thinking fields and tool calls fail validation. No text-stripping heuristic was added.
- `stage4_client.cjs`: the fixed TEST acceptance driver renders the authenticated result into the existing `#messages` / `.execution .empty` response container. It no longer creates an artificial result element. Before capture it checks exact response ID/text, computed visibility, viewport bounds and two advancing animation frames. The readiness check fails after three seconds; it does not use a long sleep. Production UI and renderer modules were not edited.
- `tests/test_stage4_ollama_transport.py`: payload, structured separation, malformed response and exact ordinary-content preservation tests.
- `tests/build_real_ollama_probe.py` and its generated `tests/real_ollama_validation.py`: new evidence directory and assertions for the actual container, clean answer and current rendered frame.

Endpoint remains exactly 127.0.0.1:11434. Authentication, ownership, Core-enforced text-only admission, provenance, duplicate prevention and lifecycle implementation were not changed.

## Performed validation

| Validation | Result |
|---|---:|
| Real local Qwen / authenticated Electron acceptance | 26/26 |
| Transport unit tests | 16/16 |
| Offline router tests | 22/22 |
| Isolated provider integration | 12/12 |
| Fresh-process history persistence | 4/4 |
| Existing Python regressions | 212/212 |
| Desktop and Intelligence tests | 29/29 |

JavaScript syntax and Python in-memory compilation checks passed. Protected production/shared file hashes match the pre-change baseline; see validation.json. These totals are separate suites, not a claim of that many distinct end-to-end scenarios. Stage 1–3 full suites were not rerun in this narrow correction turn.

The real prompt was “What is 2 plus 2? Answer only with the number.” Final content was exactly `4`. The authenticated TEST Core and Electron client received it; the existing conversation container held the matching response ID and text. The screenshot was inspected visually and shows `4`, without thinking text or an artificial overlay. The driver exercises the real authenticated response path and existing DOM container; this is not a manual Send-button usability test.

The same run verifies one TEST Core, no tool events, duplicate response identity, cancellation without false successful provenance, client close/reopen and reauthentication to the same Core, persisted last-provider lookup, authorized bounded shutdown and released lifetime ownership. TEST clients and Core exited normally. Physical voice remained unavailable.

## Provenance

OpenAI failure was simulated: no OpenAI network request. Actual generation used Ollama / qwen3:4b. Stored provenance records fallback=true, temporary_rate_limit, owner/session, response ID and completed generation. Last-response lookup returned that persisted provenance, including after reattachment and history restart. This does not represent the simulated primary failure as a paid provider event.

Installed-model evidence in the preceding diagnosis identifies Ollama 0.34.0 and Qwen3-4B-Thinking-2507, Q4_K_M, tag qwen3:4b, digest 359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7. The real response identifies qwen3:4b; no model download or replacement was performed.

## Observed performance

- Driver request: 7.015 seconds.
- Transport wall time: 5.953 seconds.
- Ollama total: 5.942 seconds; model load: 2.637 seconds.
- Prompt evaluation: 55 tokens, 0.281 seconds.
- Generation evaluation: 221 tokens, 3.020 seconds, 73.19 tokens/second. These evaluation tokens include thinking; they are not 221 user-visible answer tokens.
- Time to first token was unavailable with buffered transport. CPU/RAM/GPU/VRAM were not measured.

## Evidence and limitations

Primary evidence: real-ollama-electron-184474f33a3043318fda81571afc3ab9.json and electron-final-answer.png. Exact before/after source, diff, regression logs and SHA-256 manifest accompany this report. Earlier failed runs and screenshots in docs/real-ollama-test and docs/ollama-acceptance-diagnosis are preserved, not overwritten by the passing result.

This is one fixed arithmetic request, not a broad model-quality evaluation. Structured final content is preserved byte-for-byte; literal ordinary text including think-like tags is not heuristically removed. Future model variants can behave differently. Existing output/deadline limits remain; thinking consumes generation capacity and longer requests may fail closed. Cancellation at the Core does not prove the local backend consumed no resources or stopped computation immediately. The successful shutdown follows cancellation/completion; it is not a new physical-media or active-provider emergency-stop demonstration. No broader Stage 4 gate, historical incident classification, or production block is cleared here.

## Rollback

Review source-changes.diff and restore only the five changed files from the included before/ snapshots, after confirming no subsequent edits would be lost. Do not reset the working tree or touch production data/configuration. Preserve all evidence. Reverting restores the known thinking-display and acceptance-driver defects, so rerun the focused tests before any further acceptance claim.

Production database moved/modified: NO. Production Core restarted: NO. Production configuration/authentication changed: NO. Production activation: NO. Stage 5 started: NO. No acceptance commit created.
