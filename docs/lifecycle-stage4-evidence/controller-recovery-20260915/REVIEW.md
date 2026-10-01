# Stage 4 TEST controller reauthentication and lifecycle recovery

2026-09-15 — **Approved narrow correction: PASS, STOP FOR REVIEW.** Overall Stage 4 remains incomplete. Production activation and Stage 5 remain blocked. No acceptance commit was created.

## Problem and exact correction

An expired TEST controller previously had only STATUS and SHUTDOWN commands, both using the expired session. Fresh ordinary attachment was also unavailable after emergency suspension. The approved correction provides explicit fresh authentication without restoring expired request authority.

Four source files changed:

| File | Change |
|---|---|
| `stage4_sessions.py` | New restricted recovery session with a fresh ownership family. Existing session lifetime, enrollment revocation, protocol checks and ordinary admission remain enforced. |
| `stage4_runtime.py` | Authenticated `recovery-attach` operation and a recovery-session operation allowlist. Parent-only TEST clock injection for the actual-runtime expiry fixture. |
| `tests/lifecycle_stage4/fixtures.py` | Explicit retained-controller REAUTH/RECOVER commands, same-Core identity validation, and authenticated actual-App expiry scenario. |
| `tests/lifecycle_stage4/test_stage4.py` | 52 focused recovery/expiry/authority checks. |

`correction.diff`, `before/`, `current/` and the source manifest describe the exact delta independently of the repository's many unrelated existing changes.

### Explicit operator actions

- **REAUTH:** performs one existing fresh authenticated attachment while RUNNING, using the retained in-memory enrollment and pinned Core peer/identity. It replaces the saved session only after the returned identity and epoch match. It does not retry, renew an expired token, replay work or inherit the old ownership family.
- **RECOVER:** performs a distinct freshly authenticated attachment for an already enrolled lifecycle controller in SUSPENDED, DRAINING, CANCELLING or RECOVERY_REQUIRED. Core-fixed scopes are `attach` and `lifecycle`; the dispatcher permits only lifecycle status, separately requested shutdown and detach. It has no chat, repair, media, history, inspection, emergency-stop or prior-request authority.
- **STATUS / SHUTDOWN:** remain separate actions. Attachment itself never terminates anything. Existing lifecycle rules still refuse unresolved UNKNOWN outcomes and prevent restarting an active drain deadline.

Ordinary clients and emergency-only enrollments cannot obtain recovery authority. Recovery attachment is refused in RUNNING and FINALIZING. Recovery sessions cannot be renewed into ordinary sessions. Expired/revoked tokens remain invalid. Credentials remain in trusted TEST process memory and are not printed, persisted or exposed to a renderer.

Every actual pipe operation continues through the unchanged Stage 2 named-pipe peer/process identity and authenticated transcript checks before the post-authentication dispatcher. Returned identity comparison is an additional check, not a substitute for OS peer verification. No authentication algorithm, lifetime lock, Stage 1–3 semantics, shutdown policy, database schema or provider routing changed.

## Validation performed in this checkpoint

| Validation | Result |
|---|---:|
| Focused controller recovery, actual post-auth dispatcher, injected clock, no Core/App/Store | 52 passed |
| Real isolated App/Core, authenticated TEST pipe, expiry → REAUTH → emergency → expiry → RECOVER → explicit shutdown | 45 passed |
| Existing ownership/lifecycle model | 27 passed |
| Existing synthetic repair worker/accounting tests | 22 passed |
| Existing inspection worker tests | 13 passed |
| Real isolated synthetic repair emergency regression | 45 passed |
| Real isolated shutdown deadline regression | 36 passed |
| Actual Electron v44.2.0, both authenticated TEST interfaces, close/reopen/crash/lifecycle | 29 passed |
| Native peer identity / bootstrap | 15 / 6 passed |
| Unchanged Stage 1 | 23 passed, 1 existing skip (24 discovered) |
| Unchanged Stage 2 | 35 passed, 1 existing skip (36 discovered) |
| Unchanged Stage 3 | 43 passed |
| Existing Python suite | 212 passed |
| Existing desktop JavaScript suite | 29 passed |
| Offline provider/router suite | 62 passed |
| Python compilation | All 4 changed Python files passed |
| Protected source hashes / permanent audit-guard AST | 22 unchanged / unchanged |

`result-index.json` links the original machine-readable results. The checkpoint logs retain test command output. Selected original event/journal JSON and two Electron screenshots are copied under `results/`; synthetic databases, TEST credentials and Electron profiles are excluded.

Actual-runtime results:

