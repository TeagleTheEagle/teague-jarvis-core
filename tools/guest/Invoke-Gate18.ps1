<#
.SYNOPSIS
Gate 18 (backup / restore / recovery) run INSIDE the acceptance machine, after Gates 17 and 19 and only after
the owner's RESUME_STAGE6_RECOVERY. Started by gate18.cmd at the root of the recovery disc.

Restores the owner's verified backup into a SECOND, disposable install with the shipped switch_over.py and
checks: backup identity; a dry run that changes nothing; the import (the shipped tool checks every file hash,
database integrity and the row counts against the backup); startup on the restored data; version identity; a
second launch joining the same Core; clean shutdown; both installs still verify; the first install's data and
the backup file unchanged. The first install (Gate 17) stays stopped throughout.

The backup is personal data. This script writes only counts, hashes, names of the two configuration files and
statuses to the evidence folder, never any content of the backup. Windows PowerShell 5.1 only; the first failure
stops the run (no silent retry).

.PARAMETER Disc       Folder holding the backup zip and BACKUP-RECORD.json (the mounted recovery disc root).
.PARAMETER Evidence   Folder for the records (the VM's single egress folder).
.PARAMETER FirstHome  The install made by Gate 17. VM: default %LOCALAPPDATA%\JARVIS.
.PARAMETER RestoreHome The disposable restore target. VM: default %LOCALAPPDATA%\JARVIS-restore. Must not exist yet.
.PARAMETER Staging    The package extracted by Gate 17 (its installer and Python are used). VM: default %LOCALAPPDATA%\JARVIS-package.
#>
param(
    [string] $Disc = $PSScriptRoot,
    [string] $Evidence = 'Z:\',
    [string] $Share = '\\VBOXSVR\guest-egress-01',
    [string] $FirstHome = (Join-Path $env:LOCALAPPDATA 'JARVIS'),
    [string] $RestoreHome = (Join-Path $env:LOCALAPPDATA 'JARVIS-restore'),
    [string] $Staging = (Join-Path $env:LOCALAPPDATA 'JARVIS-package')
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Evidence)) {
    if ($Evidence -like 'Z:*') { cmd /c "net use Z: $Share /persistent:no >nul 2>&1" }
    if (-not (Test-Path -LiteralPath $Evidence)) { Write-Host "STOPPED: the evidence folder $Evidence cannot be reached. Photograph this window for Claude and wait."; exit 3 }
}
$earlier = @(Get-ChildItem -LiteralPath $Evidence -Directory -Filter 'gate18-*')
if ($earlier) { Write-Host "STOPPED: Gate 18 was already started here ($($earlier[-1].Name)). It is not run again without a decision. Photograph this window for Claude and wait."; exit 2 }
$script:Started = Get-Date
$script:EvidenceDir = Join-Path $Evidence ('gate18-' + $script:Started.ToUniversalTime().ToString('yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $script:EvidenceDir -Force | Out-Null
$script:Summary = New-Object Collections.ArrayList
$Utf8 = New-Object Text.UTF8Encoding $false

function Now { (Get-Date).ToUniversalTime().ToString('o') }
function Record($name, $data) {
    [IO.File]::WriteAllText((Join-Path $script:EvidenceDir "$name.json"), ($data | ConvertTo-Json -Depth 8), $Utf8)
    $script:Summary.Add([ordered]@{ step = $name; status = $data.status; at = (Now) }) | Out-Null
    Write-Host ("{0,-30} {1}" -f $name, $data.status)
}
function Finish($overall) {
    $summary = [ordered]@{ schema = 'jarvis-gate18-run-v1'; overall = $overall; phase = 'Restore'; first_home = $FirstHome; restore_home = $RestoreHome; disc = $Disc
                           started_utc = $script:Started.ToUniversalTime().ToString('o'); finished_utc = (Now); steps = @($script:Summary) }
    [IO.File]::WriteAllText((Join-Path $script:EvidenceDir 'SUMMARY.json'), ($summary | ConvertTo-Json -Depth 6), $Utf8)
    Write-Host "gate18 Restore : $overall  ($script:EvidenceDir)"
}
function Fail($name, $data, $why) { $data.status = 'FAIL'; $data.reason = $why; Record $name $data; Finish 'FAIL'; Write-Host ''; Write-Host 'STOPPED. Photograph this window for Claude and wait.'; exit 2 }
function Sha256($path) { (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower() }
function Processes($installHome) { @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like (Join-Path $installHome 'releases\*') }) }
function Link($installHome) { Get-Content -LiteralPath (Join-Path $installHome 'data\core-connection.json') -Raw | ConvertFrom-Json }
function Session($installHome) {
    $link = Link $installHome
    $null = Invoke-WebRequest -Uri ($link.origin + '/') -Headers @{ 'X-Jarvis-Desktop' = $link.token } -SessionVariable s -UseBasicParsing -TimeoutSec 15
    @{ origin = $link.origin; headers = @{ 'X-Jarvis-Desktop' = $link.token }; session = $s }
}
function Api($installHome, $route, $body) {
    $c = Session $installHome
    if ($null -eq $body) { return Invoke-RestMethod -Uri ($c.origin + $route) -Headers $c.headers -WebSession $c.session -TimeoutSec 60 }
    Invoke-RestMethod -Uri ($c.origin + $route) -Headers $c.headers -WebSession $c.session -Method Post -ContentType 'application/json' -Body ($body | ConvertTo-Json -Compress) -TimeoutSec 600
}
function WaitForCore($installHome, $seconds) {
    $deadline = (Get-Date).AddSeconds($seconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Path -LiteralPath (Join-Path $installHome 'data\core-connection.json')) { try { $null = Session $installHome; return $true } catch {} }
        Start-Sleep -Milliseconds 500
    }
    $false
}
function Launch($installHome) { Start-Process powershell -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $installHome 'JARVIS.ps1') -WindowStyle Hidden }
function StopJarvis($installHome) {
    try { $null = Api $installHome '/api/shutdown' @{} } catch {}
    $deadline = (Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $deadline -and (Test-Path -LiteralPath (Join-Path $installHome 'data\core-connection.json'))) { Start-Sleep -Milliseconds 500 }
    $coreStopped = -not (Test-Path -LiteralPath (Join-Path $installHome 'data\core-connection.json'))
    Start-Sleep -Seconds 5
    $left = Processes $installHome
    $left | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 2
    [ordered]@{ core_stopped_on_request = $coreStopped; shell_processes_ended = $left.Count; processes_now = (Processes $installHome).Count }
}
function Installer($installHome, [string[]] $arguments) {
    # installer.py of the extracted package, run with the package's own Python; never touches shortcuts here.
    $previous = $ErrorActionPreference; $ErrorActionPreference = 'Continue'   # text on stderr must not end the run; it is captured
    $out = & (Join-Path $Staging 'release\python\python.exe') (Join-Path $Staging 'installer.py') @arguments --home $installHome --no-shortcuts 2>&1 | Out-String
    $ErrorActionPreference = $previous
    try { $out | ConvertFrom-Json } catch { @{ status = 'error'; output = $out.Substring(0, [Math]::Min(1500, $out.Length)) } }
}
function SwitchOver([string[]] $arguments) {
    # The shipped switch_over.py, run from the restore target's own release with no JARVIS_* environment, so it
    # finds that install's data and config folders by itself.
    $id = (Get-Content -LiteralPath (Join-Path $RestoreHome 'current.json') -Raw | ConvertFrom-Json).release
    $app = Join-Path $RestoreHome "releases\$id\app"
    $saved = @{}; foreach ($v in @(Get-ChildItem Env: | Where-Object { $_.Name -like 'JARVIS_*' })) { $saved[$v.Name] = $v.Value; Remove-Item -LiteralPath ("Env:" + $v.Name) }
    Push-Location $app
    $previous = $ErrorActionPreference; $ErrorActionPreference = 'Continue'   # a Python error message on stderr is captured, not fatal here
    try { $out = & (Join-Path $RestoreHome "releases\$id\python\python.exe") (Join-Path $app 'switch_over.py') @arguments 2>&1 | Out-String }
    finally { $ErrorActionPreference = $previous; Pop-Location; foreach ($k in $saved.Keys) { Set-Item -LiteralPath ("Env:" + $k) -Value $saved[$k] } }
    try { $out | ConvertFrom-Json } catch { @{ status = 'error'; output = $out.Substring([Math]::Max(0, $out.Length - 1500)) } }
}
function CountsText($counts) { if ($null -eq $counts) { return '' }; (($counts.PSObject.Properties | Sort-Object Name | ForEach-Object { "$($_.Name)=$($_.Value)" }) -join ';') }
function DataState($installHome) {
    $db = Join-Path $installHome 'data\jarvis.sqlite3'
    [ordered]@{ database_sha256 = (Sha256 $db); database_bytes = (Get-Item -LiteralPath $db).Length
                data_files = @(Get-ChildItem -LiteralPath (Join-Path $installHome 'data') -Recurse -File | Where-Object { $_.FullName -notlike '*\logs\*' }).Count }
}

