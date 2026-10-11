# Proposed single small diagnostic — OWNER REVIEW ONLY

No execution is authorized by this document. No UAC prompt has been issued.
Scope: one fresh normal-case run, 12 synthetic files / 786,432 bytes, no retry.
Historical ETW-loss cause remains UNCONFIRMED.

## Preparation and binding (before any UAC)

1. Verify this action's archive receipt, candidate `witness-source-v1.json`, all
   candidate member hashes, unchanged predecessor manifest and latest failed-run
   archive. The current candidate is an OFFLINE preparation directory on C:;
   do not launch it there or reuse either predecessor's mutable run directory.
2. Use the existing reviewed fresh-workspace procedure to copy the candidate to
   one new `D:\JARVIS-STAGE6-LIVE\<fresh-workspace-id>\code` directory. No rebuild,
   source edit, provider change, buffer change or timeout change. Only the
   existing explicit synthetic-root/preservation-root rebind is permitted.
   Preserve a byte-for-byte before/after inventory of that rebind. If existing
   preparation cannot bind these additional witness artifacts without another
   code/contract change, STOP before UAC for owner review.
3. Include the witness source, exporter, analyzer, preservation module and rebuilt
   observer binaries in the frozen candidate manifest. Finalize both the existing
   `small-source-v3.json` and the witness's `witness-source-v1.json` before launch.
   The latter is the candidate-manifest SHA-256 exported in the sidecars; it must
   cover the observer binaries and integration sources, exclude itself, and never
   be regenerated after seeing results. Record expected binary SHA-256 separately.
4. Verify all 12 dataset files, their exact hashes, total bytes, canonical Windows
   relative paths, no duplicates/escapes/reparse points, candidate-local DLL and
   existing runtime bindings. Apply the existing controlled per-process PATH,
   PSModulePath and run-local TEMP/TMP policy, without permanent environment edits.
5. Create exactly one fresh `protected-<32 lowercase hex>` run through the existing
   `small_binding_v3.make('normal')`, `workspace_binding_v4.prepare` and `verify`
   procedure. Pin its workspace-binding digest and source manifest digest.
6. Require zero matching diagnostic processes and zero diagnostic trace sessions;
   VirtualBox remains closed. Do not inspect/hash the protected VM/configuration.
   Verify the four planned sibling sidecar paths do not exist. Preserve preflight
   results and a create-new one-attempt launch record. Any mismatch: STOP, no UAC.

## Exactly three sequential UAC prompts, after explicit owner approval

1. Kernel authority observer: candidate-local `J6AuthorityTraceV3.exe`.
2. Detailed startup observer: candidate-local `J6StartupTrace.exe`.
3. Application-event observer: the existing bound PowerShell executable executing
   candidate-local `timed_monitor.ps1` with its existing reviewed arguments.

Each executable/hash, command line, fresh run path, parent identity and publisher
context must match the reviewed launch binding. Unexpected/fourth/materially
different prompt or canceled prompt: STOP; no automatic reissue.

## Execution and unchanged acceptance rules

Use the existing one-run route (`one_run_v4.execute` and existing failure policy)
with the fresh binding. Run normal case only; both small hash passes and metadata
checks must agree. Keep authority and detailed providers/buffers, telemetry,
heartbeat <10 seconds, existing process deadlines, helper handoff, two-phase
cleanup and ONE original 20-second absolute cleanup deadline unchanged.

The witness records process START/STOP callbacks only. It observes the actual
parent/instance decision; it does not defer, retry, reorder or rescue selection.
Existing ETW-loss/sequence/identity/handle/native-entry failures still reject the
run. Local witness sequence is diagnostic and cannot repair authoritative gaps.

After each tracing thread joins, its witness exports to a sibling of the run tree:

- `<code>\<run>.authority-lifecycle-witness-v1.json`
- `<code>\<run>.detailed-lifecycle-witness-v1.json`
- on export failure, the corresponding
  `<run>.<channel>-lifecycle-witness-export-failure-v1.json`, if writable.

No witness file is placed inside the frozen checker/finalizer's artifact tree.
These sidecars are NOT an acceptance seal. Export adds post-join work within the
existing lifecycle; if it prevents timely cleanup, that run fails. No deadline
extension/reset is permitted.

Require terminal helper receipt, pre-shutdown workload census, ordered observer
shutdown, independent launcher/observer exit proof and final zero-process/zero-trace
census under the existing rules. Run the unchanged checker/finalizer only when
its existing prerequisites pass. On the FIRST failure, permanently reject and
use the existing bounded NON-ACCEPTANCE failure route; no success finalizer/retry.

## Post-quiescence diagnostic analysis and preservation

Preserve both sidecars even if the run failed. Once process/trace cleanup is proven,
use the new bounded, separate non-acceptance archive helper (substitute the single
preflight-recorded paths; do not invent a second run):

```powershell
& $BoundPython -B "$Code\preserve_lifecycle_witness_v1.py" --run-root "$RunRoot" --archive "$ReportRoot\lifecycle-witness-nonacceptance.zip" --first-failure "$PreservedFirstFailure"
```

`$PreservedFirstFailure` must retain the original failure verbatim, or explicitly
state NONE OBSERVED for a successful run. Missing sidecars/export-failure markers
remain WITNESS_INCOMPLETE. Archive creation is exclusive and hash-verified; it
cannot change the main run's disposition.

Bind each channel's sidecar to expected fresh run/session, candidate-manifest hash,
observer binary hash and frequency. Check capacity/overflow, complete consecutive
witness sequence and quiescence. Unknown/missing/stale binding fails closed.

Prepare offline normalized target inputs from the run's independent creator/tracer
handles and native records: PID AND creation/exit FILETIMEs, evidence SHA-256,
conservative independently derived START/STOP QPC windows, and process sequence
where known. Preserve clock-domain uncertainty; do not invent tight timing bounds.
List all eight roles and any potentially overlapping reused-PID identities.
Unresolved identity stays unresolved. Never bootstrap these independent windows
from the witness observation being tested.

For each channel run the analyzer with the corresponding expected binding, targets
and successful loss-counter samples in the same clock domain:

```powershell
& $BoundPython -B "$Code\analyze_lifecycle_witness_v1.py" --witness "$Sidecar" --binding "$ExpectedBinding" --targets "$IndependentTargets" --loss "$LossSamples" --output "$FreshAnalysisOutput"
```

Inputs/analysis hashes and normalization provenance must be archived alongside the
separate sidecar archive. The analyzer does not itself attest the provenance of
externally normalized targets: unresolved/missing independent records cannot be
replaced with PID-only inputs. Report START/STOP presence, disposition, actual
parentKnown/instanceKnown/admitted flags and loss-window overlap for each role.
No callback observation alone proves a lost payload or historical root cause.

Verify final source/binary/dataset preservation and both archives. Report the first
failure, any missing diagnostic evidence and complete cleanup. A clean diagnostic
cannot retroactively pass the prior failed run or qualify Stage 6.

## Stop and result

Stop after this one attempt, PASS or FAIL. No correction, retry, medium, 59.7 GB,
protected baseline, VM operation or production operation follows automatically.

Possible run results: TRACE_DIAGNOSTIC_RUN_PASS, TRACE_DIAGNOSTIC_RUN_FAILED,
BLOCKED, PRESERVATION_FAILURE or INCONCLUSIVE. Diagnostic results remain separate:
callback disposition established for a uniquely correlated observation, identity
unresolved, CALLBACK_NOT_OBSERVED, or WITNESS_INCOMPLETE. ETW cause remains
UNCONFIRMED unless the new evidence actually proves it.
