# Stage 6 TEST health publication and fresh medium acceptance

**HEALTH_PUBLICATION_VALIDATED; MEDIUM_VALIDATED after archive verification. Stage 6 remains INCOMPLETE.**

Fresh run `identity-793e92be19324eb5957d673dc2d2a34d`. One attempt, no retry. Both required per-run UAC approvals succeeded. No change to the 10-second health limit, 13.6-second process deadline, 15-second independent observer or 120-second second-prompt gate. No large campaign, protected hashing, VM operation or production activity.

## Correction

New candidate: `D:\JARVIS-STAGE6-LIVE\e55504d627d24f24a6f56f9e2435230b\code`. Only two existing behavioral TEST files changed: timed_monitor.ps1 and qualified_worker.py. Added health_publication.ps1 and health_reader.py. Three additional files changed only for fresh-run declaration/intent and launcher DLL-path binding. Exact raw before/after hashes are in final-source-changes.json; diffs and original freeze references are preserved.

The monitor opens a unique D: append-only health journal, serializes complete newline-delimited records, preserves durable flushing, and never truncates published records. Ready publication uses a flushed/closed staging file and non-overwriting rename after the first completed journal record. The reader reuses the unchanged bounded journal parser, checks a creation-verified publisher handle, latches failures and enforces age strictly below 10 seconds. Incomplete tails never renew health; final successful closure requires a complete tail after confirmed observer exit. Worker and observer retain their existing external result formats. The frozen v5 checker and shared journal.py are unchanged.

No authentication, authority, Core code, production behavior, kernel/native tracing, queue semantics or acceptance rule changed. Publisher closure validation is separate from live health: it does not pretend an exited publisher is healthy.

## Focused evidence

184 focused tests/checks passed, zero failures/errors/skips: 28 new Python/protocol/real PowerShell writer-reader tests; 19 writer failure/boundary checks; 7 deterministic readiness-publication checks; 69 existing monitor regressions; 21 checker composition and 40 telemetry checks. Separate existing suites passed 222 queue assertions including 10,000-event collision stress and 157 finalization assertions. These assertion counts are not mislabeled as separate live campaign trials.

The old truncate-before-write mechanism was reproduced on sacrificial data. Actual PowerShell publication was held partway through a new record: Python retained only the previous complete record, then consumed the completed record exactly once. A deliberately interrupted writer exited nonzero as expected; this is a passing negative test, not an unexpected failure. Ready publication was held after staging/flush but before rename; no final ready path existed until release. Malformed completed records, wrong identities, exactly-ten-second age, stale/future health, replacement/truncation, unavailable files, capacity overflow, write/flush failure and failed finalization rejected. Test child exits were confirmed; no forced termination occurred.

Python syntax and PowerShell parsing passed. Test commands and captured subprocess outputs are preserved in the review directory. Existing run_focused.py, queue_regression.ps1 and test_finalization_gate.ps1 were executed against this new candidate; no historical result was substituted for current acceptance.

## Actual medium results

