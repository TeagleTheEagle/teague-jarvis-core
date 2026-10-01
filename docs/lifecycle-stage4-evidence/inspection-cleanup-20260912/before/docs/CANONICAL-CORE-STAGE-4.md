# Canonical Core Stage 4 — implementation preflight / scope review

Status: **FAIL / INCOMPLETE — SCOPE EXPANSION REVIEW REQUIRED**. No runtime implementation or Stage 4 acceptance is claimed.

The user authorized isolated implementation of the ownership/drain design, with an explicit STOP AND REQUEST REVIEW requirement for files/modules beyond its exact scope. Preflight identified the client-side native identity dependency below. Production and real TEST Core startup were not attempted.

## Dependency requiring review

The unchanged Stage 2 `bootstrap.client` first checks `pipe.peer() == pinned_peer`, before sending hello, then checks authenticated transcript identity, the client's OS process binding and protocol before sending client proof/token. `pipe_transport.Pipe.peer` calls Windows GetNamedPipeServerProcessId/GetNamedPipeClientProcessId and verifies OS creation time and executable digest using process handles.

Neither Electron entry contains that bridge. Current desktop/intelligence package manifests list Electron only. Inspection of installed desktop native modules found archive-extraction binaries, not a pipe-peer identity binding. Installed Node net.Socket type declarations expose no corresponding peer-PID/creation-time API. These are local inspection results, not a claim that every possible transport implementation has been ruled out.

The proposed shared `stage4_client.cjs` can implement framing/HMAC/origin checks, but a pure JS translation must not substitute descriptor-supplied PID information for the accepted OS-observed pipe peer. A matching PID, application name, HMAC proof or health response alone is not the full accepted check. Changing that trust contract also needs review.

Spawning the Python Stage 2 client directly from Intelligence would conflict with the earlier explicit no-Python-spawn client constraint and would authenticate the helper process rather than the Electron process. It is not being introduced as an unreviewed workaround. No temporary alternate backend was created.

## Proposed precise scope addition — NOT IMPLEMENTED

Review a narrow Windows native transport/identity binding for the shared Electron TEST adapter:

- NEW `stage4_native/peer_identity.cc`: owns the TEST named-pipe connection and exposes bounded framing plus OS-observed server/client process identity. Do not accept renderer-supplied handles or arbitrary process operations. Validate the same connected handle used for authentication, not a separate probe connection.
- NEW `stage4_native/CMakeLists.txt`: local build definition for the Electron-compatible native binding; no download/install steps implicitly authorized.
- NEW `stage4_native/README.md`: bridge contract, build prerequisites, supported runtime and trust limitations.
- Add bridge tests to the already approved `desktop/test/stage4-client.test.cjs` and shared client integration tests. Use the already approved `stage4_client.cjs` as the sole native main-process caller; renderer receives no raw handles/keys.

Required bridge checks: wrong pipe server, stale creation identity, mismatched executable, unexpected TEST namespace, peer death during authentication, non-inheritable handles, same-connection binding, bounded malformed frames/timeouts, and no reusable credentials sent before expected-peer/server-proof validation. Keep the existing Stage 2 algorithms and tests unchanged.

First inspect availability of an existing compatible compiler, Electron/Node headers and build tools after scope approval. If unavailable, report the exact build dependency; this proposal does not authorize system installations, security changes, downloads or a weaker fallback. A native bridge would run within the existing client, not create another Core, Store or provider.

This is the proposed solution, not a completed native API design/security proof. A separately reviewed broker transport is an alternative architecture, but is not silently selected here.

## Checks performed and retained evidence

- Unchanged Stage 1: **20 discovered; 19 passed; 1 skipped; 0 failures/errors; 28.426 seconds**.
- Cross-session/fast-user-switching remains skipped/unverified.
- Raw run: `tests/lifecycle_stage1/evidence/TEST-c57078734e8a4d40a266e38c3fb6f77f/results.json`.
- Byte-identical selected evidence: `docs/lifecycle-stage4-evidence/stage1-preflight.json`.
- Source baseline: `docs/lifecycle-stage4-evidence/implementation-baseline.json`.
- Machine-readable stop result: `docs/lifecycle-stage4-evidence/scope-review.json`.
- All 25 baseline source/launcher/Stage 1–3 Python hashes still match. Existing unrelated dirty work was neither reverted nor staged.
- Stage 4 tests: **0 run**. Stage 2/3 reruns: **NOT RUN**, stopped at the scope gate. Historical passing results are not substituted.
- Actual Electron/manual voice/media verification: **NOT RUN**.

The earlier Stage 1 PermissionError remains **ROOT CAUSE UNCONFIRMED / FAIL-SAFE / REVIEW REQUIRED**. It was not observed in this rerun; this does not erase it or unblock production. Prior evidence remains intact. This new scope dependency is distinct from that issue.

No runtime development failure is invented: no Stage 4 runtime was built. Read-only discovery commands initially attempted absent package-lock files and a literal wildcard path; inspection then used the actual installed pnpm type path. Those command errors are not lifecycle/security test failures.

## Boundaries and next decision

Production runtime files changed by this task: NO.

Production data changed by this task: NO.

Production Core restarted: NO.

Real TEST Core started: NO. Stage 1 ran only its existing credential-free dummy lock fixtures, not a JARVIS App.

Stage 5 started: NO.

Only the implementation baseline, selected regression evidence, scope-review record and this report were created in this implementation preflight. The ownership/drain design document predates this authorization and remains separate. No runtime files were created. No commit was made; commit ID: NONE. No broad records sync occurred.

Approval requested: add the three native-bridge files above and their tests to isolated Stage 4 scope, preserving the same connected-pipe OS identity checks and all existing production/Stage 1–3 boundaries. Stop for a further dependency review if the required local build tools are unavailable. No production activation is requested.

## Publication/read contention diagnostic — 2026-09-11

Status: **STOP FOR CORRECTION REVIEW**. Stage 4 runtime integration remains incomplete. This diagnostic is separately authorized by the additional investigation lead; it does not change accepted Stage 1 semantics.

