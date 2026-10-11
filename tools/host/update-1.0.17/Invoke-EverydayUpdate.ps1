<#
Invoke-EverydayUpdate.ps1, version 2 (release 1.0.17, "JARVIS as his own app"; docs/UPDATE-EVERYDAY-1.0.17.md)

Updates the owner's everyday JARVIS (the installed release at %LOCALAPPDATA%\JARVIS) to a release that passed its
Stage 7 check: run BY THE OWNER, own account (jonny), non-elevated, one double-click of update-step.cmd per step. It
does nothing until Claude has recorded the owner's approval (update-authorized.json beside this script, schema
jarvis-everyday-update-authorized-v2: the two builds, the package zip and the Setup with their hashes).

Version 2 differs from the 1.0.14 to 1.0.16 launcher in step 3 only: the update is made by the release's own
JARVIS-Setup-<id>.exe (the file the owner will use for every later update), run silently with the owner's defaults
exactly as the Stage 7 check ran it, so the Setup writes the Desktop and Startup shortcuts straight at the new
JARVIS.exe, registers "JARVIS <version>, Teague Industries" in Settings > Apps, and leaves its package and uninstaller
in %LOCALAPPDATA%\JARVIS-package. Step 1 renames a leftover JARVIS-package folder aside first: the Setup would delete
its release folder and the records rule says nothing is deleted, and the Setup's own answer must be the only one in
that folder. The zip is still unpacked for the installer's own verify and rollback commands, with the package's own
Python (never the installed release's).

  check     the zip and the Setup against their hashes, the installed release and its files, nothing running, free
            space, no Settings > Apps entry yet; a leftover staging folder renamed aside; the package unpacked
  backup    a fresh backup of the everyday JARVIS with its own backup code (as Settings > Backups: "Create verified
            backup" then "Test restore"), copied to <Root>\backup with hashes; the program still verifies
  update    the Setup, silently; its own answer (setup-result.json) checked, every file verified, the entry, the
            shortcuts' targets, no JARVIS.ps1, the database byte-for-byte unchanged (a change stops the step);
            JARVIS is not started
  rollback  only with rollback-approved.json beside the records (the owner's word, recorded by Claude): the package
            installer switches back to the previous release (its shortcuts and launcher script follow); the
            Settings > Apps entry keeps saying the new version until the next update (said in the plan)

A step that fails stops and says what state the installation is in; nothing is repeated without a decision; a record
is never overwritten. For rehearsals every location is a parameter and -SetupSwitches carries the Setup's sandbox
switches ("/DIR=...;/HOME=...;/NOSHORTCUTS", one string, semicolons between: PowerShell's -File cannot pass a list).
The home and the package folder must agree with those switches, and a real run (no switch) uses the default folders
only: a rehearsal can never reach the owner's installation through a default (review finding 1, 2026-10-07).
#>
param(
    [string] $Root = 'D:\JARVIS-update-1.0.17',
    [string] $InstallHome = (Join-Path $env:LOCALAPPDATA 'JARVIS'),
    [string] $Staging = (Join-Path $env:LOCALAPPDATA 'JARVIS-package'),
    [string] $SetupSwitches = '',
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
function Full($p) { [IO.Path]::GetFullPath([string]$p).TrimEnd('\') }
$switches = @($SetupSwitches -split ';' | Where-Object { $_ })
$homeSwitch = @($switches | Where-Object { $_ -like '/HOME=*' } | ForEach-Object { $_.Substring(6).Trim('"') })
$dirSwitch = @($switches | Where-Object { $_ -like '/DIR=*' } | ForEach-Object { $_.Substring(5).Trim('"') })
$sandbox = [bool]$homeSwitch.Count
if ($dirSwitch.Count) { $Staging = $dirSwitch[0] }
$Staging = $Staging.TrimEnd('\')
$defaultHome = Join-Path $env:LOCALAPPDATA 'JARVIS'; $defaultStaging = Join-Path $env:LOCALAPPDATA 'JARVIS-package'
if ($sandbox) {
    if (-not $dirSwitch.Count -or (Full $homeSwitch[0]) -ne (Full $InstallHome) -or (Full $dirSwitch[0]) -ne (Full $Staging)) { Halt 'a rehearsal must name the same sandbox home and package folder in -InstallHome, -Staging and the Setup switches (/HOME, /DIR).' }
    if ((Full $InstallHome) -eq (Full $defaultHome) -or (Full $Staging) -eq (Full $defaultStaging)) { Halt 'a rehearsal may not use the real install folders.' }
} elseif ($switches.Count -or (Full $InstallHome) -ne (Full $defaultHome) -or (Full $Staging) -ne (Full $defaultStaging)) {
    Halt 'the real update takes no Setup switch and uses the default folders only; a rehearsal names its sandbox in every parameter.'
}
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
function LinkTarget($p) {
    if (-not (Test-Path -LiteralPath $p)) { return $null }
    try { (New-Object -ComObject WScript.Shell).CreateShortcut($p).TargetPath } catch { 'unreadable: ' + $_.Exception.Message }
}
# The owner's real Desktop and Startup shortcuts: present or not, and where each points (read only; the Setup writes them).
function Links { [ordered]@{ desktop = (LinkTarget (Join-Path ([Environment]::GetFolderPath('Desktop')) 'JARVIS.lnk')); startup = (LinkTarget (Join-Path ([Environment]::GetFolderPath('Startup')) 'JARVIS.lnk')) } }
function Entry($appId) {
    $key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\' + $appId + '_is1'
    if (Test-Path -LiteralPath $key) { $e = Get-ItemProperty -LiteralPath $key; [ordered]@{ present = $true; name = $e.DisplayName; version = $e.DisplayVersion; publisher = $e.Publisher; uninstall = $e.UninstallString; location = $e.InstallLocation } } else { [ordered]@{ present = $false } }
}
function StateNow {
    # What the installation is in, read now, for a message after a failure (review finding 2).
    $c = Current; $links = Links
    'Your JARVIS is on ' + $(if ($c) { $c.release } else { 'nothing (no current.json)' }) + '; the old launcher script JARVIS.ps1 is ' + $(if (Test-Path -LiteralPath (Join-Path $InstallHome 'JARVIS.ps1')) { 'present' } else { 'gone' }) + '; the Desktop shortcut points at ' + $(if ($links.desktop) { $links.desktop } else { 'nothing (absent)' }) + '; the Startup shortcut at ' + $(if ($links.startup) { $links.startup } else { 'nothing (absent)' }) + '.'
}
function NotRunning { if ((JarvisProcesses).Count) { Halt 'JARVIS is running. Quit it completely (right-click its icon near the clock > Quit JARVIS completely), then double-click update-step again.' } }
function FreeBytes { (Get-PSDrive -Name ([IO.Path]::GetPathRoot($InstallHome).Substring(0, 1))).Free }

if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { Halt 'this window has administrator rights. Close it and start update-step from a normal File Explorer window.' }
if (-not (Test-Path -LiteralPath $Authorized)) { Halt 'this update has not been approved yet (no update-authorized.json beside this script).' }
$auth = Get-Content -LiteralPath $Authorized -Raw | ConvertFrom-Json
if ($auth.schema -ne 'jarvis-everyday-update-authorized-v2' -or -not $auth.final -or -not $auth.previous -or -not $auth.final_zip -or -not $auth.final_zip_sha256 -or -not $auth.final_setup -or -not $auth.final_setup_sha256) { Halt 'the approval file does not name the two builds, the package and the Setup (version 2 approval).' }
$setupRecordFile = $auth.final_setup -replace '\.exe$', '.setup.json'
if (-not (Test-Path -LiteralPath $setupRecordFile)) { Halt "the Setup's record is missing: $setupRecordFile" }
$setupRecord = Get-Content -LiteralPath $setupRecordFile -Raw | ConvertFrom-Json
$appId = $(if ($sandbox) { $setupRecord.sandbox_app_id } else { $setupRecord.app_id })
if (-not $appId) { Halt "the Setup's record names no application id for this run." }
New-Item -ItemType Directory -Path $evidence -Force | Out-Null

# ---------------------------------------------------------------- 1. check
if (-not (Has 'check.json')) {
    Say "STEP 1 of 3: checks before the update to $($auth.final) (nothing in your JARVIS changes)"
    if ($WhatIf) { Done '(test mode) would run the checks and unpack the package' }
    foreach ($p in $auth.final_zip, $auth.final_setup, (Join-Path $InstallHome 'current.json')) { if (-not (Test-Path -LiteralPath $p)) { Halt "missing: $p" } }
    $current = Current
    if ($current.release -ne $auth.previous) { Halt "your JARVIS is on $($current.release); this update is planned from $($auth.previous). Tell Claude." }
    NotRunning
    $free = FreeBytes
    if ($free -lt $MinFreeBytes) { Halt ('only {0:N1} GB free on the install drive; {1:N1} GB are needed.' -f ($free / 1GB), ($MinFreeBytes / 1GB)) }
    if (Test-Path -LiteralPath $package) { Halt "$package already exists from an earlier attempt; tell Claude." }
    $entryBefore = Entry $appId
    if ($entryBefore.present) { Halt "Settings > Apps already lists JARVIS ($($entryBefore.name) $($entryBefore.version)); this is the first update through a Setup and expects none. Tell Claude." }
    Say 'Checking the package and the Setup against their hashes (a minute or two) ...'
    $zipHash = Sha256 $auth.final_zip
    if ($zipHash -ne $auth.final_zip_sha256) { Halt "the package zip does not match its approved hash ($zipHash)." }
    $setupHash = Sha256 $auth.final_setup
    if ($setupHash -ne $auth.final_setup_sha256) { Halt "the Setup does not match its approved hash ($setupHash)." }
    if ($setupRecord.setup_sha256 -ne $setupHash -or $setupRecord.release_id -ne $auth.final) { Halt "the Setup's record does not describe this Setup." }
    # A leftover staging folder (the switch-over's copy of an old package): the Setup would delete its release folder
    # and installer before unpacking, and the records rule says nothing is deleted; the Setup's own answer must also
    # be the only setup-result.json there. Renamed aside; the owner may remove it later.
    $aside = $null
    if (Test-Path -LiteralPath $Staging) {
        $aside = $Staging + '-before-' + $auth.final
        if (Test-Path -LiteralPath $aside) { Halt "$aside exists already; tell Claude." }
        try { Move-Item -LiteralPath $Staging -Destination $aside } catch { Halt "the leftover folder $Staging could not be renamed aside ($($_.Exception.Message)). Close any window showing it and double-click update-step again." }
        if ((Test-Path -LiteralPath $Staging) -or -not (Test-Path -LiteralPath $aside)) { Halt 'the leftover staging folder could not be moved aside. Tell Claude.' }
        Say "The leftover folder $Staging was renamed to $aside (nothing deleted)."
    }
    Say 'Unpacking the package (a few minutes) ...'
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::ExtractToDirectory($auth.final_zip, $package)
    $dir = PackageDir
    $manifest = Get-Content -LiteralPath (Join-Path $dir 'release\manifest.json') -Raw | ConvertFrom-Json
    if ($manifest.release_id -ne $auth.final) { Halt "the package says $($manifest.release_id), not $($auth.final)." }
    Say 'Checking every file of your installed JARVIS (a minute or two) ...'
    $v = Json (Installer @('verify')) 'The verification'
    if ($v.status -ne 'verified' -or $v.release -ne $auth.previous) { Halt "your installed JARVIS does not verify ($($v.status) $($v.reason)). Tell Claude." }
    Save 'check.json' ([ordered]@{ schema = 'jarvis-everyday-update-check-v2'; utc = (Now); final = $auth.final; previous = $auth.previous
        zip = $auth.final_zip; zip_sha256 = $zipHash; setup = $auth.final_setup; setup_sha256 = $setupHash; app_id = $appId; sandbox = $sandbox
        package_unpacked_to = $dir; package_release = $manifest.release_id; package_files = @($manifest.files).Count
        install_home = $InstallHome; current = $current; installed_verified = $v.status; free_bytes = $free; jarvis_processes = 0
        staging = $Staging; staging_moved_aside = $aside; entry_before = $entryBefore; shortcuts = (Links) })
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
    $tested = Json (Recovery $auth.previous @('rehearse', '--id', $made.id)) 'The test restore'
    if ($tested.status -ne 'restore_rehearsal_passed') { Halt "the test restore did not pass ($($tested.status) $($tested.reason))." }
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
        backup_id = $made.id; created = $made; test_restore = $tested
        backup = $zip; backup_sha256 = $zipHash; copy = (Join-Path $backupDir ($made.id + '.zip')); copy_sha256 = $copyHash
        installed_still_verified = $v.status; database_sha256_after_backup = (DatabaseHash) })
    Done ('STEP 2 PASSED: backup {0} made and test-restored; a copy is in {1}. Tell Claude "step 2 done", then double-click update-step again for step 3 (the update).' -f $made.id, $backupDir)
}

# ---------------------------------------------------------------- 3. update (the Setup)
if (-not (Has 'update.json')) {
    Say "STEP 3 of 3: update your JARVIS from $($auth.previous) to $($auth.final) with its Setup"
    if ($WhatIf) { Done '(test mode) would run the Setup' }
    NotRunning
    $current = Current
    if ($current.release -ne $auth.previous) { Halt "your JARVIS is on $($current.release), not $($auth.previous) as at step 1. Tell Claude." }
    if (-not (Has 'backup.json')) { Halt 'no backup record: step 2 first.' }
    if (Test-Path -LiteralPath $Staging) {
        if ((Test-Path -LiteralPath (Join-Path $Staging 'setup-result.json')) -or (Test-Path -LiteralPath (Join-Path $Staging 'unins000.exe'))) { Halt "a package folder from an earlier attempt of this step exists ($Staging). Tell Claude; nothing is deleted here. " + (StateNow) }
        Halt "$Staging exists; step 1 should have moved it aside. Tell Claude."
    }
    $free = FreeBytes
    if ($free -lt $MinFreeBytes) { Halt ('only {0:N1} GB free on the install drive now (the backup took some); {1:N1} GB are needed.' -f ($free / 1GB), ($MinFreeBytes / 1GB)) }
    $dbBefore = DatabaseHash; $linksBefore = Links; $entryBefore = Entry $appId
    $setupLog = Join-Path $evidence ('setup-update-' + (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss') + '.log')
    $quoted = @($switches | ForEach-Object { if ($_ -match '^(/(?:DIR|HOME)=)(.*)$' -and $matches[2] -match ' ' -and $matches[2] -notmatch '^"') { $matches[1] + '"' + $matches[2] + '"' } else { $_ } })
    $arguments = @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', ('/LOG="' + $setupLog + '"')) + $quoted
    Say 'Running the Setup (several minutes: it unpacks the package, then its installer copies and checks every file; a line every half minute) ...'
    $t = [Diagnostics.Stopwatch]::StartNew()
    try { $p = Start-Process -FilePath $auth.final_setup -ArgumentList $arguments -PassThru } catch { Halt "the Setup could not be started ($($_.Exception.Message)). " + (StateNow) }
    $null = $p.Handle
    $next = 30
    while (-not $p.HasExited) {
        Start-Sleep -Milliseconds 500
        if ($t.Elapsed.TotalSeconds -ge $next) { $files = $(if (Test-Path -LiteralPath $Staging) { @(Get-ChildItem -LiteralPath $Staging -Recurse -File -ErrorAction SilentlyContinue).Count } else { 0 }); Say ("  the Setup still running: {0} s, {1} files in the package folder" -f [int]$t.Elapsed.TotalSeconds, $files); $next += 30 }
    }
    $p.WaitForExit()
    $seconds = [Math]::Round($t.Elapsed.TotalSeconds, 1)
    $resultFile = Join-Path $Staging 'setup-result.json'
    if (-not (Test-Path -LiteralPath $resultFile)) { Halt "the Setup left no answer ($resultFile; Setup exit $($p.ExitCode); its log is $setupLog). " + (StateNow) + ' Tell Claude.' }
    $in = $null; try { $in = Get-Content -LiteralPath $resultFile -Raw | ConvertFrom-Json } catch { Halt "the Setup's answer could not be read (its log is $setupLog). " + (StateNow) + ' Tell Claude.' }
    if ($in.status -ne 'installed' -or $in.release -ne $auth.final -or $in.previous -ne $auth.previous) {
        $now = Current
        $still = $(if ($now -and $now.release -eq $auth.previous) { ' The previous release is still current.' } else { '' })
        Halt "the installer inside the Setup answered '$($in.status)' $($in.reason) (Setup exit $($p.ExitCode); its log is $setupLog).$still " + (StateNow) + ' Tell Claude.'
    }
    $v = Json (Installer @('verify')) 'The verification'
    if ($v.status -ne 'verified' -or $v.release -ne $auth.final) { Halt 'the updated JARVIS does not verify. ' + (StateNow) + ' Tell Claude (the previous release is still installed beside it).' }
    $entry = Entry $appId
    if (-not $entry.present -or $entry.version -ne $setupRecord.version -or $entry.uninstall -notlike ('*' + (Join-Path $Staging 'unins000.exe') + '*')) { Halt "Settings > Apps does not list JARVIS $($setupRecord.version) with the uninstaller in $Staging (the update itself is in place and verified). " + (StateNow) + ' Tell Claude.' }
    $links = Links
    $program = Join-Path $InstallHome ('releases\' + $auth.final + '\electron\JARVIS.exe')
    if (-not $sandbox) {
        if ($in.shortcuts -ne 'written') { Halt "the installer did not write the shortcuts ($($in.shortcuts)) (the update itself is in place and verified). " + (StateNow) + ' Tell Claude.' }
        foreach ($pair in @(@('Desktop', $links.desktop), @('Startup', $links.startup))) { if ($pair[1] -ne $program) { Halt "the $($pair[0]) shortcut points at '$($pair[1])', not at $program (the update itself is in place and verified). Tell Claude." } }
        if (Test-Path -LiteralPath (Join-Path $InstallHome 'JARVIS.ps1')) { Halt 'the old launcher script JARVIS.ps1 is still in the install folder (the update itself is in place and verified). Tell Claude.' }
    } elseif ($in.shortcuts -notlike 'withheld*' -and $in.shortcuts -notlike 'skipped*') { Halt "a sandbox run must not write shortcuts ($($in.shortcuts))." }
    $dbAfter = DatabaseHash
    if ($dbBefore -ne $dbAfter) { Halt "the database file changed during the update ($dbBefore -> $dbAfter); an update must not touch it. " + (StateNow) + ' Tell Claude before starting JARVIS.' }
    Save 'update.json' ([ordered]@{ schema = 'jarvis-everyday-update-v2'; utc = (Now); setup = $auth.final_setup; setup_exit = $p.ExitCode; setup_switches = $arguments; setup_log = $setupLog
        setup_wall_seconds = $seconds; installer = $in; installer_seconds = $in.seconds; verify = $v.status; current = (Current); entry_before = $entryBefore; entry = $entry
        database_sha256_before = $dbBefore; database_sha256_after = $dbAfter; database_unchanged = ($dbBefore -eq $dbAfter); free_bytes_before = $free
        shortcuts_before = $linksBefore; shortcuts_after = $links; program = $program; launcher_script_left = (Test-Path -LiteralPath (Join-Path $InstallHome 'JARVIS.ps1')); jarvis_started = $false })
    $where = $(if ($sandbox) { 'the sandbox entry registered, the shortcuts withheld as a sandbox run must' } else { 'listed in Settings > Apps, the shortcuts pointing at its own JARVIS.exe' })
    Done "STEP 3 PASSED: your JARVIS is now $($auth.final), every file verified, $where. It was not started. Tell Claude ""step 3 done""; Claude gives you the short check to do when you start it."
}

# ---------------------------------------------------------------- rollback (only on the owner's word)
if ((Has 'rollback-approved.json') -and -not (Has 'rollback.json')) {
    Say "ROLLBACK: switch your JARVIS back to $($auth.previous)"
    if ($WhatIf) { Done '(test mode) would roll back' }
    NotRunning
    $back = Json (Installer @('rollback')) 'The rollback'
    if ($back.status -ne 'rolled_back' -or $back.release -ne $auth.previous) { Halt "the rollback answered '$($back.status)' $($back.reason). " + (StateNow) }
    $v = Json (Installer @('verify')) 'The verification'
    if ($v.status -ne 'verified' -or $v.release -ne $auth.previous) { Halt 'the previous release does not verify after the rollback. ' + (StateNow) + ' Tell Claude.' }
    Save 'rollback.json' ([ordered]@{ schema = 'jarvis-everyday-update-rollback-v2'; utc = (Now); result = $back; verify = $v.status; current = (Current); shortcuts = (Links); launcher_script_present = (Test-Path -LiteralPath (Join-Path $InstallHome 'JARVIS.ps1')); entry_still = (Entry $appId) })
    Done "ROLLBACK PASSED: your JARVIS is back on $($auth.previous); its PowerShell shortcuts and launcher script are back (the Settings > Apps entry still says $($setupRecord.version) until the next update). Tell Claude ""rollback done""."
}
if (Has 'rollback.json') { Done "This launcher's work is complete and recorded: the update to $($auth.final) was rolled back to $($auth.previous). Nothing more to do here." }
Done "The update to $($auth.final) is complete and recorded. Nothing more to do here."
