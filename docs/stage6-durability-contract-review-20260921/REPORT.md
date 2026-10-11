# Stage 6 — durability architecture and lifecycle contract review

**ACCEPTANCE_CONTRACT_REVIEW_REQUIRED**

No writer/checker/monitor/runtime implementation changed and no sacrificial process campaign was launched in this pass. The explicit contract decision below precedes adoption of a combined architecture. The independent durability work remains authorized, but is not represented here as implemented or validated. This review stops at the owner's requested contract-review boundary.

## Exact blocker and authority

The current request, Part B8, says that an explicit accepted requirement making CIM completeness authoritative cannot be demoted without separate owner review. Its quality standard requires `ACCEPTANCE_CONTRACT_REVIEW_REQUIRED` when the contract needs revision.

That explicit requirement exists in the owner's earlier instructions:

1. [Cleanup-checker approval, C5](</C:/Users/jonny/.codex/attachments/6ca20665-0e62-480f-a0e6-015a78999e74/Pasted text.txt:154>): “Kernel exit evidence must NOT replace the existing process-event START/STOP requirements.” It further says: “Kernel trace is independent ground truth, not a substitute for application-level event evidence.” Missing application STOP must fail even with complete kernel evidence.
2. [Fresh dual-evidence approval, Phase C](</C:/Users/jonny/.codex/attachments/d4604b3d-f2a6-443e-a1a7-9e6a12a80b5c/Pasted text.txt:117>): “Application events, kernel events and retained handles must all map to one unambiguous process identity.” Phases E/F/G require one application START and STOP per tracked identity and reject missing counterparts.
3. [Recorded dual-evidence design](</C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-dual-cleanup-20260920/DESIGN.md:17>) preserves both independently persisted application events. This was an acceptance requirement, not merely optional telemetry.
4. The inspected current `cleanup_checker.py` enforces this at lines 31, 61–62 and 88: application collector health; `INDEPENDENT_EVENT_INSTANCE_IDENTITY_UNPROVEN`; `UNKNOWN_APPLICATION_LINEAGE`; `APPLICATION_START_STOP_INCOMPLETE`.

**Classification: ESSENTIAL_AUTHORITATIVE_LIFECYCLE under the current acceptance contract.** This describes its normative role, not a claim that CIM actually carries adequate instance identity. The newer request conditionally permits a different hierarchy; it explicitly withholds permission to silently change this existing requirement.

The old kernel-only 97-identity run was previously blocked for this same requirement. It must not be upgraded retrospectively. Likewise the 21 AMBIGUOUS / 1 UNMATCHED events stay unchanged.

## Concrete contract amendment proposed for owner approval

This is a proposal, not an adopted or validated rule:

- Authoritative process identity becomes capture/boot scope + subject PID + kernel CreateTime + ProcessSequenceNumber, with exact parent sequence/creation and image corroboration. The observed provider exposes these fields; API key equivalences across providers must not be assumed.
- Require actual kernel START and matching kernel STOP for every intended tracked process and descendant. Missing START/STOP, trace loss, duplicate/conflicting identity, unknown lineage, unexpected live process or stale authority remains a failure.
- Require matching retained-handle creation, signaled exit, exit time/code and closure when available. Keep the existing narrowly qualified post-exit acquisition exception; generic access denial or missing acquisition ordering cannot qualify.
- Keep native PE-entry proof mandatory wherever the existing contract requires it for directly controlled processes. Do not demote that requirement to optional telemetry. OS-created helper coverage retains its explicitly reviewed kernel/handle rules.
- Continue independent CIM collection, durable raw-event storage, exact queue reconciliation, internal event tokens and observer-health checks. A dropped captured record, corrupt secondary evidence, collector failure or unexplained queue residue still fails the run.
- Remove only the requirement that every tracked process have exactly one independently instance-bound CIM START and STOP. A CIM event lacking a sufficient discriminator may remain AMBIGUOUS or UNMATCHED without invalidating an otherwise independently complete authoritative lifecycle.
- A positively demonstrated conflict with authoritative identity still fails. An unknown/unclosed helper remains blocking; ambiguous CIM alone must not be used to declare it out of scope. Prove complete tracked scope from launch inventory, kernel lineage, native/helper evidence and retained handles independently.
- Never fabricate a CIM subject key or claim UNIQUE_CORRELATED from one candidate in an incomplete table. Preserve raw event, run-scoped event token, candidate set, exclusions, status, version and any selected identity separately.
- Apply only to new evidence under a versioned TEST acceptance contract. Preserve every old failure and its governing contract.

