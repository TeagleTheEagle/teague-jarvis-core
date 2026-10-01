# Preservation-safe Stage 6 restart — preparation only

Disposition: PROCEDURE PROPOSED; ISOLATION NOT PROVEN; GUEST VALIDATION BLOCKED.
Date: 2026-09-18. This document supersedes no historical evidence.

## Evidence boundary reviewed

Reviewed STATUS.md, PHASE-A.md, STOP-RESULT.json, clone-verification.json,
original-config-difference.txt, snapshot list records, vm-config-before.json,
the preserved original logs and their manifest, and prior command outcomes.
Four preserved original log copies were rehashed in the workspace: 4/4 match.
No protected original, normal VirtualBox configuration, VM-management API or
live guest was inspected in this resumed pass.

Last observed original .vbox SHA-256 (historical observation, not refreshed):
98a89e62fd19ba49dc316b6e9c902fb6ba18fe4c66ec0ba8bf20deb3a892e93c

Last observed .vbox-prev SHA-256, matching the pre-operation original:
9d69cc14a480aac13c9c03817aeeb4bc4d068a6fc27a81fc15ff2bc91de2c797

Last observed normal VirtualBox.xml SHA-256:
f05da097d96f073a2569488a0fffc1682d7034e69069bab51b4409d88c2bdf0d

These are reference observations, not complete immutable backups. The earlier
claim that both configuration files had been preserved must not be interpreted
as evidence that copies were saved: the record contains hashes and a diff, not
verified full copies of both original configuration files.

The attempted live clone log preservation created a 121203-byte VBox.log copy,
but verification failed on the locked live source. There is no completed clone
log manifest or preserved VBoxHardening.log in that attempt. Preserve the partial
copy; do not call it a fully verified log capture.

An ACPI shutdown was requested only for disposable clone
65b44206-338e-4674-a64e-e69ff13fe75b. It remained running at the last observation.
No forced power-off occurred. Current power state is unknown in this pass.
The interrupted original-disk hashing shell was cancelled/resumed to termination
on return (exit 1, no hash output). No complete disk hash baseline exists.

## Why the earlier proposal is insufficient

Oracle documents VBOX_USER_HOME as selecting an alternate global settings
directory and registry. That is configuration separation, not a filesystem
security boundary. An ordinary same-user process still has its existing file
permissions, and absolute disk/ISO/share references may lead outside a copied
directory. No test established service/process isolation on this host. Merely
setting the variable and launching VBoxManage cannot guarantee no original
access. Do not test this assumption by calling VirtualBox against the original
or by running a same-host registry probe while normal services may be active.

The original preservation violation remains: the prior log reports
LocalhostReachable=0; clone log reports 1; original XML changed in current and
both snapshot NAT entries. Transient-property removal does not explain away
this material networking difference.

## Recommended boundary

Use a separate validation Windows host where the protected source disk and
normal host configuration are not attached, mapped, shared, synchronized or
network-accessible. Install/use VirtualBox only there for this procedure.
VBOX_USER_HOME supplements this storage separation; it does not replace it.

A dedicated same-host account/restricted process could be considered only after
a separately reviewed OS-enforced access boundary is demonstrated. No account,
ACL, service, security setting or hypervisor configuration change is authorized
by this document. It is not the selected fallback without that review.

Do not run any VirtualBox operations in the source owner's normal environment.
In particular do not unregister the protected VM, stop its shared service, edit
VirtualBox.xml, restore .vbox-prev, or modify the source's permissions.

## Paths and copy requirements

Protected, prohibited source (reference only):
C:\Users\jonny\VirtualBox VMs\JARVIS-CLEAN-WIN11
Protected normal registry (reference only):
C:\Users\jonny\.VirtualBox
Rejected old validation clone (preserve; never use for acceptance):
C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\clean-validation-vms\JARVIS-E2E-DISPOSABLE-20260918

