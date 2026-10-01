# Stage 6 TEST-only failure evidence preservation

Disposition is recorded with final hash/archive verification in `final-receipt.json`.
This is implementation/focused testing only, not a live run or Stage 6 acceptance.

## Exact implementation

Four new versioned artifacts, final staged copy:
`D:\JARVIS-STAGE6-LIVE\cab9745de28a4cae8aa6f6f7a516bf54\code-r2`

- `failure_preserve_v1.py`: independent evidence-only preserver and verifier.
- `one_run_v1.py`: explicit-approval one-run wrapper; failure hook only, no retry.
- `policy.json`: fixed candidate/preservation paths and approved artifact patterns.
- `test_failure_preserve_v1.py`: 48 focused sacrificial tests.

Complete file sizes/hashes: `new-source-manifest-r2.json`.
Final add-on manifest SHA-256:
`e781ed6389dd809805fb89c27b6f838623d4f2da707fcd7a160d22c25249ea28`.

No existing candidate, launcher, observer, frozen checker, success finalizer,
production/runtime module, threshold, security setting or preservation boundary
was modified. The original 216-file coordination candidate remains frozen at
`675ba3f5cd6966fc6040083922d857769af418878f1f403afa38e6d5a6f50fc8`.

## Preservation behavior

The preserver has no process-launch, stop, kill, retry, finalizer or checker authority;
its only subprocess is a fixed read-only process/trace census. Its writes are outside
the failed run. Output names and manifests explicitly say NON-ACCEPTANCE FAILURE
EVIDENCE and `acceptance_seal=false`. Existing acceptance receipts reject use of this
path. Separate wrapper success/failure branches are covered with mocked invocations;
no real driver or finalizer was launched.

It records failure classification/component/time/reason, earliest timestamped run
failure, all available later failure records, known identities and binding, stage
presence (never presence-as-validity), missing/unknown evidence, inventory, metadata,
hashes, census evidence and deadline disposition. Missing chronology remains unknown.

Two host census samples plus read-only Windows file handles gate stable archival.
Recorded process instances, including console helpers, receive native handle-derived
creation/image and signaled-state checks. PID reuse is explicit, never force matched.
These checks do not manufacture kernel STOP records or confer acceptance qualification.

If writers are active/unknown, potentially live file contents are omitted and the
manifest lists them explicitly; a metadata-only archive is partial, never complete.
Approved stable files are copied byte-for-byte, including malformed JSON. Reparse
paths, hard links, unknown artifact names and cross-run binding are excluded/rejected
and reported. `.env` contents are never archived. No source evidence is repaired,
renamed, rewritten, touched or deleted by the preserver.

An output directory is exclusive per run; duplicate attempts cannot overwrite it.
Independent ZIP reopen verifies manifest, inventory, duplicate members, sizes and
every file hash. Archive/census instability is `ARCHIVE_UNVERIFIED`; partial outputs
remain. Timely acceptance cleanup and eventual cleanup are separate fields. Only
the original 20-second formula and matching clock frequency can establish timeliness;
unknown origin remains unknown. Eventual cleanup cannot reverse rejection.

## Validation

Final command (bundled Python, no observers/UAC):

```
C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -B -m unittest -v test_failure_preserve_v1
```

Working directory: this action's `code` folder. Final result: **48/48 tests PASS**,
`focused-final-r2.txt`. Coverage includes all 25 requested cases plus archive corruption,
duplicate entries, source mutation, output overwrite, traversal/hardlink rejection,
missing/foreign binding, clock mismatch, actual Windows writer locks and handle-derived
identity checks against the existing unittest process. Wrapper tests mock process
invocation; they do not start any live validation.

The historical small-live fixture was copied into disposable test fixtures without
editing the original. Its bytes can be preserved as failure evidence; it remains
failed. Offline fixture census simulations are not claimed as live cleanup acceptance.

Syntax: three new Python modules parsed during final staging. The final four staged
files were hash-compared with the tested files. Pre/post preservation checks cover all
216 candidate files, 482 preserved inputs and the prior 515-member archive. See final
verification/receipt for the post-archive recheck.

## Preserved transitional results

- Initial 42 focused tests passed (`focused-first.txt`).
- Added historical-byte fixture run: 44 passed, one errored. The new fixture incorrectly
  expected a v3 declaration in historical v2 evidence. Only the new fixture adapter was
  corrected; `focused-second.txt` and its disposable directory remain.
- Next 45 tests passed (`focused-final.txt`).
- Read-only review added exact recorded-instance cleanup checks to avoid overlooking
  known console helpers. Final 48 tests passed. Earlier staged r1 files remain at
  `D:\JARVIS-STAGE6-LIVE\cab9745de28a4cae8aa6f6f7a516bf54\code`; r2 is authoritative.
- Restricted D: mkdir denied before copying (`staging-failure.json`); bounded host-context
  file copy succeeded. No Windows Administrator/UAC launch occurred.
- Restricted Win32_Process census returned access denied (`restricted-census.json`);
  host-context read-only census succeeded with zero matching processes/traces/unknowns
  (`host-census.json`). No security settings were changed.
- Deliberately corrupted ZIPs, active-writer fixtures, simulated disk-full and census
  failures remain in their test directories. These are injection results, not live runs.

## Limits and rollback

The future live path is not validated in this action. Twenty-second live cleanup
feasibility, actual observer timing and full terminal-evidence acceptance remain open.
If existing cleanup is still running when the failure hook executes, the preservation
result can legitimately be metadata-only/CLEANUP_UNPROVEN. It cannot stop writers or
prove omitted evidence, and it cannot automatically retry later. Unknown/unapproved
files are explicitly omitted; original bytes remain in their source directory.

First historical failure ordering cannot be reconstructed where timestamps are absent.
Historical 21 AMBIGUOUS / 1 UNMATCHED remain unchanged. Historical delay causes remain
UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Rollback: do not invoke the separate new wrapper/preserver. All originals and the
accepted candidate remain unchanged. Keep the new artifacts and evidence; no production
rollback, installation, deletion or automatic cleanup is required.

No live run, UAC request, medium/large validation, 59.7 GB access, protected VM/configuration
access, VirtualBox launch, production operation or acceptance commit occurred.

The exact future single-run procedure is `ONE_RUN_REVIEW.md`, OWNER REVIEW ONLY.
