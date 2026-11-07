<#
Invoke-EverydayUpdate.ps1, version 3 (release 1.0.19, "OpenRouter for every AI job"; docs/UPDATE-EVERYDAY-1.0.19.md)

Updates the owner's everyday JARVIS (the installed release at %LOCALAPPDATA%\JARVIS) to a release that passed its
Stage 7 check: run BY THE OWNER, own account (jonny), non-elevated, one double-click of update-step.cmd per step. It
does nothing until Hermes has recorded the owner's approval (update-authorized.json beside this script, schema
jarvis-everyday-update-authorized-v3: the two builds, the package zip and the Setup with their hashes).

Version 3 is the 1.0.17 launcher (version 2: the update made by the release's own JARVIS-Setup-<id>.exe, run silently
with the owner's defaults exactly as the Stage 7 check ran it) with three differences for 1.0.19, the OpenRouter
release:
  - the Settings > Apps entry exists already (JARVIS 1.0.17, written by 1.0.17's Setup) and the Setup updates it; step 1
    expects it with the previous version, step 3 checks it says the new one with the new uninstaller;
  - the folder %LOCALAPPDATA%\JARVIS-package is 1.0.17's own Setup package (its uninstaller inside); it is renamed aside
    in step 1 as a leftover was for 1.0.17 (nothing deleted; the Setup's own answer must be the only one in that
    folder), and 1.0.19's Setup leaves its own package there;
  - the key file: 1.0.19 accepts only OpenRouter (JARVIS_PROVIDER=openrouter or no such line, and OPENROUTER_API_KEY).
    Step 1 reads the key file for the NAMES of its lines only (never a value: the record holds which names are present
    and the provider word), stops when 1.0.19 would refuse it (the owner edits it himself), and keeps a byte-for-byte
    copy beside it (config\.env.before-<id>) for the rollback, which puts it back.
The zip is still unpacked for the installer's own verify and rollback commands, with the package's own Python (never
the installed release's).

  check     the zip and the Setup against their hashes, the installed release and its files, nothing running, free
            space, the Settings > Apps entry with the previous version, the key file fit for 1.0.19 and copied aside;
            the previous Setup's package folder renamed aside; the package unpacked
  backup    a fresh backup of the everyday JARVIS with its own backup code (as Settings > Backups: "Create verified
            backup" then "Test restore"), copied to <Root>\backup with hashes; the program still verifies
  update    the Setup, silently; its own answer (setup-result.json) checked, every file verified, the entry, the
            shortcuts' targets, no JARVIS.ps1, the database byte-for-byte unchanged (a change stops the step);
            JARVIS is not started
  rollback  only with rollback-approved.json beside the records (the owner's word, recorded by Hermes): the package
            installer switches back to the previous release (its shortcuts follow: 1.0.17's own JARVIS.exe), the key
            file is put back from the copy made at step 1 (the file as it stood at the rollback is kept beside it);
            the Settings > Apps entry keeps saying the new version until the next update (said in the plan)

A step that fails stops and says what state the installation is in; nothing is repeated without a decision; a record
is never overwritten. For rehearsals every location is a parameter and -SetupSwitches carries the Setup's sandbox
switches ("/DIR=...;/HOME=...;/NOSHORTCUTS", one string, semicolons between: PowerShell's -File cannot pass a list).
The home and the package folder must agree with those switches, and a real run (no switch) uses the default folders
only: a rehearsal can never reach the owner's installation through a default (review finding 1, 2026-10-07).
#>
param(
    [string] $Root = 'D:\JARVIS-update-1.0.19',
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
function Halt($t) {
    # A message built with + must be in parentheses (review of 2026-10-13, finding 1: in command mode '+' and what
    # follows become extra arguments and the state would be dropped); a slip is still printed in full here.
    if ($args.Count) { $t = $t + (($args | Where-Object { "$_" -ne '+' }) -join '') }
    Say ''; Say "STOPPED: $t"; Say 'Nothing further was done. Photograph this window for Hermes.'; exit 2
}
$script:movedAside = $null
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
    # What the installation is in, read now, for a message after a failure (review finding 2 of 2026-10-07; the
    # Settings > Apps entry and the renamed package folder added by the review of 2026-10-13, finding 4: the Setup
    # removes the entry when the installer inside it refuses).
    $c = Current; $links = Links; $e = Entry $appId
    $state = 'Your JARVIS is on ' + $(if ($c) { $c.release } else { 'nothing (no current.json)' }) + '; the old launcher script JARVIS.ps1 is ' + $(if (Test-Path -LiteralPath (Join-Path $InstallHome 'JARVIS.ps1')) { 'present' } else { 'gone' }) + '; the Desktop shortcut points at ' + $(if ($links.desktop) { $links.desktop } else { 'nothing (absent)' }) + '; the Startup shortcut at ' + $(if ($links.startup) { $links.startup } else { 'nothing (absent)' }) + '; Settings > Apps lists ' + $(if ($e.present) { "$($e.name) $($e.version), uninstaller $($e.uninstall)" } else { 'no JARVIS entry' }) + '.'
    if ($script:movedAside) { $state += " The previous Setup's package folder ($($auth.previous)'s uninstaller inside) is at $($script:movedAside), renamed, nothing deleted; the Uninstall button in Settings > Apps does not work until Hermes says how to put it back (a rollback does not need it)." }
    $state
}
function NotRunning { if ((JarvisProcesses).Count) { Halt 'JARVIS is running. Quit it completely (right-click its icon near the clock > Quit JARVIS completely), then double-click update-step again.' } }
# The key file, names only (never a value): which setting names hold something, and the provider word. 1.0.19 accepts
# JARVIS_PROVIDER=openrouter, an empty line or no provider line, and needs OPENROUTER_API_KEY; openai, qwen or anything
# else is refused by 1.0.19 with a message naming openrouter (release-notes.json, 1.0.19; providers.py).
function KeyFilePath { Join-Path $InstallHome 'config\.env' }
function KeyFile {
    $f = KeyFilePath
    if (-not (Test-Path -LiteralPath $f)) { return [ordered]@{ present = $false } }
    $names = New-Object Collections.ArrayList; $provider = 'absent'
    # The same reading as 1.0.19's server.load_env: NAME=value, NAME of capitals, digits and _ only (case matters), no
    # 'export', quotes around the value dropped; a line it would not read is not counted here either.
    foreach ($line in @(Get-Content -LiteralPath $f -Encoding UTF8)) {
        $t = "$line".Trim()
        if (-not $t -or $t.StartsWith('#')) { continue }
        if ($t -cmatch '^([A-Z][A-Z0-9_]*)\s*=\s*(.*)$') {
            $name = $matches[1]; $value = $matches[2].Trim().Trim('"').Trim("'")
            if ($name -ceq 'JARVIS_PROVIDER') { $provider = $(if (-not $value) { 'empty' } elseif ($value.ToLower() -in @('openrouter', 'openai', 'qwen')) { $value.ToLower() } else { 'other' }) }
            elseif ($value) { [void]$names.Add($name) }
        }
    }
    $listed = @($names | Where-Object { $_ -clike '*KEY*' -or $_ -clike 'JARVIS_*' -or $_ -clike '*MODEL*' } | Sort-Object -Unique)
    [ordered]@{ present = $true; sha256 = (Sha256 $f); bytes = (Get-Item -LiteralPath $f -Force).Length; provider = $provider
        has_openrouter_key = [bool]($names -ccontains 'OPENROUTER_API_KEY'); names = $listed }
}
function KeyFileCopyPath { (KeyFilePath) + '.before-' + $auth.final }
function FreeBytes { (Get-PSDrive -Name ([IO.Path]::GetPathRoot($InstallHome).Substring(0, 1))).Free }

if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { Halt 'this window has administrator rights. Close it and start update-step from a normal File Explorer window.' }
if (-not (Test-Path -LiteralPath $Authorized)) { Halt 'this update has not been approved yet (no update-authorized.json beside this script).' }
$auth = Get-Content -LiteralPath $Authorized -Raw | ConvertFrom-Json
if ($auth.schema -ne 'jarvis-everyday-update-authorized-v3' -or -not $auth.final -or -not $auth.previous -or -not $auth.final_zip -or -not $auth.final_zip_sha256 -or -not $auth.final_setup -or -not $auth.final_setup_sha256) { Halt 'the approval file does not name the two builds, the package and the Setup (version 3 approval).' }
$previousVersion = $auth.previous.Split('-')[0]
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
    if ($current.release -ne $auth.previous) { Halt "your JARVIS is on $($current.release); this update is planned from $($auth.previous). Tell Hermes." }
    NotRunning
    $free = FreeBytes
    if ($free -lt $MinFreeBytes) { Halt ('only {0:N1} GB free on the install drive; {1:N1} GB are needed.' -f ($free / 1GB), ($MinFreeBytes / 1GB)) }
    if (Test-Path -LiteralPath $package) { Halt "$package already exists from an earlier attempt; tell Hermes." }
    # The entry the previous release's Setup wrote (a sandbox: the sandbox entry its Setup wrote with the sandbox switches).
    $entryBefore = Entry $appId
    if (-not $entryBefore.present -or $entryBefore.version -ne $previousVersion) {
        Halt ("Settings > Apps should list JARVIS $previousVersion (written by its Setup) before this update; it lists " + $(if ($entryBefore.present) { "$($entryBefore.name) $($entryBefore.version)" } else { 'nothing' }) + '. Tell Hermes.')
    }
    if ($entryBefore.uninstall -notlike ('*' + (Join-Path $Staging 'unins000.exe') + '*')) { Halt "Settings > Apps points its Uninstall button at '$($entryBefore.uninstall)', not at the uninstaller in $Staging. Tell Hermes." }
    # The key file (names only): 1.0.19 must accept it. Its copy for the rollback is made at the end of this step, once
    # every check has passed (review of 2026-10-13, finding 5).
    $keys = KeyFile
    if (-not $sandbox -or $keys.present) {   # a sandbox without a key file: 1.0.19 runs without keys there, as in the Stage 7 VM
        if (-not $keys.present) { Halt "no key file at $(KeyFilePath). Tell Hermes." }
        if ($keys.provider -notin @('absent', 'empty', 'openrouter') -or -not $keys.has_openrouter_key) {
            Halt ("1.0.19 would refuse your key file as it stands: the provider line says '{0}' and OPENROUTER_API_KEY is {1}. Open {2} yourself (Hermes never reads or edits it): set JARVIS_PROVIDER=openrouter (or remove that line), make sure a line OPENROUTER_API_KEY=... is there (that exact name, capitals), save, then double-click update-step again. The old OPENAI_* and DASHSCOPE_* lines may stay; 1.0.19 ignores them." -f $keys.provider, $(if ($keys.has_openrouter_key) { 'present' } else { 'missing' }), (KeyFilePath))
        }
    }
    Say 'Checking the package and the Setup against their hashes (a minute or two) ...'
    $zipHash = Sha256 $auth.final_zip
    if ($zipHash -ne $auth.final_zip_sha256) { Halt "the package zip does not match its approved hash ($zipHash)." }
    $setupHash = Sha256 $auth.final_setup
    if ($setupHash -ne $auth.final_setup_sha256) { Halt "the Setup does not match its approved hash ($setupHash)." }
    if ($setupRecord.setup_sha256 -ne $setupHash -or $setupRecord.release_id -ne $auth.final) { Halt "the Setup's record does not describe this Setup." }
    # The previous Setup's package folder (its uninstaller, which the Settings > Apps entry points at, and its answer):
    # looked at here, renamed aside at step 3 right before the Setup runs (version 3: the entry's Uninstall button
    # points at a missing file for the minutes of step 3 only, not from step 1 on). Nothing is deleted.
    $aside = $Staging + '-before-' + $auth.final
    if (Test-Path -LiteralPath $aside) { Halt "$aside exists already; tell Hermes." }
    $stagingBefore = [ordered]@{ present = (Test-Path -LiteralPath $Staging) }
    if ($stagingBefore.present) {
        $u = Join-Path $Staging 'unins000.exe'; $a = Join-Path $Staging 'setup-result.json'
        $stagingBefore['uninstaller_present'] = (Test-Path -LiteralPath $u)
        if ($stagingBefore.uninstaller_present) { $stagingBefore['uninstaller_sha256'] = (Sha256 $u) }
        if (Test-Path -LiteralPath $a) { try { $stagingBefore['answer_release'] = (Get-Content -LiteralPath $a -Raw | ConvertFrom-Json).release } catch { $stagingBefore['answer_release'] = 'unreadable' } }
        if (-not $stagingBefore.uninstaller_present) { Halt "$Staging holds no unins000.exe, though Settings > Apps points there. Tell Hermes." }
        if ($stagingBefore.answer_release -ne $auth.previous) { Halt "$Staging is not the package folder of $($auth.previous) (its answer says '$($stagingBefore.answer_release)'). Tell Hermes." }
        Say "The previous Setup's package folder $Staging (its uninstaller inside) will be renamed to $aside at step 3, right before the Setup runs (nothing deleted; 1.0.19's Setup makes its own)."
    } else { Halt "$Staging (the previous Setup's package folder, which Settings > Apps points at) is missing. Tell Hermes." }
    Say 'Unpacking the package (a few minutes) ...'
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::ExtractToDirectory($auth.final_zip, $package)
    $dir = PackageDir
    $manifest = Get-Content -LiteralPath (Join-Path $dir 'release\manifest.json') -Raw | ConvertFrom-Json
    if ($manifest.release_id -ne $auth.final) { Halt "the package says $($manifest.release_id), not $($auth.final)." }
    Say 'Checking every file of your installed JARVIS (a minute or two) ...'
    $v = Json (Installer @('verify')) 'The verification'
    if ($v.status -ne 'verified' -or $v.release -ne $auth.previous) { Halt "your installed JARVIS does not verify ($($v.status) $($v.reason)). Tell Hermes." }
    # The copy of the key file for the rollback, last: a copy with the same bytes from an earlier attempt is kept.
    if ($keys.present) {
        $copy = KeyFileCopyPath
        if ((Test-Path -LiteralPath $copy) -and (Sha256 $copy) -ne $keys.sha256) { Halt "$copy exists already and differs from the key file; tell Hermes (nothing is deleted here)." }
        if (-not (Test-Path -LiteralPath $copy)) { try { Copy-Item -LiteralPath (KeyFilePath) -Destination $copy } catch { Halt "the key file could not be copied to $copy ($($_.Exception.Message)). Nothing has changed. Tell Hermes." } }
        if ((Sha256 $copy) -ne $keys.sha256) { Halt 'the copy of the key file does not match the key file. Tell Hermes.' }
        $keys['copy'] = $copy
    }
    Save 'check.json' ([ordered]@{ schema = 'jarvis-everyday-update-check-v3'; utc = (Now); final = $auth.final; previous = $auth.previous; key_file = $keys
        zip = $auth.final_zip; zip_sha256 = $zipHash; setup = $auth.final_setup; setup_sha256 = $setupHash; app_id = $appId; sandbox = $sandbox
        package_unpacked_to = $dir; package_release = $manifest.release_id; package_files = @($manifest.files).Count
        install_home = $InstallHome; current = $current; installed_verified = $v.status; free_bytes = $free; jarvis_processes = 0
        staging = $Staging; staging_before = $stagingBefore; staging_to_be_moved_aside = $(if ($stagingBefore.present) { $aside } else { $null }); entry_before = $entryBefore; shortcuts = (Links) })
    Done 'STEP 1 PASSED. Tell Hermes "step 1 done". Then double-click update-step again for step 2 (the backup).'
}

# ---------------------------------------------------------------- 2. backup
if (-not (Has 'backup.json')) {
    Say 'STEP 2 of 3: a fresh backup of your JARVIS (the same as Settings > Backups: create, then test restore)'
    if ($WhatIf) { Done '(test mode) would make and test the backup' }
    NotRunning
    $current = Current
    if ($current.release -ne $auth.previous) { Halt "your JARVIS is on $($current.release), not $($auth.previous) as at step 1. Tell Hermes." }
    Say 'Making the backup (about a minute) ...'
    $made = Json (Recovery $auth.previous @('create')) 'The backup'
    if ($made.status -ne 'backup_verified' -or -not $made.id) { Halt "the backup did not report backup_verified ($($made.status) $($made.reason))." }
    Say ("Backup {0}: {1} files, verified. Testing the restore in a temporary folder ..." -f $made.id, $made.files)
    $tested = Json (Recovery $auth.previous @('rehearse', '--id', $made.id)) 'The test restore'
    if ($tested.status -ne 'restore_rehearsal_passed') { Halt "the test restore did not pass ($($tested.status) $($tested.reason))." }
    $folder = Join-Path $InstallHome 'data-backups'
    $zip = Join-Path $folder ($made.id + '.zip'); $receipt = Join-Path $folder ($made.id + '.restore-check.json')
    foreach ($p in $zip, $receipt) { if (-not (Test-Path -LiteralPath $p)) { Halt "the backup file $p is missing." } }
    if (Test-Path -LiteralPath $backupDir) { Halt "$backupDir already exists; tell Hermes." }
    New-Item -ItemType Directory -Path $backupDir | Out-Null
    $zipHash = Sha256 $zip
    Copy-Item -LiteralPath $zip, $receipt -Destination $backupDir
    $copyHash = Sha256 (Join-Path $backupDir ($made.id + '.zip'))
    if ($copyHash -ne $zipHash) { Halt 'the copy of the backup does not match the backup.' }
    $v = Json (Installer @('verify')) 'The verification'
    if ($v.status -ne 'verified' -or $v.release -ne $auth.previous) { Halt 'your installed JARVIS no longer verifies after the backup. Tell Hermes.' }
    Save 'backup.json' ([ordered]@{ schema = 'jarvis-everyday-update-backup-v1'; utc = (Now); release_used = $auth.previous
        backup_id = $made.id; created = $made; test_restore = $tested
        backup = $zip; backup_sha256 = $zipHash; copy = (Join-Path $backupDir ($made.id + '.zip')); copy_sha256 = $copyHash
        installed_still_verified = $v.status; database_sha256_after_backup = (DatabaseHash) })
    Done ('STEP 2 PASSED: backup {0} made and test-restored; a copy is in {1}. Tell Hermes "step 2 done", then double-click update-step again for step 3 (the update).' -f $made.id, $backupDir)
}

# ---------------------------------------------------------------- 3. update (the Setup)
if (-not (Has 'update.json')) {
    Say "STEP 3 of 3: update your JARVIS from $($auth.previous) to $($auth.final) with its Setup"
    if ($WhatIf) { Done '(test mode) would run the Setup' }
    NotRunning
    $current = Current
    if ($current.release -ne $auth.previous) { Halt ("your JARVIS is on $($current.release), not $($auth.previous) as at step 1. Tell Hermes. " + (StateNow)) }
    if (-not (Has 'backup.json')) { Halt 'no backup record: step 2 first.' }
    $check = Get-Content -LiteralPath (Join-Path $evidence 'check.json') -Raw | ConvertFrom-Json
    $aside = $Staging + '-before-' + $auth.final
    if (Test-Path -LiteralPath $aside) { Halt ("$aside exists already (an earlier attempt of this step?). Tell Hermes; nothing is deleted here. " + (StateNow)) }
    if (Test-Path -LiteralPath $Staging) {
        if (-not $check.staging_before.present) { Halt ("$Staging appeared after step 1. Tell Hermes; nothing is deleted here. " + (StateNow)) }
        $u = Join-Path $Staging 'unins000.exe'
        if ($check.staging_before.uninstaller_present -and (-not (Test-Path -LiteralPath $u) -or (Sha256 $u) -ne $check.staging_before.uninstaller_sha256)) { Halt ("$Staging changed since step 1 (an earlier attempt of this step?). Tell Hermes; nothing is deleted here. " + (StateNow)) }
    } elseif ($check.staging_before.present) { Halt ("$Staging is gone since step 1. Tell Hermes. " + (StateNow)) }
    $free = FreeBytes
    if ($free -lt $MinFreeBytes) { Halt ('only {0:N1} GB free on the install drive now (the backup took some); {1:N1} GB are needed.' -f ($free / 1GB), ($MinFreeBytes / 1GB)) }
    $dbBefore = DatabaseHash; $linksBefore = Links; $entryBefore = Entry $appId
    $keyBefore = $(if (Test-Path -LiteralPath (KeyFilePath)) { Sha256 (KeyFilePath) } else { $null })   # the update must not touch the key file either
    if (-not $entryBefore.present -or $entryBefore.version -ne $previousVersion) { Halt ("Settings > Apps no longer lists JARVIS $previousVersion as at step 1. Tell Hermes. " + (StateNow)) }
    # The previous Setup's package folder renamed aside now (seen at step 1): the Setup would delete its release folder
    # and installer before unpacking, and the records rule says nothing is deleted; the Setup's own answer must also be
    # the only setup-result.json there. From here until the Setup has written its own uninstaller, the entry's
    # Uninstall button points at a missing file; a rollback does not need it.
    $moved = $null
    if (Test-Path -LiteralPath $Staging) {
        try { Move-Item -LiteralPath $Staging -Destination $aside } catch { Halt "the previous Setup's package folder $Staging could not be renamed aside ($($_.Exception.Message)). Close any window showing it and double-click update-step again. Nothing has changed." }
        if ((Test-Path -LiteralPath $Staging) -or -not (Test-Path -LiteralPath $aside)) { Halt 'the previous Setup''s package folder could not be moved aside. Tell Hermes.' }
        $moved = $aside; $script:movedAside = $aside
        Say "The previous Setup's package folder $Staging was renamed to $aside (nothing deleted). Until the Setup has written its own uninstaller (a few minutes) the Uninstall button in Settings > Apps points at the old place: do not press it."
    }
    $setupLog = Join-Path $evidence ('setup-update-' + (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss') + '.log')
    $quoted = @($switches | ForEach-Object { if ($_ -match '^(/(?:DIR|HOME)=)(.*)$' -and $matches[2] -match ' ' -and $matches[2] -notmatch '^"') { $matches[1] + '"' + $matches[2] + '"' } else { $_ } })
    $arguments = @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', ('/LOG="' + $setupLog + '"')) + $quoted
    Say 'Running the Setup (several minutes: it unpacks the package, then its installer copies and checks every file; a line every half minute) ...'
    $t = [Diagnostics.Stopwatch]::StartNew()
    try { $p = Start-Process -FilePath $auth.final_setup -ArgumentList $arguments -PassThru } catch { Halt ("the Setup could not be started ($($_.Exception.Message)). " + (StateNow)) }
    $null = $p.Handle
    $next = 30
    while (-not $p.HasExited) {
        Start-Sleep -Milliseconds 500
        if ($t.Elapsed.TotalSeconds -ge $next) { $files = $(if (Test-Path -LiteralPath $Staging) { @(Get-ChildItem -LiteralPath $Staging -Recurse -File -ErrorAction SilentlyContinue).Count } else { 0 }); Say ("  the Setup still running: {0} s, {1} files in the package folder" -f [int]$t.Elapsed.TotalSeconds, $files); $next += 30 }
    }
    $p.WaitForExit()
    $seconds = [Math]::Round($t.Elapsed.TotalSeconds, 1)
    $resultFile = Join-Path $Staging 'setup-result.json'
    $refused = ' When the installer inside the Setup refuses, the Setup removes the Settings > Apps entry; a rollback does not need it, and Hermes will say how to put the entry and the renamed folder back (nothing deleted).'
    if (-not (Test-Path -LiteralPath $resultFile)) { Halt ("the Setup left no answer ($resultFile; Setup exit $($p.ExitCode); its log is $setupLog). " + (StateNow) + $refused + ' Tell Hermes.') }
    $in = $null; try { $in = Get-Content -LiteralPath $resultFile -Raw | ConvertFrom-Json } catch { Halt ("the Setup's answer could not be read (its log is $setupLog). " + (StateNow) + $refused + ' Tell Hermes.') }
    if ($in.status -ne 'installed' -or $in.release -ne $auth.final -or $in.previous -ne $auth.previous) {
        $now = Current
        $still = $(if ($now -and $now.release -eq $auth.previous) { ' The previous release is still current.' } else { '' })
        Halt ("the installer inside the Setup answered '$($in.status)' $($in.reason) (Setup exit $($p.ExitCode); its log is $setupLog).$still " + (StateNow) + $refused + ' Tell Hermes.')
    }
    $v = Json (Installer @('verify')) 'The verification'
    if ($v.status -ne 'verified' -or $v.release -ne $auth.final) { Halt ('the updated JARVIS does not verify. ' + (StateNow) + ' Tell Hermes (the previous release is still installed beside it).') }
    $entry = Entry $appId
    if (-not $entry.present -or $entry.version -ne $setupRecord.version -or $entry.uninstall -notlike ('*' + (Join-Path $Staging 'unins000.exe') + '*')) { Halt ("Settings > Apps does not list JARVIS $($setupRecord.version) with the uninstaller in $Staging (the update itself is in place and verified). " + (StateNow) + ' Tell Hermes.') }
    $links = Links
    $program = Join-Path $InstallHome ('releases\' + $auth.final + '\electron\JARVIS.exe')
    if (-not $sandbox) {
        if ($in.shortcuts -ne 'written') { Halt ("the installer did not write the shortcuts ($($in.shortcuts)) (the update itself is in place and verified). " + (StateNow) + ' Tell Hermes.') }
        foreach ($pair in @(@('Desktop', $links.desktop), @('Startup', $links.startup))) { if ($pair[1] -ne $program) { Halt "the $($pair[0]) shortcut points at '$($pair[1])', not at $program (the update itself is in place and verified). Tell Hermes." } }
        if (Test-Path -LiteralPath (Join-Path $InstallHome 'JARVIS.ps1')) { Halt 'the old launcher script JARVIS.ps1 is still in the install folder (the update itself is in place and verified). Tell Hermes.' }
    } elseif ($in.shortcuts -notlike 'withheld*' -and $in.shortcuts -notlike 'skipped*') { Halt "a sandbox run must not write shortcuts ($($in.shortcuts))." }
    $dbAfter = DatabaseHash
    if ($dbBefore -ne $dbAfter) { Halt ("the database file changed during the update ($dbBefore -> $dbAfter); an update must not touch it. " + (StateNow) + ' Tell Hermes before starting JARVIS.') }
    $keyAfter = $(if (Test-Path -LiteralPath (KeyFilePath)) { Sha256 (KeyFilePath) } else { $null })
    if ($keyBefore -ne $keyAfter) { Halt ("the key file changed during the update; an update must not touch it. " + (StateNow) + ' Tell Hermes before starting JARVIS.') }
    Save 'update.json' ([ordered]@{ schema = 'jarvis-everyday-update-v3'; utc = (Now); setup = $auth.final_setup; setup_exit = $p.ExitCode; setup_switches = $arguments; setup_log = $setupLog; staging_moved_aside = $moved
        setup_wall_seconds = $seconds; installer = $in; installer_seconds = $in.seconds; verify = $v.status; current = (Current); entry_before = $entryBefore; entry = $entry
        database_sha256_before = $dbBefore; database_sha256_after = $dbAfter; database_unchanged = ($dbBefore -eq $dbAfter); key_file_sha256_before = $keyBefore; key_file_sha256_after = $keyAfter; key_file_unchanged = ($keyBefore -eq $keyAfter); free_bytes_before = $free
        shortcuts_before = $linksBefore; shortcuts_after = $links; program = $program; launcher_script_left = (Test-Path -LiteralPath (Join-Path $InstallHome 'JARVIS.ps1')); jarvis_started = $false })
    $where = $(if ($sandbox) { 'the sandbox entry registered, the shortcuts withheld as a sandbox run must' } else { 'listed in Settings > Apps, the shortcuts pointing at its own JARVIS.exe' })
    Done "STEP 3 PASSED: your JARVIS is now $($auth.final), every file verified, $where. It was not started. Tell Hermes ""step 3 done""; Hermes gives you the short check to do when you start it."
}

# ---------------------------------------------------------------- rollback (only on the owner's word)
if ((Has 'rollback-approved.json') -and -not (Has 'rollback.json')) {
    Say "ROLLBACK: switch your JARVIS back to $($auth.previous)"
    if ($WhatIf) { Done '(test mode) would roll back' }
    NotRunning
    # Only from the new release (review of 2026-10-13, finding 2): an earlier attempt that switched back and then stopped
    # before its record must not be followed by a second installer rollback, which would switch FORWARD again.
    $c = Current
    if (-not $c -or $c.release -ne $auth.final) {
        if ($c -and $c.release -eq $auth.previous -and $c.previous -eq $auth.final) { Halt ("an earlier attempt already switched your JARVIS back to $($auth.previous) but did not finish its checks; nothing is switched again. Tell Hermes. " + (StateNow)) }
        Halt ("your JARVIS is on " + $(if ($c) { $c.release } else { 'nothing (no current.json)' }) + ", not $($auth.final); nothing is switched. Tell Hermes. " + (StateNow))
    }
    Save ('rollback-attempt-' + (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss') + '.json') ([ordered]@{ schema = 'jarvis-everyday-update-rollback-attempt-v1'; utc = (Now); from = $c.release; to = $auth.previous })
    $back = Json (Installer @('rollback')) 'The rollback'
    if ($back.status -ne 'rolled_back' -or $back.release -ne $auth.previous) { Halt ("the rollback answered '$($back.status)' $($back.reason). " + (StateNow)) }
    $v = Json (Installer @('verify')) 'The verification'
    if ($v.status -ne 'verified' -or $v.release -ne $auth.previous) { Halt ('the previous release does not verify after the rollback. ' + (StateNow) + ' Tell Hermes.') }
    # The key file back as it stood at step 1 (undoing any change made on the new release); the file as it stands now is
    # kept beside it. The step 1 file was already the one for 1.0.19 (its provider line openrouter), which 1.0.17 does
    # not know: the owner sets that line himself before starting 1.0.17 (said below and in the plan).
    $keyBack = [ordered]@{ restored = $false }
    $copy = KeyFileCopyPath
    $check = $(if (Has 'check.json') { Get-Content -LiteralPath (Join-Path $evidence 'check.json') -Raw | ConvertFrom-Json } else { $null })
    if (Test-Path -LiteralPath $copy) {
        if ($check -and $check.key_file.sha256 -and (Sha256 $copy) -ne $check.key_file.sha256) { Halt ("the copy of the key file ($copy) is not the one step 1 made (its hash differs from the record); the key file is left as it is. " + (StateNow) + ' Tell Hermes.') }
        $now = KeyFile
        $kept = (KeyFilePath) + '.rolled-back-from-' + $auth.final
        if (Test-Path -LiteralPath $kept) { Halt ("$kept exists already; the key file is left as it is. " + (StateNow) + ' Tell Hermes.') }
        try {
            if ($now.present) { Copy-Item -LiteralPath (KeyFilePath) -Destination $kept; if ((Sha256 $kept) -ne $now.sha256) { throw 'the kept copy does not match the key file' } }
            Copy-Item -LiteralPath $copy -Destination (KeyFilePath) -Force
            if ((Sha256 (KeyFilePath)) -ne (Sha256 $copy)) { throw 'the key file does not match its copy after the restore' }
        } catch { Halt ("the key file could not be put back ($($_.Exception.Message)). Nothing is lost: the file as it stood on $($auth.final) is at " + $(if (Test-Path -LiteralPath $kept) { $kept } else { (KeyFilePath) }) + " and the step 1 copy at $copy. " + (StateNow) + ' Tell Hermes.') }
        $after = KeyFile
        $keyBack = [ordered]@{ restored = $true; from = $copy; kept_as = $(if ($now.present) { $kept } else { $null }); sha256 = (Sha256 $copy); provider_after = $after.provider }
    } elseif (-not $sandbox) { $keyBack = [ordered]@{ restored = $false; reason = "the copy $copy is missing"; provider_now = (KeyFile).provider } }
    $links = Links
    if (-not $sandbox) {
        $program = Join-Path $InstallHome ('releases\' + $auth.previous + '\electron\JARVIS.exe')
        foreach ($pair in @(@('Desktop', $links.desktop), @('Startup', $links.startup))) { if ($pair[1] -ne $program) { Halt ("after the rollback the $($pair[0]) shortcut points at '$($pair[1])', not at $program (the rollback itself is in place and verified). " + (StateNow) + ' Tell Hermes.') } }
    }
    Save 'rollback.json' ([ordered]@{ schema = 'jarvis-everyday-update-rollback-v3'; utc = (Now); result = $back; verify = $v.status; current = (Current); shortcuts = $links; key_file = $keyBack; launcher_script_present = (Test-Path -LiteralPath (Join-Path $InstallHome 'JARVIS.ps1')); entry_still = (Entry $appId) })
    $where = $(if ($sandbox) { 'the shortcuts withheld as a sandbox run must' } else { "its shortcuts at that release's JARVIS.exe" })
    $keyWord = $(if ($keyBack.restored) { "the key file as it stood at step 1 (its provider line says '$($keyBack.provider_after)'" + $(if ($keyBack.provider_after -in @('openrouter', 'absent', 'empty')) { ", which $($auth.previous) does not know: open $(KeyFilePath) yourself and set JARVIS_PROVIDER=qwen or openai before starting JARVIS)" } else { ')' }) } else { "BUT the key file was NOT put back ($($keyBack.reason)): it stands as it was on $($auth.final)" })
    Done "ROLLBACK PASSED: your JARVIS is back on $($auth.previous), $where, $keyWord (the Settings > Apps entry still says $($setupRecord.version) until the next update). Tell Hermes ""rollback done""."
}
if (Has 'rollback.json') { Done "This launcher's work is complete and recorded: the update to $($auth.final) was rolled back to $($auth.previous). Nothing more to do here." }
Done "The update to $($auth.final) is complete and recorded. Nothing more to do here."
