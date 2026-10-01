# Stage 6 preservation campaign — Phase 0–1 review

Disposition: BLOCKED. No Phase 2 baseline capture or subsequent phase started.

Authority: owner brief attachment 7fdfc317-25e2-4511-99bb-212b806019c8. Its initial action authorizes Phase 0 and Phase 1 only. No VirtualBox command/API, account, ACL, environment, source, production, VM or disk-content changes were performed. Only this new evidence report was created.

## Evidence reviewed

Repository: C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis

Reviewed docs/clean-windows-e2e-20260918/STATUS.md, STOP-RESULT.json, original-config-difference.txt, PRESERVATION-SAFE-RESTART-REVIEW.md, preserved original logs/hash manifest, and docs/clean-deployment-hardening-20260918/REPORT.md/source-hashes.json.

Four preserved original log copies hash-verified: 4/4 match. Current eight deployment-hardening files: 8/8 match recorded hashes. Historical test results are not rerun or promoted to new guest acceptance evidence.

## Protected state

Protected original: C:\Users\jonny\VirtualBox VMs\JARVIS-CLEAN-WIN11
Protected normal configuration: C:\Users\jonny\.VirtualBox

Read-only metadata inventory: 12 files, 59,665,402,098 bytes (55.567735897 GiB). Three VDI files total 59,661,877,248 bytes; all other artifacts total 3,524,850 bytes. No saved-state file appeared in the recursive inventory. Disk last-write timestamps remain the previously recorded September 17 values. This is not byte-level disk verification.

Current small-file SHA-256 reads match the previously recorded post-incident values:

- JARVIS-CLEAN-WIN11.vbox: 98a89e62fd19ba49dc316b6e9c902fb6ba18fe4c66ec0ba8bf20deb3a892e93c
- JARVIS-CLEAN-WIN11.vbox-prev: 9d69cc14a480aac13c9c03817aeeb4bc4d068a6fc27a81fc15ff2bc91de2c797
- normal VirtualBox.xml: f05da097d96f073a2569488a0fffc1682d7034e69069bab51b4409d88c2bdf0d

No new mutation observed in those comparisons. Full protected-disk preservation cannot be certified: historical full hashes are absent and Phase 2 has not run. Nothing was restored. The earlier NAT 0→1 preservation violation remains recorded.

## Running processes and rejected clone

Normal registry XML read directly, without VirtualBox, contains the protected original and rejected clone 65b44206-338e-4674-a64e-e69ff13fe75b.

Rejected clone directory: C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\clean-validation-vms\JARVIS-E2E-DISPOSABLE-20260918

Windows process inventory:

| Process | PID | Parent | Creation time, local UTC+10 |
|---|---:|---:|---|
| VBoxSVC.exe | 17084 | 1592 | 2026-09-18 11:45:18.991416 |
| VBoxSDS.exe | 5268 | 1392 | 2026-09-18 11:45:19.058982 |
| VirtualBoxVM.exe | 15476 | 17084 | 2026-09-18 11:45:19.471277 |
| VirtualBoxVM.exe | 2096 | 15476 | 2026-09-18 11:45:19.700010 |
| VirtualBoxVM.exe | 11516 | 2096 | 2026-09-18 11:45:20.608943 |

The rejected clone's current VBox.log identifies PID 11516 and the installed VirtualBoxVM.exe, opened at 2026-09-18T01:46:00.844958600Z. It records Running, LocalhostReachable=1, and no subsequent powered-off transition. Combined with the live process chain, this supports the rejected clone remaining running. It is still registered and excluded from acceptance. This is not sufficient process identity evidence for forced termination: current executable/command-line fields for the VM processes were unavailable.

No separate VirtualBox Manager or VBoxManage process appeared. Original logs/metadata support its previous powered-off state; independently proving current original quiescence without a management API remains incomplete. Shared VBoxSVC/VBoxSDS are active. No termination/shutdown was attempted. Live clone logs remain in place; the prior incomplete snapshot is preserved, not relabelled a verified complete capture.

## Storage feasibility

Windows Get-Volume/Get-Disk/Get-Partition read-only inventory:

| Volume | Filesystem | Storage | Total bytes | Free bytes | Free GiB |
|---|---|---|---:|---:|---:|
| C: | NTFS | internal SATA ADATA SU650 | 238368616448 | 22545403904 | 20.9970 |
| D: | NTFS | internal SATA ST2000DM008-2FR102 | 2000381014016 | 1917504532480 | 1785.8153 |
| E: | NTFS | USB Samsung M2 Portable 3 | 1000175824896 | 996118384640 | 927.7075 |

All three report Healthy. The unlettered ~0.965-GiB NTFS partition is unsuitable; it is not proposed for use.

Conservative planning budget: complete master S + complete Work S + disposable allocation S + 64 GiB growth/media/evidence reserve, with S=59,665,402,098 bytes. Total 247,715,683,030 bytes =230.7032 GiB; round to at least 232 GiB free before starting. This is a planning reserve, not a proven maximum virtual-disk-growth bound. Recalculate capacity at copy/boot gates, including external media and actual virtual disk limits.

D: is preferred for internal storage reliability; E: is capacity-sufficient but introduces USB disconnect/power risk. Additional storage required on D: =0 bytes. C: is unsuitable. No deletion or copying occurred. Proposed root D:\JARVIS-STAGE6 was not created; existence was not established by the listing probe.

D: root ACL grants broad inherited rights to Authenticated Users/Users. A later dedicated subtree must have explicitly bounded permissions; inheriting D: defaults cannot establish account separation. No ACL was changed. NTFS supports the proposed design; actual account/ACL proof remains a later gate.

BitLocker queries returned access-denied errors for C:, D:, E:. The follow-on 'does not have an associated BitLocker volume' messages do NOT establish lack of encryption. Encryption/lock/recovery status remains UNKNOWN. Whole-VM master copies may contain credentials and must not enter the ordinary project evidence archive.

## Exact blockers and next action

Storage capacity is sufficient. READY_FOR_BASELINE_CAPTURE is not established because protected/normal-configuration quiescence is not proven while the rejected clone and shared services remain active; current process visibility is incomplete. Encryption status also remains unverified.

No Phase 2 hashing should start until a preservation-safe way to establish quiescence is reviewed. Stopping the clone or shared services may itself cause normal registry writes; do not silently assume this is permitted. The current initial-action scope prohibits VirtualBox operations. Preserve final clone evidence before later cleanup.

Next owner-reviewed action: authorize a specifically scoped, non-VirtualBox guest shutdown of only the rejected clone if it is interactively available, with before/after small-config observations and explicit disposition of any normal-registry write risk. Do not force-terminate or stop shared services under this report. Alternatively supply an already quiescent host state through an approved preservation procedure. Resolve BitLocker status through an appropriately authorized read-only administrative query; do not disclose recovery keys.

No new full baseline, account, ACL proof, independent copy, VM registration, guest test, provider call, Stage 6 acceptance, Stage 7 action or production operation occurred. Existing evidence remains unchanged. Rollback: none required for runtime/system state; retain this report as additional evidence.

HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
