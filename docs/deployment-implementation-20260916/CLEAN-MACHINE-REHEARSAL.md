# Clean-machine rehearsal — preparation only, NOT RUN

This host already contains development tools and Microsoft runtime components. Moving the TEST package here does not make it a clean Windows environment. No VM, second Windows account, second machine, driver installation or security change was performed.

The current package can relocate on this host. A genuinely clean-machine restore is not yet executable end to end: current-user DPAPI protects the installation binding and enrollment; copying those records to another owner/machine is not an approved recovery protocol. The owner recovery/trust transfer must be reviewed before that step. Do not substitute a newly generated data identity or copy reusable client/controller credentials to make it work.

## Exact proposed sequence and evidence

1. Obtain approval for a disposable Windows environment, its owner account, TEST-only destination and any prerequisite installation. Record Windows build, architecture, installed software, account/SID, and absence of the source repository, development venv, global Python packages, Node/npm and JARVIS production state. A VM on this host is a proposed environment, not an accepted clean-machine equivalent until reviewed.
2. Transfer the hash-pinned TEST release and a coherent **synthetic** backup through an explicitly approved private channel. The source package manifest SHA-256 for this milestone is `4c07cf1d46544d248db711bfb3249bfe4f933a3f8f9241b4a182dddce00d9d04`. Verify every manifest entry, not only the manifest file. Do not transfer this host's DPAPI records as portable enrollment, and do not use the project-record archive as a credential carrier.
3. Resolve the native dependency prerequisite. The import inventory in `independent-final.json` includes `MSVCP140.dll`, `VCRUNTIME140.dll`, `VCRUNTIME140_1.dll`, Windows API sets and Windows multimedia/graphics libraries. VCRUNTIME files in the packaged Python directory do not prove that Electron resolves the bridge's imports there. Review either a pinned, licensed app-local runtime inventory or an explicitly approved Microsoft redistributable prerequisite. No prerequisite installation is authorized by this document.
4. **STOP at the owner recovery gate.** Review an authenticated, identity-bound transfer that fences the previous host, binds the expected existing synthetic data identity and backup digest, permits only the target installation/owner, expires, is one-use, records interruption states, and enrolls fresh clients without restoring old sessions or reusable old grants. No cross-machine recovery command is implemented in this milestone. Its absence is not a successful restore and must not trigger NEW initialization.
5. After that separately reviewed mechanism exists, select RESTORE explicitly. Independently verify backup consistency, artifact hashes, expected data identity, SQLite application/schema identifiers and package compatibility before activating any Core. Refuse missing/corrupt/incompatible data without generating a replacement identity. Preserve failures and the original backup.
6. Stage the immutable package and the separate mutable TEST state root, protected for the approved target owner. Persist the reviewed target binding and fresh owner-authorized client enrollment. Record package/runtime hashes, owner, installation ID, data ID and enrollment revisions without keys. OLD credentials must fail.
7. Use the existing bounded authenticated coordinator transaction to start exactly one TEST Core. Do not use raw Python execution or a legacy desktop launcher as a fallback. Record real PID, creation time, executable digest, epoch, namespace and lifetime-lock ownership. Simultaneous contenders must resolve to that same owner or fail closed.
8. Attach both actual Electron TEST clients with their actual executable identities. Verify the shared restored canonical data, separate owner/session authority, fresh presence, ordinary shutdown denial, explicit shutdown/restart, new epoch, stale-authority rejection and interruption/adoption behavior. Record actual process/import evidence and screenshots. Physical voice and paid/live providers remain outside this test.
9. Shut down through the authenticated lifecycle controller, verify cleanup against exact process identities, and verify canonical data independently after exit. Run corruption/interruption, uninstall-retention and reinstall cases in separate disposable TEST runs. Do not erase failures or roll persistent data back over newer writes.
10. Review the complete evidence before claiming clean-machine PASS. Any missing step remains NOT RUN/OPEN. No result authorizes production cutover.

## Current commands and their limits

The already executed same-host campaign is:

```powershell
Set-Location 'C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis'
.\.venv\Scripts\python.exe -B tests\deployment_contract\campaign.py
```

That is a source-owned TEST **driver** which packages explicit inputs, then launches the installed Core/controller/clients from the independent package. It is not a clean-machine installer or a portable owner recovery command. Do not run it on a production installation. The installed fixed-role bootstrap accepts only private, authenticated bounded input from the trusted TEST driver; its command alone does not grant enrollment or restart authority.

## Readiness conclusion

Same-host relocation and same-owner synthetic restore: validated. Genuine clean-machine recovery, a changed-build client upgrade, cross-account/cross-machine owner recovery, signing/distribution and native-runtime prerequisite deployment: not validated here. They require the next concrete review and environment decision. No claim of production readiness.
