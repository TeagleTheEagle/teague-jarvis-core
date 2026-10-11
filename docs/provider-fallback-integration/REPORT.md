# Bounded TEST fallback integration

Outcome: offline TEST integration PASS. Production activation remains blocked; Stage 5 not started. No paid calls, real Ollama calls, production Core restart, or production database changes. No acceptance commit.

## Implemented

`request-text-only` is an explicit authenticated TEST operation with text and an idempotency operation ID. Core admission checks request scope and lifecycle state. Its worker never calls App.work, command classification, or a tool dispatcher. Both buffered provider transports receive only text messages/model/cancellation/deadline, never tool schemas. Tool output from either provider is refused. The Core's check_tool separately rejects any text-only Run. Normal `request` continues through App.work and its existing tools unchanged.

`last-response-provider` accepts no owner supplied by the renderer. The authenticated Stage 2 client binding and session determine the stable enrollment owner; read scope is required. Reauthenticated sessions of that same owner can read history after restart. Different owners cannot read it. Original ephemeral session family is recorded for attribution, not reused as authentication. This is a client/enrollment owner boundary, not a newly implemented human-account system.

One new table, `stage4_response_provenance`, lives in the existing canonical synthetic TEST jarvis.sqlite3. No second Store, memory database, production schema, lifecycle, or authentication service. Existing application_id must match TEST identity; mode=rw cannot silently create a missing database. The TEST audit guard recognizes only the exact canonical TEST database URI in rw mode, alongside its existing ro mode; arbitrary database access remains denied.

Records include response ID, authenticated owner, original session, timestamp, request mode, final status, configured model, provider/model attempts, actual returned model/provider, fallback flag/reason and simulation flag. Final response text and provenance commit together before the completed event. Normal responses also receive provenance distinguishing deterministic Core output from the existing synthetic provider. The deterministic query uses persisted final records, not current provider configuration. Reported provider identities in this validation are SIMULATED, not real model generation.

Owner+operation uniqueness and a request fingerprint prevent duplicate provider execution, including after process restart. Changed payload under the same operation is refused. Pending/failed attempts are not replayed. Failed/cancelled generations do not enter the completed-response query. Cancellation is serialized against final persistence through existing ownership locking. Committed completion followed by disconnect remains a completed historical response; delivery itself is not asserted.

## Validation

- 12 real isolated App/Context integration checks PASS, covering A–P combinations: both successes, 429 categories, offline/generation failure, normal tools, text-only tool rejection, actual attribution, owner binding/isolation, cancellation, duplicate prevention and deterministic persisted history query.
- 4 fresh-process checks PASS: new isolated Context/App using the same TEST database, reauthenticated owner history, foreign-owner exclusion, duplicate prevention, and one App/Store/VoiceEngine/WakeDetector per isolated runtime. This did not exercise the named-pipe restart coordinator or Electron reopening.
- 22 offline router tests PASS.
- 212 existing Python regressions PASS.
- 16 existing desktop/Intelligence adapter tests PASS.
- Python in-memory compilation and JavaScript syntax validation PASS.
- Production providers.py, ollama_provider.py, ollama_shadow.py, server.py and store.py hashes match the previous read-only audit.

The final integration run passed 12/12 again after the normal-provider attempt metadata refinement. Exact outputs are preserved alongside this report; validation.json and hashes.json provide machine-readable records.

## Failed development evidence

integration-first.txt: fixture omitted the required TEST_ONLY marker. No App was constructed. Fixture corrected.

integration-second.txt: new SQLite rw URI was refused by the existing isolated database audit guard. 1/12 checks passed; other checks failed closed. Corrected the exact canonical TEST URI recognition, without allowing arbitrary paths. integration-third.txt passed 12/12. Earlier failures are retained, not erased by later success.

## Files changed

- stage4_runtime.py: authenticated explicit mode, lifecycle dispatch, tool guard, final provenance recording/query, exact TEST database URI support, offline router setup.
- stage4_client.cjs: allowlisted TEST operations and exact argument validation; no production client behavior changes.
- stage4_provider_fallback.py: trusted-parent-selected deterministic transport fixtures. Original routing safety checks retained.
- stage4_response_history.py: new canonical TEST database provenance table/access.
- tests/provider_fallback_integration.py and tests/provider_history_restart.py: isolated validation.
- This evidence directory. Source copies, pre-edit snapshots and changes.diff are included.

## Rollback

After verified TEST workers exit, restore only this change's hunks in stage4_runtime.py, stage4_client.cjs and stage4_provider_fallback.py from before/ or changes.diff; preserve unrelated later changes. Remove the three new implementation/test files if desired. Preserve synthetic database/evidence. Do not delete history or migrate production. Existing production files require no rollback. Source snapshot paths reproduce the reviewed change without credentials.

## Limits / review

All provider generation is deterministic/offline and labelled simulated. No real HTTP/OpenAI/Ollama transport, model quality or live network cancellation was tested. Existing TEST external-network denial remains. Transports must cooperate with deadlines; no false claim of forced cancellation. Unfinished PENDING reservations remain uncertain and non-replayable across restart; they do not masquerade as completed responses.

The new operations are exposed through the existing gated TEST bridge, not a new visual UI. Tests exercised the trusted authenticated dispatcher seam plus existing adapter regressions; no new manual Electron/UI test or full named-pipe end-to-end fallback test was performed. Stage 1–3 suites were not rerun for this addition; those modules and semantics were unchanged. This is not full Stage 4 acceptance or authorization for production. STOP FOR REVIEW.
