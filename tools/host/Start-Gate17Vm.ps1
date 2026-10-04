<#
.SYNOPSIS
Starts the acceptance VM for Gates 17 and 19: run BY THE OWNER in the jarvis-s6-val session, VM powered off.
Checks both package discs in D:\JARVIS-S6-FRESHVM\media against their hash records, puts the disc with the
previous build on SATA port 1 (in place of the Windows disc) and the disc with the build under acceptance on
SATA port 2, records what is attached, and then starts the VM through Start-FreshVm.ps1 as for every start
(localhost-reachable re-applied and proven from VBox.log). Safe to run again for a later start: attaching the
same discs changes nothing.
#>
param(
    [Parameter(Mandatory)] [string] $FinalId,
    [Parameter(Mandatory)] [string] $PreviousId,
    [string] $Name = 'JARVIS-S6-FRESH',
    [string] $Root = 'D:\JARVIS-S6-FRESHVM',
    [string] $Evidence = 'D:\JARVIS-S6-FRESHVM\evidence\gate17\vm'
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
foreach ($pair in @(@('previous', $PreviousId, 1), @('final', $FinalId, 2))) {
    $iso = Join-Path $Root "media\JARVIS-PACKAGE-$($pair[1]).iso"
    if (-not (Test-Path -LiteralPath $iso) -or -not (Test-Path -LiteralPath "$iso.sha256.json")) { throw "package disc or its hash record missing: $iso; STOP" }
    Write-Host "Checking $(Split-Path -Leaf $iso) ..."
    $recorded = (Get-Content -LiteralPath "$iso.sha256.json" -Raw | ConvertFrom-Json).sha256; $actual = Sha256 $iso
    if ($actual -ne $recorded) { throw "$iso hashes $actual, its record says $recorded; STOP" }
    $discs[$pair[0]] = [ordered]@{ release = $pair[1]; iso = $iso; sha256 = $actual; sata_port = $pair[2] }
}
$state = Val (Info) 'VMState'
if ($state -ne 'poweroff') { throw "VM state is '$state'; expected poweroff; STOP" }
foreach ($d in $discs.Values) { VBM storageattach $Name --storagectl SATA --port $d.sata_port --device 0 --type dvddrive --medium $d.iso }
$info = Info
$record = [ordered]@{
    schema = 'stage6-gate17-discs-attached-v1'; utc = (Get-Date).ToUniversalTime().ToString('o'); account = $env:USERNAME
    vm_name = $Name; vm_uuid = (Val $info 'UUID'); current_snapshot = (Val $info 'CurrentSnapshotName'); discs = $discs
    storage_lines = @($info | Where-Object { $_ -like '"SATA-*' })
}
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
[IO.File]::WriteAllText((Join-Path $Evidence "gate17-discs-$stamp.json"), (ConvertTo-Json -InputObject $record -Depth 4), (New-Object Text.UTF8Encoding $false))
Write-Host 'Discs attached. Starting the VM ...'
& (Join-Path $PSScriptRoot 'Start-FreshVm.ps1') -Name $Name -Root $Root -Evidence $Evidence
if ($LASTEXITCODE) { exit $LASTEXITCODE }
