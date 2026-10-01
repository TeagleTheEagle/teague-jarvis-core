import pathlib,json
R=pathlib.Path(__file__).parent;plan=json.loads((R/'plan.json').read_text());C=pathlib.Path(plan['code']);m=json.loads((R/'miniature-summary.json').read_text());r=json.loads((R/'regression-summary.json').read_text());h=json.loads((R/'host-final.json').read_text())
assert not h['matchingLive'] and not h['scopedProcesses'] and not h['traceSessions'] and h['traceQueryExit']==0
v=dict(status='DRY_RUN_HARNESS_VALIDATED',dryRun1Executed=False,dryRun2Executed=False,protectedBaselineAuthorized=False,stage6Advanced=False,protectedAccess=False,productionChanged=False,historical87='UNKNOWN',PID13340='CAUSE_UNCONFIRMED',PID9240='CAUSE_UNCONFIRMED',historicalStage1='UNCONFIRMED',archiveReceiptRequired=True)
with (R/'disposition.json').open('x') as f:json.dump(v,f,indent=2)
text=f'''# Stage 6 full dry-workflow harness integration — 2026-09-20

DRY_RUN_HARNESS_VALIDATED, with the accompanying HASH_VERIFIED archival receipt. This validates the TEST harness and miniature end-to-end run only. Dry Run #1 and #2 were NOT RUN. Stage 6 status was not advanced; protected baseline hashing remains unauthorized.

## Mandatory report

| # | Requirement | Result |
|---|---|---|
| 1 | Exact files changed | Seven new files in `{C}`: dry_contract.py, dry_health.py, dry_hash_worker.py, dry_collect.py, dry_finalize.py, dry_launch.ps1, test_dry_integration.py. Existing 66 candidate files untouched. Report/preparation/regression/archive scripts are additional evidence tooling under this report directory. |
| 2 | Pre-change hashes | source-before.json lists all 66 exact prior paths/hashes; original-source-preservation.json confirms original and copied files unchanged. New files have no prior hash. final-source.json records all 73 final candidate hashes. |
| 3 | Original mode producer | launch.ps1:7; idle/disk/sustained/cpu/Dhash/dry workload labels. Historical file unchanged. |
| 4 | Original phase consumer | collect.py imports collect_hardened.py; collect_hardened.py:11 requires A-E diagnostic subset. Different semantics; no blind rename. |
| 5 | Canonical contract | Version-1 contract.json pins scenario, run ID, allowlisted input inventory and immutable thresholds. state.json owns ordered phases/history. Single writer per phase, explicit handoff at child/observer exit. DESIGN.md contains complete flow. |
| 6 | Compatibility | Old mode/letter-phase input rejected before observers. Historical entry points retained for reference and old tests; they are not the supported integrated dry command. No silent translation. |
| 7 | Workflow map | prepare/validate → both independent observers ready → hash worker + real policy probes → hash1 → hash2 → metadata → worker/probe closure → observer quiescence/closure → unchanged cleanup checker → fsync evidence → manifest/hash → archive verification → final metadata verification. |
| 8 | Dual evidence | PASS: {m['cleanup']['appStarts']} application START, {m['cleanup']['appStops']} application STOP, {m['cleanup']['kernelCreates']} kernel create, {m['cleanup']['kernelExits']} kernel exit. Independent CIM stream, ETW stream and retained handles, no synthetic lifecycle records. |
| 9 | D: containment | All active state/evidence/control/temp/manifest/archive paths under unique D: run. Mini input there too; full dry input is only the pinned pre-existing sacrificial C: directory. Protected/arbitrary/reparse inputs rejected. No environment change outside child process scope. |
| 10 | Focused tests | 30/30 PASS before miniature; 30/30 repeated in final regression suite. Tests include legacy contract, phase/stale rejection, hash/metadata, containment, failed lifecycle, primary error, flush/archive failures. |
| 11 | Miniature integration | MINIATURE_INTEGRATION_PASS. `{m['run']}`. 12 × 4096-byte synthetic artifacts = 49,152 bytes; no full-sized dry run. |
| 12 | Hash pass #1 | PASS: all 12 actual tiny files hashed. |
| 13 | Hash pass #2 | PASS: independently reread and hashed; all hashes/metadata equal. Both passes lie inside the independently recorded hash-worker kernel lifetime. |
| 14 | Lifecycle | 7 identities = 6 retained-handle exits + 1 strictly qualified post-exit acquisition; 0 unexplained identities. All children/helpers accounted by independent tree matching. |
| 15 | Heartbeat | PASS: max interval {m['heartbeatMax']:.7f}s; max hash-worker observed age {m['hashHeartbeatMaxAge']:.7f}s; max collector observed age {m['collectorHeartbeatMaxAge']:.7f}s; fixed 10s limit unchanged. |
| 16 | Cleanup | PASS: both observers exited normally, retained handles closed, no primary failure. Probe count {m['probeCount']}, max policy-confirmed duration {m['probeMaxConfirmedSeconds']:.6f}s, hard-deadline violations {m['hardDeadlineViolations']}. |
| 17 | Finalization | PASS: independent application collector unsubscribed, quiescence completed, final drain empty; native trace stopped/consumer joined. Queue 19 enqueued/selected/persisted/removed, residue 0. Offline acceptance began only after OBSERVERS_CLOSED. |
| 18 | Manifest | PASS after CLEANUP_VERIFIED and durable FINALIZED. SHA-256 `{m['archive']['manifestSHA256']}`. |
| 19 | Archive | Miniature archive {m['archive']['members']} members verified; SHA-256 `{m['archive']['sha256']}`. Entire campaign/report archive separately copied/hash-verified to canonical database; see archive-verification.json. |
| 20 | Regressions | {r['total']} unittest cases PASS: integration 30, dual 40, kernel 12, hardening 24, probe 26, monitor 69. Queue {r['queueAssertions']} assertions PASS including 10,000-event collision stress. Finalization {r['finalizationAssertions']} executed assertions PASS. Eight command groups exit 0. Actual counts retained rather than copied from previous runs. |
| 21 | Live processes | 0 matching live across {len(h['identities'])} recorded identities from this and preceding campaigns; 0 scoped diagnostic/VirtualBox processes. No termination performed. |
| 22 | Trace sessions | 0 J6Kernel sessions; read-only enumeration succeeded. |
| 23 | Production | UNCHANGED: 223 recorded application hashes match. No JARVIS launch/provider/configuration change. |
| 24 | Protected VM/config | NOT ACCESSED; no inventory, hash, copy or VirtualBox launch. Invalid protected-path unit test rejects text before any filesystem access. |
| 25 | Dry Run #1 readiness | Harness entry point exists, contract consistent, candidate frozen, full sacrificial 12-file input available (1,073,786,880 bytes; metadata only inspected). Ready for owner review; live preflight must be repeated at actual execution. |
| 26 | Final status | DRY_RUN_HARNESS_VALIDATED. Stop before Dry Run #1. |

## Integration-test requirement coverage

H7.1/2: focused contract tests 1–3/22/30. H7.3/4/5: tests 4–6 plus actual miniature hash files. H7.6/7/8: actual miniature independent events, kernel worker lifetime and live heartbeat/liveness samples; mocks are not used for those conclusions. H7.9/10/11/12: live state history and observer exit receipts plus tests 9–12/23/26/28. H7.13/14/15: explicit failure tests 26, 11 and 27. H7.16/18: tests 13–16 and fixed source/containment checks. H7.17: actual 223-file preservation reconciliation. H7.19/20: tests 17–19/22/24. Detailed logs are in the D: integration-focused-1.txt and integration-regress directory.

The miniature native trace also records infrastructure outside the collector tree; those records remain in raw evidence and final identity inventory. Counts above are the reconciled collector/hash-worker/probe/helper tree, not raw machine-wide CIM counts. Out-of-scope notifications are retained, not counted as missing tracked events. The three evidence mechanisms are independent collection paths over the same Windows OS, not independent operating systems.

## Preserved scope, limitations and rollback

No accepted cleanup, EventIdentifier, queue, heartbeat threshold or probe deadline semantics changed. Original historical failures and previous archives remain unchanged. Fresh runs cannot explain historical PID 13340/9240 causes (UNCONFIRMED) or turn 87 historical helper gaps into known exits (UNKNOWN). HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Unit tests deliberately preserve expected injected failure artifacts. There was no failed miniature live run or hidden retry. Phase/writer integration is new TEST infrastructure; production runtime and accepted components are untouched. No acceptance commit was created.

The miniature proves integration, not large-file timing reliability. C: runtime/Windows executable dependencies remain; all critical live monitoring state is D:. Full-size hashing and the historical hard-deadline scenario remain unvalidated until the separately approved Dry Run #1 succeeds. Fresh preflight, sufficient free space, and the two known diagnostic UAC approvals are still needed then.

Rollback: discontinue the new D: candidate, preserving all its evidence, and retain the unchanged prior accepted diagnostic candidate. No production or VM restoration/deletion is required. Do not run historical launch.ps1 as an integrated dry run; only the documented dry_launch.ps1 entry point represents the new canonical contract.

See DRY-RUN-1-PROCEDURE.md for the exact reviewed command. It was NOT executed in this pass.
'''
with (R/'REPORT.md').open('x',encoding='utf-8') as f:f.write(text)
procedure=f'''# Dry Run #1 procedure — OWNER REVIEW ONLY

This command is provided for the next authorization. It has NOT been executed. It runs only the pinned sacrificial workflow, never protected VM hashing, and cannot select Dry Run #2.

1. Keep VirtualBox closed. Recheck zero matching diagnostic processes/identities and zero J6Kernel trace sessions, unchanged frozen candidate hashes, D: space, prior archive integrity and the 12 allowlisted sacrificial inputs. A failed preflight means STOP; do not retry or change a limit.
2. Run in an ordinary Windows PowerShell terminal after owner approval. Do not run the whole shell as administrator; only the two read-only diagnostic observers request UAC. No execution-policy change is needed.

```powershell
& 'C:\\Users\\jonny\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\native\\powershell\\pwsh.exe' -NoProfile -File '{C}\\dry_launch.ps1' -Scenario dry1
```

3. Approve the identified J6KernelTrace.exe UAC prompt followed by the independent app_monitor.ps1 PowerShell observer prompt. If either is canceled, preserve the new run and its cleanup result; do not automatically rerun.
4. The launcher prints a fresh `integrated-dry1-<GUID>` directory. Require final `DRY_RUN_1_PASS`, independent identity reconciliation, two matching hash passes, unchanged source, fixed deadline compliance, durable manifest/archive verification and authenticated-by-record observer identity/exit proof. A command exit code alone is insufficient.
5. Reconcile the run against the 30-item Dry Run #1 acceptance checklist, recheck no live recorded identities/diagnostic sessions/VirtualBox, verify final source hashes, then archive finalized evidence to TEAGUE INDUSTRIES DATABASE. Preserve any failure.
6. STOP for owner review. Do not run Dry Run #2 or protected baseline capture.

The full-size source allowlist is `{repo / 'docs/stage6-heartbeat-journal-20260918/sacrificial'}`. Its only permitted inputs are the 12 existing .bin files. The launcher has no arbitrary source-path argument. All live output/temp/control/manifest state is under D:.
'''
with (R/'DRY-RUN-1-PROCEDURE.md').open('x',encoding='utf-8') as f:f.write(procedure)
print(v['status'])
