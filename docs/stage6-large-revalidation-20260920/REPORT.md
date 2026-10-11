# Stage 6 large synthetic protected-collector revalidation

**BLOCKED — source admission failed before either observer or hash worker started.**

The owner explicitly required stopping if any preflight condition failed. No correction/retry, large monitored hash pass, acceptance finalization or protected capture was attempted after rejection.

## What passed before source admission

The frozen protected collector's 84 files and hardened diagnostic candidate's 96 files match their accepted hashes. Calibration records match their preserved archive. Dry Run #1 (131 members), Dry Run #2 (133 members), collector integration/calibration (1,333 members) and diagnostic hardening (755 members) archives were independently verified without reopening their historical test fixtures.

The existing synthetic dataset's 12-file listing, sizes and modification timestamps match calibration. There are 59,665,402,098 bytes; largest file is synthetic `base.vdi`, 34,359,738,368 bytes. D: had 1,856,480,759,808 bytes free. Host process/ETW preflight found zero matching processes/traces. Only synthetic filesystem metadata and ACLs were read; no protected VM/configuration file was accessed.

The old large-data launcher selected the older observer and did not run the bounded sampler. A separate integration copy was therefore prepared at `D:\JARVIS-STAGE6-LIVE\e23d36c0a24246c996aa28e5d5561863\code`. Frozen candidates were not edited. The new orchestration uses the unchanged protected hash worker, contract, finalizer, limits, hardened observer, checker and sampler. Four focused wiring tests passed; PowerShell syntax passed. Exact changes/hashes are recorded in `candidate.json`, `prepare.py` and `collector-wiring.diff`.

## Exact blocker

The approved synthetic source remains at:

`D:\JARVIS-STAGE6-LIVE\1c1f5d0c390b42cc9ba9f4f6221dabc6\code\large-synthetic`

The fresh integration copy is under a different `CODE` directory. `baseline_contract.approved()` checked the source's explicit allowlist entry, then called `workspace.check_path()`. That existing guard requires synthetic paths to be beneath the current `CODE`, and correctly raised:

`ValueError: D live workspace containment required`

The launcher then stopped with `Preflight contract/source failed before observers`, exit 1. The `prepare()` call failed before creating the live run. No UAC prompt, kernel tracer, independent observer, sampler, probe or hash worker started. The launcher/contract interpreter themselves ran and exited; they are not represented as an executed collector campaign.

The post-stop PowerShell metadata comparison initially reported differences because previously loaded JSON timestamps were DateTime objects while freshly captured timestamps were strings. Both complete serialized before/after datasets are identical. Independent JSON comparison and comparison after loading both sides with the same type conversion agree: all 15 synthetic file/directory metadata and ACL records are unchanged. The original false comparison result is preserved in `source-preservation.json`, with `comparison-type-diagnosis.json` and `final-preservation.json` recording the correction. No source metadata was repaired or changed.

This is an integration setup error, not evidence of a collector runtime defect or a recurrence of the original timing failures. `launch-rejection.json` preserves the observed command, call path and tool-output provenance. The successful preliminary integrity checks do not make full source-admission preflight PASS.

## Minimum next procedure — review only

Keep the containment guard unchanged. In a newly authorized attempt, place a complete copy of the existing sacrificial dataset beneath the integration candidate's own `CODE` directory, with an exact synthetic-only allowlist entry. Verify the copy against the preserved calibration hashes, record its new file identities/timestamps, capture its ACL/metadata baseline and freeze the run configuration before UAC.

This requires about 59.7 GB of additional D: storage plus evidence headroom, which the observed capacity permits. Copy only the synthetic source, never protected VM artifacts. Preserve the existing dataset and all failed records. Then repeat preflight and, if it passes, issue the two known UAC observer prompts and perform the unchanged two-pass/long-observation workflow. No broader filesystem exception, deadline change or protected-root authorization is proposed. This procedure was NOT executed in this pass.

## Required 30-point disposition

| # | Requirement | Result |
|---|---|---|
| 1 | Dataset size | 59,665,402,098 bytes, existing synthetic dataset |
| 2 | File count | 12 |
| 3 | Largest file | 34,359,738,368 bytes; synthetic `base.vdi` |
| 4 | Total hash duration | NOT RUN |
| 5 | Pass #1 duration | NOT RUN |
| 6 | Pass #2 duration | NOT RUN |
| 7 | Measured throughput | NOT MEASURED |
| 8 | Hash equality | NOT RUN in this attempt; prior calibration is historical evidence only |
| 9 | Source metadata preservation | Preliminary listing/size/mtime matches calibration; before/after ACL and metadata check recorded separately |
| 10 | Maximum heartbeat | NOT MEASURED; observer did not start |
| 11 | Longest monitor stage | NOT MEASURED |
| 12 | Sampler | NOT RUN; four orchestration tests passed; previous seven actual sampler cases remain historical validated evidence |
| 13 | START total | NOT COLLECTED; monitored workload never started |
| 14 | STOP total | NOT COLLECTED; no fabricated lifecycle events |
| 15 | Child/helper total | No diagnostic workload/helpers launched |
| 16 | Lineage ambiguities | NOT EVALUATED for a new run |
| 17 | Deadline violations | NOT EVALUATED; no workload admitted |
| 18 | Queue reconciliation | NOT RUN; no observer queue created |
| 19 | Finalization | Collector acceptance finalization NOT RUN; failure evidence archived separately |
| 20 | Manifest | No successful baseline manifest; diagnostic failure archive manifest only |
| 21 | Manifest SHA-256 | Baseline: NOT CREATED; failure archive hash in archive-verification.json |
| 22 | Archive verification count | Exact new count in archive-verification.json; this is failure/preparation evidence, not collector acceptance |
| 23 | Cleanup | Final read-only host result in host-final.json; no forced termination or security change |
| 24 | Collector hashes | 84 unchanged; final recheck recorded |
| 25 | Diagnostic hashes | 96 unchanged; integration copy hashes separately frozen/rechecked |
| 26 | Historical delay status | Original long probe-delay cause UNCONFIRMED; original heartbeat-delay cause UNCONFIRMED |
| 27 | Protected VM access | NOT ACCESSED; VirtualBox not launched |
| 28 | Production change | NONE by this work |
| 29 | Protected-baseline eligibility | NOT ELIGIBLE; large synthetic acceptance is incomplete; real capture remains unauthorized |
| 30 | Final status | BLOCKED |

## Scope, reused evidence and rollback

Previously validated unreadable/mutating/disappearing-source, hash-mismatch, heartbeat/observer, sampler, lineage, queue, manifest/archive and capacity rejection evidence is retained. Relevant implementation files were compared with frozen candidates. These prior tests are not counted as new large-run checks and do not substitute for the unexecuted acceptance gate. Fresh checks in this attempt were integrity/metadata/host preflight, four orchestration tests, syntax validation and source admission, which failed.

The original protected collector, hardened diagnostic candidate, calibration and previous archives remain unchanged. Changes are new report files and a separate diagnostic integration copy only. No production JARVIS code/configuration/data, VM permission, Windows security setting, provider or threshold was changed. No commit was created.

Rollback requires no production action: retain the rejected integration copy as evidence and do not select it for a new campaign until its synthetic dataset containment is corrected and reviewed. Do not delete historical evidence.

HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
