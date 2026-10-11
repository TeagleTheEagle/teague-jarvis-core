# Stage 6 TEST acceptance amendment — kernel process-instance authority

Contract ID: `STAGE6-TEST-KERNEL-INSTANCE-20260921-v1`

Status: **OWNER-APPROVED CONTRACT; IMPLEMENTATION / QUALIFICATION PENDING**

Authority: the owner's “APPROVED — narrowly scoped TEST acceptance-contract amendment” message following the 2026-09-21 durability/identity review. All ten conditions apply. This document records that decision; it does not claim that the proposed writer, kernel evidence persistence or revised checker has passed validation.

## Scope and precedence

This amendment governs only future Stage 6 TEST/validation evidence explicitly identifying this contract version. It narrowly supersedes the former C5/dual-evidence requirement that every tracked process have independently instance-bound CIM/application START and STOP counterparts. All unrelated acceptance requirements remain in force.

Historical records retain their original contract and result. In particular, **21 AMBIGUOUS / 1 UNMATCHED** remain unchanged. Historical probe, sampler and storage delay causes remain **UNCONFIRMED**. **HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.** No earlier failure becomes a PASS through this amendment.

Reference: [immutable pre-approval review](../stage6-durability-contract-review-20260921/REPORT.md). That report correctly remains a historical proposal awaiting approval at its own timestamp; it must not be rewritten to imply approval preceded the owner's decision.

## Exact acceptance semantics

| ID | Required rule |
|---|---|
| K1 | Kernel START/STOP is the authoritative process-instance lifecycle source **only after** completeness, independent persistence verification, capture-sequence integrity and process-instance uniqueness are demonstrated. Absent proof means INCOMPLETE/FAIL, never presumptive acceptance. |
| K2 | Bind each instance to capture/boot scope, subject PID, kernel creation identity and kernel process sequence, corroborated by image and parent-instance identity. PID alone, event-arrival time, CIM TIME_CREATED, or a nearest-time lookup is insufficient. Provider field semantics must be verified; unrelated provider keys are not assumed equivalent. |
| K3 | Prove tracked scope independently from explicit launch inventory and kernel parent/child lineage, corroborated by the existing native/helper and handle evidence. Every in-scope instance requires a genuine matching kernel START and STOP. Unknown or unclosed helpers block acceptance; CIM ambiguity cannot justify excluding them. |
| K4 | Any kernel/ETW loss, duplicate/conflicting instance, missing lifecycle edge, sequence gap, missing/corrupt segment, incomplete capture, unresolved authoritative identity or positive lifecycle contradiction fails closed. Zero ETW loss counters alone do not prove complete durable evidence. |
| K5 | Capture sequence means the authoritative writer's contiguous admitted-record order within this capture, not consecutive numeric Windows ProcessSequenceNumber values. ProcessSequenceNumber identifies an instance; gaps in global OS process numbering are not automatically evidence-record gaps. Rejected admissions and missing required records remain failures. |
| H1 | Retained handles remain an independent channel. Preserve creation identity, image corroboration, kernel-signaled exit, exit time/code and closure checks. Any contradiction fails. Keep only the existing narrowly qualified post-exit handle-acquisition exception; do not widen it to generic access denial, missing ordering or missing evidence. |
| N1 | Validated native PE-entry evidence remains independent and mandatory wherever the accepted controlled-process contract requires it. Preserve entry, instance and temporal checks. Missing required entry evidence or a contradiction fails. Existing explicitly reviewed OS-helper rules are unchanged. |
| C1 | CIM/application START/STOP collection remains enabled, healthy, independently captured and durably persisted. Preserve raw records, unique run-scoped event tokens, exact queue-entry semantics, persistence receipts, queue reconciliation and observer cleanup. Collection failure, lost captured records, corrupt supporting evidence or unexplained queue residue still fails. |
| C2 | Every correlation retains its raw event, candidate set, rationale and explicit result. AMBIGUOUS and UNMATCHED remain visible and unmodified. Never manufacture an instance discriminator, force a unique match or discard troublesome events. A UNIQUE correlation requires independent event-bound evidence. |
| C3 | Remove only the requirement for exactly one uniquely instance-bound CIM START and STOP per tracked process. AMBIGUOUS/UNMATCHED CIM, or lack of an independently bindable counterpart, alone does not fail an otherwise fully qualified authoritative lifecycle. This is not permission to disable collection, omit captured records or fabricate completeness. |
| C4 | A positively established CIM contradiction remains blocking. An ambiguous candidate disagreement is not asserted as a proven contradiction; retain it explicitly. If scope/identity cannot be resolved independently, K1–K4 still block acceptance. |
| D1 | Successful acceptance requires proof of persisted bytes, complete ordered segments, hashes and manifest integrity in addition to externally observed process outcomes. The durable-segment architecture remains a design, not an accepted implementation. No final acceptance seal while any required evidence is pending/unverified. |
| G1 | Existing heartbeat, process and observer deadlines, queue limits, fail-closed behavior, cleanup and production/protected-source boundaries remain unchanged. No medium/large run, 59.7 GB campaign, protected VM access or protected baseline hashing is authorized by this amendment. |

The event storage transport and process identity authority are distinct: a file named “authoritative” containing CIM records does not thereby become authoritative kernel lifecycle evidence.

## Decision examples (normative requirements, not executed tests)

| Evidence | Required disposition |
|---|---|
| Proven complete durable kernel stream; valid required handles/native entry; healthy durable CIM with AMBIGUOUS/UNMATCHED events | Those CIM correlation results alone do not fail the gate; all other gates must still pass. |
| Same, but missing authoritative STOP or unclosed helper | FAIL. |
| Kernel loss counter nonzero, record-sequence gap, missing segment or hash mismatch | FAIL. |
| Complete reported kernel summary without independently verified persistent evidence | INCOMPLETE / no acceptance. |
| Retained-handle or required native-entry contradiction | FAIL. |
| CIM observer disabled, captured events lost, queue not reconciled, or evidence corrupted | FAIL. |
| Only PID/time-based matching is available for the authoritative identity | FAIL. |
| Historical failed run replayed against the new rules | Not current acceptance evidence; historical result unchanged. |

## Application boundary

This is the adopted normative contract. The frozen legacy checker remains unchanged and still enforces its older, stricter CIM rule. It must not be described as implementing this version, nor may a caller suppress its errors and declare PASS.

Future implementation must use a fresh versioned TEST candidate and explicitly bind the run, checker output and manifest to this contract. It must demonstrate K1–D1 before adopting the revised CIM disposition. Unknown/missing contract versions must not silently select relaxed behavior. No checker integration has occurred in this documentation-only amendment pass.

Changing policy is not qualification of its implementation. Stage 6 and protected-baseline eligibility remain blocked pending the required implementation and evidence.