### Source finding

The unchanged `tests/lifecycle_stage1/harness.py` Core loop reads challenge.json and calls write(response.json, ...) on every nonempty request, then sleeps 15ms. It does not remember the last answered challenge. Its coordinator polls at 20ms until a matching response is validated, then returns. Thus the Core continues publishing even after a successful reconciliation while the challenge remains present. This repeated-publication behavior is confirmed by source inspection; its role in the historical failure remains inferred.

### Experiment

`tests/lifecycle_stage4/fixtures.py` contains only disposable publisher/reader processes. It imports no JARVIS App, Store, providers or accepted harness. The instrumented writer preserves the temporary.write_text -> os.replace sequence, logs the exact Python operation on error, and stops on a publication error without retry. No lock, ACL, identity, provider or production change was made. No Core was started.

Each trial lasts 1.2 seconds with one unchanged synthetic challenge, separate TEST directory, one publisher and one reader (idle in the no-reader control). Mode order alternates across pairs. Per-challenge publication attempts/completions, all errors, process IDs, monotonic timestamps, source/destination paths and tracebacks are preserved. Every case and its leftover files is retained. The once-per-challenge comparator records a challenge only after successful publication and does not change Stage 1 code.

| Profile | Repeated failed/trials | Once failed/trials | Repeated successful publications |
|---|---:|---:|---:|
| Baseline 20ms reader / 15ms writer | 3/20 | 0/20 | 1,368 |
| Amplified reader, 0.5ms interval | 10/10 | 0/10 | 222 |
| Amplified reader holds open file for 10ms | 10/10 | 0/10 | 35 |
| No-reader control | 0/10 | 0/10 | 709 |

Total: **100 completed diagnostic trials**. The 23 publication failures are expected retained observations, not 23 accepted regression failures. All 23 captured `PermissionError`, `errno=13`, `winerror=5`, at `os.replace(temporary, response.json)`, with full traceback and paths. All 23 retained temporary files contain valid JSON for the unchanged challenge. Once mode published exactly once in each of 50 trials.

### Interpretation and limitations

Repeated publication materially increased observed per-trial failures under reader contention in this experiment. The no-reader control and amplified-reader profiles support a replace/read contention mechanism. This is a reproduced reliability defect/risk in the publication pattern, not proof of the exact historical failure or the identity of a blocking handle/filter.

The baseline retains Stage 1's sleep intervals but continues polling for the trial duration; real reconciliation stops when it succeeds. Therefore its failure percentage is not a production or Stage 1 incidence estimate. Fast/held-read profiles deliberately amplify overlap. Cases were run on one machine, with finite samples and alternating rather than randomized mode order; no process-wide native handle trace, antivirus attribution or power-loss testing was performed. Zero comparator failures does not prove that publishing once cannot fail, especially on a new challenge while a reader still has the prior response open. No unique-challenge transition safety acceptance is claimed by these single-challenge trials.

Historical classification remains **ROOT CAUSE UNCONFIRMED / FAIL-SAFE / REVIEW REQUIRED**. Historical os.replace remains inferred. New diagnostic failures establish the Python call and WinError for these runs only; they do not supply the missing historical traceback or WinError.

### Minimum proposed correction — NOT APPLIED

Subject to separate approval, change only the accepted Core fixture publication loop to remember the last successfully published challenge value within that Core instance and skip redundant publication for an identical value. Publish for a new challenge; update the remembered value only after write success. Keep lifetime/supervisor locks, fresh coordinator challenges, full identity comparison, timeouts and fail-closed write-error behavior unchanged. No retries, permissive sharing, ACL changes, file deletion, fabricated adoption or production changes.

Before accepting that delta, separately test unchanged challenge suppression, new challenge response, process/epoch reset, stale/malformed challenges, publication failure, missing response behavior, concurrent coordinators and the complete Stage 1 exclusion/crash suite plus Stage 2/3 regressions. Missing-response behavior must be reviewed explicitly; do not silently recreate or reuse stale responses. If once-per-challenge is insufficient, return for review rather than broaden the correction.

The defect concern triggers the user's STOP-and-propose gate. No Stage 1 correction or further client integration was performed after the experiment.

### Evidence and boundaries

- `docs/lifecycle-stage4-evidence/publication-diagnostic-review.json`: machine-readable summary, unchanged baseline verification and SHA256 manifest.
- `docs/lifecycle-stage4-evidence/publication-diagnostic-b41e867c8ffa4a7b9956caeb3d181f79/`: all 80 comparative cases, summaries, successful and failed publications.
- `docs/lifecycle-stage4-evidence/publication-diagnostic-b5c369042899488f8a68d99b403f8a34/`: 20 no-reader controls.
- `tests/lifecycle_stage4/fixtures.py`: isolated diagnostic source. No accepted Stage 1 import or monkeypatch.

All 25 preflight baseline file hashes still match, including accepted Stage 1–3 source and production modules. No Stage 1–3 regression was rerun by this diagnostic task. Earlier runs remain separate evidence.

PRODUCTION DATABASE MODIFIED: NO. PRODUCTION CORE RESTARTED: NO. PRODUCTION CONFIGURATION CHANGED: NO. STAGE 1 CODE CHANGED: NO. STAGE 5 STARTED: NO. FIX APPLIED: NO.

No commit or broad source-record sync performed. STOP FOR REVIEW of the narrow Stage 1 correction above.

## Approved isolated Stage 1 correction — validation complete

Status: **ISOLATED CORRECTION VALIDATED / STOP FOR REVIEW**. This section supersedes the earlier unimplemented-correction proposal, not its historical evidence.

### Exact change

Only `tests/lifecycle_stage1/harness.py` accepted logic changed: initialize a per-instance unanswered sentinel, compare the incoming challenge to last_answered, publish when different, then assign last_answered only after successful write returns. An unchanged challenge does not republish. No changes to lifetime locking, startup exclusion, coordinator reconciliation, identity/PID/creation checks, freshness generation, stop latch or fail-closed behavior. No retries. The accepted Stage 1 regression test file and all Stage 2 source remain byte-identical to baseline.

