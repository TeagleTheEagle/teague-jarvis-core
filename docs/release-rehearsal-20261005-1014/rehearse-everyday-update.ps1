# Rehearsal of tools\host\Invoke-EverydayUpdate.ps1 (the update of the everyday JARVIS) in a sandbox on D:.
# 1.0.11 is installed into a sandbox home (no shortcuts) and started once so it has a database; then the launcher runs
# with a test approval: refusals (no approval; JARVIS running), check, backup, update, 1.0.14 started on the same
# data, a rerun that changes nothing, rollback (only with its approval file), and a final rerun. Every JARVIS started
# here runs from the sandbox home; the owner's installed JARVIS (%LOCALAPPDATA%\JARVIS) is never addressed, and the
# number of its processes is recorded before and after.
param(
    [string] $Base = 'D:\JARVIS-release-work\update-rehearsal-1.0.14',
    [string] $PreviousZip = 'D:\JARVIS-release-work\pkg-1.0.11\JARVIS-1.0.11-60d406fb6398.zip',
    [string] $PreviousId = '1.0.11-60d406fb6398',
    [string] $FinalZip = 'D:\JARVIS-release-work\pkg-1.0.14\JARVIS-1.0.14-e03872680e1d.zip',
    [string] $FinalId = '1.0.14-e03872680e1d',
    [string] $Launcher = ''
)
$ErrorActionPreference = 'Stop'
# Set here, not as the parameter default: PowerShell 5.1 can leave $PSScriptRoot empty in a parameter default.
if (-not $Launcher) { $Launcher = Join-Path $PSScriptRoot '..\..\tools\host\Invoke-EverydayUpdate.ps1' }
if (Test-Path -LiteralPath $Base) { throw "$Base exists" }
$sandboxHome = Join-Path $Base 'home'; $root = Join-Path $Base 'update'; $auth = Join-Path $Base 'update-authorized.json'
New-Item -ItemType Directory -Path $Base | Out-Null
$log = Join-Path $Base 'rehearsal.output.txt'
$results = New-Object Collections.ArrayList
function Note($text) { Add-Content -LiteralPath $log -Value $text; Write-Host $text }
function LiveCount { @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like "$env:LOCALAPPDATA\JARVIS\releases\*" }).Count }
function SandboxProcesses { @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith("$sandboxHome\releases\", [StringComparison]::OrdinalIgnoreCase) }) }
function Check($name, [bool] $ok, $detail) { $results.Add([ordered]@{ check = $name; passed = $ok; detail = $detail }) | Out-Null; Note ("{0}  {1}  {2}" -f $(if ($ok) { 'PASS' } else { 'FAIL' }), $name, $detail) }
function Step([string] $title, [string] $authorizedFile) {
    # 'Continue': a line on the launcher's error output must be recorded, not end this harness.
    $ErrorActionPreference = 'Continue'
    Note "===== $title  $(Get-Date -Format 'HH:mm:ss')"
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $Launcher -Root $root -InstallHome $sandboxHome -Authorized $authorizedFile 2>&1 | Out-String
    $code = $LASTEXITCODE
    Note $out.Trim(); Note "exit=$code"
    [pscustomobject]@{ exit = $code; text = $out }
}
function Records { if (Test-Path -LiteralPath (Join-Path $root 'evidence')) { @(Get-ChildItem -LiteralPath (Join-Path $root 'evidence') -File | ForEach-Object { $_.Name } | Sort-Object) } else { @() } }
function CoreLink { $f = Join-Path $sandboxHome 'data\core-connection.json'; if (Test-Path -LiteralPath $f) { Get-Content -LiteralPath $f -Raw | ConvertFrom-Json } else { $null } }
function StartSandbox {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $sandboxHome 'JARVIS.ps1')
    for ($i = 0; $i -lt 240; $i++) {
        $link = CoreLink
        if ($link) { try { $r = Invoke-WebRequest -UseBasicParsing -Uri ($link.origin + '/') -Headers @{ 'X-Jarvis-Desktop' = $link.token } -TimeoutSec 5; if ($r.StatusCode -eq 200) { return $link } } catch {} }
        Start-Sleep -Milliseconds 500
    }
    throw 'the sandbox JARVIS did not become ready'
}
function StateOf($link) {
    $page = Invoke-WebRequest -UseBasicParsing -Uri ($link.origin + '/') -Headers @{ 'X-Jarvis-Desktop' = $link.token } -TimeoutSec 10
    $cookie = ($page.Headers['Set-Cookie'] -split ';')[0]
    (Invoke-WebRequest -UseBasicParsing -Uri ($link.origin + '/api/state') -Headers @{ 'X-Jarvis-Desktop' = $link.token; Cookie = $cookie } -TimeoutSec 20).Content | ConvertFrom-Json
}
function StopSandbox {
    # A requested shutdown of the sandbox Core, then the sandbox's own remaining programs (started by this harness).
    $link = CoreLink
    if ($link) {
        try {
            $page = Invoke-WebRequest -UseBasicParsing -Uri ($link.origin + '/') -Headers @{ 'X-Jarvis-Desktop' = $link.token } -TimeoutSec 10
            $cookie = ($page.Headers['Set-Cookie'] -split ';')[0]
            Invoke-WebRequest -UseBasicParsing -Method Post -Uri ($link.origin + '/api/shutdown') -Body '{}' -ContentType 'application/json' -Headers @{ 'X-Jarvis-Desktop' = $link.token; Cookie = $cookie } -TimeoutSec 10 | Out-Null
        } catch {}
        for ($i = 0; $i -lt 60 -and (CoreLink); $i++) { Start-Sleep -Milliseconds 500 }
    }
    for ($round = 0; $round -lt 5 -and (SandboxProcesses).Count; $round++) {
        SandboxProcesses | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
        Start-Sleep -Seconds 2
    }
    if ((SandboxProcesses).Count) { throw 'sandbox JARVIS processes did not end' }
}

$liveBefore = LiveCount
Note "live JARVIS processes at the start: $liveBefore"

# 1. The everyday JARVIS of the sandbox: 1.0.11 installed with its own package installer, started once.
Note '===== install 1.0.11 into the sandbox home'
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::ExtractToDirectory($PreviousZip, (Join-Path $Base 'pkg-previous'))
$prevPkg = @(Get-ChildItem -LiteralPath (Join-Path $Base 'pkg-previous') -Directory)[0].FullName
$ErrorActionPreference = 'Continue'
$installed = (& (Join-Path $prevPkg 'release\python\python.exe') (Join-Path $prevPkg 'installer.py') install --package $prevPkg --home $sandboxHome --no-shortcuts 2>&1 | Out-String) | ConvertFrom-Json
$ErrorActionPreference = 'Stop'
Check 'sandbox: 1.0.11 installed' ($installed.status -eq 'installed' -and $installed.release -eq $PreviousId) $installed.status
$link = StartSandbox
$state = StateOf $link
Check 'sandbox: 1.0.11 running on its data' ($state.updates.installed_release -eq $PreviousId) $state.updates.installed_release

# 2. Refusals.
$r = Step 'no approval: refused' (Join-Path $Base 'no-such-approval.json')
Check 'refused without approval' ($r.exit -eq 2 -and $r.text -like '*not been approved*' -and -not (Records).Count) "exit $($r.exit)"
$authorization = [ordered]@{ schema = 'jarvis-everyday-update-authorized-v1'; final = $FinalId; previous = $PreviousId; final_zip = $FinalZip
    final_zip_sha256 = (Get-FileHash -LiteralPath $FinalZip -Algorithm SHA256).Hash.ToLower(); note = 'rehearsal approval, sandbox only' }
[IO.File]::WriteAllText($auth, (ConvertTo-Json -InputObject $authorization), (New-Object Text.UTF8Encoding $false))
$r = Step 'JARVIS running: refused' $auth
Check 'refused while JARVIS runs' ($r.exit -eq 2 -and $r.text -like '*JARVIS is running*' -and -not ((Records) -contains 'check.json')) "exit $($r.exit)"
StopSandbox

# 3. The three steps.
$r = Step 'step 1 check' $auth
Check 'step 1 check' ($r.exit -eq 0 -and ((Records) -contains 'check.json')) "exit $($r.exit)"
$r = Step 'step 2 backup' $auth
Check 'step 2 backup' ($r.exit -eq 0 -and ((Records) -contains 'backup.json')) "exit $($r.exit)"
$r = Step 'step 3 update' $auth
Check 'step 3 update' ($r.exit -eq 0 -and ((Records) -contains 'update.json')) "exit $($r.exit)"
$update = Get-Content -LiteralPath (Join-Path $root 'evidence\update.json') -Raw | ConvertFrom-Json
Check 'update: database unchanged' ([bool]$update.database_unchanged) "$($update.database_sha256_before)"
Check 'update: current is 1.0.14, previous 1.0.11' ($update.current.release -eq $FinalId -and $update.current.previous -eq $PreviousId) "$($update.current.release)"

# 4. 1.0.14 on the same data.
$link = StartSandbox
$state = StateOf $link
Check 'sandbox: 1.0.14 running on the same data' ($state.updates.installed_release -eq $FinalId) $state.updates.installed_release
StopSandbox
$before = Records
$r = Step 'rerun after the update: nothing to do' $auth
Check 'rerun changes nothing' ($r.exit -eq 0 -and $r.text -like '*complete and recorded*' -and ((Records) -join ',') -eq ($before -join ',')) "exit $($r.exit)"

# 5. Rollback, only with its approval file.
[IO.File]::WriteAllText((Join-Path $root 'evidence\rollback-approved.json'), '{"note": "rehearsal"}', (New-Object Text.UTF8Encoding $false))
$r = Step 'rollback (approved)' $auth
$current = Get-Content -LiteralPath (Join-Path $sandboxHome 'current.json') -Raw | ConvertFrom-Json
Check 'rollback to 1.0.11' ($r.exit -eq 0 -and ((Records) -contains 'rollback.json') -and $current.release -eq $PreviousId) "$($current.release)"
$r = Step 'rerun after the rollback: nothing to do' $auth
Check 'rerun after rollback changes nothing' ($r.exit -eq 0 -and $r.text -like '*complete and recorded*') "exit $($r.exit)"

$liveAfter = LiveCount
Note "live JARVIS processes at the end: $liveAfter (start: $liveBefore); sandbox processes at the end: $((SandboxProcesses).Count)"
$failed = @($results | Where-Object { -not $_.passed }).Count
$summary = [ordered]@{ base = $Base; launcher_sha256 = (Get-FileHash -LiteralPath $Launcher -Algorithm SHA256).Hash.ToLower(); checks = @($results); failed = $failed
    live_processes_before = $liveBefore; live_processes_after = $liveAfter; sandbox_processes_after = (SandboxProcesses).Count }
[IO.File]::WriteAllText((Join-Path $Base 'rehearsal-summary.json'), (ConvertTo-Json -InputObject $summary -Depth 5), (New-Object Text.UTF8Encoding $false))
Note ("{0} checks, {1} failed" -f $results.Count, $failed)
exit $(if ($failed) { 1 } else { 0 })
