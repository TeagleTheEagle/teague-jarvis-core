# Stage 6 quiescence gate — awaiting normal guest shutdown

Final status for this checkpoint: BLOCKED.
Single immediate blocker: the rejected disposable guest has not yet completed a verified normal shutdown. Owner desktop interaction is required. No baseline capture is authorized by this checkpoint.

## VM state and process evidence

Direct read of the normal registry identifies exactly two registered entries:
- Protected original JARVIS-CLEAN-WIN11 / 5dc3824d-8abc-476c-bc9e-b8170b6337d8.
- Rejected JARVIS-E2E-DISPOSABLE-20260918 / 65b44206-338e-4674-a64e-e69ff13fe75b.

Protected original: last recorded PoweredOff; current offline/quiescent state not conclusively certified. No VirtualBox query or operation against it occurred.
Rejected clone: current captured log identifies live PID 11516, records Running and no later PoweredOff transition. It remains registered. Live guest responsiveness cannot be established from a host log alone; GUI interaction was requested.

Before shutdown, process observations were unchanged from the preceding review:

| Name | PID | Parent PID | Creation time UTC+10 | Owner |
|---|---:|---:|---|---|
| VBoxSVC.exe | 17084 | 1592 | 2026-09-18 11:45:18.991416 | THEGRIZZLYBEAR\jonny |
| VBoxSDS.exe | 5268 | 1392 | 2026-09-18 11:45:19.058982 | LocalSystem per service configuration; process owner query denied |
| VirtualBoxVM.exe | 15476 | 17084 | 2026-09-18 11:45:19.471277 | THEGRIZZLYBEAR\jonny |
| VirtualBoxVM.exe | 2096 | 15476 | 2026-09-18 11:45:19.700010 | THEGRIZZLYBEAR\jonny |
| VirtualBoxVM.exe | 11516 | 2096 | 2026-09-18 11:45:20.608943 | THEGRIZZLYBEAR\jonny |

No VirtualBox.exe Manager, VBoxManage, VBoxHeadless or separately named clone/copy process appeared. This is not proof of no in-process pending operation. Current VM executable/command-line fields were unavailable; log executable evidence is supplementary and does not authorize PID-only termination.

After-shutdown processes: NOT YET OBSERVED. No process was terminated or service stopped.

Oracle documents VBoxSVC as exiting after its last client disconnects. This does not establish that VBoxSDS, a separate Manual-start Windows service running as LocalSystem, will exit automatically. Do not stop it without the required identity/handle review.
Source: https://www.virtualbox.org/manual/ch10.html

## Rejected-clone evidence preservation

Source directory:
C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\clean-validation-vms\JARVIS-E2E-DISPOSABLE-20260918

Recorded current configuration path/hash, all file names/sizes/timestamps, current log state, process identities, and registry entries. Current clone configuration SHA-256:
6b2d4eab4242151149924f596c4a04571e1978312c90e25992c918e810143dda

Two available logs captured using shared-read text snapshots without modifying the live source:
- clone-VBox.log: 01c767a7afb4884fa2758be2891ddc072240b618655924f6f752dd04464c0db3
- clone-VBoxHardening.log: 47a7089f4ed7789f5e693a746e650ff75237351b00111fd00f34f95cc79b9c06

These hashes identify the captured copies. They do not claim byte-for-byte completeness against a still-growing final log. No rotated clone logs were present in the enumerated log directory. Snapshots were screened for common secret patterns before saving; no .env, disk contents, guest credentials or API keys were read/copied. Log line 258 records LocalhostReachable=1; this rejected clone remains excluded from acceptance.

Four previously archived original logs rehashed: 4/4 match. No historical evidence overwritten.

## Shutdown and handles

Method requested: owner uses Start → Power → Shut down inside JARVIS-E2E-DISPOSABLE-20260918 only. No Save State, forced power-off, unregister, deletion or protected-VM action.
Result: pending owner interaction. Native desktop control is unavailable in this session; no attempt was made to substitute an unverified guest command or reinstantiate VirtualBox management services.

Protected-source handles: UNPROVEN. Clone handles: UNPROVEN; live log/VM process evidence indicates ongoing activity but does not enumerate handles. Normal-registry handles: UNPROVEN. No handle.exe/handle64.exe/Procmon executable was found through command discovery. No tool installed, no EULA/registry setting changed, no privileged-handle bypass attempted. Process absence after shutdown and, where necessary, authorized handle inspection remain required; absence of logged opens is not proof of no handles.

## Protected comparisons

Before and pre-shutdown follow-up hashes both match:
- original .vbox: 98a89e62fd19ba49dc316b6e9c902fb6ba18fe4c66ec0ba8bf20deb3a892e93c
- original .vbox-prev: 9d69cc14a480aac13c9c03817aeeb4bc4d068a6fc27a81fc15ff2bc91de2c797
- normal VirtualBox.xml: f05da097d96f073a2569488a0fffc1682d7034e69069bab51b4409d88c2bdf0d

All 12 protected files retain size and LastWriteTimeUtc during this pass. Last-access timestamps are not used as preservation invariants. Post-shutdown comparison: NOT RUN. No full disk hashes captured; no retrospective disk-integrity claim made.

## BitLocker and capacity

BITLOCKER_NON_BLOCKING for this file-level preservation/hash/copy readiness gate. Encryption status remains unknown; no further elevation or BitLocker query/change performed. Accessible file reads are available regardless of whether transparent volume encryption is enabled. Future copies still require full file hashes and bounded ACLs; encryption status is not a substitute for either. This classification does not certify at-rest confidentiality, future unlock/recovery availability, or successful reading of every large file.

Microsoft describes on-the-fly decryption for reads after unlock:
https://learn.microsoft.com/en-us/windows/security/operating-system-security/data-protection/bitlocker/recovery-process

D: remains Healthy NTFS, 1,917,504,532,480 bytes free, comfortably above the 232-GiB planning reserve. No storage created there or copied to it.

## Gate disposition and next action

Q1 PARTIAL: registrations, process identities/owners and log association recorded; handle/quiescence proof incomplete.
Q2 PARTIAL: pre-shutdown evidence captured/hashed; final closed logs pending.
Q3 BLOCKED: owner-operated normal guest shutdown pending.
Q4/Q5 BLOCKED: require Q3; no force termination authorized by this result.
Q6 COMPLETE: BitLocker status-query limitation is non-blocking for file-level integrity.
Q7 BLOCKED: quiescence has not passed.

OWNER ACTION REQUIRED:
Inside JARVIS-E2E-DISPOSABLE-20260918, choose Start → Power → Shut down. Do not interact with JARVIS or the protected VM. Report completion or an unavailable/unresponsive guest window.

After that, re-observe process/service state, final clone log PoweredOff, handle coverage and protected metadata/hashes; allow VBoxSVC to exit naturally. Preserve final evidence before any cleanup. Stop on an unexplained mutation or any need for forced termination. Even if quiescence passes, provide the baseline procedure only; do not begin full baseline hashing in this pass.

Production unchanged. No account/ACL/security change, VM copy, JARVIS launch or guest acceptance. No Stage 6 acceptance or Stage 7 action.
HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