# K0 no administrator rights (owner decision 2026-10-04).
$elevated = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$data = [ordered]@{ status = 'PASS'; account = "$env:USERDOMAIN\$env:USERNAME"; process_elevated = $elevated }
if ($elevated) { Fail 'K0-not-elevated' $data 'this window has administrator rights; close it and start gate18 from a normal window' }
Record 'K0-not-elevated' $data

# K1 backup identity: the file on the disc is the file the owner copied from the backup drive.
$record = Get-Content -LiteralPath (Join-Path $Disc 'BACKUP-RECORD.json') -Raw | ConvertFrom-Json
$zip = Join-Path $Disc $record.file
$t = [Diagnostics.Stopwatch]::StartNew(); $hash = Sha256 $zip
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [IO.Compression.ZipFile]::OpenRead($zip)
try { $names = @($archive.Entries | ForEach-Object { $_.FullName }) } finally { $archive.Dispose() }
$credentialNames = @($names | Where-Object { ($_ -split '/')[-1] -like '.env*' })
$data = [ordered]@{ status = 'PASS'; file = $record.file; bytes = (Get-Item -LiteralPath $zip).Length; sha256 = $hash; recorded_sha256 = $record.sha256; matches_record = ($hash -eq $record.sha256)
                    hash_seconds = [Math]::Round($t.Elapsed.TotalSeconds, 1); entries = $names.Count; has_manifest = ($names -contains 'manifest.json'); has_database = ($names -contains 'data/jarvis.sqlite3')
                    credential_file_entries = $credentialNames.Count }
