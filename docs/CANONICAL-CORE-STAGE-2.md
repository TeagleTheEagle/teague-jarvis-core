# Canonical Core Stage 2 — isolated authentication closure

Date: 2026-09-11. Status: PASS within the tested isolation boundary; stop for review.

**THIS IS AN ISOLATED TEST HARNESS.**

**PRODUCTION JARVIS AUTHENTICATION HAS NOT BEEN CHANGED.**

**PRODUCTION JARVIS CORE LIFECYCLE HAS NOT BEEN CHANGED.**

**STAGE 3 HAS NOT BEGUN.**

## Purpose and isolation

Prove that enrolled TEST clients authenticate the same Stage 1 lifetime-lock-owning fixture, without making authentication another startup mechanism. The fixture has no JARVIS App, Store, memory, personality, conversations, providers, voice, devices, budget ledger or repair controller. No production service is started or contacted. TEST directories are beneath `tests/lifecycle_stage1/evidence`; pipe names are strictly `TEAGUE-TEST-<32 hexadecimal characters>`. Generated test keys exist only in process memory and trusted test-parent IPC. Production code and existing dirty working-tree changes are excluded from this commit.

## Transport and trust model

Local Windows named pipes use CreateNamedPipeW with duplex, overlapped I/O, FILE_FLAG_FIRST_PIPE_INSTANCE and PIPE_REJECT_REMOTE_CLIENTS. An explicit protected DACL grants the current process user's SID access: `D:P(A;;GA;;;SID)`. Pipe handles and I/O event handles are non-inheritable. Clients use identification-level security QoS, not an impersonation grant. GetNamedPipeServerProcessId/GetNamedPipeClientProcessId supply peer PIDs, checked against OS creation time and executable SHA-256 via a process handle.

Messages are length-prefixed UTF-8 JSON objects, 1–8192 bytes. I/O waits are bounded to 1.2 seconds each and five seconds per accepted connection; connection retry is bounded to four seconds. The transport exposes no arbitrary shell, file or process operation. Current-user ACL inspection, explicit access-denied and namespace collision are exercised. Remote rejection is configured, but actual remote-host behavior is UNVERIFIED.

## Authentication sequence

1. A trusted test parent provisions expected bootstrap peer identity, expected Core identity, a random server proof key and separate enrolled-client keys through in-memory fixture setup. Descriptors never supply trust.
2. Client verifies the named-pipe peer's PID, creation time and executable digest before sending an unprivileged hello: client ID, fresh random nonce and protocol range.
3. Server checks enrollment and actual client executable digest, then signs a transcript containing both nonces, Core identity, client process identity and selected protocol using HMAC-SHA256.
4. Client verifies the server proof, echoed fresh nonce, exact expected identity, live Core process and compatible highest protocol. Only then does it send its client proof and request/session token.
5. Server verifies the client proof before issuing or using a session. Every operation checks live Core identity and stop intent. No authentication function starts a Core.

The proof is pinned-key authentication within a trusted test setup, not a production enrollment or signed-software solution. A Python interpreter digest does not authenticate user-writable Python source. The parent supplies the runtime digest; this is not runtime attestation. Same-user compromise, administrator access and process-memory inspection are outside the demonstrated protection.

## Identities, enrollment and credentials

Identity fields: installation_id, data_id, core_instance_id, startup_epoch, PID, OS creation time, executable digest, runtime_build, runtime_digest, mode=TEST, namespace, protocol range and schema. Installation/data identity are distinct from per-start identity. All expected fields must match. TEST-only checks reject production-mode expectations and claims; no production client is exercised.

In-memory enrollment records contain client ID, enabled state, separate random key, executable digest, protocol range and scopes. Fixtures represent Teague, Intelligence, media and lifecycle-controller clients; these are test labels, not launched applications. A claimed client name or matching process alone is insufficient.

Scopes are attach/status/test/media/lifecycle. Ordinary clients cannot request media or lifecycle privileges. Lifecycle operations return permission-model results only, always `lifecycle_executed=false`; authentication never grants JARVIS tool authority. There is no discovery-to-start fallback or override of persistent stop intent.

