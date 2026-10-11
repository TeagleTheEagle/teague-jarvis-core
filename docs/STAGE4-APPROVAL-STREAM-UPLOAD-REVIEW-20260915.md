# Stage 4 approval / stream / upload ownership gate

2026-09-15 — **PARTIAL / STOP FOR SCOPE REVIEW.** No runtime implementation or new integration PASS is claimed. Only this gate was investigated; no next gate was started.

## Finding

The current validated TEST surface is an authenticated named-pipe dispatcher plus the restricted Electron ordinary-operation bridge. It does not serve the legacy HTTP Handler. `server.main` explicitly refuses Stage 4 construction. The legacy application's approval and upload implementations therefore cannot simply be treated as supported TEST workflows.

Source inspection establishes:

1. `stage4_runtime.py:Authority.operation` exposes `request-status` after `check_owner`, returning the owner's event list and completion state. Each pipe request has bounded handling and closes its pipe. `stage4_client.cjs` permits request/status/cancel through its fixed ordinary operation map. This is event polling, not a persistent SSE/WebSocket stream.
2. Neither that dispatcher nor the ordinary Electron map exposes approval list/use or upload/create/discard/use. Unknown operations reach the existing denial path. This is a source finding, not a fresh negative integration test.
3. `stage4_runtime.py:Context.check_tool` allows only time_now, list_items, read_conversation and search_conversations for normal TEST requests; text-only/deep-review requests cannot execute tools. The existing approval-producing preview/development actions are outside this TEST allowlist. `start_request` passes `attachment=None` to the actual App worker.
4. `server.py:App.approve` consumes an approval before checking expiry and originating-run cancellation, but has no authenticated Stage 4 session parameter/check before consumption. It can route to preview actions, development application or process launch. Exposing it as-is would not preserve the required owner and authority boundaries. This is not a claim that it is currently remotely reachable from TEST or a newly observed production exploit.
5. Legacy `/api/upload` extracts decoded content, creates an attachment, and indexes text into Store. Its records are not bound to a Stage 4 request/session family. Legacy discard only removes a matching screen-capture attachment; it is not general cancellation or reversal of indexing. Calling it directly in a fixture would bypass the TEST transport/admission/ownership boundary and would not prove the requested integrated workflow.
6. Legacy `/api/runs/.../events` is itself long-polling under a condition, not SSE. Its global run-ID lookup is not the authenticated TEST `request-status` operation. Starting the legacy HTTP server to exercise it would add an unreviewed listener/lifecycle surface.

The files are already named in the broader design, but file inclusion alone does not authorize exposing additional routes/actions. The current request explicitly requires STOP if broader routes or authority are needed. That condition is met before approval/upload integration can be implemented honestly.

## Supported / unsupported workflow assessment

| Requirement | Current evidence and status |
|---|---|
| Same-owner approval; foreign denial before consumption; one use; approval expiry | **OPEN for integrated TEST workflow.** No approval creation/use endpoint or approved approval-bearing TEST action. Legacy implementation and generic owner checks are not substitutes. |
| Approval revocation on disconnect, drain/shutdown; rejection after admission closes | **OPEN for approval workflow.** General session/work cancellation exists, but no integrated approval ownership/revocation path is evidenced. |
| Stream/event ownership and foreign-session read/control denial | **PARTIAL.** Supported event polling uses the actual owner check. Preserved authenticated App and actual Electron results prove foreign read/cancel denial, same-owner completion, reattachment without old request authority. No new tests were run here. |
| Stream cancellation, cleanup and no late writes after ownership loss | **PARTIAL.** Existing cancellation/drain protections and worker tests are relevant, but a complete pending-event-poll/cancel/detach race and late-output/persistence matrix is not established by the current evidence. No independent persistent stream worker exists to certify as cleaned up. Legitimate terminal audit/settlement of already-started work must remain distinct from unauthorized new content writes. |
| Upload ownership, cancellation/cleanup, foreign inspection/control denial and no late indexing | **OPEN for integrated TEST workflow.** Uploads are unavailable; attachment extraction/indexing and request use would require a defined TEST route, owner mapping and commit/cancellation boundary. No upload was performed. |
| No restored authority on reconnect | **CLOSED for existing requests/controller recovery**, supported by the already validated controller and Electron evidence; **not established for absent approval/upload workflows**. |

