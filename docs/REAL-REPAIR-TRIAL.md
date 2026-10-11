# First real generated repair — 11 September 2026

Result: READY_FOR_REVIEW. Real existing JARVIS Core generated `return max(0, seconds)` to repair the supplied negative-delay fault. Baseline passed 4/6 independent fixed cases; candidate passed 6/6. Provider timing 2761 ms, buffered first-token measurement 2761 ms; entire successful trial 3.406 seconds. Evidence: repair-trial-result.json.

## Scope and architecture

No second App/Core, provider client, canonical database, voice owner or device registry. Reused wearables.real_core.RealCore as the existing authenticated same-PC read-limited text client. This temporarily uses its existing local-wearable-client interaction identity; it does not register a new device or implement a new gateway. Provider credentials stay in Core. The exercise and answer can be stored as an ordinary conversation in the existing shared store under a unique wearable-repair-trial ID; no second memory is created. The provider receives the small fixture prompt through normal Core context construction, which can include existing relevant context. No new keys or provider settings.

The first request failed before generation because the conversation ID lacked the bridge-required wearable- prefix. Fixed in the trial client, then successful. No security boundary or server code changed. Exactly one successful Core request; no candidate retry loop or promotion.

## Isolation and interpretation

Docker executable not found; WSL reports not installed. No OS features or security policies were changed. Consequently this first trial uses a restricted numeric AST interpreter, NOT general Python execution. Only a single delay(seconds) function, a return, finite bounded numeric literals, seconds, unary minus and two-argument min/max are accepted. Input length and AST size are bounded. Imports, file access, attributes, loops, decorators, defaults, arbitrary calls and additional statements are rejected before evaluation. No eval, exec, compile or subprocess is used for model-generated text.

Existing development.prepare stages the validated text against a temporary fixture named wake.py solely to satisfy the existing allowlist; this is NOT production wake-word code. The fixed independent checks are never supplied by the model. The fixture source remains unchanged. Temporary staging is cleaned up; candidate, hash and diff remain in the report. Nothing is deployed.

This demonstrates a genuine generated patch and its numeric behavior under a supported subset. It does not prove arbitrary Python runtime correctness, general OS sandboxing, autonomous discovery, self-training, or production self-repair. Existing bridge request timeout/cancellation is reused; cancellation acknowledgement depends on a responsive Core and is not an OS kill guarantee. No resource purchase or allocation, screen capture or TTS was requested. One provider response incurs normal configured provider usage; exact cost was not measured.

## Reproduce

Verification: full Python discovery passed 177/177 in 14.748 seconds, including four new tests for numeric correctness, rejection of execution paths, bounded inputs and the existing client contract. The earlier 14-test targeted run passed before the live prefix correction; full discovery passed afterward. Desktop tests were not repeated because no desktop or production integration code changed; live desktop voice was not exercised.

With the existing desktop Core running: `.venv\Scripts\python.exe repair_trial.py`. This makes a live provider request and writes docs/repair-trial-result.json. Unit-only checks: `.venv\Scripts\python.exe -m unittest test_repair_trial`.

Next milestone: review the general execution-isolation design before running arbitrary generated patches. Preserve existing major Core/Gateway review gates; no automatic deployment or Ollama Phase 2 enabled.
