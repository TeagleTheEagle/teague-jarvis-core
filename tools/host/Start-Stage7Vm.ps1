<#
.SYNOPSIS
Starts the acceptance VM for Stage 7: run BY THE OWNER in the jarvis-s6-val session, VM powered off.
1. Restores the clean snapshot FRESH-PREREQ (no JARVIS, no personal data). The other snapshots, including
   GATE18-PASS with the owner's data, are kept; only the VM's current state moves.
2. Checks both discs against their hash records and attaches them: the previous build's package disc on SATA
   port 1 and the Stage 7 disc on port 2 (the same layout as Stage 6 Gate 17).
3. Starts the VM through Start-FreshVm.ps1, as for every start (NAT localhost-reachable off, proven from VBox.log).
Records what it did in <Evidence>\stage7-start-<utc>.json. Owner decision of 2026-10-04: the Stage 6 VM is reused
for Stage 7 from this snapshot.
#>
param(
    [Parameter(Mandatory)] [string] $FinalId,
    [Parameter(Mandatory)] [string] $PreviousId,
    [string] $Snapshot = 'FRESH-PREREQ',
    [string] $Name = 'JARVIS-S6-FRESH',
    [string] $Root = 'D:\JARVIS-S6-FRESHVM',
    [string] $Evidence = 'D:\JARVIS-stage7\evidence\vm'
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
foreach ($pair in @(@('previous', "JARVIS-PACKAGE-$PreviousId.iso", 1), @('stage7', "JARVIS-STAGE7-$FinalId.iso", 2))) {
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
# The restore discards the VM's current state. That is only safe when the VM has not run since its last snapshot:
# the last Stage 6 snapshot (GATE18-PASS), or an earlier Stage 7 start that restored FRESH-PREREQ and never ran.
if ($before -notin 'GATE18-PASS', $Snapshot) { throw "the current snapshot is '$before', expected GATE18-PASS or $Snapshot; nothing was restored; STOP" }
Write-Host "Restoring the clean snapshot $Snapshot (the snapshot $before is kept) ..."
VBM snapshot $Name restore $Snapshot
$info = Info
$after = Val $info 'CurrentSnapshotName'
if ($after -ne $Snapshot -or (Val $info 'VMState') -ne 'poweroff') { throw "after the restore the current snapshot is '$after' and the state '$(Val $info 'VMState')'; STOP" }
foreach ($d in $discs.Values) { VBM storageattach $Name --storagectl SATA --port $d.sata_port --device 0 --type dvddrive --medium $d.iso }
$info = Info
$record = [ordered]@{
    schema = 'jarvis-stage7-vm-start-v1'; utc = (Get-Date).ToUniversalTime().ToString('o'); account = $env:USERNAME
    vm_name = $Name; vm_uuid = (Val $info 'UUID'); snapshot_before = $before; restored_snapshot = $after
    snapshots_kept = @($info | Where-Object { $_ -like 'SnapshotName*' } | ForEach-Object { $_ -replace '^SnapshotName[^=]*="(.*)"$', '$1' })
    discs = $discs; storage_lines = @($info | Where-Object { $_ -like '"SATA-*' })
}
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
[IO.File]::WriteAllText((Join-Path $Evidence "stage7-start-$stamp.json"), (ConvertTo-Json -InputObject $record -Depth 4), (New-Object Text.UTF8Encoding $false))
Write-Host 'Snapshot restored and discs attached. Starting the VM ...'
& (Join-Path $PSScriptRoot 'Start-FreshVm.ps1') -Name $Name -Root $Root -Evidence $Evidence
if ($LASTEXITCODE) { exit $LASTEXITCODE }
