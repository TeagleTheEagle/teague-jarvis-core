<#
.SYNOPSIS
Gate 18 preparation (AMENDMENT-v3 D8): run BY THE OWNER, own account, non-elevated. Lists the backup
archives on the backup drive (read-only), copies the chosen one (newest by default) to
D:\JARVIS-S6-FRESHVM\media\, hashes the source before and after the copy and the copy itself, and writes
gate18\backup-copy.json. The backup drive is never written. Claude then builds JARVIS-RECOVERY.iso from
the copy and records its hash; the restore itself happens inside the VM after RESUME_STAGE6_RECOVERY.
#>
param(
    [string] $Source = 'E:\JARVIS-BACKUP',
    [string] $Dest = 'D:\JARVIS-S6-FRESHVM\media',
    [string] $File,
    [string] $Evidence = 'D:\JARVIS-S6-FRESHVM\evidence\gate18'
)
$ErrorActionPreference = 'Stop'
if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Elevated session: STOP' }
if (-not (Test-Path -LiteralPath $Source)) { throw "backup folder not found: $Source (is the backup drive connected?)" }
function Sha256($p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() }
$archives = @(Get-ChildItem -LiteralPath $Source -File -Recurse -Include '*.zip' | Sort-Object LastWriteTimeUtc -Descending)
if (-not $archives.Count) { throw "no .zip archive under $Source" }
Write-Host 'Backup archives found (read-only):'
$archives | ForEach-Object { Write-Host ("  {0}  {1:N0} bytes  {2:u}" -f $_.FullName, $_.Length, $_.LastWriteTimeUtc) }
$chosen = if ($File) { $archives | Where-Object { $_.Name -eq $File -or $_.FullName -eq $File } | Select-Object -First 1 } else { $archives[0] }
if (-not $chosen) { throw "archive not found: $File" }
$target = Join-Path $Dest $chosen.Name
if (Test-Path -LiteralPath $target) { throw "already exists, not touched: $target" }
New-Item -ItemType Directory -Path $Evidence -Force | Out-Null
Write-Host "Hashing source (before copy)..."; $before = Sha256 $chosen.FullName
Write-Host "Copying to $target ..."; Copy-Item -LiteralPath $chosen.FullName -Destination $target
Write-Host "Hashing copy..."; $copyHash = Sha256 $target
Write-Host "Hashing source (after copy)..."; $after = Sha256 $chosen.FullName
if ($copyHash -ne $before -or $after -ne $before) { throw "hash mismatch: source before $before, copy $copyHash, source after $after; STOP" }
$record = [ordered]@{
    schema = 'stage6-gate18-backup-copy-v1'; utc = (Get-Date).ToUniversalTime().ToString('o'); performed_by = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    source = $chosen.FullName; source_bytes = $chosen.Length; source_last_write_utc = $chosen.LastWriteTimeUtc.ToString('o')
    source_sha256_before = $before; source_sha256_after = $after; copy = $target; copy_sha256 = $copyHash; copy_bytes = (Get-Item -LiteralPath $target).Length
    backup_drive_written = $false; archives_seen = @($archives | ForEach-Object { [ordered]@{ path = $_.FullName; bytes = $_.Length; last_write_utc = $_.LastWriteTimeUtc.ToString('o') } })
    next = 'Claude builds JARVIS-RECOVERY.iso from the copy and records its hash; Gate 18 runs inside the VM only after the owner issues RESUME_STAGE6_RECOVERY'
}
[IO.File]::WriteAllText((Join-Path $Evidence 'backup-copy.json'), (ConvertTo-Json -InputObject $record -Depth 4), (New-Object Text.UTF8Encoding $false))
ConvertTo-Json -InputObject $record -Depth 4
