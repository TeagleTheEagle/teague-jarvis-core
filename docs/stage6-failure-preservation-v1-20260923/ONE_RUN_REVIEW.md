# ONE fresh small-live run — OWNER REVIEW ONLY

This action did not authorize or execute a live run or request Windows UAC.
Do not execute these commands until the owner separately approves exactly one run
and its three existing sequential observer prompts.

## Fixed inputs and integrity

- Frozen coordination candidate: `D:\JARVIS-STAGE6-LIVE\7f204e14c90a497a8476be0e9927e074\code`.
- Candidate source manifest: `675ba3f5cd6966fc6040083922d857769af418878f1f403afa38e6d5a6f50fc8`, 216 files.
- Separate preservation/wrapper revision: `D:\JARVIS-STAGE6-LIVE\cab9745de28a4cae8aa6f6f7a516bf54\code-r2`.
- Its four-file source manifest: `e781ed6389dd809805fb89c27b6f838623d4f2da707fcd7a160d22c25249ea28`.
- Failure output root: `D:\JARVIS-STAGE6-LIVE\cab9745de28a4cae8aa6f6f7a516bf54\preservation`.
- Dataset: frozen candidate's `small-synthetic`, 12 files / 786,432 bytes.
- Case: `normal` only; fresh UUID `protected-<32 lowercase hexadecimal characters>`.
- No reuse of mutable run state, no second attempt, no controlled-failure live case.

Before preparation, verify both source manifests and every listed source file,
the previous preserved archive and a new host-context read-only census. Require
zero matching diagnostic processes, zero trace sessions and VirtualBox closed.
Do not inspect protected VM/configuration files to establish that VirtualBox is closed.
Stop on any drift, uncertainty or unexpected identity. Census failure is not zero.

## Expected Windows UAC prompts

1. `D:\JARVIS-STAGE6-LIVE\7f204e14c90a497a8476be0e9927e074\code\J6AuthorityTraceV3.exe`, with run root, launcher PID and launcher creation FILETIME.
2. `D:\JARVIS-STAGE6-LIVE\7f204e14c90a497a8476be0e9927e074\code\J6StartupTrace.exe`, with run's detail directory and the same launcher identity.
3. `C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe`, with `-NoProfile -File D:\JARVIS-STAGE6-LIVE\7f204e14c90a497a8476be0e9927e074\code\timed_monitor.ps1 -Run <fresh-ID> -KernelPid <authority-PID>`.

These are the existing fixed read-only observers. The wrapper/preserver stays
non-elevated. Windows publisher/display wording is not asserted. Denial or
cancellation is a failed/blocked attempt, never permission to retry a prompt.

## Prospective commands — only after separate approval and preflight

```powershell
$stage6Code = 'D:\JARVIS-STAGE6-LIVE\7f204e14c90a497a8476be0e9927e074\code'
$stage6Preserver = 'D:\JARVIS-STAGE6-LIVE\cab9745de28a4cae8aa6f6f7a516bf54\code-r2'
$stage6Python = 'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
Set-Location -LiteralPath $stage6Code
$stage6Prepared = & $stage6Python -B .\small_binding_v3.py prepare normal
if ($LASTEXITCODE -ne 0) { throw 'Preparation failed. STOP; preserve any identified partial run, no retry.' }
$stage6Run = Split-Path -Leaf $stage6Prepared
& $stage6Python -B "$stage6Preserver\one_run_v1.py" $stage6Run --owner-approved-one-small-run-and-three-uac
$stage6Result = $LASTEXITCODE
```

Do not immediately abort the surrounding owner procedure on a nonzero wrapper
exit without inspecting its preservation result. A rejected run intentionally
returns nonzero even when failure evidence was successfully archived.

## Unchanged live ordering

Observers ready before collector -> Phase A stops admissions, finalizes local
evidence and releases local handles -> collector returns -> observers stay alive
for exact-instance terminal capture -> independent immutable terminal receipt
validated -> pre-shutdown workload census -> application observer stops/drains ->
detail observer stops/drains -> authority captures subordinate terminal-tail
receipt -> authority observer stops/drains -> launcher exits -> external driver
verifies exits -> final zero-process/zero-trace census -> versioned checker/finalizer.

