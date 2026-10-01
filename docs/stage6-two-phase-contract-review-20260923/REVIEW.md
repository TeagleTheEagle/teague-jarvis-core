# Two-phase cleanup — contract review only

TWO_PHASE_CLEANUP_AMENDMENT_RECOMMENDED

Prospective TEST-only amendment recommended. No implementation, rerun, checker replacement, threshold change, VM access, production operation or archive mutation performed.

## Answers to the ten review questions

1–2. **Current local rule: yes, for every tracked descendant.** No general accepted prose sentence saying literally “all helpers must already be exited before collector return” was located. The approved tracker design explicitly says: “Descendants must still satisfy the original exit/handle-closure conditions and bounds” (stage6-tracker-correction-design-20260923/REVIEW.md:31). It excludes only the collector anchor from allExited at line 27. The concrete enforced requirement is large_collect.py:56–57: call tree.finish(root,20), require supportingEvidenceValid/allExited/allHandlesClosed/threadStopped, otherwise fail before return. evidence_support.py:212–225 performs that wait; line 133 requires every descendant's exit and closure. Thus two-phase helper cleanup is NOT already permitted by that local contract.

The earlier combined contract is compatible with the goal: stage6-small-combined-20260922/CONTRACT.md:15 puts global acceptance after application observer, handles, queues, host cleanup and archive verification. This review recommends amending the local ordering while retaining those global conditions.

3. **A console/helper lifetime can legitimately extend past the collector's internal return decision.** Microsoft documents that a console closes when its last attached process terminates or detaches; it does not promise console-host exit before a particular caller returns. Windows also does not automatically terminate all child processes when a parent terminates. The preserved helper kernel STOP occurs 1.765 ms after collector kernel STOP. This supports the specific ordering conflict; it does not independently establish every Windows mechanism or every historical Stage 6 delay.