### Actual corrected implementation tests

`tests/lifecycle_stage4/test_stage4.py` invokes the actual corrected Stage 1 core() in disposable credential-free fixture processes. Diagnostic wrappers record calls to the actual write helper, preserve its exceptions, and observe last_answered on an exception without changing its value. This is not another production JARVIS/App/Store. Each trial uses a separate TEST namespace under the accepted harness evidence directory, real Core lifetime locking and an unchanged challenge for 1.2 seconds. The reader profiles match the preceding controlled experiment; all successful/failed artifacts remain retained.

| Profile | BEFORE repeated failures | AFTER corrected failures | AFTER successful publications |
|---|---:|---:|---:|
| Normal polling intervals | 3/20 | 0/20 | 20 |
| Faster polling | 10/10 | 0/10 | 10 |
| Reader holds response briefly | 10/10 | 0/10 | 10 |
| No reader | 0/10 | 0/10 | 10 |

Two additional actual-fixture semantic checks passed:

1. A receives a response with the actual live Core identity; fresh B receives a fresh matching response; repeated B produces no third publication; B's response does not satisfy a C challenge.
2. After successful A, a deliberately held read handle prevents publication of fail-B. The actual write raises WinError 5; its traceback is preserved; Core exception-frame inspection shows last_answered is still A. The old response remains A, the failure is recorded FAILED_CLOSED, and this fixture starts no replacement. This injected failure is a successful fail-closed test, not counted as an ordinary comparison failure. Test-local handle sharing was used solely to create the approved failure injection; accepted lock code, filesystem ACLs and Windows security settings were unchanged.

### Regressions and limits

- Full unchanged Stage 1 test suite: **20 discovered; 19 passed; 1 skipped; 0 failed/errors; 28.634 seconds**. Includes independent Core ownership, crash/recovery, coordinator loss/adoption, repeated concurrent starts, stop/start races, stale metadata, PID creation mismatch and uncertainty/fail-closed cases.
- Full unchanged Stage 2 test suite: **36 discovered; 35 passed; 1 skipped; 0 failed/errors; 67.335 seconds**. Includes composed coordinator startup races, identities, session/token validation and fake-listener credential protection.
- Stage 4 diagnostic dependency checks: **50 comparisons and 2 semantic scenarios passed**. No native bridge or real-client Stage 4 acceptance suite exists yet; no Stage 4 completion claimed.
- Python syntax parsing passed for the changed harness, unchanged Stage 1 tests and both Stage 4 diagnostic files. Stage 3 was not rerun in this correction task.
- Cross-session/other-user/actual remote-host coverage remains skipped/unverified. No production or physical-media verification was performed.

The correction removes the demonstrated redundant-publication exposure in these tests. New challenge publication can still fail; that path remains fail-closed. Finite zero-failure samples do not prove universal absence of errors. Real coordinator polling stops after success, unlike sustained diagnostic polling; percentages are experiment-specific. No missing-file recovery, production retry or speculative protocol change was introduced.

### Separate historical and new findings

HISTORICAL ROOT CAUSE: **UNCONFIRMED**. Historical classification stays **ROOT CAUSE UNCONFIRMED / FAIL-SAFE / REVIEW REQUIRED**. Its absent traceback/WinError cannot be retroactively supplied.

NEW EXPERIMENTAL FINDING: **reproducible os.replace/read-contention mechanism confirmed in isolated file-IPC tests**, with WinError 5 and exact Python traceback; corrected actual Stage 1 fixture eliminates redundant publications and had 0/50 ordinary comparison failures. No native handle/filter attribution is claimed.

Proposed reviewed reliability disposition: **reproduced redundant-publication defect corrected and validated in isolation; historical cause unconfirmed; review still required**. Production gate is NOT automatically cleared. Recommend reviewing this narrow delta and retained evidence before considering the Stage 1 reliability gate disposition; production activation and the remaining lifecycle/auth/data/client gates require separate review.

### Shortcut read-only finding

Both JARVIS INDUSTRIES.lnk and TEAGUE INDUSTRIES.lnk currently point to the same PowerShell executable, Start-Desktop.ps1 and project working directory. Both currently include `-ExecutionPolicy Bypass`; this was observed, not added or executed. The script starts Electron on the same desktop directory. desktop/main.cjs acquires requestSingleInstanceLock before startBackend; a losing instance quits and the winning instance handles second-instance by showing its window.

Consequently shortcut launches can cause competing Electron startup attempts, but do not invoke the isolated Stage 1 harness/coordinator or its TEST response files. They are unrelated to the historical isolated failure and relevant to future production startup validation. This is a source-path assessment, not a live simultaneous-launch test or a system-wide exclusion guarantee across users/profiles/direct backend starts. Neither shortcut nor production runtime was modified or launched.

### Evidence, changed files and stop

- Changed accepted file: tests/lifecycle_stage1/harness.py (only publication suppression).
- Added: tests/lifecycle_stage4/test_stage4.py (diagnostic runner, NOT full Stage 4 acceptance suite).
- Updated: docs/CANONICAL-CORE-STAGE-4.md (this report).
- Added selected evidence: docs/lifecycle-stage4-evidence/correction-TEST-54b75d4077704d88a9fd56e17eb975ed/ including comparison.json, semantics.json, summary.json, stage1-regression.json, stage2-regression.json, review.json.
- Raw corrected fixtures: tests/lifecycle_stage1/evidence/TEST-54b75d4077704d88a9fd56e17eb975ed/.
- Raw Stage 1 regression: tests/lifecycle_stage1/evidence/TEST-041ef70285514917a7b3a9c9df5751f1/results.json.
- Raw Stage 2 regression: tests/lifecycle_stage2/evidence/b4507f606d4a4e81b0e2bb08779b4a5e.json.

Of the 25 baseline files, only the explicitly approved tests/lifecycle_stage1/harness.py differs. Production modules/data/configuration/launchers/shortcuts were untouched. No production Core restart, Stage 5, production activation, repair deployment or provider changes occurred. Prior diagnostic fixtures and all prior failure evidence remain intact.

