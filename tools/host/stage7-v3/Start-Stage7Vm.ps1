<#
.SYNOPSIS
Starts the acceptance VM for one Stage 7 check (version 3; unchanged from version 2 but for this word): run BY THE OWNER in the jarvis-s6-val session, VM
powered off. A copy of tools\host\Start-Stage7Vm.ps1 (used for 1.0.11; unchanged, evidence) with the check's label
in the disc name and the allowed current snapshot taken from the owner's approval.
1. Restores the clean snapshot FRESH-PREREQ (no JARVIS, no personal data). Every other snapshot is kept; only the
   VM's current state moves. Allowed only when the VM is on the snapshot named in the approval (or already on
   FRESH-PREREQ) AND VirtualBox records no change since that snapshot (currentStateModified="false" in the .vbox),
   so the restore never discards anything.
2. Checks both discs against their hash records and attaches them: the previous build's disc on SATA port 1
   (its package disc JARVIS-PACKAGE-<id>.iso when there is one, otherwise its own Stage 7 disc
   JARVIS-STAGE7-<id>.iso, which carries that build's zip and record at its root: version 3, for every build after
   1.0.11, which was the last one with a package disc) and this check's Stage 7 disc on port 2.
3. Starts the VM through Start-FreshVm.ps1, as for every start (NAT localhost-reachable off, proven from VBox.log).
Records what it did in <Evidence>\stage7-start-<utc>.json.
#>
param(
    [Parameter(Mandatory)] [string] $FinalId,
    [Parameter(Mandatory)] [string] $PreviousId,
    [Parameter(Mandatory)] [string] $Label,
    [Parameter(Mandatory)] [string[]] $AllowedCurrent,
    [Parameter(Mandatory)] [string] $Evidence,
    [string] $Snapshot = 'FRESH-PREREQ',
    [string] $Name = 'JARVIS-S6-FRESH',
    [string] $Root = 'D:\JARVIS-S6-FRESHVM'
)
$ErrorActionPreference = 'Stop'
if ($env:USERNAME -ne 'jarvis-s6-val') { throw "Run this in the jarvis-s6-val session, not as $env:USERNAME" }
if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Elevated session: STOP' }
if ($env:VBOX_USER_HOME -ne "$Root\vbox-home") { throw "VBOX_USER_HOME must be $Root\vbox-home for this account" }
$vbm = 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
function VBM { param([Parameter(ValueFromRemainingArguments)] $a) & $vbm @a; if ($LASTEXITCODE) { throw "VBoxManage failed: $($a -join ' ')" } }
function Info { & $vbm showvminfo $Name --machinereadable }
function Val($info, $key) { ($info | Where-Object { $_ -like "$key=*" } | Select-Object -First 1) -replace "^$key=`"?(.*?)`"?$", '$1' }
function Sha256($p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() }
if (-not (Test-Path -LiteralPath $Evidence)) { New-Item -ItemType Directory -Path $Evidence -Force | Out-Null }
$discs = [ordered]@{}
# The previous build's disc: its package disc (1.0.11 and older) or, from 1.0.12 on, its own Stage 7 disc.
$previousDisc = "JARVIS-PACKAGE-$PreviousId.iso"
if (-not (Test-Path -LiteralPath (Join-Path $Root "media\$previousDisc"))) { $previousDisc = "JARVIS-STAGE7-$PreviousId.iso" }
foreach ($pair in @(@('previous', $previousDisc, 1), @('stage7', "JARVIS-STAGE7-$Label.iso", 2))) {
    $iso = Join-Path $Root "media\$($pair[1])"
    if (-not (Test-Path -LiteralPath $iso) -or -not (Test-Path -LiteralPath "$iso.sha256.json")) { throw "disc or its hash record missing: $iso; STOP" }
    Write-Host "Checking $($pair[1]) ..."
    $recorded = (Get-Content -LiteralPath "$iso.sha256.json" -Raw | ConvertFrom-Json).sha256; $actual = Sha256 $iso
    if ($actual -ne $recorded) { throw "$iso hashes $actual, its record says $recorded; STOP" }
    $discs[$pair[0]] = [ordered]@{ iso = $iso; sha256 = $actual; sata_port = $pair[2] }
}
$info = Info
$state = Val $info 'VMState'
if ($state -ne 'poweroff') { throw "VM state is '$state'; expected poweroff; STOP" }
$names = @($info | Where-Object { $_ -like 'SnapshotName*' } | ForEach-Object { $_ -replace '^SnapshotName[^=]*="(.*)"$', '$1' })
if ($names -notcontains $Snapshot) { throw "snapshot $Snapshot not found; STOP" }
$before = Val $info 'CurrentSnapshotName'
if ($before -notin (@($AllowedCurrent) + $Snapshot)) { throw "the current snapshot is '$before', expected one of: $((@($AllowedCurrent) + $Snapshot) -join ', '); nothing was restored; STOP" }
# The restore discards the VM's current state: only allowed when VirtualBox records no change since that snapshot.
$cfg = (Val $info 'CfgFile') -replace '\\\\', '\'
[xml] $vbox = Get-Content -LiteralPath $cfg -Raw
$modified = $vbox.VirtualBox.Machine.currentStateModified
if ($modified -ne 'false') { throw "VirtualBox records changes since the snapshot '$before' (currentStateModified='$modified'); restoring would discard them; nothing was restored; STOP" }
Write-Host "Restoring the clean snapshot $Snapshot (the snapshot $before is kept) ..."
VBM snapshot $Name restore $Snapshot
$info = Info
$after = Val $info 'CurrentSnapshotName'
if ($after -ne $Snapshot -or (Val $info 'VMState') -ne 'poweroff') { throw "after the restore the current snapshot is '$after' and the state '$(Val $info 'VMState')'; STOP" }
foreach ($d in $discs.Values) { VBM storageattach $Name --storagectl SATA --port $d.sata_port --device 0 --type dvddrive --medium $d.iso }
$info = Info
$record = [ordered]@{
    schema = 'jarvis-stage7-vm-start-v2'; utc = (Get-Date).ToUniversalTime().ToString('o'); account = $env:USERNAME
    label = $Label; final = $FinalId; previous = $PreviousId
    vm_name = $Name; vm_uuid = (Val $info 'UUID'); snapshot_before = $before; allowed_current = @($AllowedCurrent)
    current_state_modified_before = $modified; restored_snapshot = $after
    snapshots_kept = @($info | Where-Object { $_ -like 'SnapshotName*' } | ForEach-Object { $_ -replace '^SnapshotName[^=]*="(.*)"$', '$1' })
    discs = $discs; storage_lines = @($info | Where-Object { $_ -like '"SATA-*' })
}
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
[IO.File]::WriteAllText((Join-Path $Evidence "stage7-start-$stamp.json"), (ConvertTo-Json -InputObject $record -Depth 4), (New-Object Text.UTF8Encoding $false))
Write-Host 'Snapshot restored and discs attached. Starting the VM ...'
& (Join-Path $PSScriptRoot 'Start-FreshVm.ps1') -Name $Name -Root $Root -Evidence $Evidence
if ($LASTEXITCODE) { exit $LASTEXITCODE }