if (-not $data.matches_record) { Fail 'K1-backup-identity' $data 'the backup on the disc does not match the recorded hash' }
if (-not $data.has_manifest -or -not $data.has_database) { Fail 'K1-backup-identity' $data 'the archive has no manifest or no database snapshot' }
if ($credentialNames) { Fail 'K1-backup-identity' $data 'the archive contains a credential file (.env); no provider keys may enter the VM' }
Record 'K1-backup-identity' $data

# K2 the starting point: the Gate 17 install is present, stopped and verified; its data is fingerprinted.
$first = Installer $FirstHome @('verify'); $firstStatus = Installer $FirstHome @('status')
$data = [ordered]@{ status = 'PASS'; first_install_verify = $first.status; first_install_release = $first.release; first_install_processes = (Processes $FirstHome).Count
                    restore_target_exists = (Test-Path -LiteralPath $RestoreHome); extracted_package = (Test-Path -LiteralPath (Join-Path $Staging 'installer.py')) }
if ($first.status -ne 'verified' -or $data.first_install_processes -or $data.restore_target_exists -or -not $data.extracted_package) { Fail 'K2-starting-point' $data 'the first install is not verified and stopped, the restore target already exists, or the extracted package is missing' }
$firstBefore = DataState $FirstHome; $data.first_install_data = $firstBefore; $data.first_install_current = $firstStatus.current
Record 'K2-starting-point' $data

# K3 the disposable restore target: a second install of the same build, no shortcuts.
$t = [Diagnostics.Stopwatch]::StartNew(); $in = Installer $RestoreHome @('install', '--package', $Staging); $v = Installer $RestoreHome @('verify')
$data = [ordered]@{ status = 'PASS'; install = $in.status; release = $in.release; installer_seconds = $in.seconds; wall_seconds = [Math]::Round($t.Elapsed.TotalSeconds, 1); verify = $v.status; output = $in.output }
if ($in.status -ne 'installed' -or $in.release -ne $first.release -or $v.status -ne 'verified') { Fail 'K3-restore-target' $data 'the restore target did not install and verify as the same build' }
Record 'K3-restore-target' $data

# K4 dry run: verifies the whole backup (hashes, database integrity, counts) and changes nothing.
$dry = SwitchOver @('--archive', $zip)
$data = [ordered]@{ status = 'PASS'; result = $dry.status; backup_verified = $dry.backup_verified; backup_id = $dry.backup_id; files_to_import = $dry.files_to_import
                    database_counts = $dry.database_counts; would_move_aside = $dry.would_move_aside; skipped_protected = @($dry.skipped_protected).Count; personal_config = $dry.personal_config; output = $dry.output }
if ($dry.status -ne 'dry_run_only' -or -not $dry.backup_verified) { Fail 'K4-dry-run' $data 'the dry run did not verify the backup' }
Record 'K4-dry-run' $data

