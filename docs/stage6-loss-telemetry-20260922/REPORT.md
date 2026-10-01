# Stage 6 TEST loss telemetry — 2026-09-22

STATUS: TELEMETRY IMPLEMENTED AND SMALL DIAGNOSTICS VALIDATED.

Stage 6 remains incomplete. Historical combined tracing loss remains UNCONFIRMED. No acceptance, medium, large, collector or protected-baseline rerun occurred.

## Boundary and exact changes

Separate candidate: `D:\JARVIS-STAGE6-LIVE\f40cb16a8a384236b05179bc8f2aea6b\code`.

Modified TEST sources, copied from the preserved candidate:

- `authority_trace.cpp`: startup/control phases; first callback; callback selection, guard and metadata timing; periodic read-only ETW queries; separate final telemetry output.
- `startup_trace.cpp`: equivalent instrumentation for the detailed channel, retaining its original providers and event filters.
- `durable_sink.hpp` and `trace_sink.hpp`: wrappers measuring WriteFile, FlushFileBuffers and CloseHandle separately. Existing sink data format, bounds, serialization, hash and durability behavior remain unchanged.
- New `trace_telemetry.hpp`: bounded in-memory metrics, 128 phase slots and 2,048 counter snapshots; one-second query cadence on the existing control loop; no callback filesystem writes. Query storage is separate from session configuration storage. Snapshot/query/phase overflow errors prevent successful tracer exit. Counters and timing are written to `loss-telemetry.json` after consumer join and sink finalization.
- New `telemetry_test.cpp`, `live.ps1` and report-side build/check tools: diagnostic-only fixtures. `live.ps1` is not an acceptance launcher and does not invoke the collector.

Restored the detailed sink header into the NEW candidate from its hash-matched historical build. The original candidate and its binaries were not edited. Final source hashes and complete diffs are in `integrity.json` and `final-diffs/`; initial preparation and subsequent fixes remain preserved separately.

No change to capture provider keywords, buffer requests (64 KiB/min4/max64), one-second ETW flush timer, tracer 180/1200-second bounds, queue limits, identity filters or existing nonzero-loss rejection. No heartbeat threshold or collector deadline was changed. UAC was used only for the identified TEST tracer processes, with per-run owner approval. Codex and launcher logic remained non-elevated.

## Focused validation

Final focused result: **30 native assertions**, **10,000 concurrent callback updates**, **17 executable cases PASS**.

Coverage includes separate query storage, QUERY-only operation, exact counter capture, query errors, snapshot/phase overflow, concurrent count/selection accounting, single-clock markers, metric aggregation, four detailed sink cases (normal plus three faults), and twelve durable sink cases (normal plus eleven faults). Normal detailed segments were SHA-256 checked. Static comparisons verified unchanged capture settings and original source hashes.

Commands used installed Python `-B` with report-side `build.py`, `test_candidate.py`, and `check_live.py`. Native compilation used installed MSVC 14.44.35207, Windows SDK 10.0.26100.0, `/std:c++17 /EHsc /MT /O2 /W4`; exact arguments/results are preserved in build directories. The five final native targets compiled successfully. No dependency installation occurred.

The corrected launcher also passed an actual non-elevated three-probe lifecycle test: run `a2019c871d484030a5ccedcc55188fc8`. Creator-owned image/creation capture and retained-handle exit identity are distinct; no post-exit PID identity lookup is used.

## Live diagnostic comparisons

Each case used three identical tiny native test workloads (`J6TelemetryTest.exe`), fresh output directories, fresh tracer instances and fixed two-second observation windows before/after work to exercise periodic counter collection. No application-event observer, native PE debugger, heartbeat acceptance monitor or collector was started. These deliberately isolated diagnostic runs do NOT replace the complete integrated acceptance workflow or its mandatory independent channels.

| Case / run ID | Callback count | Selected | Counter snapshots | ETW EventsLost | Result |
|---|---:|---:|---:|---:|---|
| Authority `e78a9f8e98414394997c89b23468d1fd` | 13 | 12 | 9 | 0 | PASS |
| Detail `0e11f5cbb5314824a9dd74c1c0a68c36` | 513,595 | 4,057 | 8 | 0 | PASS |
| Combined authority `2604664358f64fcdbd7fa0ae00d89a4a` | 22 | 16 | 14 | 0 | PASS |
| Combined detail (same run) | 359,989 | 4,067 | 9 | 0 | PASS |

