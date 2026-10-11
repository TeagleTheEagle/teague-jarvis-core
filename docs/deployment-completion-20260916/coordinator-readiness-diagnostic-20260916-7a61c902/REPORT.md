# Stage 4 coordinator readiness diagnostic — STOP FOR REVIEW

16 September 2026. Diagnosis only; no correction implemented. Stage 4 acceptance remains **INCOMPLETE**. The blank-UI candidate and shared response-commit implementation remain unchanged.

The strongest supported classification is **G — multiple interacting harness failures: E, acceptance harness defect; F, cleanup harness defect**. The event that originally made the readiness read return `None` remains **UNCONFIRMED / NOT RECOVERABLE FROM THE AVAILABLE RECORDS**. Eight minimal observed readiness attempts succeeded; they do not resolve or erase the original failure.

## Coordinator readiness

- **Expected result:** a JSON object containing `identity`, `peer` and `endpoint`, describing the just-created TEST coordinator. `peer` includes PID, Windows creation FILETIME and executable SHA-256. A valid file alone does not authorize a client; live identity and the authenticated pipe protocol must still pass.
- **Actual result:** `None`, then `TypeError: 'NoneType' object is not subscriptable`.
- **Calling function:** `RestartCampaign.coordinator()` in `tests/lifecycle_stage4/fixtures.py:1007`.
- **Read function:** `stage4_runtime.exclusion.read`, imported from `tests/lifecycle_stage1/harness.py:146–149`.
- **Why None occurred:** this helper deliberately returns a failure sentinel after an `OSError` or `ValueError`, including file-read, decoding or JSON-parse errors. It can also return None if the file successfully parses as JSON `null`. The expected publisher emits a dictionary, and the later recovered file is a valid dictionary; there is no evidence that `null` was published. No captured exception or bytes from the failing read distinguish these possibilities. It is not an unhandled fall-through or a timeout return.
- **Original underlying error:** exception class, errno, WinError and original read/parse traceback were **NOT RECORDED**. A file-read/parse failure is the leading category, not an established exact operation or Windows mechanism.
- **First meaningful recorded failure:** the secondary None dereference at `fixtures.py:1022`. The antecedent failure represented by None was not preserved.

Exact consumer chain:

```text
fixtures.py:1546 --restart-campaign
  RestartCampaign.run('full') :1254
    full() :1246
      fault_case('before-intent') :1190–1192
        start old TEST Core; authenticated stop; close old coordinator
        coordinator(root, fresh_config, 'before-intent') :1007
          Popen original --restart-coordinator-worker :1012
          private configuration sent on stdin :1014
          retain process/configuration with token=None :1015
          wait for readiness path.exists() :1016–1020
          exclusion.read(path) :1021
            json.loads(path.read_text(encoding='utf8'))
            except (OSError, ValueError): return None
          live process identity query, then item['ready']['peer'] :1022
          authenticated attach :1023 — NOT REACHED
        issue restart grant :1192 — NOT REACHED
```

The first interruption case is supported by the full-loop order and the seven preserved namespaces: smoke, authorization checks, four contender rounds, then this failed namespace. No interruption checkpoint was reached in this case.

Exact publisher chain:

```text
fixtures.restart_coordinator_worker() :968–976
  stage4_runtime.serve_test_coordinator() :1089
    TestRestartCoordinator constructs TEST identity
    verifies the controller's live PID/creation time/executable identity :1091
    transport.listen(endpoint) :1095
      CreateNamedPipeW with restricted same-user ACL :pipe_transport.py:125–132
    first iteration only: exclusion.write(readiness_path, dictionary) :1098
      UUID temporary file write_text; os.replace(temp, destination)
    first=False :1099
    connect/authenticated protocol :1100–1102
```

The named pipe is created **before** readiness publication. `ConnectNamedPipe` follows publication; the transport explicitly handles a client already connected. The coordinator readiness filename is unique per launch. It is published once after successful publication, unlike the historical repeated response-publication scenario. The existing challenge/response guard intentionally does not apply to `coordinator-<uuid>.json`.

