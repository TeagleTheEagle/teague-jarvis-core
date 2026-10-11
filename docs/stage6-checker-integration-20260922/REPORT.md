# Stage 6 versioned checker integration

**CHECKER_INTEGRATION_VALIDATED**

This is an offline small-evidence replay and TEST checker integration gate only. No live observer, worker, process probe, medium workload, large dataset, VM or protected hashing was launched. Stage 6 remains incomplete. The frozen checker was not replaced.

The result is final only together with archive-verification.json and the hash-bound acceptance-seal.json created after independent verification. The archive contains **172 members**, including all new fixtures, candidate source, preserved preparation failures and the complete prior 324-member combined archive as a nested reference.

## Mandatory 50-item report

| # | Item | Result / evidence |
|---|---|---|
| 1 | Frozen checker initial SHA-256 | `e6fbefd3fd463c6c8e09d0e8273a81b46ee2806515cae05e7837ea905a3e69d6` |
| 2 | Frozen checker final SHA-256 | `e6fbefd3fd463c6c8e09d0e8273a81b46ee2806515cae05e7837ea905a3e69d6`; identical |
| 3 | Versioned candidate path | `D:\JARVIS-STAGE6-LIVE\5d7476373d4a4ad38017e89f15a538f0\checker-v2\checker_v2.py` |
| 4 | Candidate initial SHA-256 | `e6fbefd3fd463c6c8e09d0e8273a81b46ee2806515cae05e7837ea905a3e69d6`; exact initial copy recorded before separate integration |
| 5 | Candidate final SHA-256 | `a0c5bf094841bf428bb62073082627e4e3ca88d1b330f3bcd8d611ecc51f2945` |
| 6 | Schema version | `stage6-checker-input-v2`; adapter remains `stage6-small-combined-v1`; exact kernel contract v1 plus owner creator/helper clarification |
| 7 | Adapter input schema | `D:\JARVIS-STAGE6-LIVE\5d7476373d4a4ad38017e89f15a538f0\checker-v2\schema.json`; 123,353-byte closed field/type schema, CONTRACT.md and original adapter interface. Original manifest format/version, every segment range/hash/state, canonical keys, coverage, CIM and closure are required. Overlap is independently rejected by contiguous per-segment range verification. |
| 8 | Positive fixture | PASS; 72 records, 4 segments, global sequence 1–72, 36 verified instances; positive-result.json lists satisfied rules |
| 9 | Validated evidence replay | PASS; actual archived pre-archive adapter payload parsed and fully compared with recomputed output; raw persisted files re-opened; original final sidecar/archive binding verified before and after |
| 10 | Total focused tests | **114** = 83 primary + 31 review checks |
| 11 | Passed | **114** |
| 12 | Failed / skipped | **0 / 0** checker tests; two explained pre-candidate preparation errors and one archive-preparation allowlist omission preserved separately |
| 13 | Rejection checks | **103**, comprising 72 primary rejections, 28 supplemental rejections and 3 explicit nonzero CLI rejection assertions |
| 14 | Rejection checks passed | **103/103**; other 11 are positive/control/preservation assertions; category and exact reason in JSON results |
| 15 | Non-vacuous | PASS; eight empty mandatory collection fixtures rejected, including identities, handles, images, native entries, segments, STARTs, STOPs and CIM |
| 16 | Missing segment | REJECT; disposable on-disk fixture, original untouched |
| 17 | Sequence gap | REJECT even after recalculating fixture segment hash/manifest seal |
| 18 | Duplicate sequence | REJECT even after recalculating fixture hashes |
| 19 | Corrupted hash | REJECT; byte and hash mutations tested separately |
| 20 | Missing START | REJECT, including adjusted aggregate-count fixture |
| 21 | Missing STOP | REJECT, including adjusted aggregate-count fixture |
| 22 | Authoritative ambiguity | REJECT; duplicate summary/false instance sequence collision tested |
| 23 | Missing handle | REJECT |
| 24 | Missing image | REJECT |
| 25 | Missing native entry | REJECT; native fault, deadline and invalid entry state also reject |
| 26 | Direct probe class | PASS: 16 DIRECT_PROBE creator captures |
| 27 | Direct worker class | PASS: 1 DIRECT_WORKER creator capture |
| 28 | Tracer-helper class | PASS: 2 TRACER_HELPER_VERIFIED, distinct from observer infrastructure |
| 29 | Post-exit-helper class | PASS: 16 QUALIFIED_POST_EXIT_HELPER under unchanged narrow exception; **not successful creator/tracer images** |
| 30 | Incorrect helper class | REJECT; source substitution, generic access denial, unknown helper, missing helper and false creator classification |
| 31 | CIM unique | Conditional policy-unit PASS only with stipulated independent event-bound proof and canonical key. **Not a real unique CIM observation.** Public replay still rejects invented unique matches from the current raw schema. |
| 32 | CIM ambiguous | PASS as secondary when authoritative requirements pass; real replay preserves 66 AMBIGUOUS |
| 33 | CIM unmatched | PASS as secondary; real replay preserves 1 UNMATCHED |
| 34 | CIM contradiction | REJECT when positively established; ambiguous/unmatched alone are not contradictions |
| 35 | Heartbeat failure | REJECT at 10 seconds; age and interval tested, threshold unchanged |
| 36 | Deadline failure | REJECT; native and qualification deadline failures tested |
| 37 | Incomplete finalization | REJECT; missing states/manifest/seal, pending queue, writer fault/unfinished threads, limits and secondary residue |
| 38 | Cleanup failure | REJECT; worker/native closure, host process and trace-session fixtures |
| 39 | Malformed payload | REJECT; absent fields, wrong types, duplicate JSON keys, NaN/Infinity, extra fields and forged PASS |
| 40 | Unsupported schema | REJECT missing/numeric/unknown/future schema or legacy mode; no inferred version or fallback |
| 41 | Tamper tests | PASS: segment bytes/hash/range, creation/image identity, helper class, native entry, manifest, cleanup and archive mismatch all reject |
| 42 | Frozen preservation | PASS; immutable reference path `D:\JARVIS-STAGE6-LIVE\c090f8cbc0d444e493f1d801e36fd1bb\code\cleanup_checker.py`; **481** final source/evidence comparisons plus archived source verification |
| 43 | Candidate cleanup | PASS; final host inventory zero matching diagnostic/VirtualBox processes and zero diagnostic trace sessions; no observer or probe launched this gate |
| 44 | Archive verification | PASS only as independently certified by archive-verification.json and final sidecar; **172** members checked by bytes/hash and exact membership |
| 45 | Protected VM access | NONE; no protected files/configuration opened, hashed or queried; no VirtualBox command |
| 46 | Production changes | NONE; only new TEST candidate, fixtures, reports and evidence archive written |
| 47 | Historical 21/1 | UNCHANGED; raw historical identity-summary.json SHA-256 `9087f0f6596c34f3b552061a4e3578828a0491fd7ec6be3e000a2adde3729dca` reverified; distinct from small-run 66/1 |
| 48 | Historical causes | UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED. |
| 49 | Next proposed gate | Owner review of MEDIUM-PROPOSAL.md; new explicit workload declaration/binding required before live medium execution. No automatic continuation. |
| 50 | Final status | CHECKER_INTEGRATION_VALIDATED, subject to accompanying completed archive receipt/seal |

