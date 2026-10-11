# JARVIS-Setup rehearsal, version 2 (docs/OWN-APP-PLAN.md 3.4; docs/OWN-APP-1.0.17.md section 6). The version 1
# script (rehearse-setup.ps1) passed every step it checked on 2026-10-07 01:37, and still wrote and then removed the
# owner's real Desktop and Startup shortcuts, because the Setup's /NOSHORTCUTS never reached the installer and the
# record never looked at the real shortcut folders. This version records the owner's real Desktop and Startup
# JARVIS.lnk (SHA-256, or ABSENT) before anything runs, after every step and at the end; any change stops the
# rehearsal at once and is written into the record as a FAIL. It also records: the owner's installed JARVIS's
# process count before and after (never addressed); the Installed-apps entry before (must be absent: this PC has no
# real 1.0.17); the installer's own word on the shortcuts in each answer ("withheld": the home is not this PC's own
# install home); and the installer command the Setup logged (it must carry --no-shortcuts). Otherwise the steps of
# version 1, in a sandbox on D:: a silent install with /DIR, /HOME and /NOSHORTCUTS, the entry, JARVIS.exe started
# and stopped, a reinstall by the same Setup, the uninstall through the entry's own uninstaller (program removed,
# data kept, package folder and entry gone). The entry lives in this account's own registry hive for the minutes
# between install and uninstall, as the plan allows for a sandbox test that cleans up after itself.
param(
    [Parameter(Mandatory)] [string] $Setup,
    [Parameter(Mandatory)] [string] $Base
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Setup)) { throw "no Setup at $Setup" }
if (Test-Path -LiteralPath $Base) { throw "$Base exists" }
New-Item -ItemType Directory -Path $Base | Out-Null
$package = Join-Path $Base 'package'; $sandbox = Join-Path $Base 'home'
# A run with /HOME registers as "JARVIS (sandbox)" under the sandbox application id (review finding M6 of 2026-10-07),
# never under the real JARVIS's; the id is read from the Setup's own record beside it.
$setupRecord = Get-Content -LiteralPath ($Setup -replace '\.exe$', '.setup.json') -Raw | ConvertFrom-Json
if (-not $setupRecord.sandbox_app_id) { throw 'the Setup record names no sandbox_app_id; this rehearsal is for a Setup built with the sandbox id. STOP' }
$key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\' + $setupRecord.sandbox_app_id + '_is1'
$expectedName = 'JARVIS (sandbox)'
$record = Join-Path $Base 'setup-rehearsal-v2.json'
$steps = New-Object Collections.ArrayList
function Save { [IO.File]::WriteAllText($record, (ConvertTo-Json -InputObject $steps -Depth 6), (New-Object Text.UTF8Encoding $false)) }
function Step($name, $data) {
    $row = [ordered]@{ step = $name; at = (Get-Date).ToUniversalTime().ToString('o') }
    foreach ($k in $data.Keys) { $row[$k] = $data[$k] }
    $null = $steps.Add($row)
    Write-Output ("$name  " + (ConvertTo-Json -InputObject $data -Compress -Depth 5))
    Save
}
function Stop-Rehearsal($name, $why, $data) { $data['FAIL'] = $why; Step $name $data; throw "STOP: $why" }
function Entry { if (Test-Path -LiteralPath $key) { $e = Get-ItemProperty -LiteralPath $key; [ordered]@{ present = $true; name = $e.DisplayName; version = $e.DisplayVersion; publisher = $e.Publisher; uninstall = $e.UninstallString; location = $e.InstallLocation } } else { @{ present = $false } } }
function Processes { @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like "$sandbox\*" -or $_.ExecutablePath -like "$package\*" } | Select-Object Name, ProcessId, ExecutablePath) }
function LiveCount { @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like "$env:LOCALAPPDATA\JARVIS\releases\*" }).Count }
# The owner's real shortcuts: a hash each, or ABSENT. Read only; never written here.
function RealShortcuts {
    $r = [ordered]@{}
    foreach ($pair in @(@('desktop', [Environment]::GetFolderPath('Desktop')), @('startup', [Environment]::GetFolderPath('Startup')))) {
        $p = Join-Path $pair[1] 'JARVIS.lnk'
        $r[$pair[0]] = $(if (Test-Path -LiteralPath $p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() } else { 'ABSENT' })
    }
    $r
}
$shortcutsBefore = RealShortcuts
function ShortcutsUnchanged { $now = RealShortcuts; ($now.desktop -eq $shortcutsBefore.desktop) -and ($now.startup -eq $shortcutsBefore.startup) }
function WatchShortcuts($name) {
    $now = RealShortcuts
    if (-not (ShortcutsUnchanged)) { Stop-Rehearsal "$name SHORTCUTS CHANGED" "the owner's real shortcuts changed during $name" ([ordered]@{ before = $shortcutsBefore; now = $now }) }
    $now
}
function Link { Get-Content -LiteralPath (Join-Path $sandbox 'data\core-connection.json') -Raw | ConvertFrom-Json }
function WaitForCore($seconds) {
    $deadline = (Get-Date).AddSeconds($seconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Path -LiteralPath (Join-Path $sandbox 'data\core-connection.json')) {
            try { $l = Link; $r = Invoke-WebRequest -UseBasicParsing -Uri ($l.origin + '/') -Headers @{ 'X-Jarvis-Desktop' = $l.token } -TimeoutSec 5; if ($r.StatusCode -eq 200) { return $true } } catch {}
        }
        Start-Sleep -Milliseconds 500
    }
    $false
}
function Shutdown {
    try {
        $l = Link
        $null = Invoke-WebRequest -UseBasicParsing -Uri ($l.origin + '/') -Headers @{ 'X-Jarvis-Desktop' = $l.token } -SessionVariable s -TimeoutSec 5
        $null = Invoke-WebRequest -UseBasicParsing -Uri ($l.origin + '/api/shutdown') -Method Post -Body '{}' -ContentType 'application/json' -Headers @{ 'X-Jarvis-Desktop' = $l.token } -WebSession $s -TimeoutSec 15
    } catch { Write-Output "shutdown request: $_" }
    $deadline = (Get-Date).AddSeconds(40)
    while ((Get-Date) -lt $deadline -and (Processes).Count) { Start-Sleep -Milliseconds 500 }
    $left = Processes
    foreach ($p in $left) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
    @{ left_after_request = $left.Count }
}
# The installer command the Setup logged (its [Code] section writes "JARVIS installer: cmd ..." before each run).
function LoggedCommand($log) {
    $line = $null
    if (Test-Path -LiteralPath $log) { $m = Select-String -LiteralPath $log -Pattern 'JARVIS installer: cmd' | Select-Object -Last 1; if ($m) { $line = $m.Line.Trim() } }
    [ordered]@{ installer_command = $line; no_shortcuts_passed = [bool]($line -and $line -like '*--no-shortcuts*') }
}
function RunSetup($label, $log) {
    $resultFile = Join-Path $package 'setup-result.json'
    if (Test-Path -LiteralPath $resultFile) { Remove-Item -LiteralPath $resultFile -Force }   # never read a stale answer
    $t = [Diagnostics.Stopwatch]::StartNew()
    $p = Start-Process -FilePath $Setup -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/NOSHORTCUTS', "/DIR=`"$package`"", "/HOME=`"$sandbox`"", "/LOG=`"$log`"") -PassThru -Wait
    $null = $p.Handle
    $result = $null; try { $result = Get-Content -LiteralPath $resultFile -Raw | ConvertFrom-Json } catch {}
    $logged = LoggedCommand $log
    [ordered]@{ setup_exit = $p.ExitCode; seconds = [Math]::Round($t.Elapsed.TotalSeconds, 1); installer_status = $result.status; release = $result.release; previous = $result.previous; installer_seconds = $result.seconds
                installer_shortcuts = $result.shortcuts; installer_command = $logged.installer_command; no_shortcuts_passed = $logged.no_shortcuts_passed
                home_file = [string](Get-Content -LiteralPath (Join-Path $package 'setup-home.txt') -Raw -ErrorAction SilentlyContinue); noshortcuts_marker = (Test-Path -LiteralPath (Join-Path $package 'setup-noshortcuts.txt')); entry = (Entry) }
}
function RequireSandboxOnly($name, $r) {
    if ($r.setup_exit -ne 0) { Stop-Rehearsal $name "the Setup ended with code $($r.setup_exit)" $r }
    if ($r.installer_shortcuts -notlike 'withheld*') { Stop-Rehearsal $name "the installer did not withhold the real shortcuts (it said: $($r.installer_shortcuts))" $r }
    if (-not $r.no_shortcuts_passed) { Stop-Rehearsal $name 'the Setup did not pass --no-shortcuts to the installer' $r }
    if (-not $r.entry.present -or $r.entry.name -ne $expectedName -or "$($r.entry.version)" -ne "$($setupRecord.version)") { Stop-Rehearsal $name "the Installed-apps entry is not '$expectedName $($setupRecord.version)' (got: $(ConvertTo-Json -InputObject $r.entry -Compress))" $r }
}