**Timeouts/retries:** the harness's eight-second deadline only covers waiting for file existence. Once a file exists, it reads exactly once; the result is neither retried nor checked. `read()` does not turn deadline expiry into None. Named-pipe connection, proof validation and their timeouts are downstream and were not reached. The coordinator has its existing 120-second service deadline and bounded pipe I/O waits; these are unrelated to the eight-second existence wait.

### Evidence for and against proposed triggers

| Candidate trigger | Evidence-based finding |
|---|---|
| File-access, UTF-8 decode or JSON parse failure | Can yield this exact sentinel; the original exception is lost. Cannot distinguish access denied, sharing violation, missing path or malformed bytes. |
| Connection refused, closed socket/pipe, authentication denial, stale endpoint or port collision | Not shown as the consumer failure: the code had not called the pipe client. This path uses named pipes, not a TCP port. Creation of the pipe precedes publication in the writer. |
| Coordinator already exited or live process identity unavailable | The expression at line 1022 evaluates `transport.identity(proc.pid)` before indexing the None result. It did not raise there. A later read-only live observation also matched PID 9400; later absence is separate. No successful comparison to the missing readiness peer was possible. |
| Probe before bind/listen | Not supported by the implemented ordering. The exact original bind/read timestamps were not logged, so timing at native-operation resolution is unknown. File existence does not guarantee a successful subsequent read. |
| Stale TEST generation or wrong process | The later valid readiness file matches namespace, data ID, PID/creation time and executable hash. Those later bytes cannot prove the failed read's contents. No observed mismatch establishes this hypothesis. |
| Publication failure, partial write, `os.replace`/reader contention | Not established. The publisher uses temporary-write/replace, not direct target truncation. A successful publication sets `first=False`. Some outer coordinator OSErrors are caught without logging, so absence of a log is not proof none occurred. No original publication exception or native handle trace exists. |
| Antivirus, indexing, ACLs or permissions | Possible external contributors to an I/O error, but no evidence here identifies any of them. No security settings were changed and no speculative exclusion or permission adjustment was attempted. |
| Lifecycle cancellation or duplicate Core start | The prior Core was already stopped and its lock released. The next restart grant was never issued. One Core acquisition and one start-spawn event appear in this namespace; no replacement launch is recorded. This is recorded coverage, not a disk-wide/process-history claim. |

Core stdout and stderr files in this namespace are both zero bytes. The coordinator's stdout/stderr were anonymous `Popen` pipes; the failed path did not drain or preserve them. The parent process and pipe handles are gone. Neither the original failing read nor coordinator stderr can now be recovered from these records. Later evidence does not fill those gaps.

## Peer identity

- **Dereference location:** `fixtures.py:1022`, `item['ready']['peer']` (and a subsequent access to `['identity']`).
- **Result validation present:** **NO**. No dictionary, required-field or non-None check precedes the access.
- **Original error masked:** **YES, diagnostically**, if the sentinel came from the helper's caught exception. The catch has already discarded that exception, and the TypeError cannot chain it. The JSON-null alternative also produces the secondary error without an underlying read exception.
- **Secondary failure:** `TypeError`, not an authentication rejection, timeout or AttributeError.
- **Live peer query:** reached; the comparison/assertion and authenticated attachment were not completed.
- **Existing failed-read coverage:** no targeted tests were found for this Stage 4 coordinator readiness read returning None, malformed readiness or cleanup of its partially initialized item. The inspected restart unit suite tests durable intent/claim records and injected claim-write failure; that is not coverage of this path. Prior actual coordinator races cover successful attachment. The observed gap remains a proposed test addition, not a new PASS.

Authentication stays intact: `bootstrap.client()` checks the named-pipe peer, server proof, full expected identity, client process binding and negotiated protocol before transmitting client proof and operation. This diagnostic neither changed nor skipped those checks.

## Restart timeline

Times below are **16 September 2026 AEST (UTC+10)**. Machine-readable UTC timestamps, raw FILETIME integers, event clocks and provenance are in `historical-timeline.json`, `historical-events.json` and `historical-record-extract.json`. File mtime is not the instant an atomic replacement completed. Record indices are zero-based in the preserved campaign.