Sources: [Closing a Console](https://learn.microsoft.com/en-us/windows/console/closing-a-console), [Terminating a Process](https://learn.microsoft.com/en-us/windows/win32/procthread/terminating-a-process).

4. **Yes, conditionally.** The existing independently running authority tracer has creation-verified retained handles, kernel lifecycle/sequence evidence and final closure records. It can prove post-collector exit without the collector claiming its own or its helper's death. The same preserved instance was captured externally before local cleanup and observed signaled afterward. This is evidence feasibility, not an implemented or validated handoff protocol.

5. **Required identity/binding tuple:** run ID/nonce; declaration and candidate-manifest digests; authority session/capture scope; kernel process sequence; PID; creation FILETIME; normalized full handle-derived image; exact collector parent tuple (session, sequence, PID, creation); observer instance (PID, creation and expected image); QPC frequency/domain and acquisition/query/close/exit times. Bind these through immutable artifact hashes and segment manifests. An image path or digest is corroboration, never a substitute for process-instance identity. Handle numeric values are meaningful only within their owning observer instance.

6. **NO: PID reuse can never satisfy the old helper's exit requirement.** A later process with the same PID is unrelated. The original retained handle, canonical creation and process sequence must agree. PID absence/reuse may aid census interpretation only after original exact-instance exit is independently established.

7. **The complete model can preserve evidence strength, but it changes the accepted local timing/disposition rule.** Local completion becomes PENDING_EXTERNAL_EXIT, never cleanup PASS. Every previously required identity/image/exit/closure check remains mandatory at final acceptance. Direct workers/probes retain their existing cleanup and native-entry rules. This is a narrow explicit amendment, not merely a report-label change or permission to waive missing evidence.

8. **All listed unresolved cases fail closed.** See the failure table below. Eventual cleanup after a failure is preservation evidence only and cannot retroactively pass that run.

9. **Required combination, not alternatives:** independently qualified kernel START/STOP plus exact-instance external retained-handle signal/creation/exit/close evidence plus required creator/native evidence for direct processes plus final read-only process/trace census. Keep raw CIM/application persistence as supporting evidence, with ambiguity/unmatched records explicit. No synthesis of STOP from a handle, no census-only proof, no PID-only inference. The existing separately qualified error-87 post-exit acquisition class remains unchanged; it cannot be used as a new exemption for a still-live helper selected for pending external cleanup.

10. **Ordering:** stop workload admissions → finalize local-owned work/queues/evidence and close local handles → record local component seal/PENDING_EXTERNAL_EXIT → collector actual exit → obtain/verify exact helper external exit (it may already have exited) → stop/drain/join observers and their writers → verify all durable segments and required channels → final read-only process/trace census → complete checker → archive and hash verification → global acceptance receipt/seal. No successful global seal may appear earlier.

## Exact proposed contract text

> This amendment applies prospectively only to Stage 6 TEST validation. Existing failures and historical classifications remain unchanged.
>
> An OS_CONSOLE_HELPER may use two-phase cleanup only when it is independently bound to the exact collector process instance and classified through the approved kernel/handle/image evidence. Other helper classes gain no exemption. Direct probes/workers retain their current creator-owned/native and local cleanup requirements.
>
> Phase A is LOCAL_EVIDENCE_FINALIZED_PENDING_EXTERNAL_EXIT. Stop admissions; finish required local work, internal queues and local-owned writers; durably publish exact instance/image/timing and current process state; close and record every local query/retained handle and stop/join the tracker. A local handle may close while this narrowly classified helper remains live, but closure is not exit proof. The collector must not emit allExited=true, final cleanup PASS or an acceptance seal for that helper. Missing local evidence, failed close/join or a primary workload failure remains FAIL.
>
> Before relying on the external channel, final verification must prove that the approved independent observer acquired and creation-verified its own handle to that exact helper before the collector released its local handle. The observer must continuously retain that handle until confirmed signal/exit observation and record its closure. Acquisition, image, parent, session and run proofs must agree; no name-only or PID-only transfer is accepted. Phase A may record this obligation as pending, but cannot assert an unverified handoff succeeded. Absent sufficient proof, final acceptance fails. No arbitrary new privileged observer or command channel is authorized.
>
> Phase B requires the collector's actual exit from independent kernel/native/retained-handle evidence and the helper's actual exit from the same qualified kernel instance and externally retained handle. Both exit FILETIME and exit code must agree wherever required. The collector's failure code cannot be relabeled success merely because the helper later exits. All direct-process native requirements remain unchanged; OS-created helpers do not acquire a new native-entry exemption for another class.
>
> Preserve the existing 20-second tree-cleanup budget as one absolute deadline, starting at the recorded entry to the local tree-cleanup phase. The pending branch must not restart that budget at collector return, observer pickup or finalizer entry. Helper kernel exit and retained-handle signal observation must both occur within that existing deadline. Preserve the heartbeat <10 seconds, probe 13.6 seconds, independent probe observer 15 seconds and all existing campaign/observer/finalization bounds. The effective permission is the intersection of applicable bounds, never an extension. A late event may be persisted during existing drain, but cannot change late exit/observation into an on-time result.
>
> External kernel/detail/CIM writers must remain active long enough, within their existing bounds, to record required terminal evidence. “Close active writer” in Phase A means collector-owned writers only; it must not prematurely stop independent lifecycle capture. Each independently owned writer/queue closes and seals at its proper phase. Component durability seals are not global acceptance seals.
>
> After all required exact-instance exits, close observers and handles, drain/commit/hash all required segments, preserve raw supporting evidence, and run the final read-only census. Required diagnostic process count and diagnostic trace count must both be zero, obtained by successful enumeration. Unknown, denied, incomplete or contradictory cleanup is not zero.
>
> The versioned checker may issue global acceptance only after every required Phase A and Phase B predicate passes, source/run/artifact binding verifies, the final census succeeds, and the complete archive verifies. The final global acceptance receipt is an independently hash-bound sidecar. Missing/ambiguous evidence, observer death, trace loss, sequence gap, missing segment, out-of-bound termination/observation, failed finalization or residual process/trace causes FAIL or BLOCKED with preserved evidence. No automatic retry or retroactive acceptance.

## External-observer rule and evidence checklist

Use only the already-approved independent authority tracer's query/synchronize handle for this helper, with kernel-derived creation and sequence and a successful handle-derived image while valid. Match all required tuples; verify acquisition-before-local-close, no instance conflict, consistent QPC frequency, exact kernel START/STOP, no trace/sequence/segment loss, signal-before-deadline, agreed exit times/codes, external handle closure and observer exit. Native PE-entry remains required for the collector and other directly created processes; the console helper remains its approved non-native class. Keep tracker and tracer provenance separate; never rewrite the tracer error to claim an image success it did not observe.

The current tracer result exposes acquisition/signal/closure evidence, but the candidate lacks a versioned pending-cleanup record and new-phase verifier. The exact local cleanup-entry timestamp is not recorded in the failed run. This absence forbids retrofitting the proposed 20-second deadline or new semantics to that run. Prospective implementation must record that timestamp and digest-bound pending obligations before completion.

## Failure semantics

| Condition | Required result |
|---|---|
| Helper never exits | FAIL at unchanged absolute bound; preserve evidence and escalate unresolved live state; no implicit kill |
| Exit or retained signal observation after bound | FAIL, even if subsequent cleanup reaches zero |
| Observer dies, loses trace data or fails durable close | FAIL; no alternate PID lookup or replacement observer silently satisfies it |
| Same instance cannot be proven / PID reused | FAIL or BLOCKED; reused process cannot satisfy original identity |
| Identity, parent, image, native, handle or exit contradiction | FAIL; no preferred-channel overwrite |
| Local close/join/queue/writer failure | FAIL before global acceptance |
| Final census denied or unavailable | BLOCKED; counts UNKNOWN |
| Required process or trace remains live | FAIL/BLOCKED; never seal acceptance |
| Archive/hash/source binding failure | FAIL/BLOCKED; no global acceptance receipt |
| Prior run already failed | Remains failed permanently |

## Exact proposed implementation scope — not authorized by this review

Separate TEST candidate only:

- evidence_support.py: explicit eligible-helper/pending records, cleanup-entry/deadline/local-close timestamps, stop/join/local-handle cleanup. Preserve existing default/direct behavior.
- large_collect.py: distinguish local completion pending external proof from final success; keep primary failures and direct-process rules intact.
- tracker_adapter_v2.py and versioned structural/coverage checker: validate the full external proof and unchanged bounds; preserve verification classes and contradictions.
- small_check_v2.py / small_finalize_v2.py: admit final cleanup only after proof, census, durable closure and archive verification; distinguish component and acceptance seals.
- Versioned binding/declaration and focused tests: explicit amendment version, required pending obligations, stale-run rejection and fault cases.
- Launcher only if needed to consume existing phase records and preserve observer shutdown ordering. No new IPC authority, elevated helper, native tracing change or wider lifetime bound is authorized. If current telemetry cannot prove handoff/continuity, return for separate design review.

Before any live attempt, offline negative tests must cover every table row, false pending success, direct-process misclassification and dropped/stale obligations. A future small test must exercise genuine collector-owned helper exit after collector termination. No implementation or test executed during this review.

## Archival and preservation

The local diagnosis report, timeline, source references, scripts and ARCHIVE_BLOCKED.md remain present and readable. This review snapshots their SHA-256/size/timestamps and verifies they do not change during inspection. The timeline is checked against the unchanged failed-run bytes and archive. There was no prior completed archive/digest manifest for the diagnosis bundle itself, so this is not a claim of independently proven byte identity since its initial creation.

Canonical archival previously did not execute because automatic approval review failed: “Selected model is at capacity.” The tool explicitly stated this was review failure, not an unsafe-action determination, and prohibited bypass. No archive retry or mutation occurred in this contract review. A canonical retry remains separately pending successful approval review; no broader filesystem, UAC or security permission is inferred. No new owner authorization for implementation is inferred from this review.

Historical 21 AMBIGUOUS / 1 UNMATCHED remain unchanged. Historical Stage 6 causes remain UNCONFIRMED except the evidence-backed ordering finding for this one run. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

STOP for owner review. No implementation or rerun.
