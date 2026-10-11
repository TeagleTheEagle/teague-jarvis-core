# JARVIS-Setup rehearsal (docs/OWN-APP-PLAN.md 3.4) in a sandbox on D:: the Setup run silently with a sandbox
# package folder (/DIR) and a sandbox install home (/HOME), the installer's answer read, the Installed-apps entry
# read, JARVIS.exe started and stopped, a second run of the same Setup (a reinstall), then the entry's own uninstaller
# run silently: program removed, data kept, package folder and entry gone. The owner's installed JARVIS is never
# addressed. The entry lives in this account's own registry hive for the minutes between install and uninstall, as
# the plan allows for a sandbox test that cleans up after itself; this script records that it is gone at the end.
param(
    [Parameter(Mandatory)] [string] $Setup,
    [string] $Base = 'D:\JARVIS-release-work\own-app-rehearsal\setup-rehearsal'
)
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $Base) { throw "$Base exists" }
New-Item -ItemType Directory -Path $Base | Out-Null
$package = Join-Path $Base 'package'; $sandbox = Join-Path $Base 'home'
$key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{DC2C8033-1BBF-5E1C-99A0-BE0E70DC9937}_is1'
$steps = New-Object Collections.ArrayList
function Step($name, $data) {
    $row = [ordered]@{ step = $name }
    foreach ($k in $data.Keys) { $row[$k] = $data[$k] }
    $null = $steps.Add($row)
    Write-Output ("$name  " + (ConvertTo-Json -InputObject $data -Compress -Depth 5))
}
function Entry { if (Test-Path -LiteralPath $key) { $e = Get-ItemProperty -LiteralPath $key; [ordered]@{ present = $true; name = $e.DisplayName; version = $e.DisplayVersion; publisher = $e.Publisher; uninstall = $e.UninstallString; location = $e.InstallLocation } } else { @{ present = $false } } }
function Processes { @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like "$sandbox\*" -or $_.ExecutablePath -like "$package\*" } | Select-Object Name, ProcessId, ExecutablePath) }
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
function RunSetup($label, $log) {
    $t = [Diagnostics.Stopwatch]::StartNew()
    $p = Start-Process -FilePath $Setup -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/NOSHORTCUTS', "/DIR=`"$package`"", "/HOME=`"$sandbox`"", "/LOG=`"$log`"") -PassThru -Wait
    $null = $p.Handle
    $result = $null; try { $result = Get-Content -LiteralPath (Join-Path $package 'setup-result.json') -Raw | ConvertFrom-Json } catch {}
    [ordered]@{ setup_exit = $p.ExitCode; seconds = [Math]::Round($t.Elapsed.TotalSeconds, 1); installer_status = $result.status; release = $result.release; previous = $result.previous; installer_seconds = $result.seconds
                home_file = (Get-Content -LiteralPath (Join-Path $package 'setup-home.txt') -Raw -ErrorAction SilentlyContinue); entry = (Entry) }
}

Step '0 before' ([ordered]@{ setup = $Setup; setup_bytes = (Get-Item -LiteralPath $Setup).Length; entry_before = (Entry); processes = (Processes).Count })
$env:DASHSCOPE_API_KEY = ''; $env:OPENAI_API_KEY = ''

# 1 silent install into the sandbox
$r = RunSetup 'install' (Join-Path $Base 'setup-install.log')
Step '1 silent install' $r
if ($r.installer_status -ne 'installed') { throw 'the Setup did not install JARVIS' }
$exe = Join-Path $sandbox ('releases\' + $r.release + '\electron\JARVIS.exe')
Step '1b layout' ([ordered]@{ program = (Test-Path -LiteralPath $exe); package_release = (Test-Path -LiteralPath (Join-Path $package 'release\manifest.json')); uninstaller = (Test-Path -LiteralPath (Join-Path $package 'unins000.exe')); launcher_script = (Test-Path -LiteralPath (Join-Path $sandbox 'JARVIS.ps1')) })

# 2 JARVIS starts from the installed program
$t = [Diagnostics.Stopwatch]::StartNew()
Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe)
$up = WaitForCore 180
Start-Sleep -Seconds 5
Step '2 launch' ([ordered]@{ core_ready = $up; seconds_to_core = [Math]::Round($t.Elapsed.TotalSeconds, 1); processes = @((Processes) | ForEach-Object { $_.Name } | Sort-Object -Unique) })
$s = Shutdown
Step '2b shutdown' $s

# 3 the same Setup again: a reinstall (the package replaced, the installed release verified, nothing copied twice)
$r2 = RunSetup 'reinstall' (Join-Path $Base 'setup-reinstall.log')
Step '3 reinstall' $r2

# 4 uninstall through the entry's own uninstaller
$t = [Diagnostics.Stopwatch]::StartNew()
$u = Start-Process -FilePath (Join-Path $package 'unins000.exe') -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', "/LOG=`"$(Join-Path $Base 'setup-uninstall.log')`"") -PassThru -Wait
$null = $u.Handle
Start-Sleep -Seconds 3
$ur = $null; try { $ur = Get-Content -LiteralPath ($package + '-uninstall-result.json') -Raw | ConvertFrom-Json } catch {}
Step '4 uninstall' ([ordered]@{ uninstaller_exit = $u.ExitCode; seconds = [Math]::Round($t.Elapsed.TotalSeconds, 1); installer_status = $ur.status; removed = $ur.program_files_removed; kept = $ur.kept; entry_after = (Entry); package_folder_left = (Test-Path -LiteralPath $package)
                               program_left = (Test-Path -LiteralPath (Join-Path $sandbox 'releases')); current_json_left = (Test-Path -LiteralPath (Join-Path $sandbox 'current.json'))
                               data_kept = (Test-Path -LiteralPath (Join-Path $sandbox 'data\jarvis.sqlite3')); config_kept = (Test-Path -LiteralPath (Join-Path $sandbox 'config\personality.txt')); processes = (Processes).Count })
[IO.File]::WriteAllText((Join-Path $Base 'setup-rehearsal.json'), (ConvertTo-Json -InputObject $steps -Depth 6), (New-Object Text.UTF8Encoding $false))