$liveBefore = LiveCount
$entryBefore = Entry
Step '0 before' ([ordered]@{ setup = $Setup; setup_bytes = (Get-Item -LiteralPath $Setup).Length; setup_sha256 = (Get-FileHash -LiteralPath $Setup -Algorithm SHA256).Hash.ToLower(); entry_before = $entryBefore; processes = (Processes).Count; live_jarvis_processes = $liveBefore; real_shortcuts = $shortcutsBefore })
if ($entryBefore.present) { Stop-Rehearsal '0 before' 'an Installed-apps entry for JARVIS exists on this PC already; this rehearsal would overwrite and then remove it' ([ordered]@{ entry = $entryBefore }) }
$env:DASHSCOPE_API_KEY = ''; $env:OPENAI_API_KEY = ''

# 1 silent install into the sandbox
$r = RunSetup 'install' (Join-Path $Base 'setup-install.log')
$r['real_shortcuts'] = WatchShortcuts '1 silent install'
Step '1 silent install' $r
if ($r.installer_status -ne 'installed') { Stop-Rehearsal '1 silent install' 'the Setup did not install JARVIS' $r }
RequireSandboxOnly '1 silent install' $r
$exe = Join-Path $sandbox ('releases\' + $r.release + '\electron\JARVIS.exe')
Step '1b layout' ([ordered]@{ program = (Test-Path -LiteralPath $exe); package_release = (Test-Path -LiteralPath (Join-Path $package 'release\manifest.json')); uninstaller = (Test-Path -LiteralPath (Join-Path $package 'unins000.exe')); launcher_script = (Test-Path -LiteralPath (Join-Path $sandbox 'JARVIS.ps1')) })

# 2 JARVIS starts from the installed program
$t = [Diagnostics.Stopwatch]::StartNew()
Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe)
$up = WaitForCore 180
Start-Sleep -Seconds 5
Step '2 launch' ([ordered]@{ core_ready = $up; seconds_to_core = [Math]::Round($t.Elapsed.TotalSeconds, 1); processes = @((Processes) | ForEach-Object { $_.Name } | Sort-Object -Unique); real_shortcuts = (WatchShortcuts '2 launch') })
$s = Shutdown
Step '2b shutdown' $s

