# Interface inspection: first-stage review

Prepared 9 September 2026. Status: repository inspection and isolated contract candidate only. No running application files changed; no tool registered; no screenshot captured or transmitted.

## Observed architecture and blocker

- `actions.py` registers JSON-schema tools and validates arguments. Its `navigate_panel` allowlist includes the 13 requested panels plus Screen Vision. `server.py` returns `navigation_requested`; `static/app.js` handles that event by moving the visible interface. Inspection must use a different tool/event.
- `static/app.js` owns the real `view(name)` routing, render functions, voice controller, and recurring work. `static/workspaces.js`, `static/maps.js`, `static/diagrams.js` and `static/reliability.js` add panel content asynchronously. A fixed sleep is not a readiness signal.
- The Python server authenticates API requests with its session cookie and validates local Host/Origin. Static mappings are explicit. Do not weaken these checks or export session secrets to renderer JavaScript.
- **Opening the ordinary page in a hidden context is not read-only.** `App.state()` calls `store.due()`, which executes `UPDATE reminders SET fired=1`. `renderReminders()` can chime; app timers refresh state and send proactive briefings; desktop preferences may enable microphone on launch. `workspaces.js` also loads `/api/state` during initialization.
- `providers.chat(..., vision=True)` selects the configured image model. `server.py` already builds image messages from attachments. Configuration is not a successful vision test. Ordinary chat/image ingestion can persist messages or index attachments, so inspection needs a separate ephemeral analysis path.
- Desktop currently includes Electron 44.2.0. Playwright is not declared in the desktop package. Browser-only use must not depend on a running desktop window.

Safe rendering therefore requires an explicit inert frontend initialization path plus a genuinely read-only data snapshot. This is an architecture change, not just a new screenshot button. This document explains the blocker before changing the application.

## Proposed architecture

Use a backend-owned Playwright worker with a fresh nonpersistent context per job, after approving the additional dependency. This supports both the browser and desktop frontend without copying a browser profile. An Electron hidden window would reuse the installed engine, but would couple browser-only inspection to the desktop process and require new bridge routing. Prefer a single inspection implementation for both clients.

The context renders existing HTML/CSS/components, fed a frozen, redacted snapshot of actual saved data. It does not recreate the interface. Browser requests for snapshot routes are fulfilled in memory; normal state, action, upload, OAuth, provider, external map, WebSocket and event-stream routes are denied. Static requests use a fixed manifest at the configured local origin, with redirect destinations checked too. Only the trusted worker uses existing server authentication. Never put the session cookie in logs, tool arguments or DOM.

Snapshot acquisition uses a separate SQLite connection in read-only/query-only mode and an explicit SELECT allowlist. It must not call `App.state()` or construct another live App/Store that initializes jobs or databases. Existing in-memory diagnostics may be copied with timestamps; unavailable runtime state is labelled unavailable. Browser-only preferences, unsaved drafts and transient page state are omitted unless deliberately passed as bounded display preferences. Report these differences from the user's current page.

Inspection mode is supplied by the trusted worker before any frontend script executes; a URL flag alone is not a security boundary. Separate render initialization from live service startup. No microphone enumeration/capture, audio context, speech, notifications, reminder chime, proactive task, live refresh or desktop bridge. Deny those permissions in the context as a second layer. Service workers, popups, downloads and external frames are blocked. Render a truthful 'Inspection snapshot — microphone inactive' state.

## Phased changes and affected files

1. **Contract (candidate prepared now):** proposed `interface_inspection.py` initially contains strict panel/scope/focus validation and empty evidence states. Current review candidate is `review/inspection_contract_candidate.py`; `review/inspection-contract.patch` is the reviewable addition. It does not implement or register the tool.
2. **Inert real rendering:** change `static/app.js`, `static/index.html`, `static/workspaces.js`, `static/reliability.js`, `static/maps.js`, `static/diagrams.js` as needed; introduce `static/inspection.js`. Expose bounded panel rendering/readiness, track each component's completion or failure, suppress live effects at their startup points. Keep interactive initialization unchanged outside inspection mode.
3. **Read-only snapshot and worker:** proposed `inspection_snapshot.py`, `inspection_worker.py`, dependency manifest, and focused tests. One job at a time, server-owned origin, immutable resource manifest, temporary context, cancellation and deadlines. No persistent screenshot directory or general browser API exposed to the model.
4. **Tool integration and consent:** `actions.py`, `server.py`, narrowly scoped `providers.py` adapter and `static/app.js` status UI. Register `inspect_interface` only when the worker exists. Require explicit user inspection intent, not merely an unsolicited model call. Ask once for inspection-image transmission if existing consent does not cover it; show the configured recipient. Do not infer consent from primary-display authorization or screen-capture permission.
5. **Acceptance testing and rollout:** tests below, then staged installation and browser/desktop validation. Keep the existing briefing patch separate.

## Capture and analysis behavior

