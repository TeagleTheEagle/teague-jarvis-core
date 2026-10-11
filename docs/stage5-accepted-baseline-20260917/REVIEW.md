# Stage 5 accepted-baseline campaign — STOP FOR REVIEW

Baseline: d6199756f1e1f4495ad6c3de457660cbf1f03e84. Stage 5 INCOMPLETE.

5A PASS: copied and verified all 61 accepted application files into TEST-STAGE5-APP-9b0e19778db44f1287851eec9f860311. Added only accepted Stage 4 fixture and historical Stage 5 test driver, with hashes recorded. The new ordered harness separates ownership/recovery (5B) from request combinations (5C). No historical results counted as current evidence. No production .env, database, personality or credentials copied. Application code remained byte-identical.

5B PASS: 604 records, 604 passing. Four eight-contender rounds, interrupted start boundaries, three coordinator post-spawn losses, three Core crashes, smoke lifecycle and UNKNOWN recovery behavior, using the existing fixtures. See 5B-b66773f9a0064c67a98174897db4cb64.json.

5C FAILED/STOPPED: 228 records: 224 passing and four failure records (one primary exception and three related cleanup/assertion records, not four independent runtime defects). The security/capacity cases passed. Failure occurred during restart in the first `openai` simulated provider scenario. No later provider scenario or reconnect race was run. 5D and 5E NOT RUN.

## Exact failure and evidence

The existing provider_recovery test stopped the first Core, inspected persisted response/provenance successfully, then requested authorized restart. The coordinator issued a start grant. The client timed out while waiting for the execute reply at pipe_transport.py:99 (`Rejected: IO_TIMEOUT`), propagated through bootstrap.py:146, fixtures.py:1175/1181/1191, campaign.py:93. Full traceback is preserved in 5C.log and 5C-7bf1bb52eb4f4901b6cdc52caf8e50da.json.

Namespace: TEST-STAGE4-dfb34319af424ed5a389672b6506a970. A subsequent preserved start_verified event identifies new Core PID 444, creation 134340836474666300, epoch ac2c7985f8074ea9a6c192d5dda16c6b. Coordinator PID 18840, creation 134340836456181519. Both executable hashes are 372c2eae555b344520bf147be0096e009069aeca4e7f78d6aecea6d53158056a. Read-only native identity checks confirmed both remain live. The operation had an effect despite its missing client acknowledgement; do not replay it.

Authenticated cleanup attempted by the existing fixture failed its `explicit coordinator close` assertion. The returned close payload was not captured, so its exact denial reason is not established. Source permits a START_ACTIVE denial while the launch worker is alive; that is a hypothesis, not a proven cause. The failed start call did not return the new identity into the fixture's normal tracked-Core list, explaining why normal tracked-Core cleanup did not cover the subsequently verified Core. One readiness JSON remains. No forced cleanup or further attachment was attempted.

## Root cause and proposed next review

Confirmed symptom: bounded pipe receive timeout on the restart execute acknowledgement, followed by recorded successful Core startup and incomplete cleanup. Underlying cause is UNCONFIRMED. The transport has a 1,200 ms per-I/O bound within a 5-second connection deadline. This alone does not prove timeout values are wrong or that a runtime defect exists. Do not increase timeouts speculatively.

Affected components: tests/lifecycle_stage5/campaign.py provider_recovery; tests/lifecycle_stage4/fixtures.py start/execute/close and failed-start tracking; accepted stage4_runtime.py coordinator execute/_launch; accepted tests/lifecycle_stage2/bootstrap.py and pipe_transport.py. No components were corrected.

Minimum proposed next action: authorize identity-reverified cleanup of only these retained TEST processes, using a supported authenticated route if available; if forced cleanup is needed, explicitly approve those exact identities. Then a bounded diagnostic harness should record execute request/reply timing, the actual close response, coordinator launch outcome, and identity-bound post-timeout reconciliation without retrying execute or changing runtime deadlines. Preserve credentials outside evidence. A specific runtime correction cannot yet be justified.

Regression risk: treating a timeout as non-execution can duplicate startup or leave untracked ownership; indiscriminate cleanup can terminate a valid Core; extending timeouts may mask rather than explain the defect. Any correction must preserve one-use authorization, lifetime ownership, new epochs, stale-authority rejection and UNKNOWN handling.

Required validation after an approved correction: exact failed first-provider restart case; delayed/lost execute reply; successful and unsuccessful start outcomes; no grant replay or second owner; cleanup during and after launch; actual persisted state/epoch; unchanged readiness and Stage 1–4 regression contracts. Do not run these until the stop boundary is reviewed.

## Cleanup and source verification

failure-census.json preserves native identity checks, metadata and source hashes. Two matching TEST identities are LIVE. A third lookup was access denied; pid-reuse-supplement.json establishes PID 12400 is now svchost.exe with a later creation time, while the prior TEST coordinator had an authenticated exit-0 record. It is unrelated and must not be touched. One retained coordinator readiness file belongs to the still-live run, not an orphan eligible for deletion.

All 61 accepted application hashes remain unchanged after failure. Read-only census did not terminate, attach, rerun or alter runtime state. Synthetic databases, logs and metadata remain in their isolated namespaces. Historical evidence is unchanged. Current aggregate: 832 recorded checks/events, 828 passing, four failure records, zero skipped in executed 5B/5C; unexecuted gates are NOT RUN, not skipped or passed.

No acceptance commit. No production modification, activation, provider network call, schema/authority change, physical media, approvals, uploads, deployment or next-stage work. Stage 4 regressions were not rerun after the stop; no Stage 4 regression has been conclusively diagnosed.

Cross-user/cross-session/remote-host coverage remains a LIMITATION. Approvals, uploads and physical media remain DEFERRED.

HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
