<#
.SYNOPSIS
Gate 17 (clean Windows deployment / functional acceptance) run INSIDE the acceptance machine.
DRAFT for owner review; rehearsed locally against sandbox installs on D: before any VM use.

Runs on a fresh Windows 11 Home with nothing installed (Windows PowerShell 5.1 only). The
release carries its own Python, Electron and models, so no prerequisite is installed. Every
step writes a JSON record to the evidence folder; the first failure stops the run (no silent
retry). Nothing here reads or writes outside the package, the install home, the staging
folder and the evidence folder. There are no secrets on the machine; none are created.

.PARAMETER Package   Folder holding JARVIS-<id>.zip and JARVIS-<id>.release.json (the mounted ISO root).
.PARAMETER Evidence  Folder for the records (the single declared egress folder on the VM).
.PARAMETER Phase     Baseline | Install | AfterRestart | Uninstall | All (All = Baseline, Install, Uninstall).
.PARAMETER InstallHome  Install folder. VM: default %LOCALAPPDATA%\JARVIS. Local rehearsal: a sandbox on D:.
.PARAMETER NoShortcuts  Local rehearsal only (never touch the owner's real Desktop/Startup folders).
.PARAMETER SkipBaseline Local rehearsal only (this PC is a development machine and would fail the cleanliness checks).
#>
param(
    [Parameter(Mandatory)] [string] $Package,
    [Parameter(Mandatory)] [string] $Evidence,
    [ValidateSet('Baseline', 'Install', 'AfterRestart', 'Uninstall', 'All')] [string] $Phase = 'All',
    [string] $InstallHome = (Join-Path $env:LOCALAPPDATA 'JARVIS'),
    [switch] $NoShortcuts,
    [switch] $SkipBaseline
)
$ErrorActionPreference = 'Stop'
$script:Started = Get-Date
$script:EvidenceDir = Join-Path $Evidence ('gate17-' + $script:Started.ToUniversalTime().ToString('yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $script:EvidenceDir -Force | Out-Null
$script:Summary = New-Object Collections.ArrayList
$Staging = Join-Path $env:LOCALAPPDATA 'JARVIS-package'
$Utf8 = New-Object Text.UTF8Encoding $false

function Now { (Get-Date).ToUniversalTime().ToString('o') }
function Record($name, $data) {
    [IO.File]::WriteAllText((Join-Path $script:EvidenceDir "$name.json"), ($data | ConvertTo-Json -Depth 8), $Utf8)
    $script:Summary.Add([ordered]@{ step = $name; status = $data.status; at = (Now) }) | Out-Null
    Write-Host ("{0,-30} {1}" -f $name, $data.status)
}
function Finish($overall) {
    $summary = [ordered]@{ schema = 'jarvis-gate17-run-v1'; overall = $overall; phase = $Phase; home = $InstallHome; package = $Package
                           started_utc = $script:Started.ToUniversalTime().ToString('o'); finished_utc = (Now); steps = @($script:Summary) }
    [IO.File]::WriteAllText((Join-Path $script:EvidenceDir 'SUMMARY.json'), ($summary | ConvertTo-Json -Depth 6), $Utf8)
    Write-Host "Gate 17 $Phase : $overall  ($script:EvidenceDir)"
}
function Fail($name, $data, $why) { $data.status = 'FAIL'; $data.reason = $why; Record $name $data; Finish 'FAIL'; exit 2 }
function Sha256($path) { (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower() }
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

# ---------------------------------------------------------------- Baseline (FRESH-CLEAN-BASELINE negative checks)
if (($Phase -eq 'Baseline' -or $Phase -eq 'All') -and -not $SkipBaseline) {
    $cv = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
    $tools = foreach ($t in 'python', 'py', 'node', 'npm', 'git', 'codex', 'code', 'cl', 'pip') { $c = Get-Command $t -ErrorAction SilentlyContinue; if ($c) { "$t -> $($c.Source)" } }
    $dirs = foreach ($d in "$env:ProgramFiles\Python*", "${env:ProgramFiles(x86)}\Python*", "$env:ProgramFiles\nodejs", "$env:ProgramFiles\Git", "$env:ProgramFiles\Microsoft Visual Studio", "$env:LOCALAPPDATA\Programs\Python", "$env:LOCALAPPDATA\Programs\Microsoft VS Code", "$env:APPDATA\npm") { if (Test-Path $d) { $d } }
    $envFiles = @(Get-ChildItem -LiteralPath $env:USERPROFILE -Recurse -Force -Filter '.env*' -ErrorAction SilentlyContinue | Select-Object -First 20 -ExpandProperty FullName)
    $cred = (cmdkey /list 2>$null | Out-String)
    $lic = Get-CimInstance SoftwareLicensingProduct -Filter "ApplicationID='55c92734-d682-4d71-983e-d6ec3f16059f' and PartialProductKey is not null" | Select-Object -First 1
    $wu = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings' -ErrorAction SilentlyContinue
    $programs = @(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*', 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*', 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue | Where-Object DisplayName | Select-Object DisplayName, DisplayVersion, Publisher | Sort-Object DisplayName)
    $services = @(Get-Service | Select-Object Name, Status, StartType | Sort-Object Name)
    $data = [ordered]@{
        status = 'PASS'; at = (Now)
        edition = $cv.ProductName; display_version = $cv.DisplayVersion; build = "$($cv.CurrentBuildNumber).$($cv.UBR)"; edition_id = $cv.EditionID
        activation_license_status = if ($lic) { $lic.LicenseStatus } else { 'unknown' }
        hypervisor_present = (Get-CimInstance Win32_ComputerSystem).HypervisorPresent
        windows_update_pause_expiry = if ($wu) { $wu.PauseUpdatesExpiryTime } else { $null }
        account = "$env:USERDOMAIN\$env:USERNAME"; is_administrator = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        path = $env:PATH
        development_tools_on_path = @($tools); development_tool_folders = @($dirs)
        jarvis_install_present = (Test-Path -LiteralPath $InstallHome); jarvis_processes = (Processes).Count
        env_files_in_profile = $envFiles; jarvis_credentials = ($cred -match 'JARVIS'); credential_entries = ([regex]::Matches($cred, 'Target:')).Count
        installed_programs = $programs.Count; services = $services.Count
    }
    [IO.File]::WriteAllText((Join-Path $script:EvidenceDir 'baseline-programs.json'), ($programs | ConvertTo-Json -Depth 3), $Utf8)
    [IO.File]::WriteAllText((Join-Path $script:EvidenceDir 'baseline-services.json'), ($services | ConvertTo-Json -Depth 3), $Utf8)
    $problems = @()
    if ($tools) { $problems += 'development tools on PATH' }
    if ($dirs) { $problems += 'development tool folders present' }
    if ($data.jarvis_install_present) { $problems += 'JARVIS already installed' }
    if ($data.jarvis_processes) { $problems += 'JARVIS processes running' }
    if ($envFiles) { $problems += '.env files in the profile' }
    if ($data.jarvis_credentials) { $problems += 'JARVIS credential entries' }
    if ($problems) { Fail 'B1-baseline' $data ($problems -join '; ') }
    Record 'B1-baseline' $data
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
    Write-Host 'JARVIS is running. VM: quit it from the tray ("Quit JARVIS completely"), restart Windows, then run -Phase AfterRestart.'
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

Finish 'PASS'
