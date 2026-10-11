# Interface inspection — candidate ready for installation review

9 September 2026. **Not installed.** Running JARVIS source, credentials, permission enforcement and startup behavior were not modified. The isolated review dependency folder contains Playwright 1.62.0; the running virtual environment was not changed.

## What the candidate does

Recognized requests such as “Inspect Communications” or “Look at the Communications page and analyse it” open an inspection report dialog and start a local inspection. The underlying selected panel stays in place. “Inspect the whole interface” processes the 13 supported panels sequentially, bounded by a five-minute queue budget. General model-routed requests use an allowlisted `inspect_interface` tool that returns a review button; it cannot submit images or capture arbitrary targets itself.

The authenticated Python endpoint reads a frozen SQLite snapshot using mode=ro and query_only, never `App.state()`/`store.due()`. A fresh headless Chrome instance renders the application's real HTML, CSS and component scripts. Every resource request is intercepted: a fixed local static manifest and four in-memory snapshot responses are served; all other requests are denied. The hidden browser never receives authentication cookies, a personal profile or a desktop bridge. No new unauthenticated endpoint, permission bypass or change to existing authentication is introduced.

The isolated initialization disables interval callbacks and hardware/browser APIs; explicit frontend guards prevent voice, mic enumeration, speech, reminder chimes and sends. The renderer checks panel selection, component roots, completed fetches and fonts before capture. It records stage statuses, section offsets, bounded text/roles, omissions, elapsed time and ephemeral image references. An initial viewport or up to six section captures can be requested.

Local inspection makes **no external AI request**. The user can select a clearly labelled checkbox naming the configured recipient and run again for visual analysis. This choice resets on the next command. The provider receives a tools-disabled analysis request. If unavailable, the report remains explicitly DOM-only; it does not claim visual understanding.

## Deliberate limitations

- **Layout inspection, not private-content analysis.** All user-authored messages, filenames, item text and project names are replaced before rendering. This prevents free-text secrets from leaking without claiming regex can detect every credential. It changes wrapping/lengths. Settings values, project links and change-history records/diffs are omitted. Change History therefore captures its panel shell only.
- External maps, embedded content, unsaved drafts, browser preferences, desktop-only controls and live diagnostics are unavailable. The report says so. A snapshot cannot verify service connectivity, microphone performance or working buttons.
- Long panels are bounded, not complete. Internal scroll containers are sampled; virtualized or clipped content can be omitted. Per-image DOM evidence is included; aggregate text and controls are capped.
- Chrome must be installed. Playwright is an added dependency. Missing browser/dependency/render failures return an unavailable report. The dependency was downloaded to the review folder only.
- Stop/Close prevents subsequent panels. It does not interrupt an already-running capture/provider request; an already submitted image cannot be recalled. Closing discards visible results. Do not describe this as an immediate emergency cancellation feature.
- Captures are held in memory for five minutes, max 18 retained images across jobs. Expiry cleanup runs even without another request; authenticated image requests also enforce expiry. Browser report images remove themselves after five minutes. No actual user captures were created during development. Synthetic fixture screenshots in `review/inspection-test-*.png` are retained as test artifacts.
- No external vision-provider call or live headset test was performed. Provider availability, actual cost and end-to-end voice latency remain unverified. No claims of continuous/live screen vision.
- Resource interception deliberately omits network-dependent appearance and does not duplicate all HTTP response headers. Visual results describe this isolated rendering, not a byte-for-byte reproduction of an active desktop window.

## Files in the complete patch

| File | Purpose |
|---|---|
| `interface_inspection.py` | Fixed tool schema, input validation and empty evidence contract |
| `inspection_runtime.py` | Read-only snapshot, isolated capture, masking, evidence, bounded retention and optional analysis |
| `actions.py` | Register the inspection tool |
| `server.py` | Existing authenticated dispatch for inspection and expiring image retrieval; analysis-only provider adapter |
| `static/app.js` | Inert inspection guards and tool-result review control |
| `static/index.html` | Load inspection UI script |
| `static/inspection-client.js` | Request routing, local capture/report UI, explicit transmission choice and sequential inspection |
| `requirements.txt` | Add Playwright 1.62.0 |

The reviewable diff is `inspection-complete.patch`; exact original/candidate SHA-256 values are in `inspection-manifest.json`. Candidate files are in `inspection-candidate/`. The earlier daily-briefing patch remains separate and is not included.

## Tests actually run

| Check | Result |
|---|---|
| Existing backend suite loaded against candidate server/actions | **78 passed**, 8.875 s |
| Inspection contract unit tests from first stage | **8 passed**, 0.001 s |
| Final runtime suite with real isolated Chrome | **10 passed**, 22.218 s; includes subtests rendering all 13 panels |
| Candidate authenticated route dispatch | **4 passed**, 0.007 s; missing cookie/cross-origin denied; invalid inputs rejected before worker |
| Real-browser inspection controls with stubbed backend | **1 passed**, 1.372 s; request routing, per-request consent, sequential 13-panel loop and ordinary-chat fallback |
| Syntax | 4 Python modules parsed; 2 changed JavaScript files passed `node --check` |

Runtime checks covered seeded-secret exclusion, due reminder unchanged, database bytes unchanged, missing DB not created, invalid origins, no-consent analyzer suppression, provider-failure fallback, timeout cleanup/lock release, expired images, parallel-job rejection, six-capture bounds, and a separate browser page retaining its draft/scroll/URL. All panel captures recorded zero prohibited side-effect attempts. Communications and Settings captures were visually inspected. Failures were simulated where stated; provider success was not tested.

## Installation approval and rollback

Installing server/action/new-module changes is outside the application's existing executable-edit allowlist (`development.py`, documented in `DEVELOPMENT-WORKFLOW.md`). This is an application workflow limitation, not an automatic security rejection. No allowlist expansion is proposed. Obtain approval for this exact complete patch before installing it externally.

After approval: verify every original file hash against the manifest; back up the original affected files; stop JARVIS cleanly; install Playwright 1.62.0 in its existing Python environment; apply the candidate files; restart and perform an authenticated local inspection in the real desktop app. Retain source backups and record installed hashes. Do not reinstall unrelated speech dependencies.

Rollback: stop JARVIS, verify affected files still match installed hashes, restore only backed-up originals, remove only newly added inspection modules/client if unchanged, restore the requirements manifest and restart. Preserve later user edits and all databases/configuration. The optional Playwright package can remain unused; removing it is not necessary to restore behavior.

No installation, restart, credential write or live-data mutation has been performed by this review work.
