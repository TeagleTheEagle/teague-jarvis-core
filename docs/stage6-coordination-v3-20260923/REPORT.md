# Stage 6 TEST launcher/observer coordination — implementation and focused tests

LAUNCHER_COORDINATION_IMPLEMENTED_AND_FOCUSED_TESTED

This is a TEST implementation/focused-test disposition, not live lifecycle acceptance, deadline feasibility proof, Stage 6 acceptance, or authorization to run a campaign.

## Final source

Separate candidate: `D:\JARVIS-STAGE6-LIVE\7f204e14c90a497a8476be0e9927e074\code`.

Final source manifest: `small-source-v3.json` (216 files).

SHA-256: `675ba3f5cd6966fc6040083922d857769af418878f1f403afa38e6d5a6f50fc8`.

`candidate-final-r2.json` and `final-verification-r2.json` are authoritative for this action's final candidate. The initial draft and manifest are preserved in `draft-r1-source.zip`; earlier verification records describe that earlier draft. Workspace implementation templates are development records; use only the final candidate and its verified manifest for a future run.

Original candidate `2d922197cf7d4bb098d8da6e070cbff2`: 194 source files unchanged. Predecessor `978b5ce769244ec9a580fb0846f9bfdc`: 183 unchanged. All 482 recorded source/evidence inputs retain their hashes, sizes and modification timestamps. The twelve small synthetic files were already part of the source copy; their content was independently checked again. No large dataset was accessed.

## Implemented boundary

- Phase A closes local handles and tracker evidence without claiming a still-live eligible console helper exited. Direct workers/probes retain their existing local exit requirements.
- The cleanup origin is recorded at tree-cleanup entry. All terminal acceptance uses the original origin plus exactly twenty seconds; no later reset.
- The existing authority tracer has a separate native TEST successor that publishes an immutable, exclusive terminal receipt while active. Receipt publication does not grant acceptance. It reads fixed evidence filenames, does not accept arbitrary commands, and adds no process-termination or workload-launch capability.
- Kernel/handle instance, parent, image, session, run/source/obligation digests and handoff timing are checked. Creation verification must precede local handle release. Final kernel evidence must agree with the receipt.
- The launcher gates successful shutdown on terminal evidence and a workload-only census. It then drains application, detailed and authority observers in dependency order. The authority tracer retains an additional subordinate-tail capture barrier.
- A fixed external driver verifies launcher/observer exits and persists the final zero-process/zero-trace census. It never invokes the finalizer automatically.
- The checker/finalizer successors evaluate completed evidence, deadline/census ordering and final streams. A provisional receipt cannot conceal later stream loss or contradictions. Historical failures and `REJECTED` records cannot become acceptance.
- The existing 4.6-second application quiescence, 1.1-second authority drain, heartbeat limit and process deadlines are unchanged. Post-failure cleanup cannot repair an expired acceptance window.
- Existing frozen checker files and durable-segment implementation are unchanged. The two amended local admission points are in separate versioned successors.

## Exact source changes

New successor modules: `authority_trace_v3.cpp`, `terminal_receipt_v3.hpp`, `small_launch_v3.ps1`, `terminal_control_v3.ps1`, `evidence_support_v3.py`, `large_collect_v3.py`, `traced_collect_v3.py`, `small_binding_v3.py`, `tracker_adapter_v3.py`, `support_verifier_v3.py`, `coordination_v3.py`, `completed_v3.py`, `external_driver_v3.py`, `small_check_v3.py`, `small_finalize_v3.py`.

Focused fixtures: `test_coordination_v3.py`, `test_successor_v3.py`, `native_receipt_fixture.cpp`, plus the PowerShell gate test in this report directory.

Generated artifacts: `J6AuthorityTraceV3.exe`, `J6ReceiptFixtureV3.exe` and their two `.obj` files.

Only in the NEW candidate, the fixed native entry filename `traced_collect.py` is a narrow shim to `traced_collect_v3`; `baseline-allowlist.json` is rebound to that candidate's small synthetic directory, with protected roots empty and real protected access false. Original versions remain unchanged in the original candidate.

