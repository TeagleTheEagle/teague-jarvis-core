# Corrected one-run trace diagnostic — OWNER REVIEW ONLY

This procedure is NOT authorized to execute during the path-filter correction. It requires separate owner authorization for exactly one fresh normal small-live diagnostic and the three sequential observer UAC prompts. No retry, medium/large run, 59.7 GB operation, protected VM access or production change is included.

## Inputs and unchanged boundaries

Candidate: `D:\JARVIS-STAGE6-LIVE\fb0bf86657a64aff85a1799db37e94c7\code`

229-file candidate manifest SHA-256: `d2f6738f5d7c3f22fe361f6cb1da174f630d8e150574009b59825d88321ed4d7`.

Dataset: candidate-local small-synthetic/00.bin through 11.bin, 12 files, 786,432 bytes. Preserve the authoritative Windows-style manifest names. Use the corrected dataset_records validation; never rewrite the manifest or consult an old dataset.

DLL: candidate-local J6OwnedEntry.dll; SHA-256 `ff2454390795bb302cdb68990b7f52fc02db7efedb55d2bbd3dd2cbd0e1da7ef`.

Runtime paths/versions/hashes: candidate shared-runtime-v4.json; SHA-256 `db22fb24d951f7f97d0e638a5737ce656f8b53701b914732f637708f8dcdb9fd`.

Failure destination: `D:\JARVIS-STAGE6-LIVE\fb0bf86657a64aff85a1799db37e94c7\preservation-v4` under the existing policy, with an exclusive new per-run archive directory.

Heartbeat <10 seconds; probe deadline 13.6 seconds; independent observation bound 15 seconds; existing campaign/kernel bounds; ONE 20-second absolute cleanup deadline from the approved cleanup-entry QPC. No reset after return, terminal evidence, census, observer shutdown, launcher exit or final census. ETW providers, buffers, keywords, clocks, queues, writer behavior, telemetry, frozen checker and candidate bytes remain unchanged.

## 1. Preservation and corrected preflight — only after new approval

Verify this correction's archive and helper hashes, then the unchanged prior archives/candidate. Use a fresh non-elevated command process; no profile, permanent environment changes or secret logging. The corrected helper rejects old-workspace environment paths, establishes only the approved process-local runtime resolution, verifies the candidate/runtime/dataset/old evidence, and performs the existing read-only host census. All counts must be zero with no unknown census entries.

The full corrected helper has NOT been executed during offline testing. The following command is for the later authorized action:

```powershell
Set-Location -LiteralPath 'D:\JARVIS-STAGE6-LIVE\fb0bf86657a64aff85a1799db37e94c7\code'
& 'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B -c "exec(compile(open(r'C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-path-filter-fix-20260923\preflight.py').read(), 'preflight.py', 'exec'))"
if ($LASTEXITCODE -ne 0) { throw 'Preflight blocked; preserve evidence and STOP; no retry' }
```

The helper retains its exclusive-output/no-repeat guard. Its new report directory preserves the failed original helper and evidence. On success it prepares one fresh protected-<32-hex UUID> run with case=normal, creates the unchanged small declaration and separate workspace-binding-v4.json, verifies the binding, and writes preflight.json. The protected- prefix is only a synthetic TEST naming convention.

If any preflight condition fails: STOP before UAC. Do not fix, rerun or refresh hashes automatically.

## 2. Exactly one execution

From the same approved candidate CWD, read the successful preflight record. Revalidate the binding immediately before launch. Set only the current command process's approved PATH/module roots/no-user-site and fresh run TEMP/TMP. The following is a later-owner-approved command, NOT a command to run now:

```powershell
$record = Get-Content -LiteralPath 'C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-path-filter-fix-20260923\preflight.json' -Raw | ConvertFrom-Json
if ($record.status -cne 'PASS') { throw 'No passing preflight' }
$run = $record.run
$runtime = Get-Content -LiteralPath '.\shared-runtime-v4.json' -Raw | ConvertFrom-Json
$py = $runtime.executables.python.path
$env:PATH = (@($runtime.executables.python.path, $runtime.executables.pwsh.path,
  $runtime.executables.powershell.path, $runtime.executables.logman.path) |
  ForEach-Object { Split-Path -Parent $_ } | Select-Object -Unique) -join ';'
$env:PSModulePath = $runtime.moduleRoots -join ';'
$env:PYTHONNOUSERSITE = '1'
$env:TEMP = $env:TMP = Join-Path $record.root 'temp'
& $py -B .\workspace_binding_v4.py verify $run
if ($LASTEXITCODE -ne 0) { throw 'Binding changed; STOP' }
& $py -B -c "import json,sys; import one_run_v4 as w; import failure_preserve_v4 as f; r=w.execute(sys.argv[1],f.cli_policy(sys.argv[1]),approved=True); print(json.dumps(r,sort_keys=True)); sys.exit(0 if r.get('route')=='SUCCESS_FINALIZER_COMPLETED' else 1)" $run
```

Use the CWD-bound wrapper invocation shown above. Do not introduce additional D:-named orchestration processes that the unchanged census could classify as live TEST workers. The approval argument does not replace actual owner approval.

## 3. Exactly three sequential UAC prompts

Verify the candidate manifest hashes before requesting them. Expected images and arguments:

1. `<candidate>\J6AuthorityTraceV3.exe`: new run root, launcher PID, launcher creation identity.
2. `<candidate>\J6StartupTrace.exe`: new run detail directory, same launcher identity.
3. `C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe`: `-NoProfile -File <candidate>\timed_monitor.ps1 -Run <new-run> -KernelPid <authority-observer-PID>`.

The unchanged driver opens the existing prompt gates after the preceding observer publishes readiness. Do not pre-create those gates. Check the displayed publisher/context rather than assume it. Unexpected image, hash, materially different arguments, fourth request, or cancellation/denial: STOP; no automatic reissue.

## 4. Observation, cleanup and finalization

Observers ready → one normal small collector → both hash passes and unchanged metadata → Phase A local finalization → collector return → observers stay alive for exact helper terminal evidence → independent terminal receipt → pre-shutdown workload census → ordered application/detail/authority shutdown → independent launcher/observer exits → final zero-process/zero-trace census → unchanged terminal verification/checker → success finalizer only if every predicate passes.

Loss telemetry remains observational. Preserve separate authority/detail samples and slow spans. If loss occurs, do not adjust buffers/settings or excuse loss because identities later reconcile. Continue only through existing fail-closed cleanup behavior.

If any condition fails, preserve the FIRST failure and use the existing NON-ACCEPTANCE failure path. No success seal; no retry. Partial/missing telemetry, uncertain writers, remaining processes or unavailable census stay explicit. Late successful cleanup cannot reverse rejection.

Reopen/hash-verify the success or failure archive, copy only finalized nonsecret evidence to a new canonical archive, verify that copy, recheck all frozen/source hashes and perform final read-only cleanup census. Report the exact run status and per-session telemetry, keeping historical causes UNCONFIRMED unless newly proven.

STOP after that one authorized attempt. Do not modify the candidate/checker, run a larger gate, access the protected VM or modify production.