| Time / bound | Observation and evidence |
|---|---|
| 11:50:59.225574 | Restart command wrapper starts, wrapper PID 23896 (`regressions.json`). This wrapper PID is not substituted for a verified worker identity. |
| 11:51:29.767212 | Old coordinator PID 20192 created; FILETIME 134339970897672121. |
| 11:51:29.886997 | Old coordinator readiness file mtime. Its exact bind and attach times are absent. Subsequent successful start establishes that authenticated operations did occur. |
| 11:51:29.936624 | Old TEST Core PID 11728 creation FILETIME 134339970899366241, from preserved Core identity. |
| 11:51:29.944628 | Old coordinator records `start_spawned`. |
| 11:51:30.059971 | Core records `core_acquired`. |
| 11:51:30.247052 | Coordinator records authenticated `start_verified`. |
| After verification, before drained event | Controller fresh attach and authorized stop acknowledged, records 381–382. Exact operation timestamps were not recorded. The stop file mtime is retained in the inventory. |
| 11:51:31.523860 | Core records `stage4_drained`. |
| After drain, before next coordinator creation | Records 383–386 confirm Core exit/lifetime-lock release, durable stop retained, authenticated old-coordinator close and exit 0. Exact close/exit timestamps are absent. |
| 11:51:31.583331 | Next coordinator PID 9400 created; FILETIME 134339970915833311. Epoch/instance `70895a6e78c5418c89fc9440d2deab50`. |
| After creation, before initial publication | Named-pipe creation must precede readiness publication by source order; exact native timestamp unavailable. |
| 11:51:31.705933 | Next readiness file mtime, later observed valid, 684 bytes. SHA-256 `785d037804e80e87a037ffafac9635b6000c6b30c62e2ea1ea4bf157f9c8a339`. This is not a timestamp for the failing read. |
| After new process creation, before 11:51:31.965677 | File existence loop completes; readiness read returns None; live process query executes; peer dereference fails. Failure record 387. Authenticated attach, restart grant and new Core launch are **not reached**. |
| Before 11:51:31.965677 | Original cleanup retries `close()` on known coordinators; PID 9400 fails through missing readiness, record 430. Exact cleanup time unavailable. |
| 11:51:31.965677 | Wrapper observes failed command exit 1; upper bound on failure and harness cleanup, not a measured failure timestamp. |
| After failure | A preserved report describes PID 9400 observed live, then absent without intervention. The raw live snapshot timestamp is unavailable here. |
| 11:57:21.467763 | Final historical census records all 126 TEST identities absent. It does not prove authenticated cleanup succeeded. |

Both coordinator executables and the old Core use SHA-256 `372c2eae555b344520bf147be0096e009069aeca4e7f78d6aecea6d53158056a`, from `C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`. Failed TEST data identity: `TEST-871fd3c547cf403fb58585539d0fec5a`. Failed namespace: `TEST-STAGE4-54d0867bae6a4d5b85a687940dbb36fd`.

## Cleanup — separate finding

**Normal cleanup failure:** confirmed. `run()` catches the main failure, then `close(item)` at line 1072 calls `cc(item,'close')` if the coordinator is still live. `cc()` immediately indexes `ready['peer']` and `ready['identity']` at line 1027. With `ready=None`, it cannot even call the authenticated client, send close or wait for exit. If the coordinator has exited between observations, line 1076 also dereferences `ready['identity']` while reporting its exit. Both branches are unsafe for this partially initialized item. The saved cleanup record contains only the secondary error string, so its exact branch/traceback was not captured.

**Root cause:** cleanup is coupled to successful startup, reusing incomplete readiness/session state. The item and process are present in the list; this is not a missing coordinator object or proven stale identity-list issue. `token` is still None because attachment was never reached. Valid authority was not revoked by this TypeError; the owner process binding and authentication policy remain intact, but an authenticated session was never established. Retained in-memory bootstrap credentials were not sufficient for the existing cleanup implementation because it cannot proceed without readiness. No secrets were recovered, copied or archived.

