<#
.SYNOPSIS
Stage 7 (packaged-application acceptance) and the standard pre-update check, run INSIDE the acceptance machine.
A copy of Invoke-Gate17.ps1 as used for Stage 6 Gates 17 and 19 (that file is evidence and stays unchanged), with
one added phase, Interrupt: an update killed while it is copying, then run again. Rehearsed locally on D: first.

Runs on a fresh Windows 11 Home with nothing installed (Windows PowerShell 5.1 only). The
release carries its own Python, Electron and models, so no prerequisite is installed. Every
step writes a JSON record to the evidence folder; the first failure stops the run (no silent
retry). Nothing here reads or writes outside the package, the install home, the staging
folder and the evidence folder. There are no secrets on the machine; none are created.

.PARAMETER Package   Folder holding JARVIS-<id>.zip and JARVIS-<id>.release.json (the mounted ISO root).
.PARAMETER Evidence  Folder for the records (the single declared egress folder on the VM).
.PARAMETER Phase     Baseline | Install | AfterRestart | Cleanliness | Uninstall | Update | All (All = Baseline, Install, Uninstall).
                     Cleanliness = the Baseline checks repeated with JARVIS installed (nothing else may have appeared).
                     Update = Gate 19: previous build installed, updated to this package's build, rolled back, updated again.
