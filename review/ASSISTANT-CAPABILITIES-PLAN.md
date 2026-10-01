# Assistant controls, inspection archive and latency plan

Status: source inspection complete; implementation not applied.

## Verified existing implementation

- `static/app.js` directly recognises show/open hologram, start/stop sharing,
  and screenshot/analysis requests. `desktop/preload.cjs` exposes showCompanion.
  There is no corresponding hide/status bridge in that file. The activate alias
  is missing. Existing controls should be reused, not duplicated.
- `actions.py` registers inspect_interface, development_history, list_items,
  save_item and set_timer. It does not register timer adjustment/cancellation,
  saved-memory update/delete, persistent inspection retrieval or a general
  controller for microphone/hologram status.
- `inspection_jobs.py` retains completed jobs in memory for five minutes.
  `inspection_runtime.py` separately expires captured images. Persisted report
  storage must not extend screenshot retention.
- `workspaces.py` already links indexed documents to projects. A read-only
  database query confirmed project `Project Jarvis`, ID
  `0383e8c2e67346b59c484a5766b581f4`. There was one project in this database.
  Resolve and validate this ID against the active store when linking; never
  reuse it for synthetic test stores or silently create a substitute project.
- `server.py` buffers the first provider response's events until chat() returns,
  to avoid duplicated text after a stream retry. This can delay visible text.
  It is an observed implementation behavior, not a measured cloud bottleneck.
- Frontend diagnostics already measure transcription, first delivered response,
  total AI response and speech generation. First delivered response is NOT the
  provider's time to first token when the server buffers events.

## Implementation order and affected files

1. Timing: instrument server queue/context preparation, provider first delta and
   completion, retries and tool durations. Expose bounded timing metadata to the
   existing voice diagnostics in `static/app.js`. Do not log transcript text,
   audio, screenshots or credentials. Collect actual request samples before
   changing retry/streaming behavior. Test fake-clock timings and cancellation;
   label synthetic timings and live measurements separately.
2. Controls: narrow registered schemas in `actions.py`, routing in `server.py`,
   and handlers reusing the existing frontend controls in `static/app.js`.
   Add only hide/status companion operations to `desktop/main.cjs` and
   `desktop/preload.cjs`, retaining existing trusted-sender checks. Use request
   IDs and frontend acknowledgements so a request is not reported as success.
   Unmute from a muted microphone cannot be heard; text/button activation is
   needed. Opening a companion must not start microphone or capture.
3. Report archive: add a local archive module and terminal-job hook in
   `inspection_jobs.py`, wired by `server.py`. Store immutable dated Markdown
   documents plus structured inspection/tracker records transactionally in the
   existing storage layer; link reports through `workspaces.py`. Preserve
   requested/captured/analysed/partial/failed/cancelled states and omitted panels.
   Retain findings and coverage metadata, not raw screenshots, DOM text dumps,
   credentials or temporary image links presented as durable evidence.
4. Retrieval/tracker: list/read/compare reports and filter findings with narrow
   read tools. Use stable finding IDs, preserve original reports, and append
   evidence-backed status history separately. Never promote an applied change
   to verified from model prose alone. Include change IDs, actual test records
   and rollback references. Do not add Copy whole inspection.
5. Timers/memory: exact-ID list/update/cancel tools backed by transactions in
   `store.py`. Ambiguous human descriptions require selection. Reject missing,
   expired/fired timers and nonexistent memory IDs; preserve credential checks
   and duplicate prevention. Return success only after a committed operation.
6. Pending development: reuse `development_history` and current approval UI;
   make retrieval/status explicit. Do not expose self-approval to the model.

## Validation and risks

- Archive tests: restart persistence, immutable report contents, duplicate
  completion callbacks, missing project, partial results, failed disk writes,
  malicious report content, screenshot exclusion and evidence-linked tracking.
- Controls: runtime/browser tests for successful acknowledgements, denied
  permissions, disconnected renderer, timeout, cancellation and repeated calls.
- Timers/memory: exact-ID targeting, ambiguity, successful persistence, duplicate
  prevention, fired-timer races, missing records and credential rejection.
- Performance: verify cancellation/retry behavior before changing buffering;
  never repeat consequential tool actions to improve perceived latency.
- Test isolated candidate code with temporary databases first. Preserve backups
  and source hashes for review. Stop installation if live sources changed.
- Rollback: restore approved source backups; preserve archived evidence and
  existing data. Document any added tables without deleting user records.

## Required review-method clarification

The supplied prompt says “Prepare executable changes for interface approval”.
The current `development.ALLOWED` excludes `server.py`, `actions.py`, `store.py`,
`inspection_jobs.py`, new backend modules, `desktop/main.cjs`, and
`desktop/preload.cjs`. Those files are needed above. Expanding that allowlist
would change the permission boundary and is not included in this task.

The user has been asked whether these backend changes can instead be prepared
for review in Codex while keeping JARVIS's own approval rules unchanged. Until
that answer, no backend changes, new archive, new tools or speed improvement
should be described as implemented.
