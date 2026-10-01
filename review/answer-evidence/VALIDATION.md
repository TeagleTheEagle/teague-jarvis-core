# Step 2: answer evidence

Changed: answer_evidence.py (snapshot formatter and bounded receipt guard), server.py (routing, actual registry, timestamped success/failure events), actions.py (RSS response validation), static/app.js (visible evidence), test_answer_evidence.py, release-notes.json, and the isolated browser test in this folder.

Validation: 42 offline Python tests passed (test_answer_evidence, test_update_evidence, test_jarvis). One isolated Chrome test passed using actual backend-generated events, temporary saved data and a simulated unavailable news provider. Python compilation and app.js syntax passed. preview.png was visually inspected: partial results, unavailable news and per-request timestamps are readable; script-like saved text is literal text.

Limits: no live provider/network or native audio test; no confirmation that the running Electron backend loaded these edits. Source timestamps establish retrieval time, not the truth of source claims. News publication dates are feed metadata. Calendar is unavailable. Completion detection uses bounded wording patterns and does not verify arbitrary factual prose. Model-routed briefings use deterministic summaries; additional action receipts are listed, but unrelated prose may be omitted. No approval settings were changed.

Update: load the source update through the existing desktop updater when idle. Backend edits require its restart path. Verify the loaded source fingerprint in Change History before calling it loaded.

Rollback: retain existing verified backups. Recovery extracts a separate folder; do not overwrite the live app blindly. Fresh backup and rehearsal receipt are stored in the sibling jarvis-backups folder.
