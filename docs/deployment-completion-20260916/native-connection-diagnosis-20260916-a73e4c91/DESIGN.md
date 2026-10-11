# Native probe correction decision

Classification: B. Test harness defect, experimentally established for slow client startup/admission.

`peer_identity.cc:142-143` calls CreateFileW and uses GetLastError in win(); PIPE_CONNECT:2 is Windows error 2 (file not found), before GetNamedPipeServerProcessId and PEER_IDENTITY_MISMATCH. The original reported failure did not record the server reason. The new controlled trace records pipe_transport.py:99 Rejected(IO_TIMEOUT) on connect, then close, then input release and PIPE_CONNECT:2 with zero frames. The ordinary observed run passed in about 264ms from connect wait to connection. Do not claim that controlled ordering independently proves the old run's exact timing.

Expected: pending connection signals its OVERLAPPED event within the 1200ms connect operation budget. Actual controlled case: no client connect before the wait expired; timeout cancellation completed and the pipe was closed. This is not a PID/SID/hash mismatch. Pins match the server identity; peer validation is unreachable after CreateFileW fails.

Minimum correction: only TEST fixture and TEST Electron native-case driver. Native-case driver emits an explicit readiness line only under a dedicated TEST flag, after loading its existing JS modules and installing stdin handlers. The fixture waits for that line within the existing 12-second child budget, then starts the original connection window and sends the same configuration. Reset this TEST pipe's five-second operation lifetime at that handoff, not at pre-launch creation. No sleeps, retries, larger child deadline, native bridge change, Core change or auth bypass. Readiness grants no authority. All original endpoint/pin validation still occurs.

Record actual child identity, readiness timing, stdout/stderr and full server reason. Print PASS only after evaluating all native case results. Preserve failures and perform identity-checked TEST child cleanup on helper errors.

Validation: a single corrected positive; all 15 native cases; focused readiness helper tests (valid/malformed readiness, deadline, cleanup identity, startup-before-accept ordering), existing coordinator readiness and native/client regressions; then restart gate and complete 33-group inventory only when green. Stop on any new validation failure. Rollback only the exact two-file diff using pre-change snapshots; do not restore unrelated dirty files.
