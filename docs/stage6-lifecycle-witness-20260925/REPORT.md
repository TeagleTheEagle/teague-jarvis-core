# LIFECYCLE_WITNESS_IMPLEMENTED_AND_TESTED

TEST-only offline successor: `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-lifecycle-witness-20260925\candidate`.
Candidate manifest SHA-256: `3c8efb4e22ed98ef4e6a5e63a7a0040f36d10fbe40e1cb427eba760fc9e46576` (245 files).
No observer/live ETW run, UAC, protected VM/configuration access, production change,
medium/large run or source acceptance commit occurred. Historical ETW-loss cause
remains UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

## Change and boundary

Only two existing observer sources changed. Both callbacks use one static
65,536-record single-producer numeric buffer; overflow never overwrites and makes
the diagnostic incomplete. A scope starts after the process-provider/START/STOP
gate, before existing identity decoding. Field-validity bits distinguish not
decoded from decoded-invalid. No new TDH call, handle query, QPC call, lock,
callback allocation or callback I/O was added by the witness. Original selector
allocation/I/O and timing remain as before; this is not a claim those original
callbacks never allocate. Parent and instance states are sampled at their actual
existing decisions. Unevaluated state is null, never inferred false.

Unknown-parent rejection still precedes invalid-identity checking where the old
code did so. STOP still needs an exact existing row. No deferred selection,
retry, insertion reordering, forced match or acceptance rule changed.

Export runs after ProcessTrace thread.join(), with run, session, channel, manifest
and actual executable-file SHA-256, schema, frequency, quiescence and overflow.
The existing finalizer rejects unknown run-tree artifacts; therefore sidecars
are run-named siblings OUTSIDE that tree. The finalizer, checker, preservation
policy, helper-handoff and existing telemetry are byte-identical to predecessor.
Separate four-file diagnostic archival is non-acceptance and preserves first
failure. Export failure is explicit or a missing sidecar; neither may pass
diagnostic completeness. Export work still counts against unchanged deadlines.

The analyzer requires independent exact identities AND conservative event-time
windows, uses sequence when available, rejects stale bindings, preserves PID
reuse ambiguity and does not infer lost payloads from absent callbacks. Normalized
input provenance must be independently verified by the review procedure; this
analyzer is not a replacement identity authority. Invalid PID decoding in a
target time window remains identity-unresolved, not false callback absence.

## Validation

- `build-offline.cmd`: MSVC 19.44 / C++17 / O2 builds of both observers and offline
  replay executable passed; no observer binaries executed.
- `candidate\WitnessOfflineTests.exe`: 146 native assertions PASS.
  Replays the actual original and modified callback bodies with stubbed OS/TDH
  inputs, comparing decoded-query order, rows, faults, discarded counts, clocks
  and authority captures. This is OFFLINE equivalence coverage, not ETW proof.
- `export-offline\WitnessExportOffline.exe <fixture-run> authority|detailed`:
  both post-quiescence serializer fixtures PASS; binary/manifest/run binding,
  CREATE_NEW overwrite rejection and inaccessible export destination tested.
- `python -B test_witness.py`: 45 tests PASS (`tests-final-45.log`). Covers
  disposition, point-in-time state, PID reuse, missing evidence, overflow,
  bindings, static hot-path constraints, exact preserved acceptance rules,
  sidecar placement and NON-ACCEPTANCE archive verification.
- Python syntax: six affected/utility files compile without writing bytecode.
- Source/binary pre/post hashes and complete integration diff recorded separately.

## Preserved transitional findings

`tests-first.log`: 37 tests, 36 PASS, 1 change-inventory failure; a rebuilt object
file was omitted from the intended-change list. Corrected reporting, not runtime.
`build-export.log`: standalone export-fixture compile failed on the Windows
DUPLICATE macro; new internal enum renamed DUPLICATE_EVENT, serialized disposition
still DUPLICATE. Subsequent complete builds passed. Both logs retained.
An interim preservation-policy extension was reviewed against the strict frozen
finalizer and superseded by sibling export; its proposed contents and tests are
preserved as transitional artifacts, not the final design. Policy restored
byte-for-byte. Sandbox CIM census returned Access denied; host read-only census
completed with no Windows UAC. No failed live attempt was retried.

## Exact changed predecessor artifacts

- `J6AuthorityTraceV3.exe`: before `a0b643f67deb477df6bc763accdac7fa5cb57910f79bf92396940c98faa63f48`; after `9d2091aeea8c47cbaa423ca6b2c6131275ec3937357927cb3dbbd6c029cfe32c`.
- `J6StartupTrace.exe`: before `cfe90eb7a46eddea66429af51e4b214cfd6068b35d9b2e999c2a4b0cf4a7dddb`; after `5225e63c654a63fff05e4002475e8caae5910d4d11822a13119bf2791fc35634`.
- `authority_trace_v3.cpp`: before `e5eb037399262250a78f5968f452f110c822f872363de0fa01630bd5ef48c9da`; after `2c49bb2f3962bf14c014576898e2a4fd4881d2bc5b45e9e3e36a9f5f12deae76`.
- `authority_trace_v3.obj`: before `ada56087cf7fd89fd23d3481906d9910ee403dd7f443a8a50887bddf54bcec4b`; after `34247c9283af4c39f4abaa8df251c6f27cea943644803da665fc0135361d3a9f`.
- `startup_trace.cpp`: before `a916d35452edfcec025f42c9ad97713e0dbfd9b3bb71ceb2f68d3bfbc3a77817`; after `4ed4b9c45577984dd25827dd7a67916c4abfc41237d7290330e0f4252928a58c`.

Added source artifacts: lifecycle_witness_v1.hpp, lifecycle_witness_export_v1.hpp,
analyze_lifecycle_witness_v1.py, preserve_lifecycle_witness_v1.py,
witness_offline_tests.cpp and witness_export_offline.cpp. All other new build,
manifest and evidence artifacts are enumerated in after.json / archive manifest.

## Limits and rollback

No live overhead, loss reproduction or Stage 6 acceptance has been established.
The prior eight historical instances cannot be retroactively reconstructed with
this newly added witness. It may overflow during future collection; incompleteness
must remain explicit. The offline candidate still requires the existing bounded
fresh-D:-workspace rebinding/preflight under a future owner-approved procedure.

Rollback: leave this separate successor unused and retain the unchanged original
235-file candidate. No production restore, VM action or source rollback is needed.
Evidence archives must be retained, not overwritten or deleted.

One proposed live diagnostic procedure is in ONE-RUN-OWNER-REVIEW.md. STOP for
owner review; the procedure is not execution authorization.
