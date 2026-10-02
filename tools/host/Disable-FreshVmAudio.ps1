<#
.SYNOPSIS
Gate 16R step 6b: run BY THE OWNER in the jarvis-s6-val session, before the VM is ever started.
The approved prompt (step 6) requires NO audio device. New-FreshVm.ps1 used '--audio-driver none',
which VirtualBox 7.2 recorded as an enabled adapter with the Null driver (AudioAdapter enabled="true").
This script turns the adapter off (--audio-enabled off), re-records showvminfo and the .vbox hash,
and writes vm\step6b-audio-off.json. Refuses unless the VM is powered off and has never been started.
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
$info = & $vbm showvminfo $Name --machinereadable
$state = ($info | Where-Object { $_ -like 'VMState=*' }) -replace '^VMState="(.*)"$', '$1'
if ($state -ne 'poweroff') { throw "VM state is '$state', expected poweroff; STOP" }
if (Test-Path -LiteralPath "$Root\machines\$Name\Logs") { throw 'the VM has a Logs folder, so it has been started; STOP (step 6b is only for a never-started VM)' }
$before = @($info | Where-Object { $_ -like 'audio*' })
VBM modifyvm $Name --audio-enabled off
$info = & $vbm showvminfo $Name --machinereadable
[IO.File]::WriteAllLines((Join-Path $Evidence 'showvminfo-after-6b.txt'), $info)
$vbox = (($info | Where-Object { $_ -like 'CfgFile=*' }) -replace '^CfgFile="(.*)"$', '$1') -replace '\\\\', '\'
$record = [ordered]@{
    schema = 'stage6-fresh-vm-audio-off-v1'; utc = (Get-Date).ToUniversalTime().ToString('o'); account = $env:USERNAME
    vm_name = $Name; vm_uuid = (($info | Where-Object { $_ -like 'UUID=*' }) -replace '^UUID="(.*)"$', '$1')
    audio_before = $before; audio_after = @($info | Where-Object { $_ -like 'audio*' })
    vbox_file = $vbox; vbox_sha256 = (Get-FileHash -LiteralPath $vbox -Algorithm SHA256).Hash.ToLower()
    vm_state = (($info | Where-Object { $_ -like 'VMState=*' }) -replace '^VMState="(.*)"$', '$1')
}
[IO.File]::WriteAllText((Join-Path $Evidence 'step6b-audio-off.json'), (ConvertTo-Json -InputObject $record -Depth 3), (New-Object Text.UTF8Encoding $false))
ConvertTo-Json -InputObject $record -Depth 3
