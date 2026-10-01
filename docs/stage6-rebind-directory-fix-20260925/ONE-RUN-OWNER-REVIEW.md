# Exactly one small handoff revalidation â€” OWNER REVIEW ONLY

NOT authorized to execute by the implementation approval. Do not paste/run the launch command until the owner approves this one attempt and its three observer prompts.

## Inputs

Candidate `D:\JARVIS-STAGE6-LIVE\ea85ed4b4ef14769acbe0b5e750aaed2\code`.

Expected small-source-v3.json SHA-256: `5966bdb43ed1efaa85f6956dd0552c7459f2eef4e1d7970e5143ac1376b316ef`.

Expected authority executable SHA-256: `a0b643f67deb477df6bc763accdac7fa5cb57910f79bf92396940c98faa63f48`.

Other executables/DLL/runtime identities are exact entries in that manifest and shared-runtime-v4.json. Candidate-local J6OwnedEntry.dll must retain `ff2454390795bb302cdb68990b7f52fc02db7efedb55d2bbd3dd2cbd0e1da7ef`.

Only small-synthetic/00.bin through 11.bin: **12 files / 786,432 bytes**, normal case. Use a newly generated protected-<32 hex> identity; this name is a synthetic convention, not permission for real protected sources. Reuse no mutable fixture/run state.

Heartbeat <10 seconds, process hard deadline 13.6 seconds, independent observation 15 seconds, and the existing campaign/capture limits remain unchanged. Cleanup has exactly one origin plus twenty seconds. No settings changes or retries.

## Preflight after owner approval, before any UAC

1. Verify this action's archive/manifest receipt and source hashes. Verify predecessor and failed-run archive preservation.
2. Verify every candidate manifest entry, all twelve synthetic file hashes/sizes, exact directory inventory, no traversal/reparse/hardlink escape, empty protected-root allowlist and realProtectedAccess=false. Windows manifest separators must be interpreted with PureWindowsPath, without rewriting the manifest.
3. In a fresh non-elevated command process, inspect only named runtime variables for old-workspace conflicts; do not dump environment/secrets. Set only the approved child/process-local PATH, PSModulePath and no-user-site values. No security policy changes.
4. Run existing read-only host census. Require zero matching processes/traces, VirtualBox closed, no unknown census state. Do not inspect protected files or start VirtualBox to prove this.
5. Generate exactly one fresh run using small_binding_v3.make('normal'). Prepare and verify workspace_binding_v4 against that run, candidate-local DLL, runtimes and new policy. No observers start in these preparation calls. Save the run identity, binding hash and successful preflight to exclusive new evidence files. If any check fails: preserve and STOP before UAC.

Preparation API, only after passing the preceding checks and approval, from the candidate CWD in the prepared process environment:

```python
from small_binding_v3 import make
from workspace_binding_v4 import prepare, verify
root = make('normal')
prepare(root)
verify(root)
print(root.name)
```

Do not reuse the old path-filter action's preflight.py command: it is intentionally bound to the predecessor. Use the current candidate's verified binding APIs and the exact dataset checks above. Preparation must not refresh expected hashes to conceal drift.

## One execution, with the approved run identity

Set the fresh command process's TEMP/TMP to that run's existing temp directory, retain candidate CWD and approved runtime resolution. Reverify workspace_binding_v4 immediately before invocation. Do not create prompt-gate files manually.

The reviewed CWD-bound launch form is:

```powershell
# OWNER REVIEW ONLY; $run must come from the passing fresh preflight.
Set-Location -LiteralPath 'D:\JARVIS-STAGE6-LIVE\ea85ed4b4ef14769acbe0b5e750aaed2\code'
$py = 'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py -B .\workspace_binding_v4.py verify $run
if ($LASTEXITCODE -ne 0) { throw 'Binding failed; STOP without retry' }
& $py -B -c "import json,sys; import one_run_v4 as w; import failure_preserve_v4 as f; r=w.execute(sys.argv[1],f.cli_policy(sys.argv[1]),approved=True); print(json.dumps(r,sort_keys=True)); sys.exit(0 if r.get('route')=='SUCCESS_FINALIZER_COMPLETED' else 1)" $run
```

The command's approval argument is not owner approval by itself. Do not launch extra D:-named orchestration processes that the existing census would classify as diagnostic workers.

## Expected UAC prompts â€” exactly three, sequential

1. Candidate-local J6AuthorityTraceV3.exe, new run root + launcher PID + launcher creation FILETIME. This is the newly compiled, hash-bound TEST authority observer.
2. Unchanged candidate-local J6StartupTrace.exe, fresh run/detail directory + the same launcher identity.
3. Approved `C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe`, `-NoProfile -File <candidate>\timed_monitor.ps1 -Run <run> -KernelPid <authority PID>`.

Check actual executable, command and publisher context against the reviewed records. No publisher identity is invented here. Unexpected identity, materially different arguments, a fourth prompt, denial or cancellation: STOP; no reissue automatically. Only the observers are elevated. Codex/collector/controller stay non-elevated.

## Required path and PASS criteria

Observers ready â†’ normal small collector/hash passes â†’ original cleanup entry â†’ tracker joins while local helper handles remain held â†’ immutable obligations â†’ authority independently verifies its existing kernel/handle/image/parent evidence â†’ HANDOFF_ACQUIRED â†’ collector validates and records HANDOFF_OBSERVED â†’ successful local closes with pre/post timestamps â†’ Phase A â†’ collector return â†’ independent terminal helper capture â†’ workload census â†’ ordered application/detail/authority shutdown â†’ independent launcher/observer exit verification â†’ final zero-process/zero-trace census â†’ existing completed-evidence checker â†’ new handoff reconciliation + unchanged versioned checker â†’ durable success finalizer and archive verification.

Every exact helper must satisfy acquisition/creation/image/parent verification and acknowledgment before local release. Both hash passes and unchanged metadata are required. No authoritative trace loss, segment/sequence defect, unknown identity, retained-handle/native contradiction, stale binding, late evidence or residual process/trace is allowed. All acceptance cleanup must fit the SAME original twenty-second deadline. No wait for helper STOP before collector return is introduced.

## Failure and post-run procedure

First failure permanently rejects this run. Perform only existing bounded failure cleanup, preserve the three handoff artifacts and any incomplete .pending files, all original telemetry and terminal evidence through the NON-ACCEPTANCE path. No success finalizer after failure; eventual cleanup cannot reverse rejection.

Hash-verify the success/failure archive; copy only finalized nonsecret evidence into a new canonical archive and verify it. Reverify candidate/predecessor/frozen hashes and final cleanup. Report unavailable evidence explicitly. Do not retry, repair the candidate or adjust settings.

If every requirement passes: SMALL_LIVE_INTEGRATION_VALIDATED (small only). Otherwise report the exact failed handoff/identity/deadline/lifecycle/trace/preservation condition, or BLOCKED/INCONCLUSIVE where evidence is unavailable. Historical trace-loss remains UNCONFIRMED unless separately proven.

STOP after this one attempt. No medium, 59.7 GB, protected access, production operation or Stage 6 advancement.

## Directory correction and prospective run boundary

The bound preservation-v4 sibling directory now exists. It contains offline failure-preservation fixtures; do not delete, reuse or interpret them as live evidence. Generate an entirely new live run identity. No prior protected-* fixture, receipt or seal may be reused. Verify this report archive and all successor hashes before preparation. The deferred final-measurement branch must remain absent. Authority and detailed EventsLost > 0 remain failure. Historical ETW loss cause remains UNCONFIRMED. A successful small run permits only an owner-reviewed proposal for medium validation; no automatic advancement.