Proposed destination paths on the separate validation host, NOT created:
C:\JARVIS-STAGE6-ISOLATED\EvidenceMaster\JARVIS-CLEAN-WIN11
C:\JARVIS-STAGE6-ISOLATED\Work\JARVIS-CLEAN-WIN11
C:\JARVIS-STAGE6-ISOLATED\VBoxHome
C:\JARVIS-STAGE6-ISOLATED\Validation
C:\JARVIS-STAGE6-ISOLATED\Evidence

The current instruction prohibits touching the source. Consequently even a
read-only source inventory/copy/rehash is deferred until explicitly released for
that operation, or an independently supplied verified offline copy is available.
Do not silently turn the present prohibition into permission to read/copy it.

The authorized offline copy must include the complete .vbox/.vbox-prev, base
VDI, every descendant differencing disk, NVRAM, snapshot metadata, saved state
if any, logs and related machine artifacts. Inventory external ISO, share,
TPM, state and disk references: fail closed on missing/unknown/reparse paths.
Reject junctions/symlinks/hard-link aliases that defeat independent storage.
Do not copy the normal host VirtualBox.xml into the new registry.

Inventory each file with relative and resolved path, size, modification time UTC,
creation time where useful, reparse/link status and SHA-256. Hash before copy and
after copy; require equal bytes, unchanged source before/after, and consistent
snapshot/parent-disk relationships. Do not use last-access times as invariants.
Maintain both a preserved evidence master (never registered) and a separate
working copy. Compare working-copy manifest before any VirtualBox invocation.

The known source disks total 59,661,877,248 bytes (~55.6 GiB), excluding other
files. Current host free space observed: 23,249,342,464 bytes (21.65 GiB).
Full master + full work + independent baseline clone needs roughly 140 GiB
before guest growth; plan at least 180 GiB free on the selected destination,
then calculate actual needs from the complete inventory. No evidence deletion
or current clone deletion is part of this preparation.

The full deployment-pass disk may contain externally supplied credentials.
Treat whole-VM copies as potentially secret-bearing. Never archive them to
TEAGUE INDUSTRIES DATABASE, expose their contents, or call them credential-free.
Use the clean baseline snapshot for the validation guest; no .env transfer.

## Registry/UUID procedure — commands for review, NOT executed

Only in the separate validation host after the physical/storage boundary and
copy manifests pass; use one fresh process environment and capture all exits:

```powershell
$env:VBOX_USER_HOME = 'C:\JARVIS-STAGE6-ISOLATED\VBoxHome'
$vboxExe = 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
& $vboxExe list vms
# REQUIRE empty registry, and verify the actual service uses this VBoxHome.
& $vboxExe registervm 'C:\JARVIS-STAGE6-ISOLATED\Work\JARVIS-CLEAN-WIN11\JARVIS-CLEAN-WIN11.vbox'
& $vboxExe showvminfo '5dc3824d-8abc-476c-bc9e-b8170b6337d8' --machinereadable
& $vboxExe snapshot '5dc3824d-8abc-476c-bc9e-b8170b6337d8' list --machinereadable
```

The copied source machine/disk/snapshot UUIDs stay intact in this EMPTY isolated
registry. They cannot collide with an original that is absent from both registry
and accessible storage. Stop if any preexisting UUID is registered. Never resolve
a collision by editing XML, changing VDI UUIDs or unregistering the real original.

Before registration, absolute references require resolution. Existing copied
configuration references original-host installation ISOs and a shared folder.
They are not automatically relocated. Provision approved nonsecret media at
recorded destination paths, or use documented working-copy storage commands
after confirming registration cannot resolve any protected path. If metadata
cannot register without missing or escaping media, stop for review rather than
manually rewriting snapshot XML. A tested general relocation method is still an
open gate; no claim of fully executable commands is made for that case.

After copied chain/paths validate, the proposed baseline clone command is:

```powershell
& $vboxExe clonevm '5dc3824d-8abc-476c-bc9e-b8170b6337d8' --snapshot='2b0ebabc-7d4c-4ceb-bb5a-3f96d6e91992' --mode=machine --name='JARVIS-STAGE6-VALIDATION' --basefolder='C:\JARVIS-STAGE6-ISOLATED\Validation' --register
```

