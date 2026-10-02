<#
.SYNOPSIS
Gate 16R step 7 recovery: run BY THE OWNER in the jarvis-s6-val session with the VM powered off.
The first Windows Setup attempt wrote a "Windows Boot Manager" entry into the VM's UEFI variable store, ahead
of the disc, so the half-installed disk boots before the disc on every start and Setup reports "The computer
restarted unexpectedly". This re-initialises the variable store (VBoxManage modifynvram inituefivarstore) and
re-enrols the Secure Boot keys exactly as New-FreshVm.ps1 did, restoring the configured order: disc first.
Records the .nvram hash before and after into vm\step7-nvram-reset-<utc>.json. Nothing else is changed.
#>
param(
    [string] $Name = 'JARVIS-S6-FRESH',
    [string] $Root = 'D:\JARVIS-S6-FRESHVM',
    [string] $Evidence = 'D:\JARVIS-S6-FRESHVM\evidence\gate16r-20261002\vm'
)
$ErrorActionPreference = 'Stop'
if ($env:USERNAME -ne 'jarvis-s6-val') { throw "Run this in the jarvis-s6-val session, not as $env:USERNAME" }
if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Elevated session: STOP' }
if ($env:VBOX_USER_HOME -ne "$Root\vbox-home") { throw "VBOX_USER_HOME must be $Root\vbox-home for this account" }
$vbm = 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
function VBM { param([Parameter(ValueFromRemainingArguments)] $a) & $vbm @a; if ($LASTEXITCODE) { throw "VBoxManage failed: $($a -join ' ')" } }
function Val($info, $key) { ($info | Where-Object { $_ -like "$key=*" } | Select-Object -First 1) -replace "^$key=`"?(.*?)`"?$", '$1' }
$info = & $vbm showvminfo $Name --machinereadable
$state = Val $info 'VMState'
if ($state -ne 'poweroff') { throw "VM state is '$state'; power the VM off first (Machine > Close > Power off); STOP" }
$nvram = Join-Path $Root "machines\$Name\$Name.nvram"
$before = if (Test-Path -LiteralPath $nvram) { (Get-FileHash -LiteralPath $nvram -Algorithm SHA256).Hash.ToLower() } else { 'absent' }
VBM modifynvram $Name inituefivarstore
VBM modifynvram $Name enrollmssignatures
VBM modifynvram $Name enrollorclpk
$info = & $vbm showvminfo $Name --machinereadable
$record = [ordered]@{
    schema = 'stage6-fresh-vm-nvram-reset-v1'; utc = (Get-Date).ToUniversalTime().ToString('o'); account = $env:USERNAME; vm_name = $Name; vm_uuid = (Val $info 'UUID')
    reason = 'the first Windows Setup attempt (started 2026-10-02T04:12Z, stalled at 42%, reset by the owner) left a Windows Boot Manager entry in the UEFI variable store ahead of the disc; every later start booted the half-installed disk; the variable store is re-initialised and the Secure Boot keys re-enrolled as at creation'
    commands = @('modifynvram inituefivarstore', 'modifynvram enrollmssignatures', 'modifynvram enrollorclpk')
    nvram_file = $nvram; nvram_sha256_before = $before; nvram_sha256_after = (Get-FileHash -LiteralPath $nvram -Algorithm SHA256).Hash.ToLower()
    SecureBoot = (Val $info 'SecureBoot'); firmware = (Val $info 'firmware'); vm_state = (Val $info 'VMState')
    next = 'step7-start-vm-from-disc.cmd (answers the disc prompt from the host); Setup wipes the disk and installs from scratch'
}
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
[IO.File]::WriteAllText((Join-Path $Evidence "step7-nvram-reset-$stamp.json"), (ConvertTo-Json -InputObject $record -Depth 3), (New-Object Text.UTF8Encoding $false))
ConvertTo-Json -InputObject $record -Depth 3
