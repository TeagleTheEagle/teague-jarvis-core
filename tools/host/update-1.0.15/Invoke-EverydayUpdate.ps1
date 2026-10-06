<#
Copy for release 1.0.15 (tools/host/update-1.0.15/): the 1.0.14 launcher unchanged except the default root folder and the
plan it names. The 1.0.14 original stays as the approval of 2026-10-05 recorded it.
.SYNOPSIS
Updates the owner's everyday JARVIS (the installed release at %LOCALAPPDATA%\JARVIS) to a release that passed its
Stage 7 check: run BY THE OWNER, own account (jonny), non-elevated, one double-click of update-step.cmd per step. It
reads its own records, works out what is next and does only that. Plan: docs/UPDATE-EVERYDAY-1.0.15.md. Never run by
Claude against the real locations.

  check     the package zip against its hash, the installed release and its files, nothing running, free space;
            unpacks the package to <Root>\package (nothing in the installation changes)
  backup    a fresh backup of the everyday JARVIS with its own backup code (the Settings > Backups buttons "Create
            verified backup" and "Test restore"), copied to <Root>\backup with hashes; the program still verifies
  update    the package's own installer updates the installation (copy, verify, switch); data, config, profile
            and shortcuts are not touched; JARVIS is not started
  rollback  only with rollback-approved.json beside the records (written by Claude on the owner's word): switch
            back to the previous release with the same installer

It refuses everything until update-authorized.json exists beside it (written by Claude when the owner has approved
the plan; it names the two builds and the package's hash). A step that fails stops; nothing is repeated without a
decision; a record is never overwritten. For rehearsals every location is a parameter.
#>
param(
    [string] $Root = 'D:\JARVIS-update-1.0.15',
    [string] $InstallHome = (Join-Path $env:LOCALAPPDATA 'JARVIS'),
    [string] $Authorized = '',
    [long] $MinFreeBytes = 4GB,
    [switch] $WhatIf
)
$ErrorActionPreference = 'Stop'
# Set here, not as the parameter default: PowerShell 5.1 can leave $PSScriptRoot empty in a parameter default.
if (-not $Authorized) { $Authorized = Join-Path $PSScriptRoot 'update-authorized.json' }
$evidence = Join-Path $Root 'evidence'; $package = Join-Path $Root 'package'; $backupDir = Join-Path $Root 'backup'
$Utf8 = New-Object Text.UTF8Encoding $false
function Say($t) { Write-Host $t }
function Done($t) { Say ''; Say $t; exit 0 }
function Halt($t) { Say ''; Say "STOPPED: $t"; Say 'Nothing further was done. Photograph this window for Claude.'; exit 2 }
function Sha256($p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() }
function Now { (Get-Date).ToUniversalTime().ToString('o') }
function Has($name) { Test-Path -LiteralPath (Join-Path $evidence $name) }
function Save($name, $data) {
    $path = Join-Path $evidence $name
    if (Test-Path -LiteralPath $path) { Halt "$path already exists; a record is never overwritten." }
    [IO.File]::WriteAllText($path, (ConvertTo-Json -InputObject $data -Depth 8), $Utf8)
}
function JarvisProcesses {
    $root = (Join-Path $InstallHome 'releases') + '\'
    @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith($root, [StringComparison]::OrdinalIgnoreCase) })
}
function Native([string] $exe, [string[]] $arguments, [string] $workdir) {
    # Runs a program, returns its output as text; Python's error output must not become a PowerShell error, and no
    # JARVIS_* setting of this window may point the program somewhere else.
    $saved = @{}; foreach ($v in @(Get-ChildItem Env: | Where-Object { $_.Name -like 'JARVIS_*' })) { $saved[$v.Name] = $v.Value; Remove-Item -LiteralPath ('Env:' + $v.Name) }
    $previous = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    if ($workdir) { Push-Location -LiteralPath $workdir }
    try { $out = & $exe @arguments 2>&1 | Out-String } finally { if ($workdir) { Pop-Location }; $ErrorActionPreference = $previous; foreach ($k in $saved.Keys) { Set-Item -LiteralPath ('Env:' + $k) -Value $saved[$k] } }
    [pscustomobject]@{ exit = $LASTEXITCODE; text = $out.Trim() }
}
function Json($run, $what) {
    try { return ($run.text | ConvertFrom-Json) } catch { Halt ("{0} did not answer as expected (exit {1}):`n{2}" -f $what, $run.exit, $run.text.Substring([Math]::Max(0, $run.text.Length - 1500))) }
}
function PackageDir {
    # The zip holds one top folder (JARVIS-<release id>) with install.cmd, installer.py and release\.
    $inner = @(Get-ChildItem -LiteralPath $package -Directory -ErrorAction SilentlyContinue | Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'installer.py') })
    if ($inner.Count -ne 1) { Halt 'the unpacked package has no installer.py.' }
    $inner[0].FullName
}
# The package's own installer with the package's own Python (never the installed release's: stopping JARVIS ends
# every program of the installation).
function Installer([string[]] $arguments) { $dir = PackageDir; Native (Join-Path $dir 'release\python\python.exe') (@((Join-Path $dir 'installer.py')) + $arguments + @('--home', $InstallHome)) $null }
# The everyday JARVIS's own backup code (recovery.py of the release that is current now), as the Settings buttons
# run it; -B: no bytecode is written into the release, so its files keep verifying.
function Recovery([string] $release, [string[]] $arguments) {
    $app = Join-Path $InstallHome "releases\$release\app"
    Native (Join-Path $InstallHome "releases\$release\python\python.exe") (@('-B', '-E', '-s', (Join-Path $app 'recovery.py')) + $arguments + @('--root', $app, '--data', (Join-Path $InstallHome 'data'))) $app
}
function Current { $f = Join-Path $InstallHome 'current.json'; if (-not (Test-Path -LiteralPath $f)) { return $null }; Get-Content -LiteralPath $f -Raw | ConvertFrom-Json }
function DatabaseHash { $db = Join-Path $InstallHome 'data\jarvis.sqlite3'; if (Test-Path -LiteralPath $db) { Sha256 $db } else { $null } }
function Links { [ordered]@{ desktop = (Test-Path -LiteralPath (Join-Path ([Environment]::GetFolderPath('Desktop')) 'JARVIS.lnk')); startup = (Test-Path -LiteralPath (Join-Path ([Environment]::GetFolderPath('Startup')) 'JARVIS.lnk')) } }
function NotRunning { if ((JarvisProcesses).Count) { Halt 'JARVIS is running. Quit it completely (right-click its icon near the clock > Quit JARVIS completely), then double-click update-step again.' } }