Commit ID: **NONE**. No commit was requested for this correction; unrelated working-tree changes remain separate. STOP FOR REVIEW.

## Resumed native bridge work and capability roadmap

The clean Stage 1 correction commit is 8f0b9bce181800f9339249c4024e396246e94208 (15 files). Subsequent Stage 4 bridge changes remain separate and uncommitted.

Added the approved three native files, the trusted stage4_client.cjs bootstrap draft, desktop/test/stage4-client.test.cjs, and native diagnostic mode in the already approved Stage 4 fixtures.py. The native bridge builds and loads in Electron 44.2.0. Initial build failed with DWORD versus uint32_t pointer mismatch; that log is retained as native-first-build-failure.json. The corrected build succeeded. Seven actual native pipe/self checks passed (correct peer, wrong PID, wrong creation time, wrong executable hash, wrong namespace, missing bridge, and current-process-only information). Six JavaScript tests passed (exact integer serialization, unsafe number rejection, canonical escaping, missing bridge, production-mode denial, renderer denial). These are partial tests, not the full Stage 4 security/identity suite or acceptance matrix. Evidence: native-probe-cb6ed6a44d3741d783b6c6ded6e002a0.json.

### Remaining trust-contract review before real-client integration

Accepted Stage 2 permits different bootstrap-peer and Core process identities. Its client verifies the connected pipe peer before any client proof, and separately calls live process identity verification on the claimed Core. The new connection-bound native API deliberately cannot inspect arbitrary PIDs. The bootstrap draft therefore explicitly rejects different bootstrap/Core PIDs with SEPARATE_CORE_VERIFICATION_REQUIRES_REVIEW. This is a temporary fail-closed implementation guard, NOT an approved requirement to relocate the bootstrap service into Core. Do not silently skip the second live-identity check, treat a signed transcript alone as sufficient, or enable this draft in actual client entry points.

Proposed narrow review delta: a connection-bound verification operation that takes the independently pinned Core PID/creation-time/executable digest from trusted main-process state, returns match/fail only, and cannot enumerate processes or return information for renderer-supplied identifiers. The verified pipe and expected Core relationship must be retained through bootstrap. An alternative is an explicitly reviewed same-process bootstrap/Core arrangement. Either decision must preserve Stage 2 semantics and receive tests before real-client integration. This was not resolved or activated here.

The synchronous native transport also mirrors Stage 2's cancellation-completion wait; it is not evidence of an absolute bounded driver-cancellation guarantee. Keep it off the UI/control thread, and resolve shutdown/worker behavior within the approved drain design before claiming responsive stop controls. No actual Core or production client was launched by these bridge tests.

### User-prioritized future Core acceptance requirement

The user wants recursive self-improvement, goal setting, bounded autonomy and resource use developed as a coherent Core capability. The recent JARVIS reviews only demonstrated reasoning over supplied excerpts/screenshots, not autonomous gathering of complete incident evidence or execution of a controlled diagnostic experiment. Truncation and absence of raw artifacts limited that review; this is a capability/evidence-access gap, not proof that a stronger prompt alone will solve it.

Proposed later acceptance scenario: one authoritative Core detects a seeded fault, gathers complete scoped evidence, generates hypotheses and subgoals within an approved objective, reserves approved test resources, runs isolated comparisons, proposes a minimal patch, verifies it independently, preserves uncertain outcomes and stops READY_FOR_REVIEW with deployed=false. No purchases or expanded access without authorization, no second production Core, no weakening stop/auth/budget/approval boundaries. This records a future requirement, not implementation or activation of additional autonomy during Stage 4.

Production activation remains BLOCKED. Stage 4 is INCOMPLETE. Native trust-contract review remains pending before full real-client integration. No production source/data/authentication/launchers/shortcuts/security settings changed. No Stage 5, Ollama Phase 2, actual repair execution or resource purchases. Existing historical PermissionError classification remains unchanged.

## Approved separate Core identity bridge addition — implemented in isolation

The user explicitly approved the proposed isolated identity-verification addition.
This supersedes the pending narrow trust-contract review above. It does not
approve production activation or imply completion of the full Stage 4 runtime.

The trusted main adapter supplies an independently pinned Core PID, exact decimal
creation time and executable SHA256 when connecting to the independently verified
TEST bootstrap pipe. Native code captures a copy. The resulting connection exposes
verifyCore() with no arguments: live identity matches return true; mismatch,
missing pin, closed connection, native failure or supplied arguments throw.
The verified original pipe peer is checked before and after inspection. No process
enumeration, arbitrary path inspection, renderer interface or lifecycle operation
was added. The adapter verifies server proof and expected transcript identity,
then live Core identity, then client binding/protocol before sending client proof.

### Checks actually performed

- Native Release build passed. Initial MSBuild invocation failed before compilation
  because inherited environment contained both Path and PATH. Retried with only
  the build child's environment case-normalized; no persistent environment or
  security changes. Both outcomes retained in core-pin-build.json.
- 15 native tests passed: existing peer checks plus separate live process,
  wrong Core creation time/digest, dead process, missing pin, forbidden arguments,
  closed connection and immutable captured pin.
- 6 real named-pipe/Python Stage 2 HMAC interoperability cases passed through the
  actual Electron JS bootstrap adapter. Valid separate process exchange succeeds.
  Wrong creation time, wrong digest, dead process and fake server proof disclose
  no client proof/request. Wrong pipe peer sends no frame at all. Test keys are
  ephemeral, transmitted only to the disposable test client over stdin and omitted
  from saved evidence. These are transport/authentication fixtures, not an App/Core.
- 6 JavaScript tests passed (integer precision, canonicalization, missing bridge,
  production denial and renderer denial).
- Unchanged Stage 1 regression: 19 passed, 1 skipped, 0 failures/errors.
- Unchanged Stage 2 regression: 35 passed, 1 skipped, 0 failures/errors.
- Unchanged Stage 3 regression: 43 passed, 0 failures/errors.

