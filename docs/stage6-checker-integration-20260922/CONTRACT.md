# Versioned small TEST checker integration contract

This gate creates a separate candidate from the frozen reference. The reference is never imported, overwritten or automatically selected after a failure. Only `stage6-checker-input-v2` explicitly selects the new candidate. Unknown, missing, malformed or older version fields reject. No legacy-to-new fallback exists.

Before candidate modification: planned changes are a new strict checker entry point, an unchanged local copy of the validated combined adapter with its qualification import redirected to the pinned local dependency, strict closed input schemas, evidence/archive binding, rule receipts and offline mutation fixtures. No monitor, tracer, worker, production or frozen-checker changes. Initial copied hashes and source paths are in preflight.json.

## Input schema and trust

Envelope fields, all required: `schema` (exact stage6-checker-input-v2), `contract` (exact STAGE6-TEST-KERNEL-INSTANCE-20260921-v1), `adapter` (exact stage6-small-combined-v1), `runId` (identity- plus 32 hex digits), `evidenceRoot` (absolute contained D: directory), `payload` (the existing combined adapter output), and `bundle` (the original persisted inputs reopened by the adapter). Machine-readable closed schemas enumerate every nested field/type in schema.json before checker implementation. No missing-field defaults, unknown object members, bool-as-number coercion, NaN/infinity or duplicate JSON keys. Arrays required by the independent workload cannot be empty. Variable record variants preserve field presence; an empty array alone never establishes a mandatory requirement.

The bundle requires root; authoritative raw events; original durable manifest and writer result; kernel summary; structural independent inputs; complete class coverage inputs; qualification result; CIM raw-linked correlations; launcher/application/native-bridge closure; heartbeat/health records; host cleanup; and manifest path/hash. Required fields are documented mechanically in schema.json, with semantic conditions below. A schema is necessary but insufficient.

The payload retains original run, contract and schema; authoritative records/STARTs/STOPs and canonical scope+PID+creation+sequence identities; complete segment manifest (number, name, bytes, records, first/last sequence, SHA-256, durable states); segment count/range/gaps/duplicates/missing/hash result; explicit class coverage and native entries; raw CIM classifications and queue counts; heartbeat/deadline and observer closure; finalization and cleanup. `acceptanceSealed:false` and `archiveStatus:PENDING` are the original pre-archive values, not failures or final acceptance. This checker binds the separate reviewed acceptance seal and archive; it never edits that payload to manufacture a seal.

Public replay requires the pinned 324-member archive/manifest/seal identities, exact member set, every hash, archived adapter output and raw inputs, and unchanged original files before and after evaluation. Paths come only from that pinned manifest. No caller-controlled arbitrary files, code imports, symlinks, junctions, reparse ancestors, traversal, alternate streams or untrusted archive extraction. This is a bounded offline local evidence gate, not a signed adversarial remote trust system. Future runs need an explicitly reviewed new evidence binding; medium acceptance is not implicitly enabled.

## Semantic rules

1. Reopen segments, validate complete set, hashes, bytes, durable states 0–4 and manifested state 5, contiguous admitted sequence and writer totals. Kernel Windows process-sequence integers are not required to be consecutive.
2. Recompute all canonical identities, START/STOP pairs, kernel loss/closure and retained/native contradictions. Independently declared 16 direct probes plus one direct worker are required; expected inventory must equal the kernel instance set. Unknown helpers fail.
3. Direct probes/workers require creator-owned handle, matching creation and early full image capture before native entry. OS helpers require the approved tracer evidence or the existing narrow error-87 post-exit exception. Observer infrastructure remains separately classified. Missing, contradictory or substituted evidence fails. Post-exit exceptions never count as successful image captures.
4. Check strict typed inputs before calling the validated adapter; compare its entire recomputed result against the submitted payload. Caller-provided PASS summaries cannot override raw rejection. Report explicit DIRECT_CREATOR_CAPTURE, TRACER_HELPER_VERIFIED and QUALIFIED_POST_EXIT_HELPER receipts; missing/contradictory inputs reject.
5. CIM stays secondary and persisted. Recompute current real CIM correlations using the unchanged process-instance implementation: it cannot infer UNIQUE from these raw events. Preserve all ambiguous/unmatched entries. A proven contradiction blocks. A separate policy-unit test may demonstrate the conditional UNIQUE rule with stipulated event-bound proof; this is not a new event-binding mechanism and cannot admit fabricated UNIQUE evidence through public replay.
6. Heartbeat and age <10 seconds; zero deadline violations; all queues drained, threads/observers closed, manifests complete, zero matching processes/traces. No threshold changes.
7. Public PASS requires immutable original archive binding, final source preservation and independent host cleanup. Fixture rule success is labelled RULES_SATISFIED_NOT_ACCEPTANCE and cannot seal a run.

## Preservation

Historical 21 AMBIGUOUS / 1 UNMATCHED and the initial 30/31 fixture result remain unchanged. Historical causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED. No protected VM/configuration access and no production changes are authorized. These are operation-scope attestations, not a fabricated OS audit of all activity.

Only offline small evidence replay and disposable fixture tests are authorized. Stop after integration validation. Medium validation, large data, real protected hashing and replacing the frozen checker require further approval.
