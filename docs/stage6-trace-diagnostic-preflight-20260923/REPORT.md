# One trace-loss diagnostic: preflight blocked

Primary status: **BLOCKED**

Diagnosis status: **TRACE_LOSS_CAUSE_UNCONFIRMED**

No live attempt, UAC request, observer, collector, dataset preparation or fresh D: run directory was started. This is a static preflight rejection, not a new trace-loss result. The authorized single attempt has not executed. No checker or success finalizer was invoked.

## Exact blocker

The validated successor is not relocatable unchanged under the required fresh-workspace procedure:

- `candidate/baseline-allowlist.json:3` approves only `D:\JARVIS-STAGE6-LIVE\7f204e14c90a497a8476be0e9927e074\code\small-synthetic`.
- `candidate/small_binding_v3.py:29` calls `prepare(str(CODE/'small-synthetic'))`. In a new workspace this is a different path.
- `candidate/baseline_contract.py:19` rejects that path with `Unapproved root`, before inventory or run creation. Using the old source is also incompatible with current-workspace containment. No bypass was attempted.
- `candidate/small_launch_v3.ps1:21` additionally imports `J6OwnedEntry.dll` from the previous workspace. The native bridge itself derives its collector script and working directory from the supplied run root (`owned_entry.cpp:83` onward); the old DLL reference does NOT establish that the old collector script would run. It is an external candidate dependency requiring explicit reconciliation.

Both binding files are part of the frozen 217-file manifest. Rewriting them would change the candidate, contrary to this attempt's unchanged-candidate requirement. The prior report's fresh-copy procedure missed these fixed bindings. No ETW runtime defect has been inferred from this finding.

The preserved wrapper also pins its old candidate/preservation paths in `failure_preserve_v1.cli_policy()`. The earlier procedure anticipated a new policy binding; any future preparation must explicitly reconcile that invocation and include the two new diagnostic sidecars in preservation coverage. The existing wrapper/tools were not changed or executed as a live controller.

## Read-only verification

`verify.py` was executed with Python `-B` in the non-UAC host command context. It reads only documented candidate/evidence/tool paths and uses the existing read-only process/trace census. It writes only this action's preflight record.

- Successor: **217/217 hashes verified**.
- Original candidate: **216/216 hashes verified**.
- Previous failed run: **83/83 files verified**, including size, modification time and file identity.
- Preservation tools: **4/4 verified**.
- Original preserved inputs: **482/482 verified**.
- Telemetry archive: **299/299 members verified**, archive and manifest hashes matched.
- Previous failed-run archive: **105/105 members verified**, archive and manifest hashes matched.
- Host census at `2026-09-23T03:32:39.349052Z`: **0 matching processes, 0 trace sessions, 0 unknown entries**. VirtualBox was not running in that census.
- Candidate/checker changes: **none**. Protected VM/configuration access: **none**. Production changes: **none**. No protected-file hash check was performed or claimed.

Successor manifest SHA-256: `4d4c402def6435a665bffb3878dd425cc10049af64e8d2e5cfae6cf5d6452182`.

`preflight.json` records absolute supporting paths and exact hashes. All prior evidence is preserved. This new report/archive is NON-ACCEPTANCE evidence only.

## Requested live measurements

Authority/detail session IDs, current loss counters, sampling windows, consumer CPU, slow spans, buffer pressure, callback rates, queue progression, terminal receipts, lifecycle timeline, acceptance census and live finalization: **NOT RUN / NOT AVAILABLE**. There is no new loss-free result. Historical authority loss 13 and detail loss 120,281 remain preserved historical observations.

For this nonexecuted attempt, TRANSIENT_ETW_BUFFER_EXHAUSTION, CONSUMER_CALLBACK_STALL, METADATA_OR_LOCK_STALL, EVENT_RATE_BURST, WRITER_BACKPRESSURE, DISK_PERSISTENCE_PRESSURE, CPU_SCHEDULING_DELAY and OTHER_EVIDENCED_CAUSE all remain **UNCONFIRMED as explanations of historical loss**. No new causal measurement exists; this does not erase prior supporting observations.

## Proposed next action — owner review only

Authorize narrow TEST relocation/binding preparation in a separate candidate: bind the sole small synthetic allowlist entry to the fresh workspace; load the identical hash-verified native DLL from that candidate; reconcile the fresh preservation policy/invocation and sidecar allowlist. Preserve all guards, schemas, deadlines, tracing settings and frozen sources. Add focused offline relocation/binding and preservation tests, re-freeze/hash/archive, then present the concrete one-run procedure. No live retry or correction is authorized by this report.

Rollback: retain the present candidate and historical evidence unchanged; the only additions are this preflight report, verification script and non-acceptance archive. No runtime rollback is needed.

HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
