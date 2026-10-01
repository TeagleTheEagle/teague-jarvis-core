# Stage 6 — versioned checker integration and fresh-run binding review

Disposition: REVIEW COMPLETE. Separate TEST contract amendment needed before implementation. No checker/source changes or validation run performed.

## Evidence inspected

Candidate: D:\JARVIS-STAGE6-LIVE\978b5ce769244ec9a580fb0846f9bfdc\code.

- small_check.py: check() constructs helper evidence exclusively from authority-tracer rows, invokes coverage(), q.stream(), q.qualify(), detailed trace verification, application persistence, queue, cleanup, journal and workload checks.
- small_coverage.py: coverage() requires creator-owned handles for DIRECT_PROBE/DIRECT_WORKER and tracer-opened-handle for other classes. The existing qualified post-exit exception requires OS_CONSOLE_HELPER, OPEN_PROCESS_FAILED/error 87 and an acquisition attempt after kernel STOP. A successful OpenProcess followed by image error 31 does not qualify.
- medium-checker/qualification.py: stream() validates actual segment hashes, manifest/seal, global record sequence and totals. qualify() checks loss counters, session-scoped process sequence/creation uniqueness, START/STOP and summary equality, retained-handle/native contradictions and explicit CIM ambiguity.
- small_binding.py: exact v1 declaration, current CODE/source manifest, fixed small synthetic inventory and unchanged limits. Old absolute paths/source manifests cannot simply be reused in the copied candidate.
- evidence_support.py: collector anchor is scope-only, image source is independent-tree-handle-v1, captureEntryQpc is NOT acquisition-return time. Output currently lacks producer run/session/source-manifest binding.
- baseline_finalize.py: legacy path invokes cleanup_checker/evaluate and application-based probe lifecycle validation, writes authoritativeApplication, and archives only immediate run files. It is not a compatible finalizer for the amended kernel-authority combined path; do not invoke it unchanged or silently rewrite it.
- Prior integrated diagnostic finalize.py recursively archives evidence including failed runs. Archive integrity is preservation evidence, not an acceptance decision.
- support_verifier.py/test_verifier.py: 43 focused tests, synthetic cross-channel contract only. Completeness booleans and a supplied digest are not independently verified real trace evidence. Native-entry fixtures require all identities; actual approved coverage requires native-entry only for direct probes/workers. Do not import these assumptions into production acceptance.

## Smallest proposed acceptance-rule amendment

Only OS_CONSOLE_HELPER may use a new explicitly named independent tracker live-image verification branch. Kernel lifecycle remains authoritative. This branch supplies live handle/image corroboration, never START/STOP identity and never an implicit replacement for creator-owned direct-process evidence. APPLICATION_OBSERVER, DETAIL_OBSERVER, direct workers/probes and unclassified helpers retain existing rules. No generic fallback.

Require all of the following together:

1. Actual q.stream()/q.qualify() and detailed trace checks succeed without loss, gap, missing segment, metadata conflict or identity ambiguity. Preserve their current full checks; do not replace with fixture booleans.
2. Required helper inventory comes from qualified kernel instances, not tracker records. Key by session + kernel sequence + PID + creation identity. Exact parentSequence/PID/creation and lifetime must resolve uniquely, back to the actual collector/native identity where applicable.
3. Tracker row binds to exactly one such instance; actual handle PID/creation agrees before and after query. Retained handle remains valid, both zero-wait states are 258, query succeeds, full normalized image equals kernel image, timing lies strictly before kernel STOP, QPC frequency/domain agree, exit time/code agrees and handle closes. No PID/name-only inference.
4. Record handle acquisition-call begin/return separately from capture entry in a future candidate. Missing required timing fails. Never relabel existing captureEntryQpc as acquisition time or retrofit old evidence.
5. Preserve original tracer attempt/image error and tracker record separately. A documented unavailable tracer image may be supplemented only under this explicitly approved branch. Any successful conflicting tracer image, creation/exit discrepancy, contradictory native/retained evidence, ambiguous parent, or missing mandatory record fails. Failed original runs remain failed.
6. Native PE-entry remains mandatory for DIRECT_PROBE/DIRECT_WORKER and verifies the collector's eventual exit independently. It does not become mandatory for OS-created console helpers, nor become optional for direct processes. Collector anchor cannot attest its own exit.
7. Keep CIM collection/persistence enabled. Ambiguous/unmatched CIM remains explicit; proven contradictions still fail. Existing error-87 qualified post-exit rule remains separate and unchanged.

