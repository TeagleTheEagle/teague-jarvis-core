# Proposed sacrificial Dry Run #2 — OWNER REVIEW ONLY

NOT EXECUTED. Requires separate owner authorization.

Dry Run #2 should be a second independent execution of exactly the same frozen full-size sacrificial workflow, using a newly generated run directory and freshly started diagnostic observers. It must not reuse Dry Run #1 state, event records, process identities, manifests or results.

The validated CLI calls this workload scenario `dry1` and its raw receipt is `DRY_RUN_1_PASS`. That is its existing workload label. Proposed campaign bookkeeping would explicitly record the new execution as ordinal 2, retain the raw label unchanged, and link both independent run IDs. This avoids changing the validated harness merely to rename the second execution. Owner review should accept this mapping before proceeding; no raw evidence would be relabelled or overwritten.

1. Reverify the 73 frozen candidate hashes and the current canonical Dry Run #1 archive, 223 application hashes, unchanged sacrificial input metadata, D: capacity, zero matching diagnostic identities/processes, zero J6Kernel sessions and zero VirtualBox processes. Existing Dry Run #1 evidence is expected and must be retained; it is not reusable live state.
2. Record a new campaign-ordinal-2 intent outside the live heartbeat path, referencing the first run `D:\JARVIS-STAGE6-LIVE\b675935592fe41d48968e22be8cc6641\code\integrated-dry1-8c2cbaeef9d04a8080b9bcf22fae89cd` and the frozen candidate manifest. Do not change source or timeout values.
3. After owner approval only, launch the existing full workflow once:

```powershell
& 'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe' -NoProfile -File 'D:\JARVIS-STAGE6-LIVE\b675935592fe41d48968e22be8cc6641\code\dry_launch.ps1' -Scenario dry1
```

4. Approve only the known J6KernelTrace.exe and independent app_monitor.ps1 UAC prompts. Confirm the launcher creates a different `integrated-dry1-<GUID>` directory. Cancelled UAC, missing evidence, deadline/heartbeat violation or any acceptance failure means STOP, preserve and reconcile cleanup; no automatic retry.
5. Independently verify both full hash passes, preserved metadata, complete application and kernel streams, strict cleanup proof, unchanged deadlines, empty final queue, durable manifest, archive bytes and zero live identities/sessions. The raw success label alone is insufficient. Record the result as the second campaign attempt only through the explicit ordinal/run-ID mapping.
6. Archive/hash-verify finalized nonsecret evidence to TEAGUE INDUSTRIES DATABASE, then STOP for owner review. Do not perform protected baseline hashing or launch VirtualBox.

No scenario or harness changes are proposed in this procedure. If owner review requires a literal `dry2` selector instead of the explicit campaign-ordinal mapping, that would be a separately reviewed harness-label change, not part of this pass.