- Expiry: `real-app-probe-34049809379e42c8ae55903a0363fd22.json`, 45 checks, Core exit 0.
- Repair emergency: `real-app-probe-711ed793ec2349aca525352f9ebeeb98.json`, 45 checks, Core exit 0.
- Deadline: `real-app-probe-0d6374a307bd449592a4b184a3584d55.json`, 36 checks, Core exit 0. Recovery occurred after **30.047 seconds**; lifetime ownership remained held during quarantine, late completion did not automatically resume/exit, and a separate authorized shutdown subsequently completed.
- Electron: `electron-app-probe-ba76c336d41c454ba35934626c336b80.json`, 29 checks. Both interfaces used the same TEST Core; all five client launches and the Core exited normally. Screenshots were visually inspected and clearly label STAGE4_TEST authentication and unavailable physical voice/capture.

No forced cleanup was required in this checkpoint. The correction attaches to the surviving TEST Core rather than spawning a replacement. Each actual-App scenario used its own disposable synthetic namespace and exited before the next actual-App scenario. Production was not attached to, stopped or restarted.

## Failed development evidence retained

The first focused run ended after 42 successful assertions because the test helper caught `stage4_sessions.Denied` but not the existing separate Stage 2 `authentication.Denied` exception. The deliberately invalid recovery fields were correctly rejected with UNKNOWN_FIELDS; the test helper failed to recognize that expected rejection. Only the test catch was corrected. `focused-01.log`, `failed-focused-01.py.txt` and `controller-recovery-7bc293c4dff7403992b1ba695f6629ff.json` preserve it. Its partial JSON is **not** an overall PASS. The subsequent 52-check run passed.

The first evidence inventory also assumed every existing JSON result had an object root; two native probes use arrays. The inventory failed with AttributeError and was corrected to accept the existing array format. This documentation-only issue and its impact are retained in `packaging-note.json`; no runtime or test result changed.

The September 13 long-interruption broken-pipe/emergency failure remains preserved. Controlled expiry now reproduces and validates the corrected recovery behavior, but it does not establish the cause of that earlier multi-hour interruption or rewrite that failed run as passed.

## Evidence limits and remaining gates

- Expiry is exercised through the real authenticated TEST pipe using two trusted parent-only clock steps of 901 seconds. This is not a 15-minute idle/sleep/resume endurance test. No remote operation can change that clock, and ordinary TEST session lifetime remains at most 900 seconds.
- The 52 focused checks use the actual post-authentication dispatcher, not a native handshake. The separate actual-runtime and unchanged Stage 2 tests supply authenticated IPC coverage.
- Recovery is deliberately not a way to terminate unresolved work. UNKNOWN still blocks shutdown and retains ownership. If a future retained process cannot establish safe shutdown, additional identity-verified cleanup authorization may still be needed.
- Actual Electron screenshots are inspected automated evidence, not a user-performed manual acceptance or physical voice test. No microphone, screen capture, real repair execution, Podman, Ollama or paid OpenAI generation was used for this correction. Existing desktop regression capture uses its isolated test fixture.
- Resource accounting remains the existing repair attempt units, not universal monetary/token enforcement. Chat/TTS/inspection remain unmetered by that ledger; cancellation or disappearance never proves zero consumption.
- The Stage 1 cross-session skip and Stage 2 other-user/cross-session/actual-remote-host skip remain unchanged. Historical Stage 1 PermissionError remains **ROOT CAUSE UNCONFIRMED / FAIL-SAFE / REVIEW REQUIRED**. The later response-publication correction, IPC guard finding, Windows application crash and long-interruption pipe failure remain distinct findings.
- This closes only the approved controller-expiry/recovery correction for review. The broader Stage 4 approvals/stream/upload cleanup, lifecycle/race and separately authorized manual/media acceptance matrix still requires closure. No claim of overall Stage 4 acceptance or production readiness is made.

## Rollback

After confirming no subsequent edits, reverse only `correction.diff` or restore its four exact `before/` files. Preserve this report, current snapshots and all passed/failed evidence. Do not reset the working tree, change Stage 1–3, restore production data, alter credentials or restart production. Rollback removes the new TEST recovery operation and driver commands; it intentionally returns the previous expired-controller limitation. No persisted session/schema migration needs reversal.

PRODUCTION DATABASE MODIFIED: NO  
PRODUCTION CORE RESTARTED: NO  
PRODUCTION CONFIGURATION CHANGED: NO  
PRODUCTION ACTIVATED: NO  
PAID PROVIDER CALLS: NO  
STAGE 5 STARTED: NO  
ACCEPTANCE COMMIT: NONE

**STOP FOR REVIEW.**
