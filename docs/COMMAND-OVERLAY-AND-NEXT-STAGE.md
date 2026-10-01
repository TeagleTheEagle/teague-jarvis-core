# Command edge repair and proposed next stage

2026-09-11. Planning only for the next stage; no autonomous capability enabled.

## Visual repair

Both annotated lower edges showed the old body Earth wallpaper outside the fitted Command scene. A Command-only background override removes that duplicate wallpaper and its tint layer, leaving plain dark margins. Other pages retain their backgrounds. The live hologram and the reference scene are unchanged.

Changed: static/teague.css. Updated verification probe to save all three viewport screenshots. Browser checks at 1920x1080, 1280x900, 720x600 passed: centered single canvas inside viewport, normal System/Mission/Focus navigation, same canvas retained, background HTTP 200, no page errors. The 1920 screenshot was visually inspected and the duplicate horizon is gone. Full regression suite was not repeated for this CSS-only change. Live Electron refresh of this latest repair has not been separately confirmed.

## Proposed capability stage: one governed improvement loop

All four capabilities should share the existing authoritative JARVIS Core, memory, tools and authorization. First audit existing implementations to reuse them. The following is a proposed design, not a claim that these components are missing or already working.

1. Goal formation: propose and prioritize subgoals derived from user-approved objectives. Record why each goal exists, its owner, scope, budget, deadline and completion criteria. Ask before adopting unrelated objectives.
2. Autonomous execution: execute explicitly delegated, reversible tasks through existing authorized tools. Persist progress in shared task state, verify results, bound retries and duration, and honor stop/cancellation. No permissions are granted merely because a planner requests them.
3. Self-improvement: inspect failures, propose code or configuration changes on isolated branches, run fixed independent evaluations and PC regressions, and present measured candidates for review. Deploy only after the configured approval gate with a rollback point. Do not let the candidate weaken its own evaluations or authorization. This is iterative engineering, not a promise of unlimited recursive intelligence gains or model self-training.
4. Resource management: inventory user-owned compute, storage and API budgets. Schedule already-approved resources within hard limits; provide cost estimates for additions. Purchases, paid provisioning, new accounts, credentials or permission increases require specific authorization. Resources serve approved user tasks, never an independent objective of expanding or preserving the assistant.

## Suggested first combined experiment

User delegates improvement of one local deterministic test. JARVIS proposes a bounded subgoal, plans the change, uses only existing local tools and a fixed time budget, creates a patch in an isolated branch, runs tests, and returns evidence for review. No production self-deployment or resource purchase.

## Release order and acceptance

Design the four together, but release progressively: audit and constraints; shadow planning; isolated patch experiments; bounded task execution; approved resource provisioning. Preserve current Ollama shadow-only restrictions until Phase 2 is separately approved. Preserve prior Astra review gates for major Core/Gateway changes.

Required checks: one Core and canonical memory; permissions rechecked before each action; stop works during tool and provider work; restart does not duplicate execution; budgets cannot be exceeded through retries/subgoals; untrusted content cannot grant authority; evaluation failures block promotion; rollback preserves memory; resource requests cannot bypass approvals; existing PC voice/vision/tool regression suite passes.

No implementation of this next stage begins as part of the visual repair.
