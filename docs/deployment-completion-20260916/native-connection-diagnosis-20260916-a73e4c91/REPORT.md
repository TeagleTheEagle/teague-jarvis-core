# JARVIS Stage 4 — native readiness correction; stopped restart validation

**Stage 4 INCOMPLETE.** The native expected-success case and all 15 native cases passed after a TEST-harness correction; 56 focused unit/client tests also passed. The required restart/lifecycle campaign then encountered a new coordinator readiness-file `PermissionError`. Validation stopped. No full acceptance rerun, acceptance commit, production operation or Stage 5 work followed.

## Root cause and rejection condition

The confirmed experimental mechanism is **premature closure of a one-shot TEST pipe while its Electron client has not yet connected**. This is classified **B. Test harness defect**. The original native fixture starts the server's 1,200ms connect wait before launching Electron. Its subprocess budget is 12 seconds, so the child is allowed to still be starting after the pipe's connection window has expired.

Call path: existing Electron TEST driver → `client.loadBridge` → native `connectTestPipe` → TEST endpoint validation → `CreateFileW(OPEN_EXISTING)` → `win(...,"PIPE_CONNECT")` → `GetLastError()` appended to the exception. In unchanged `stage4_native/peer_identity.cc:142-143`, `PIPE_CONNECT:2` is **Windows error 2, ERROR_FILE_NOT_FOUND**, not an internal state, wrapper exit or peer mismatch. Verified from installed SDK `C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/shared/winerror.h:252`. The native PID/creation/executable comparison is later at line 145 and is never reached on this error.

The original full-run report saved only exception class `Rejected`. The new controlled trace preserves `pipe_transport.py:99`: `Rejected('IO_TIMEOUT')` raised from the pending `connect` operation; the probe's finally block closes the only pipe instance. It then releases the client configuration and receives the exact same `PIPE_CONNECT:2`, zero-frame outcome.

- EXPECTED: `WaitForSingleObject(ov.event, timeout) == 0`, signalling connection within the existing operation window.
- ACTUAL in the controlled trace: the branch `WaitForSingleObject(...) != 0` was taken; connect ended after **1208.2805ms**, with `Rejected('IO_TIMEOUT')`, followed by pipe closure.
- The raw Windows wait return DWORD was not separately recorded; do not claim a specific DWORD was captured. The exact Python exception reason and branch are captured.
- Expected peer: the server's actual PID, creation time and executable digest supplied in the same TEST configuration. The observed server identity matches that pin. There is **no observed identity mismatch**; actual peer validation is **NOT REACHED** on `PIPE_CONNECT:2`.

The ordinary instrumented run passed, connecting in **263.7244ms**. The failing comparison withheld stdin configuration until the *unchanged server closed*, using a threading event rather than a sleep. It is an explicit slow-client ordering experiment, **not a naturally occurring failure**. It proves this source mechanism produces the reported error but does not recover the original failure's missing timing/server-reason evidence. The initial ordinary observation also hashed Electron before launch, potentially warming the executable cache. This limitation is retained. Historical Stage 1 and earlier native incident timing remain unconfirmed where no original telemetry exists.

Evidence: `original-single-33c9ce367c99400da62879b51ba6bf94/trace.json` and `controlled-slow-client-4711fee560d84d078d7dbb7cd1df8a6f/trace.json`. Both include launch command, executable hash, child/server creation identity, owner SID/session, endpoint, expected pin, whitelisted environment, timestamps, stdout/stderr and exit status. The AST-selected fixture frame uses a diagnostic source mapping; use the preserved original fixture snapshot and unchanged `pipe_transport.py:99` for exact source attribution. No runtime source was edited during diagnosis.

## Difference table: native probe versus passing restart/lifecycle path

