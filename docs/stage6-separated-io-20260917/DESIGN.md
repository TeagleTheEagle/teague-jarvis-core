# TEST updater separation — scope and design

Accepted Stage 4/5 snapshots remain immutable. Implementation is in the separate source recorded in source.json. No production source, data, ACL or configuration is changed. Windows owner-only inherited DACL and current-user DPAPI remain as accepted; these are not protection against arbitrary same-owner malware or an administrator.

Before: bootstrap rejects opens of .py/.pyc/.pyd outside the current release, without distinguishing hashing, copying or execution. This blocks incoming verification and staging. Allowing a read alone cannot establish execution denial.

After, candidate only:

1. The installed fixed control program preloads its verified modules. Only update/rollback/enroll-update/commit-update/abort-update commands enable execution freezing. They cannot compile, exec, construct Python functions/code objects, spawn processes, or load non-allowlisted DLLs. Restrictions continue after temporary data authority ends, preventing retained input bytes from being compiled under a fabricated filename. Existing preloaded functions continue running. Core/coordinator and unrelated control commands keep the original open guard.
2. Existing owner HMAC, binding, expiry and exclusive nonce-receipt validation occurs before update data authority. Locks, stop state, pending intent, enrollment and activation semantics remain unchanged. No renderer interface or reusable credential is added.
3. Verification temporarily allows reads of exact validated manifest entries only. Incoming root/hash must match authenticated request; staged root/hash must match the protected pending intent. Manifest has a Windows read handle denying write/delete sharing while parsed. Normal full package/native verification still runs. No code callback is accepted. Permission is context-local and revoked in finally. Unrelated external file opens and writes are denied in the phase.
4. Staging copies already verified held files into the exact new pending target. It never overwrites an existing release. Each file uses exclusive binary creation, bounded copy chunks, hash checking, flush/fsync, and a finally-revoked per-file read/write scope. Source remains read-only. Activation and execution authority are not granted by copying. Existing separate enrollment/commit and explicit restart remain required.
5. New staged package becomes eligible for the existing authenticated bootstrap only through the existing committed activation history, matching executable/app identity and package verification. Rollback retains the same checks and newer-data refusal.

Changed candidate files: deployment_test/bootstrap.py, deployment_test/upgrade.py, deployment_test/package.py (explicit module inventory), new deployment_test/update_io.py. No Store/schema/Core lifecycle changes.

Threat-model limit: Python audit enforcement in the fixed trusted updater is not a general OS sandbox. Malicious code already running as the same owner or within the interpreter can use native APIs/modify process state outside the accepted model. These tests must not be described as proving universal Windows non-executability of readable files, nor as an AppContainer/restricted-token sandbox. No Windows-wide policy or execute-deny ACL was installed.

Failure evidence is retained. The initial null-executable audit error and test replay exception mismatch are preserved. The adversarial retained-byte test initially failed; it motivated permanent execution freezing for updater commands. The first packaged run failed before Core construction because freezing all control commands affected initialization; freezing was then narrowed to updater commands only.

Rollback of candidate: retain/discard the separate TEST candidate and packages; resume the immutable accepted snapshot. Do not overwrite historical packages/evidence or move production data. No acceptance commit or production activation is authorized by this document. Fresh-Windows recovery remains required.
