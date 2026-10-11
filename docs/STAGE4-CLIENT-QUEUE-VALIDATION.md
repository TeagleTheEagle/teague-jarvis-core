# Stage 4 TEST client queue continuation — 2026-09-12

Stage 4 remains INCOMPLETE. Production activation blocked. No acceptance commit.

## Change

The previous client transport queue started each 6.5-second timeout only after
earlier calls finished. Queued requests could survive a timeout and dispatch
later; close could wait behind those requests. Within the approved shared TEST
client file scope, TransportQueue now starts the deadline at admission, includes
queue waiting, rejects all outstanding work on transport timeout/failure/exit,
and ignores late replies. It never replays requests. Close rejects undispatched
work and allows a cooperative detach behind the current request if transport
remains healthy. No timeout establishes zero resource consumption. Main-thread
event-loop or native worker termination hangs are not claimed to have a hard
wall-clock bound. No physical media functionality is added or certified.

Changed source: stage4_client.cjs and desktop/test/stage4-client.test.cjs.
Before bytes and hashes: lifecycle-stage4-evidence/client-queue-20260912/before/.
Legacy launchers, production authentication, Stage 1–3 source, VoiceEngine,
WakeDetector, Store and provider routing were not edited.

## Checks actually performed

- Focused Node tests: 13 passed, including 7 new queue cases.
- Combined desktop/Intelligence Node tests: 29 passed.
- Existing Python regression: 212 passed.
- Stage 1: 23 passed, 1 existing skip.
- Stage 2: 35 passed, 1 existing skip.
- Stage 3: 43 passed.
- Stage 4 ownership/drain model: 27 passed.
- stage4_client.cjs JavaScript syntax: passed.
- An initial Electron-as-Node invocation produced no test output; not counted.

## New failed actual Electron probe — retained

electron-app-probe-54da8dc9921c4760aa72c77327a1e27f.json records successful Stage 1
reconciliation, then Electron startup exit 2147483651. No completed client
attachment or screenshot was obtained. The client stderr records an encryption
error (0x2), repeated GPU-process exits (-1073741515), then the fatal message
"GPU process isn't usable. Goodbye." These are observations, not a diagnosed
DLL, graphics-driver, sandbox or queue defect. No security flags or dependencies
were changed to bypass this failure, and no automatic rerun erased it.

Namespace: TEST-STAGE4-91058ac0aa2e47b3b8c87016e4da1968.
The probe recorded TEST Core launcher PID 7308 exiting normally with code 0 via
the existing authenticated cleanup. No forced termination or production restart.
Do not use that historical PID for later cleanup without re-verification.

This new failure is separate from the historical Stage 1 PermissionError, the
corrected repeated-response mechanism, the guarded IPC contention, and the old
Windows memory-access crash. No common cause is established.

## Remaining gates and rollback

Actual Electron validation of this delta remains failed/unverified pending startup
diagnosis. Native/bootstrap checks were not newly certified. Broader worker,
inspection/repair cleanup, approval/stream/upload coverage, media watchdog wiring,
human lifecycle controls and separately authorized physical voice/media validation
remain open as recorded in the master Stage 4 report. Existing skips remain skips.

Rollback only the two source files from the byte-preserved before copies if no
later edits exist, or reverse this delta alone. Retain all new evidence. Do not
reset unrelated working-tree changes or roll back any database. No rollback was
performed. No acceptance commit, Stage 5, installer, autonomy or production change.