| Dimension | Native expected-success probe | Restart/lifecycle reference | Relevance |
|---|---|---|---|
| Endpoint/namespace | Fresh `TEAGUE-TEST-<uuid>`; `\\.\pipe\` resolution | Same namespace validator and resolution | IRRELEVANT to demonstrated mechanism |
| Creation/permissions | `pipe_transport.listen`, protected current-SID DACL, no inherited handle, local pipe | Same transport creation/security helper | IRRELEVANT; unchanged in experiment |
| Caller startup | New Electron-as-Node process starts after accept wait begins | Already-running Python controller waits for published/validated coordinator readiness before authenticated attach | RELEVANT |
| Readiness | No client readiness barrier; one-shot listener | Explicit coordinator readiness file/live identity before attach | RELEVANT |
| Connection budget | 1,200ms operation window competes with up-to-12s child startup | Python client already executing; connection path has bounded handling of initial absent/busy pipe | RELEVANT structural difference; no Core retry change proposed |
| PID/creation/hash | Exact native server pin; fresh Electron caller | Exact coordinator/Core pin; controller bound to its live identity | IRRELEVANT to pre-validation missing-pipe failure; checks preserved |
| Owner/session | Observed server and Electron have the same owner SID and Windows session 1 | TEST children launched under the controller's normal host context; actual cross-user tokens not measured in this comparison | UNCONFIRMED as a cross-path token comparison; no mismatch observed in native experiment |
| Executable/arguments/ancestry | Direct Electron TEST script child, `--native-case`, `ELECTRON_RUN_AS_NODE=1` | Python isolated TEST coordinator/Core children and existing controller | RELEVANT to startup workload; exact source of slow historical startup UNCONFIRMED |
| Quoting/escaping/cwd | Argument list, no shell interpolation; JARVIS repository cwd | Argument lists; repository fixture context | IRRELEVANT to demonstrated fixed-config ordering |
| Environment | Recorded allowlisted Windows paths plus Electron-as-Node | Isolated TEST child environment; no real provider configuration | UNCONFIRMED as a startup-latency contributor |
| Authentication payload | Synthetic hello only after native peer gate; no reusable auth material | Stage 2 authenticated client envelope after pin/identity checks | IRRELEVANT to failure before pipe open; never weakened |
| Cleanup | One-shot listener closes on timeout | Approved authenticated lifecycle/cleanup, retained authority on uncertainty | RELEVANT to why the missing-pipe error is terminal in this probe |

No ACL changes, username/PID/path hardcoding, key rotation, runtime authentication changes or security bypasses were made. Windows elevation/integrity level, antivirus effects, scheduler load and the original startup's exact delay were not measured and are not assigned as causes.

## Correction

Only TEST code changed:

1. `tests/lifecycle_stage4/fixtures.py`: bounded `_run_native_case` waits for a TEST readiness line before starting the server thread and sending configuration; starts that pipe's existing five-second lifetime at handoff; retains the existing 1,200ms I/O and overall 12-second child budget; records native child identity, stdout/stderr, timing and full server reason; prints PASS only after evaluating results. On helper errors, only the reverified owned TEST child can be terminated. Unknown identity is retained for review.
2. `desktop/test/stage4-client.test.cjs`: emits `STAGE4_NATIVE_READY` only under `--native-ready`, after existing modules and stdin handlers are ready. This is a driver signal, **not authentication or authority**. Normal test/bootstrap paths are unchanged without the flag.
3. `tests/lifecycle_stage4/test_native_readiness.py`: nine focused tests of handoff ordering, malformed/empty readiness, deadline rejection, unchanged configuration/results, negative peer outcomes and identity-checked cleanup.

Native bridge, Core, coordinator, Store, provider routing, production UI/configuration and peer-check semantics were not changed. No arbitrary sleep or retry was introduced. The idle identity targets in the native suite remain disposable Python sleep processes, not JARVIS Cores.

| File | Before SHA-256 | After SHA-256 |
|---|---|---|
| `tests/lifecycle_stage4/fixtures.py` | `792d96f09da1b37301d217f817ec1500bfc7821392e5b89a64213242d818d68a` | `5965f308384764d79e2e677a4a0cd6ad5ae6643c1be3dc147cb6e9d64ae4a285` |
| `desktop/test/stage4-client.test.cjs` | `f7ead69d6078060a78d4031cf007d1aae4e169406d35f9a3becb54813a73017d` | `8a975f69fd45a434a7553a3fbbfccea26be6087090041728ec4a9edb2564a838` |
| `tests/lifecycle_stage4/test_native_readiness.py` | `NEW` | `a34c654d4ad28729caa53bba355e3cd4a177db6f0e7cd57b9abeef3c9e145834` |

`correction.patch` and before/after snapshots preserve exact rollback. No rollback has been applied: this TEST candidate remains unaccepted while the next blocker is reviewed.

## Exact validation results

All commands ran from `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis` through `run_gate.py`; exact argument arrays, timestamps, PIDs, exit statuses and log hashes are in `targeted-command.json` and `restart-command.json`.

| Targeted group | Result |
|---|---|
| Corrected expected-success case | 1 / 1 PASS |
| Complete native suite | 15 / 15 PASS, 0 failed |
| Native readiness unit tests | 9 / 9 PASS |
| Coordinator readiness tests | 25 / 25 PASS |
| Desktop/Intelligence peer-client tests | 22 / 22 PASS |

Focused unit/client total: **56 executed, 56 passed, 0 failed, 0 errors, 0 skips**. Separately: **16 actual native case executions passed**, including the single-case rerun plus 15-case suite. All five targeted command groups passed. Explicit simulated negative unit-test evidence is preserved in `unit-negative-evidence/`; those expected outcomes are not unexpected regression failures.

### Restart/lifecycle — FAIL; stopped

Command: `.\.venv\Scripts\python.exe -B tests\lifecycle_stage4\fixtures.py --restart-campaign`.

**104 records: 102 passed, 2 failed records describing ONE underlying exception.** The required 636-check baseline was not reached. During startup contenders, the first strict UTF-8 read/open of:

`C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\tests\lifecycle_stage1\evidence\TEST-STAGE4-f44b3e90d8f04881a4a5d0ff69ec91bc\coordinator-f72ed905810c47ec982b8d173327263b.json`

raised **PermissionError, errno 13, winerror not available** at the current `fixtures.py:1134`, `content=path.read_text(encoding='utf8')`. The traceback identifies `pathlib.open` → `io.open`. It does not establish the Windows sharing/ACL/security cause. Read attempts: **1**; existence-wait polls: **6**; recorded elapsed: **0.125s**.

Coordinator PID **3020**, creation **134340091569635874**, executable SHA-256 **372c2eae555b344520bf147be0096e009069aeca4e7f78d6aecea6d53158056a**. This finding is distinct from the native connection timeout. The reviewed readiness code was not edited by this correction, and the old 636/636 success remains preserved rather than being erased.

The cleanup-only path subsequently authenticated and recorded `AUTHENTICATED_CLOSE_SUCCEEDED` / exit 0 for this coordinator. This does not turn the failed startup into a pass. All other recorded TEST cleanup completed. A read-only post-run OS census found **34/34 recorded identities absent**; no extra termination was performed. The corrected native reports now include real Electron child identities; a legacy generic limitation string in the reused census helper is superseded by those actual records. Separate native idle targets were terminated/waited by their existing fixture path; their creation records are not separately persisted.

Evidence: `restart-gate-b91a932d56fe4336b6c46b36bc89365b.log` and `raw-evidence/restart-gate-restart-campaign-701357f9e8da49349906b0131021128a.json`. No retry, extra regression or correction followed this new failure.

### Full acceptance / cancellation / deferrals

- Full 33-group campaign THIS TURN: **33 planned, 0 executed, 0 passed, 0 failed, 33 not run** because the prerequisite restart gate failed. The previous campaign's 13 passed / 1 failed / 19 unrun groups are historical results, not new execution.
- Cancellation regression: **NOT RERUN**. Prior **306 trials / 4,748 assertions / direct SQLite PASS** retained in the previous hash-verified marker evidence. Its runtime source is unchanged. No fresh success is claimed.
- Approvals: **DEFERRED** — workflow not present in current Stage 4 TEST product surface.
- Uploads: **DEFERRED** — separate authority/persistence review required.
- Physical media: **DEFERRED**.
- Existing cross-session skips and restricted-context Electron GPU limitation remain disclosed, not newly validated; exact missing/inaccessible DLL remains unconfirmed.

## Integrity / archive / preservation

`collection.json` reconciles **103 final source entries** against their post-targeted snapshots, with no subsequent drift; all **796 unchanged candidate payload hashes** match manifest `fcbd0381f3b4d2b0acd89c15e373418dc27172a60456e3e1698a1963fec091e3`. The older 101-entry list omitted the desktop TEST driver; its separately preserved before/after snapshots supply that hash and are included in the final reconciliation. An initial collection assertion exposed this list-coverage mismatch; `collection-error.json` preserves it. This was a collection error, not a test rerun or source failure.

All **54 files/receipt from the previous marker-validation archive remain unchanged**. Current diagnostic failures, successful runs, logs, source snapshots and new failure evidence are retained. No credentials, database or private runtime configs are selected for archive. An explicit narrow archive is used instead of broad Sync-TeagueIndustries to honor the evidence-only scope. See `SHA256.json` and `archive-verification.json` for exact files, destination and comparison results.

## Review / rollback / final status

Review the new coordinator `read_text` PermissionError before any further validation or correction. Its low-level cause remains UNCONFIRMED. This report does not request or imply a retry, security change or weakening of the strict read/identity contract.

Rollback requires reviewing `correction.patch`, comparing current hashes and restoring only the two changed TEST files from `before/`; the new unit test may be removed only as part of a reviewed rollback. Do not reset the dirty repository or touch production/package state. Keep all evidence. Production requires no rollback because it was untouched.

- Cleanup: **PASS for recorded TEST identities**.
- Production touched: **NO**. Activated: **NO**. Paid calls: **0**.
- Acceptance commit created: **NO**. Hash: **None**. Existing HEAD: `8f0b9bce181800f9339249c4024e396246e94208`; index remains empty.
- Stage 4: **INCOMPLETE**.
- Stage 5: **NOT STARTED**; no readiness proposal because Stage 4 did not pass.

**STOP FOR REVIEW — new coordinator readiness-file PermissionError.**
