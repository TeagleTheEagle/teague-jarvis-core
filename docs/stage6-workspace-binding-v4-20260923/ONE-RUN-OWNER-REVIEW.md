# Corrected one-run diagnostic procedure — OWNER REVIEW ONLY

NOT EXECUTED. Requires separate authorization for exactly one fresh normal small-live diagnostic and its three sequential UAC prompts. No medium, large, 59.7 GB, protected VM, production or backup operation is included.

## Fixed inputs

- Candidate: `D:\JARVIS-STAGE6-LIVE\fb0bf86657a64aff85a1799db37e94c7\code`
- Source manifest SHA-256: `d2f6738f5d7c3f22fe361f6cb1da174f630d8e150574009b59825d88321ed4d7` (229 files).
- Dataset: candidate-local small-synthetic/00.bin–11.bin, 12 files, 786,432 bytes, hashes from that manifest.
- DLL: candidate-local J6OwnedEntry.dll, SHA-256 `ff2454390795bb302cdb68990b7f52fc02db7efedb55d2bbd3dd2cbd0e1da7ef`.
- Shared runtime: exact paths/versions/hashes in shared-runtime-v4.json, itself SHA-256 `db22fb24d951f7f97d0e638a5737ce656f8b53701b914732f637708f8dcdb9fd`.
- New run name: protected- plus a newly generated 32-hex UUID. Never use an existing offline fixture or failed run.
- Failure destination: sibling preservation-v4, fixed by preservation-policy-v4.json. No old preservation destination.

## Before launch

1. Reopen this action's archive; verify every member and the candidate source/runtime identities. Verify originals remain unchanged. Run the existing read-only host census: require no matching process, no trace, no unknown entry and VirtualBox closed. Do not inspect protected files.
2. Use a fresh non-elevated command process. Reject existing old-workspace environment/CWD/import dependencies before preparation. Apply only process-local approved runtime PATH/module roots and PYTHONNOUSERSITE=1, with no profile. Do not dump the environment. Do not change machine settings or security policy.
3. Prepare one normal run with the unchanged small_binding_v3.make('normal'). It creates only the small contract and run directories. Point TEMP/TMP to this run's temp directory. Create workspace-binding-v4.json with workspace_binding_v4.prepare(root), then verify it. No observer starts during preparation. Keep the exact-equality declaration unchanged.
4. Preserve this fresh binding, manifest hash and prospective command record before launching. Stop on any mismatch; do not update hashes merely to continue.

The intended preparation commands, after the separate approval and preflight, are:

```powershell
$candidate = 'D:\JARVIS-STAGE6-LIVE\fb0bf86657a64aff85a1799db37e94c7\code'
$py = 'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
Set-Location -LiteralPath $candidate
$runtime = Get-Content -LiteralPath "$candidate\shared-runtime-v4.json" -Raw | ConvertFrom-Json
# First complete the old-environment rejection described above. The following
# assignments apply only to this disposable command process, not the machine.
$env:PATH = (@($runtime.executables.python.path, $runtime.executables.pwsh.path,
  $runtime.executables.powershell.path, $runtime.executables.logman.path) |
  ForEach-Object { Split-Path -Parent $_ } | Select-Object -Unique) -join ';'
$env:PSModulePath = $runtime.moduleRoots -join ';'
$env:PYTHONNOUSERSITE = '1'
$root = (& $py -B -c "from small_binding_v3 import make; print(make('normal'))").Trim()
if ($LASTEXITCODE -ne 0) { throw 'Small preparation failed' }
$run = Split-Path -Leaf $root
$env:TEMP = $env:TMP = Join-Path $root 'temp'
& $py -B .\workspace_binding_v4.py prepare $run
if ($LASTEXITCODE -ne 0) { throw 'Binding preparation failed' }
& $py -B .\workspace_binding_v4.py verify $run
if ($LASTEXITCODE -ne 0) { throw 'Binding verification failed' }
```

This block is a procedure for a later authorized action, not an instruction to execute now. No approval flag substitutes for owner approval.

## Exactly one execution and three prompts

After fresh-run preflight passes, the approved wrapper is invoked once through an import from the verified CWD:

```powershell
& $py -B -c "import json,sys; import one_run_v4 as w; import failure_preserve_v4 as f; r=w.execute(sys.argv[1],f.cli_policy(sys.argv[1]),approved=True); print(json.dumps(r,sort_keys=True)); sys.exit(0 if r.get('route')=='SUCCESS_FINALIZER_COMPLETED' else 1)" $run
```

Use this CWD-bound invocation, not an unrelated historical wrapper or a shell command naming a prior D: workspace. The existing census excludes its exact controller and inspects other D:-named command lines; do not introduce extra D:-named wrapper/helper processes or relax that census. The one-run wrapper has no retry loop.

Expected UAC requests, in order:

1. `D:\JARVIS-STAGE6-LIVE\fb0bf86657a64aff85a1799db37e94c7\code\J6AuthorityTraceV3.exe`, arguments: fresh run root, launcher PID and creation identity.
2. `D:\JARVIS-STAGE6-LIVE\fb0bf86657a64aff85a1799db37e94c7\code\J6StartupTrace.exe`, arguments: fresh run's detail directory and the same launcher identity.
3. `C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe`, arguments: `-NoProfile -File <candidate>\timed_monitor.ps1 -Run <fresh-run> -KernelPid <fresh-authority-observer-PID>`.

The current driver publishes the existing sequential prompt gates only after the prior observer's readiness record. Do not pre-create those gates. Verify each image/hash and displayed UAC context; publisher text must be checked as displayed, not assumed. Unexpected executable/command/publisher context or a fourth prompt: stop, decline it, preserve failure. Cancellation/denial consumes this attempt; no automatic reissue.

## Lifecycle and acceptance

Observers ready → collector → two small hash passes/metadata checks → Phase A local finalization → collector return → observers remain for exact helper terminal evidence → independent terminal receipt → pre-shutdown workload census → ordered application/detail/authority shutdown → independent launcher/observer exit proof → final zero-process/zero-trace census → unchanged completed_v3 and small_check_v3 → v4 finalizer.

There is ONE original 20-second cleanup deadline: cleanupEntryQpc + 20 × frequency. It does not reset at collector return, helper exit, receipt, census, observer shutdown or launcher exit. All acceptance cleanup must finish before it. Heartbeat remains <10 seconds; the 13.6-second probe deadline and 15-second independent observation period are unchanged. Durable archival never grants extra acceptance-cleanup time.

Require all original authority/sequence/segment/loss/identity/native/handle predicates, both hashes, unchanged metadata, valid run binding, exact local DLL/runtime identity, complete terminal evidence, valid censuses, ordered exits, unchanged frozen sources and verified archive. The two diagnostic sidecars must have correct schema/run/session/channel/frequency/hash and remain diagnostic-only. They cannot override loss or a failed lifecycle predicate.

Success finalizer runs only after completed terminal evidence and checker eligibility. A diagnostic may finish collecting useful data while its acceptance remains rejected; do not equate collection completion with acceptance.

## Failure and archival

Any missing/contradictory/lost evidence, deadline breach, source/runtime drift, stale binding, unexpected artifact, unknown census, UAC failure, live leftover or archive error: preserve the FIRST failure and perform only the existing bounded failure cleanup. Route to fresh failure_preserve_v4; acceptance_seal=false. Missing telemetry/binding stays explicit PARTIAL, not accepted. If writers cannot be proven stopped, preserve control/census evidence and report CLEANUP_UNPROVEN; do not read/archive potentially mutable evidence as frozen.

Expected status families: SMALL_NORMAL_PASS only after successful finalizer/archive; otherwise the exact original rejection plus FAILURE_EVIDENCE_COMPLETE, FAILURE_EVIDENCE_PARTIAL, CLEANUP_UNPROVEN or ARCHIVE_UNVERIFIED as appropriate. Later cleanup does not change the failed outcome. UAC cancellation or preflight failure is BLOCKED, never PASS.

After either outcome, independently reopen/hash the local archive, copy finalized nonsecret evidence to a new canonical evidence directory, verify that copy, recheck source hashes, and perform the final read-only census. Stop after this one attempt. Do not retry, edit the candidate, replace a checker, run a larger gate, access the protected VM, or change production.
