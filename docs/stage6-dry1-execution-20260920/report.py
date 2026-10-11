import pathlib,json
R=pathlib.Path(__file__).parent;v=json.loads((R/'run-verification.json').read_text());p=json.loads((R/'preflight.json').read_text());h=json.loads((R/'host-after.json').read_text());c=v['cleanup'];C=pathlib.Path(p['code'])
assert not h['matchingLive'] and not h['scopedProcesses'] and not h['traceSessions'] and h['traceQueryExit']==0
text=f'''# Sacrificial Dry Run #1 — 2026-09-20

DRY_RUN_1_PASS, with the accompanying HASH_VERIFIED canonical archive receipt.

One attempt only: `{v['run']}`. No automatic retry, harness correction, timeout adjustment, production operation, protected VM access or Dry Run #2 occurred.

## Evidence summary

| # | Requirement | Result |
|---|---|---|
| 1 | Pre-run integrity | PASS: 73 candidate hashes, 223 application hashes unchanged; previous 1,886-member archive reverified. 215 recorded identities checked, no matching live or scoped diagnostic/VirtualBox process; no J6Kernel session. D: free approximately {p['DfreeBytes']/2**30:.3f} GiB. No previous integrated dry1 run existed. |
| 2 | Sacrificial artifacts | 12 existing .bin files, {v['syntheticBytes']:,} bytes, exact approved source directory. |
| 3 | Hash pass #1 | PASS; {v['hashPass1Seconds']:.7f} seconds. Actual bytes read and SHA-256 computed for all 12. |
| 4 | Hash pass #2 | PASS; {v['hashPass2Seconds']:.7f} seconds. Independently reread all 12; hashes match pass #1. |
| 5 | Metadata preservation | PASS: preflight, run contract, both passes and post-run sizes/modification times agree. |
| 6 | Reconciled process identities | {c['total']} — collector, hash worker, eight policy probes and associated console/helper descendants. |
| 7 | Application START | {c['appStarts']} independently captured and persisted for tracked identities. |
| 8 | Application STOP | {c['appStops']} independently captured and persisted. |
| 9 | Kernel CREATE | {c['kernelCreates']}. |
| 10 | Kernel EXIT | {c['kernelExits']}. |
| 11 | Retained-handle exits | {c['handleConfirmed']}. |
| 12 | Qualified post-exit acquisition | {c['kernelPostExit']}; unchanged strict cleanup rule. |
| 13 | Unexplained identities | {c['insufficient']}; no PID reuse ambiguity. |
| 14 | Orphan helpers | 0; child/tree evidence reconciled and final identity check clear. |
| 15 | Maximum process lifetime | {v['maximumTrackedLifetimeSeconds']:.7f}s across the tracked tree. Probe maximum kernel lifetime {v['maximumProbeLifetimeSeconds']:.7f}s; maximum policy-confirmed elapsed {v['maximumProbeConfirmedSeconds']:.7f}s. Observer infrastructure uses its existing separate bounds. |
| 16 | Hard-deadline violations | {v['hardDeadlineViolations']}. Eight probes passed unchanged 13.6s policy and independent 15s observation. |
| 17 | Heartbeat | Maximum interval {v['maximumHeartbeatInterval']:.7f}s; maximum observed age {v['maximumHeartbeatAge']:.7f}s; both below unchanged 10s. |
| 18 | External EventIdentifier collisions | {c['externalEventIdentifierCollisions']} in this run. Existing collision protection unchanged. |
| 19 | Internal queue-ID collisions | {c['queueIdentityCollisions']}. |
| 20 | Quiescence/finalization | PASS: {v['queue']['enqueued']} raw application events enqueued/selected/persisted/removed; residue 0. Independent subscriptions closed, native trace stopped/consumer joined. No event loss or duplicate persistence. |
| 21 | Durable finalization | PASS; actual fsync/flush and finalizer receipts verified. |
| 22 | Baseline-style manifest | Created only after verified lifecycle closure and durable finalization; contents match both hash passes. |
| 23 | Manifest SHA-256 | `{v['manifestSHA256']}` |
| 24 | Archive verification | Dry-run archive: {v['runArchive']['members']} members independently reverified; SHA-256 `{v['runArchive']['sha256']}`. Canonical campaign archive receipt separately records its full member count and hash. |
| 25 | Live-process cleanup | PASS: {len(h['identities'])} prior/current identity observations checked; 0 matching live and 0 scoped diagnostic/VirtualBox processes. No forced termination. |
| 26 | Kernel trace cleanup | PASS: read-only enumeration returned success; 0 J6Kernel sessions. |
| 27 | Protected VM/config | NOT ACCESSED. No VirtualBox launch or protected hash/inventory/copy. |
| 28 | Production | UNCHANGED; 223 recorded application hashes match. All 73 candidate sources also unchanged. |
| 29 | Historical PID status | PID 13340/9240 causes UNCONFIRMED. Historical 87 helper gaps UNKNOWN. Prior kernel-only evidence remains kernel-only. |
| 30 | Final status | DRY_RUN_1_PASS. Stop before Dry Run #2. |

## Interpretation and preservation

The success conclusion uses actual hashes, native process identities/creation and exit records, independently persisted CIM lifecycle events, retained handles or strict post-exit proof, unchanged probe policy, final queue reconciliation, closed observers and verified archive bytes. It does not rely only on a launcher exit code.

Raw out-of-scope application notifications ({v['outsideApplicationEventCount']}) and native infrastructure records are preserved, explicitly excluded from the tracked 19-identity equation, and included where applicable in final host cleanup checks. The live checker has no insufficient identities or per-identity errors. Kernel faults/loss/flush/stop/consumer status are all zero. All application subscription and durable-finalization checks passed.

The two hash passes are full logical reads and SHA-256 computations; no uncached physical disk-read claim is made. This pass demonstrates current Dry Run #1 acceptance under observed conditions, not a proven cause for historical Windows/storage/probe delays. Historical failed runs remain failed and untouched.

No new regressions were run because the harness was unchanged and this authorization was one acceptance dry run only. Source/application hashes and previous acceptance archive were reconciled. Synthetic input files were read only, and no API keys, environment files or paid providers were used. All live artifacts remained within the D: run; archival to canonical storage occurred only after monitoring and cleanup ended.

Rollback requires no production or VM action: preserve the run and stop using it if later review finds an issue. Do not delete or rewrite prior evidence. No commit was created. Stage 6 is not declared complete, and protected baseline capture remains unauthorized.

HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

See PROPOSED-DRY-RUN-2.md for the next procedure, OWNER REVIEW ONLY.
'''
with (R/'REPORT.md').open('x',encoding='utf-8') as f:f.write(text)
procedure=f'''# Proposed sacrificial Dry Run #2 — OWNER REVIEW ONLY

NOT EXECUTED. Requires separate owner authorization.

Dry Run #2 should be a second independent execution of exactly the same frozen full-size sacrificial workflow, using a newly generated run directory and freshly started diagnostic observers. It must not reuse Dry Run #1 state, event records, process identities, manifests or results.

The validated CLI calls this workload scenario `dry1` and its raw receipt is `DRY_RUN_1_PASS`. That is its existing workload label. Proposed campaign bookkeeping would explicitly record the new execution as ordinal 2, retain the raw label unchanged, and link both independent run IDs. This avoids changing the validated harness merely to rename the second execution. Owner review should accept this mapping before proceeding; no raw evidence would be relabelled or overwritten.

1. Reverify the 73 frozen candidate hashes and the current canonical Dry Run #1 archive, 223 application hashes, unchanged sacrificial input metadata, D: capacity, zero matching diagnostic identities/processes, zero J6Kernel sessions and zero VirtualBox processes. Existing Dry Run #1 evidence is expected and must be retained; it is not reusable live state.
2. Record a new campaign-ordinal-2 intent outside the live heartbeat path, referencing the first run `{v['run']}` and the frozen candidate manifest. Do not change source or timeout values.
3. After owner approval only, launch the existing full workflow once:

```powershell
& 'C:\\Users\\jonny\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\native\\powershell\\pwsh.exe' -NoProfile -File '{C}\\dry_launch.ps1' -Scenario dry1
```

4. Approve only the known J6KernelTrace.exe and independent app_monitor.ps1 UAC prompts. Confirm the launcher creates a different `integrated-dry1-<GUID>` directory. Cancelled UAC, missing evidence, deadline/heartbeat violation or any acceptance failure means STOP, preserve and reconcile cleanup; no automatic retry.
5. Independently verify both full hash passes, preserved metadata, complete application and kernel streams, strict cleanup proof, unchanged deadlines, empty final queue, durable manifest, archive bytes and zero live identities/sessions. The raw success label alone is insufficient. Record the result as the second campaign attempt only through the explicit ordinal/run-ID mapping.
6. Archive/hash-verify finalized nonsecret evidence to TEAGUE INDUSTRIES DATABASE, then STOP for owner review. Do not perform protected baseline hashing or launch VirtualBox.

No scenario or harness changes are proposed in this procedure. If owner review requires a literal `dry2` selector instead of the explicit campaign-ordinal mapping, that would be a separately reviewed harness-label change, not part of this pass.
'''
with (R/'PROPOSED-DRY-RUN-2.md').open('x',encoding='utf-8') as f:f.write(procedure)
with (R/'disposition.json').open('x') as f:json.dump(dict(status='DRY_RUN_1_PASS',attempts=1,harnessChanged=False,dryRun2Executed=False,protectedAccess=False,productionChanged=False,protectedBaselineAuthorized=False,historical87='UNKNOWN',PID13340='CAUSE_UNCONFIRMED',PID9240='CAUSE_UNCONFIRMED',archiveReceiptRequired=True),f,indent=2)
print('DRY_RUN_1_PASS; canonical archive receipt pending')