Evidence under docs/lifecycle-stage4-evidence:
core-pin-build.json;
native-probe-1e237ca1a094472b9136abdb56dbec1f.json;
core-pin-bootstrap-8df901c1ebef4b968a8859a055426e65.json;
core-pin-stage1-regression.json; core-pin-stage2-regression.json;
core-pin-stage3-regression.json. Original suite evidence paths are in those logs.

### Remaining acceptance work and boundaries

Full Stage 4 ownership/session/drain implementation, actual client attachment,
manual Electron UI and voice/media validation remain incomplete. Native IO must
remain off the UI/control thread; pathological OS cancellation latency is still
unproven. Actual PID recycling and cross-session behavior remain unverified.
Live identity is an observation, not a guarantee a process cannot subsequently exit.
No production module/data/configuration/authentication/launcher changed by this
addition; no production restart. No Stage 5, deployment or additional autonomy.
Historical PermissionError remains ROOT CAUSE UNCONFIRMED / FAIL-SAFE / REVIEW REQUIRED;
the separately reproduced and corrected mechanism does not rewrite history.

Files changed in this addition: stage4_native/peer_identity.cc,
stage4_native/README.md, stage4_client.cjs,
desktop/test/stage4-client.test.cjs, tests/lifecycle_stage4/fixtures.py,
this report and the listed evidence files. No new commit in this step.
Production activation remains BLOCKED pending broader Stage 4 acceptance.

## Core-owned ownership and drain foundation — isolated implementation checkpoint

The master roadmap context keeps execution at Stage 4. Stage 5 reliability attack,
Stage 6 production cutover, Stage 7 release and future capability programmes remain
unauthorized. The earlier activation approval is superseded by that explicit boundary.

Added stage4_sessions.py and stage4_lifecycle.py within the reviewed file scope.
These modules are not wired into production or an Electron client. They instantiate
no App, Store, voice engine, wake detector, provider or Core process.

Implemented ownership foundation:
- Core-issued opaque session credentials retained only as hashes in the registry;
  immutable client/session-family binding, renewal rotation, epoch rejection,
  expiry, detach and enrollment revocation.
- Request owner checks usable before cancellation, event access and approval
  consumption; shared data access is not permission to control foreign requests.
- Single active chat admission under a common lock; no queue or scheduler.
- Separate capture/playback leases, expiry, no foreign takeover and no duplicated
  automatic playback. Leases alone do not control actual hardware yet.
- Separate scoped one-use management capabilities bound to action/operation/family,
  denied to ordinary enrollments. Human-controller and authenticated-bootstrap
  integration remain pending; trusted internal methods are not remote endpoints.

Implemented drain foundation:
- Admission barrier shared with shutdown; content-free TEST operation/stop journal;
  accepted work is recorded before effects and completion after cleanup.
- Worker completion is distinct from a cancellation event or displayed status.
- Ten-second grace / thirty-second deadline logic using a monotonic clock;
  emergency suspension is distinct from shutdown; unresolved work or persistence
  failure enters RECOVERY_REQUIRED and never automatically resumes.
- Same management operation is idempotent and does not restart the deadline.
- FINALIZING only means workers are accounted for; no process exit, lock release,
  listener closure or successful Core shutdown is claimed by these modules.
- Tracked budget references and UNKNOWN outcomes are retained; no refunds or
  universal resource enforcement were added. Ordinary operations remain unmetered.

Validation actually performed: 24 distinct model/thread/journal tests passed,
then ten repeated full model-suite runs passed (240 repeated test executions).
The tests include eight-thread chat contention and admission/stop races, ownership,
renewal/expiry/revocation, media isolation, management denial/expiry/single use,
idempotency, uncooperative worker, late completion, persistence failures, unknown
consumption, archive-style cleanup, malformed journal and destination identity.
Tests exercise real Python threads and isolated synthetic journal files. Deadline
tests advance an injected clock; this is NOT a real 30-second runtime shutdown
guarantee. No microphone, screen sharing, provider call or repair was executed.
Python syntax parsing passed for both modules and the amended Stage 4 test file.

Evidence: lifecycle-stage4-evidence/ownership-model-546943a612a44b24a2c7a007a02cc750.json,
the ten subsequent ownership-model records, and ownership-repeated-validation.json
(all outputs and source hashes). Isolated journal cases are under
tests/lifecycle_stage4/evidence/STAGE4_TEST-*; none contains production data.

Stage 1–3 source was unchanged in this checkpoint; their most recent full reruns
are the passing core-pin-stage1/2/3-regression.json records above. They were not
rerun again for these unintegrated pure modules. The complete Stage 4 matrix,
unchanged Stage 1–3 and affected legacy regressions remain required at integration
closure. No Stage 4 acceptance or clean Stage 4 commit is claimed yet.

Remaining immediate step: compose these modules with authenticated Stage 2
bootstrap and the reviewed lifetime-owned real TEST App, then adapt both actual
clients. Actual VoiceEngine/WakeDetector ownership, DeviceRegistry presence,
all HTTP/approval/upload/stream checks, real listener draining, journal recovery
reconciliation and manual Electron/media gates remain incomplete. Explicit replay
and lease watchdog wiring also remain integration work. Retain this distinction
between a tested foundation and an enabled runtime feature.

Files changed by this checkpoint: stage4_sessions.py, stage4_lifecycle.py,
tests/lifecycle_stage4/test_stage4.py, this report and selected ownership evidence.
Production files/data/configuration/authentication unchanged by this checkpoint;
production Core not restarted; no Stage 5; production activation BLOCKED.

## Authenticated real TEST App composition — integration checkpoint

Implemented stage4_runtime.py and gated server.py hooks. Eight reviewed source
files were preserved before editing under tests/lifecycle_stage4/evidence/
integration-preedit-20260911; their hashes are in real-integration-preedit.json.
Only server.py was changed among those existing source files in this checkpoint.
It is a production-used source file with an explicit TEST branch; claiming that
no production source file changed would be inaccurate. The running production
Core, its data/configuration, authentication and launchers were not modified or
restarted. Legacy mode remains default and its regression suite passed.

