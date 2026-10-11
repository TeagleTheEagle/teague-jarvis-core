<#
.SYNOPSIS
Takes a named snapshot of the Gate 16R acceptance VM: run BY THE OWNER in the jarvis-s6-val session with the
VM powered off (shut down cleanly from inside Windows first). Refuses if the VM is not powered off or if a
snapshot of that name already exists. Records the snapshot UUID, the current-snapshot pointer, the .vbox and
.nvram hashes and the Snapshots folder listing into vm\snapshot-<name>-<utc>.json (AMENDMENT-v2 section 6(h)/(i)).
#>
param(
    [Parameter(Mandatory)] [string] $Snapshot,
    [string] $Description = '',
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
function Info { & $vbm showvminfo $Name --machinereadable }
function Val($info, $key) { ($info | Where-Object { $_ -like "$key=*" } | Select-Object -First 1) -replace "^$key=`"?(.*?)`"?$", '$1' }
function Sha256($p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() }
$info = Info
$state = Val $info 'VMState'
if ($state -ne 'poweroff') { throw "VM state is '$state'; shut Windows down from inside the VM first (Start > Power > Shut down) and wait for the window to close; STOP" }
$existing = @($info | Where-Object { $_ -like 'SnapshotName*' } | ForEach-Object { $_ -replace '^SnapshotName[^=]*="(.*)"$', '$1' })
if ($existing -contains $Snapshot) { throw "a snapshot named $Snapshot already exists; not taken again; STOP" }
$vbox = (Val $info 'CfgFile') -replace '\\\\', '\'
$nvram = Join-Path $Root "machines\$Name\$Name.nvram"
$before = [ordered]@{ vbox_sha256 = (Sha256 $vbox); nvram_sha256 = (Sha256 $nvram); snapshots = $existing }
if ($Description) { VBM snapshot $Name take $Snapshot --description $Description } else { VBM snapshot $Name take $Snapshot }
$info = Info
$names = @($info | Where-Object { $_ -like 'SnapshotName*' })
$uuids = @($info | Where-Object { $_ -like 'SnapshotUUID*' })
$list = @(for ($i = 0; $i -lt $names.Count; $i++) { [ordered]@{ name = ($names[$i] -replace '^[^=]*="(.*)"$', '$1'); uuid = ($uuids[$i] -replace '^[^=]*="(.*)"$', '$1') } })
$taken = $list | Where-Object { $_.name -eq $Snapshot } | Select-Object -First 1
if (-not $taken) { throw "snapshot $Snapshot not found after taking it; STOP" }
$snapDir = Join-Path $Root "machines\$Name\Snapshots"
$record = [ordered]@{
    schema = 'stage6-fresh-vm-snapshot-v1'; utc = (Get-Date).ToUniversalTime().ToString('o'); account = $env:USERNAME
    vm_name = $Name; vm_uuid = (Val $info 'UUID'); snapshot_name = $Snapshot; snapshot_uuid = $taken.uuid; description = $Description
    current_snapshot_name = (Val $info 'CurrentSnapshotName'); current_snapshot_uuid = (Val $info 'CurrentSnapshotUUID')
    before = $before
    vbox_file = $vbox; vbox_sha256_after = (Sha256 $vbox); nvram_sha256_after = (Sha256 $nvram)
    all_snapshots = $list
    snapshots_folder = @(if (Test-Path -LiteralPath $snapDir) { Get-ChildItem -LiteralPath $snapDir -File | ForEach-Object { [ordered]@{ name = $_.Name; bytes = $_.Length; last_write_utc = $_.LastWriteTimeUtc.ToString('o') } } })
    vm_state = (Val $info 'VMState')
}
Copy-Item -LiteralPath $vbox -Destination (Join-Path $Evidence "$Name.vbox.$Snapshot-copy")
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
[IO.File]::WriteAllText((Join-Path $Evidence "snapshot-$Snapshot-$stamp.json"), (ConvertTo-Json -InputObject $record -Depth 4), (New-Object Text.UTF8Encoding $false))
ConvertTo-Json -InputObject $record -Depth 4
