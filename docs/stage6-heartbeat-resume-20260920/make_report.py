import json, pathlib
from prepare import R
def read(n):return json.loads((R/n).read_text(encoding='utf-8-sig'))
a=read('loads2-reconciliation.json')
target=r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 HEARTBEAT RESUME 20260920'
text='''# Stage 6 heartbeat durability-decoupling resumed validation — 2026-09-20

**MONITOR_STILL_DEFECTIVE — process-event coverage requirement fails.**
This is the acceptance disposition of the monitor pipeline, not a claim that the loss has been located in PowerShell, CIM, Windows, or storage. Protected hashing remains prohibited. No dry run was started.

1. **Files changed.** No existing candidate or JARVIS runtime source was edited. A new `stage6-heartbeat-resume-20260920` evidence directory contains 19 byte-identical validation-source copies, `prepare.py`, `run_focused.py`, `test_event_rejection.py`, `reconcile.py`, `verify_processes.py`, `make_report.py`, `archive.py`, preserved analysis-script v1, report, diffs, manifests and generated test evidence. `validation-source-copy.json` identifies every copied file/hash. The original candidate's earlier correction consists of changed `monitor.ps1` and `resources.ps1`, plus new `DESIGN.md`, `campaign.py`, `finalize.py`, `hash_sources.py`, `Start-DryRun.ps1`, `test_extended_finalization.py`, `test_finalization.py`, `test_probe_handles.py` relative to the checked predecessors. Two preserved source versions are historical material, not additional runtime corrections. `prior-source-reconciliation.json` records exact comparisons. The unchanged journal reader retains its ten-second limit.

2. **Preserved-state audit.** 352 existing files were inventoried, SHA-256 hashed, copied and rechecked without modification. The corrected loads2 run completed all five phases on September 18, including C: hashing; it was not left interrupted. Its independent finalizer exited 1 with `RuntimeError: Event count mismatch` at `finalize.py:38`. The earlier ambiguous-PID loads run remains rejected. Neither dry1 nor dry2 contained acceptance evidence. No successful finalization receipt was manufactured.

3. **Corrected harness.** Preserved loads2 records 77 distinct PID/creation-time identities, all with retained-through-finalization flags and exit code zero. Today's Windows-handle regression independently retained and queried 50 distinct identities successfully. `J6Probe.exe` is hash-identical to installed System32/whoami.exe (SHA-256 23240ef9f8b0a9a324110b1c2331de31dc1b0e08f5359cb707e51a939af56cd3). It is a sacrificial process probe, not JARVIS or VirtualBox.

4. **Focused tests.** 50 executed, 50 passed, 0 failures, 0 errors, 0 skips; 23.781 seconds. Six modules: test_journal (22), test_processes (9), test_finalization (14), test_extended_finalization (1), test_probe_handles (1), test_event_rejection (3). The latter adds explicit duplicate-PID, missing-stop and wrong-PID rejection tests without changing monitor/finalizer semantics. Command:

```powershell
& 'C:\\Users\\jonny\\Documents\\Codex\\2026-09-07\\cr\\outputs\\jarvis\\.venv\\Scripts\\python.exe' -B 'C:\\Users\\jonny\\Documents\\Codex\\2026-09-07\\cr\\outputs\\jarvis\\docs\\stage6-heartbeat-resume-20260920\\run_focused.py'
```

5–7. **Five-class results, intervals and age.** Values below are recovered from corrected loads2 evidence, not a newly claimed rerun. All heartbeat measurements stayed under 10 seconds. C: reads failed event coverage, so the combined campaign failed. Other rows meet their measured heartbeat/event checks but do not provide standalone accepted campaign receipts.

| Workload | Duration s | Max heartbeat interval s | Max observed age s | Starts / expected | Stops / expected | Measured heartbeat/event result |
|---|---:|---:|---:|---:|---:|---|
'''
names={'idle':'Idle','disk':'C: reads','sustained':'C: hashing','cpu':'CPU only','Dhash':'D: hashing; journal on C:'}
for p in a['phases']:
    text+=f"| {names[p['phase']['mode']]} | {p['duration_seconds']:.3f} | {p['heartbeat_intervals']['max']:.6f} | {p['observed_age']['max']:.6f} | {p['captured_starts']}/{p['expected_starts']} | {p['captured_stops']}/{p['expected_stops']} | {'FAIL — missing stops' if p['captured_stops']!=p['expected_stops'] else 'PASS (measured checks)'} |\n"
text+='''
Overall maximum observed age: **7.0791509 seconds**. Complete count/min/median/p95/max distributions, observed performance-counter paths and values are in `loads2-reconciliation.json`; original observations are in `preserved-original/loads2/`.

| Workload | Max stream Write s | Max Flush(false) s | Max event-drain s | Max wait-overrun upper bound s | Peak total CPU % |
|---|---:|---:|---:|---:|---:|
'''
for p in a['phases']:
    s=p['stage_seconds'];cpu=next(v['max'] for k,v in p['resource_counters'].items() if 'processor(_total)' in k.lower())
    text+=f"| {names[p['phase']['mode']]} | {s['journal.write']['max']:.7f} | {s['journal.flush']['max']:.7f} | {s['drain']['max']:.7f} | {p['scheduling_wait_overrun_upper_bound_seconds']:.7f} | {cpu:.2f} |\n"