# 3 the same Setup again: a reinstall (the package replaced, the installed release verified, nothing copied twice)
$r2 = RunSetup 'reinstall' (Join-Path $Base 'setup-reinstall.log')
$r2['real_shortcuts'] = WatchShortcuts '3 reinstall'
Step '3 reinstall' $r2
if ($r2.installer_status -ne 'installed') { Stop-Rehearsal '3 reinstall' 'the reinstall did not report installed' $r2 }
RequireSandboxOnly '3 reinstall' $r2

# 4 uninstall through the entry's own uninstaller
$t = [Diagnostics.Stopwatch]::StartNew()
$ulog = Join-Path $Base 'setup-uninstall.log'
$u = Start-Process -FilePath (Join-Path $package 'unins000.exe') -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', "/LOG=`"$ulog`"") -PassThru -Wait
$null = $u.Handle
$deadline = (Get-Date).AddSeconds(30)
while ((Get-Date) -lt $deadline -and ((Test-Path -LiteralPath $package) -or (Test-Path -LiteralPath $key))) { Start-Sleep -Milliseconds 500 }
$ur = $null; try { $ur = Get-Content -LiteralPath ($package + '-uninstall-result.json') -Raw | ConvertFrom-Json } catch {}
$logged = LoggedCommand $ulog
$u4 = [ordered]@{ uninstaller_exit = $u.ExitCode; seconds = [Math]::Round($t.Elapsed.TotalSeconds, 1); installer_status = $ur.status; removed = $ur.program_files_removed; kept = $ur.kept; installer_shortcuts = $ur.shortcuts
                  installer_command = $logged.installer_command; no_shortcuts_passed = $logged.no_shortcuts_passed; entry_after = (Entry); package_folder_left = (Test-Path -LiteralPath $package)
                  program_left = (Test-Path -LiteralPath (Join-Path $sandbox 'releases')); current_json_left = (Test-Path -LiteralPath (Join-Path $sandbox 'current.json'))
                  data_kept = (Test-Path -LiteralPath (Join-Path $sandbox 'data\jarvis.sqlite3')); config_kept = (Test-Path -LiteralPath (Join-Path $sandbox 'config\personality.txt')); processes = (Processes).Count }
$u4['real_shortcuts'] = WatchShortcuts '4 uninstall'
Step '4 uninstall' $u4
if ($u.ExitCode -ne 0) { Stop-Rehearsal '4 uninstall' "the uninstaller ended with code $($u.ExitCode)" $u4 }
if ($ur.status -ne 'uninstalled' -or $u4.entry_after.present -or $u4.package_folder_left -or $u4.program_left -or -not $u4.data_kept -or $u4.processes) { Stop-Rehearsal '4 uninstall' 'the uninstall did not remove the program, the entry and the package folder with the data kept' $u4 }
if ($ur.shortcuts -notlike 'withheld*' -or -not $logged.no_shortcuts_passed) { Stop-Rehearsal '4 uninstall' "the uninstall did not withhold the real shortcuts (installer: $($ur.shortcuts); --no-shortcuts passed: $($logged.no_shortcuts_passed))" $u4 }

$liveAfter = LiveCount
$final = [ordered]@{ real_shortcuts = (WatchShortcuts '5 after'); real_shortcuts_unchanged = (ShortcutsUnchanged); live_jarvis_processes_before = $liveBefore; live_jarvis_processes_after = $liveAfter; entry_after = (Entry); result = 'PASS' }
if ($liveAfter -ne $liveBefore) { Stop-Rehearsal '5 after' "the owner's installed JARVIS has $liveAfter processes now, $liveBefore before: something outside the sandbox changed" $final }
Step '5 after' $final
Write-Output "SETUP REHEARSAL V2 PASSED: $record"