### Are exclusions permitted?

The design permits unsupported operations to fail closed. It does **not** permit counting that denial as completion of its explicit approval/stream/upload integration requirements. Design section B says list/stream/approval/upload endpoints require ownership checks, and section I requires pending-approval revocation. The latest acceptance checklist explicitly states that denied unsupported operations do not certify the approved workflows.

A nonexistent persistent SSE/WebSocket stream need not be invented: the applicable stream requirement can be tested against the supported owner-bound event-polling mechanism. Approval and upload exclusion from Stage 4 acceptance would, however, require an explicit acceptance-scope decision. No exclusion is assumed in this report, and no fabricated approval or upload feature was added to make a cell pass.

## Minimum decision before implementation

Review an explicit TEST-surface contract for the two missing workflows, or explicitly defer them in the acceptance criteria. If integration is required, the minimum contract must specify:

- The genuine existing approval-bearing TEST workflow/action permitted. Bind the originating approval to authenticated ownership before lookup/consumption; retain the actual one-use/expiry semantics and existing action authorization. Do not enable development application or process launch by exposing generic `App.approve`.
- The supported TEST upload types/size and lifecycle: admission, owner-bound attachment, extraction worker, cancellation, indexing commit and attachment use. No general path access, arbitrary parser/provider expansion or credential-bearing files. Preserve existing schema; if that cannot be done, return for schema review.
- Use the existing authenticated transport/ordinary bridge where feasible, rather than adding a legacy HTTP listener. Exact operation/argument names and authority must be reviewed before exposing them. Event polling should retain its current protocol, with focused owner/cancel/drain validation rather than a new streaming subsystem.

Likely existing file boundaries for a reviewed contract: `stage4_runtime.py`, `stage4_sessions.py`, gated `server.py`, `tests/lifecycle_stage4/fixtures.py`, `tests/lifecycle_stage4/test_stage4.py`; only if actual Electron workflow access is required, `stage4_client.cjs`, `desktop/preload.cjs`, `static/app.js` and `intelligence/stage4-renderer.js` need their exact interface delta reviewed. This is a scope map, not authorization or a final patch. No new module, Store/schema change or generic tool permission is proposed here.

After that decision, use real isolated App/Store plus authenticated TEST clients with synthetic content: same/foreign owner, duplicate/expired/revoked approval, admission races, polling cancellation/detach/drain, upload extraction/commit cancellation, late-result rejection, reconnect without inherited authority and independent TEST state comparison. Capture every failure, then run directly affected ownership/lifecycle/App/client regressions. Test no paid providers, real repair or production data.

## Evidence, tests and rollback

- **New integration tests: 0. Regressions rerun: 0.** Stopped on the explicit scope condition before creating new routes, action authority or a synthetic workflow. No generic model test is offered as an integration PASS.
- Preserved prior evidence, not rerun: [45-check authenticated expiry/App result](lifecycle-stage4-evidence/real-app-probe-34049809379e42c8ae55903a0363fd22.json), [29-check actual Electron result](lifecycle-stage4-evidence/electron-app-probe-ba76c336d41c454ba35934626c336b80.json), [52-check recovery result](lifecycle-stage4-evidence/controller-recovery-892e0d7e456b4b92a21672e4123ca10f.json), and [reviewed source/validation report](lifecycle-stage4-evidence/controller-recovery-20260915/REVIEW.md).
- Read-only evidence includes source hashes and line-numbered excerpts in `lifecycle-stage4-evidence/approval-stream-upload-review-20260915/`. The four final controller-correction sources still match their validated snapshots; no implementation changed.
- No new failed runtime run exists from this inspection; all prior failures remain untouched. Search-command truncation or unmatched search globs are not application test results.
- Files changed: this review, a link in the remaining-requirements checklist, and new documentation/evidence manifests/copy proof only. No source test, runtime, configuration, database, credentials or process was changed.
- Rollback: no runtime rollback is needed. Documentation can be superseded by a reviewed contract; retain this finding and hashes rather than removing historical evidence. A later implementation must snapshot its exact pre-edit source and preserve TEST state/failed runs on rollback.

**GATE: PARTIAL. Stage 4 paused at this scope review. Production unchanged and blocked. No acceptance commit. No Stage 5.**
