# Blocked-attribution analysis/binding successor v1

Scope: new offline TEST analysis/binding only. No fixture execution, rebuild, recorder change, ETW session, UAC, protected VM/configuration access, production change, or later Stage 6 gate.

## Implemented artifacts

- analyzer_v1.py: strict raw/binding/execution validation; seven conditional within-block contrasts; grouped Student-t intervals; classifications; drift diagnostics; separate bound inference review; external historical sanity comparisons. No process-launch function and no imports of old gates.
- candidate.json: immutable historical/source/executable/compiler/audit/launcher identity records and external reference IDs/hashes.
- contract-v1.json: exact approved future experiment, confidence levels, planning targets, classification rules, no-retry/no-extension policy, unchanged final screen.
- binding-template-v1.json: non-executable schema template. Actual bindings require a fresh ID and empty bounded D: workspace; template schema is not accepted as run evidence.
- evidence_v1.py: archive and census validators.
- test_analyzer_v1.py: fabricated-data unit tests only.
- ONE-RUN-OWNER-REVIEW.md: exact future fixed experiment and evidence/analysis procedure; not authorized to run by this implementation.

All are new files in this report directory. Existing source, fixture, scripts, checker, and evidence were not edited. The original failed 40-pair/640-pair outcomes remain unchanged. No new benchmark binary was built.

## Statistics and prospective semantics

Exact contrasts: B-A, B-D, C-A, D-E, E-A, D-A, B-C-D+A. Per-block values, ten consecutive four-block means, estimate, half-width and interval are preserved in ns/callback and percentage using each block's A. All ordinary noisy blocks remain. No trimming/winsorization. Fixed sample of exactly 40 complete blocks; wrong/missing/duplicate/extra data rejects the attempt.

df9 t criticals: 95% = 2.2621571627982; 97.5% = 2.685010846816449. Computed by a standard-library integral/recurrence, verified against a known 95% value and an independent Simpson integration of the t density. No dependency installed. An initial read-only check found scipy unavailable; no benchmark or source consequence.

B-D and D-A have adjusted 97.5% intervals. Other 95% intervals are descriptive. Planning half-width targets: B-D/D-A 0.20pp; C-A/D-E/E-A 0.30pp; residual 0.40pp; B-A has no width gate. The final <=1% diagnostic screen remains unchanged, and finalInstrumentationQualified is always false.

STRONGLY_SUPPORTED requires B-D lower strictly >0.5 AND D-A upper <=0.9. DISPROVEN means the specific required saving is ruled out: B-D upper <=0.5 and half-width <=0.20. This uses the approved precision planning target to give 'sufficiently precise' a deterministic conservative interpretation. Otherwise a positive saving lower bound yields SUPPORTED_BUT_UNCERTAIN; remaining cases are INSUFFICIENT. Strong support does not require an arbitrary additional width gate if the adjusted bounds already resolve the decision. No category authorizes real timestamp substitution.

Drift diagnostics report first/last half means, temporal slope, treatment-centered position effects, grouped residuals and lag-one correlation. They are descriptive: no unapproved numerical drift cutoff was invented. Default analysis is INCONCLUSIVE until a separate run/raw/binding/diagnostics-bound assessment supports the inference assumptions. Material dependence/drift or unresolved assumptions remains INCONCLUSIVE. No estimator switching or automatic additional measurements. Historical intervals are not pooled; non-overlap requests review rather than automatically claiming a reproducibility defect.

Warm-up count is absent from the unchanged fixture JSONL. It is checked against the pinned fixture source and mandatory execution declaration, NOT portrayed as independently measured per-arm evidence. Actual process/CPU records still originate from the existing retained-handle launcher. SHA binding prevents accidental substitution; it is not a new security authority or a defense against a malicious evidence producer.

## Validation and preserved failure

First attempt: 72 tests, 71 passed, 1 failed. `test_reject_binding_schedule` found shared mutable contract data: mutating a candidate schedule also mutated the in-memory validation expectation. Pre-correction source/tests and the observed failure are preserved under preserved-failure-01. The successor now returns independent contract data and compares canonical contract bytes. This was a new successor-only implementation defect, not a historical fixture or runtime failure.

Second attempt: 79/79 passed. Final source adds external-reference sanity reporting and its test: **80/80 passed; 0 failures/errors/skips**. Exact test names and output are in offline-tests-final.txt. Syntax checks: all three final Python modules PASS. No attribution, reference benchmark or variant selftest ran.

Coverage includes all requested areas: fixed schedule/repeats/counts; missing/duplicate/extra blocks; raw statistics/schema; warm-up declaration; process/exit/identity/deadline; no retries/extensions; all seven arithmetic contrasts; A_i denominator; four-block grouping/ten means; interval levels and boundary categories; no B-A width gate; screen separation; no old-gate import; stale/hash/workspace rejection; source preservation; balanced-not-randomized labelling; D never production valid; raw-byte retention; archive corruption; fail-closed census.

Commands used: bundled Python `-B -m unittest -v test_analyzer_v1` for first attempt; then the same unittest loader/runner with exclusive new result/log files for attempts 2 and final. Standard-library ast.parse syntax checks (no bytecode). Final census: read-only host Get-CimInstance Win32_Process and logman query -ets; no Windows elevation/UAC. final-census.json records **0 matching diagnostic processes / 0 diagnostic trace sessions**.

## Preservation and limits

65 pre-existing files and 262 members across the three historical archives verified before changes; post-verification and new archive receipt complete the record. final-source-freeze.json records exact new module/binding hashes. Archive path, manifest SHA-256, archive SHA-256 and verified member count are in archive-receipt.json after finalization. Broad project synchronization is intentionally avoided because this narrow task must not overwrite unrelated evidence.

Tests use fabricated data and do not establish component performance, statistical power on this host, or actual future launch success. Existing fixture compiler/replay effects and fixed balanced (not randomized) schedule remain disclosed. The existing launcher's 1,200-second timeout is not itself cleanup proof. No runtime/source correction to that launcher occurred.

Historical 21 AMBIGUOUS / 1 UNMATCHED remain unchanged. Historical ETW-loss cause remains UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Rollback: no previous file needs restoring. Retain this separate successor and evidence; do not invoke it if withdrawn. No commit created. STOP after final evidence verification; the 40-block experiment requires separate owner authorization.