.PARAMETER PreviousPackage  Update phase: folder holding the previous build's zip and release record (the second package disc).
.PARAMETER InstallHome  Install folder. VM: default %LOCALAPPDATA%\JARVIS. Local rehearsal: a sandbox on D:.
.PARAMETER Staging      Where the package is extracted. VM: default %LOCALAPPDATA%\JARVIS-package. Local rehearsal: a folder on D:.
.PARAMETER NoShortcuts  Local rehearsal only (never touch the owner's real Desktop/Startup folders).
.PARAMETER SkipBaseline Local rehearsal only (this PC is a development machine and would fail the cleanliness checks).
#>
param(
    [Parameter(Mandatory)] [string] $Package,
    [Parameter(Mandatory)] [string] $Evidence,
    [ValidateSet('Baseline', 'Install', 'AfterRestart', 'Cleanliness', 'Uninstall', 'Update', 'Interrupt', 'All')] [string] $Phase = 'All',
    [string] $PreviousPackage,
    [string] $InstallHome = (Join-Path $env:LOCALAPPDATA 'JARVIS'),
    [string] $Staging = (Join-Path $env:LOCALAPPDATA 'JARVIS-package'),
    [switch] $NoShortcuts,
    [switch] $SkipBaseline
)
$ErrorActionPreference = 'Stop'
$script:Started = Get-Date
$Gate = 'stage7'
$script:EvidenceDir = Join-Path $Evidence ("$Gate-" + $script:Started.ToUniversalTime().ToString('yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $script:EvidenceDir -Force | Out-Null
$script:Summary = New-Object Collections.ArrayList
$PreviousStaging = "$Staging-previous"
$Utf8 = New-Object Text.UTF8Encoding $false

function Now { (Get-Date).ToUniversalTime().ToString('o') }
function Record($name, $data) {
    [IO.File]::WriteAllText((Join-Path $script:EvidenceDir "$name.json"), ($data | ConvertTo-Json -Depth 8), $Utf8)
    $script:Summary.Add([ordered]@{ step = $name; status = $data.status; at = (Now) }) | Out-Null
    Write-Host ("{0,-30} {1}" -f $name, $data.status)
}
function Finish($overall) {
    $summary = [ordered]@{ schema = 'jarvis-stage7-run-v1'; overall = $overall; phase = $Phase; home = $InstallHome; package = $Package
                           started_utc = $script:Started.ToUniversalTime().ToString('o'); finished_utc = (Now); steps = @($script:Summary) }
    [IO.File]::WriteAllText((Join-Path $script:EvidenceDir 'SUMMARY.json'), ($summary | ConvertTo-Json -Depth 6), $Utf8)
    Write-Host "$Gate $Phase : $overall  ($script:EvidenceDir)"
}
function Fail($name, $data, $why) { $data.status = 'FAIL'; $data.reason = $why; Record $name $data; Finish 'FAIL'; exit 2 }
function Sha256($path) { (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower() }
# True when a name refers to JARVIS itself. The acceptance VM's account (jarvis-s6-guest) and computer name
# (JARVIS-S6-FRESH) contain the word, and Windows and Guest Additions name things after them (for example the pipe
# VBoxTrayIPC-<account>), so both names are removed before testing.
function MentionsJarvis([string] $text) { (($text -replace [regex]::Escape($env:USERNAME), '') -replace [regex]::Escape($env:COMPUTERNAME), '') -match 'jarvis' }
function Processes { @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like (Join-Path $InstallHome 'releases\*') }) }
function Link { Get-Content -LiteralPath (Join-Path $InstallHome 'data\core-connection.json') -Raw | ConvertFrom-Json }
function Session {
    $link = Link
    $null = Invoke-WebRequest -Uri ($link.origin + '/') -Headers @{ 'X-Jarvis-Desktop' = $link.token } -SessionVariable s -UseBasicParsing -TimeoutSec 15
    @{ origin = $link.origin; headers = @{ 'X-Jarvis-Desktop' = $link.token }; session = $s }
}
function Api($route, $body) {
    $c = Session
    if ($null -eq $body) { return Invoke-RestMethod -Uri ($c.origin + $route) -Headers $c.headers -WebSession $c.session -TimeoutSec 60 }
    Invoke-RestMethod -Uri ($c.origin + $route) -Headers $c.headers -WebSession $c.session -Method Post -ContentType 'application/json' -Body ($body | ConvertTo-Json -Compress) -TimeoutSec 600
}
function WaitForCore($seconds) {
    $deadline = (Get-Date).AddSeconds($seconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Path -LiteralPath (Join-Path $InstallHome 'data\core-connection.json')) { try { $null = Session; return $true } catch {} }
        Start-Sleep -Milliseconds 500
    }
    $false
}
function Launch {
    $shortcut = Join-Path ([Environment]::GetFolderPath('Desktop')) 'JARVIS.lnk'
    if (-not $NoShortcuts -and (Test-Path -LiteralPath $shortcut)) { Start-Process -FilePath $shortcut; return 'desktop shortcut' }
    Start-Process powershell -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $InstallHome 'JARVIS.ps1') -WindowStyle Hidden
    'JARVIS.ps1'
}
function StopJarvis {
    # What the installer does before an update: ask the Core to stop, then end any shell left showing "Core stopped".
    try { $null = Api '/api/shutdown' @{} } catch {}
    $deadline = (Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $deadline -and (Test-Path -LiteralPath (Join-Path $InstallHome 'data\core-connection.json'))) { Start-Sleep -Milliseconds 500 }
    $coreStopped = -not (Test-Path -LiteralPath (Join-Path $InstallHome 'data\core-connection.json'))
    Start-Sleep -Seconds 5
    $left = Processes
    $left | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 2
    [ordered]@{ core_stopped_on_request = $coreStopped; shell_processes_ended = $left.Count; processes_now = (Processes).Count }
}
function Release {
    $current = (Get-Content -LiteralPath (Join-Path $InstallHome 'current.json') -Raw | ConvertFrom-Json).release
    $dir = Join-Path $InstallHome ('releases\' + $current)
    @{ id = $current; python = (Join-Path $dir 'python\python.exe'); app = (Join-Path $dir 'app') }
}
function Installer([string[]] $arguments) {
    # Maintenance runs with the PACKAGE's own Python (installer.py ships beside release\ and is not
    # installed). Never run it with the installed release's Python: uninstall and update first stop
    # every process running from the install folder, which would include that interpreter.
    $python = Join-Path $Staging 'release\python\python.exe'
    $out = & $python (Join-Path $Staging 'installer.py') @arguments --home $InstallHome $(if ($NoShortcuts) { '--no-shortcuts' }) 2>&1 | Out-String
    if ([string]::IsNullOrWhiteSpace($out)) { return @{ status = 'error'; output = '(no output)' } }
    try { $out | ConvertFrom-Json } catch { @{ status = 'error'; output = $out.Substring(0, [Math]::Min(1500, $out.Length)) } }
}

# ---------------------------------------------------------------- No elevation (owner decision 2026-10-04)
# JARVIS installs and runs per user. The acceptance account is in the Administrators group, so every phase that
# installs or runs JARVIS first records that this process has no administrator rights and stops if it has.
if ($Phase -ne 'Baseline') {
    $elevated = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    $data = [ordered]@{ status = 'PASS'; account = "$env:USERDOMAIN\$env:USERNAME"; process_elevated = $elevated; note = 'the installer and JARVIS are started from this process and inherit its rights; a UAC prompt at any point is a STOP reported by the owner' }
    if ($elevated) { Fail 'E0-not-elevated' $data 'this window has administrator rights; close it and start the gate from a normal window' }
    Record 'E0-not-elevated' $data
}

# ---------------------------------------------------------------- Baseline (FRESH-CLEAN-BASELINE negative checks) and
# Cleanliness (the same checks with JARVIS installed: nothing except JARVIS itself may have appeared)
if ((($Phase -eq 'Baseline' -or $Phase -eq 'All') -and -not $SkipBaseline) -or $Phase -eq 'Cleanliness') {
    $jarvisExpected = ($Phase -eq 'Cleanliness')
    $ownFolders = @($InstallHome, $Staging, $PreviousStaging) | ForEach-Object { $_.TrimEnd('\') }
    function InOwnFolders([string] $path) { [bool]($ownFolders | Where-Object { $path -eq $_ -or $path.StartsWith($_ + '\', [StringComparison]::OrdinalIgnoreCase) }) }
    $cv = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
    # A fresh Windows 11 ships Microsoft Store "app execution aliases" (zero-byte reparse-point stubs under
    # %LOCALAPPDATA%\Microsoft\WindowsApps, e.g. python.exe) that only open the Store: nothing is installed.
    # They are recorded separately and do not count as development tools.
    $aliasDir = Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps'
    $tools = @(); $storeAliases = @()
    foreach ($t in 'python', 'py', 'node', 'npm', 'git', 'codex', 'code', 'cl', 'pip') {
        $c = Get-Command $t -ErrorAction SilentlyContinue
        if (-not $c -or -not $c.Source) { continue }
        $item = Get-Item -LiteralPath $c.Source -ErrorAction SilentlyContinue
        $isStoreAlias = ($c.Source -like (Join-Path $aliasDir '*')) -and $item -and ((($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) -or $item.Length -eq 0)
        if ($isStoreAlias) { $storeAliases += "$t -> $($c.Source) (Microsoft Store app execution alias, $($item.Length) bytes; nothing installed)" } else { $tools += "$t -> $($c.Source)" }
    }
    $dirs = foreach ($d in "$env:ProgramFiles\Python*", "${env:ProgramFiles(x86)}\Python*", "$env:ProgramFiles\nodejs", "$env:ProgramFiles\Git", "$env:ProgramFiles\Microsoft Visual Studio", "$env:LOCALAPPDATA\Programs\Python", "$env:LOCALAPPDATA\Programs\Microsoft VS Code", "$env:APPDATA\npm") { if (Test-Path $d) { $d } }
    $envFiles = @(Get-ChildItem -LiteralPath $env:USERPROFILE -Recurse -Force -Filter '.env*' -ErrorAction SilentlyContinue | Where-Object { -not ($jarvisExpected -and (InOwnFolders $_.FullName)) } | Select-Object -First 20 -ExpandProperty FullName)
    $cred = (cmdkey /list 2>$null | Out-String)
    $lic = Get-CimInstance SoftwareLicensingProduct -Filter "ApplicationID='55c92734-d682-4d71-983e-d6ec3f16059f' and PartialProductKey is not null" | Select-Object -First 1
    $wu = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings' -ErrorAction SilentlyContinue
    $programs = @(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*', 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*', 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue | Where-Object DisplayName | Select-Object DisplayName, DisplayVersion, Publisher | Sort-Object DisplayName)
    $services = @(Get-Service | Select-Object Name, Status, StartType | Sort-Object Name)
    # AMENDMENT-v2 section 6(f), the remaining negatives: JARVIS services, scheduled tasks, named pipes and folders;
    # global package folders; default PATH; and the sign-in state (local account, no signed-in online account).
    $jarvisServices = @(Get-Service | Where-Object { (MentionsJarvis $_.Name) -or (MentionsJarvis $_.DisplayName) } | ForEach-Object { $_.Name })
    $jarvisTasks = @(Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object { (MentionsJarvis $_.TaskName) -or (MentionsJarvis $_.TaskPath) } | ForEach-Object { "$($_.TaskPath)$($_.TaskName)" })
    $pipeNames = @(try { [IO.Directory]::GetFiles('\\.\pipe\') } catch { @(Get-ChildItem '\\.\pipe\' -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }) })
    $jarvisPipes = @($pipeNames | Where-Object { MentionsJarvis $_ })
    $accountNamedPipes = @($pipeNames | Where-Object { ($_ -match 'jarvis') -and -not (MentionsJarvis $_) })
    $jarvisDirs = @(foreach ($d in "$env:LOCALAPPDATA\JARVIS*", "$env:APPDATA\JARVIS*", "$env:ProgramData\JARVIS*", "$env:ProgramFiles\JARVIS*", "$env:USERPROFILE\JARVIS*") { Get-Item -Path $d -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName } })
    $globalPackages = @(foreach ($d in "$env:APPDATA\npm", "$env:APPDATA\Python", "$env:LOCALAPPDATA\pip", "$env:USERPROFILE\.cargo", "$env:USERPROFILE\.nuget") { if (Test-Path $d) { $d } })
    $nonDefaultPath = @($env:PATH -split ';' | Where-Object { $_ -and ($_ -notlike "$env:SystemRoot*") -and ($_.TrimEnd('\') -ne $aliasDir.TrimEnd('\')) })
    $localUser = Get-LocalUser -Name $env:USERNAME -ErrorAction SilentlyContinue
    $principalSource = if ($localUser) { "$($localUser.PrincipalSource)" } else { 'unknown' }
    $oneDrive = Get-ItemProperty 'HKCU:\Software\Microsoft\OneDrive\Accounts\Personal' -ErrorAction SilentlyContinue
    $os = Get-CimInstance Win32_OperatingSystem
    $credCount = ([regex]::Matches($cred, 'Target:')).Count
    $forOwner = @()
    if ($credCount -gt 0 -and -not (MentionsJarvis $cred)) { $forOwner += "credential-manager entries exist ($credCount); section 6(f) lists credential-manager entries under 'no secrets'; recorded for the owner's disposition, not failed by the script" }
    if ($principalSource -eq 'unknown') { $forOwner += 'the account principal source could not be read' }
    $data = [ordered]@{
        status = 'PASS'; at = (Now)
        os_caption = $os.Caption; os_architecture = $os.OSArchitecture
        edition = $cv.ProductName; display_version = $cv.DisplayVersion; build = "$($cv.CurrentBuildNumber).$($cv.UBR)"; edition_id = $cv.EditionID
        activation_license_status = if ($lic) { $lic.LicenseStatus } else { 'unknown' }
        hypervisor_present = (Get-CimInstance Win32_ComputerSystem).HypervisorPresent
        windows_update_pause_expiry = if ($wu) { $wu.PauseUpdatesExpiryTime } else { $null }
        account = "$env:USERDOMAIN\$env:USERNAME"; is_administrator = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        path = $env:PATH
        development_tools_on_path = @($tools); store_app_execution_aliases = @($storeAliases); development_tool_folders = @($dirs)
        jarvis_install_present = (Test-Path -LiteralPath $InstallHome); jarvis_processes = (Processes).Count
        env_files_in_profile = $envFiles; jarvis_credentials = (MentionsJarvis $cred); credential_entries = ([regex]::Matches($cred, 'Target:')).Count
        credential_targets = @([regex]::Matches($cred, 'Target:\s*(.+)') | ForEach-Object { $_.Groups[1].Value.Trim() })
        account_principal_source = $principalSource; onedrive_account_configured = [bool]($oneDrive -and $oneDrive.UserEmail)
        jarvis_services = $jarvisServices; jarvis_scheduled_tasks = $jarvisTasks; jarvis_named_pipes = $jarvisPipes; named_pipes_enumerated = $pipeNames.Count; jarvis_folders = $jarvisDirs
        pipes_named_after_the_account = $accountNamedPipes
        name_matching_note = "the account name '$env:USERNAME' and the computer name '$env:COMPUTERNAME' are removed from names before testing for 'jarvis'"
        global_package_folders = $globalPackages; non_default_path_entries = $nonDefaultPath
        owner_disposition_required = $forOwner
        installed_programs = $programs.Count; services = $services.Count
    }
    $recordName = if ($jarvisExpected) { 'C1-cleanliness' } else { 'B1-baseline' }
    $filePrefix = if ($jarvisExpected) { 'cleanliness' } else { 'baseline' }
    [IO.File]::WriteAllText((Join-Path $script:EvidenceDir "$filePrefix-programs.json"), ($programs | ConvertTo-Json -Depth 3), $Utf8)
    [IO.File]::WriteAllText((Join-Path $script:EvidenceDir "$filePrefix-services.json"), ($services | ConvertTo-Json -Depth 3), $Utf8)
    $jarvisDirsElsewhere = @($jarvisDirs | Where-Object { -not (InOwnFolders $_.TrimEnd('\')) })
    if ($jarvisExpected) {
        $data.jarvis_expected = $true; $data.jarvis_own_folders = $ownFolders; $data.jarvis_folders_elsewhere = $jarvisDirsElsewhere
        $data.note = 'JARVIS is installed: its install folder, package folder, processes and pipes are recorded and not counted; everything else is judged as at the baseline'
    }
    $problems = @()
    if ($tools) { $problems += 'development tools on PATH' }
    if ($dirs) { $problems += 'development tool folders present' }
    if ($jarvisExpected) {
        if (-not $data.jarvis_install_present) { $problems += 'JARVIS is not installed (the Cleanliness phase runs after the Install phase)' }
        if ($jarvisDirsElsewhere) { $problems += 'JARVIS folders outside the install and package folders' }
    } else {
        if ($data.jarvis_install_present) { $problems += 'JARVIS already installed' }
        if ($data.jarvis_processes) { $problems += 'JARVIS processes running' }
        if ($jarvisPipes) { $problems += 'JARVIS named pipes present' }
        if ($jarvisDirs) { $problems += 'JARVIS folders present' }
    }
    if ($envFiles) { $problems += '.env files in the profile' }
    if ($data.jarvis_credentials) { $problems += 'JARVIS credential entries' }
    if ($jarvisServices) { $problems += 'JARVIS services present' }
    if ($jarvisTasks) { $problems += 'JARVIS scheduled tasks present' }
    if ($globalPackages) { $problems += 'global package folders present' }
    if ($nonDefaultPath) { $problems += 'non-default PATH entries' }
    if ($principalSource -in 'MicrosoftAccount', 'AzureAD', 'ActiveDirectory') { $problems += "the account is not a local account ($principalSource)" }
    if ($data.onedrive_account_configured) { $problems += 'OneDrive is signed in to an online account' }
    if ($problems) { Fail $recordName $data ($problems -join '; ') }
    Record $recordName $data
}

# ---------------------------------------------------------------- Install
if ($Phase -eq 'Install' -or $Phase -eq 'All') {
    # I1 package identity: every payload file against the ISO manifest (when present), the zip against its release record.
    $record = Get-ChildItem -LiteralPath $Package -Filter 'JARVIS-*.release.json' | Select-Object -First 1
    if (-not $record) { Fail 'I1-package' @{} 'no JARVIS-<id>.release.json in the package folder' }
    $rel = Get-Content -LiteralPath $record.FullName -Raw | ConvertFrom-Json
    $zip = Join-Path $Package $rel.zip
    $t = [Diagnostics.Stopwatch]::StartNew(); $zipHash = Sha256 $zip
    $data = [ordered]@{ status = 'PASS'; release_id = $rel.release_id; commit = $rel.commit; zip = $rel.zip; zip_bytes = (Get-Item -LiteralPath $zip).Length; zip_sha256 = $zipHash; zip_matches_record = ($zipHash -eq $rel.zip_sha256); hash_seconds = [Math]::Round($t.Elapsed.TotalSeconds, 1) }
    $manifestPath = Join-Path $Package 'PAYLOAD-MANIFEST.json'
    if (Test-Path -LiteralPath $manifestPath) {
        $pm = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
        $bad = @(foreach ($f in $pm.files) { if ((Sha256 (Join-Path $Package $f.path)) -ne $f.sha256) { $f.path } })
        $data.payload_manifest_files = $pm.files.Count; $data.payload_mismatches = $bad
        if ($bad) { Fail 'I1-package' $data 'payload file hash mismatch' }
    }
    if (-not $data.zip_matches_record) { Fail 'I1-package' $data 'zip hash does not match its release record' }
    Record 'I1-package' $data

    # I2 extract to staging inside the profile.
    if (Test-Path -LiteralPath $Staging) { Remove-Item -LiteralPath $Staging -Recurse -Force }
    $t = [Diagnostics.Stopwatch]::StartNew()
    Expand-Archive -LiteralPath $zip -DestinationPath $Staging
    $inner = Get-ChildItem -LiteralPath $Staging -Directory | Select-Object -First 1
    Get-ChildItem -LiteralPath $inner.FullName -Force | Move-Item -Destination $Staging
    Remove-Item -LiteralPath $inner.FullName -Recurse -Force
    $data = [ordered]@{ status = 'PASS'; staging = $Staging; seconds = [Math]::Round($t.Elapsed.TotalSeconds, 1); files = (Get-ChildItem -LiteralPath $Staging -Recurse -File).Count; has_install_cmd = (Test-Path -LiteralPath (Join-Path $Staging 'install.cmd')) }
    if (-not $data.has_install_cmd) { Fail 'I2-extract' $data 'install.cmd missing after extraction' }
    Record 'I2-extract' $data

    # I3 install exactly as the owner would (install.cmd); stdin from nul so a failure's "pause" cannot hang.
    $t = [Diagnostics.Stopwatch]::StartNew()
    $installArgs = "--home `"$InstallHome`"" + $(if ($NoShortcuts) { ' --no-shortcuts' } else { '' })
    $out = cmd /c "`"$(Join-Path $Staging 'install.cmd')`" $installArgs < nul" 2>&1 | Out-String
    $result = $null; try { $result = $out | ConvertFrom-Json } catch {}
    $data = [ordered]@{ status = 'PASS'; seconds = [Math]::Round($t.Elapsed.TotalSeconds, 1); result = $result; raw = $(if ($result) { $null } else { $out.Substring(0, [Math]::Min(1500, $out.Length)) }) }
    if (-not $result -or $result.status -ne 'installed') { Fail 'I3-install' $data 'install.cmd did not report installed' }
    if ($result.release -ne $rel.release_id) { Fail 'I3-install' $data 'installed release id differs from the package record' }
    Record 'I3-install' $data

    # I4 installed files verified against the manifest; shortcuts present (VM) or deliberately absent (local).
    $v = Installer @('verify')
    $desk = Test-Path -LiteralPath (Join-Path ([Environment]::GetFolderPath('Desktop')) 'JARVIS.lnk'); $startup = Test-Path -LiteralPath (Join-Path ([Environment]::GetFolderPath('Startup')) 'JARVIS.lnk')
    $data = [ordered]@{ status = 'PASS'; verify = $v.status; desktop_shortcut = $desk; startup_shortcut = $startup; shortcuts_expected = (-not $NoShortcuts) }
    if ($v.status -ne 'verified') { Fail 'I4-verify' $data 'installed files do not verify' }
    if (-not $NoShortcuts -and -not ($desk -and $startup)) { Fail 'I4-verify' $data 'shortcuts missing' }
    Record 'I4-verify' $data

    # I5 first launch: Core startup, runtime identity, data in the canonical folder.
    $t = [Diagnostics.Stopwatch]::StartNew(); $how = Launch
    $up = WaitForCore 180
    $data = [ordered]@{ status = 'PASS'; launched_via = $how; core_ready = $up; seconds_to_ready = [Math]::Round($t.Elapsed.TotalSeconds, 1) }
    if (-not $up) { Fail 'I5-launch' $data 'Core not reachable within 180 s' }
    Start-Sleep -Seconds 3
    $state = Api '/api/state'
    $memo = 'Gate 17 memory: the test colour is teal'
    $null = Api '/api/item' @{ kind = 'memory'; body = $memo }
    $after = Api '/api/state'
    $data.installed_release = $state.updates.installed_release; $data.source_revision = $state.updates.source_revision
    $data.identity_matches_package = ($state.updates.installed_release -eq $rel.release_id)
    $data.memory_saved = [bool]($after.memory | Where-Object { $_.body -eq $memo })
    $data.database_in_home = (Test-Path -LiteralPath (Join-Path $InstallHome 'data\jarvis.sqlite3'))
    $data.processes = (Processes).Count
    $data.process_images_outside_install = @(Processes | Where-Object { $_.ExecutablePath -notlike (Join-Path $InstallHome 'releases\*') } | Select-Object -ExpandProperty ExecutablePath)
    if (-not $data.identity_matches_package) { Fail 'I5-launch' $data 'running Core does not report the package release id' }
    if (-not $data.memory_saved) { Fail 'I5-launch' $data 'memory not saved' }
    if (-not $data.database_in_home) { Fail 'I5-launch' $data 'database not in the canonical data folder' }
    Record 'I5-launch' $data

    # I6 duplicate-Core fencing: a second launch joins the running Core.
    $owner = Get-Content -LiteralPath (Join-Path $InstallHome 'data\core-owner.json') -Raw | ConvertFrom-Json
    $origin = (Link).origin; $null = Launch; Start-Sleep -Seconds 12
    $owner2 = Get-Content -LiteralPath (Join-Path $InstallHome 'data\core-owner.json') -Raw | ConvertFrom-Json
    $data = [ordered]@{ status = 'PASS'; core_pid_before = $owner.pid; core_pid_after = $owner2.pid; origin_unchanged = ((Link).origin -eq $origin); core_answers = $true; processes = (Processes).Count }
    try { $null = Api '/api/state' } catch { $data.core_answers = $false }
    if ($owner.pid -ne $owner2.pid -or -not $data.origin_unchanged -or -not $data.core_answers) { Fail 'I6-duplicate-core' $data 'a second launch did not join the existing Core' }
    Record 'I6-duplicate-core' $data

    # I7 local speech recognition offline (bundled model, synthetic speech, network blocked by the check itself).
    $r = Release; $t = [Diagnostics.Stopwatch]::StartNew()
    $voice = & $r.python (Join-Path $r.app 'check_voice_offline.py') 2>&1 | Out-String
    $data = [ordered]@{ status = 'PASS'; exit_code = $LASTEXITCODE; seconds = [Math]::Round($t.Elapsed.TotalSeconds, 1); output = $voice.Substring(0, [Math]::Min(1200, $voice.Length)) }
    if ($LASTEXITCODE -ne 0) { Fail 'I7-local-stt' $data 'offline speech check failed' }
    Record 'I7-local-stt' $data

    # I8 application restart: stop, verify after use, start again, data and identity intact.
    $stop = StopJarvis
    $v = Installer @('verify')
    $t = [Diagnostics.Stopwatch]::StartNew(); $null = Launch; $up = WaitForCore 180
    $state = $(if ($up) { Api '/api/state' } else { $null })
    $data = [ordered]@{ status = 'PASS'; stop = $stop; verify_after_use = $v.status; restarted = $up; seconds_to_ready = [Math]::Round($t.Elapsed.TotalSeconds, 1)
                        memory_persisted = [bool]($state.memory | Where-Object { $_.body -eq $memo }); identity_same = ($state.updates.installed_release -eq $rel.release_id) }
    if (-not $stop.core_stopped_on_request -or $v.status -ne 'verified' -or -not $up -or -not $data.memory_persisted -or -not $data.identity_same) { Fail 'I8-restart' $data 'restart did not pass every check' }
    Record 'I8-restart' $data
    Write-Host 'JARVIS is running. On the VM the next phase is AfterRestart, after quitting JARVIS from the tray and restarting Windows.'
}

# ---------------------------------------------------------------- After a Windows restart (Startup shortcut)
if ($Phase -eq 'AfterRestart') {
    $t = [Diagnostics.Stopwatch]::StartNew(); $up = WaitForCore 240
    $state = $(if ($up) { Api '/api/state' } else { $null })
    $boot = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
    $data = [ordered]@{ status = 'PASS'; last_boot = $boot.ToUniversalTime().ToString('o'); started_by_login_launch = $up; seconds_waited = [Math]::Round($t.Elapsed.TotalSeconds, 1)
                        installed_release = $state.updates.installed_release; memory_persisted = [bool]($state.memory | Where-Object { $_.body -like 'Gate 17 memory:*' }); processes = (Processes).Count }
    if (-not $up -or -not $data.memory_persisted) { Fail 'R1-after-restart' $data 'JARVIS did not come up after the Windows restart with its data' }
    Record 'R1-after-restart' $data
}

# ---------------------------------------------------------------- Uninstall, reinstall
if ($Phase -eq 'Uninstall' -or $Phase -eq 'All') {
    $logs = Join-Path $InstallHome 'data\logs'
    if (Test-Path -LiteralPath $logs) { Copy-Item -LiteralPath $logs -Destination (Join-Path $script:EvidenceDir 'core-logs') -Recurse -Force }
    $u = Installer @('uninstall')
    $leftover = @(Get-ChildItem -LiteralPath (Join-Path $InstallHome 'releases') -Recurse -File -ErrorAction SilentlyContinue).Count
    $data = [ordered]@{ status = 'PASS'; result = $u.status; output = $u.output; program_files_removed = $u.program_files_removed; kept = $u.kept; leftover_program_files = $leftover; processes = (Processes).Count
                        data_kept = (Test-Path -LiteralPath (Join-Path $InstallHome 'data\jarvis.sqlite3')); config_kept = (Test-Path -LiteralPath (Join-Path $InstallHome 'config\personality.txt'))
                        desktop_shortcut_gone = -not (Test-Path -LiteralPath (Join-Path ([Environment]::GetFolderPath('Desktop')) 'JARVIS.lnk')); startup_shortcut_gone = -not (Test-Path -LiteralPath (Join-Path ([Environment]::GetFolderPath('Startup')) 'JARVIS.lnk')) }
    if ($u.status -ne 'uninstalled' -or $leftover -or $data.processes -or -not $data.data_kept -or -not $data.desktop_shortcut_gone -or -not $data.startup_shortcut_gone) { Fail 'U1-uninstall' $data 'uninstall left program files, processes or shortcuts, or removed data' }
    Record 'U1-uninstall' $data

    $python = Join-Path $Staging 'release\python\python.exe'
    $out = & $python (Join-Path $Staging 'installer.py') install --package $Staging --home $InstallHome $(if ($NoShortcuts) { '--no-shortcuts' }) 2>&1 | Out-String
    $re = $null; try { $re = $out | ConvertFrom-Json } catch {}
    $null = Launch; $up = WaitForCore 180
    $state = $(if ($up) { Api '/api/state' } else { $null })
    $v = Installer @('verify')
    $data = [ordered]@{ status = 'PASS'; reinstall = $re.status; release = $re.release; core_ready = $up; memory_restored = [bool]($state.memory | Where-Object { $_.body -like 'Gate 17 memory:*' }); verify = $v.status }
    if ($re.status -ne 'installed' -or -not $up -or -not $data.memory_restored -or $v.status -ne 'verified') { Fail 'U2-reinstall' $data 'reinstall did not bring JARVIS back with its data' }
    Record 'U2-reinstall' $data
    $data = [ordered]@{ status = 'PASS'; stop = (StopJarvis) }
    Record 'U3-final-stop' $data
}

# ---------------------------------------------------------------- Gate 19: previous build, update, rollback, update again
# Runs after the Uninstall phase, in the same Windows session: -Package is the build under acceptance (already
# extracted to the staging folder by the Install phase), -PreviousPackage the build before it. Each installer call
# reports its own per-phase seconds (AMENDMENT-v3 D9: the timing bound is set from these measurements).
if ($Phase -eq 'Update' -or $Phase -eq 'Interrupt') {
    function PackageRecord($folder) {
        $record = Get-ChildItem -LiteralPath $folder -Filter 'JARVIS-*.release.json' | Select-Object -First 1
        if ($record) { Get-Content -LiteralPath $record.FullName -Raw | ConvertFrom-Json }
    }
    function RunInstaller($stagingFolder, [string[]] $arguments) {
        # installer.py of the named extracted package, run with that package's own Python (never the installed one).
        $out = & (Join-Path $stagingFolder 'release\python\python.exe') (Join-Path $stagingFolder 'installer.py') @arguments --home $InstallHome $(if ($NoShortcuts) { '--no-shortcuts' }) 2>&1 | Out-String
        try { $out | ConvertFrom-Json } catch { @{ status = 'error'; output = $out.Substring(0, [Math]::Min(1500, $out.Length)) } }
    }
    function RunningState($expectedId) {
        # Start JARVIS, wait for the Core, and report identity, data and which release folder the processes run from.
        $t = [Diagnostics.Stopwatch]::StartNew(); $null = Launch; $up = WaitForCore 180
        $state = $(if ($up) { Start-Sleep -Seconds 3; Api '/api/state' } else { $null })
        $paths = @(Processes | Select-Object -ExpandProperty ExecutablePath)
        $prefix = Join-Path $InstallHome "releases\$expectedId\"
        [ordered]@{
            core_ready = $up; seconds_to_ready = [Math]::Round($t.Elapsed.TotalSeconds, 1)
            installed_release = $state.updates.installed_release; identity_matches = ($state.updates.installed_release -eq $expectedId)
            gate17_memory = [bool]($state.memory | Where-Object { $_.body -like 'Gate 17 memory:*' })
            gate19_memory = [bool]($state.memory | Where-Object { $_.body -like 'Gate 19 memory:*' })
            processes = $paths.Count; processes_from_other_releases = @($paths | Where-Object { -not $_.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase) })
        }
    }
    function Healthy($run) { $run.core_ready -and $run.identity_matches -and $run.gate19_memory -and -not $run.processes_from_other_releases }
    function ProcessesLeft {
        # The installer ends leftover JARVIS processes as it returns; give Windows up to 15 s to remove them before counting.
        $deadline = (Get-Date).AddSeconds(15)
        while ((Processes).Count -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 500 }
        (Processes).Count
    }
}
if ($Phase -eq 'Update') {
    # G1 both packages identified; the build under acceptance is the installed one and its extracted package is present.
    $data = [ordered]@{ status = 'PASS' }
    if (-not $PreviousPackage -or -not (Test-Path -LiteralPath $PreviousPackage)) { Fail 'G1-packages' $data 'the folder of the previous build was not given or does not exist' }
    $final = PackageRecord $Package; $prev = PackageRecord $PreviousPackage
    if (-not $final -or -not $prev) { Fail 'G1-packages' $data 'a package folder has no JARVIS-<id>.release.json' }
    $prevZip = Join-Path $PreviousPackage $prev.zip
    $t = [Diagnostics.Stopwatch]::StartNew(); $prevHash = Sha256 $prevZip
    $stagedId = $null; try { $stagedId = (Get-Content -LiteralPath (Join-Path $Staging 'release\manifest.json') -Raw | ConvertFrom-Json).release_id } catch {}
    $current = $null; try { $current = (Get-Content -LiteralPath (Join-Path $InstallHome 'current.json') -Raw | ConvertFrom-Json).release } catch {}
    $data = [ordered]@{ status = 'PASS'; release_under_acceptance = $final.release_id; previous_release = $prev.release_id; previous_zip = $prev.zip; previous_zip_bytes = (Get-Item -LiteralPath $prevZip).Length
                        previous_zip_sha256 = $prevHash; previous_zip_matches_record = ($prevHash -eq $prev.zip_sha256); hash_seconds = [Math]::Round($t.Elapsed.TotalSeconds, 1)
                        extracted_package = $stagedId; installed_before = $current; processes_before = (Processes).Count }
    $manifestPath = Join-Path $PreviousPackage 'PAYLOAD-MANIFEST.json'
    if (Test-Path -LiteralPath $manifestPath) {
        $pm = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
        $bad = @(foreach ($f in $pm.files) { if ((Sha256 (Join-Path $PreviousPackage $f.path)) -ne $f.sha256) { $f.path } })
        $data.payload_manifest_files = $pm.files.Count; $data.payload_mismatches = $bad
        if ($bad) { Fail 'G1-packages' $data 'payload file hash mismatch on the previous build''s disc' }
    }
    if (-not $data.previous_zip_matches_record) { Fail 'G1-packages' $data 'the previous build''s zip does not match its release record' }
    if ($final.release_id -eq $prev.release_id) { Fail 'G1-packages' $data 'both package folders hold the same build' }
    if ($stagedId -ne $final.release_id) { Fail 'G1-packages' $data 'the package extracted by the Install phase is missing or is a different build' }
    if ($current -ne $final.release_id) { Fail 'G1-packages' $data 'the build under acceptance is not the installed one; this phase runs after the Uninstall phase' }
    Record 'G1-packages' $data

    # G2 extract the previous build next to the first package.
    if (Test-Path -LiteralPath $PreviousStaging) { Remove-Item -LiteralPath $PreviousStaging -Recurse -Force }
    $t = [Diagnostics.Stopwatch]::StartNew()
    Expand-Archive -LiteralPath $prevZip -DestinationPath $PreviousStaging
    $inner = Get-ChildItem -LiteralPath $PreviousStaging -Directory | Select-Object -First 1
    Get-ChildItem -LiteralPath $inner.FullName -Force | Move-Item -Destination $PreviousStaging
    Remove-Item -LiteralPath $inner.FullName -Recurse -Force
    $data = [ordered]@{ status = 'PASS'; staging = $PreviousStaging; seconds = [Math]::Round($t.Elapsed.TotalSeconds, 1); files = (Get-ChildItem -LiteralPath $PreviousStaging -Recurse -File).Count; has_installer = (Test-Path -LiteralPath (Join-Path $PreviousStaging 'installer.py')) }
    if (-not $data.has_installer) { Fail 'G2-extract-previous' $data 'installer.py missing after extraction' }
    Record 'G2-extract-previous' $data

    # G3 starting point: the previous build installed over the kept data, running, with a new memory written under it.
    $u = RunInstaller $Staging @('uninstall')
    $in = RunInstaller $PreviousStaging @('install', '--package', $PreviousStaging)
    $run = RunningState $prev.release_id
    $memo = "Gate 19 memory: written under $($prev.release_id)"
    if ($run.core_ready) { $null = Api '/api/item' @{ kind = 'memory'; body = $memo }; $run.gate19_memory = [bool]((Api '/api/state').memory | Where-Object { $_.body -eq $memo }) }
    $data = [ordered]@{ status = 'PASS'; uninstall = $u.status; install = $in.status; release = $in.release; installer_seconds = $in.seconds; output = $in.output; running = $run }
    if ($u.status -ne 'uninstalled' -or $in.status -ne 'installed' -or $in.release -ne $prev.release_id -or -not (Healthy $run)) { Fail 'G3-previous-installed' $data 'the previous build did not install and run over the kept data' }
    Record 'G3-previous-installed' $data

    # G4 update to the build under acceptance while the previous build is running.
    $t = [Diagnostics.Stopwatch]::StartNew(); $up = RunInstaller $Staging @('install', '--package', $Staging); $wall = [Math]::Round($t.Elapsed.TotalSeconds, 1)
    $left = ProcessesLeft; $v = RunInstaller $Staging @('verify'); $st = RunInstaller $Staging @('status')
    $run = RunningState $final.release_id
    $data = [ordered]@{ status = 'PASS'; result = $up.status; release = $up.release; previous = $up.previous; installer_seconds = $up.seconds; wall_seconds = $wall; output = $up.output
                        processes_left_after_update = $left; verify = $v.status; verified_release = $v.release; current = $st.current; releases = $st.releases; running = $run }
    if ($up.status -ne 'installed' -or $up.release -ne $final.release_id -or $up.previous -ne $prev.release_id -or $left -or $v.status -ne 'verified' -or $v.release -ne $final.release_id -or $st.current.release -ne $final.release_id -or -not (Healthy $run)) { Fail 'G4-update' $data 'the update did not pass every check' }
    Record 'G4-update' $data

    # G5 roll back to the previous build while the updated build is running.
    $t = [Diagnostics.Stopwatch]::StartNew(); $rb = RunInstaller $Staging @('rollback'); $wall = [Math]::Round($t.Elapsed.TotalSeconds, 1)
    $left = ProcessesLeft; $v = RunInstaller $Staging @('verify')
    $run = RunningState $prev.release_id
    $data = [ordered]@{ status = 'PASS'; result = $rb.status; release = $rb.release; previous = $rb.previous; wall_seconds = $wall; output = $rb.output
                        processes_left_after_rollback = $left; verify = $v.status; verified_release = $v.release; running = $run }
    if ($rb.status -ne 'rolled_back' -or $rb.release -ne $prev.release_id -or $left -or $v.status -ne 'verified' -or $v.release -ne $prev.release_id -or -not (Healthy $run)) { Fail 'G5-rollback' $data 'the rollback did not pass every check' }
    Record 'G5-rollback' $data

    # G6 update again (both builds are now present), so the machine ends on the build under acceptance, stopped.
    $t = [Diagnostics.Stopwatch]::StartNew(); $up = RunInstaller $Staging @('install', '--package', $Staging); $wall = [Math]::Round($t.Elapsed.TotalSeconds, 1)
    $left = ProcessesLeft; $v = RunInstaller $Staging @('verify')
    $run = RunningState $final.release_id
    $stop = StopJarvis; $st = RunInstaller $Staging @('status')
    $logs = Join-Path $InstallHome 'data\logs'
    if (Test-Path -LiteralPath $logs) { Copy-Item -LiteralPath $logs -Destination (Join-Path $script:EvidenceDir 'core-logs') -Recurse -Force }
    $data = [ordered]@{ status = 'PASS'; result = $up.status; release = $up.release; previous = $up.previous; installer_seconds = $up.seconds; wall_seconds = $wall; output = $up.output
                        processes_left_after_update = $left; verify = $v.status; verified_release = $v.release; running = $run; final_stop = $stop; current = $st.current; releases = $st.releases }
    if ($up.status -ne 'installed' -or $up.release -ne $final.release_id -or $left -or $v.status -ne 'verified' -or $v.release -ne $final.release_id -or -not (Healthy $run) -or -not $stop.core_stopped_on_request -or $stop.processes_now -or $st.current.release -ne $final.release_id) { Fail 'G6-update-again' $data 'the second update or the final stop did not pass every check' }
    Record 'G6-update-again' $data
}

# ---------------------------------------------------------------- Stage 7: an update interrupted while it is copying
# Runs after the Update phase, in the same Windows session (both packages are extracted, the machine is on the build
# under acceptance, stopped). The program is removed (data kept) and the previous build installed fresh, so that the
# update really has to copy the new release; the installer is killed part-way through that copy; the running
# previous build must be unharmed; the update is then run again and must finish cleanly.
if ($Phase -eq 'Interrupt') {
    $data = [ordered]@{ status = 'PASS' }
    if (-not $PreviousPackage -or -not (Test-Path -LiteralPath $PreviousPackage)) { Fail 'X0-starting-point' $data 'the folder of the previous build was not given or does not exist' }
    $final = PackageRecord $Package; $prev = PackageRecord $PreviousPackage
    if (-not $final -or -not $prev) { Fail 'X0-starting-point' $data 'a package folder has no JARVIS-<id>.release.json' }
    $manifest = $null; try { $manifest = Get-Content -LiteralPath (Join-Path $Staging 'release\manifest.json') -Raw | ConvertFrom-Json } catch {}
    $prevStagedId = $null; try { $prevStagedId = (Get-Content -LiteralPath (Join-Path $PreviousStaging 'release\manifest.json') -Raw | ConvertFrom-Json).release_id } catch {}
    $current = $null; try { $current = (Get-Content -LiteralPath (Join-Path $InstallHome 'current.json') -Raw | ConvertFrom-Json).release } catch {}
    $total = @($manifest.files).Count
    $data = [ordered]@{ status = 'PASS'; release_under_acceptance = $final.release_id; previous_release = $prev.release_id; extracted_package = $manifest.release_id; extracted_previous = $prevStagedId
                        release_files = $total; installed_before = $current; processes_before = (Processes).Count }
    if ($manifest.release_id -ne $final.release_id -or $prevStagedId -ne $prev.release_id) { Fail 'X0-starting-point' $data 'the packages extracted by the Install and Update phases are missing or are different builds' }
    if ($data.processes_before) { Fail 'X0-starting-point' $data 'JARVIS is running; this phase starts from a stopped install' }
    Record 'X0-starting-point' $data

    # X1 the previous build installed fresh over the kept data and running; the new release is not on the machine.
    $newDir = Join-Path $InstallHome "releases\$($final.release_id)"; $incoming = Join-Path $InstallHome "releases\.incoming-$($final.release_id)"
    $u = RunInstaller $Staging @('uninstall')
    $in = RunInstaller $PreviousStaging @('install', '--package', $PreviousStaging)
    $run = RunningState $prev.release_id
    $data = [ordered]@{ status = 'PASS'; uninstall = $u.status; install = $in.status; release = $in.release; installer_seconds = $in.seconds; output = $in.output; running = $run
                        new_release_present = (Test-Path -LiteralPath $newDir) }
    if ($u.status -ne 'uninstalled' -or $in.status -ne 'installed' -or $in.release -ne $prev.release_id -or -not (Healthy $run) -or $data.new_release_present) { Fail 'X1-previous-running' $data 'the previous build did not install fresh and run over the kept data' }
    Record 'X1-previous-running' $data

    # X2 start the update and kill the installer while it is copying the new release.
    $python = Join-Path $Staging 'release\python\python.exe'
    $arguments = @(('"' + (Join-Path $Staging 'installer.py') + '"'), 'install', '--package', ('"' + $Staging + '"'), '--home', ('"' + $InstallHome + '"'))
    if ($NoShortcuts) { $arguments += '--no-shortcuts' }
    $threshold = [Math]::Max(200, [int]($total * 0.3)); $copied = 0
    $t = [Diagnostics.Stopwatch]::StartNew()
    $proc = Start-Process -FilePath $python -ArgumentList $arguments -PassThru -WindowStyle Hidden
    $deadline = (Get-Date).AddSeconds(900)
    while (-not $proc.HasExited -and (Get-Date) -lt $deadline) {
        if (Test-Path -LiteralPath $incoming) {
            $copied = @(Get-ChildItem -LiteralPath $incoming -Recurse -File -Force -ErrorAction SilentlyContinue).Count
            if ($copied -ge $threshold) { break }
        }
        Start-Sleep -Milliseconds 250
    }
    $finishedByItself = $proc.HasExited; $secondsToKill = [Math]::Round($t.Elapsed.TotalSeconds, 1)
    if (-not $finishedByItself) { cmd /c "taskkill /F /T /PID $($proc.Id) >nul 2>&1"; $null = $proc.WaitForExit(60000) }
    Start-Sleep -Seconds 3
    $partial = $(if (Test-Path -LiteralPath $incoming) { @(Get-ChildItem -LiteralPath $incoming -Recurse -File -Force -ErrorAction SilentlyContinue).Count } else { 0 })
    $st = RunInstaller $PreviousStaging @('status'); $v = RunInstaller $PreviousStaging @('verify')
    $answers = $true; $state = $null; try { $state = Api '/api/state' } catch { $answers = $false }
    $paths = @(Processes | Select-Object -ExpandProperty ExecutablePath); $prefix = Join-Path $InstallHome "releases\$($prev.release_id)\"
    $data = [ordered]@{ status = 'PASS'; installer_pid = $proc.Id; installer_killed = (-not $finishedByItself); seconds_until_kill = $secondsToKill; kill_threshold_files = $threshold
                        files_copied_when_killed = $partial; of_total = $total; incoming_folder_left = (Test-Path -LiteralPath $incoming); new_release_folder_exists = (Test-Path -LiteralPath $newDir)
                        current = $st.current.release; verify = $v.status; verified_release = $v.release
                        previous_build_processes = $paths.Count; processes_from_other_releases = @($paths | Where-Object { -not $_.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase) })
                        core_answers = $answers; installed_release = $state.updates.installed_release
                        gate17_memory = [bool]($state.memory | Where-Object { $_.body -like 'Gate 17 memory:*' }); gate19_memory = [bool]($state.memory | Where-Object { $_.body -like 'Gate 19 memory:*' }) }
    if ($finishedByItself) { Fail 'X2-killed-mid-copy' $data 'the installer finished before it could be interrupted' }
    if ($partial -lt 1 -or $partial -ge $total) { Fail 'X2-killed-mid-copy' $data 'the installer was not interrupted in the middle of the copy' }
    if ($st.current.release -ne $prev.release_id -or $v.status -ne 'verified' -or $v.release -ne $prev.release_id -or $data.new_release_folder_exists) { Fail 'X2-killed-mid-copy' $data 'the installed build is no longer the intact previous build' }
    if (-not $paths.Count -or $data.processes_from_other_releases -or -not $answers -or $state.updates.installed_release -ne $prev.release_id -or -not $data.gate17_memory -or -not $data.gate19_memory) { Fail 'X2-killed-mid-copy' $data 'the running JARVIS was harmed by the interrupted update' }
    Record 'X2-killed-mid-copy' $data

    # X3 run the update again: it must clear the leftovers and finish; the machine ends on the build under acceptance, stopped.
    $t = [Diagnostics.Stopwatch]::StartNew(); $up = RunInstaller $Staging @('install', '--package', $Staging); $wall = [Math]::Round($t.Elapsed.TotalSeconds, 1)
    $left = ProcessesLeft; $v = RunInstaller $Staging @('verify')
    $run = RunningState $final.release_id
    $stop = StopJarvis; $st = RunInstaller $Staging @('status')
    $logs = Join-Path $InstallHome 'data\logs'
    if (Test-Path -LiteralPath $logs) { Copy-Item -LiteralPath $logs -Destination (Join-Path $script:EvidenceDir 'core-logs') -Recurse -Force }
    $data = [ordered]@{ status = 'PASS'; result = $up.status; release = $up.release; previous = $up.previous; installer_seconds = $up.seconds; wall_seconds = $wall; output = $up.output
                        incoming_folder_left = (Test-Path -LiteralPath $incoming); processes_left_after_update = $left; verify = $v.status; verified_release = $v.release
                        running = $run; final_stop = $stop; current = $st.current; releases = $st.releases }
    if ($up.status -ne 'installed' -or $up.release -ne $final.release_id -or $up.previous -ne $prev.release_id -or $data.incoming_folder_left -or $left -or $v.status -ne 'verified' -or $v.release -ne $final.release_id -or -not (Healthy $run) -or -not $stop.core_stopped_on_request -or $stop.processes_now -or $st.current.release -ne $final.release_id) { Fail 'X3-update-after-interruption' $data 'the update run again after the interruption did not pass every check' }
    Record 'X3-update-after-interruption' $data
}

Finish 'PASS'
