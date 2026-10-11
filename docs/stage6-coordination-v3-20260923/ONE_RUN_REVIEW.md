# Proposed ONE-RUN small-live procedure — OWNER REVIEW ONLY

Not authorized or executed in this action. No medium/large/protected run follows it.

1. Verify `candidate-final-r2.json`, all 216 candidate file hashes, the source manifest SHA-256 `675ba3f5cd6966fc6040083922d857769af418878f1f403afa38e6d5a6f50fc8`, originals and this action's final archive. Stop for any drift.
2. Perform a new read-only host census into a new evidence file. Require zero matching diagnostic processes/traces and VirtualBox closed. Do not inspect protected files.
3. Confirm separate owner authorization for exactly one normal small run and its three sequential UAC prompts: `J6AuthorityTraceV3.exe`, unchanged `J6StartupTrace.exe`, and the known bundled PowerShell running unchanged `timed_monitor.ps1`. No broader elevation or automatic retry.
4. After that approval, prepare a fresh UUID run using only the candidate's 12-file/786432-byte synthetic dataset. No old mutable state is reused.

Proposed commands, ONLY after the approval and preflight above:

```powershell
Set-Location -LiteralPath 'D:\JARVIS-STAGE6-LIVE\7f204e14c90a497a8476be0e9927e074\code'
$stage6Python = 'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$stage6Prepared = & $stage6Python -B .\small_binding_v3.py prepare normal
if ($LASTEXITCODE -ne 0) { throw 'Preparation failed; STOP' }
$stage6Run = Split-Path -Leaf $stage6Prepared
& $stage6Python -B .\external_driver_v3.py $stage6Run --owner-approved-one-small-run
if ($LASTEXITCODE -ne 0) { throw 'Run failed; preserve evidence; no retry' }
```

5. Verify genuine Phase A/local closure, collector termination, immutable independent terminal receipt, exact helper kernel/handle proof, workload-only census, observer dependency ordering, launcher exit and final census. All timed cleanup must finish within the original twenty-second deadline; the 4.6-second and 1.1-second drains are unchanged. Missing/late/contradictory evidence fails.
6. Only if the driver and completed evidence pass, run the versioned checker/finalizer once on that exact run:

```powershell
& $stage6Python -B -c "import sys; from workspace import run_dir; from small_finalize_v3 import finalize; print(finalize(run_dir(sys.argv[1])))" $stage6Run
if ($LASTEXITCODE -ne 0) { throw 'Finalization failed; preserve evidence; no retry' }
```

7. Verify the run archive and canonical evidence copy, candidate/original hashes and final cleanup. Keep every failure and provisional artifact. If cleanup cannot be proven, stop and report exact live identities; do not terminate an unrelated process.
8. Report this single small-run result and STOP for owner review. Do not run a second small case, medium validation, 59.7 GB hashing or any protected/production operation automatically.