- Inputs: panel from the 13 requested IDs, scope `viewport` or `full_panel`, optional focus up to 2,000 characters. Unknown fields rejected. No URLs, source paths, code or clicks. 'Whole interface' is a trusted orchestrator loop over the same fixed list, not arbitrary multi-step model automation.
- Proposed limits: viewport 1440 x 900; at most 6 captures per panel, 2,000 visible elements and 20,000 text characters; 20-second render deadline per panel and 5-minute whole-interface deadline; one provider request at a time. These are design limits, not benchmarks. Report skipped panels after the aggregate cap/cancellation.
- Call real panel renderer; verify active navigation and expected visible panel root. Wait for explicit component readiness and fonts; freeze decorative motion before capturing. Fail readiness honestly when content cannot load.
- For `full_panel`, enumerate visible internal scroll containers and capture bounded overlapping sections. Restore isolated scroll positions. Record offsets, total scroll extent, virtualized/unknown totals, clipped regions and budget omissions. Never declare complete coverage solely from a full-document screenshot.
- Before any capture/text extraction: remove password/token fields, credential-bearing URLs/attributes and marked secret regions. Sanitize snapshot strings before rendering. Mask unknown embedded content. If secret exclusion cannot be established, withhold image submission and report that limitation; regex matching alone cannot guarantee arbitrary free-text secrets are absent. Test seeded secrets in messages, inputs, links and rendered content.
- Return requested/verified panel, snapshot/capture timestamps, viewport, per-section coverage, omissions, redacted visible text and accessible roles/names, ephemeral screenshot references, provider identity, separate stage statuses and errors. Stage states begin `not_attempted`; they do not imply success.
- Use a separate analysis-only model request with **no tools**. Mark DOM/image content as untrusted evidence. Model text cannot invoke mutations. If the model fails or consent is absent, offer a deterministic local DOM report labelled 'DOM only; no image analysis'. Do not send DOM text externally as a hidden substitute for image consent.
- Final report: purpose, observed elements, key findings with capture references, limitations, next steps. Screenshot evidence establishes appearance, not service connectivity or working controls.
- Images/text remain in job memory. If a runtime requires temporary files, use a private per-job temporary directory, cleanup in `finally`, and remove expired leftovers on next inspection startup. References expire on dismissal or after 5 minutes. No page content in logs or saved conversations by default; explicitly saving the report is a separate user action. Disclose that provider submission cannot be recalled; provider retention policy still applies.

## Risks and validation gates

| Risk | Required evidence before enabling |
|---|---|
| Hidden read writes reminders | Isolated fixture database SQL trace and before/after content comparison; no UPDATE/INSERT/DELETE during snapshot/render. Separate authorized report-saving tests. |
| Duplicate voice/jobs | Instrument mic/audio/notification/startup/proactive code; assert zero starts in inspection, including reminders already due and mic-on-launch preference true. |
| Active page moved | Two real contexts; compare active tab/panel, focus, scroll and draft before/after inspection. |
| Wrong or incomplete panel | Each supported ID, delayed component, failed component, empty and long/virtualized lists; verify root, readiness and coverage metadata. |
| Secret leakage | Seed secrets across sources; assert absence from DOM/AX output and provider payload; inspect masked screenshots. Reject uncertain content rather than promise universal detection. |
| Destination escape | Reject tool URL/code fields; deny redirects, external subresources, popups, downloads, WebSockets and unexpected local API requests. |
| Misleading model success | Consent denied, missing model, timeout, invalid response and cancellation: stages and DOM-only report remain accurate. |
| Orphan workers/captures | Fail at each lifecycle stage; assert context closure, temp cleanup and expired reference rejection. |
| Resource use | Measure per-panel render/provider latency and peak worker memory on this PC. Record provider usage if returned; do not invent cost when pricing/usage is unavailable. |

## Review/approval and rollback

`DEVELOPMENT-WORKFLOW.md` and `development.py` allow staging certain frontend files but exclude `server.py`, `actions.py`, desktop bridges and new service modules. Installing this proposal through the current interface is therefore unavailable. Do not expand the allowlist or weaken permissions to force it through. The user can approve an exact external review patch after the complete implementation is prepared, or choose a frontend-only limited alternative. This contract patch is not that complete implementation.

Before eventual installation, retain original files and lockfile, record hashes, apply the reviewed cohesive patch, and run regression/acceptance checks. Roll back only if current hashes match installed versions, preserving later edits; stop inspection workers and restore originals. No schema migration, credential changes, startup change or live data deletion is proposed.

## Current validation scope

Ran `.venv/Scripts/python.exe review/test_inspection_contract.py`: **8 tests passed in 0.001 seconds**. They cover strict input validation, supported panels, bounded focus, schema controls, independent evidence and initially unverified statuses. They do not exercise authentication, rendering, isolation, secret masking, screenshot lifecycle or vision. No runtime feature is claimed complete.

Framework references: [Playwright context isolation](https://playwright.dev/docs/browser-contexts), [Electron sessions and nonpersistent partitions](https://www.electronjs.org/docs/latest/api/session). These document framework capabilities, not proof that JARVIS implements them.