The isolated runtime validates a synthetic namespace and existing TEST database
before App construction. Provisioning refuses existing data; it does not migrate
anything. Lifetime ownership is acquired with the unchanged Stage 1 lock before
the real App/Store opens. App construction is single-use, and constructor counters
observe one Store, VoiceEngine and WakeDetector. A second App attempt is rejected
before another Store/provider/voice stack is opened. Source .env is skipped,
personality/model paths are synthetic, and a disposable-child Python audit guard
denies production data/personality/.env reads, outside-namespace writes, external
connections and subprocess/system execution. This cooperative Python guard is
not an OS sandbox or a production security boundary.

Stage 2's unchanged serve_one authenticates each TEST client before the Core-owned
dispatcher handles requests. Session tokens remain hashed in the ownership
registry; client/protocol binding is checked on subsequent operations. Both
authenticated Python TEST clients read the same App Store and identity. They
cannot access/cancel foreign requests or shut down Core as ordinary clients.
Closing ordinary sessions or stdin does not own Core lifetime. A replacement
coordinator reconciles the existing Core through unchanged Stage 1 reconciliation.
Authorized TEST management shutdown closes admission, records intent/stop latch,
drains registered work, closes the listener/control thread and exits with the
lifetime handle held until that exit. Runtime uncertainty remains quarantined.

The real App local-time path and deterministic provider branch were exercised.
The existing VoiceEngine produced explicitly labelled silent WAV fixture audio;
no real provider, microphone or browser-TTS fallback was used. Repeated synthesis
for the same response reuses its operation. Foreign access and retrieval after
playback lease release are denied. This proves a Core synthesis transport fixture,
not the user's normal voice, audibility, microphone ownership or hardware parity.
One WakeDetector is constructed but no real model is loaded and wake is reported
unavailable. Device presence is represented through the existing DeviceRegistry;
its complete reconnect/media matrix remains pending.

### Validation and failed development evidence

- Latest real-App probe: 23/23 checks passed in
  real-app-probe-2a8417c12960487b97b87a6a218f946c.json. Earlier successful 18/21-case
  development probes remain separate and are not summed as independent coverage.
- Three pre-App isolation/recovery checks passed in real-integration-isolation.json:
  wrong data identity, existing fixture overwrite refusal, unresolved prior journal.
- Legacy Python: 212/212 passed. Desktop: 19/19 passed (13 existing plus 6 bridge).
- Unchanged Stage 1: 19 passed/1 skipped; Stage 2: 35 passed/1 skipped;
  Stage 3: 43 passed. Logs: real-integration-*-regression.json.
- Python syntax checks passed for changed runtime/server and existing ownership
  modules. Initial syntax-reader invocation failed because it used cp1252 for
  UTF8 source; explicit UTF8 fixed the validation command, not application code.
- The initial audit guard rejected the validated fixture's read-only SQLite URI.
  Two failed startup records are retained: real-app-probe-09016cf983214c088aa7b51d82ac8902.json
  (traceback initially truncated) and real-app-probe-15d910507e47470b9e01f2f17ea33adc.json
  (full traceback). Child exit 1, before App construction; no production access.
  Correction accepts only the exact validated fixture database's read-only URI;
  general filesystem/SQLite restrictions remain. Successful subsequent probes do
  not erase those failures. No historical Stage 1 incident was reproduced or
  reclassified by these new TEST guard failures.

### Still incomplete

These are actual App + authenticated Python-client tests, NOT actual Teague or
Intelligence Electron attachment. There is no production activation, installer,
Stage 5, live repair or new autonomy. Full client entrypoint integration, native
worker isolation, HTTP/stream/upload/approval ownership coverage, disconnect and
reconnect/lease watchdogs, real voice/media verification, inspection/repair cleanup
hooks and full runtime crash/drain matrix remain outstanding. Journals with
unresolved history currently refuse startup; automatic reconciliation/replay is
not implemented or authorized by a journal record. Final Stage 4 commit and
acceptance are pending; the current files remain an uncommitted checkpoint.

Files changed in this checkpoint: stage4_runtime.py; gated server.py changes;
tests/lifecycle_stage4/fixtures.py; this report and selected integration evidence.
Rollback must remove only these Stage 4 hunks after verified TEST exit, preserving
earlier unrelated edits and all failed/synthetic-state evidence. Production
activation remains BLOCKED. ONE production JARVIS remains authoritative.

## Actual Electron acceptance — Intelligence renderer scope review

Read-only inspection for the requested actual Electron acceptance found a renderer
scope gap. intelligence/index.html contains inline fetch/chat/polling logic,
hard-coded capability/readiness text, and a Voice button without a handler.
The existing server CSP permits self-hosted scripts, not that inline script.
The reviewed Stage 4 affected-file map includes intelligence/main.cjs but does
not include intelligence/index.html or an Intelligence renderer adapter.

Proposed minimal additional file scope:
- intelligence/index.html: add the gated TEST renderer integration point and
  identifiers needed to update actual connection/media status and controls.
- NEW intelligence/stage4-renderer.js: TEST-only actual-interface adapter for the
  narrow trusted preload bridge, scoped request/cancel/media events, and truthful
  disconnected/degraded status. No standalone demo or replacement App/Core.

Keep transport credentials and native identity verification in trusted main/worker
code; renderers receive neither bootstrap/session/management secrets nor general
process-inspection functions. Use the already-approved desktop/preload.cjs for
the narrow shared TEST bridge where suitable. Do not weaken CSP to execute inline
code, or put a second synthesis/provider authority in the renderer. Legacy behavior
must remain on its existing branch. Existing approved main/client/server files
may supply the TEST-only script route and ordinary operation mapping.

Required validation after scope approval: actual Intelligence and Teague Electron
entrypoints against the same authenticated TEST App; no renderer Node/native/key
exposure; foreign request/media denial; missing/dead Core status; no browser-TTS
fallback; local close/crash and reauthentication; existing regression suites.
Rollback removes only these TEST renderer integration hunks/new adapter after
verified TEST client exit, preserving all earlier evidence and unrelated edits.