if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { Halt 'this window has administrator rights. Close it and start update-step from a normal File Explorer window.' }
if (-not (Test-Path -LiteralPath $Authorized)) { Halt 'this update has not been approved yet (Claude records your approval of the plan first).' }
$auth = Get-Content -LiteralPath $Authorized -Raw | ConvertFrom-Json
if ($auth.schema -ne 'jarvis-everyday-update-authorized-v1' -or -not $auth.final -or -not $auth.previous -or -not $auth.final_zip -or -not $auth.final_zip_sha256) { Halt 'the approval file does not name the two builds and the package.' }
New-Item -ItemType Directory -Path $evidence -Force | Out-Null

# ---------------------------------------------------------------- 1. check
if (-not (Has 'check.json')) {
    Say "STEP 1 of 3: checks before the update to $($auth.final) (nothing in your JARVIS changes)"
    if ($WhatIf) { Done '(test mode) would run the checks and unpack the package' }
    foreach ($p in $auth.final_zip, (Join-Path $InstallHome 'current.json')) { if (-not (Test-Path -LiteralPath $p)) { Halt "missing: $p" } }
    $current = Current
    if ($current.release -ne $auth.previous) { Halt "your JARVIS is on $($current.release); this update is planned from $($auth.previous). Tell Claude." }
    NotRunning
    $free = (Get-PSDrive -Name ([IO.Path]::GetPathRoot($InstallHome).Substring(0, 1))).Free
    if ($free -lt $MinFreeBytes) { Halt ('only {0:N1} GB free on the install drive; {1:N1} GB are needed.' -f ($free / 1GB), ($MinFreeBytes / 1GB)) }
    if (Test-Path -LiteralPath $package) { Halt "$package already exists from an earlier attempt; tell Claude." }
    Say 'Checking the package against its hash (about a minute) ...'
    $zipHash = Sha256 $auth.final_zip
    if ($zipHash -ne $auth.final_zip_sha256) { Halt "the package hashes $zipHash, not $($auth.final_zip_sha256)." }
    Say "Unpacking the package to $package (a few minutes) ..."
    $t = [Diagnostics.Stopwatch]::StartNew()
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::ExtractToDirectory($auth.final_zip, $package)
    $unpack = [Math]::Round($t.Elapsed.TotalSeconds, 1)
    $manifest = Get-Content -LiteralPath (Join-Path (PackageDir) 'release\manifest.json') -Raw | ConvertFrom-Json
    if ($manifest.release_id -ne $auth.final) { Halt "the unpacked package is $($manifest.release_id), not $($auth.final)." }
    Say 'Checking every file of your installed JARVIS (a minute or two) ...'
    $v = Json (Installer @('verify')) 'The verification'
    if ($v.status -ne 'verified' -or $v.release -ne $auth.previous) { Halt "your installed JARVIS does not verify ($($v.status) $($v.reason)). Tell Claude." }
    Save 'check.json' ([ordered]@{ schema = 'jarvis-everyday-update-check-v1'; utc = (Now); performed_by = [Security.Principal.WindowsIdentity]::GetCurrent().Name; elevated = $false
        script = [ordered]@{ name = (Split-Path -Leaf $PSCommandPath); sha256 = (Sha256 $PSCommandPath) }
        final = $auth.final; previous = $auth.previous; zip = $auth.final_zip; zip_sha256 = $zipHash; unpack_seconds = $unpack; package = (PackageDir)
        install_home = $InstallHome; current = $current; installed_verified = $v.status; free_bytes = $free; jarvis_processes = 0; shortcuts = (Links) })
    Done 'STEP 1 PASSED. Tell Claude "step 1 done". Then double-click update-step again for step 2 (the backup).'
}

