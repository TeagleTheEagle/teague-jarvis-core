# Stage6 single evidence restoration and immutable preflight

**EVIDENCE_RESTORATION_COMPLETE**

INCIDENT OCCURRED → DETECTED → FAIL CLOSED → BOTH VERSIONS PRESERVED → AUTHORITATIVE ORIGINAL RESTORED → OVERWRITE PATH HARDENED → VERIFICATION PASSED.

The overwrite was an agent error caused by reexecuting a historical host-check script with a fixed output path. This report preserves that fact. The original143-member archive and8-member incident archive remain unchanged. Restoration was explicitly authorized for one local file only.

1. **Canonical evidence file path:** C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-instance-stream-design-20260921\final-host-state.json

2. **Overwritten local SHA-256:** d95aefe75a1815037f2c1dc184ed4e91373686cc3fb465974b1784c06d58de12

3. **Authoritative archived SHA-256:** c01b96eecf05c4b29723b900d0543d104fe0f514487886339f080d3d709b17cb

4. **Restored local SHA-256:** c01b96eecf05c4b29723b900d0543d104fe0f514487886339f080d3d709b17cb

5. **Authoritative-source proof:** AUTHORITATIVE_RESTORATION_SOURCE_CONFIRMED. Archive manifest finalized2026-09-21T02:36:35.586137+00:00, before accidental host check02:41:15.8810587Z. Archive/member trusted hashes match; independent incident record and both separately preserved copies agree. No conflicting equally authoritative original found in the recorded evidence set.

6. **Overwritten-version preservation path:** C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-evidence-restoration-20260921\incident\final-host-state.overwritten.0bf9c9a3d03842248480f2ef04d688c4.json

7. **Byte-for-byte restoration result:** PASS;494 bytes, equal to archived member. New local LastWriteTimeUtc=2026-09-21T02:49:24.545749+00:00; historical timestamp not recreated.

8. **Surrounding directory preservation result:** PASS. Complete before/after filename,size,hash,mtime comparison of both relevant evidence directories: only the authorized target changed. No neighboring rename,deletion,content or timestamp change.

9. **Historical archive integrity result:** PASS;143/143 members verified. Archive SHA-256:46dddb7c33c87154325778989f51fda265e9833f8f50d550b9506fdc770dc1a5. Archive unchanged.

10. **Incident archive integrity result:** PASS;8/8 members verified, every member hash recorded in freeze.json. Archive SHA-256:a18270f1aee8510ba0895d794fb66a95f0c52f473477b1db3f5f836c06c7bec1. Archive unchanged.

11. **Exact overwrite code path:** C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-instance-stream-design-20260921\final_host.ps1:9. Top-level operation uses $r=$PSScriptRoot then Join-Path $r final-host-state.json and Set-Content, which truncates/replaces an existing file on repeated invocation.

12. **Exclusive-create correction:** New host_preflight.ps1 accepts a required32-hex RunId, confines output to its own precreated final/run-id directory, rejects reparse output directories and atomically FileMode.CreateNew-reserves before any host queries. Existing path explicitly fails; no truncate/delete/suffix retry. Python create_bytes/create_json/create_report use xb and flush/fsync. create_run uses exist_ok=False. Historical script is preserved unchanged and retired from reuse by POLICY.md.

13. **Other vulnerable output paths found:** 47 relevant operations audited:18 UNSAFE_OVERWRITE,13 SAFE_EXCLUSIVE_CREATE,9 SAFE_UNIQUE_RUN_PATH,6 INTENTIONAL_MUTABLE_RUNTIME_FILE,1 UNKNOWN. Fixed result paths include prior plan,measurements,reconciliation,hash listings,diff,REPORT,probe/check and capacity-test summaries. Monitor Save mixes mutable health and final outputs; broader hardening documented only. Exact file/line inventory in output-audit.json. Archived scripts were not edited or reexecuted.

14. **Focused test totals:** 18/18 PASS;0 failures,0 errors,0 skipped. Includes15 requested cases and runtime/final separation,run reuse/traversal rejection. Sixteen concurrent creators yielded exactly one successful creator. Actual PowerShell path separately checked below.

15. **Duplicate-write rejection result:** PASS for final JSON,reports,incident copies,restoration-source copies and archive receipts. Original bytes,hash,mtime and file identity preserved where tested. No delete/recreate fallback.