# K5 the import, with the owner's personality and preferences.
$t = [Diagnostics.Stopwatch]::StartNew(); $imp = SwitchOver @('--archive', $zip, '--apply', '--include-personal-config')
$data = [ordered]@{ status = 'PASS'; result = $imp.status; backup_id = $imp.backup_id; files_imported = $imp.files_imported; database_counts = $imp.database_counts
                    counts_equal_backup = ((CountsText $imp.database_counts) -eq (CountsText $dry.database_counts)); previous_data_moved_aside = [bool]$imp.previous_data_moved_to
                    personal_config_written = $imp.personal_config_written; seconds = [Math]::Round($t.Elapsed.TotalSeconds, 1); output = $imp.output }
if ($imp.status -ne 'switch_over_imported' -or $imp.files_imported -ne $dry.files_to_import -or -not $data.counts_equal_backup) { Fail 'K5-import' $data 'the import did not complete with the counts of the backup' }
$data.program_files_after_import = (Installer $RestoreHome @('verify')).status
if ($data.program_files_after_import -ne 'verified') { Fail 'K5-import' $data 'the program files no longer verify after the import' }
Record 'K5-import' $data

# K6 startup on the restored data: identity, restored items visible, a second launch joins the same Core.
$t = [Diagnostics.Stopwatch]::StartNew(); Launch $RestoreHome; $up = WaitForCore $RestoreHome 240
$data = [ordered]@{ status = 'PASS'; core_ready = $up; seconds_to_ready = [Math]::Round($t.Elapsed.TotalSeconds, 1) }
if (-not $up) { Fail 'K6-startup' $data 'the Core did not start on the restored data within 240 s' }
Start-Sleep -Seconds 3
$state = Api $RestoreHome '/api/state'
$owner = Get-Content -LiteralPath (Join-Path $RestoreHome 'data\core-owner.json') -Raw | ConvertFrom-Json; $origin = (Link $RestoreHome).origin
Launch $RestoreHome; Start-Sleep -Seconds 12
$owner2 = Get-Content -LiteralPath (Join-Path $RestoreHome 'data\core-owner.json') -Raw | ConvertFrom-Json
$data.installed_release = $state.updates.installed_release; $data.identity_matches = ($state.updates.installed_release -eq $first.release)
$data.memory_items_visible = @($state.memory).Count; $data.core_pid_before = $owner.pid; $data.core_pid_after = $owner2.pid
$data.second_launch_joined_same_core = ($owner.pid -eq $owner2.pid -and (Link $RestoreHome).origin -eq $origin)
$data.processes = (Processes $RestoreHome).Count; $data.first_install_processes = (Processes $FirstHome).Count
if (-not $data.identity_matches -or -not $data.second_launch_joined_same_core -or $data.first_install_processes) { Fail 'K6-startup' $data 'identity, single-Core or first-install-stopped check failed' }
Record 'K6-startup' $data

# K7 clean shutdown of the restore target.
$stop = StopJarvis $RestoreHome
$data = [ordered]@{ status = 'PASS'; stop = $stop }
if (-not $stop.core_stopped_on_request -or $stop.processes_now) { Fail 'K7-shutdown' $data 'the restore target did not stop cleanly' }
Record 'K7-shutdown' $data

# K8 rollback readiness and separation: both installs verify; the first install's data is untouched.
$v1 = Installer $FirstHome @('verify'); $v2 = Installer $RestoreHome @('verify'); $s1 = Installer $FirstHome @('status'); $s2 = Installer $RestoreHome @('status')
$firstAfter = DataState $FirstHome
$data = [ordered]@{ status = 'PASS'; first_install_verify = $v1.status; restore_target_verify = $v2.status; first_install_current = $s1.current; first_install_releases = $s1.releases; restore_target_current = $s2.current
                    first_install_data_before = $firstBefore; first_install_data_after = $firstAfter
                    first_install_data_unchanged = ($firstAfter.database_sha256 -eq $firstBefore.database_sha256 -and $firstAfter.data_files -eq $firstBefore.data_files) }
if ($v1.status -ne 'verified' -or $v2.status -ne 'verified' -or -not $data.first_install_data_unchanged) { Fail 'K8-separation' $data 'an install no longer verifies or the first install''s data changed' }
Record 'K8-separation' $data

# K9 the backup on the disc is unchanged by everything above.
$hashAfter = Sha256 $zip
$data = [ordered]@{ status = 'PASS'; sha256_after = $hashAfter; unchanged = ($hashAfter -eq $hash) }
if (-not $data.unchanged) { Fail 'K9-backup-unchanged' $data 'the backup file changed' }
Record 'K9-backup-unchanged' $data

Finish 'PASS'
Write-Host ''
Write-Host 'ALL GATE 18 STEPS PASSED.'
Write-Host 'Now shut Windows down: Start > Power > Shut down. Wait until the VM window closes, then tell Claude: gate 18 done'
