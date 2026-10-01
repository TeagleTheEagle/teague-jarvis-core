# Reviewed validation-only durability separation

Previous behavior: every heartbeat called FileStream.Flush(true) in the serial event/heartbeat loop. Two synthetic failures measured 11.001 and 12.254 seconds inside that call.

Candidate behavior: the live loop uses Flush(false), which transfers managed buffered bytes for the reader without forcing physical durability on every heartbeat. It remains synchronous I/O, not a hard-real-time/nonblocking OS guarantee. Open/write/ordinary flush errors still escape to the monitor failure path. Event draining remains coupled to publication. The reader is byte-identical to the previous version: pinned process creation identity/handle, nonce, sequence, monotonic ticks, event-pump state, 10-second stale limit and fail-closed latch are retained.

Journal bounds remain 4 KiB/record and 1 MiB/journal; event evidence is bounded to approximately 1 MiB, trace to 50,000 entries, monitor lifetime to 600 seconds. No rotation is performed. Replacement/truncation is rejected, rather than breaking readers or deleting evidence.

## State machine

COLLECTING -> LIVE_MONITOR_HEALTHY -> LIVE_COLLECTION_CLOSED -> EVIDENCE_DURABLY_FINALIZED -> SACRIFICIAL_RUN_ACCEPTED.

Each transition is mandatory. Any failure leaves the run unaccepted.

- The consumer keeps checking liveness during all synthetic read/hash jobs, including source hash and rehash.
- After the final health check it records the live result and requests collection closure.
- The monitor performs its final event grace/drain and zero-VirtualBox check, freezes collection, performs Flush(true), closes the journal and exits. Exceptions prevent a successful exit.
- The consumer waits using the already pinned process handle and requires exit code zero, preserving creation identity. The separate closure/durability wait is bounded to 60 seconds; this does not extend the live 10-second threshold.
- An independent finalizer validates the complete closed journal, exact sequence/identity/event counts, probe correspondence, recorded healthy samples and (for dry runs) all 12 source hashes/sizes/mtime values before/after.
- Every frozen evidence file is fsynced using Windows-backed os.fsync, hashed, copied into a run-local archive, fsynced there and hash-compared. The manifest and finalization receipt are likewise flushed and verified.
- The consumer requires the finalizer's actual successful process exit and revalidates source/archive hashes. A receipt file alone is insufficient. It writes and durably archives acceptance only after that succeeds.
- Finalizer execution has its own 60-second bound. A timeout terminates only that directly launched synthetic worker using its retained process handle, records failure and prevents acceptance. No arbitrary retries occur.

## Crash and failure semantics

Monitor/writer death invalidates the pinned live handle. Reader/controller death cannot produce the successful live result or final acceptance; the monitor's 600-second lifetime limit eventually closes the abandoned run as failure. A reader may restart only by revalidating the same live publisher identity and complete journal; an old process identity cannot authenticate a replacement publisher.

Truncation, malformed sequences, stale/incomplete data and inaccessible journal access fail closed. A partial trailing line may be tolerated during append but must not renew freshness. Finalization requires a complete final line and correct terminal sequence; partial final records are rejected.

A host/process interruption before the complete finalization and acceptance protocol leaves the run unaccepted. Buffered data may have been lost and must not be described as complete. No real host power-cut test is performed; durability relies on Windows/storage honoring successful flushes. No filesystem crash-recovery guarantee beyond that is claimed.

Durable flush failure, hash mismatch, corrupted archive, missing event, nonzero process exit or failed live collection prevents acceptance. The external Stage 6 decision must inspect the combined acceptance and evidence, not a live-health or monitor-close field alone.

## Scope and rollback

All changes are new files in this candidate directory. Previous diagnostic scripts/evidence, protected VM/configuration, production JARVIS and security settings are unchanged. Synthetic C:/D: inputs from the prior diagnostic are read only. Rollback is to stop using this candidate and retain its evidence; no production configuration or runtime needs reverting.

This validation does not authorize protected hashing. Historical 13.7-second and 14.084-second causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
