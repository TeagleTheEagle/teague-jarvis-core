# Own-app rehearsal (docs/OWN-APP-PLAN.md 3.1 to 3.3) in a sandbox on D:: install the rehearsal build with the
# package's installer (no shortcuts), start JARVIS.exe with no arguments as a double-click would, read the name and
# version Windows sees, prove the stale-start hand-over, uninstall. The owner's installed JARVIS is never addressed:
# every check is limited to the sandbox home. Provider keys are blanked for the sandbox Core.
param(
    [string] $Package = 'D:\JARVIS-release-work\own-app-rehearsal\JARVIS-1.0.17-09fed5f54c31',
    [string] $Base = 'D:\JARVIS-release-work\own-app-rehearsal'
)
$ErrorActionPreference = 'Stop'
$sandbox = Join-Path $Base 'home'
if (Test-Path -LiteralPath $sandbox) { throw "$sandbox exists" }
$python = Join-Path $Package 'release\python\python.exe'
$installer = Join-Path $Package 'installer.py'
$steps = New-Object Collections.ArrayList
function Step($name, $data) {
    $row = [ordered]@{ step = $name }
    foreach ($k in $data.Keys) { $row[$k] = $data[$k] }
    $null = $steps.Add($row)
    Write-Output ("$name  " + (ConvertTo-Json -InputObject $data -Compress -Depth 5))
}
function Processes { @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like "$sandbox\*" } | Select-Object Name, ProcessId, ExecutablePath) }
function Link { Get-Content -LiteralPath (Join-Path $sandbox 'data\core-connection.json') -Raw | ConvertFrom-Json }
function WaitForCore($seconds) {
    $deadline = (Get-Date).AddSeconds($seconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Path -LiteralPath (Join-Path $sandbox 'data\core-connection.json')) {
            try {
                $l = Link
                $r = Invoke-WebRequest -UseBasicParsing -Uri ($l.origin + '/') -Headers @{ 'X-Jarvis-Desktop' = $l.token } -TimeoutSec 5
                if ($r.StatusCode -eq 200) { return $true }
            } catch {}
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
    @{ left_after_request = $left.Count; forced = $left.Count }
}

# 1 install into the sandbox with the package's own Python, no shortcuts
$out = & $python $installer install --package $Package --home $sandbox --no-shortcuts | Out-String
$r = $out | ConvertFrom-Json
Step '1 install' ([ordered]@{ status = $r.status; release = $r.release; launcher_script_written = (Test-Path -LiteralPath (Join-Path $sandbox 'JARVIS.ps1')); seconds = $r.seconds })
$exe = Join-Path $sandbox ('releases\' + $r.release + '\electron\JARVIS.exe')

# 2 the program file as Windows sees it
$vi = (Get-Item -LiteralPath $exe).VersionInfo
Step '2 program' ([ordered]@{ exists = (Test-Path -LiteralPath $exe); product = $vi.ProductName; company = $vi.CompanyName; description = $vi.FileDescription
                             file_version = $vi.FileVersion; product_version = $vi.ProductVersion; original = $vi.OriginalFilename
                             electron_exe_absent = -not (Test-Path -LiteralPath (Join-Path (Split-Path $exe) 'electron.exe'))
                             bootstrap = (Test-Path -LiteralPath (Join-Path (Split-Path $exe) 'resources\app\main.cjs')) })

# 3 a double-click: JARVIS.exe with no arguments; no provider keys for the sandbox Core
$env:DASHSCOPE_API_KEY = ''; $env:OPENAI_API_KEY = ''
$t = [Diagnostics.Stopwatch]::StartNew()
Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe)
$up = WaitForCore 180
Start-Sleep -Seconds 8
$procs = Processes
$shell = @(Get-Process -Name JARVIS -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "$sandbox\*" })
Step '3 launch' ([ordered]@{ core_ready = $up; seconds_to_core = [Math]::Round($t.Elapsed.TotalSeconds, 1); process_names = @($procs | ForEach-Object { $_.Name } | Sort-Object -Unique)
                            jarvis_exe_processes = $shell.Count; window_title = ($shell | ForEach-Object { $_.MainWindowTitle } | Where-Object { $_ } | Select-Object -First 1)
                            data_in_sandbox = (Test-Path -LiteralPath (Join-Path $sandbox 'data\jarvis.sqlite3')); profile_in_sandbox = (Test-Path -LiteralPath (Join-Path $sandbox 'profile'))
                            real_home_untouched_by_this = (-not (Test-Path -LiteralPath (Join-Path $sandbox 'JARVIS.ps1'))) })
$s = Shutdown
Step '3b shutdown' $s

# 4 stale start: current.json names a copy of the release; the original's JARVIS.exe must hand over and exit
$copyId = $r.release + '-copy'
Copy-Item -LiteralPath (Join-Path $sandbox ('releases\' + $r.release)) -Destination (Join-Path $sandbox ('releases\' + $copyId)) -Recurse
[IO.File]::WriteAllText((Join-Path $sandbox 'current.json'), ('{"release": "' + $copyId + '", "previous": "' + $r.release + '", "switched_at": 0}'))
$t = [Diagnostics.Stopwatch]::StartNew()
Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe) -ArgumentList '--login-launch'
$up = WaitForCore 180
Start-Sleep -Seconds 8
$running = @(Get-Process -Name JARVIS -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "$sandbox\*" } | ForEach-Object { $_.Path } | Sort-Object -Unique)
$fromCopy = @($running | Where-Object { $_ -like "*\$copyId\*" }).Count
$fromOld = @($running | Where-Object { $_ -like ("*\" + $r.release + "\*") }).Count
Step '4 stale start' ([ordered]@{ core_ready = $up; seconds_to_core = [Math]::Round($t.Elapsed.TotalSeconds, 1); running_from = $running; from_current_copy = $fromCopy; from_old = $fromOld; handed_over = (($fromCopy -ge 1) -and ($fromOld -eq 0)) })
$s = Shutdown
Step '4b shutdown' $s

# 5 uninstall (both release folders carry a manifest: both go; data kept)
[IO.File]::WriteAllText((Join-Path $sandbox 'current.json'), ('{"release": "' + $r.release + '", "previous": null, "switched_at": 0}'))
$out = & $python $installer uninstall --home $sandbox --no-shortcuts | Out-String
$u = $out | ConvertFrom-Json
Step '5 uninstall' ([ordered]@{ status = $u.status; removed = $u.program_files_removed; kept = $u.kept; processes = (Processes).Count; releases_left = (Test-Path -LiteralPath (Join-Path $sandbox 'releases')) })
[IO.File]::WriteAllText((Join-Path $Base 'own-app-rehearsal.json'), (ConvertTo-Json -InputObject $steps -Depth 6), (New-Object Text.UTF8Encoding $false))