Approval of this amendment would authorize implementing/testing the revised TEST evidence hierarchy. It would not itself validate PID reuse, authorize a medium/large run, or authorize protected baseline capture.

Likely TEST files: `cleanup_checker.py`, `process_instances.py`, the independent monitor's raw-schema capture, `baseline_finalize.py`, authority-stream reader/writer, and focused fixtures. No production JARVIS changes. The actual source snapshot under review is `D:\JARVIS-STAGE6-LIVE\0febafa860ad4fc1aee8d72669c3484a\code`; it remains an unaccepted diagnostic copy.

## Proposed durable-segment design — not implemented

Use one canonical ingestion order and one active writer. Preserve the 65,536 ingestion-item limit and byte bound; derive an additional finite segment-finalization budget from measured service rates rather than treating it as free capacity.

| State | Required evidence / ownership |
|---|---|
| RECEIVED | Admission recorded under bounded queue ownership; a rejected record makes the run permanently ineligible. |
| SERIALIZED | Global sequence assigned; immutable encoded bytes; no persistence claim. |
| WRITTEN | Successful handoff of the complete batch to OS/file cache. A buffered `FileStream.Write` alone may leave bytes in managed buffers; implementation must either disable managed buffering with bounded explicit batching or track that additional state and drain it before using this label. |
| SEGMENT_CLOSED | Logically sealed: no further record append is permitted. This is **not** an OS-handle close. Writer relinquishes the original stream and immutable metadata in one ownership transfer. |
| DURABLY_COMMITTED | Finalizer exclusively owns that original open stream and successfully performs the required `Flush(true)` before releasing its handle. No flush under the producer lock. |
| HASH_VERIFIED | Verify the durable segment's byte count, sequence range/count and actual-byte SHA-256 against the writer's expected digest. Do not equate an incremental digest alone with a reread verification. |
| MANIFEST_COMMITTED | All segments satisfy the previous states; ordered complete manifest is written exclusively, flushed durably, hash-verified, and accompanied by a final eligibility seal. No seal before all conditions pass. |

A safe candidate is exclusive transfer of the **same original handle**, not close/reopen-and-assume-durability. The finalizer may receive an exclusively owned read/write stream opened with share-read only, with the writer unable to access it after transfer. That enables post-flush readback on the same handle without path substitution. Verify thread handoff/memory visibility and deny second-owner use in focused tests; FileStream must not be used concurrently.