This changes the accepted verification source for one class and therefore requires explicit owner approval. It is not merely format conversion.

## Proposed fresh-run binding and finalization

Use a separately versioned small-only checker candidate; retain all v1 files/evidence. At prepare time exclusively create a fresh contained D: run directory and declaration with run nonce, checker-contract version, candidate manifest digest, exact small workload inventory/digest, unchanged limits and declared channels/classes. Reject reparse escapes, stale directories, preexisting output and unbound absolute paths.

Bind tracker output at production time to the run/declaration digest, producer PID+creation, QPC frequency and source-manifest digest. The launcher must record actual observer/kernel sessions and collector identity before workload admission. Final verification compares those records to qualified kernel/native instances. A final manifest alone cannot prove historical run provenance or repair missing producer binding. Hashes provide integrity within the existing trusted TEST harness, not protection against a malicious same-user writer; no new security claim.

After workload and observers stop, verify joins, retained handles, tracer stop/loss counters, stream closure, queue, health samples, native bridge and zero matching leftovers under the existing cleanup contract. Preserve every failure. Normal success and deliberate startup-failure rejection get distinct dispositions; a deliberate failure is not normal workload success.

A separate small-v2 finalizer must consume the actual versioned checker result and its input digests. Recursively inventory all required artifacts, including detail segments and native files; reject missing/extra unexpected evidence, duplicate entries, path escapes or changed bytes. Flush/finalize on D:, construct deterministic input manifest, verify current source hashes, create exclusive result/manifest/seal and archive, verify every archive member and source again. Keep archive receipt outside the sealed set to avoid a circular hash. Any archival/finalization failure prevents acceptance. Canonical archive copy happens only after live monitoring ends and must be independently hash-verified.

Do not use baseline_finalize.py to claim this new contract. Preserve the failed-run archiving path independently of acceptance sealing.

## Proposed files/boundaries

- Separate versioned copies/new modules: small_check_v2.py, small_coverage_v2.py, small_binding_v2.py, small_finalize_v2.py and a narrowly scoped actual-evidence adapter with negative fixtures.
- Separate TEST candidate evidence_support.py/large_collect.py: acquisition timing and producer binding only; no polling interval/deadline change.
- Separate launcher/preparation adaptation only where required to carry declaration/session binding; inspect exact launch chain before editing.
- Keep original small checker, authority tracer, native PE-entry implementation, durable writer and runtime frozen. If actual integration requires changing those authority mechanisms, return for review.

## Required validation before a small attempt

1. Test actual serialized kernel segments/seals/summaries and native records through existing verifiers, not a synthetic completeness flag. Cover hash/sequence/loss/parent/source/run contradictions and missing/duplicate required identities.
2. Coverage matrix regression: direct creator-owned requirements unchanged; eligible helper branch explicit; other roles rejected; qualified error-87 exception unchanged; image error 31 alone still fails.
3. Acquisition timing, capture state, cleanup/close/join failure injection and producer binding tests. Test stale/replayed run, changed declaration/source, copied old artifact, wrong session and reparse/path escape rejection.
4. Finalizer tests: nested artifact omission, interrupted/changed writes, archive failure, evidence mutation, missing cleanup and failure-ledger presence all prevent success. Prior failed evidence byte-preserved.
5. Then one fresh small normal run and one controlled startup-failure run using established per-run UAC observers, with unchanged thresholds and exact small inventory. Verify actual kernel/helper corroboration, collector output equivalence, shutdown, final archive and no leftovers. Stop on unexpected failure; no automatic retry.

No medium/large/protected acceptance is authorized by this design. Even a small pass does not prove capture of every short-lived helper; discovery polling remains fallible and missing mandatory evidence remains FAIL.

## Integrity, rollback and decision

Review verification records all 183 candidate hashes and both preceding archive digests unchanged. No runtime, checker, VM/configuration or dataset accessed for execution; protected VM/configuration not read. Only review/evidence files created.

Rollback: leave existing candidate selected; proposed v2 is separate and not implemented. No production rollback needed.

NEXT ACTION: Approve the explicit OS-helper independent-tracker corroboration rule and bounded versioned TEST binding/finalizer implementation with focused tests. That approval need not authorize the subsequent live small attempt; define that separately if desired.

Stage 6 remains INCOMPLETE. Historical 21 AMBIGUOUS / 1 UNMATCHED unchanged. Historical tracing/delay causes UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