**Physical outcome:** normal close was not established; PID 9400 was initially retained/live, then later absent. The existing coordinator loop's 120-second deadline, with 1.2-second connect waits, is consistent with a later natural exit when no start worker was launched. There is no captured coordinator exit status/time to prove this caused its historical disappearance. Absence must not be relabelled authenticated cleanup PASS.

**Reporting issue:** even an already-exited process can hit the second None dereference, and the catch records only a string. A separate process result, close-operation result and primary startup exception are required to avoid conflating physical exit with successful protocol cleanup.

## Minimal isolated reproduction

Exact executed command, in the source repository, using the approved host execution context:

```powershell
.\.venv\Scripts\python.exe -B docs\deployment-completion-20260916\coordinator-readiness-diagnostic-20260916-7a61c902\minimal_probe.py
```

The new diagnostic script calls the **unchanged** `RestartCampaign.coordinator/start/stop/close` methods. Six fresh coordinator-only starts use no Core. A seventh namespace runs the exact old-Core start → authenticated stop → old-coordinator close → next coordinator with `before-intent` profile sequence. It stops before issuing the next restart grant; no crash injection occurs. No Electron, providers, new authority or full campaign was used.

`sys.settrace` observes only the coordinator readiness boundary and helper in the parent, recording any original exception/errno/WinError/traceback before the existing helper swallows it. It records no credentials or frame locals. Child launch code, filtered environment, executable and private stdin configuration path remain unchanged. Observation can affect scheduling; this is not the same load as the preceding full contender campaign.

- **8/8 readiness reads** returned dictionaries; **0 None returns / 0 original read exceptions**.
- **8/8 authenticated attachments** completed; **8/8 original authenticated coordinator closes**, exit 0.
- **1 TEST Core** started and stopped through existing authority; lifetime lock release verified. No replacement Core or restart authorization was issued.
- **33/33 original fixture checks** passed; these are diagnostic results, not rerun acceptance totals.
- Elapsed diagnostic process work: **3.417 seconds**, measured by this script; no reliability/incidence estimate inferred from eight trials.
- Original coordinator stdout/stderr are preserved (16 empty log files).
- Subsequent independent read-only process verification finds all **9/9** diagnostic identities absent.
- No correction, retry, forced cleanup, deletion or fault injection; all measured source hashes unchanged.

Exact process creation times, executable hashes, epochs, launch arguments, filtered environment, read/attach order, cleanup and timestamps: `minimal-result.json`; assertion records: `minimal-original-fixture-records.json`; follow-up census: `final-process-verification.json`.

**This reproduction did not recover the original trigger. Stop here; do not keep rerunning until a desired outcome appears.**

## Minimum proposed corrections — NOT IMPLEMENTED

1. **Runtime/lifecycle:** none justified by this evidence. Do not change `stage4_runtime.py`, Stage 1 `harness.read()`, locking, IPC guard, response-commit code, blank-UI bootstrap or package contents to address an unconfirmed cause. Additional runtime instrumentation would require a concrete separate proposal if later necessary.
2. **Acceptance driver diagnosis:** in `tests/lifecycle_stage4/fixtures.py`, use a strict, explicit readiness-load path for this coordinator record. Preserve the original exception, operation/path, errno/WinError and traceback. Validate object and required fields before dereferencing; retain and report the exact spawned process identity separately. Keep the existing deadline, process-generation checks and authenticated bootstrap. A failed read must fail clearly; no broad retry loop or automatic replacement start is proposed. Capture bounded stdout/stderr and startup state rather than masking the first failure with TypeError.
3. **Cleanup driver:** in that same file, handle a partially initialized coordinator independently of its normal return value. Keep the original startup failure immutable. An already-exited process can be reported from its retained verified process handle/identity without indexing None. For a live, never-attached coordinator, propose a separate bounded cleanup-only readiness read: validate namespace, endpoint, full identity and live process against the retained creation-time/executable pin, then use the existing owner bootstrap and ordinary authenticated close. This must not retry admission, issue a start/restart grant or silently turn the failed trial into PASS. If identity is uncertain, or attach outcome/session is unknown, retain for review or observe the existing deadline; do not bypass proof checks, forcibly kill or invent a new session-recovery authority. Whether this exact recovery path is accepted requires owner review before implementation.