Sessions are random 256-bit values; only SHA-256 lookup hashes are kept in the authority's in-memory map. Records bind client, complete Core identity/epoch, selected protocol, scopes and monotonic expiry. Test TTL is configurable (one second by default), with a 128-session ceiling. Renewal requires a still-valid session and fresh authenticated exchange, invalidates the old session and issues a new one. Own-session revocation and controller enrollment revocation are deterministic; revoked clients cannot attach or renew. Bootstrap restart clears sessions. Core death denies use, and replacement Core plus bootstrap requires fresh authentication. Expired entries are not proactively swept; long-running lifecycle/DoS hardening remains future work.

## Evidence matrix

Numbers below refer to `test_NN` in the committed Stage 2 suite. PASS means only the described exercised behavior, not a broader security certification.

| Requirement | Exercised evidence / scope |
|---|---|
| Approved attachment, unapproved rejection | 01, 22: enrolled clients attach/status; unknown clients denied; actual multiple processes share identity |
| Core/install/data/epoch/runtime/schema identity | 02, 14: altered expected fields rejected; OS creation identity checked. Actual forced PID recycling is not exercised |
| Production/test separation | 03: TEST client model rejects mismatching production expectations/claims; no production binary involved |
| Scopes and no tool authority | 04, 18: ordinary client denied expanded scopes and six privileged operations; controller/media model scoped; no execution |
| Expiry, renewal, own revocation | 05–07: expired status/renew denied; valid renewal invalidates old token; revoked/random/malformed/wrong-client values denied |
| Enrollment revocation | 08, 31, 34: revoked client, wrong executable enrollment, and another client's proof key denied |
| Instance/epoch/restart binding | 09–11: Core death denies old use; Core/bootstrap replacement and different namespace deny old sessions |
| Protocol | 12–13: highest compatible selection, malformed/no-overlap/range mismatch rejection, tampered downgrade rejection |
| Wrong listener and freshness | 13–14: invalid proof, modified nonce, tampered protocol, fake health/application identity and wrong pinned process/key denied. Replay is a modified-nonce fixture, not a captured full-traffic replay campaign |
| No early reusable credential disclosure | 35: fake-proof listener sees only hello field names; existing token and client proof are not sent |
| Origin / redirect protection | 15: parsed-origin pure-function tests reject host/prefix/port/userinfo/scheme confusion and unexpected redirect target. No HTTP client/server or redirect-following transport tested |
| Descriptor non-authority | 16, 28: atomic Stage 1 writer, truncated/modified/copied hint cases; descriptors exclude generated secrets and cannot supply proof key. No filesystem credential discovery is implemented |
| Bounded/malformed input | 17–18, 33: empty/oversized/invalid encoding/truncated frames, unexpected fields/operations, stalled partial input; subsequent valid attachment succeeds. Not exhaustive fuzzing or sustained DoS testing |
| Crash-safe handshake | 19–20, 29: server exits 81; client disconnects or exits 82 before proof; denial/cleanup and later client recovery |
| Concurrent attachment | 21–22: three rounds of four threads and two rounds of two client processes |
| Stage 1 composition | 23: three rounds of four replacement coordinators adopt surviving fixture without spawning; clients attach same epoch. 32: three fresh namespace races of four coordinators produce exactly one acquisition/spawn and both clients attach |
| Authentication cannot start / stop intent | Static review: bootstrap/transport have no Core-start API. 24 denies new and existing sessions after stop latch and preserves file. Stage 1 regression independently exercises coordinator death/recovery |
| Handles / child credentials | 30: child stays alive after parent pipe closes while a new first-instance pipe succeeds; 36: explicitly unprivileged child has only allowed environment names. Approved authentication children intentionally receive TEST keys via trusted in-memory setup; this is not a general no-child-secrets claim |
| ACL / remote namespace | 25–26: current SID ACL, no Everyone/Anonymous ACE, collision denied, explicit deny ACL produces error 5, remote endpoint strings refused locally |
| Other users / sessions / remote hosts | 27 skipped. ALL THREE UNVERIFIED |

The combined evidence supports Stage 1 ownership remaining independent of Stage 2 attachment. The Stage 1 source diff is empty. Stage 2's bootstrap process is a test authority beside a dummy locked fixture, not an integrated production supervisor. Stage 1 crash/replacement and Stage 2 surviving-Core adoption are composed evidence, not a claim that every crash boundary was re-exercised with an active authenticated session.

## Development failures retained

See `lifecycle-stage2-evidence/development-failures.json` and separate raw development JSON files. None is silently replaced by final evidence.