Status: STOP FOR NARROW FILE-SCOPE REVIEW. No runtime/client code changed or new
Core launched during this inspection. The earlier 23 real-App checks and passing
regressions remain historical evidence; they do not establish Electron acceptance.
No final Stage 4 commit or acceptance; production activation and Stage 5 blocked.

## Approved renderer integration — actual Electron checkpoint, 11 September 2026

The user approved intelligence/index.html and intelligence/stage4-renderer.js.
This supersedes the preceding file-scope pause, not any production gate.

Implemented gated `--stage4-test` entry branches in both actual main.cjs files,
before legacy preferences/backend/descriptor handling. Both use the reviewed
native bridge in a worker, authenticate the pinned TEST pipe/Core, and attach
ordinary sessions. Session secrets remain in the worker; renderer IPC exposes
connection, shared reads, own request/status/cancel and local stop requests only.
No renderer native/management API, no browser TTS fallback, no microphone grant.
An authenticated 30-second renewal rotates the session token without disclosing
it to main callers or renderer code. Queuing is bounded to eight calls.

TEST UI assets use an exact allowlist under `stage4-test://app/`, isolated Electron
profiles, denied external requests/redirects/permissions, sandboxed renderers and
strict CSP. Actual Teague/Intelligence HTML and existing forms are exercised.
The TEST-only adapter disables unsupported features and removes misleading
historical capability/readiness panels; this is not full production UI parity.
Teague's TEST /app.js maps to this adapter, leaving static/app.js byte-identical
to its preintegration snapshot. Existing Intelligence legacy inline behavior is
guarded from the TEST bridge; no CSP weakening was added.

### Results actually obtained

- Actual Electron 44.2.0: **29 checks passed** in
  `electron-app-probe-1e08fbd195914cd08ad18be0034b7760.json`.
  Both real entrypoints/renderer forms authenticate the same Core and TEST state.
  A request through each actual form completed. Foreign cancellation through the
  renderer was denied. Both close orders, last-client departure, reopen without
  replay, fresh renewal and Intelligence renderer crash retained the Core and
  the other client. Separate authorized shutdown completed; the lock released
  only after exit. No claim of capture or audible voice verification.
- Renderer boundary checks denied external fetch and invalid request IDs; neither
  renderer exposed Node, the production preload bridge, native access or shutdown.
- Python **212 passed**; desktop **19 passed**; new Intelligence **3 passed**.
- Stage 1 **19 passed/1 skipped**, Stage 2 **35 passed/1 skipped**, Stage 3 **43 passed**.
  Logs are electron-python/stage1/stage2/stage3-* and electron-static-js-*.
- Ownership/drain model: latest **27 passed**, including explicit owner-only
  re-evaluation after late known completion, separate shutdown after suspension,
  failed final journal persistence, and retaining the failed original attempt.
  `ownership-model-86e5a210b2d44cfaa58b86c557e7ac35.json`.
- JS syntax and Python compilation passed. Full regression counts above precede
  the latest drain-journal/real-deadline additions; those additions still require
  the complete end-to-end rerun. Model success is not a real 30-second deadline PASS.
- Screenshots were inspected. The first capture revealed wrong Intelligence CSS
  mapping and Teague hidden-page classes; both were fixed in TEST adapters.
  Later screenshots show styled authenticated interfaces. Earlier captures retained.

### Failed development evidence is retained

The first GUI probes exited on stdin EOF: Windows GUI Electron did not receive
that channel. The TEST parent now uses inherited Node IPC, with configuration in
memory and no credentials in arguments/files. Restricted command-sandbox launches
then failed Chromium initialization (GPU child exit -1073741515); the authorized
outside-sandbox runs passed. No Windows security settings were changed.
One capture-step failure was not diagnosed before a subsequent successful run;
it remains a failed run, not erased or claimed resolved. Additional bounded error
diagnostics are now present. Failed records: electron-app-probe-a136*, d661*,
727729*, aca9*, and 3903*. The first four probes' TEST Cores were authenticatedly
shut down; 3903 also completed cooperative cleanup. Initial regression wrapper
commands had shell-quoting syntax errors before tests started; corrected wrappers
produced the explicit passing regression logs.

### Current blocker: two retained TEST Core processes

New real deadline/emergency probes each passed the preceding 21 checks, then failed
before entering the new scenario. A harness reattachment reused a revoked token,
so the Core correctly returned DENIED; the parent raised KeyError('token'). Its
old failure path exited without using its still-held controller credentials.
The credentials existed only in parent memory and were lost on parent exit.
This was a test harness error introduced during this work, not a production fault.

Preserved failed records:
- real-app-probe-4c386e29fc3c4bcc9ae513929b0cf04c.json
- real-app-probe-3722176cc9184c2a8b333f904fca0aab.json

Read-only identity verification confirms:
- Core **23524**, creation time **134335956497225784**, launcher **18604**,
  namespace **TEST-STAGE4-3b8aff3dd30249f680a43e05f8e781f8**.
- Core **28464**, creation time **134335956497223930**, launcher **25136**,
  namespace **TEST-STAGE4-464fe9b679cd4866b84bcc83c7c36cdc**.

Each isolated namespace recorded exactly one Core acquisition and still holds its
own lifetime lock. These are two disposable synthetic test cases, not additional
production JARVIS systems. Both actual command lines are fixtures.py --app-worker
for the recorded TEST roots; their live creation-time/executable identities were
checked. No production database, credentials or provider path was used.
The original inspection compared virtualenv launcher PIDs to metadata Core PIDs;
that mismatch and its correction are both retained in electron-retained-test-cores*.json.

Harness correction now sends null for every fresh attach and attempts one
authenticated cooperative cleanup while controller credentials are still available.
The source compiles, but new process probes are paused until retained processes
receive a reviewed disposition. No forced termination, lock-file deletion, ACL
change, credential bypass or replacement start was attempted.

