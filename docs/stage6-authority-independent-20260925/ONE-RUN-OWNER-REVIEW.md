# Proposed ONE-RUN authority-independence discrimination procedure

OWNER REVIEW ONLY. This document does not authorize execution or UAC.
Exactly one normal small synthetic run; no retry. Historical underlying ETW-loss cause remains UNCONFIRMED.

## Inputs and preparation before UAC

Use the candidate and pinned hashes in adjacent `successor-binding.json`, not a source-tree build. This is an offline C: preparation candidate; do not launch it in place. Detailed executable is byte-identical to the predecessor. Only authority requested LogFileMode changes from 0x00000100 to 0x08000100.

1. Verify the archived report, all 245 candidate members, both frozen candidate manifests, successor binding, authority/detailed binaries, and predecessor/historical archives.
2. Create one fresh `D:\JARVIS-STAGE6-LIVE\<32-lowercase-hex>\code` directory. Copy only manifest-listed candidate files. No rebuild or source edit. Perform ONLY the existing reviewed path rebind: `baseline-allowlist.json` syntheticRoots to the fresh `code\small-synthetic`; `preservation-policy-v4.json` candidate/preservationRoot to this fresh workspace. Keep approvedProtectedRoots empty and realProtectedAccess false. Record both JSON before/after bytes. Freeze both source manifests with these path-only substitutions before any run. If existing preparation needs another change, STOP before UAC.
3. Verify exactly `small-synthetic\00.bin` through `11.bin`, 12 files / 786,432 bytes and expected per-file hashes. Reject extra/missing/duplicate/escaped/reparse paths. Verify candidate-local J6OwnedEntry.dll, pinned shared runtime binaries/components, scripts, unchanged helper handoff and preservation policy structure.
4. Use the existing `small_binding_v3.make('normal')`, `workspace_binding_v4.prepare(root)` and `verify(root)` sequence. Pin the fresh `protected-<32-lowercase-hex>` identity and binding/manifest digests. Use only existing per-process PATH/PSModulePath/PYTHONNOUSERSITE/run-local TEMP policy. No global environment edit.
5. Complete the existing host-context read-only census: zero matching diagnostic/VirtualBox processes, zero diagnostic trace sessions. Do not open protected VM/configuration or production files. Verify expected sidecar paths and run outputs do not already exist. Create the exclusive one-attempt launch record. Any mismatch: STOP, no launch.

## Expected elevation, only after separate owner approval

The existing launcher issues precisely these three sequential prompts; `<root>` is the prepared run directory, `<launcher PID/created>` its creation-verified identity:

1. `<code>\J6AuthorityTraceV3.exe <root> <launcher PID> <launcher creation FILETIME>`; successor authority hash must match the frozen binding.
2. `<code>\J6StartupTrace.exe <root>\detail <launcher PID> <launcher creation FILETIME>`; unchanged detailed hash must match the binding.
3. Bound `C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe -NoProfile -File <code>\timed_monitor.ps1 -Run <run> -KernelPid <authority PID>`.

Each executable, command, identity and publisher context must match the approved bindings. Unknown/different executable, fourth prompt, cancellation or unresolved identity: STOP, no automatic reissue. Only these TEST observers are elevated.

## Single execution

Invoke the existing `one_run_v4.execute(run, failure_preserve_v4.cli_policy(run), approved=True)` through the bound Python in the fresh candidate working directory with the existing controlled child environment. No other run, retry or configuration change.

Keep all providers/keywords/levels, BufferSize 64 KiB, requested minimum 4 / maximum 64, FlushTimer 1, QPC, per-processor behavior, callbacks, selection, handoff, telemetry and limits unchanged. Detailed requested mode remains 0x02000100 and must not gain the independent-session bit. Authority requested mode is 0x08000100; returned Windows default flags must be recorded separately, not silently normalized. Verify runtime-recorded mode retains the new authority bit and excludes it on detailed; any unrelated configuration drift rejects the run.

Execute the real collector path: both small hash passes, metadata checks, Phase A, exact terminal helper receipt, pre-shutdown workload census, ordered observer shutdown, independent exits, and final zero-process/zero-trace census. Keep the same original absolute 20-second cleanup deadline; never reset it after any phase. Heartbeat <10 seconds; existing probe/observer/campaign limits remain unchanged.

Once launch is dispatched, do not issue parallel shell status-inspection commands containing the D: run/workspace path during the failure-preserver census. Poll only the existing command session until its preservation route returns. This prevents the controller's read-only inspection shell from being mistaken for a live diagnostic; no census filter is relaxed.

## Failure, analysis and preservation

On the first acceptance-critical failure, permanently reject. Run only existing bounded failure cleanup and NON-ACCEPTANCE preservation. Do not invoke success finalizer. Later cleanup cannot convert failure to PASS.

After quiescence, preserve diagnostic sidecars separately using the existing bounded preservation helper; validate exact run/session/binary/candidate bindings and overflow flags. Correlate the eight fresh target identities with independent creation-verified handles and native records, never PID alone. Analyze each channel using the existing analyzer and independent timing windows. Record final EventsLost and every sampled increment, callback receipt/selection, buffers, CPU/progress, writer/persistence, first failure, cleanup and any evidence limitation.

Run the unchanged versioned checker and success finalizer only when all existing prerequisites pass. Every required START/STOP must be complete, exact identity/handle/native evidence consistent, both EventsLost zero, no sequence/segment/loss contradiction, timely cleanup, durable evidence and verified archive. A missing or wrong runtime independent-session flag is also rejection. No loss tolerance or substitution is introduced.

Archive PASS or FAIL and hash-verify. Verify all frozen sources, dataset metadata/hashes, predecessor and historical archives afterward. Canonical-copy only this run's nonsecret finalized evidence and verify it. Final census must prove zero matching processes/traces. If the original failure archive is partial, preserve that disposition and report it explicitly; do not silently reseal it.

## Predeclared discrimination

- Authority complete/zero-loss while detailed loses: supports cross-session coupling; overall run FAIL, detailed defect unresolved.
- Both lose: this change did not resolve session reliability; overall FAIL.
- Both pass: this one run passes only if every other acceptance predicate passes; one non-reproduction does not prove historical cause.
- Authority zero-loss but required lifecycle missing: FAIL, not successful isolation proof.
- Any identity, source, configuration, deadline, archive or cleanup defect: FAIL/BLOCKED with exact first reason.

Report run disposition separately from causal interpretation. Do not claim this run alone completes Stage 6. STOP after one attempt for owner review, even if it passes. No medium, 59.7 GB, protected-baseline, VM, backup/restore or production operation follows.
