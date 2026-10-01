# Stage 6 — resumed kernel authority qualification

**KERNEL_AUTHORITY_STILL_DEFECTIVE**

The live capture succeeded, but full qualification failed its required-verification coverage audit. This is an evidence/qualification-adapter defect, not evidence of a Windows kernel failure or a JARVIS production defect. Small combined validation was NOT RUN.

## Preservation and execution

Preflight independently reread/hash-verified all 402 prior archive members and checked all 401 archived source/evidence files against that manifest. All 510 earlier preservation checks matched. The completed 12,000-record / 45-segment durability run and 14 expected rejection cases were preserved and were **not repeated**.

Fresh run: `D:\JARVIS-STAGE6-LIVE\a684e9f6f9ae4826af45c0a04c18d839\code\identity-33a0d87538384974ae2c71b49c62f689`.

The owner approved the kernel tracer and independent application-event observer UAC prompts. Both started successfully this time. The preserved launcher, collector, binaries and frozen checker were unchanged. Exact execution used:

```powershell
& 'D:\JARVIS-STAGE6-LIVE\a684e9f6f9ae4826af45c0a04c18d839\code\qualified_launch.ps1' -Run identity-33a0d87538384974ae2c71b49c62f689
```

The second UAC launch was released only after `KERNEL_READY_WAITING_FOR_SECOND_PROMPT`. No medium/large run, dataset hashing, protected VM/configuration access, VirtualBox launch or production operation occurred.

## Actual positive evidence

| Requirement | Result |
|---|---|
| Real probe set | 16: four ordinary, four repeated/rapid launches, eight concurrent identical probes. |
| Persisted kernel lifecycle | 72 records; 36 STARTs and 36 STOPs, four segments; contiguous global sequence, hashes, durable manifest/seal and final states verified. |
| Scope | 34 worker/descendant identities; two observer/infrastructure identities recorded separately. No missing tracked kernel START/STOP was found. |
| Canonical identity | Capture session + subject PID + kernel creation FILETIME + ProcessSequenceNumber. Parent identity checked against parent sequence and lifetime; never PID-only. |
| Probe positive unique matches | 16/16 matched independently to retained process creation/exit times, exit code and native PE entry. Exact image paths matched using captured QueryDosDevice mappings; not basename-only. |
| Observed kernel identity ambiguity | Zero in this captured set; zero observed false unique probe matches. This does not prove missing verification records are safely rejected. |
| Retained kernel handles | 20 across full capture; 18 in tracked worker tree. Remaining 16 identities satisfy the existing qualified post-exit acquisition rule. |
| Required independent image coverage | Only 16/18 retained tracked identities have the required recorded comparison. Worker and one helper are missing that independent evidence. **FAIL**. |
| Native PE-entry | All 16 probe entries lie between matching kernel START and STOP; native exit/retained proof agrees. Coverage outside the probe set is not invented. |
| PID reuse | No actual process or parent PID reuse occurred. A separate two-incarnation fixture verifies distinct PID+creation+sequence handling and rejects a wrong-incarnation STOP. This is not real OS reuse evidence. Parent reuse remains unexercised. |
| ETW loss counters | Faults, events lost and both buffer-loss counters zero; control/consumer exit codes zero. |
| CIM | 86 raw events independently persisted; 66 AMBIGUOUS, 20 UNMATCHED, zero forced UNIQUE. Every correlation/token is preserved. These counts are new and distinct from historical 21/1. |
| CIM queue | Enqueued/selected/persisted/removed = 86 each; remaining zero; no collector/tap error or overflow. |
| Heartbeat | Maximum interval 1.1075672 s; maximum observed live age 1.029939 s; threshold unchanged at 10 s. |
| Deadline | Zero probe deadline violations; original process/observer limits unchanged. |
| Observer/worker closure | Kernel, application observer and worker each exited with code zero. Native tracing threads exited; handles reconciled and closed. |

`qualification-result.json` records the earlier positive component checks, with `combinedAcceptance=false`. It is not the final disposition: the subsequent `coverage-audit.json` explicitly fails qualification. Neither record is overwritten or hidden.

## Exact blockers

### Missing independent evidence for two retained tracked identities

| PID | Creation FILETIME | Kernel sequence | Role |
|---|---|---|---|
| 15636 | 134344496080300147 | 43359 | Python worker |
| 17088 | 134344496080379803 | 43360 | Worker's console helper |

