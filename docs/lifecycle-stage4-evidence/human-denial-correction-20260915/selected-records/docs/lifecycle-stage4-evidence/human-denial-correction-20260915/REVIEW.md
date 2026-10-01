# Stage 4 — narrow human lifecycle denial-driver correction

2026-09-15. **Correction validation: PASS. Human lifecycle acceptance: OPEN. Stage 5: NOT STARTED.** The entire SELECT → DENIAL → CRASH → EMERGENCY → SHUTDOWN sequence must be performed by the owner in a fresh TEST run.

## Preserved failure and cause

The original [human run](../human-lifecycle-7cc0db70a76149c9954eb82fc4c0c5b5.json) remains byte-for-byte unchanged, SHA-256 `828772b7b257fd60fc1fd494ba20f05c54477e50a8e067edf4d300d720816a2c`. Correct identity selection and correct DENIAL input both passed. The script then attempted `campaign.attach(..., 'teague')` from Python. The Teague enrollment requires Electron's executable identity. Authentication correctly rejected the wrong executable before the shutdown request; `UNKNOWN_FIELDS` surfaced while the bootstrap client expected an authenticated transcript. This was a TEST-driver defect, not the required shutdown-policy denial or an operator error.

That record retains its failure. Later automated success does not convert it to human acceptance. Its authenticated cleanup recorded Core exit and lifetime-lock release; the four recorded identities were rechecked as part of the nine-identity read-only cleanup verification below.

## Minimum correction

Only two TEST source/fixture files changed:

- `stage4_client.cjs`: add a single fixed `shutdown-denial` action to the already-gated trusted TEST-parent driver. It accepts only a 32-character operation identifier and uses the ordinary client's existing worker, session, enrollment and native verified pipe. It cannot select another client, executable, endpoint, PID, credential or arbitrary operation. It adds no renderer method. Transport errors remain errors; a rejected transport alone is explicitly insufficient evidence.
- `tests/lifecycle_stage4/fixtures.py`: replace the Python-as-Teague call with that real Electron action. Require one matching Core-side receipt showing the actual authenticated Electron PID/creation/executable, owner/session, ordinary scopes, intended Core epoch, and `SCOPE` rejection at `Ownership.management_capability`. Verify the same Core and client are still operational and no stop latch was created. Add a focused automated probe and a fixture-only observer enabled by the trusted `TEST_observe_shutdown_denial` configuration flag.

The observer wraps the existing Stage 2 `serve_one` and Core `Authority.operation` in the disposable fixture process only. It delegates the original arguments unchanged, calls the original implementation exactly once, and preserves its return value or exception. It restores the operation method after each connection. It does not issue credentials, change enrollment/scopes, suppress a failure, authorize a request, change the Store or add a runtime route. The recorded peer comes from the actual Windows pipe; policy observations occur only after original bootstrap authentication invokes the Core dispatcher. A handshake failure cannot produce this receipt. No token, proof, private key or management credential is recorded.

The human sequence and targets remain unchanged. DENIAL now prints `Ordinary shutdown: DENIED (authenticated Electron; Core policy SCOPE)` only after both the real client result and matching Core policy receipt pass. CRASH still affects only the disposable Intelligence renderer. EMERGENCY and SHUTDOWN still use the separately authenticated Python owner controller. All executable verification, management scope checks, Core locking, response-commit transactions, session expiry and production paths remain unchanged.

## Actual validation

Working directory for every command: `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis`.

| Check | Exact invocation / record | Result |
|---|---|---|
| Focused actual Electron denial | `.\.venv\Scripts\python.exe -B tests\lifecycle_stage4\fixtures.py --human-denial-probe`; [log](actual-denial-01.log), [records](../human-denial-probe-975dc5ebc14240ba9a3ff8839f604b92.json) | **38 checks PASS** |
| Existing actual Electron lifecycle | `.\.venv\Scripts\python.exe -B tests\lifecycle_stage4\fixtures.py --electron-app-probe`; [log](electron-lifecycle.log), [records](../electron-app-probe-993086388f7546c2b0865e27c9eb2863.json) | **29 checks PASS** |
| Desktop and Intelligence | Installed Node `--test` with every existing `*.test.cjs` in `desktop/test` and `intelligence/test`; [log](desktop.log), exact expanded invocation in `commands.json` | **35 tests PASS** |
| Stage 2 authentication regression | `.\.venv\Scripts\python.exe -B tests\lifecycle_stage2\test_stage2.py`; [log](stage2.log) | **35 PASS + 1 existing skip** |
| Stage 4 ownership regression | `.\.venv\Scripts\python.exe -B tests\lifecycle_stage4\test_stage4.py --ownership-tests`; [log](ownership.log) | **27 PASS** |
| Controller recovery regression | `.\.venv\Scripts\python.exe -B tests\lifecycle_stage4\test_stage4.py --controller-recovery-tests`; [log](controller-recovery.log) | **52 checks PASS** |
| Syntax | Python `compile(source_bytes, filename, 'exec')` without execution; installed Node `--check stage4_client.cjs`; [exact file hashes/commands](syntax.json) | **2 files PASS**, syntax only |

