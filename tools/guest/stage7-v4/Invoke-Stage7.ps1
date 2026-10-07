<#
.SYNOPSIS
Stage 7 (packaged-application acceptance) and the standard pre-update check, run INSIDE the acceptance machine.
A copy of Invoke-Gate17.ps1 as used for Stage 6 Gates 17 and 19 (that file is evidence and stays unchanged), with
one added phase, Interrupt: an update killed while it is copying, then run again. Rehearsed locally on D: first.
Version 4 (tools\guest\stage7-v4; for 1.0.17, the first release that is its own app, docs\OWN-APP-PLAN.md 3.6):
the version 3 file with the install and uninstall done the way the owner does them from 1.0.17 on. The disc carries
JARVIS-Setup-<id>.exe with its record beside the zip. The Install phase checks the Setup against its record, runs it
silently (it unpacks the package into the staging folder and runs the package's own installer: the same engine as
before), and checks the entry in Settings > Apps > Installed apps; a launch without a shortcut starts the release's own
JARVIS.exe (an older release still its JARVIS.ps1); the shortcuts must point at JARVIS.exe. The Uninstall phase runs
the entry's own uninstaller (program removed, data kept, package folder and entry gone) and reinstalls from the Setup.
The Update phase gets one more step, G7: back on the previous build and running, one update through the Setup. The
update, rollback, update-again and interrupted-update steps run on the package's installer exactly as in version 3.
Version 3 (tools\guest\stage7-v3): the version 2 file with one change, found by the 1.0.15 sandbox rehearsal: a run
never writes into another run's folder (two phases that start within the same second got the same folder name).
The driver Invoke-Stage7Pass.ps1 is where version 3 otherwise differs.
Version 2 (tools\guest\stage7-v2; the 1.0.11 copy in tools\guest stays unchanged): E0 also records the Windows
build (CurrentBuildNumber.UBR), its display version and whether the account is in Administrators.

Runs on a fresh Windows 11 Home with nothing installed (Windows PowerShell 5.1 only). The
release carries its own Python, Electron and models, so no prerequisite is installed. Every
step writes a JSON record to the evidence folder; the first failure stops the run (no silent
retry). Nothing here reads or writes outside the package, the install home, the staging
folder and the evidence folder. There are no secrets on the machine; none are created.

