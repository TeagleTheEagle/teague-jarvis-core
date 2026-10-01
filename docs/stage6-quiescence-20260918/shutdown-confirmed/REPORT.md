# Quiescence follow-up — READY_FOR_BASELINE_CAPTURE

2026-09-18. Read-only inspection plus new evidence copies only. No VirtualBox command/API, VM start/control, service stop, termination, ACL change, production action or full baseline hashing.

## Shutdown finding

The rejected JARVIS-E2E-DISPOSABLE-20260918 guest completed a guest ACPI power-down. Preserved VBox.log:
- line 1781: ACPI entering S5 power state.
- line 1782: RUNNING → POWERING_OFF.
- line 2245: POWERING_OFF → OFF.
- line 3963: DESTROYING → TERMINATED.
- line 3964: PoweredOff.
- following lines: UI closes because the VM is powered off, then normal QApp quit completes.

This supports normal guest-initiated shutdown, not a still-running/hung VM or saved-state transition. The precise Windows initiator and whether an earlier ACPI request contributed are NOT established. Guest Windows event logs were not collected; do not claim every Windows service shutdown was independently verified.

The final log write was 2026-09-18T02:46:20.8376663Z (12:46:20 local). This is a file timestamp, not an independently measured guest shutdown completion timestamp.

## Process/VM state

Before: VBoxSVC 17084; VBoxSDS 5268; VirtualBoxVM 15476, 2096, 11516. Owners recorded in prior evidence.
After: zero matching VirtualBox execution/frontend/coordinator processes in two Windows CIM observations. VBoxSDS service Stopped, PID 0. Final captured observation: 2026-09-18T02:49:37.9341325Z.

Rejected clone: PoweredOff, remains registered, not deleted and excluded from acceptance.
Protected original: prior PoweredOff log state, unchanged artifacts, no current VM execution process; no operation against it occurred.
VirtualBox Manager: no process. No VBoxManage/copy process. No active VirtualBox process exists to hold protected VM or normal-registry handles. This is process-lifetime evidence, NOT a system-wide assertion that no antivirus/indexer/other process has file handles. No direct all-process handle census was performed.

## Preservation

Original .vbox before/after SHA-256:
98a89e62fd19ba49dc316b6e9c902fb6ba18fe4c66ec0ba8bf20deb3a892e93c

Original .vbox-prev before/after:
9d69cc14a480aac13c9c03817aeeb4bc4d068a6fc27a81fc15ff2bc91de2c797

Normal VirtualBox.xml before/after:
f05da097d96f073a2569488a0fffc1682d7034e69069bab51b4409d88c2bdf0d

All three hash/timestamp comparisons PASS. All 12 protected file sizes/LastWriteTimeUtc unchanged. No retrospective disk-content proof: full disk hashes still absent. Earlier preservation violation remains unchanged in history.

Final clone logs copied byte-for-byte; source/copy/source hash comparison PASS:
- VBox.log: 43934c0afd8130ea4115d41aeabb456a7f72fb885bfdcace280d4ce68b6f9764
- VBoxHardening.log: 75abaa212644d1bc5cbe3471ba31f62fed8ee494509aa1a0c9206189a4ce94ea

Prior pre-shutdown evidence remains untouched. No credentials/.env/disks copied. No source mutation performed.

BITLOCKER_NON_BLOCKING remains limited to accessible file-level hashing/copy integrity. Encryption status remains unknown. D: capacity was confirmed at 1,917,504,532,480 bytes free in preceding gate, above the 232-GiB reserve; no intervening copy/install was performed.

## Disposition and next procedure

Quiescence: PASS at observation time. READY_FOR_BASELINE_CAPTURE. No owner shutdown action is now required. Do not reopen either VM or VirtualBox Manager before capture.

Next baseline procedure, NOT EXECUTED:
1. Recheck no VM/frontend/VBoxSVC processes and no active VBoxSDS process; recheck storage and the three small hashes. Stop on drift.
2. Inventory protected VM and relevant normal VirtualBox configuration files read-only, including size, LastWriteTimeUtc, path and links/reparse attributes; resolve required artifact relationships without invoking VirtualBox.
3. While quiescent, SHA-256 every required VM artifact including both configs, all three VDI files, NVRAM and supporting metadata, plus relevant normal configuration. Parse snapshot/disk/NVRAM references read-only. Fail on missing/external/unresolved required artifacts or interrupted hashing.
4. Compare metadata before/after and repeat quiescence/configuration checks; label the complete result NEW POST-INCIDENT BASELINE, never pre-incident proof.
5. Save and hash the nonsecret manifest, verify its archived copy, then stop before account/ACL/copy/VM operations unless separately authorized by the current gate.

Production unchanged. Stage 6 is not complete. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