# ---------------------------------------------------------------- 2. backup
if (-not (Has 'backup.json')) {
    Say 'STEP 2 of 3: a fresh backup of your JARVIS (the same as Settings > Backups: create, then test restore)'
    if ($WhatIf) { Done '(test mode) would make and test the backup' }
    NotRunning
    $current = Current
    if ($current.release -ne $auth.previous) { Halt "your JARVIS is on $($current.release), not $($auth.previous) as at step 1. Tell Claude." }
    Say 'Making the backup (about a minute) ...'
    $made = Json (Recovery $auth.previous @('create')) 'The backup'
    if ($made.status -ne 'backup_verified' -or -not $made.id) { Halt "the backup did not report backup_verified ($($made.status) $($made.reason))." }
    Say ("Backup {0}: {1} files, verified. Testing the restore in a temporary folder ..." -f $made.id, $made.files)
    $test = Json (Recovery $auth.previous @('rehearse', '--id', $made.id)) 'The test restore'
    if ($test.status -ne 'restore_rehearsal_passed') { Halt "the test restore did not pass ($($test.status) $($test.reason))." }
    $folder = Join-Path $InstallHome 'data-backups'
    $zip = Join-Path $folder ($made.id + '.zip'); $receipt = Join-Path $folder ($made.id + '.restore-check.json')
    foreach ($p in $zip, $receipt) { if (-not (Test-Path -LiteralPath $p)) { Halt "the backup file $p is missing." } }
    if (Test-Path -LiteralPath $backupDir) { Halt "$backupDir already exists; tell Claude." }
    New-Item -ItemType Directory -Path $backupDir | Out-Null
    $zipHash = Sha256 $zip
    Copy-Item -LiteralPath $zip, $receipt -Destination $backupDir
    $copyHash = Sha256 (Join-Path $backupDir ($made.id + '.zip'))
    if ($copyHash -ne $zipHash) { Halt 'the copy of the backup does not match the backup.' }
    $v = Json (Installer @('verify')) 'The verification'
    if ($v.status -ne 'verified' -or $v.release -ne $auth.previous) { Halt 'your installed JARVIS no longer verifies after the backup. Tell Claude.' }
    Save 'backup.json' ([ordered]@{ schema = 'jarvis-everyday-update-backup-v1'; utc = (Now); release_used = $auth.previous
        create = [ordered]@{ status = $made.status; id = $made.id; files = $made.files; bytes = $made.bytes; database_counts = $made.database_counts }
        rehearse = [ordered]@{ status = $test.status; files = $test.files; database_counts = $test.database_counts }
        backup = $zip; backup_sha256 = $zipHash; copy = (Join-Path $backupDir ($made.id + '.zip')); copy_sha256 = $copyHash
        installed_still_verified = $v.status; database_sha256_after_backup = (DatabaseHash) })
    Done ('STEP 2 PASSED: backup {0} made and test-restored; a copy is in {1}. Tell Claude "step 2 done", then double-click update-step again for step 3 (the update).' -f $made.id, $backupDir)
}