All snapshot queries succeeded; no telemetry overflow; zero final EventsLost, RealTimeBuffersLost and LogBuffersLost in these runs. All nine probe START/STOP pairs were matched to creator-owned creation identity. Kernel-measured probe lifetimes ranged 0.0261979–0.0303032 seconds. Tracers and probes exited normally.

Actual buffers: authority 32; detail-only 32/33/39; combined detail 32/33/40. Maximum query duration: 0.0000845 seconds. Maximum callback interval: authority-only 0.0014731 seconds; detail-only 0.3980078 seconds; combined authority 0.0011012 seconds; combined detail 0.1913926 seconds. Callback intervals include descheduling and nested work; they are not proof of CPU execution time or a historical loss mechanism.

The large difference between received callbacks and selected records is now measured directly. Zero loss on these tiny isolated workloads does not clear the original loss or establish safe capacity under application-observer finalization.

Raw launch commands use installed `pwsh.exe -NoProfile -File <candidate>\live.ps1 -Mode authority|detail|combined -RunId <IDs above>`. `checked-<runid>.json` records the per-channel checks, probe identities, timing and cleanup.

## Failures preserved and narrowly corrected

1. Initial compilation failed because a Windows `min` macro collided with `std::min` in the new header. `NOMINMAX` now precedes Windows headers. The failed compiler output remains preserved.
2. Initial authority diagnostic `99bdb7a3d80944318790226f07923832` failed because the NEW launcher repeated image lookup after a probe exited, despite successful creation-time image capture. It now reuses that early image evidence and verifies creation/exit FILETIME through the retained handle. A standalone non-elevated test passed before the fresh live comparisons. The original run remains FAIL.
3. That failed run exposed a NEW marker defect: two QPC calls passed as arguments could evaluate in reverse order. A single-clock `mark` fixes this; a focused assertion and live phase-order checks cover it. Revision1 source/binaries and evidence remain preserved.

No acceptance retry occurred. Failed diagnostic artifacts were not overwritten. These new TEST defects do not explain the historical combined ETW loss.

Initial finalization also stopped before archive creation because the build inventory included `live.ps1`, whose subsequently added harness-only mode was an intentional validated edit. Final verification compares compiled artifacts to the build inventory and the launcher to its reviewed report-side source, recording both separately. See `finalization-initial-failure.json`; no unknown mismatch was waived.

## Cleanup, preservation and archive

Final independent host census at 2026-09-22T08:44:11.0110346Z found **zero matching diagnostic/VirtualBox processes and zero diagnostic trace sessions**. All launched observers exited via their existing stop-file path; no forced termination. See `final/dc90a8cb641b41a28a2f1d81297b58e2/final-host-state.json`.

Protected VM/configuration: NOT ACCESSED. Production JARVIS: NOT MODIFIED. Synthetic large dataset: NOT ACCESSED. No account, ACL, security-policy, schema or application changes. No acceptance commit.

Archive receipt records the new archive path, member verification count and SHA-256. Prior small-integration and diagnosis archives are hash-checked separately by finalization. Finalization fails if expected source/archive hashes differ.

## Limitations and next action

Telemetry itself adds measurement overhead. Bounded counters do not remove observer effects. QUERY sampling localizes a loss interval, not individual missing events. Existing aggregate timing cannot assign a long callback to a precise individual process/event. ProcessTrace entry is recorded immediately before the API call, not proof that every provider is already being drained.

The original collector/application-observer workload, application heartbeat, CIM evidence, native PE-entry channel and complete helper qualification were not exercised by these isolated comparisons. Their acceptance requirements remain unchanged.

Next proposed step: a single bounded SMALL integrated diagnostic with this telemetry candidate and the existing application observer/collector, preserving all independent channels. Correlate loss-counter increments with startup, collection and application-observer finalization. Do not adjust buffers/providers or promote large/protected validation on these results alone.

Rollback: select the unchanged prior candidate at `ac2f7b1000034e9bbcb0486fcb6ef9cb`; preserve this diagnostic candidate and archives as evidence. No runtime rollback is required.

Historical 21 AMBIGUOUS / 1 UNMATCHED remain unchanged. Historical delay/loss causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
