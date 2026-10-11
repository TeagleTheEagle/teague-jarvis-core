import pathlib,json
R=pathlib.Path(__file__).parent
v=json.loads((R/'run-verification.json').read_text());p=json.loads((R/'preflight.json').read_text());h=json.loads((R/'host-after.json').read_text());c=v['cleanup']
assert not h['matchingLive'] and not h['scopedProcesses'] and not h['traceSessions'] and h['traceQueryExit']==0
assert c['status']=='PASS' and not c['errors'] and v['state']['phase']=='VERIFIED'
report=f'''# Sacrificial Dry Run #2 — 2026-09-20

DRY_RUN_2_PASS, subject to the accompanying HASH_VERIFIED canonical archive receipt.

One fresh execution; no retry. The frozen workflow's existing selector remains `dry1` and raw receipt remains `DRY_RUN_1_PASS`. `campaign-intent.json` explicitly identifies this independent execution as campaign ordinal 2. No raw receipt was renamed or rewritten. Fresh observers and process identities were verified against Dry Run #1.

| # | Required evidence | Result |
|---|---|---|
| 1 | Run ID | `{pathlib.Path(v['run']).name}` |
| 2 | Sacrificial files | {v['syntheticFiles']}; {v['syntheticBytes']:,} bytes |
| 3 | Both hash passes | PASS: {v['hashPass1Seconds']:.7f}s and {v['hashPass2Seconds']:.7f}s; every SHA-256 matches |
| 4 | Source metadata | PASS: sizes/modification times agree before, during and after |
| 5 | Reconciled identities | {c['total']} |
| 6 | Retained-handle exits | {c['handleConfirmed']} |
| 7 | Qualified post-exit cases | {c['kernelPostExit']}; existing strict rules satisfied |
| 8 | Unexplained identities | {c['insufficient']}; no checker errors |
| 9 | Orphan/helper result | PASS: all tracked descendants reconcile; zero orphan helpers |
| 10 | Deadline violations | {v['hardDeadlineViolations']}; {v['probeCount']} probes satisfy unchanged 13.6s/15s rules |
| 11 | Maximum heartbeat interval | {v['maximumHeartbeatInterval']:.7f}s; maximum observed age {v['maximumHeartbeatAge']:.7f}s; below unchanged 10s |
| 12 | START/STOP reconciliation | Application {c['appStarts']}/{c['appStops']}; kernel CREATE/EXIT {c['kernelCreates']}/{c['kernelExits']} |
| 13 | Finalization | PASS: {v['queue']['enqueued']} raw events enqueued/selected/persisted/removed, residue zero; durable finalization PASS |
| 14 | Durable manifest | PASS; SHA-256 `{v['manifestSHA256']}` |
| 15 | Archive | Raw run archive: {v['runArchive']['members']} members verified. Complete canonical campaign archive count/hash recorded in archive-verification.json |
| 16 | Final cleanup | {len(h['identities'])} known identity observations checked; zero matching live identities/processes, zero scoped diagnostic/VirtualBox processes, zero J6Kernel trace sessions |
| 17 | Protected VM/configuration | NOT ACCESSED; no protected hashing, inventory, copying or VirtualBox launch |
| 18 | Production | UNCHANGED; {v['applicationHashCount']} recorded application hashes unchanged |
| 19 | Candidate source | {v['candidateHashCount']} hashes unchanged; no harness/deadline correction |
| 20 | Proposed next procedure | PROPOSED-PROTECTED-BASELINE.md — OWNER REVIEW ONLY; not executed |

Full run directory: `{v['run']}`.

Preflight reverified Dry Run #1's 131-member canonical archive and its original source files. Final archival repeats that preservation check. Existing sacrificial input bytes were read again; mutable state, observers, events, contracts and output evidence were fresh. All live artifacts remained on D:. Canonical archival occurs only after observers and live collection have closed.

Maximum tracked process lifetime: {v['maximumTrackedLifetimeSeconds']:.7f}s. Maximum probe kernel lifetime: {v['maximumProbeLifetimeSeconds']:.7f}s; maximum policy-confirmed elapsed: {v['maximumProbeConfirmedSeconds']:.7f}s. External EventIdentifier collisions: {c['externalEventIdentifierCollisions']}; internal queue-ID collisions: {c['queueIdentityCollisions']}. The existing exact-entry collision protection remains unchanged.

The {v['outsideApplicationEventCount']} out-of-scope application notifications and native observer/infrastructure records remain preserved and explicitly excluded from the tracked identity equation. Relevant identities were included in the final host check. The cleanup checker's raw `acceptance:false` is its diagnostic-only scope marker, not a failed verdict: `status:PASS`, no errors, and the integration finalizer separately verifies every dry-run acceptance condition. No kernel lifecycle evidence was synthesized from retained handles.

Raw run archive SHA-256: `{v['runArchive']['sha256']}`. The full campaign archive additionally contains report/check scripts, receipts and frozen candidate source snapshots.

## Limits and preservation

This is one successful independent sacrificial repetition, not proof that historical delays were explained. Full logical reads were hashed; no uncached physical disk-read claim is made. The approximately 1 GiB input does not prove that the protected approximately 55.6 GiB tree will fit the current fixed collector/monitor bounds.

Historical failed runs remain failed. PID 9240/13340 causes remain UNCONFIRMED; historical 87 helper gaps remain UNKNOWN. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

No additional regression campaign was run: the user authorized this single dry run with the validated harness unchanged. Existing regression results were preserved, not relabelled as newly executed tests. No paid providers, credentials, production runtime, VM or normal VirtualBox configuration were used. No commit was created.

Rollback requires no runtime, production or VM changes: retain the evidence and discontinue use of the candidate if later review identifies a defect. Do not delete earlier runs.

Stage 6 is not declared complete. Protected baseline capture remains unauthorized. STOP for owner review.
'''
with (R/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
with (R/'disposition.json').open('x') as f:json.dump(dict(status='DRY_RUN_2_PASS',attempts=1,campaignOrdinal=2,rawHarnessStatus=v['rawHarnessStatus'],run=v['run'],harnessChanged=False,protectedAccess=False,productionChanged=False,protectedBaselineAuthorized=False,archiveReceiptRequired=True),f,indent=2)
print('Report prepared; canonical archive verification required')