Actual Electron executions used the previously approved host context, Electron 44.2.0. No speculative GPU flags or runtime changes were added. No automated human confirmations or input piping were used. The focused probe is separately named and explicitly records `human_actions_supplied: false`.

Focused Core namespace: `TEST-STAGE4-b310564de96f4625a256345f28b88cb9`; data identity: `TEST-b4478e2718c54ef68e0ce1af92239d9c`; epoch: `c3223b5797aa449187fdc2308a7601cf`. These are closed automated fixtures, **not identities to reuse for the next human run**.

Teague operation `f7b400c570804408bfd890f9b5e44288` and Intelligence operation `352a3ade783544908a520a6b25b6d363` each produced exactly one Core receipt. Both reached management-capability policy using their actual Electron peer and ordinary scopes (`attach`, `media`, `read`, `request`), were rejected for `SCOPE`, and left the Core RUNNING. The negative Python-as-Electron control remained rejected and generated no authenticated policy receipt. Renderer inspection confirmed no shutdown method or production bridge was exposed.

The separate owner controller remained authorized, survived the TEST renderer crash, suspended the same Core through emergency stop, then shut it down through the existing authorized path. The lifetime lock released; both Electron launchers exited with status 0. The existing 29-check Electron regression also exited cleanly. No forced process termination occurred.

No correction-development or regression failures occurred in this change. The earlier failed human run and all historical failures remain preserved. No unrelated suites were rerun, and existing closed Core gates were not reopened.

## Baseline, cleanup and limitations

[Source verification](source-after.json) covers the same 27 paths as the prior validated baseline: exactly the two reviewed TEST files changed; **25 paths remain unchanged**. [Scope verification](scope-verification.json) lists the changed fixture symbols. Before snapshots, exact diffs and after hashes are included. Git HEAD alone is not this working-source baseline; no acceptance commit was created.

[Read-only cleanup](cleanup.json) checked **nine recorded complete process identities** across the failed human run, focused automated run and existing Electron regression. All had exited. Additional client/launcher exits are recorded by the respective probes. This is finite recorded-process coverage, not a claim that every unrelated Windows process was inspected.

- Human acceptance is still OPEN; the original human selection and observations do not satisfy the unperformed CRASH/EMERGENCY/SHUTDOWN steps.
- Physical voice/media, approvals and uploads retain their explicit DEFERRED status; none is represented as passed.
- Session deadlines remain unchanged. An expired session or unexpected error must stop the human check; this correction does not restore expired authority or bypass authentication.
- The existing Stage 2 other-user/cross-session/actual-remote-host skip remains unverified.
- Restricted-context Electron GPU/DLL cause remains UNCONFIRMED; original Stage 1 PermissionError classification is unchanged.
- Production Core, database, configuration, authentication and enrollment remain untouched. No paid provider calls, live hardware, new models, Stage 5 or acceptance commit.

## Rollback and next human action

Rollback only the two recorded TEST source diffs against matching before/after hashes after verifying the affected TEST processes have exited. Preserve all evidence, stop latches, journals and TEST data. Do not reset unrelated working-tree files. Reverting restores the defective human driver, so human acceptance would remain blocked; it is not a reason to rerun the old procedure.

Use the corrected [human checklist](../../STAGE4-HUMAN-LIFECYCLE-CHECK.md). When ready, run the same documented command; it creates a new namespace and TEST identity. Begin with SELECT, then DENIAL, CRASH, EMERGENCY and SHUTDOWN. Do not reuse either the failed human identity or the automated identities above. The owner performs every prompt personally. Verify the resulting record, source hashes, observations and cleanup before closing Stage 4 or beginning Stage 5.