Both have complete kernel lifecycle and kernel-retained handle creation/exit records. However, the qualification driver records independent probe image/handle comparison only for the 16 probes. It did not retain an independent handle-image comparison record for these two additional retained identities. A kernel image string must not be relabeled as an independent image query. Their processes have exited, so that missing historical observation cannot be reconstructed now.

This is an evidence gap, not an observed identity contradiction. The gap still blocks the acceptance requirement covering retained handles where present.

### Draft qualifier can omit mandatory verification records

The test passes a **copy** of the fresh kernel evidence to the existing unaccepted draft `qualification.py`, with both `handles=[]` and `natives=[]`.

- Expected: FAIL — mandatory independent verification omitted.
- Actual: PASS.
- Cause established from source: `qualify()` loops over the supplied handle list and checks native entries inside that loop. It has no required-coverage set enforcing which identities must supply those records. An empty list bypasses those checks.

This is a demonstrated draft-adapter defect. The frozen acceptance checker was never modified or invoked as if it implemented the amended contract.

## Negative/contract tests

23 focused cases met their expected dispositions. They include the ten requested contract cases, ETW/buffer loss, duplicate START, missing native entry, forced CIM matching, parent contradiction, retained-handle metadata error, distinct same-PID fixture lifetimes, wrong-incarnation STOP, sequence gap, missing/corrupt segment and missing acceptance seal.

The three CIM disposition cases use explicit unit fixtures; the UNIQUE case is not a claim that the actual CIM schema supplied a discriminator. The actual raw CIM stream remains ambiguous/unmatched. The sequence-gap test recalculates its disposable manifest/hash envelope so rejection demonstrates sequence validation rather than only a hash mismatch. All mutations occur in new disposable fixture directories, never in the real captured run.

The additional required-verification omission test **failed**: expected rejection, actual PASS. Thus **23 expected-disposition checks passed / 1 failed**, plus the separate two-identity coverage deficiency. Those results must not be summarized as all qualification tests passing.

Evidence: `contract-tests.json`, `coverage-audit.json`, `qualification-inputs.json`, `cim-correlations.json` and the preserved real run.

## Minimum proposed correction — not implemented

1. In a new versioned TEST adapter, derive the required independent-verification set from the independently established launch/lineage inventory and preserved rules. Do not let the presence/absence of caller-supplied lists define the required set. Reject missing, duplicate, unknown or contradictory required records, including empty-list input.
2. Extend the TEST evidence driver to capture the missing retained-handle image/creation/exit observations for the worker and retained descendants before handles close, preserving existing native-entry applicability and qualified post-exit rules. Never query an exited/reused PID to fill old evidence.
3. Add empty/partial/duplicate coverage regressions and full-path image contradiction tests. Preserve existing kernel loss/sequence/segment and handle/native fail-closed tests.
4. Run a fresh bounded qualification after that correction. Preserve this run unchanged. Record actual PID/parent reuse only if it occurs; explicitly retain fixture-versus-real distinctions.
5. Only if full qualification passes, run the separately approved SMALL combined validation. Do not integrate into the frozen checker, perform medium/large validation or access protected data.

Likely files: a new TEST qualifier/adapter, the qualification worker/launcher or existing retained-tree evidence helper, and focused tests. No JARVIS runtime/security/authority changes are proposed. The durable writer need not be changed to address this demonstrated coverage defect.

## Cleanup, integrity and rollback

Final host-context inventory: zero matching diagnostic/VirtualBox processes and zero diagnostic trace sessions. All 401 previous source/evidence files and 510 preservation checks still match. Frozen checker SHA-256 remains `e6fbefd3fd463c6c8e09d0e8273a81b46ee2806515cae05e7837ea905a3e69d6`. The unaccepted qualifier itself also remains unchanged.

Only new analysis/test scripts, fresh-run output, disposable mutated fixtures and report/archive material were added. The report archive receipt supplies the actual member count and hashes after independent verification. No evidence was rewritten and no commit was created. Rollback is to leave this unaccepted evidence/candidate unpromoted; no production rollback is needed.

Protected VM/configuration: NOT ACCESSED. Production: UNCHANGED. Historical **21 AMBIGUOUS / 1 UNMATCHED** unchanged. Historical delay causes UNCONFIRMED. **HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.**

Final status: **KERNEL_AUTHORITY_STILL_DEFECTIVE**. Combined validation and frozen-checker integration are not eligible yet.