text+='''
Write and ordinary flush are separately measured; they are not guaranteed nonblocking. Wait overrun is an upper bound, not measured CPU scheduler latency. Resource samples overlapping phase edges are retained, so counters are not exact causal attribution to the synthetic workload. Observed C: read peaks during C: reads/hash: 154,384,057.946 / 148,847,418.106 bytes/sec. D: read peak during D: hash: 234,068,945.202 bytes/sec. No collector stale-heartbeat or monitor failure was recorded; downstream finalization failed.

8. **Process events.** Expected 77 starts + 77 stops = 154. Captured 77 starts + 74 stops = 151. Missing stop PIDs 13248, 22544, 21896, all during C: reads; each has a recorded successful wait/exit and creation identity. The missing stop events are absent from the entire saved event file, not merely misplaced in its ordering. Final drain recorded zero backlog and no newly drained events. This does not establish whether an event was never emitted, delayed outside collection, lost by the provider/subscription or omitted by the consumer.

9. **Identity integrity.** No duplicate PID in corrected loads2; no observed event attributed to an unexpected probe PID. Full start/stop identity coverage FAILS due to missing records. The finalizer matches event PID/kind/name to a handle-retained probe set; it does not obtain a separate creation-time field from every CIM event. Today's duplicate/wrong-PID synthetic rejection tests PASS. A read-only 197-record historical/current identity check initially had four access denials; a host-context read-only check proved all four PIDs now belong to unrelated, newer processes. Zero matching identities remained among the checked records; no process was terminated for cleanup. Workload subprocesses lacking independently saved creation times are not retroactively identity-proven by this check.

10. **Failure injection.** Passed focused fixtures cover publisher termination; reader termination/restart; inaccessible journal (injected PermissionError, not ACL mutation); malformed append; stale/stalled publisher including actual 10.25-second pause; delayed durable finalization; injected final flush failure; evidence-copy hash failure; actual sacrificial hashing-worker death; wrong-PID identity mismatch; duplicate PID rejection. Finalization withheld acceptance for 10.203524 seconds, then finished in 0.074420 seconds after release. No false final acceptance in these tested cases. This does not claim real disk-full, hardware power-loss or Windows ACL failure was exercised where only exceptions were injected.

11. **Dry Run #1:** NOT RUN — corrected load event-coverage gate fails.

12. **Dry Run #2:** NOT RUN — Dry Run #1 cannot be admitted.

13. **Durable finalization:** focused success/failure/hash fixtures PASS; actual loads2 finalization REJECTED with exit 1. Monitor journal final Flush(true) and monitor exit zero are recorded, but do not substitute for independent full-evidence finalization. Archiving this failed evidence does not turn it into accepted campaign evidence.

14. **Evidence archive:** `'''+target+'''`. Workspace receipt `archive-verification.json` records the final count/hash and archive manifest. The archived copy includes all 352 historical files, today's complete test evidence and failed analysis attempt.

15. **Hash verification:** all 352 historical originals and their preservation copies matched. The complete resumption/archive count is recorded in `archive-verification.json` after report creation to avoid circular self-hashing. Every listed payload, the manifest and the receipt are compared source-to-archive. Nineteen previously modified tracked file contents were rechecked unchanged; byte-identical copied monitor infrastructure is independently verified.

16. **Protected VM access:** none by this task; no protected VM/config file read, hash, modification or VirtualBox command. Prior runs are represented only by their saved evidence; no retroactive claim of independently audited protected-file access is made. Current snapshots show zero VirtualBox processes; host service query reports VBoxSDS stopped. No fresh privileged continuous subscription was started for focused fixture tests, so snapshots alone cannot prove no intervening external transient process.

17. **Production changes:** none by this task. Existing unrelated working-tree edits were left intact. No JARVIS, provider, production database or VM launched. No credentials loaded. No commit, ACL, security setting or service change.

18. **Uncertainty and preserved failures:** event loss location/root cause UNCONFIRMED. Historical 13.7-second and 14.084-second incident causes remain UNCONFIRMED. Supported narrower finding: synchronous FileStream.Flush(true) was experimentally demonstrated to produce >10-second stalls under heavy C: storage activity. Earlier ambiguous-PID run, delayed-finalization test failure and new loads2 failure remain preserved. Today's offline reconciliation initially used the wrong JSON field `startQpc` (actual `start_qpc`); its source/error are preserved in `preserved-reconcile-v1.py` and `reconciliation-failure-01.json`. Only the analysis key was corrected; this did not change tests, monitoring or earlier evidence. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

19. **Protected baseline capture justified:** NO. Required exact event coverage, two dry runs and full durable acceptance are not established. Next bounded diagnostic: instrument raw CIM notification receipt versus PowerShell queue drain and event-file append under the same sacrificial C: read/probe conditions. Preserve event IDs, subscription state/errors and raw/queued/written counts; do not add synthetic stop records, relax counts or extend deadlines merely to pass. No such new monitor correction was implemented in this pass.

20. **Final status:** MONITOR_STILL_DEFECTIVE. This disposition identifies a demonstrated acceptance failure, while the component-level cause remains unknown. Rollback is to leave this candidate unaccepted and stop using it for protected hashing; all additions are isolated evidence/test files. No production rollback is needed. No dry-run or protected-baseline retry command is offered while the gate fails.
'''
with (R/'REPORT.md').open('x',encoding='utf-8') as f:f.write(text)
