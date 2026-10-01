# Stage 6 heartbeat journal — sacrificial validation

**Disposition: MONITOR_STILL_DEFECTIVE. Protected baseline retry is NOT justified.**

The append-only correction passed focused testing, but dry run 1 failed closed after 117.031 seconds. The recorded publisher interval reached 14.0840902 seconds. The stale threshold remains 10 seconds. Dry run 2 was NOT RUN, following the explicit stop rule. No protected VM files, normal VirtualBox configuration, production JARVIS, or security settings were accessed/changed by this implementation. No VM or JARVIS Core was launched. No protected baseline manifest was created.

## Files and mechanism

All new work is confined to `docs/stage6-heartbeat-journal-20260918`:

- `journal.py`: bounded journal encoder/reader and Windows process-handle liveness/creation-time verification.
- `monitor.ps1`: elevated read-only WMI process-start/stop subscriptions and append-only heartbeat publisher.
- `test_journal.py`, `test_processes.py`, `process_fixture.py`: synthetic unit and child-process tests.
- `diagnose_launcher.py`: preserved investigation of the failed termination test.
- `dryrun.py`: synthetic-only hashing, event probes, manifest and preservation rehearsal.
- `resources.ps1`: read-only Windows performance counter sampling.
- `reconcile.py`: prepared two-success-run reconciler; NOT executed because dry run 1 failed.
- `analyze_failed_dryrun.py`: read-only failed-run analysis.

The writer holds a single CreateNew FileStream, appends UTF-8 newline-delimited JSON, and calls Flush(true). It never replaces the reader-held journal. Each record includes nonce, PID, exact process creation FILETIME, sequence, UTC, QPC ticks/frequency, event-pump generation and violations. The reader pins the process handle/creation time and journal file identity. Complete records must have consecutive sequences and consistent identity. Partial trailing lines do not renew health. Invalid data, failed liveness, inaccessible files, stale/future timestamps and sequence/identity violations invalidate the run.

Bounds: 4 KiB record, 1 MiB heartbeat journal, approximately 1 MiB event log, 600-second monitor lifetime. Rotation is deliberately unsupported: truncation/replacement is rejected; reaching a bound stops rather than wrapping or deleting evidence. These are sacrificial implementation limits, not permission to extend protected baseline timeouts.

## Focused testing and preserved failures

Commands, run from this directory using the repository `.venv\Scripts\python.exe`:

`python -B -m unittest test_journal test_processes -v`

- Initial 22 unit checks passed, with two test resource warnings; the test file handles were closed explicitly. Original output: `focused.txt`.
- First combined run: 31 tests, 30 PASS, 1 FAIL. Original output: `focused-final.txt`.
- Corrected combined run: **31/31 PASS**, 12.249 seconds. Evidence: `focused-corrected.txt`.

The failed termination injection killed venv launcher PID 12112 in an independent reproduction while publisher PID 18368 remained alive. `launcher-diagnosis.json` establishes the distinction. The test driver now launches `sys._base_executable` directly and asserts that its process PID equals the publisher identity before injecting termination. This is a fixture correction; journal semantics were not relaxed.

Coverage includes continuous held-reader/concurrent publication, complete and partial writes, malformed data, duplicate/skipped sequences, stale data and the exact 10-second boundary, publisher death, publisher restart, reader death/restart, rotation/truncation, delayed publication, hash-worker crash, capacity/short-write faults, and simulated access-denied/disk-full faults. Permission/disk-full tests use injected exceptions; no ACL change or actual disk filling occurred. Rotation is rejected or prevented by Windows sharing semantics. The actual WMI monitor was started once; a second complete fresh WMI-monitor run remains unvalidated.

## Sacrificial stress result

`python -B dryrun.py prepare` generated one random 1 GiB file plus eleven 4 KiB files. `python -B dryrun.py dry1` performed repeated SHA-256 hashing using aligned unbuffered Windows reads, with the journal reader continuously open. The target was at least 120 seconds followed by source re-verification. It stopped at 117.031 seconds before completion. The second full hash/preservation pass and sacrificial manifest were NOT completed. Synthetic binaries remain local and are excluded from the archive.

Recorded heartbeat distribution across 104 published records:

| Measurement | Seconds |
|---|---:|
| Minimum interval | 0.0925743 |
| Median interval | 1.0388169 |
| P95 interval (reported order statistic) | 1.1408071 |
| Maximum interval | **14.0840902** |
| Maximum successfully observed age | 9.733781 |

The exact age at the rejected poll was not captured by the exception. The collector stopped on `stale/future heartbeat`; the subsequent journal interval independently establishes a greater-than-10-second publication gap. Sequence 103 was stamped 04:15:28.3967161Z; sequence 104 was stamped 04:15:42.4808051Z. Earlier gaps were 9.914, 5.146 and 5.799 seconds. No journal read/write exception was recorded; one freshness failure was recorded. The monitor's later `PASS` describes its own clean exit/event checks only and **does not constitute capture acceptance**.

45 resource samples: peak total CPU 33.65%; peak C: disk active percentage derived from idle counter 100%; peak instantaneous C: queue 34; minimum available memory 20,315 MiB. Maximum completed unbuffered read duration was 4.0 seconds. Disk contention is a plausible lead, not an established cause. Phase timings inside Drain, Write, Flush(true), scheduling and WMI delivery were not captured sufficiently to locate the stall. Hashing and monitoring remained separate processes.

## Event coverage and cleanup

Harmless copied Windows `whoami.exe`, named `J6Probe.exe`, produced **12 expected/12 captured starts and 12 expected/12 captured stops**, matched by unique PID. No real VirtualBox executable was launched. The unchanged VBox/VirtualBox prefix filters cover the six requested names and truncated stop-event names by static inspection. Live coverage used the harmless probe branch; there is no claim of universal event reliability or a guaranteed minimum detectable process lifetime.

The collector failure signalled completion to the monitor; the monitor unsubscribed and exited. The sampler also exited. `final-cleanup-verified.json` records a successful process query with **0 relevant helpers and 0 VirtualBox processes**. An earlier sandboxed CIM query returned Access denied; its misleading zero-count artifact `final-cleanup.json` is preserved but explicitly INVALID for process counts and superseded. Its two original validation-script hashes are valid and remain unchanged.

## Uncertainty, rollback and next decision

The new delay's root cause is **UNCONFIRMED**. The original 13.7-second delay remains **UNCONFIRMED**; this new symptom does not establish historical causation. **HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.**

Rollback is to leave this candidate unused; no production or prior baseline collector was replaced. Retain all failed evidence. Do not run `dry2` or protected capture from this candidate. The next review should authorize bounded phase timing of event draining, append/Flush(true), scheduler delays and disk contention if further diagnosis is desired. Do not increase the freshness threshold to obtain a pass.

Protected retry procedure is withheld as not yet justified. Prerequisites remain two complete successful sacrificial rehearsals, acceptable monitoring/event/cleanup evidence and owner review. Future baseline work must preserve the distinct networking facts: protected post-incident 1; historical 0; required future validation-copy 0. None was inspected or changed during this pass.

Archive verification is recorded separately in `archive-verification.json`. Source/evidence SHA-256 values are in the archive manifest. Archive excludes executable copies, synthetic binary payloads and cache files; no credentials are included.