| Requirement | Result |
|---|---|
| Workload | 64 probes: 16 idle, 16 churn, 32 overlap; one direct worker |
| Workload elapsed | 6.2397666 seconds |
| Input size | Process events only; no dataset hashing |
| Authoritative instances | 132 |
| START / STOP | 132 / 132 |
| Records / bytes | 264 / 114830 |
| Segments / first–last sequence | 15 / 1–264 |
| Gaps / duplicate authority / missing segments | 0 / 0 / 0 under strict checker |
| Segment bytes min / mean / max | 4834 / 7655.333333333333 / 8176 |
| Segment hashes, manifest, seal | PASS |
| Writer lifetime | 59.6529707 seconds |
| Records/sec, bytes/sec, segments/minute over writer lifetime | 4.42560, 1924.96700, 15.08726 |
| Writer capacity | 65536 items / 67108864 bytes, unchanged |
| Writer high water | 61 items / 25394 bytes |
| Finalizer capacity / high water | 2 / 2 |
| Backpressure started / completed / interrupted | 2 / 2 / 0 |
| Backpressure elapsed | 0.0327884 seconds |
| Rejected admissions | 0 |
| Flush mean / p95 / maximum | 0.05676082 / 0.21659170 / 0.21659170 seconds |
| Readback/hash mean / maximum | 0.000073413 / 0.000092700 seconds |
| Queue snapshots | 843, strict transition/lag accounting PASS |
| Direct creator captures | 65 |
| Qualified post-exit helpers | 64 |
| Tracer helper verifications | 2 |
| Independently verified application observer | 1 |
| Retained handle evidence | 68 |
| Real native entries | 65 including worker |
| False uniqueness / authoritative ambiguity | 0 / 0 |
| CIM supporting evidence | {'AMBIGUOUS': 258, 'UNMATCHED': 2}; preserved, not force-matched |
| Actual PID / parent PID reuse | 0 / 0; not claimed exercised |
| Maximum heartbeat / successful health age | 1.2433837 / 1.1976877 seconds |
| Slow heartbeat warnings | NOT CONFIGURED under approved policy |
| Slow probe warnings / deadline violations | 0 / 0 |
| Longest probe lifetime | 0.4864345 seconds |
| Complete health journal | 20 records / 4502 bytes; complete final newline |
| App / worker / kernel exit | 0 / 0 / 0 |
| Public checker | EVIDENCE_VALIDATED_PENDING_ARCHIVE, stage6-checker-telemetry-v5 |
| Final host census | Zero matching processes / zero trace sessions at 2026-09-22T04:44:29.0919825Z |
| Candidate / previous source hashes | 162 / 160 unchanged after freeze |
| Protected VM/configuration access / production change | NONE / NONE |

Raw metrics include dequeue/completion/finalizer lags and complete timing references. The throughput denominator includes observer startup/closure; this finite run does not establish sustainable throughput. With 15 segments the nearest-rank p95 equals the maximum. Readback/hash time includes read/record validation, not just CPU hashing. Sampler behavior was not exercised because this is the declared process-only medium workflow.

## Preserved failures and limitations

The earlier 221-member medium JSON-read failure archive remains unchanged, as do the prior nested-writer checker rejection and missed second-UAC-gate archive. No historical run was reclassified. The new passing evidence demonstrates the corrected mechanism, not the exact bytes observed during the prior failure. Historical 21 AMBIGUOUS / 1 UNMATCHED remain unchanged; this run's supporting CIM counts are separate. Historical delay causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

## Next genuine integration boundary

Stage 6 is not finished by medium acceptance. The copied large_launch.ps1 still waits for app-health.json (line 24) while this corrected monitor publishes app-health.jsonl. Its large_collect.py imports dry_health.Health, whose check still parses app-health.json. It also selects the older J6BaselineTrace.exe path; this is not proof that it consumes the now-qualified authority stream/checker. Running that copied launcher as-is would not be a valid next acceptance step.

The next review must identify the authoritative current large-collector integration candidate and minimally connect the validated health journal and qualified durable kernel/checker paths. Preserve both observer handle checks, collector/sample ownership, startup tracing, existing output contracts, bounded capacity and cleanup. Likely affected interfaces include large launch readiness, dry_health.Health or a dedicated large adapter, source manifest and versioned large checker binding; exact scope must be reviewed before edits. Validate that integration on small sacrificial data first, then qualify the 59.7 GB synthetic workload. Do not substitute this 64-probe run for large-data calibration, large acceptance, protected-source preservation, clean-Windows recovery or deployment/cutover requirements.

Protected VM access and real protected baseline hashing remain outside this pass. No owner approval for broad new authority or production activity is inferred from “finish Stage 6.” No acceptance commit or Stage 7 work.

## Rollback and archive

Rollback is to stop selecting this TEST candidate; preserve all artifacts. No production restore, protected VM change or evidence deletion is needed. Canonical nonsecret archive: `C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 HEALTH JOURNAL MEDIUM PASS 20260922\evidence.zip`. MEDIUM_VALIDATED is contingent on the accompanying completed archive-verification receipt; the receipt and final disposition are mirrored separately after verification.
