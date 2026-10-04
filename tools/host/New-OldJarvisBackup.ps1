<#
.SYNOPSIS
Gate 18 (after gate18-incident-02): makes a backup of the everyday JARVIS with ITS OWN backup code
(recovery.py in its folder: "create", then "rehearse" = the Settings buttons "Create verified backup" and
"Test restore in temporary folder"), run with the FINAL package's Python because the everyday JARVIS's own
Python (Codex's runtime) no longer exists. Then copies the new backup with Copy-BackupForGate18-v2.ps1.
Run BY THE OWNER, own account (jonny), non-elevated. Never run by Claude: the everyday JARVIS folder and its
backup folder are owner-only paths.

Writes only new files: <id>.zip and <id>.restore-check.json in the everyday JARVIS's backup folder (beside its
program folder, 'jarvis-backups'), the copy in D:\JARVIS-S6-FRESHVM\media and records in evidence\gate18.
The everyday JARVIS's program and data files are only read (the database through a read-only snapshot).
#>
param(
    [string] $Old = 'C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis',
    [string] $Python = 'D:\JARVIS-release-work\release\JARVIS-1.0.11-60d406fb6398\release\python\python.exe',
    [string] $Dest = 'D:\JARVIS-S6-FRESHVM\media',
    [string] $Evidence = 'D:\JARVIS-S6-FRESHVM\evidence\gate18'
)
$ErrorActionPreference = 'Stop'
function Halt($m) { Write-Host ''; Write-Host "STOPPED: $m"; Write-Host 'Photograph this window for Claude.'; exit 2 }
function Sha256($p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() }
if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { Halt 'this window has administrator rights. Close it and use a normal PowerShell window.' }
$record = Join-Path $Evidence 'old-backup-made.json'
if (Test-Path -LiteralPath $record) { Halt "$record already exists; this step has been run before." }
$recovery = Join-Path $Old 'recovery.py'
foreach ($p in $Python, $recovery, (Join-Path $Old 'data\jarvis.sqlite3')) { if (-not (Test-Path -LiteralPath $p)) { Halt "missing: $p" } }
$running = @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like "$Old\*" -or ($_.CommandLine -like "*$Old*" -and $_.CommandLine -like '*server.py*') })
if ($running.Count) { Halt 'part of the everyday JARVIS is running. Quit it (tray > Quit) and run this again.' }

function RunOld([string[]] $arguments) {
    $ErrorActionPreference = 'Continue'   # Windows PowerShell 5.1 would turn Python's error output into a terminating error
    Push-Location -LiteralPath $Old
    try { $out = & $Python -E -s $recovery @arguments 2>&1 | Out-String } finally { Pop-Location }
    if ($LASTEXITCODE -ne 0) { Halt ("recovery.py {0} failed:`n{1}" -f ($arguments -join ' '), $out.Trim()) }
    try { return ($out | ConvertFrom-Json) } catch { Halt ("recovery.py {0} printed something unexpected:`n{1}" -f ($arguments -join ' '), $out.Trim()) }
}
Write-Host 'Making the backup with the everyday JARVIS''s own backup code (this can take a minute) ...'
$made = RunOld @('create')
if ($made.status -ne 'backup_verified' -or -not $made.id) { Halt "the backup did not report backup_verified (status: $($made.status))." }
Write-Host ("Backup {0}: {1} files, {2:N0} bytes, verified." -f $made.id, $made.files, $made.bytes)
Write-Host 'Testing the restore in a temporary folder ...'
$test = RunOld @('rehearse', '--id', $made.id)
if ($test.status -ne 'restore_rehearsal_passed') { Halt "the test restore did not pass (status: $($test.status))." }
Write-Host 'Test restore passed.'

New-Item -ItemType Directory -Path $Evidence -Force | Out-Null
$out = [ordered]@{
    schema = 'stage6-gate18-old-backup-made-v1'; utc = (Get-Date).ToUniversalTime().ToString('o'); performed_by = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    helper = [ordered]@{ name = Split-Path -Leaf $PSCommandPath; sha256 = (Sha256 $PSCommandPath) }
    everyday_jarvis_folder = $Old; backup_code = [ordered]@{ path = $recovery; sha256 = (Sha256 $recovery) }
    python = [ordered]@{ path = $Python; sha256 = (Sha256 $Python); version = ((& $Python --version) -join '') ; why = 'the everyday JARVIS''s own Python (Codex runtime) no longer exists (gate18-incident-02)' }
    create = [ordered]@{ status = $made.status; id = $made.id; files = $made.files; bytes = $made.bytes; database_counts = $made.database_counts }
    rehearse = [ordered]@{ status = $test.status; files = $test.files; database_counts = $test.database_counts }
}
[IO.File]::WriteAllText($record, (ConvertTo-Json -InputObject $out -Depth 5), (New-Object Text.UTF8Encoding $false))

Write-Host ''
Write-Host 'Copying the new backup for Gate 18 ...'
& (Join-Path $PSScriptRoot 'Copy-BackupForGate18-v2.ps1') -Source (Join-Path (Split-Path -Parent $Old) 'jarvis-backups') -File ($made.id + '.zip') -Dest $Dest -Evidence $Evidence
exit $LASTEXITCODE
