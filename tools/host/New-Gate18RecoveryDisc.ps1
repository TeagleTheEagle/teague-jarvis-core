<#
.SYNOPSIS
Builds the Gate 18 recovery disc: run BY THE OWNER, own account, non-elevated, after Copy-BackupForGate18.ps1.
Takes the backup copy named in evidence\gate18\backup-copy.json (never the backup drive itself), checks it
against the hash recorded at the copy, and images it together with gate18.cmd, Invoke-Gate18.ps1 and
BACKUP-RECORD.json into D:\JARVIS-release-work\stage6-media\JARVIS-RECOVERY.iso with tools\New-PackageIso.ps1.
Copies the disc and its hash record into D:\JARVIS-S6-FRESHVM\media, checks the copy, and writes
evidence\gate18\recovery-disc.json. Nothing that already exists is overwritten. The backup is personal data:
the payload folder and the disc stay on D: and are never uploaded.
#>
param(
    [string] $Repo = 'C:\Users\jonny\JARVIS-claude-workspace\repo',
    [string] $Media = 'D:\JARVIS-release-work\stage6-media',
    [string] $Dest = 'D:\JARVIS-S6-FRESHVM\media',
    [string] $Evidence = 'D:\JARVIS-S6-FRESHVM\evidence\gate18',
    [long] $MaxBytes = 600MB   # the image builder's default size limit is about 681 MB
)
$ErrorActionPreference = 'Stop'
if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Elevated session: STOP' }
function Sha256($p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() }
$copyRecord = Join-Path $Evidence 'backup-copy.json'
if (-not (Test-Path -LiteralPath $copyRecord)) { throw "missing $copyRecord : run Copy-BackupForGate18.ps1 first; STOP" }
$copied = Get-Content -LiteralPath $copyRecord -Raw | ConvertFrom-Json
$backup = $copied.copy
$guest = 'Invoke-Gate18.ps1', 'gate18.cmd' | ForEach-Object { Join-Path $Repo "tools\guest\$_" }
$builder = Join-Path $Repo 'tools\New-PackageIso.ps1'
foreach ($p in @($backup, $builder) + $guest) { if (-not (Test-Path -LiteralPath $p)) { throw "missing: $p" } }
$payload = Join-Path (Split-Path -Parent $Media) 'recovery-payload'
$out = Join-Path $Media 'JARVIS-RECOVERY.iso'; $copy = Join-Path $Dest 'JARVIS-RECOVERY.iso'; $record = Join-Path $Evidence 'recovery-disc.json'
foreach ($p in $payload, $out, $copy, $record) { if (Test-Path -LiteralPath $p) { throw "already exists, not touched: $p" } }
$bytes = (Get-Item -LiteralPath $backup).Length
if ($bytes -gt $MaxBytes) { throw ("the backup is {0:N0} bytes, larger than this disc builder is proven for ({1:N0}); STOP and tell Claude" -f $bytes, $MaxBytes) }
Write-Host 'Checking the backup copy against the hash recorded when it was copied ...'
$hash = Sha256 $backup
if ($hash -ne $copied.copy_sha256) { throw "the backup copy hashes $hash, the copy record says $($copied.copy_sha256); STOP" }
New-Item -ItemType Directory -Path $payload | Out-Null
Copy-Item -LiteralPath $backup -Destination $payload
$guest | ForEach-Object { Copy-Item -LiteralPath $_ -Destination $payload }
$name = Split-Path -Leaf $backup
$onDisc = [ordered]@{ schema = 'stage6-gate18-backup-on-disc-v1'; file = $name; bytes = $bytes; sha256 = $hash; copied_from_backup_drive_utc = $copied.utc; synthetic = $false }
[IO.File]::WriteAllText((Join-Path $payload 'BACKUP-RECORD.json'), (ConvertTo-Json -InputObject $onDisc), (New-Object Text.UTF8Encoding $false))
$readme = @"
JARVIS recovery disc for Stage 6 Gate 18. It carries the owner's verified backup (personal data; sha256 $hash), BACKUP-RECORD.json, gate18.cmd and Invoke-Gate18.ps1, and PAYLOAD-MANIFEST.json (SHA-256 of every file).
Inside the VM (account jarvis-s6-guest), only after the owner's RESUME_STAGE6_RECOVERY: open this disc in File Explorer and double-click gate18.
No provider keys are on this disc. Built by the owner with tools\host\New-Gate18RecoveryDisc.ps1.
"@
[IO.File]::WriteAllText((Join-Path $payload 'README.txt'), $readme, (New-Object Text.UTF8Encoding $false))
Write-Host 'Building JARVIS-RECOVERY.iso (the disc is opened once to check it) ...'
& $builder -Payload $payload -Out $out -Label JARVIS_RECOVERY | Out-Null
$built = Get-Content -LiteralPath "$out.sha256.json" -Raw | ConvertFrom-Json
Write-Host "Copying the disc to $Dest ..."
Copy-Item -LiteralPath $out -Destination $Dest
Copy-Item -LiteralPath "$out.sha256.json" -Destination $Dest
$copyHash = Sha256 $copy
if ($copyHash -ne $built.sha256) { throw "copy hash $copyHash differs from the build record $($built.sha256); STOP" }
$result = [ordered]@{
    schema = 'stage6-gate18-recovery-disc-v1'; utc = (Get-Date).ToUniversalTime().ToString('o'); performed_by = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    backup_file = $name; backup_bytes = $bytes; backup_sha256 = $hash; backup_equals_copy_record = $true
    guest_files = @($guest | ForEach-Object { [ordered]@{ name = (Split-Path -Leaf $_); sha256 = (Sha256 $_) } })
    iso = $out; iso_sha256 = $built.sha256; iso_bytes = $built.bytes; payload_files = $built.payload_files; payload_manifest_sha256 = $built.payload_manifest_sha256; readback = $built.readback
    copy = $copy; copy_sha256 = $copyHash
}
[IO.File]::WriteAllText($record, (ConvertTo-Json -InputObject $result -Depth 4), (New-Object Text.UTF8Encoding $false))
Write-Host ''
Write-Host "Recovery disc: $copy"
Write-Host ("JARVIS-RECOVERY.iso  {0:N0} bytes  sha256 {1}" -f $built.bytes, $built.sha256)