16. **Narrow preflight result:** PASS:2 fresh final host checks through established PowerShell7.6.5; original restored hash,116 candidate hashes and both historical archives reverified. Initial Windows PowerShell5.1 invocation was blocked by its execution policy before script execution; failed invocation/source preserved. No policy was changed or bypass flag used.

17. **Repeated-preflight overwrite protection:** PASS:repeat of first real preflight output rejected with FINAL_EVIDENCE_CREATE_REJECTED before host queries; bytes,hash and timestamp unchanged. A second explicit run ID produced a separate valid result.

18. **Candidate hash result:** PASS:116 frozen candidate hashes plus6 additional frozen checks unchanged. No identity/stream/runtime candidate edited.

19. **Live-process result:** 0 matching diagnostic/VirtualBox processes at final completed host query. No observers or validation workloads launched. Short-lived preflight shell and filesystem-test threads exited normally.

20. **Trace-session result:** 0 diagnostic trace sessions; logman query -ets succeeded. No trace session started.

21. **Protected VM access result:** NOT ACCESSED. No protected configuration/hash/VM/snapshot operation. This is an operation-scope statement, not a newly acquired protected-file hash proof.

22. **Production-change result:** UNCHANGED by this pass. No production source/configuration/provider/credential/security changes or launch.

23. **Remaining limitations:** Immutability applies to the tested new entry points, not arbitrary programs/owner edits or frozen legacy scripts. No ACL enforcement added. A failed new write may leave a partial artifact that must be preserved; no automatic retry. One-off fixed-target restoration is an explicit approved exception, guarded by overwritten hash and refuses replay. Existing integration/identity/capacity blockers remain open.

24. **Final status:** EVIDENCE_RESTORATION_COMPLETE

## Restoration method and metadata

Before restoration the overwritten file was494 bytes, LastWriteTimeUtc2026-09-21T02:41:15.921175+00:00. Its current bytes were copied with exclusive creation to the new incident path. The original archive member was materialized into a separate exclusive-created file and hashed. Only after both copies and the restoration intent were recorded was the exact canonical target opened r+b; the current handle bytes were hash-checked, replaced with the archived original, truncated to its exact length and flushed durably. Byte equality and surrounding-directory preservation were then verified. No broad extraction, deletion or timestamp fabrication occurred.

## Changed files and commands

The only pre-existing changed file is the explicitly restored canonical file. New hardening: evidence_io.py,host_preflight.ps1,POLICY.md. New restoration/audit/validation/report tooling: restore_evidence.py,audit_outputs.py,test_evidence_io.py,verify_preflight.py,finish.py. All reside in this new evidence directory. hardened-source-hashes.json records their hashes; the archive manifest covers all resulting artifacts.

Commands: bundled Python with -B ran restore_evidence.py freeze/restore/verify, test_evidence_io.py,audit_outputs.py and verify_preflight.py. preflight-validation.json and per-invocation command records contain exact PowerShell executable/arguments,exit codes and output. No execution-policy option was supplied.

## Evidence

- [freeze.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-evidence-restoration-20260921/freeze.json)
- [restoration-intent.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-evidence-restoration-20260921/restoration-intent.json)
- [restoration-result.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-evidence-restoration-20260921/restoration-result.json)
- [final-preservation.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-evidence-restoration-20260921/final-preservation.json)
- [focused-tests.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-evidence-restoration-20260921/focused-tests.json)
- [output-audit.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-evidence-restoration-20260921/output-audit.json)
- [POLICY.md](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-evidence-restoration-20260921/POLICY.md)
- [preflight-validation.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-evidence-restoration-20260921/preflight-validation.json)
- [winps-policy-failure.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-evidence-restoration-20260921/winps-policy-failure.json)
- [hardened-source-hashes.json](C:/Users/jonny/Documents/Codex/2026-09-07/cr/outputs/jarvis/docs/stage6-evidence-restoration-20260921/hardened-source-hashes.json)

New archive verification is recorded in archive-verification.json outside its own archive to avoid circular hashing. Both overwritten versions and the separately materialized original are retained. Historical delay causes remain UNCONFIRMED. HISTORICAL STAGE1 CAUSE: UNCONFIRMED.

## Owner review only — proposed resume point

**AUTHORITATIVE EVENT STREAM + INDEPENDENT PROCESS-INSTANCE IDENTITY INTEGRATION**

Begin with the new immutable preflight against a fresh run ID, reconcile116 candidate hashes and prior evidence, then resume the previously requested dataflow/design review. This pass stops here. No identity/stream integration, medium/large validation or protected baseline capture has been resumed.
