<#
.SYNOPSIS
Starts the acceptance VM for Gate 18: run BY THE OWNER in the jarvis-s6-val session, VM powered off, only after
the owner's RESUME_STAGE6_RECOVERY. Checks the recovery disc in D:\JARVIS-S6-FRESHVM\media against its hash
record, puts it on SATA port 2 (in place of the FINAL package disc; the VM already holds the extracted package
from Gate 17), records what is attached, and starts the VM through Start-FreshVm.ps1 as for every start.
The VM continues from the state of snapshot GATE17-19-PASS. Safe to run again for a later start.
#>
param(
    [string] $Name = 'JARVIS-S6-FRESH',
    [string] $Root = 'D:\JARVIS-S6-FRESHVM',
    [string] $Evidence = 'D:\JARVIS-S6-FRESHVM\evidence\gate18\vm'
)
$ErrorActionPreference = 'Stop'
if ($env:USERNAME -ne 'jarvis-s6-val') { throw "Run this in the jarvis-s6-val session, not as $env:USERNAME" }
if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Elevated session: STOP' }
if ($env:VBOX_USER_HOME -ne "$Root\vbox-home") { throw "VBOX_USER_HOME must be $Root\vbox-home for this account" }
$vbm = 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
function VBM { param([Parameter(ValueFromRemainingArguments)] $a) & $vbm @a; if ($LASTEXITCODE) { throw "VBoxManage failed: $($a -join ' ')" } }
function Info { & $vbm showvminfo $Name --machinereadable }
function Val($info, $key) { ($info | Where-Object { $_ -like "$key=*" } | Select-Object -First 1) -replace "^$key=`"?(.*?)`"?$", '$1' }
if (-not (Test-Path -LiteralPath $Evidence)) { New-Item -ItemType Directory -Path $Evidence -Force | Out-Null }
$iso = Join-Path $Root 'media\JARVIS-RECOVERY.iso'
if (-not (Test-Path -LiteralPath $iso) -or -not (Test-Path -LiteralPath "$iso.sha256.json")) { throw "recovery disc or its hash record missing: $iso; STOP" }
Write-Host 'Checking JARVIS-RECOVERY.iso ...'
$recorded = (Get-Content -LiteralPath "$iso.sha256.json" -Raw | ConvertFrom-Json).sha256; $actual = (Get-FileHash -LiteralPath $iso -Algorithm SHA256).Hash.ToLower()
if ($actual -ne $recorded) { throw "$iso hashes $actual, its record says $recorded; STOP" }
$info = Info
if ((Val $info 'VMState') -ne 'poweroff') { throw "VM state is '$(Val $info 'VMState')'; expected poweroff; STOP" }
$snapshot = Val $info 'CurrentSnapshotName'
if ($snapshot -ne 'GATE17-19-PASS') { throw "current snapshot is '$snapshot', expected GATE17-19-PASS; STOP" }
VBM storageattach $Name --storagectl SATA --port 2 --device 0 --type dvddrive --medium $iso
$info = Info
$record = [ordered]@{
    schema = 'stage6-gate18-disc-attached-v1'; utc = (Get-Date).ToUniversalTime().ToString('o'); account = $env:USERNAME
    vm_name = $Name; vm_uuid = (Val $info 'UUID'); current_snapshot = $snapshot; recovery_disc = [ordered]@{ iso = $iso; sha256 = $actual; sata_port = 2 }
    storage_lines = @($info | Where-Object { $_ -like '"SATA-*' })
}
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
[IO.File]::WriteAllText((Join-Path $Evidence "gate18-disc-$stamp.json"), (ConvertTo-Json -InputObject $record -Depth 4), (New-Object Text.UTF8Encoding $false))
Write-Host 'Recovery disc attached. Starting the VM ...'
& (Join-Path $PSScriptRoot 'Start-FreshVm.ps1') -Name $Name -Root $Root -Evidence $Evidence
if ($LASTEXITCODE) { exit $LASTEXITCODE }
