# Two Ollama acceptance issues — diagnosis only

No correction was implemented. stage4_ollama_transport.py and stage4_client.cjs remain byte-for-byte identical to the preserved pre-diagnosis source. Production unchanged; Stage 5 not started. Earlier failed runs and the successful transport/provenance trial are retained.

## 1. Qwen thinking in final content

Established for the installed model and tested request: the local qwen3:4b tag identifies Qwen3-4B-Thinking-2507. Its template inserts an opening think tag. This is a thinking-only variant, not the switchable original Qwen3-4B model.

Two bounded requests differed only in think:false versus think:true, using the existing numeric-loopback transport request method, same prompt, no tools, 256-token cap and 20-second deadline:

| Condition | Raw fields | Final content | Completion |
|---|---|---|---|
| think:false | role, content; no thinking field | 888 characters, including reasoning and closing think tag | done:true, reason:stop |
| think:true | role, content, thinking | content exactly `4`; separate 877-character thinking field | done:true, reason:stop |

Evidence: thinking-comparison.json and raw-think-false.json/raw-think-true.json, with hashes. Earlier real-ollama-test/local-model-metadata.json records installed template and variant. The new diagnostic did not normalize, strip or rewrite response text.

Conclusion: for this exact tested Ollama 0.34.0/model/template combination, think:false did not suppress the model's reasoning and did not expose it as a separate field. The adapter passed message.content through; it did not invent the reasoning. Its current nonempty-thinking rejection would also reject a correct structured think:true response. This is an output-contract mismatch involving a thinking-only model, not a failed provider connection. We have not established a universal Ollama think:false defect across other models.

Minimum proposed correction, NOT implemented: explicitly request think:true for this fixed model; permit the provider's structured thinking field without publishing it; use only nonempty message.content as the final answer after done:true/reason:stop/model/tool checks. Reject ambiguous embedded reasoning delimiters in content rather than stripping arbitrary text. Preserve the token/deadline cap and clear incomplete-generation failure. Pin or verify the expected installed variant/digest so a mutable tag cannot silently change the assumption.

Files that would change: stage4_ollama_transport.py and tests/test_stage4_ollama_transport.py; the real_ollama_validation.py acceptance fixture/generator needs final-content assertions. No provider routing or Core ownership change is needed.

Focused validation: raw structured thinking remains separate; clean content delivered; no content after incomplete/empty/malformed result; tool calls rejected; model mismatch denied; duplicate/cancel/provenance regressions; real short request and preserved over-token failure. The 256-token cap may make longer thinking requests fail safely; increasing it is a separate review.

Sources read: https://huggingface.co/Qwen/Qwen3-4B-Thinking-2507/blob/main/README.md?code=true documents thinking-only behavior and the template's opening tag; https://docs.ollama.com/capabilities/thinking documents structured thinking/content fields. Local raw responses, not generic documentation alone, establish behavior for this installed instance.

## 2. Electron receives the answer but screenshot misses it

Established in an authenticated offline TEST reproduction, without a live provider call:

- The trusted TEST driver receives the completed response and provenance, then executeJavaScript writes them to PRE#test-fallback-result directly under body. Thus the renderer DOM DOES receive the text.
- The real conversation DIV#messages remains unchanged at the original 136-character attachment notice. The driver bypasses the normal renderer's message-state/display path.
- The new PRE has display:block, visibility:visible and opacity:1 at all three observed times (immediate, +250ms, +1000ms). It remains in the DOM with 253 characters; no overwrite was observed.
- The first capture still shows the old frame, without the PRE or its layout shift. A later capture shows the PRE at the top and the application shifted downward. The original test waited for JS completion, not a verified painted frame.
- The PRE is static with z-index:auto, outside .shell. static/teague.css sets body::before to a fixed z-index:0 overlay with rgba(6,12,20,0.93) on Communications; .shell is positioned at z-index:1. The later screenshot shows PRE text heavily dimmed behind that overlay.

Evidence: ui-diagnostic-cc87bea3e13d4059a3bd84dfe379d645.json contains authenticated transport result, three DOM samples, geometry/styles/timing and screenshot paths. screenshot-immediate.png and screenshot-delayed.png were visually inspected. A fixed in-memory instrumentation module loaded the unchanged TEST client source; no runtime source file was rewritten. The test used one disposable TEST Core and both Core/client exited normally.

The diagnosis shows two issues: wrong display destination/stacking and capture before a new painted frame. It does not demonstrate lost authentication, provider failure or overwritten response data. The inherited fixed diagnostic display label says “real local response” even for the offline fixture; actual provenance correctly says simulation. Future display wording must come from provenance, not a hardcoded driver label.

Minimum proposed correction, NOT implemented: send text-only final responses through the existing visible renderer output container/state, using textContent and preserving the existing trusted bridge. Render provider labels from saved provenance. After the exact response ID/text is committed, wait for a paint acknowledgement before capture and assert the text is in the intended visible viewport. Do not fix it with a global z-index change or by weakening CSP/authentication.

Files that would change: stage4_client.cjs and tests/real_ollama_validation.py (plus its generator); intelligence/stage4-renderer.js only if the implementation routes through its existing write function rather than the fixed TEST-driver display seam. The approved correction should name the selected minimal approach before edits.

Focused validation: exact final text and response ID present in visible #messages/.execution .empty; capture after paint; immediate and delayed observations agree; initial placeholder replaced; no clipping/overlay at normal and smaller windows; simulated/real labels truthful; existing auth/owner/cancel/reattach/lifecycle tests still pass. Physical voice remains unavailable.

## Rollback and review

There are no output/display corrections to roll back. Diagnostic code is in tests/ollama_thinking_diagnosis.py, tests/ollama_ui_diagnostic.cjs, tests/build_ollama_ui_diagnostic.py and generated tests/ollama_ui_probe.py. The native/authenticated client source was instrumented only in memory for fixed read-only DOM observations. Removing these diagnostics changes no production behavior; preserve the evidence.

For any later approved correction, save source before-images and roll back only its scoped diff; retain failed-run evidence and provenance. No ACL, model installation, credential, schema, production routing, lifecycle or approval change is proposed. STOP FOR REVIEW before either correction.
