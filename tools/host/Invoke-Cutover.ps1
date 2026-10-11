<#
.SYNOPSIS
The switch-over (cutover) of the everyday JARVIS to the installed FINAL build: run BY THE OWNER, own account
(jonny), non-elevated, one double-click of cutover-step.cmd per step. It reads its own records, works out what
is next and does only that. Plan: docs/CUTOVER-BLUEPRINT.md. Never run by Claude against the real locations.

  check    the FINAL zip, free space, nothing installed or running yet, the verified backup and its hash
  install  unpack the zip, install with the package's own installer (same command as install.cmd), verify
  dryrun   copy the backup to the cutover folder, let the new install verify it and list what would come across
           (changes nothing); then it waits for import-approved.json (written by Claude on the owner's OK)
  import   import the data, personality and preferences; counts checked against the backup; verify
  retire   only with retire-approved.json: move the OLD shortcuts into old-shortcuts\ (nothing is deleted)

It refuses everything until cutover-authorized.json exists beside it (written by Claude when the owner has
approved the plan). The old JARVIS folder and its backup folder are only read. A step that fails stops; nothing
is repeated without a decision. For rehearsals every location is a parameter and -NoShortcuts skips shortcuts.
#>
param(
    [string] $Root = 'D:\JARVIS-cutover',
    [string] $Zip = 'D:\JARVIS-release-work\release\JARVIS-1.0.11-60d406fb6398.zip',
    [string] $ZipSha256 = '1923651176dd3095e84b0628a5c7a90608b6db57fe06986670e0ea8246225a58',
    [string] $ReleaseId = '1.0.11-60d406fb6398',
    [string] $InstallHome = (Join-Path $env:LOCALAPPDATA 'JARVIS'),
    [string] $Old = 'C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis',
    [string] $Backup = 'C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis-backups\bcc2753f736f43ba946ec3f342b35c3a.zip',
    [string] $BackupSha256 = 'b81be404e1677c48cffc7d26a8d77998b54fa2fa588bd4eeb5614e841ce0bfe3',
    [string] $Authorized = (Join-Path $PSScriptRoot 'cutover-authorized.json'),
    [string] $DesktopDir = [Environment]::GetFolderPath('Desktop'),
    [string] $StartupDir = [Environment]::GetFolderPath('Startup'),
    [long] $MinFreeBytes = 4GB,
    [switch] $NoShortcuts,
    [switch] $WhatIf
)
$ErrorActionPreference = 'Stop'
$evidence = Join-Path $Root 'evidence'; $package = Join-Path $Root 'package'; $backupCopy = Join-Path (Join-Path $Root 'backup') (Split-Path -Leaf $Backup)
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
    $roots = @(($Old.TrimEnd('\') + '\'), ((Join-Path $InstallHome 'releases') + '\'))
    @(Get-CimInstance Win32_Process | Where-Object { $p = $_; $p.ExecutablePath -and @($roots | Where-Object { $p.ExecutablePath.StartsWith($_, [StringComparison]::OrdinalIgnoreCase) }).Count })
}
function Native([string] $exe, [string[]] $arguments, [string] $workdir) {
    # Runs a program, returns its output as text; Python's error output must not become a PowerShell error.
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
    if (Test-Path -LiteralPath (Join-Path $package 'installer.py')) { return $package }
    $inner = @(Get-ChildItem -LiteralPath $package -Directory | Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'installer.py') })
    if ($inner.Count -ne 1) { Halt 'the unpacked package has no installer.py.' }
    $inner[0].FullName
}
function Installer([string[]] $arguments) { $dir = PackageDir; Native (Join-Path $dir 'release\python\python.exe') (@((Join-Path $dir 'installer.py')) + $arguments + @('--home', $InstallHome)) $null }
function SwitchOver([string[]] $arguments) {
    $app = Join-Path $InstallHome "releases\$ReleaseId\app"
    Native (Join-Path $InstallHome "releases\$ReleaseId\python\python.exe") (@((Join-Path $app 'switch_over.py')) + $arguments) $app
}
function CountsText($c) { if ($null -eq $c) { return '' }; (($c.PSObject.Properties | Sort-Object Name | ForEach-Object { "$($_.Name)=$($_.Value)" }) -join ';') }

if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { Halt 'this window has administrator rights. Close it and start cutover-step from a normal File Explorer window.' }
if (-not (Test-Path -LiteralPath $Authorized)) { Halt 'the switch-over has not been approved yet (Claude records your approval of the plan first).' }
New-Item -ItemType Directory -Path $evidence -Force | Out-Null

# ---------------------------------------------------------------- 1. check
if (-not (Has 'check.json')) {
    Say 'STEP 1 of 5: checks before anything is installed'
    if ($WhatIf) { Done '(test mode) would run the checks' }
    foreach ($p in $Zip, $Backup, (Join-Path $Old 'data\jarvis.sqlite3')) { if (-not (Test-Path -LiteralPath $p)) { Halt "missing: $p" } }
    if (Test-Path -LiteralPath $InstallHome) { Halt "$InstallHome already exists. The switch-over installs into an empty place; tell Claude." }
    if (Test-Path -LiteralPath $package) { Halt "$package already exists from an earlier attempt; tell Claude." }
    $running = JarvisProcesses
    if ($running.Count) { Halt 'a JARVIS is running. Quit it completely (tray icon > Quit) and start this step again.' }
    $free = (Get-PSDrive -Name ([IO.Path]::GetPathRoot($InstallHome).Substring(0, 1))).Free
    if ($free -lt $MinFreeBytes) { Halt ('only {0:N1} GB free on the install drive; {1:N1} GB are needed.' -f ($free / 1GB), ($MinFreeBytes / 1GB)) }
    Say 'Checking the FINAL package against its hash (about a minute) ...'
    $zipHash = Sha256 $Zip
    if ($zipHash -ne $ZipSha256) { Halt "the package hashes $zipHash, not the FINAL hash $ZipSha256." }
    Say 'Checking the backup against the hash proven at Gate 18 ...'
    $backupHash = Sha256 $Backup
    if ($backupHash -ne $BackupSha256) { Halt "the backup hashes $backupHash, not $BackupSha256." }
    $receiptPath = [IO.Path]::ChangeExtension($Backup, $null).TrimEnd('.') + '.restore-check.json'
    if (-not (Test-Path -LiteralPath $receiptPath)) { Halt "the backup has no Test restore receipt ($receiptPath)." }
    $receipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
    if ($receipt.status -ne 'restore_rehearsal_passed') { Halt 'the Test restore receipt does not say restore_rehearsal_passed.' }
    # Reference time: the Test restore receipt, written after the backup run had finished and closed the database.
    $backupTime = (Get-Item -LiteralPath $receiptPath).LastWriteTimeUtc
    $newer =@(Get-ChildItem -LiteralPath (Join-Path $Old 'data') -File -Filter 'jarvis.sqlite3*' | Where-Object { $_.LastWriteTimeUtc -gt $backupTime })
    if ($newer.Count) { Halt ('the old JARVIS database changed after the backup was made ({0}). A fresh backup is needed first; tell Claude.' -f (($newer | ForEach-Object { $_.Name }) -join ', ')) }
    Save 'check.json' ([ordered]@{ schema = 'jarvis-cutover-check-v1'; utc = (Now); performed_by = [Security.Principal.WindowsIdentity]::GetCurrent().Name; elevated = $false
        script = [ordered]@{ name = (Split-Path -Leaf $PSCommandPath); sha256 = (Sha256 $PSCommandPath) }
        zip = $Zip; zip_sha256 = $zipHash; release_id = $ReleaseId; install_home = $InstallHome; install_home_existed = $false; free_bytes = $free
        backup = $Backup; backup_sha256 = $backupHash; backup_bytes = (Get-Item -LiteralPath $Backup).Length; backup_written_utc = $backupTime.ToString('o'); restore_check = $receipt.status
        old_database_not_newer_than_backup = $true; jarvis_processes = 0; shortcuts = (-not $NoShortcuts) })
    Done 'STEP 1 PASSED. Tell Claude "step 1 done". Then double-click cutover-step again for step 2 (install).'
}

# ---------------------------------------------------------------- 2. install
if (-not (Has 'install.json')) {
    Say 'STEP 2 of 5: install the new JARVIS (the old one is not touched)'
    if ($WhatIf) { Done '(test mode) would unpack and install' }
    if ((Test-Path -LiteralPath $InstallHome) -or (Test-Path -LiteralPath $package)) { Halt 'an earlier install attempt left files behind; tell Claude.' }
    if ((JarvisProcesses).Count) { Halt 'a JARVIS is running. Quit it completely and start this step again.' }
    Say "Unpacking the package to $package (a few minutes) ..."
    $t = [Diagnostics.Stopwatch]::StartNew()
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::ExtractToDirectory($Zip, $package)
    $unpack = [Math]::Round($t.Elapsed.TotalSeconds, 1)
    $packageDir = PackageDir
    Say 'Installing (a few minutes) ...'
    $t.Restart()
    $arguments = @('install', '--package', $packageDir); if ($NoShortcuts) { $arguments += '--no-shortcuts' }
    $in = Json (Installer $arguments) 'The installer'
    $seconds = [Math]::Round($t.Elapsed.TotalSeconds, 1)
    if ($in.status -ne 'installed' -or $in.release -ne $ReleaseId) { Halt "the installer answered '$($in.status)' $($in.reason)" }
    $v = Json (Installer @('verify')) 'The verification'
    if ($v.status -ne 'verified') { Halt 'the installed files do not verify.' }
    $links = [ordered]@{ desktop = (Test-Path -LiteralPath (Join-Path $DesktopDir 'JARVIS.lnk')); startup = (Test-Path -LiteralPath (Join-Path $StartupDir 'JARVIS.lnk')) }
    if (-not $NoShortcuts -and -not ($links.desktop -and $links.startup)) { Halt 'the new JARVIS shortcuts were not created.' }
    Save 'install.json' ([ordered]@{ schema = 'jarvis-cutover-install-v1'; utc = (Now); unpack_seconds = $unpack; install_seconds = $seconds; installer = $in; verify = $v.status
        install_home = $InstallHome; shortcuts_requested = (-not $NoShortcuts); new_shortcuts = $links; old_shortcuts_untouched = $true })
    Done 'STEP 2 PASSED: the new JARVIS is installed and verified, not started. Do NOT start it yet. Tell Claude "step 2 done", then double-click cutover-step again for step 3 (the dry run).'
}

# ---------------------------------------------------------------- 3. dry run
if (-not (Has 'dryrun.json')) {
    Say 'STEP 3 of 5: dry run of the import (changes nothing in the new JARVIS)'
    if ($WhatIf) { Done '(test mode) would copy the backup and run the dry run' }
    if (Test-Path -LiteralPath $backupCopy) { Halt "$backupCopy already exists; tell Claude." }
    New-Item -ItemType Directory -Path (Split-Path -Parent $backupCopy) -Force | Out-Null
    $before = Sha256 $Backup; Copy-Item -LiteralPath $Backup -Destination $backupCopy; $copyHash = Sha256 $backupCopy; $after = Sha256 $Backup
    if ($before -ne $BackupSha256 -or $copyHash -ne $before -or $after -ne $before) { Halt 'the backup copy does not match the backup.' }
    $dry = Json (SwitchOver @('--archive', $backupCopy)) 'The dry run'
    if ($dry.status -ne 'dry_run_only' -or -not $dry.backup_verified) { Halt "the dry run did not verify the backup: $($dry.status) $($dry.reason)" }
    Save 'dryrun.json' ([ordered]@{ schema = 'jarvis-cutover-dryrun-v1'; utc = (Now); backup_copy = $backupCopy; backup_copy_sha256 = $copyHash; source_sha256_before = $before; source_sha256_after = $after
        result = $dry.status; backup_id = $dry.backup_id; files_to_import = $dry.files_to_import; database_counts = $dry.database_counts
        would_move_aside = $dry.would_move_aside; skipped_protected = @($dry.skipped_protected).Count; personal_config = $dry.personal_config })
    Say ''; Say ("The backup is good: {0} data files would be imported." -f $dry.files_to_import)
    Done 'STEP 3 PASSED. Tell Claude "step 3 done". Claude reads the list and reports it to you; the import (step 4) starts only after your OK.'
}

# ---------------------------------------------------------------- 4. import
if (-not (Has 'import.json')) {
    if (-not (Has 'import-approved.json')) { Done 'Waiting: Claude has not recorded your OK for the import yet. Tell Claude "step 3 done" and answer its question.' }
    Say 'STEP 4 of 5: import your data, personality and preferences into the new JARVIS'
    if ($WhatIf) { Done '(test mode) would import' }
    if ((JarvisProcesses).Count) { Halt 'a JARVIS is running. Quit it completely and start this step again.' }
    $dryRecord = Get-Content -LiteralPath (Join-Path $evidence 'dryrun.json') -Raw | ConvertFrom-Json
    if ((Sha256 $backupCopy) -ne $BackupSha256) { Halt 'the backup copy changed since the dry run.' }
    $t = [Diagnostics.Stopwatch]::StartNew()
    $imp = Json (SwitchOver @('--archive', $backupCopy, '--apply', '--include-personal-config')) 'The import'
    $seconds = [Math]::Round($t.Elapsed.TotalSeconds, 1)
    $equal = (CountsText $imp.database_counts) -eq (CountsText $dryRecord.database_counts)
    if ($imp.status -ne 'switch_over_imported' -or $imp.files_imported -ne $dryRecord.files_to_import -or -not $equal) { Halt "the import did not complete with the counts of the backup: $($imp.status) $($imp.reason)" }
    $v = Json (Installer @('verify')) 'The verification'
    if ($v.status -ne 'verified') { Halt 'the program files no longer verify after the import.' }
    Save 'import.json' ([ordered]@{ schema = 'jarvis-cutover-import-v1'; utc = (Now); seconds = $seconds; result = $imp.status; backup_id = $imp.backup_id; files_imported = $imp.files_imported
        database_counts = $imp.database_counts; counts_equal_backup = $equal; previous_data_moved_aside = $imp.previous_data_moved_aside; personal_config_written = $imp.personal_config_written
        program_files_after_import = $v.status; backup_copy_sha256_after = (Sha256 $backupCopy) })
    Done 'STEP 4 PASSED: your data is in the new JARVIS. Tell Claude "step 4 done". Next (with Claude): your AI keys, then start the new JARVIS from its Desktop icon and check it.'
}

# ---------------------------------------------------------------- 5. retire the old shortcuts
if (-not (Has 'retire.json')) {
    if (-not (Has 'retire-approved.json')) { Done 'The new JARVIS is installed and has your data. The old shortcuts are still in place. They are moved away only after you have checked the new JARVIS and told Claude to make the switch.' }
    Say 'STEP 5 of 5: move the OLD JARVIS shortcuts away (nothing is deleted)'
    if ($WhatIf) { Done '(test mode) would move the old shortcuts' }
    $moved = New-Object Collections.ArrayList
    foreach ($entry in @(@($DesktopDir, 'JARVIS Desktop.lnk', 'desktop'), @($DesktopDir, 'JARVIS INDUSTRIES.lnk', 'desktop'), @($StartupDir, 'JARVIS Desktop.lnk', 'startup'))) {
        $source = Join-Path $entry[0] $entry[1]
        if (-not (Test-Path -LiteralPath $source)) { continue }
        $target = (New-Object -ComObject WScript.Shell).CreateShortcut($source)
        if ("$($target.Arguments) $($target.TargetPath)" -notlike "*$Old*") { Halt "$source does not point at the old JARVIS; it is not moved. Tell Claude." }
        $folder = Join-Path (Join-Path $Root 'old-shortcuts') $entry[2]; New-Item -ItemType Directory -Path $folder -Force | Out-Null
        $destination = Join-Path $folder $entry[1]
        if (Test-Path -LiteralPath $destination) { Halt "$destination already exists." }
        $hash = Sha256 $source; Move-Item -LiteralPath $source -Destination $destination
        $moved.Add([ordered]@{ from = $source; to = $destination; sha256 = $hash }) | Out-Null
    }
    Save 'retire.json' ([ordered]@{ schema = 'jarvis-cutover-retire-v1'; utc = (Now); moved = @($moved); new_shortcuts = [ordered]@{ desktop = (Test-Path -LiteralPath (Join-Path $DesktopDir 'JARVIS.lnk')); startup = (Test-Path -LiteralPath (Join-Path $StartupDir 'JARVIS.lnk')) }
        undo = 'move each file back from "to" to "from"' })
    Done ('STEP 5 PASSED: {0} old shortcut(s) moved to {1}. Only the new JARVIS starts when you sign in. Tell Claude "step 5 done".' -f $moved.Count, (Join-Path $Root 'old-shortcuts'))
}
Done 'The switch-over is complete and recorded. Nothing more to do here.'