Do not pass Link or keep-UUID/MAC options. Record VirtualBox-generated clone UUID,
hardware ID, MAC and disk UUID; verify independent disk/no protected parent.
Full original snapshot lineage stays in EvidenceMaster and Work. The validation
clone intentionally represents only CLEAN-WIN11-BASELINE; do not claim it contains
the entire snapshot chain. If acceptance requires in-guest lineage restoration,
that is a separate plan adjustment rather than silently flattening it.

## Networking and preboot gate

Expected baseline: NAT LocalhostReachable=0. Explicitly configure only the NEW
validation clone via the supported option, using its freshly recorded UUID:

```powershell
# $validationId must come from the new clone result and pass identity/path checks.
& $vboxExe modifyvm $validationId --nat-localhostreachable1=off
& $vboxExe showvminfo $validationId --machinereadable
```

Confirm syntax against that installed version's help before execution. No boot
if expected off/0 is not reported or XML reports true. Also verify no host-only
or bridged adapter, unexpected forwarding, clipboard, drag/drop, source-host
shares or externally resolving media paths. This is a proposed clone-specific
configuration change, not authorization to alter source/host security settings.

Before first boot: independent UUID/path/chain proofs; empty isolated registry
before registration; all registered paths under approved Work/Validation; no
protected storage reachable; expected networking; complete content hashes;
source/normal-registry preservation comparisons by the separately authorized
read-only evidence collector. This collector must not launch VirtualBox on the
source host. Until permission for those comparisons exists, gate remains OPEN.

After boot, require actual log LocalhostReachable=0 before JARVIS setup. Any
normalization to 1 stops validation. Do not infer runtime networking from XML only.

## Expected mutations and proof requirements

Only Work/Validation/VBoxHome may change: .vbox normalization/.vbox-prev, isolated
registry/media registration, cloned disks/NVRAM, logs and guest writes after boot.
EvidenceMaster is never registered, modified or mounted. Hash comparisons detect
mutation; inaccessible source storage prevents it. Both controls are required.

First validate the isolation mechanics with throwaway synthetic VM metadata on
the separate host: empty registry, no normal-registry visibility, only sandbox
paths opened/written, UUID collision fails safely, no parent reference escape,
and normal registry is unchanged. Trace operations where available. Then repeat
against the independent copied chain before boot. Synthetic success alone is
not proof that the actual copied VM passes. No such test has run this turn.

## Cleanup and unresolved gates

Old clone: use ordinary Windows Shut down inside that clone only if authorized
and available. Prior ACPI request did not establish exit. Do not force power-off,
unregister, delete or call management APIs on this host under the current boundary.
Preserve final clone logs after confirmed shutdown; initial capture is partial.

New validation: authenticated JARVIS shutdown, then guest OS shutdown; verify
only expected isolated processes remain. Retain EvidenceMaster/failed runs.
Any later unregister/delete targets require exact resolved destination checks
and separate cleanup authorization. No original restoration is rollback here.

OPEN: a separate host/enforced access boundary; sufficient destination capacity;
authorized offline source capture and preservation comparisons; complete hashes;
absolute-reference relocation validation; service/registry isolation proof;
safe old-clone shutdown and complete logs; first-boot networking proof.

Stage 6 remains blocked. No guest setup, credentials, provider calls, JARVIS
launch, source/runtime changes, Stage 7 execution or production operation occurs.

## Sources

- Oracle VirtualBox 7.2, global settings and VBOX_USER_HOME:
  https://docs.oracle.com/en/virtualization/virtualbox/7.2/user/Troubleshooting.html
- Oracle VirtualBox CLI, registervm/clonevm/NAT options:
  https://docs.oracle.com/en/virtualization/virtualbox/7.1/user/vboxmanage.html
- Prior recorded installed VirtualBox 7.2.18 help and command results in this task.

HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