Every changed/new candidate artifact, its SHA-256 and size is listed in `final-verification-r2.json`. Complete text changes are in `implementation-final-r2.diff`.

## Final validation

| Check | Result | Evidence |
|---|---|---|
| Requested 43 cases plus additional evidence rejections | 54 Python tests passed | `focused-85a38b5ffca14f3fb636951d5685b6ad/command-1.json` |
| Actual PowerShell receipt/census gate with offline API seams | 17 checks passed | same folder, `command-2.json` |
| Python syntax | 13 affected files parsed | same folder, `result.json` |
| PowerShell syntax | 2 scripts parsed | same folder, `command-3.json` |
| Existing actual qualifier, coverage, stream, adapter, finalizer and journal regressions | 44 Python tests passed | same folder, `command-4.json` |
| Actual successor binding, local evidence and mock-handle tracker tests | 12 Python tests passed | `successor-tests-final-r2.json` |
| Native successor/fixture compilation | Both targets compiled | `native-real-format-after-fix.json` |
| Actual native receipt producer using constructed row evidence | 10 checks passed | `native-real-format-after-fix.json` |

Total Python methods: 110 passed. PowerShell/native check counts are separate, not inflated into Python test counts. Earlier repeated runs are not additional final tests. Offline fixtures are not substitutes for the future actual live process/observer test.

Exact commands are recorded in the cited JSON files. Compiler setup affects only its child command environment; no installation or persistent environment/security change occurred.

## Preserved transitional findings

1. Initial compiler shell quoting failed before compilation; the fixed build-script invocation compiled successfully.
2. Focused preparation attempted to create an already-copied synthetic directory. It stopped before compilation/execution. The next preparation verified existing identical files instead of overwriting them.
3. Native receipt parsing initially rejected the real declaration's decimal values (for example `13.6`). The offline reproduction exited 90 with `separator`. The parser now accepts JSON decimal syntax while retaining exact-integer requirements for identity/clock fields. The same fixture then passed. Limits were not changed.
4. A read-only check of command PID 1544 showed native creation FILETIME `134346004017751746` versus CIM `134346004017751740`. The draft census compared these representations exactly and could reject the same process. Final revision uses CIM for enumeration and obtains the native process creation identity for matching; it does not round identities. Offline tests cover the precision difference and a reused-PID mismatch.

The preserved small-live failure remains FAILED. None of these findings explains unrelated historical delays. Historical 21 AMBIGUOUS / 1 UNMATCHED remain unchanged. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

## Cleanup and preservation

`final-host-census.json`: host-context read-only enumeration at 2026-09-23T01:24:37.3436185Z found zero matching diagnostic/VirtualBox processes and zero diagnostic trace sessions. Subsequent focused commands also completed normally; no observer or live collector was launched in this action. A final supplemental census and final archive receipt accompany this report.

No UAC/Administrator process, live integrated validation, protected VM/configuration access, production change, backup/restore, acceptance commit or protected hashing occurred.

## Limitations and rollback

Live helper capture, real observer shutdown timing and completing the complete Phase B within twenty seconds remain unproven. The native fixture used constructed rows and did not start ETW. PowerShell tests deliberately replace process/CIM access with controlled inputs. A fresh live attempt may expose a timing or integration failure and must remain failed if it does.

The fixed TEST controller and native parser target this bounded Windows candidate; this is not a general deployment or new production authority interface. Archive verification is a separate requirement and must be confirmed by `archive-receipt.json` rather than inferred from this report.

Rollback: do not use this new candidate. The original source candidates, frozen checkers, historical failed runs and canonical archives remain unchanged. No installation/production rollback is necessary. Retain the new candidate and failed fixtures as evidence; do not delete them automatically.

STOP. The exact proposed single live procedure is in `ONE_RUN_REVIEW.md`; it requires separate owner approval, including its three existing observer UAC prompts. It has NOT been executed.