All timed acceptance cleanup uses the original cleanup-entry QPC plus exactly
20 seconds. No reset at collector return, receipt publication, census, observer
shutdown or launcher exit. Heartbeat 10s, probe 13.6s, independent observer 15s,
campaign 90s and kernel capture 180s remain unchanged.

## Success branch

The unchanged external driver must complete evidence successfully. The wrapper
then invokes the existing versioned success finalizer once. It cannot invoke it
after a nonzero driver result. The finalizer owns checker evaluation, normal
archive verification and the normal acceptance receipt. The wrapper itself
creates no acceptance seal.

Require both hashes, unchanged source metadata, complete run binding, exact
terminal identities, independent-channel consistency, zero authoritative loss,
healthy heartbeat/deadlines, ordered shutdown, independent exit evidence, zero
final matching processes/traces, checker success and durable verified archive.
Any missing criterion is not a pass.

After wrapper exit, perform the read-only host census again to establish that
the previously explicitly excluded controller/census processes have also exited.
Verify the frozen source and wrapper hashes, then copy the finalized evidence to
a fresh canonical record directory and independently hash-verify that copy.
Canonical archival failure blocks completion; the existing local archive remains.

## Failure branch

The wrapper records its first observed driver/finalizer exception separately and
calls the independent failure-preservation tool once. It does not invoke the
success finalizer after driver failure. Existing launcher failure cleanup retains
its already-approved bounds; the wrapper adds no termination or wait authority.

If writers/cleanup are still live, unknown or inaccessible, the tool does NOT
pretend they stopped. It preserves a metadata-only partial archive with
`CLEANUP_UNPROVEN`, missing/unpreserved files, census evidence and the observed
failure. It does not read potentially mutable source contents. Where independently
quiescent, it holds deny-write/delete read handles, preserves approved files
byte-for-byte, checks recorded helper instances through native handles, records
missing/malformed/cross-run/unknown artifacts, and independently verifies the ZIP.

Expected output is exactly one exclusive directory:

`D:\JARVIS-STAGE6-LIVE\cab9745de28a4cae8aa6f6f7a516bf54\preservation\FAILURE-EVIDENCE-<run-ID>`

Every result is NON-ACCEPTANCE FAILURE EVIDENCE with `acceptance_seal=false`.
Archive states: `FAILURE_EVIDENCE_COMPLETE`, `FAILURE_EVIDENCE_PARTIAL`,
`CLEANUP_UNPROVEN`, or `ARCHIVE_UNVERIFIED`. None means live validation passed.
Eventual cleanup after the deadline cannot change rejection. Unknown timestamps
and historical causes remain unknown. No STOP evidence is synthesized from handles.

If preparation failed after creating evidence, or the wrapper itself could not
reach its failure handler, identify that exact new directory without guessing.
Invoke the standalone tool once, only if no preservation directory already exists:

```powershell
& $stage6Python -B "$stage6Preserver\failure_preserve_v1.py" $stage6Run --component 'preparation-or-wrapper' --reason '<exact nonsecret observed failure>'
```

Do not use this command to overwrite or retry a failed archive. If no evidence
directory exists, there is nothing to archive. If the tool cannot create/verify
the archive, preserve its partial outputs and report `ARCHIVE_UNVERIFIED`/BLOCKED.
If cleanup is uncertain, stop and report exact known identities; no unapproved
termination. Copy only frozen nonsecret preservation outputs into a fresh canonical
directory; hash-verify the copy and report any copy failure separately.

## Final stop

Report the one run's real outcome and archival/cleanup status, then STOP for owner
review. No automatic retry, medium validation, 59.7 GB run, protected hashing,
VirtualBox operation, production change, checker replacement or deadline change.
Historical 21 AMBIGUOUS / 1 UNMATCHED and unexplained causes remain unchanged.
