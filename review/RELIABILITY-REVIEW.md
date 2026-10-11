# Reliability review — 9 September 2026

## Confirmed changes

Applied only the supported personality change, with backup and diff in development proposal `716fe370fbd54a0d9b82d32770066dc7`. It asks for fresh briefing evidence, distinguishes unavailable from empty results, preserves news freshness uncertainty, requires confirmed action outcomes, and clarifies ambiguous saves. It also removes the instruction to treat all returned headlines as current. The server reads personality.txt for each model-backed conversation turn. Model compliance has not been tested against a live provider; instructions are not programmatic enforcement.

## Briefing fix: prepared, not installed

Evidence: server.py's daily_briefing branch calls news before reading any local sections, uses store.items('project') while the Projects workspace uses workspaces.listing, and discards news_search's retrieved_at value. Initial acceptance run: six tests, three passes, one failure and two errors reproducing these gaps.

`briefing.patch` changes only the daily_briefing branch. `server_candidate.py` is an isolated review copy, not a launcher or installed server. The candidate checks sections independently, reads the workspace catalog, preserves news retrieval timestamps, reports per-section ok/empty/unavailable states, labels list truncation, and measures check durations using a monotonic clock. Errors expose a generic unavailable message, not exception contents. Published dates remain in news items; old retrieval metadata is preserved rather than overwritten with a new timestamp. The candidate does not enforce a headline freshness cutoff; the updated personality instructs the model to disclose old or undated items.

Benefit: a news outage no longer hides local tasks and reminders, and a blank result no longer silently implies successful checking. Risk: consumers must honour checks metadata; broad exception handling yields an unavailable section rather than propagating its failure, which can make debugging less specific. Workspace entries have names and links rather than legacy project body fields. No frontend rendering of this candidate has been verified.

Approval limitation: DEVELOPMENT-WORKFLOW.md and development.py exclude server.py from interface approval. No pending interface approval was created, and the allowlist was not changed. Applying the server diff requires explicit permission for a direct source edit outside that interface workflow. Do not apply the whole candidate file over later changes; review the narrow patch against the current server first. Rollback: reverse that patch after confirming its changed block has not subsequently changed, then restart the backend. No database migration is involved.

## Other requested areas

| Area | Evidence and next improvement | Risk / approval / validation / rollback |
|---|---|---|
| Action status | Existing Python tests cover approvals, denial, cancellation, single-use execution and provider failure. Navigation returns navigation_requested. Applied personality clarifies that requested is not completed. A comprehensive UI action-state audit remains pending. | No action gateway changes. Any future executable change must be reviewed; test terminal states and rendering before claiming completion. Roll back a future patch through its recorded diff. |
| Regression coverage | Existing tests cover timer persistence/dismissal, memory correction/deletion, navigation, context retention and single-use approval. Eight new briefing acceptance tests cover freshness metadata, repeated fresh checks, partial failure, project consistency, sanitized errors, truncation and duplicate prevention during briefing reads. | Tests use temporary data and mocked news. They do not prove general write idempotency or model resolution of ambiguous "save that". Next: mocked model tool sequences for ambiguous references and retried writes; approval required for runtime changes. Review-only test files can be removed without changing the application. |
| Voice | Four scripts pass for stale wake failures, recovery, sustained interruption, silence/noise rejection and diagnostics while capture is stopped. static/app.js records transcription duration and displays microphone-off states. | Synthetic audio is not headset evidence. Next: user-led quiet/noisy activation trials, labelled transcription samples, interruption timing and sleep recovery. Record counts/timing only; no recordings by default. No voice code changed, so no rollback needed. |
| Memory | Tests pass for explicit saves, correction/deletion, persistence, credential rejection and separation of retained tool evidence from memory. | Arbitrary secret detection and semantic deduplication are not proven. Next: ambiguous-reference and paraphrase-duplicate tests before changing behaviour; avoid merging distinct facts. No storage or permissions change; personality rollback below. |
| Performance | Tests have measured suite runtimes; frontend has transcription timing. Candidate adds section-check duration_ms without audio or screenshot logging. | No live API cost, model response latency, headset latency or resource benchmark collected. Mock timing is not production performance. Next: review a bounded metadata-only latency summary; any code needs approval and a reversible diff. |

## Validation performed

- Installed application: 78 Python tests passed in 9.539 seconds.
- Isolated server candidate: 86 Python tests passed in 10.354 seconds, including eight briefing regressions. The candidate was imported only in a test process; no candidate server was started. Its ROOT points to normal resources for tests; test data remains temporary.
- JavaScript runtime scripts passed: test_wake_race.cjs, test_voice_recovery.cjs, test_barge_in.cjs, test_voice_diagnostics.cjs.
- Python candidate parsed successfully before tests. This syntax check is separate from the runtime unit tests above.
- No live news request, AI conversation, GUI check, headset test or Windows sleep/wake test performed in this review.

Commands from the JARVIS directory:

```
.venv\Scripts\python.exe -m unittest discover -p "test_*.py"
.venv\Scripts\python.exe -m review.validate_candidate
```

The standalone review/briefing_regressions.py suite asserts the proposed contract and will fail against the unchanged server until the patch is approved and applied. This is deliberate evidence of unresolved runtime gaps, not a claim the installed version is fixed.

Personality rollback: use Change History with proposal `716fe370fbd54a0d9b82d32770066dc7`; the existing rollback mechanism checks for later edits before restoring its saved previous text. Preserve any later changes. Review artifacts do not modify startup, credentials, the desktop bridge or permission enforcement.