# ---------------------------------------------------------------- 3. update
if (-not (Has 'update.json')) {
    Say "STEP 3 of 3: update your JARVIS from $($auth.previous) to $($auth.final)"
    if ($WhatIf) { Done '(test mode) would update' }
    NotRunning
    $current = Current
    if ($current.release -ne $auth.previous) { Halt "your JARVIS is on $($current.release), not $($auth.previous) as at step 1. Tell Claude." }
    $dbBefore = DatabaseHash; $linksBefore = Links
    Say 'Updating (a few minutes; your data, settings and keys are not touched) ...'
    $t = [Diagnostics.Stopwatch]::StartNew()
    $in = Json (Installer @('install', '--package', (PackageDir), '--no-shortcuts')) 'The installer'
    $seconds = [Math]::Round($t.Elapsed.TotalSeconds, 1)
    if ($in.status -ne 'installed' -or $in.release -ne $auth.final -or $in.previous -ne $auth.previous) { Halt "the installer answered '$($in.status)' $($in.reason)" }
    $v = Json (Installer @('verify')) 'The verification'
    if ($v.status -ne 'verified' -or $v.release -ne $auth.final) { Halt 'the updated JARVIS does not verify. Tell Claude (the previous release is still installed beside it).' }
    $dbAfter = DatabaseHash
    Save 'update.json' ([ordered]@{ schema = 'jarvis-everyday-update-v1'; utc = (Now); installer = $in; wall_seconds = $seconds; verify = $v.status; current = (Current)
        database_sha256_before = $dbBefore; database_sha256_after = $dbAfter; database_unchanged = ($dbBefore -eq $dbAfter)
        shortcuts_before = $linksBefore; shortcuts_after = (Links); jarvis_started = $false })
    Done "STEP 3 PASSED: your JARVIS is now $($auth.final), every file verified. It was not started. Tell Claude ""step 3 done""; Claude gives you the short check to do when you start it."
}

# ---------------------------------------------------------------- rollback (only on the owner's word)
if ((Has 'rollback-approved.json') -and -not (Has 'rollback.json')) {
    Say "ROLLBACK: switch your JARVIS back to $($auth.previous)"
    if ($WhatIf) { Done '(test mode) would roll back' }
    NotRunning
    $back = Json (Installer @('rollback')) 'The rollback'
    if ($back.status -ne 'rolled_back' -or $back.release -ne $auth.previous) { Halt "the rollback answered '$($back.status)' $($back.reason)" }
    $v = Json (Installer @('verify')) 'The verification'
    if ($v.status -ne 'verified' -or $v.release -ne $auth.previous) { Halt 'the previous release does not verify after the rollback. Tell Claude.' }
    Save 'rollback.json' ([ordered]@{ schema = 'jarvis-everyday-update-rollback-v1'; utc = (Now); result = $back; verify = $v.status; current = (Current) })
    Done "ROLLBACK PASSED: your JARVIS is back on $($auth.previous). Tell Claude ""rollback done""."
}
Done "The update to $($auth.final) is complete and recorded. Nothing more to do here."