**Proposed file scope:** `tests/lifecycle_stage4/fixtures.py`; focused tests in `tests/lifecycle_stage4/test_stage4.py`; nonsecret diagnostic/report files. No Stage 1 semantics or production enrollment changes. If the existing session contract prevents safe cleanup, stop for review rather than expanding it.

**Focused validation after approval:** failing read with original OSError/errno/WinError; invalid UTF-8/JSON/null/missing fields; delayed file/process exit/deadline; mismatched PID/creation time/executable/namespace; no attach or restart issuance on failed readiness; successful original path; live unattached and already-exited cleanup; uncertain/partly attached cleanup fails closed; no primary-exception masking; authenticated close proof and process/lifetime-lock verification. These are prospective deterministic failure tests, not events alleged to have happened historically. Then rerun the original failing restart campaign, and only afterward the required applicable acceptance/regressions. No new test was executed for these proposed cases in this diagnosis.

**Rollback:** retain these exact pre-correction source hashes and the existing failed-source snapshots. Revert only the future reviewed driver/test diff; never reset the dirty working tree. Diagnostic evidence and the original failed candidate remain immutable. This diagnosis itself needs no runtime rollback.

## Risk and preserved boundaries

| Boundary | Proposed impact / constraint |
|---|---|
| Production | No production source behavior, process, database, configuration or enrollment changes. Driver changes must remain TEST-only. |
| Authentication | Preserve full live process pin and existing pipe proofs. A cleanup-only read is not identity or authority by itself. Reject mismatch; never transmit proof before verified peer. |
| Lifecycle authority | Reuse only the original controller's existing close authority. No new restart/adoption/grant authority. Unknown attach state remains fail-closed. |
| TEST isolation | Unique TEST namespace/data and private random TEST bootstrap material; no production credentials. |
| Cancellation semantics | No changes proposed. |
| Response-commit boundary | Frozen; no changes proposed. Its prior 306-trial/4,748-assertion PASS remains separate. |
| Package integrity | No package change/rebuild proposed. 796/796 frozen candidate files remain identical. |

Original package manifest SHA-256: `fcbd0381f3b4d2b0acd89c15e373418dc27172a60456e3e1698a1963fec091e3`.
Source/rollback HEAD: `8f0b9bce181800f9339249c4024e396246e94208`; HEAD tree: `e61f7d1df443826556c306ed0359b815c1ca19ed`.

Final verification confirms **101/101 recorded source entries unchanged**, **796/796 candidate payloads unchanged**, **84/84 prior archive files plus the matching verification receipt unchanged**, and **28/28 files in the historical failed TEST namespace unchanged**. Source entries include duplicate paths and are not claimed as distinct-file totals. See `preservation.json`, `source-comparison.json` and `final-integrity.json`.

New files are confined to this diagnostic folder and seven fresh TEST namespaces created by the original fixture; synthetic runtime state remains local. Only this folder's nonsecret reports, scripts, copied nonsecret historical records/logs and hashes are archived to TEAGUE INDUSTRIES DATABASE. No database, provider key, session token, bootstrap configuration or heavy runtime is archived. The broad synchronization script is deliberately not used because this task authorizes only a narrow evidence archive.

Read-only collection command mistakes (a PowerShell-unquoted Git tree expression, literal wildcard arguments passed to rg, and an initial lookup of `authentication.py` instead of the imported `bootstrap.py`) were corrected as lookups only. They did not execute tests or change configuration. All actual diagnostic results and the original acceptance failure remain preserved.

Historical findings remain separate: the original Stage 1 PermissionError is unconfirmed; the response-publication defect and challenge/response contention investigations retain their existing dispositions; the restricted-context Electron GPU/DLL finding is unchanged. None proves the cause of this new coordinator readiness read.

**PRODUCTION TOUCHED: NO. ACCEPTANCE COMMIT: NO. FULL ACCEPTANCE RERUN: NO. STAGE 5: NOT STARTED.**

Review requested: only the TEST driver readiness diagnostics, validation and partial-start cleanup changes described above, with focused negative tests. No runtime correction or acceptance approval is implied. **STOP FOR REVIEW.**