- Test-runner naming collision: a class path named `run` shadowed unittest's callable; failed before evidence output. Renamed `run_folder`. No original machine-readable run exists; retained as a retrospective narrative, not fabricated raw evidence.
- Path-reference issue: expanded test 32 retained an old `self.run` reference; 34 tests, one error, one skip. Corrected reference to `run_folder`.
- Environment/helper-import issue: an unnecessary unittest.mock import loaded asyncio/Windows overlapped infrastructure while environment pruning had removed SystemRoot because Windows normalizes key case. The mixed-revision development run recorded ten failures. Corrected whitelist comparison using uppercase names, removed the unnecessary import in favor of a narrowly restored test spy, and registered cleanup before setup completion.
- These are TEST INFRASTRUCTURE FAILURES. No protocol/security failure was established by these traces. Failed or mixed-revision runs are not acceptance evidence. This classification does not imply exhaustive absence of security defects.

## Final validation and acceptance

Commands run from the authoritative repository root:

```powershell
& .\.venv\Scripts\python.exe -I tests/lifecycle_stage2/test_stage2.py
& .\.venv\Scripts\python.exe -I tests/lifecycle_stage1/test_stage1.py
& .\.venv\Scripts\python.exe -I -c "import ast,pathlib,py_compile,json; roots=[pathlib.Path('tests/lifecycle_stage1'),pathlib.Path('tests/lifecycle_stage2')]; files=[p for r in roots for p in r.glob('*.py')]; result=[]; [py_compile.compile(str(p),doraise=True) for p in files]; imports={str(p):sorted({n.names[0].name if isinstance(n,ast.Import) else n.module or '' for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,(ast.Import,ast.ImportFrom))}) for p in files}; print(json.dumps({'compiled':len(files),'imports':imports},indent=2))"
git diff -- tests/lifecycle_stage1
git diff --check
git diff --cached --check
```

Final Stage 2: 36 discovered, 35 passed, one skipped, zero errors/failures, 66.052 seconds. Prior unchanged candidate run also passed 35/36 with one skip (68.528 seconds). Final Stage 1 result and exact validation outcomes are in `lifecycle-stage2-evidence/closure.json`. Five Python files compiled and parsed successfully; import review finds standard-library dependencies plus local test harness modules, no production imports. No production regression suite was run in this closure. Existing unrelated working-tree modifications are neither certified nor included.

Final Stage 1 rerun: 20 discovered, 19 passed, one skipped, zero errors/failures, 28.723 seconds, exit 0. Both suite commands exited 0. Python compilation/static command exited 0. Stage 1 source diff was empty. Working-tree whitespace check passed with Git line-ending notices on pre-existing unrelated files. Staged whitespace check initially found a trailing blank line in bootstrap.py; this and trailing test-file blank lines were normalized without changing semantics. Five files were compiled again after normalization; staged whitespace check then exited 0. No additional behavioral test was needed for EOF whitespace alone. Evidence JSON parsing and a recursive forbidden-secret-field-name check passed; this bounded check is not a claim of exhaustive secret detection. Evidence writers were also reviewed to ensure they export identities, timings, case results and exception classes rather than credentials or request bodies.

Closure changes: the three Stage 2 Python files, its local .gitignore, this report and eight JSON evidence/closure records. The implementation logic was not changed during closure. The record mirror is a scoped copy of these files only; the broad Sync-TeagueIndustries.ps1 was intentionally not run because it would also copy unrelated working-tree work outside this closure's scope.

## Risks and Stage 3 gate

Other-Windows-user, cross-session/fast-user-switching and actual remote-host rejection remain UNVERIFIED production gates. Same-user software trust, protected key provisioning/storage, authenticated supervisor-to-Core binding, production discovery, signed build identity, permission upgrades, race/TOCTOU threat review and wider protocol fuzzing require design/review before production adoption. The model does not implement an encrypted transport or formal transcript security proof. Its finite connection/session limits are not demonstrated sustained-load protection.

Stage 0 architecture: PASS (approved direction). Stage 1 ownership/exclusion: PASS in its recorded test scope. Stage 2 isolated authentication: PASS in the matrix above, with explicit unverified gates. This does not authorize production use.

**Exact next gate:** user review of this report, failed and passing evidence, limitations and discrete Stage 2 commit, followed by separate explicit authorization for Stage 3 data/migration rehearsal. No migration, production authentication/lifecycle change, installer, device expansion, Ollama Phase 2, suite conversion or additional autonomy is included. STOP.