.PARAMETER Package   Folder holding JARVIS-<id>.zip, JARVIS-<id>.release.json, JARVIS-Setup-<id>.exe and
                     JARVIS-Setup-<id>.setup.json (the mounted ISO root).
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
# Version 3: one folder per run, never another run's. The driver starts the next phase the moment the last one has
# ended, and a phase whose checks are instant (AfterRestart with JARVIS already up) ends within the same second, so
# the next phase got the same folder name and wrote its records over the first one's (seen in the 1.0.15 sandbox
# rehearsal: the after-restart run's SUMMARY was replaced by the uninstall run's, and the driver then ran the
# after-restart phase again). A run whose folder already exists waits for a free second.
while (Test-Path -LiteralPath $script:EvidenceDir) {
    Start-Sleep -Seconds 1
    $script:Started = Get-Date
    $script:EvidenceDir = Join-Path $Evidence ("$Gate-" + $script:Started.ToUniversalTime().ToString('yyyyMMdd-HHmmss'))
}
New-Item -ItemType Directory -Path $script:EvidenceDir -Force | Out-Null
$script:Summary = New-Object Collections.ArrayList
$PreviousStaging = "$Staging-previous"
$Utf8 = New-Object Text.UTF8Encoding $false
# Version 4: the Setup's own defaults. On the VM both are in use and the Setup gets no folder switch at all, exactly as
# the owner's double-click; a sandbox rehearsal (another home or staging folder, no shortcuts) adds the matching switch.
$DefaultHome = Join-Path $env:LOCALAPPDATA 'JARVIS'
$DefaultStaging = Join-Path $env:LOCALAPPDATA 'JARVIS-package'
# A sandbox (another install home) gets /HOME, and the Setup then registers as "JARVIS (sandbox)" under its own
# application id, so a rehearsal never touches the entry of the real JARVIS on the build PC. The two ids come from
# the Setup's record (written by the tool that built it); these are the values of the 1.0.17 template as a fallback.
$Sandbox = ($InstallHome.TrimEnd('\') -ne $DefaultHome.TrimEnd('\'))
$script:SetupRecord = $null
$script:AppIds = @{ real = '{DC2C8033-1BBF-5E1C-99A0-BE0E70DC9937}'; sandbox = '{7A3F1C52-9E4B-4D16-8C0D-2B5E6F7A9D31}' }
$ExpectedEntryName = $(if ($Sandbox) { 'JARVIS (sandbox)' } else { 'JARVIS' })

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
# Runs a program and returns everything it printed, error output included. Version 2: under 'Stop', Windows
# PowerShell 5.1 turns any line a program writes to its error output into a fatal error, so a Python error message
# ended the whole phase without a record; here it becomes part of the output and the step records a FAIL with it.
function Capture([scriptblock] $command) { $ErrorActionPreference = 'Continue'; (& $command 2>&1 | ForEach-Object { "$_" }) -join "`n" }
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
    # Version 4: without a shortcut, the current release's own program (JARVIS.exe, from 1.0.17 on), started with no
    # arguments as a double-click would. An older release (the previous build in the update phases) has no program
    # file and keeps its JARVIS.ps1, which the installer writes for it.
    $program = $null; try { $program = Join-Path (Join-Path $InstallHome ('releases\' + (Release).id)) 'electron\JARVIS.exe' } catch {}
    if ($program -and (Test-Path -LiteralPath $program)) { Start-Process -FilePath $program -WorkingDirectory (Split-Path -Parent $program); return 'JARVIS.exe' }
    Start-Process powershell -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $InstallHome 'JARVIS.ps1') -WindowStyle Hidden
    'JARVIS.ps1'
}
function ShortcutTarget($path) {
    # Where a shortcut points (version 4: the shortcuts must point at the release's JARVIS.exe).
    try { $shell = New-Object -ComObject WScript.Shell; $link = $shell.CreateShortcut($path); "$($link.TargetPath)" } catch { "(unreadable: $_)" }
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
    $out = Capture { & $python (Join-Path $Staging 'installer.py') @arguments --home $InstallHome $(if ($NoShortcuts) { '--no-shortcuts' }) }
    if ([string]::IsNullOrWhiteSpace($out)) { return @{ status = 'error'; output = '(no output)' } }
    try { $out | ConvertFrom-Json } catch { @{ status = 'error'; output = $out.Substring(0, [Math]::Min(1500, $out.Length)) } }
}
function PackageRecord($folder) {
    $record = Get-ChildItem -LiteralPath $folder -Filter 'JARVIS-*.release.json' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($record) { Get-Content -LiteralPath $record.FullName -Raw | ConvertFrom-Json }
}
# ---- Version 4: the Setup, the Installed-apps entry and the uninstaller (docs\OWN-APP-PLAN.md 3.4) ----
# The Setup beside the zip on the disc, with its record (JARVIS-Setup-<id>.setup.json, written by the tool that built it).
function SetupFile($folder, $releaseId) {
    $exe = Join-Path $folder "JARVIS-Setup-$releaseId.exe"; $record = Join-Path $folder "JARVIS-Setup-$releaseId.setup.json"
    if (-not (Test-Path -LiteralPath $exe) -or -not (Test-Path -LiteralPath $record)) { return $null }
    $script:SetupRecord = Get-Content -LiteralPath $record -Raw | ConvertFrom-Json
    if ($script:SetupRecord.app_id) { $script:AppIds.real = "$($script:SetupRecord.app_id)" }
    if ($script:SetupRecord.sandbox_app_id) { $script:AppIds.sandbox = "$($script:SetupRecord.sandbox_app_id)" }
    @{ exe = $exe; record = $script:SetupRecord }
}
# The registry key of the Installed-apps entry this run's Setup writes (the sandbox id in a sandbox).
function EntryKey { 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\' + $(if ($Sandbox) { $script:AppIds.sandbox } else { $script:AppIds.real }) + '_is1' }
# The word the installer's answer must carry about the real shortcuts (installer.py's own evidence line): on the VM
# "written" by an install and "removed" by the uninstall; in a sandbox always "withheld" (the home is not the PC's
# own install home), whatever the switches say; --no-shortcuts on the PC's own home would say "skipped".
function ShortcutWord([string] $action) {
    if ($Sandbox) { return 'withheld*' }
    if ($NoShortcuts) { return 'skipped*' }
    if ($action -eq 'uninstall') { 'removed' } else { 'written' }
}
# Waits for a Setup or uninstaller process, saying every half minute that it is still running and how many files the
# package folder holds (the Setup's unpack of about 1.2 GB plus the installer's work can take a quarter of an hour in
# the VM, and the owner's rule is "15 minutes without progress: tell Claude before any reset").
function WaitSaying($process, [string] $what) {
    $t = [Diagnostics.Stopwatch]::StartNew(); $said = 0
    while (-not $process.HasExited) {
        Start-Sleep -Seconds 2
        if ($t.Elapsed.TotalSeconds - $said -ge 30) {
            $said = [Math]::Floor($t.Elapsed.TotalSeconds)
            $files = @(Get-ChildItem -LiteralPath $Staging -Recurse -File -ErrorAction SilentlyContinue).Count
            Write-Host ("    {0} still running: {1} s, {2:N0} files in the package folder" -f $what, $said, $files)
        }
    }
    [Math]::Round($t.Elapsed.TotalSeconds, 1)
}
# Runs the Setup silently: it unpacks the package into the staging folder and runs the package's own installer
# (install when nothing is installed, update when an older release is current, reinstall when this one is), the
# engine every earlier check proved. The installer's JSON answer is read from <staging>\setup-result.json; the
# Setup's own log goes into this run's records. On the VM only the silent switches and the log are given: the home
# and the package folder are the Setup's defaults, as for the owner's double-click. A sandbox (another home or
# staging folder, -NoShortcuts) adds /HOME, /DIR and /NOSHORTCUTS; the installer itself also withholds the real
# shortcuts from any home that is not the PC's own install home.
function RunSetup([string] $setup, [string] $name) {
    $log = Join-Path $script:EvidenceDir "setup-$name.log"
    $arguments = @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', ('/LOG="' + $log + '"'))
    if ($Staging.TrimEnd('\') -ne $DefaultStaging.TrimEnd('\')) { $arguments += ('/DIR="' + $Staging.TrimEnd('\') + '"') }
    if ($InstallHome.TrimEnd('\') -ne $DefaultHome.TrimEnd('\')) { $arguments += ('/HOME="' + $InstallHome.TrimEnd('\') + '"') }
    if ($NoShortcuts) { $arguments += '/NOSHORTCUTS' }
    $resultFile = Join-Path $Staging 'setup-result.json'
    if (Test-Path -LiteralPath $resultFile) { Remove-Item -LiteralPath $resultFile -Force }
    $switches = @($arguments | Where-Object { $_ -notlike '/LOG=*' })
    if (-not (Test-Path -LiteralPath $setup)) { return [ordered]@{ setup_exit = -1; wall_seconds = 0; switches = $switches; log = $null; installer = $null; installer_raw = "missing: $setup" } }
    $p = Start-Process -FilePath $setup -ArgumentList $arguments -PassThru
    $null = $p.Handle   # Windows PowerShell 5.1: ExitCode is empty unless the handle was read first
    $seconds = WaitSaying $p "the Setup ($name)"
    $answer = $null; $raw = $null
    if (Test-Path -LiteralPath $resultFile) { $raw = Get-Content -LiteralPath $resultFile -Raw; try { $answer = $raw | ConvertFrom-Json } catch {} }
    [ordered]@{ setup_exit = $p.ExitCode; wall_seconds = $seconds; switches = $switches; log = (Split-Path -Leaf $log)
                installer = $answer; installer_raw = $(if ($answer) { $null } elseif ($raw) { $raw.Substring(0, [Math]::Min(1500, $raw.Length)) } else { '(no answer file)' }) }
}
# The entry Settings > Apps > Installed apps shows, written by the Setup under this account's own registry hive.
function InstalledAppsEntry {
    $key = EntryKey
    if (-not (Test-Path -LiteralPath $key)) { return [ordered]@{ present = $false; key = $key } }
    $e = Get-ItemProperty -LiteralPath $key
    [ordered]@{ present = $true; key = $key; name = "$($e.DisplayName)"; version = "$($e.DisplayVersion)"; publisher = "$($e.Publisher)"; uninstall = "$($e.UninstallString)"; location = "$($e.InstallLocation)" }
}
# Uninstall through that entry's own uninstaller (unins000.exe in the package folder), silently: it runs the
# package's installer with uninstall (program removed, data kept) and only when that succeeds removes the package
# folder and the entry. The installer's answer is kept beside the folder (<staging>-uninstall-result.json).
function RunUninstaller([string] $name) {
    $uninstaller = Join-Path $Staging 'unins000.exe'
    $log = Join-Path $script:EvidenceDir "setup-$name.log"
    $resultFile = $Staging.TrimEnd('\') + '-uninstall-result.json'
    if (Test-Path -LiteralPath $resultFile) { Remove-Item -LiteralPath $resultFile -Force }
    if (-not (Test-Path -LiteralPath $uninstaller)) { return [ordered]@{ uninstaller_exit = -1; wall_seconds = 0; log = $null; installer = $null; installer_raw = "missing: $uninstaller" } }
    $p = Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', ('/LOG="' + $log + '"')) -PassThru
    $null = $p.Handle
    $seconds = WaitSaying $p "the uninstaller ($name)"
    # The uninstaller finishes from a copy of itself in a temporary folder: the package folder and the entry can take a moment to go.
    $deadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $deadline -and ((Test-Path -LiteralPath $Staging) -or (Test-Path -LiteralPath (EntryKey)))) { Start-Sleep -Milliseconds 500 }
    $answer = $null; $raw = $null
    if (Test-Path -LiteralPath $resultFile) { $raw = Get-Content -LiteralPath $resultFile -Raw; try { $answer = $raw | ConvertFrom-Json } catch {} }
    [ordered]@{ uninstaller_exit = $p.ExitCode; wall_seconds = $seconds; log = (Split-Path -Leaf $log)
                installer = $answer; installer_raw = $(if ($answer) { $null } elseif ($raw) { $raw.Substring(0, [Math]::Min(1500, $raw.Length)) } else { '(no answer file)' }) }
}

# ---------------------------------------------------------------- No elevation (owner decision 2026-10-04)
# JARVIS installs and runs per user. The acceptance account is in the Administrators group, so every phase that
# installs or runs JARVIS first records that this process has no administrator rights and stops if it has.
if ($Phase -ne 'Baseline') {
    $elevated = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    $data = [ordered]@{ status = 'PASS'; account = "$env:USERDOMAIN\$env:USERNAME"; process_elevated = $elevated; note = 'the installer and JARVIS are started from this process and inherit its rights; a UAC prompt at any point is a STOP reported by the owner' }
    # Version 2: also note which Windows build ran the check (fix list item 7) and whether the account belongs to
    # Administrators (recorded, not failed). A failed read is recorded as 'unknown' and never stops the phase.
    $data.windows_build = 'unknown'; $data.windows_display_version = 'unknown'; $data.administrators_group_member = 'unknown'
    try { $cvE0 = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'; $data.windows_build = "$($cvE0.CurrentBuildNumber).$($cvE0.UBR)"; $data.windows_display_version = "$($cvE0.DisplayVersion)" } catch {}
    try { $data.administrators_group_member = [bool]((whoami /groups) -match 'S-1-5-32-544') } catch {}
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
    # Version 4: the Setup beside the zip, against its own record (hash, release, and the package manifest it was
    # built from, which must be the zip's). Hashed once: the payload-manifest check below reuses both big hashes.
    $setup = SetupFile $Package $rel.release_id
    if (-not $setup) { Fail 'I1-package' $data "no JARVIS-Setup-$($rel.release_id).exe with its .setup.json in the package folder" }
    $t = [Diagnostics.Stopwatch]::StartNew(); $setupHash = Sha256 $setup.exe
    $data.setup = Split-Path -Leaf $setup.exe; $data.setup_bytes = (Get-Item -LiteralPath $setup.exe).Length; $data.setup_sha256 = $setupHash
    $data.setup_matches_record = ($setupHash -eq $setup.record.setup_sha256); $data.setup_hash_seconds = [Math]::Round($t.Elapsed.TotalSeconds, 1)
    $data.setup_record_release = $setup.record.release_id; $data.setup_version = $setup.record.version
    $data.setup_built_from_this_package = ($setup.record.manifest_sha256 -eq $rel.manifest_sha256)
    $data.entry_key = EntryKey; $data.sandbox = $Sandbox
    $known = @{ "$($rel.zip)" = $zipHash; "$($data.setup)" = $setupHash }
    $manifestPath = Join-Path $Package 'PAYLOAD-MANIFEST.json'
    if (Test-Path -LiteralPath $manifestPath) {
        $pm = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
        $bad = @(foreach ($f in $pm.files) { $h = $(if ($known.ContainsKey("$($f.path)")) { $known["$($f.path)"] } else { Sha256 (Join-Path $Package $f.path) }); if ($h -ne $f.sha256) { $f.path } })
        $data.payload_manifest_files = $pm.files.Count; $data.payload_mismatches = $bad
        if ($bad) { Fail 'I1-package' $data 'payload file hash mismatch' }
    }
    if (-not $data.zip_matches_record) { Fail 'I1-package' $data 'zip hash does not match its release record' }
    if (-not $data.setup_matches_record) { Fail 'I1-package' $data 'the Setup does not match its record' }
    if ($setup.record.release_id -ne $rel.release_id) { Fail 'I1-package' $data 'the Setup record names another release' }
    if (-not $data.setup_built_from_this_package) { Fail 'I1-package' $data 'the Setup was built from another package than the zip' }
    Record 'I1-package' $data

    # I2 install from the Setup, silently: the package unpacked into the staging folder and the package's own installer
    # run, exactly what the owner's double-click does (version 3 extracted the zip and ran install.cmd).
    $r = RunSetup $setup.exe 'install'
    $stagedId = $null; try { $stagedId = (Get-Content -LiteralPath (Join-Path $Staging 'release\manifest.json') -Raw | ConvertFrom-Json).release_id } catch {}
    $data = [ordered]@{ status = 'PASS'; setup = $data.setup; setup_exit = $r.setup_exit; seconds = $r.wall_seconds; switches = $r.switches; setup_log = $r.log
                        result = $r.installer; raw = $r.installer_raw; installer_seconds = $r.installer.seconds; staging = $Staging; package_unpacked_release = $stagedId
                        uninstaller_present = (Test-Path -LiteralPath (Join-Path $Staging 'unins000.exe')); has_installer = (Test-Path -LiteralPath (Join-Path $Staging 'installer.py'))
                        files_in_package = @(Get-ChildItem -LiteralPath $Staging -Recurse -File -ErrorAction SilentlyContinue).Count }
    # The installer's own word on the real shortcuts, and on the VM no folder switch at all (the owner's double-click).
    $data.shortcuts_word = "$($r.installer.shortcuts)"; $data.shortcuts_expected = ShortcutWord 'install'
    if ($r.setup_exit -ne 0) { Fail 'I2-setup-install' $data "the Setup ended with code $($r.setup_exit)" }
    if (-not $r.installer -or $r.installer.status -ne 'installed') { Fail 'I2-setup-install' $data 'the Setup did not report installed' }
    if ($r.installer.release -ne $rel.release_id) { Fail 'I2-setup-install' $data 'installed release id differs from the package record' }
    if ($stagedId -ne $rel.release_id -or -not $data.has_installer) { Fail 'I2-setup-install' $data 'the package the Setup unpacked is missing or is another release' }
    if (-not $data.uninstaller_present) { Fail 'I2-setup-install' $data 'no uninstaller in the package folder' }
    if ($data.shortcuts_word -notlike $data.shortcuts_expected) { Fail 'I2-setup-install' $data "the installer's word on the shortcuts is '$($data.shortcuts_word)', expected $($data.shortcuts_expected)" }
    if (-not $Sandbox -and -not $NoShortcuts -and $r.switches.Count -ne 3) { Fail 'I2-setup-install' $data 'the Setup was given a folder or shortcut switch outside a sandbox' }
    Record 'I2-setup-install' $data

    # I3 the entry in Settings > Apps > Installed apps: JARVIS, this version, Teague Industries, its uninstaller the one in the package folder.
    $entry = InstalledAppsEntry
    $uninstaller = Join-Path $Staging 'unins000.exe'
    $data = [ordered]@{ status = 'PASS'; entry = $entry; expected_name = $ExpectedEntryName; expected_version = "$($setup.record.version)"; expected_uninstaller = $uninstaller }
    if (-not $entry.present) { Fail 'I3-installed-apps' $data 'no JARVIS entry in Installed apps' }
    if ($entry.name -ne $ExpectedEntryName -or $entry.version -ne "$($setup.record.version)" -or $entry.publisher -ne 'Teague Industries') { Fail 'I3-installed-apps' $data "the entry does not say $ExpectedEntryName, this version and Teague Industries" }
    if ($entry.uninstall -notlike "*$uninstaller*") { Fail 'I3-installed-apps' $data 'the entry does not point at the uninstaller in the package folder' }
    Record 'I3-installed-apps' $data

    # I4 installed files verified against the manifest; shortcuts present (VM) or deliberately absent (local).
    # Version 4: the shortcuts must point straight at this release's JARVIS.exe (docs\OWN-APP-PLAN.md 3.3).
    $v = Installer @('verify')
    $deskLink = Join-Path ([Environment]::GetFolderPath('Desktop')) 'JARVIS.lnk'; $startupLink = Join-Path ([Environment]::GetFolderPath('Startup')) 'JARVIS.lnk'
    $desk = Test-Path -LiteralPath $deskLink; $startup = Test-Path -LiteralPath $startupLink
    $program = Join-Path $InstallHome "releases\$($rel.release_id)\electron\JARVIS.exe"
    $data = [ordered]@{ status = 'PASS'; verify = $v.status; desktop_shortcut = $desk; startup_shortcut = $startup; shortcuts_expected = (-not $NoShortcuts); program = $program; program_present = (Test-Path -LiteralPath $program)
                        desktop_shortcut_target = $(if ($desk) { ShortcutTarget $deskLink } else { $null }); startup_shortcut_target = $(if ($startup) { ShortcutTarget $startupLink } else { $null })
                        launcher_script_present = (Test-Path -LiteralPath (Join-Path $InstallHome 'JARVIS.ps1')) }
    if ($v.status -ne 'verified') { Fail 'I4-verify' $data 'installed files do not verify' }
    if (-not $data.program_present) { Fail 'I4-verify' $data 'the release has no JARVIS.exe' }
    if ($data.launcher_script_present) { Fail 'I4-verify' $data 'JARVIS.ps1 was written although the release has its own program (decision D6)' }
    if (-not $NoShortcuts -and -not ($desk -and $startup)) { Fail 'I4-verify' $data 'shortcuts missing' }
    if (-not $NoShortcuts -and ($data.desktop_shortcut_target -ne $program -or $data.startup_shortcut_target -ne $program)) { Fail 'I4-verify' $data 'a shortcut does not point at this release''s JARVIS.exe' }
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
    $voice = Capture { & $r.python (Join-Path $r.app 'check_voice_offline.py') }
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
    # Version 4: uninstall through the Installed-apps entry's own uninstaller (the owner's way from 1.0.17 on): the
    # package's installer removes the program and keeps the data; the package folder and the entry go with it.
    $rel = PackageRecord $Package
    if (-not $rel) { Fail 'U1-uninstall' @{} 'no JARVIS-<id>.release.json in the package folder' }
    $setup = SetupFile $Package $rel.release_id   # read first: the Setup's record names the entry's application id
    if (-not $setup) { Fail 'U1-uninstall' @{} "no JARVIS-Setup-$($rel.release_id).exe with its .setup.json in the package folder" }
    $entryBefore = InstalledAppsEntry
    $u = RunUninstaller 'uninstall'
    $leftover = @(Get-ChildItem -LiteralPath (Join-Path $InstallHome 'releases') -Recurse -File -ErrorAction SilentlyContinue).Count
    $data = [ordered]@{ status = 'PASS'; uninstaller_exit = $u.uninstaller_exit; seconds = $u.wall_seconds; setup_log = $u.log; result = $u.installer.status; output = $u.installer_raw
                        program_files_removed = $u.installer.program_files_removed; kept = $u.installer.kept; installer_seconds = $u.installer.seconds; leftover_program_files = $leftover; processes = (Processes).Count
                        data_kept = (Test-Path -LiteralPath (Join-Path $InstallHome 'data\jarvis.sqlite3')); config_kept = (Test-Path -LiteralPath (Join-Path $InstallHome 'config\personality.txt'))
                        desktop_shortcut_gone = -not (Test-Path -LiteralPath (Join-Path ([Environment]::GetFolderPath('Desktop')) 'JARVIS.lnk')); startup_shortcut_gone = -not (Test-Path -LiteralPath (Join-Path ([Environment]::GetFolderPath('Startup')) 'JARVIS.lnk'))
                        entry_before = $entryBefore.present; entry_gone = -not (InstalledAppsEntry).present; package_folder_gone = -not (Test-Path -LiteralPath $Staging)
                        current_json_gone = -not (Test-Path -LiteralPath (Join-Path $InstallHome 'current.json')); launcher_script_gone = -not (Test-Path -LiteralPath (Join-Path $InstallHome 'JARVIS.ps1')) }
    # With -NoShortcuts (local rehearsal) the installer neither creates nor removes shortcuts, and a JARVIS.lnk on
    # that PC belongs to the owner's own installation: the shortcut checks apply only when shortcuts are in play.
    $shortcutsLeft = (-not $NoShortcuts) -and (-not $data.desktop_shortcut_gone -or -not $data.startup_shortcut_gone)
    $data.shortcuts_word = "$($u.installer.shortcuts)"; $data.shortcuts_expected = ShortcutWord 'uninstall'
    if ($u.uninstaller_exit -ne 0 -or $u.installer.status -ne 'uninstalled' -or $leftover -or $data.processes -or -not $data.data_kept -or $shortcutsLeft -or -not $data.entry_before -or -not $data.entry_gone -or -not $data.package_folder_gone) { Fail 'U1-uninstall' $data 'uninstall left program files, processes, shortcuts, the Installed-apps entry or the package folder, or removed data' }
    if ($data.shortcuts_word -notlike $data.shortcuts_expected) { Fail 'U1-uninstall' $data "the installer's word on the shortcuts is '$($data.shortcuts_word)', expected $($data.shortcuts_expected)" }
    Record 'U1-uninstall' $data

    # U2 reinstall from the Setup (the package unpacked again, the entry written again), then JARVIS back with its data.
    $setup = SetupFile $Package $rel.release_id
    if (-not $setup) { Fail 'U2-reinstall' @{} "no JARVIS-Setup-$($rel.release_id).exe with its .setup.json in the package folder" }
    $r = RunSetup $setup.exe 'reinstall'
    $entry = InstalledAppsEntry
    $null = Launch; $up = WaitForCore 180
    $state = $(if ($up) { Api '/api/state' } else { $null })
    $v = Installer @('verify')
    $data = [ordered]@{ status = 'PASS'; setup_exit = $r.setup_exit; seconds = $r.wall_seconds; setup_log = $r.log; reinstall = $r.installer.status; release = $r.installer.release; installer_seconds = $r.installer.seconds; output = $r.installer_raw
                        entry_present = $entry.present; entry_name = $entry.name; entry_version = $entry.version; core_ready = $up; memory_restored = [bool]($state.memory | Where-Object { $_.body -like 'Gate 17 memory:*' }); verify = $v.status
                        shortcuts_word = "$($r.installer.shortcuts)"; shortcuts_expected = (ShortcutWord 'install') }
    if ($r.setup_exit -ne 0 -or $r.installer.status -ne 'installed' -or $r.installer.release -ne $rel.release_id -or -not $entry.present -or $entry.name -ne $ExpectedEntryName -or -not $up -or -not $data.memory_restored -or $v.status -ne 'verified') { Fail 'U2-reinstall' $data 'reinstall from the Setup did not bring JARVIS back with its data and its entry' }
    if ($data.shortcuts_word -notlike $data.shortcuts_expected) { Fail 'U2-reinstall' $data "the installer's word on the shortcuts is '$($data.shortcuts_word)', expected $($data.shortcuts_expected)" }
    if (-not $Sandbox -and -not $NoShortcuts -and $r.switches.Count -ne 3) { Fail 'U2-reinstall' $data 'the Setup was given a folder or shortcut switch outside a sandbox' }
    Record 'U2-reinstall' $data
    $data = [ordered]@{ status = 'PASS'; stop = (StopJarvis) }
    Record 'U3-final-stop' $data
}

# ---------------------------------------------------------------- Gate 19: previous build, update, rollback, update again
# Runs after the Uninstall phase, in the same Windows session: -Package is the build under acceptance (already
# extracted to the staging folder by the Install phase), -PreviousPackage the build before it. Each installer call
# reports its own per-phase seconds (AMENDMENT-v3 D9: the timing bound is set from these measurements).
if ($Phase -eq 'Update' -or $Phase -eq 'Interrupt') {
    # (PackageRecord is defined above: version 4 needs it in the Uninstall phase too.)
    function RunInstaller($stagingFolder, [string[]] $arguments) {
        # installer.py of the named extracted package, run with that package's own Python (never the installed one).
        $out = Capture { & (Join-Path $stagingFolder 'release\python\python.exe') (Join-Path $stagingFolder 'installer.py') @arguments --home $InstallHome $(if ($NoShortcuts) { '--no-shortcuts' }) }
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

    # G7 (version 4): one update through the Setup, the way the owner updates from 1.0.17 on. Back on the previous
    # build (the package's rollback) and running, the Setup is run silently: it unpacks this package again over the
    # package folder and runs the package's installer, which updates while JARVIS runs. Version, files, both memories,
    # nothing left from the other release, the entry, then the final stop; the machine ends on the build under
    # acceptance, stopped, as after G6.
    $rb = RunInstaller $Staging @('rollback'); $left = ProcessesLeft; $before = RunningState $prev.release_id
    $setup = SetupFile $Package $final.release_id
    if (-not $setup) { Fail 'G7-update-through-setup' ([ordered]@{ status = 'PASS'; rollback = $rb.status; previous_running = $before }) "no JARVIS-Setup-$($final.release_id).exe with its .setup.json in the package folder" }
    $r = RunSetup $setup.exe 'update'
    $left2 = ProcessesLeft; $v = RunInstaller $Staging @('verify')
    $run = RunningState $final.release_id
    $stop = StopJarvis; $st = RunInstaller $Staging @('status'); $entry = InstalledAppsEntry
    $logs = Join-Path $InstallHome 'data\logs'
    if (Test-Path -LiteralPath $logs) { Copy-Item -LiteralPath $logs -Destination (Join-Path $script:EvidenceDir 'core-logs') -Recurse -Force }
    $data = [ordered]@{ status = 'PASS'; rollback = $rb.status; rolled_back_to = $rb.release; processes_left_after_rollback = $left; previous_running = $before
                        setup = (Split-Path -Leaf $setup.exe); setup_exit = $r.setup_exit; wall_seconds = $r.wall_seconds; switches = $r.switches; setup_log = $r.log
                        result = $r.installer.status; release = $r.installer.release; previous = $r.installer.previous; installer_seconds = $r.installer.seconds; output = $r.installer_raw
                        processes_left_after_update = $left2; verify = $v.status; verified_release = $v.release; running = $run; final_stop = $stop; current = $st.current; releases = $st.releases; entry = $entry
                        shortcuts_word = "$($r.installer.shortcuts)"; shortcuts_expected = (ShortcutWord 'install'); expected_entry_name = $ExpectedEntryName }
    # On the VM the update rewrote both shortcuts: they must point at this release's JARVIS.exe again (as I4 checked after the install).
    $program = Join-Path $InstallHome "releases\$($final.release_id)\electron\JARVIS.exe"
    $deskLink = Join-Path ([Environment]::GetFolderPath('Desktop')) 'JARVIS.lnk'; $startupLink = Join-Path ([Environment]::GetFolderPath('Startup')) 'JARVIS.lnk'
    $data.desktop_shortcut_target = $(if (Test-Path -LiteralPath $deskLink) { ShortcutTarget $deskLink } else { $null }); $data.startup_shortcut_target = $(if (Test-Path -LiteralPath $startupLink) { ShortcutTarget $startupLink } else { $null })
    if ($rb.status -ne 'rolled_back' -or $rb.release -ne $prev.release_id -or $left -or -not (Healthy $before)) { Fail 'G7-update-through-setup' $data 'the previous build was not back and running before the update through the Setup' }
    if ($r.setup_exit -ne 0 -or $r.installer.status -ne 'installed' -or $r.installer.release -ne $final.release_id -or $r.installer.previous -ne $prev.release_id -or $left2 -or $v.status -ne 'verified' -or $v.release -ne $final.release_id -or -not (Healthy $run) -or -not $stop.core_stopped_on_request -or $stop.processes_now -or $st.current.release -ne $final.release_id -or -not $entry.present -or $entry.name -ne $ExpectedEntryName -or $entry.version -ne "$($setup.record.version)") { Fail 'G7-update-through-setup' $data 'the update through the Setup or the final stop did not pass every check' }
    if ($data.shortcuts_word -notlike $data.shortcuts_expected) { Fail 'G7-update-through-setup' $data "the installer's word on the shortcuts is '$($data.shortcuts_word)', expected $($data.shortcuts_expected)" }
    if (-not $Sandbox -and -not $NoShortcuts -and ($r.switches.Count -ne 3 -or $data.desktop_shortcut_target -ne $program -or $data.startup_shortcut_target -ne $program)) { Fail 'G7-update-through-setup' $data 'outside a sandbox the Setup got a folder or shortcut switch, or a shortcut does not point at this release''s JARVIS.exe' }
    Record 'G7-update-through-setup' $data
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
