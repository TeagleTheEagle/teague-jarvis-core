<#
.SYNOPSIS
Starts the Gate 16R acceptance VM JARVIS-S6-FRESH. Run BY THE OWNER in the jarvis-s6-val session for EVERY
start of the VM during Stage 6.
Why a script: VirtualBox 7.2.18 does not persist NAT "localhost-reachable = off" in the .vbox. It saves the
value as the empty default (<NAT/>) and reads that empty default back as "on" (observed between step 6 and
step 6b; see step6-evaluation.json). So this script re-applies --nat-localhostreachable1 off, confirms it
through showvminfo in the same VBoxSVC session, starts the VM at once, and then records the value the running
VM actually received, from its own VBox.log (CFGM key LocalhostReachable). Writes vm\start-<utc>.json.
#>
param(
    [string] $Name = 'JARVIS-S6-FRESH',
    [string] $Root = 'D:\JARVIS-S6-FRESHVM',
    [string] $Evidence = 'D:\JARVIS-S6-FRESHVM\evidence\gate16r-20261002\vm',
    [int] $LogWaitSeconds = 90
)
$ErrorActionPreference = 'Stop'
if ($env:USERNAME -ne 'jarvis-s6-val') { throw "Run this in the jarvis-s6-val session, not as $env:USERNAME" }
if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Elevated session: STOP' }
if ($env:VBOX_USER_HOME -ne "$Root\vbox-home") { throw "VBOX_USER_HOME must be $Root\vbox-home for this account" }
$vbm = 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
function VBM { param([Parameter(ValueFromRemainingArguments)] $a) & $vbm @a; if ($LASTEXITCODE) { throw "VBoxManage failed: $($a -join ' ')" } }
function Info { & $vbm showvminfo $Name --machinereadable }
function Val($info, $key) { ($info | Where-Object { $_ -like "$key=*" } | Select-Object -First 1) -replace "^$key=`"?(.*?)`"?$", '$1' }
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
$info = Info
$state = Val $info 'VMState'
if ($state -ne 'poweroff') { throw "VM state is '$state'; expected poweroff; STOP" }
$vbox = (Val $info 'CfgFile') -replace '\\\\', '\'
# Re-apply the non-persisted isolation setting and confirm it in this VBoxSVC session.
VBM modifyvm $Name --nat-localhostreachable1 off
$info = Info
$reach = Val $info 'localhostReachable'
if ($reach -ne '0') { throw "localhostReachable is '$reach' after re-applying off; STOP" }
$before = [ordered]@{
    vbox_sha256 = (Get-FileHash -LiteralPath $vbox -Algorithm SHA256).Hash.ToLower(); localhostReachable = $reach; audio = (Val $info 'audio')
    nic1 = (Val $info 'nic1'); nic2 = (Val $info 'nic2'); nic3 = (Val $info 'nic3'); nic4 = (Val $info 'nic4')
    usb = (Val $info 'usb'); clipboard = (Val $info 'clipboard'); draganddrop = (Val $info 'draganddrop'); SecureBoot = (Val $info 'SecureBoot')
}
VBM startvm $Name --type gui
# The running VM's own log lists the configuration it received (CFGM dump); wait for that line.
$log = Join-Path $Root "machines\$Name\Logs\VBox.log"
$deadline = (Get-Date).AddSeconds($LogWaitSeconds); $lines = @()
while ((Get-Date) -lt $deadline) {
    if (Test-Path -LiteralPath $log) { $lines = @(Select-String -LiteralPath $log -Pattern 'LocalhostReachable' | ForEach-Object { $_.Line.Trim() }); if ($lines.Count) { break } }
    Start-Sleep -Seconds 2
}
$bad = @($lines | Where-Object { $_ -notmatch '= 0x0+ \(0\)' })
$verdict = if ($lines.Count -and -not $bad.Count) { 'LocalhostReachable = 0 confirmed in VBox.log' } elseif ($lines.Count) { 'CHECK: VBox.log shows a non-zero LocalhostReachable; STOP' } else { 'VBox.log line not found within the wait; Claude reads the log' }
$record = [ordered]@{
    schema = 'stage6-fresh-vm-start-v1'; utc = (Get-Date).ToUniversalTime().ToString('o'); account = $env:USERNAME; vm_name = $Name; vm_uuid = (Val $info 'UUID')
    settings_at_start = $before; vbox_log = $log; vbox_log_localhost_reachable = $lines; verdict = $verdict; vm_state_after = (Val (Info) 'VMState')
}
[IO.File]::WriteAllText((Join-Path $Evidence "start-$stamp.json"), (ConvertTo-Json -InputObject $record -Depth 4), (New-Object Text.UTF8Encoding $false))
ConvertTo-Json -InputObject $record -Depth 4
if ($verdict -like 'CHECK*') { exit 2 }