Microsoft documents `Flush(true)` as flushing intermediate buffers to disk. Windows `FlushFileBuffers` requires a write-capable open handle and reports errors. Closing a handle alone is not the selected durability proof. See [FileStream.Flush](https://learn.microsoft.com/en-us/dotnet/api/system.io.filestream.flush?view=net-10.0), [FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers), and [CloseHandle](https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-closehandle). These APIs support the proposed approach; this pass did not experimentally validate handle transfer or power-loss behavior.

The finalizer must have bounded queued **and in-service** segment count/bytes/handles. Acquire a finalization credit before transferring a segment. If unavailable, propagate bounded backpressure; admission exhaustion or any failed transfer/flush/hash is sticky failure. Do not lose ownership or double-close a handle on the failure path. Finalizer output contains metadata only; it cannot alter record bytes. A single ordered finalizer is the smallest starting candidate; asynchronous completion order must never define record order.

Compare 8/16/32 MiB sacrificial segment candidates with record/time caps held explicit. No segment size or backlog bound is selected as validated. Measure sustained durable service, not just fast cache writes. The old measurements show that moving flush to another worker can absorb a burst but cannot fix a sustained service deficit by itself. No unlimited pending segments and no unbounded wait at finalization are permitted. Keep all existing heartbeat/process/observer deadlines; reconcile the existing 5-second writer-close condition with the required finalizer closure before implementation rather than silently extending it.

Writer/finalizer/host crash, unfinished active segment, pending commit, hash failure, manifest failure or missing final seal means **RUN NOT ACCEPTABLE**. Partial segments remain diagnostic evidence. A process-crash test is not proof of physical power-loss tolerance or storage-controller behavior. No heuristic reconstruction or promotion of recovered partial evidence.

## Required focused validation after the contract decision

Use new D: run directories and sacrificial bytes only. Preserve all failures. Before integration:

1. Prove exclusive original-handle handoff, no append after transfer, ordering and correct WRITTEN versus durable counters; verify actual bytes and sequence ranges after finalization.
2. Exercise all requested failure cases: write/partial batch, rotation, transfer, finalizer death, delayed/failed flush, failed hash, bounded backlog, writer crash, finalizer crash, failed manifest, simulated disk full and corrupt closed segment. No acceptance seal on failure. Real host power loss is not part of this scope.
3. Test sizes and bounded batches, then 50k/75k/100k and justified margin with representative records. Measure active writer and durable finalizer service separately, all queue/backlog high-waters, lock wait/hold, rollover/flush/hash maxima and rejected admissions. Both queues must remain finite and all admitted bytes durable before eligibility.
4. Capture the complete actual CIM schema independently, plus kernel provider/version and subject fields. Obtain fresh real canonical matches with native/handle ground truth; exercise actual PID reuse without altering process identifiers and preserve inconclusive attempts. Never substitute historical reuse for fresh acceptance.
5. Under the approved revised contract, test missing kernel evidence/loss/conflicts, handle and native mismatches, qualified post-exit cases, secondary ambiguity/unmatched/disagreement, and preservation of every raw event. A unique secondary correlation must be justified or remain unresolved.
6. Only after both independent parts pass, wire the real TEST collector/checker/finalizer, run focused integration and bounded readiness stress with the actual health callback (not the previous diagnostic no-op), unchanged deadlines and full cleanup/archive verification.

Then stop at MEDIUM_INTEGRATION_READY and present the exact medium procedure for review. No 59.7 GB data or protected VM access.

## Mandatory report (53 items)

All numerical performance/identity facts below are **previous preserved evidence reverified this pass**, not new test results.

| # | Item | Disposition |
|---|---|---|
| 1 | Current durability semantics | Existing `persisted` advances after Write + incremental hash, before segment durable flush. It must not be interpreted as per-record durable commit. Final manifest follows writer completion. |
| 2 | Current hot path | `AuthoritativeEvents.Publish`: gate, serialize/encode/admit. `WriteLoop`: dequeue, Write/hash, counters; rotation executes Flush(true), Dispose, digest/metadata inline. `Finish`: join, manifest Write/Flush(true). EventTap adds secondary records; no per-record console or manifest rewrite. |
| 3 | Durable flush timing | Prior margin run: 2.531 s cumulative of 2.899 s total. Later 100k/s test max 1.505 s in one durable flush. Not attributed to a specific driver. |
| 4 | Lock timing | Prior unpaced producer ~228 ms, writer lock wait ~210 ms. Bounded dequeue experiment reduced wait to ~7 ms but still overflowed. |
| 5 | Selected segment lifecycle | Proposed seven states above; no implementation/adoption in this review. |
| 6 | Active writer ownership | Proposed single logical writer, sequence before persistence, exclusive active segment. |
| 7 | Finalizer ownership | Proposed exclusive original-handle transfer, no appends after logical closure; not yet experimentally proven. |
| 8 | Batching | Previous experiment not adopted. New byte-batch design awaits measured benefit/correctness. |
| 9 | Segment size | Existing 8 MiB; proposed comparison 8/16/32 MiB, no newly accepted size. |
| 10 | Finalizer bound | Not selected. Must bound queued + in-service count/bytes/handles and prove service margin. |
| 11 | Crash semantics | Any unproven durable record or incomplete final seal rejects run; partial evidence retained. |
| 12 | Durability failure injection | NOT RUN this pass; 14-case plan above. |
| 13 | Sustained writer rate | Not proven. Prior 50k/s for 3 s passed; other 75k/100k/121.5k trials failed. |
| 14 | Finalizer rate | No separate finalizer exists; NOT MEASURED. |
| 15 | Queue high-water | Prior hard exhaustion at 65,536 items; bound unchanged. |
| 16 | Finalizer backlog high-water | N/A — proposed only. |
| 17 | Max durable flush | Prior measured 1.505 s, not a bound on future latency. |
| 18 | Rejected admissions | Six prior writer trials each rejected one; no new admissions/runs. |
| 19 | Sequence gaps | Prior completed admitted prefixes verified zero gaps; rejected admissions still invalidate run. |
| 20 | Raw CIM fields | Documented full schema includes PID/parent/name/session/SID/security descriptor/TIME_CREATED, STOP ExitStatus. Existing saved observer retains only subset plus receipt/queue fields. Full actual-property capture NOT performed anew. |
| 21 | CIM discriminator | No stable process-instance key in inspected available schema/subset. CIM CANNOT BE AUTHORITATIVE FOR PROCESS INSTANCE IDENTITY BY ITSELF on this evidence. No claim about every possible Windows provider/version. |
| 22 | Kernel fields | Preserved START v4/STOP v2: subject PID, CreateTime, ProcessSequenceNumber; parent sequence on START; ExitTime/code on STOP. |
| 23 | Kernel key | Subject ProcessSequenceNumber observed. Do not conflate it with an unverified emitter ProcessStartKey or unrelated API sequence. |
| 24 | Retained fields | Creation/exit FILETIME, PID, image where obtainable, handle signal, exit code, closure evidence. |
| 25 | Canonical identity | Proposed scope + PID + creation FILETIME + subject kernel sequence; parent identity separate. |
| 26 | PID reuse | Historical kernel reuse preserved; no fresh reuse campaign this pass. |
| 27 | Positive unique identity | Previous 16 exact kernel/native/handle agreements; zero independently proven CIM instance bindings. No fresh acceptance claim. |
| 28 | False unique matches | None selected in previous diagnostics; general false-match guarantee not validated. |
| 29 | Native PE role | Keep required controlled-process entry proof; no downgrade to optional evidence. |
| 30 | CIM role | CURRENT: mandatory dual-evidence identity-level counterpart. PROPOSED: independently collected secondary consistency channel. |
| 31 | Contract classification | ESSENTIAL_AUTHORITATIVE_LIFECYCLE. Demotion requires explicit owner amendment. |
| 32 | CIM unique correlations | Zero proven in previous diagnostic; no new attempt. |
| 33 | CIM ambiguous | 32 previous fresh diagnostic events unresolved; historical 21 remain ambiguous. |
| 34 | CIM unmatched | Zero in previous 16-probe set; historical one remains unmatched. |
| 35 | Identity failure injection | NOT RUN; existing acceptance semantics unchanged. |
| 36 | Evidence hierarchy | Proposed, not adopted: kernel instance/lifecycle + required handle/native corroboration; independently healthy CIM secondary; bounded tap/resource telemetry secondary. |
| 37 | Authoritative capture | Proposed sequence-complete, zero-rejection, durably sealed/hashed stream; not just WRITTEN. |
| 38 | Authoritative lifecycle | Proposed complete kernel scope plus required corroboration. Current dual-source requirement still applies pending approval. |
| 39 | Tap role | Existing bounded secondary view, not completeness authority. |
| 40 | Integration tests | NOT RUN — contract review boundary. |
| 41 | Medium readiness stress | NOT RUN / NOT READY. |
| 42 | Max heartbeat | No new observer. Previous identity diagnostic 1.2544289 s; unchanged 10 s criterion. |
| 43 | Deadlines | Unchanged. No new timed campaign. Prior driver clock-origin defect remains preserved and distinct from historical delays. |
| 44 | Finalization | No new acceptance finalization. Only review-evidence archive finalized and verified. |
| 45 | Cleanup | Read-only host snapshot: zero matching diagnostic/VirtualBox processes; zero diagnostic trace sessions. No helpers launched. |
| 46 | Archive | Previous 382 members reread/hash-verified. New review archive receipt records its own count/hash. |
| 47 | Candidate hashes | 116 frozen + six other checks unchanged; every archived current source/evidence payload also matches. |
| 48 | Protected VM | NOT ACCESSED. No protected/configuration hashing. |
| 49 | Production | UNCHANGED; no production operations. |
| 50 | Historical event status | 21 AMBIGUOUS / 1 UNMATCHED unchanged; 97-run remains kernel-only historical. |
| 51 | Historical cause | Delay causes UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED. |
| 52 | Next gate | Owner review of the exact TEST contract amendment above, then independently prove durability and revised identity architecture before integration. |
| 53 | Final status | ACCEPTANCE_CONTRACT_REVIEW_REQUIRED. |

## Preservation and rollback

`preservation.json` records reference snapshots/hashes, all previous archive source hashes and current verification. Original source, evidence and user attachments were read only. New files exist solely in this new review directory and its separate verified evidence archive. There is no runtime/checker correction to roll back. Leave all old candidates and failures immutable.

No blanket administrative authority or UAC change is requested. The owner decision needed is narrowly about TEST acceptance semantics, not production or VM permissions.
