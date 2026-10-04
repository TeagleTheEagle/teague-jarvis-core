<#
.SYNOPSIS
Gate 18 backup copy, version 2 (after gate18-incident-01): run BY THE OWNER, own account (jonny), non-elevated,
after making a fresh backup in the everyday JARVIS (Settings > Backups > "Create verified backup", then
"Test restore in temporary folder"). Never run by Claude: the backup folder is an owner-only path.

It looks only at the .zip files directly in the backup folder (no subfolders), takes the newest (or -File),
and copies it to D:\JARVIS-S6-FRESHVM\media only if:
  - its "Test restore" receipt <id>.restore-check.json is beside it and says restore_rehearsal_passed;
  - the archive holds manifest.json (format 1, same id), data/jarvis.sqlite3, and no .env file;
  - it is no larger than the recovery disc builder is proven for (600 MB).
The source is hashed before and after the copy, the copy itself is hashed, and the record is written to
evidence\gate18\backup-copy.json (never overwritten). The backup folder is only read.

Version 1 listed every file on the backup drive (Windows PowerShell 5.1 ignores -Include together with
-LiteralPath) and copied a report file; see evidence\gate18\incident-01-backup-copy.json.
#>
param(
    [string] $Source = 'C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis-backups',
    [string] $File,
    [string] $Dest = 'D:\JARVIS-S6-FRESHVM\media',
    [string] $Evidence = 'D:\JARVIS-S6-FRESHVM\evidence\gate18',
    [long] $MaxBytes = 600MB
)
$ErrorActionPreference = 'Stop'
function Halt($m) { Write-Host ''; Write-Host "STOPPED: $m"; Write-Host 'Nothing was copied. Photograph this window for Claude.'; exit 2 }
function Sha256($p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() }
if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { Halt 'this window has administrator rights. Close it and use a normal PowerShell window.' }
$record = Join-Path $Evidence 'backup-copy.json'
if (Test-Path -LiteralPath $record) { Halt "$record already exists; it is not overwritten." }
if (-not (Test-Path -LiteralPath $Source -PathType Container)) { Halt "backup folder not found: $Source. Look at the folder named in JARVIS Settings > Backups and tell Claude." }

$archives = @(Get-ChildItem -LiteralPath $Source -File | Where-Object { $_.Extension -eq '.zip' } | Sort-Object LastWriteTimeUtc -Descending)
Write-Host "Backups in $Source (read only):"
$archives | ForEach-Object { Write-Host ('  {0}  {1:N0} bytes  {2:u}' -f $_.Name, $_.Length, $_.LastWriteTimeUtc) }
if (-not $archives.Count) { Halt "no .zip backup in $Source. Make one in JARVIS Settings > Backups first." }
$chosen = if ($File) { $archives | Where-Object { $_.Name -eq $File } | Select-Object -First 1 } else { $archives[0] }
if (-not $chosen) { Halt "backup not found in that folder: $File" }
$id = [IO.Path]::GetFileNameWithoutExtension($chosen.Name)
Write-Host "Chosen: $($chosen.Name)"

$receiptPath = Join-Path $Source ($id + '.restore-check.json')
if (-not (Test-Path -LiteralPath $receiptPath)) { Halt "no Test restore receipt for this backup ($id.restore-check.json). In JARVIS Settings > Backups press 'Test restore in temporary folder', then run this again." }
$receipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
if ($receipt.status -ne 'restore_rehearsal_passed' -or $receipt.id -ne $id) { Halt "the Test restore receipt does not say restore_rehearsal_passed for $id." }
if ($chosen.Length -gt $MaxBytes) { Halt ('the backup is {0:N0} bytes, larger than the recovery disc builder is proven for ({1:N0}). Tell Claude.' -f $chosen.Length, $MaxBytes) }

Write-Host 'Hashing the backup (before copy)...'; $before = Sha256 $chosen.FullName
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::OpenRead($chosen.FullName)
try {
    $names = @($zip.Entries | ForEach-Object { $_.FullName })
    $m = $zip.GetEntry('manifest.json')
    if (-not $m) { Halt 'the archive has no manifest.json.' }
    $reader = New-Object IO.StreamReader($m.Open()); try { $manifest = $reader.ReadToEnd() | ConvertFrom-Json } finally { $reader.Dispose() }
} finally { $zip.Dispose() }
if ($manifest.format -ne 1 -or $manifest.id -ne $id) { Halt "manifest.json is not format 1 for id $id." }
if ($names -notcontains 'data/jarvis.sqlite3') { Halt 'the archive has no data/jarvis.sqlite3.' }
$keyFiles = @($names | Where-Object { ($_ -split '/')[-1] -eq '.env' })
if ($keyFiles.Count) { Halt 'the archive contains a .env (key) file. It must not go into the VM.' }

$target = Join-Path $Dest $chosen.Name
if (Test-Path -LiteralPath $target) { Halt "already exists, not touched: $target" }
New-Item -ItemType Directory -Path $Evidence -Force | Out-Null
Write-Host "Copying to $target ..."; Copy-Item -LiteralPath $chosen.FullName -Destination $target
Write-Host 'Hashing the copy...'; $copyHash = Sha256 $target
Write-Host 'Hashing the backup again (after copy)...'; $after = Sha256 $chosen.FullName
if ($copyHash -ne $before -or $after -ne $before) { Halt "hash mismatch: backup before $before, copy $copyHash, backup after $after." }

$created = [DateTimeOffset]::FromUnixTimeMilliseconds([long]([double]$manifest.created_at * 1000)).UtcDateTime
$checked = [DateTimeOffset]::FromUnixTimeMilliseconds([long]([double]$receipt.checked_at * 1000)).UtcDateTime
$out = [ordered]@{
    schema = 'stage6-gate18-backup-copy-v2'; utc = (Get-Date).ToUniversalTime().ToString('o'); performed_by = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    copy_script = [ordered]@{ name = Split-Path -Leaf $PSCommandPath; sha256 = (Sha256 $PSCommandPath) }
    source_folder = $Source; source = $chosen.FullName; source_bytes = $chosen.Length; source_last_write_utc = $chosen.LastWriteTimeUtc.ToString('o')
    source_sha256_before = $before; source_sha256_after = $after; copy = $target; copy_sha256 = $copyHash; copy_bytes = (Get-Item -LiteralPath $target).Length
    backup = [ordered]@{ id = $id; format = $manifest.format; created_utc = $created.ToString('o'); files_in_manifest = @($manifest.files.PSObject.Properties).Count; archive_entries = $names.Count; database_counts = $manifest.database_counts; key_files = 0 }
    restore_check = [ordered]@{ status = $receipt.status; checked_utc = $checked.ToString('o'); files = $receipt.files; database_counts = $receipt.database_counts }
    source_written = $false
    archives_seen = @($archives | ForEach-Object { [ordered]@{ name = $_.Name; bytes = $_.Length; last_write_utc = $_.LastWriteTimeUtc.ToString('o') } })
    next = 'gate18-step in the jonny account builds the recovery disc (after Claude has checked this record)'
}
[IO.File]::WriteAllText($record, (ConvertTo-Json -InputObject $out -Depth 5), (New-Object Text.UTF8Encoding $false))
Write-Host ''
Write-Host ('DONE: copied {0} ({1:N0} bytes), made {2:u}, Test restore passed {3:u}. The backup was not changed.' -f $chosen.Name, $chosen.Length, $created, $checked)
Write-Host 'Tell Claude "copied".'
