# Two-phase implementation — preservation complete, ordering boundary found

TWO_PHASE_CLEANUP_CONTRACT_CONFLICT

The prospective two-phase contract is approved. Implementation has NOT started. The conflict is between that contract and the current live shutdown control path, not a claim that two-phase cleanup is intrinsically unsafe.

## Preservation first

The previously blocked diagnosis archive was retried under the owner's existing explicit archival authorization. It completed with six members verified; SHA-256 a3690392bcc2b9e843c15b7eca01bf01f9a21b68069c43b6bc3e1cf8745ee318. Original ARCHIVE_BLOCKED.md remains unchanged as historical evidence; an exclusive archive receipt records the successful retry. No UAC or Administrator token was requested.

The contract review and its integrity record are preserved in this new canonical boundary-review archive, along with the original owner approval and inspected source hashes. Existing failed live-run evidence remains failed.

## Exact conflict discovered before editing

Candidate: D:\JARVIS-STAGE6-LIVE\2d922197cf7d4bb098d8da6e070cbff2\code.

- small_launch_v2.ps1:33 returns from RunCollector. Its finally block at lines 37–44 immediately writes app-stop, waits for application exit, writes detail/etw-stop, waits for detailed observer exit, writes etw-stop and waits for the authority tracer. There is no conditional gate proving the selected helper's terminal evidence was captured before those stop requests.
- authority_trace.cpp:56 samples retained handles internally. Lines 72–73 leave the collection loop on etw-stop (or the existing limit), then flush/stop tracing and join. Lines 75–77 serialize the complete per-instance handle/signal/closure result and write etw-result.json only afterward.
- Thus waiting for the complete current result before issuing stop would wait for an output whose publication itself depends on stop. Conversely, retaining the current unconditional stop sequence and rejecting incomplete evidence afterward can fail closed, but does NOT implement the separately required rule that observers remain active until required terminal evidence is captured.

This does not claim there is no potentially reusable intermediate channel anywhere in the system. The inspected shutdown path has no validated terminal-readiness gate, and current complete results cannot be used as that pre-stop gate. Selecting/proving a different live channel or adding a receipt is further coordination design, not a safe assumption.

The latest authorization lists separate collector, tracker, fresh-run binding, verifier, finalizer and checker adapter/interface copies. It does not explicitly authorize changing launcher stop sequencing or native authority-tracer publication. The preceding review also required returning for review if current telemetry cannot prove handoff/continuity. I have not interpreted checker-interface authorization as permission to modify these lifecycle controls.

## Deadline constraint

The owner's latest text requires Phase B proof to complete within one absolute 20-second window starting at the existing cleanup entry, including the stated completion/census obligations. No later fresh 20-second timer, enlarged observer wait or backdated completion is permitted. Existing 60/30/30-second launcher waits are maximum safety waits, not permission to satisfy this new absolute deadline late. A proposed coordinator must enforce the earlier applicable deadline and preserve failure evidence; it cannot hide a timeout by running longer.

## Minimum next design decision — not implemented

Authorize a narrowly scoped TEST launcher/observer coordination review to establish:

1. How a read-only, exact-run/process-instance terminal-ready proof is available while the independent lifecycle observer is still running. Prefer an already validated channel if one can be demonstrated; otherwise identify an explicit minimal observer receipt change for separate approval.
2. How the launcher withholds stop requests until that proof is verified, while retaining bounded failure cleanup and the original absolute deadline.
3. How collector local-handle release, externally retained handle ownership, kernel STOP, observer shutdown, complete durability and final census are ordered and bound without weakening any proof.

No native change or new authority is proposed as implicitly approved. If a safe existing-channel solution is established, document its exact files and tests before implementation. Do not increase thresholds, omit the final census or relabel pending as PASS.

## Work not performed

No candidate or checker modification, implementation test, live validation, UAC, process launch/termination, VM access, production operation, backup/restore, medium/large campaign or new acceptance seal. No live census was run during this read-only boundary inspection; previous cleanup evidence is historical, not a fresh claim.

Required two-phase focused tests have NOT RUN because implementation stopped before source changes. Syntax checks of unchanged implementation were not repeated. No claim of TWO_PHASE_CLEANUP_IMPLEMENTED_AND_FOCUSED_TESTED.

Historical failure and 21 AMBIGUOUS / 1 UNMATCHED classifications unchanged. Historical causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

STOP for owner review.