## Exact changes and commands

`preflight.json` records seven copied files and their before hashes. `changes.json` records all final hashes and new files. Only the separate copied checker_v2.py and the candidate combined.py differ from copied sources: the former is a new explicit versioned entry point; the latter changes only its qualification dependency to the local frozen copy. coverage.py, qualification.py, process_instances.py, application_authority.py and frozen_reference.py remain byte-identical to their references. New candidate schema.json, binding.json, positive-fixture.json and test_candidate.py support the bounded replay. Source-freeze.json records the candidate set. All changed source diffs are archived.

Commands used Python `C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe` with `-B`:

1. `prepare.py` -> rejected expected-hash transcription error; source evidence was correct. `prepare_v2.py` -> rejected Windows default-code-page decode of UTF-8 historical report. Both preserved. `prepare_v3.py` -> PASS; 324-member prior archive and 470 initial comparisons verified.
2. `host_preflight.ps1 -RunId 821023fd57c1401985cb0b28a869247e` -> PASS; read-only inventory, no UAC monitoring launch.
3. `install.py` -> wrote contract/schema before separate candidate implementation and froze all candidate files.
4. `D:\JARVIS-STAGE6-LIVE\5d7476373d4a4ad38017e89f15a538f0\checker-v2\test_candidate.py` -> 83/83 PASS; disposable fixture root in test-results-location.json.
5. `review_tests.py` -> 31/31 PASS and exact original evidence replay PASS.
6. `finish.py` -> 481 comparisons PASS, 16 Python source parses PASS, source diffs/hashes recorded. archive.py independently parsed all 18 current Python sources without bytecode writes.
7. `host_preflight.ps1 -RunId 15e2234e97c8435d88ac357238ecaff7` -> PASS; zero matching processes/traces.
8. `archive.py` -> stopped before archive creation because the deliberate archive-mismatch fixture ZIP was absent from the packaging suffix allowlist. `archive_v2.py` admits only that exact fixture ZIP, then performs exact archive/member/source verification, preservation recheck and final acceptance sidecar; actual hashes in archive-verification.json.

Full paths for scripts are under `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-checker-integration-20260922`, unless the D: candidate path is shown. No frozen legacy suite was repurposed or relabelled under the amended contract. Historical results remain under their original semantics.

## Source review, limits and rollback

SOURCE-REVIEW.md covers default PASS branches, exception handling, required/empty fields, strict types, enums/version dispatch, file paths, evidence substitution and mutable-input assumptions. The replay is restricted to the explicitly pinned accepted small archive. It is not a general medium/large checker, a signed remote proof, or an OS protection boundary against hostile same-user administrators. No actual PID reuse or new real unique CIM event match was demonstrated in this offline gate.

Preserved qualified results are replay evidence, not newly run process results: 72 kernel records / 36 instances, 17 creator captures, 2 tracer helpers, 16 qualified post-exit helpers, 1 infrastructure observer; maximum recorded heartbeat 1.0918706 seconds. Thresholds, monitors and runtime are unchanged.

Rollback: stop selecting this separate candidate and keep the frozen reference as before. No installation, runtime route, registration, configuration or production data needs restoring. Preserve the entire candidate/fixture/archive tree for audit; no deletion or automatic restoration is required.

STOP. Medium validation, the 59.7 GB campaign, protected hashing and VM operations were not performed and remain pending owner review.
