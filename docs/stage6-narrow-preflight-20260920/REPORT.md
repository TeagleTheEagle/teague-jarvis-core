# Narrow preflight correction and monitored synthetic failure — 2026-09-20

Status: **PROTECTED_COLLECTOR_STILL_DEFECTIVE**. This is the acceptance disposition, not a finding that a particular source, Windows, storage or driver defect has been established. No retry occurred.

## Scope and correction

Only new report/preflight files were added in this report directory. The frozen collector, monitor, queue, deadlines, ACLs and production source were not changed. Protected VM/configuration was not accessed; no VirtualBox command or protected hashing was performed.

The old `../stage6-protected-resume-20260920/preflight.py` module-level manifest loop (lines 9–14) verified ZIP members and then reopened every manifest `source` path. The archive's recursively collected historical fixtures therefore caused `final-test-1kkhohf2/collector-finished.json` to be reopened. Any other inaccessible generated source could cause the same failure. The reason that Windows denied that file is not established by this correction. The old helper and evidence remain unchanged.

The replacement `verification.py` verifies the archive ZIP and manifest hashes, exact member set, each member hash and embedded manifest. Historical `source` fields are provenance only and are never reopened. `preflight.py` directly verifies only the 84 frozen candidate files, candidate manifest, required current calibration records and 12 synthetic source metadata records. `pre_live.ps1` provides host process/trace checks. `close_failure.py` is report-only post-run reconciliation, not an acceptance override.

Added files: verification.py, test_verification.py, preflight.py, candidate.json, pre_live.ps1, close_failure.py, archive_failure.py, this report, and their evidence receipts. No existing collector/runtime source changed. Rollback is to stop using these new report helpers; it does not require modifying the candidate or deleting evidence.

## Focused validation

From this report directory:

```powershell
& 'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B -m unittest -v test_verification
```

14 tests passed in 18.822 seconds, exit 0. This result was observed in the command output; it was not rerun to generate a different result. Tests cover candidate/calibration/ZIP/manifest/member success; inaccessible historical extracted fixtures; missing archive; ZIP/manifest/candidate/calibration mismatch; live process/trace rejection and empty safety-state success.

Corrected preflight passed: 84 candidate hashes; unchanged calibration; all 1,333 prior archive members; 12 synthetic files totaling 59,665,402,098 bytes; unchanged sizes/mtime; no generated historical paths opened. Host preflight separately confirmed zero relevant processes and trace sessions before launch. The prior calibration was not repeated.

## Actual resumed run

Fresh run: `D:\JARVIS-STAGE6-LIVE\1c1f5d0c390b42cc9ba9f4f6221dabc6\code\protected-3aec3ce0062c42a19077a2bad0571bd7`.

Command:

```powershell
& 'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe' -NoProfile -File 'D:\JARVIS-STAGE6-LIVE\1c1f5d0c390b42cc9ba9f4f6221dabc6\code\baseline_launch.ps1' -Source 'D:\JARVIS-STAGE6-LIVE\1c1f5d0c390b42cc9ba9f4f6221dabc6\code\large-synthetic'
```

Both per-run UAC observers started. Launcher exited 1 with `Primary/observer failure preserved; no acceptance finalization`. No monitored hash pass completed. No acceptance manifest or successful durable finalization was produced.

Primary failure: probe PID 24516, parent 3552, `J6Probe.exe` from the frozen D: candidate. Creation FILETIME 134343658823845218; exit FILETIME 134343659021165297. Of 35 probes, one exceeded the hard deadline. CreateProcess took 0.0022782 s. Deadline observed at 13.6132482 s after launch request; retained handle remained unsignaled. Independent 15-second wait returned unsignaled after 15.0091488 s. Kernel lifetime was 19.7320079 s; eventual exit code was 0. Eventual exit does not repair this failed acceptance condition. These measurements do not locate the internal delay.

The hash worker PID 17376 was then canceled through `workload-stop`; its retained handle signaled, exit code 1, and stdout/stderr drains reached EOF. Its nonzero canceled exit and the independent probe observer failure remain secondary failures.

Later the application-event observer failed its unchanged 10-second heartbeat limit. Last recorded heartbeat QPC 1986318515785; error receipt QPC 1986474175566; frequency 10,000,000. Their separation is **15.5659781 s**. This is not a measured duration of an identified blocking call. Maximum interval among the earlier successfully recorded heartbeat entries was 4.0601669 s; that smaller value must not be represented as the full-run maximum.

Underlying causes of the probe lifetime and later heartbeat delay remain **UNCONFIRMED**. No timeout, observer threshold, source or security adjustment was made.

## Lifecycle and cleanup evidence

- 73 tracked application STARTs and 73 STOPs; 73 kernel creates and 73 exits.
- Application queue: 176 enqueued/persisted/removed, zero remaining; maximum depth 34.
- One external EventIdentifier collision; zero internal queue-ID collisions.
- Kernel tracer reports zero lost events/buffers/faults, successful flush and stop.
- 65 local tree handles have signal evidence and are closed.
- Application observer exited 1; tracer exited 0.
- Strict unchanged cleanup checker: **FAIL**, 73 identities insufficient for accepted proof because `APPLICATION_COLLECTOR_FAILED` and `OBSERVER_NOT_CLOSED` (normal unsubscribe/finalization flags false). No checker condition was waived.
- Fresh host check: zero scoped live diagnostic processes and zero trace sessions.
- Independent PID + creation-time recheck: 79 recorded entries checked; zero matching live identities. No process termination was needed.

Current absence and retained-handle exits are cleanup observations, not a successful lifecycle acceptance seal. All raw failures are retained.

## Integrity and archive

Post-run verification: 84 candidate hashes unchanged; required calibration hashes unchanged; all 12 synthetic files retain size/mtime; prior 1,333-member archive verified again. No repeat 59.7 GB hashing was performed. No claim is made that source metadata alone proves the interrupted second monitored hashing requirement.

The new archive is a **failed-run evidence archive**, not the missing protected-baseline acceptance manifest. It contains this report, report helpers/receipts, frozen candidate files and the fresh failed run's raw evidence. It excludes the large synthetic dataset, secrets, .env, production data and protected VM/configuration. `archive-verification.json` records its exact path, count and hashes. Originals are rehashed after archive creation; prior evidence is not overwritten.

## Next action

Stop for review. Diagnose the preserved probe deadline and later observer heartbeat/finalization failure before any further acceptance attempt. Do not rerun synthetic acceptance or protected baseline capture automatically. The collector remains ineligible for real protected baseline capture.

Production JARVIS unchanged. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED. This run does not establish causation for earlier Stage 6 failures.