The approved ownership/drain design section E states: "Separately authorized forced
termination is **not included** in Stage 4 implementation scope." Request narrowly
scoped permission to terminate only these two disposable TEST Core processes after
rechecking PID + creation time + executable digest + exact TEST command line, then
wait for their virtualenv launchers and verify lifetime-lock release. If a launcher
does not exit, include only its separately reverified recorded identity in cleanup.
Retain all TEST data/journals/evidence. Do not terminate any production process.

### Latest scoped code and remaining acceptance

Files changed in this continuation: desktop/main.cjs, desktop/preload.cjs,
intelligence/main.cjs, intelligence/index.html, intelligence/stage4-renderer.js,
intelligence/test/stage4-client.test.cjs, stage4_client.cjs, stage4_runtime.py,
stage4_lifecycle.py, tests/lifecycle_stage4/fixtures.py,
tests/lifecycle_stage4/test_stage4.py, this report and selected nonsecret evidence.
Existing unrelated working-tree changes were not reverted. static/app.js was
restored byte-for-byte after a discarded gated-wrapper experiment.

Drain-journal finalization and explicit owner re-evaluation have model coverage;
real deadline/emergency probes are NOT PASS and must be rerun after cleanup.
Further gates still include full worker/inspection/repair-cleanup and approval/
stream/upload coverage, complete process race/crash matrix, local lease watchdog/
media integration, native human emergency/shutdown controls and separately authorized
physical voice/media validation. Unsupported TEST routes remain denied, not certified.
Ordinary chat/TTS/inspection remain not universally budget-metered. Cancellation,
timeout or disappearance never proves zero consumption or authorizes refunds.

STAGE 4 ISOLATED IMPLEMENTATION: INCOMPLETE — REVIEW REQUIRED.
COMMIT: NONE; all-gates-pass commit condition not met.
Historical Stage 1 root cause remains UNCONFIRMED; experimental corrected mechanism
is separate evidence. Production activation remains blocked.
Production-used source files have explicit gated TEST changes; production running
Core/data/configuration/authentication were not changed or restarted.
STAGE 5 STARTED: NO. No installer, repair deployment, Ollama Phase 2 or autonomy.

## Real deadline/emergency lifecycle rerun — 2026-09-12

The previously failed TEST-only deadline and emergency scenarios were rerun with
the existing harness after the approved TEST cleanup. No production process,
database, configuration or authentication was touched. The deadline probe passed
36/36 checks and the emergency probe passed 32/32 checks; fresh evidence is:
`real-app-probe-ce5dc7e3358e4453881c7972b1292ef9.json` and
`real-app-probe-e45f9381acdb4f03985858d03b9c8cd4.json`. Both probes exited through
the authenticated TEST cleanup path. These passes supersede neither the retained
earlier failures nor the remaining Stage 4 gates (worker/inspection/repair
cleanup, approval/stream/upload, process race/crash breadth, lease watchdog,
media/physical voice and final manual review). No Stage 4 acceptance commit is
created and production activation remains blocked.


## Approved TEST cleanup and reattachment investigation — 2026-09-11

Cleanup PASS: PIDs 23524 and 28464 were matched against preserved TEST namespace,
creation time, executable digest and command line before termination through held
verified Windows process handles. Both exited; lifetime locks released; waiting
launchers exited without termination. Preserved incident/identity hashes remained
unchanged. See cleanup-approved-974ae7c5dffe42a09f9f922d6c38cbb0.json.

The Python TEST probe reused a revoked ordinary session token for a new attach.
A controlled stale-token attach reproduces denial; fresh attach without that token
reauthenticates to the same Core, cannot access the former session's request, and
leaves controller authority intact. The test controller now retains in-memory
credentials if authenticated failure cleanup cannot establish exit, accepting only
explicit STATUS/SHUTDOWN commands. No management credentials are persisted.
An injected failure confirmed authenticated cleanup succeeds. No speculative retry
or production authentication change was introduced.

Initial corrected real App probes: normal 29 PASS, emergency 32 PASS on two runs,
deadline 36 PASS on one run (30–32 second assertion; exact duration not recorded in
that run), and one expected failure-cleanup PASS. These are authenticated Python
clients using the actual synthetic TEST App, not a new Electron/manual-media PASS.

A repeated deadline run FAILED BEFORE its deadline scenario, during replacement
coordinator reconciliation: PermissionError [WinError 5] replacing challenge.json
from its temporary file. Probe 877484482a1d4083b6b1dbbaa11c5291 preserved the paths
and message but not a traceback or structured errno. Source path is harness.py
reconcile line 127 -> write lines 81–83. Stage4 control thread reads challenge.json
at stage4_runtime.py line 350. Reader contention is plausible, not proven.
The valid leftover temporary challenge differs from the target; response matches
the old challenge. No stale response was accepted as the new challenge.
Authenticated failure shutdown PASSED, launcher exited 0, one Core acquisition and
one drained event are recorded; actual Core PID 28844 is absent at follow-up.
These counts do not substitute for a complete external process-start trace.

This NEW challenge publication failure is distinct from the historical response
publication incident and its approved duplicate-response correction. Historical
root cause remains UNCONFIRMED. No Stage1 semantics were changed here.
Per the approved ownership/drain design: “Stop on meaningful PermissionError
recurrence; preserve every failure.” Further integration is paused for review.
Proposed next scope: isolated challenge-publication diagnostic with exact exception
and read/replace timing evidence; propose any Stage1 correction separately, without
retries, ACL changes, weakened freshness or replacement startup on uncertain identity.

Only fixtures.py source changed in this cleanup continuation, plus evidence/report.
Python AST validation PASS. Full regressions were not rerun after the new blocker;
previous regression results remain historical and do not erase this failure.
Stage4 acceptance INCOMPLETE. No acceptance commit. Production running Core, data,
configuration and authentication unchanged; no production restart/activation or
Stage5. Earlier gated production-used source changes remain uncommitted.


## Approved IPC guard correction checkpoint

See STAGE4-IPC-GUARD-VALIDATION.md for cleanup, exact guard, preserved failures,
final automated test results and rollback. Approved correction validation PASS;
overall Stage4 acceptance remains incomplete and production blocked. No commit.
