# Rehearsal of tools\host\update-1.0.17\Invoke-EverydayUpdate.ps1 (version 2: the update made by the release's own Setup)
# in a sandbox on D:. 1.0.16 is installed into a sandbox home (no shortcuts) and started once so it has a database; a
# stale staging folder is planted; then the launcher runs with a test approval: refusals (no approval; JARVIS
# running), check (the stale folder moved aside), backup, update through the Setup with the sandbox switches (/DIR,
# /HOME, /NOSHORTCUTS: the entry "JARVIS (sandbox)" under the sandbox id, no real shortcut touched), 1.0.17 started on
# the same data through its own JARVIS.exe, a rerun that changes nothing, rollback (only with its approval file), a
# final rerun, and the sandbox uninstalled through its own entry. The owner's real Desktop and Startup shortcuts are
# hashed before, after every step and at the end and must not change; the owner's installed JARVIS
# (%LOCALAPPDATA%\JARVIS) is never addressed, and the number of its processes is recorded before and after.
param(
    [string] $Base = 'D:\JARVIS-release-work\update-rehearsal-1.0.17',
    [string] $PreviousZip = 'D:\JARVIS-release-work\pkg-1.0.16\JARVIS-1.0.16-fccde24e2cc6.zip',
    [string] $PreviousId = '1.0.16-fccde24e2cc6',
    [string] $FinalZip = 'D:\JARVIS-release-work\pkg-1.0.17\JARVIS-1.0.17-0d38218c4e1d.zip',
    [string] $FinalSetup = 'D:\JARVIS-release-work\pkg-1.0.17\JARVIS-Setup-1.0.17-0d38218c4e1d.exe',
    [string] $FinalId = '1.0.17-0d38218c4e1d',
    [string] $Launcher = ''
)
$ErrorActionPreference = 'Stop'
# Set here, not as the parameter default: PowerShell 5.1 can leave $PSScriptRoot empty in a parameter default.
if (-not $Launcher) { $Launcher = Join-Path $PSScriptRoot '..\..\tools\host\update-1.0.17\Invoke-EverydayUpdate.ps1' }
if (Test-Path -LiteralPath $Base) { throw "$Base exists" }
$sandboxHome = Join-Path $Base 'home'; $root = Join-Path $Base 'update'; $auth = Join-Path $Base 'update-authorized.json'; $staging = Join-Path $Base 'staging'
$setupRecord = Get-Content -LiteralPath ($FinalSetup -replace '\.exe$', '.setup.json') -Raw | ConvertFrom-Json
if (-not $setupRecord.sandbox_app_id) { throw 'the Setup record names no sandbox_app_id. STOP' }
$key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\' + $setupRecord.sandbox_app_id + '_is1'
$realKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\' + $setupRecord.app_id + '_is1'
if (Test-Path -LiteralPath $key) { throw 'a sandbox entry exists already. STOP' }
New-Item -ItemType Directory -Path $Base | Out-Null
$log = Join-Path $Base 'rehearsal.output.txt'
$results = New-Object Collections.ArrayList
$switches = '/DIR=' + $staging + ';/HOME=' + $sandboxHome + ';/NOSHORTCUTS'
function Note($text) { Add-Content -LiteralPath $log -Value $text; Write-Host $text }
function LiveCount { @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like "$env:LOCALAPPDATA\JARVIS\releases\*" }).Count }
function SandboxProcesses { @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith("$sandboxHome\releases\", [StringComparison]::OrdinalIgnoreCase) }) }
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
function Check($name, [bool] $ok, $detail) { $results.Add([ordered]@{ check = $name; passed = $ok; detail = $detail }) | Out-Null; Note ("{0}  {1}  {2}" -f $(if ($ok) { 'PASS' } else { 'FAIL' }), $name, $detail) }
function Step([string] $title, [string] $authorizedFile) {
    # 'Continue': a line on the launcher's error output must be recorded, not end this harness.
    $ErrorActionPreference = 'Continue'
    Note "===== $title  $(Get-Date -Format 'HH:mm:ss')"
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $Launcher -Root $root -InstallHome $sandboxHome -Staging $staging -SetupSwitches $switches -Authorized $authorizedFile 2>&1 | Out-String
    $code = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    Note $out.Trim(); Note "exit=$code"
    if (-not (ShortcutsUnchanged)) { Note 'STOPPED: the real shortcuts changed'; throw 'the real shortcuts changed. STOP' }
    [pscustomobject]@{ exit = $code; text = $out }
}
function Records { if (Test-Path -LiteralPath (Join-Path $root 'evidence')) { @(Get-ChildItem -LiteralPath (Join-Path $root 'evidence') -File | ForEach-Object { $_.Name } | Sort-Object) } else { @() } }
function CoreLink { $f = Join-Path $sandboxHome 'data\core-connection.json'; if (Test-Path -LiteralPath $f) { Get-Content -LiteralPath $f -Raw | ConvertFrom-Json } else { $null } }
function StartSandbox {
    # 1.0.16 through its JARVIS.ps1; 1.0.17 through its own JARVIS.exe (the launcher script is gone once it is current).
    $script = Join-Path $sandboxHome 'JARVIS.ps1'
    if (Test-Path -LiteralPath $script) { & powershell -NoProfile -ExecutionPolicy Bypass -File $script }
    else {
        $current = Get-Content -LiteralPath (Join-Path $sandboxHome 'current.json') -Raw | ConvertFrom-Json
        $exe = Join-Path $sandboxHome ('releases\' + $current.release + '\electron\JARVIS.exe')
        $null = Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe) -PassThru
    }
    for ($i = 0; $i -lt 240; $i++) {
        $link = CoreLink
        if ($link) { try { $r = Invoke-WebRequest -UseBasicParsing -Uri ($link.origin + '/') -Headers @{ 'X-Jarvis-Desktop' = $link.token } -TimeoutSec 5; if ($r.StatusCode -eq 200) { return $link } } catch {} }
        Start-Sleep -Milliseconds 500
    }
    throw 'the sandbox JARVIS did not become ready'
}
function Session($link) {
    $null = Invoke-WebRequest -UseBasicParsing -Uri ($link.origin + '/') -Headers @{ 'X-Jarvis-Desktop' = $link.token } -SessionVariable s -TimeoutSec 15
    $s
}
function StateOf($link) {
    $s = Session $link
    Invoke-RestMethod -Uri ($link.origin + '/api/state') -Headers @{ 'X-Jarvis-Desktop' = $link.token } -WebSession $s -TimeoutSec 30
}
function StopSandbox {
    $link = CoreLink
    if ($link) {
        try {
            $s = Session $link
            Invoke-RestMethod -Method Post -Uri ($link.origin + '/api/shutdown') -Body '{}' -ContentType 'application/json' -Headers @{ 'X-Jarvis-Desktop' = $link.token } -WebSession $s -TimeoutSec 10 | Out-Null
        } catch {}
        for ($i = 0; $i -lt 60 -and (CoreLink); $i++) { Start-Sleep -Milliseconds 500 }
    }
    for ($round = 0; $round -lt 5 -and (SandboxProcesses).Count; $round++) {
        SandboxProcesses | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
        Start-Sleep -Seconds 2
    }
    if ((SandboxProcesses).Count) { throw 'sandbox JARVIS processes did not end' }
}
function Entry { if (Test-Path -LiteralPath $key) { $e = Get-ItemProperty -LiteralPath $key; [ordered]@{ present = $true; name = $e.DisplayName; version = $e.DisplayVersion } } else { @{ present = $false } } }

$liveBefore = LiveCount
Note "live JARVIS processes at the start: $liveBefore; real shortcuts: $($shortcutsBefore.desktop) $($shortcutsBefore.startup); real entry present: $(Test-Path -LiteralPath $realKey)"

# 1. The everyday JARVIS of the sandbox: 1.0.16 installed with its own package installer, started once. A stale
#    staging folder planted, as the switch-over left one on the owner's C:.
Note '===== install 1.0.16 into the sandbox home'
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::ExtractToDirectory($PreviousZip, (Join-Path $Base 'pkg-previous'))
$prevPkg = @(Get-ChildItem -LiteralPath (Join-Path $Base 'pkg-previous') -Directory)[0].FullName
$ErrorActionPreference = 'Continue'
$installed = (& (Join-Path $prevPkg 'release\python\python.exe') (Join-Path $prevPkg 'installer.py') install --package $prevPkg --home $sandboxHome --no-shortcuts 2>&1 | Out-String) | ConvertFrom-Json
$ErrorActionPreference = 'Stop'
Check 'sandbox: 1.0.16 installed' ($installed.status -eq 'installed' -and $installed.release -eq $PreviousId) $installed.status
New-Item -ItemType Directory -Path (Join-Path $staging 'release') | Out-Null
[IO.File]::WriteAllText((Join-Path $staging 'release\stale.txt'), 'a file from an old package', (New-Object Text.UTF8Encoding $false))
$link = StartSandbox
$state = StateOf $link
Check 'sandbox: 1.0.16 running on its data' ($state.updates.installed_release -eq $PreviousId) $state.updates.installed_release

# 2. Refusals.
$r = Step 'no approval: refused' (Join-Path $Base 'no-such-approval.json')
Check 'refused without approval' ($r.exit -eq 2 -and $r.text -like '*not been approved*' -and -not (Records).Count) "exit $($r.exit)"
$authorization = [ordered]@{ schema = 'jarvis-everyday-update-authorized-v2'; final = $FinalId; previous = $PreviousId; final_zip = $FinalZip
    final_zip_sha256 = (Get-FileHash -LiteralPath $FinalZip -Algorithm SHA256).Hash.ToLower(); final_setup = $FinalSetup
    final_setup_sha256 = (Get-FileHash -LiteralPath $FinalSetup -Algorithm SHA256).Hash.ToLower(); note = 'rehearsal approval, sandbox only' }
[IO.File]::WriteAllText($auth, (ConvertTo-Json -InputObject $authorization), (New-Object Text.UTF8Encoding $false))
$r = Step 'JARVIS running: refused' $auth
Check 'refused while JARVIS runs' ($r.exit -eq 2 -and $r.text -like '*JARVIS is running*' -and -not ((Records) -contains 'check.json')) "exit $($r.exit)"
StopSandbox

# 3. The three steps.
$r = Step 'step 1 check' $auth
$check = $(if ((Records) -contains 'check.json') { Get-Content -LiteralPath (Join-Path $root 'evidence\check.json') -Raw | ConvertFrom-Json } else { $null })
Check 'step 1 check' ($r.exit -eq 0 -and $null -ne $check) "exit $($r.exit)"
Check 'step 1: stale staging folder moved aside, nothing deleted' ($null -ne $check -and $check.staging_moved_aside -and (Test-Path -LiteralPath (Join-Path $check.staging_moved_aside 'release\stale.txt')) -and -not (Test-Path -LiteralPath $staging)) "$($check.staging_moved_aside)"
Check 'step 1: no entry before' ($null -ne $check -and -not $check.entry_before.present) "$($check.entry_before.present)"
$r = Step 'step 2 backup' $auth
Check 'step 2 backup' ($r.exit -eq 0 -and ((Records) -contains 'backup.json')) "exit $($r.exit)"
$r = Step 'step 3 update through the Setup' $auth
Check 'step 3 update' ($r.exit -eq 0 -and ((Records) -contains 'update.json')) "exit $($r.exit)"
$update = $(if ((Records) -contains 'update.json') { Get-Content -LiteralPath (Join-Path $root 'evidence\update.json') -Raw | ConvertFrom-Json } else { $null })
Check 'update: database unchanged' ($null -ne $update -and [bool]$update.database_unchanged) "$($update.database_sha256_before)"
Check 'update: current is 1.0.17, previous 1.0.16' ($null -ne $update -and $update.current.release -eq $FinalId -and $update.current.previous -eq $PreviousId) "$($update.current.release)"
Check 'update: the installer inside the Setup withheld the shortcuts (sandbox)' ($null -ne $update -and "$($update.installer.shortcuts)" -like 'withheld*') "$($update.installer.shortcuts)"
$entry = Entry
Check 'update: the entry JARVIS (sandbox) with the version' ($entry.present -and $entry.name -eq $setupRecord.sandbox_display_name -and $entry.version -eq $setupRecord.version) "$($entry.name) $($entry.version)"
Check 'update: the real entry untouched' (-not (Test-Path -LiteralPath $realKey)) "$(Test-Path -LiteralPath $realKey)"
Check 'update: the Setup logged --no-shortcuts' ((Test-Path -LiteralPath (Join-Path $root 'evidence\setup-update.log')) -and ((Get-Content -LiteralPath (Join-Path $root 'evidence\setup-update.log') -Raw) -like '*--no-shortcuts*')) 'setup-update.log'

# 4. 1.0.17 on the same data, through its own JARVIS.exe.
$link = StartSandbox
$state = StateOf $link
Check 'sandbox: 1.0.17 running on the same data through JARVIS.exe' ($state.updates.installed_release -eq $FinalId) $state.updates.installed_release
$names = @(SandboxProcesses | ForEach-Object { $_.Name } | Sort-Object -Unique)
Check 'sandbox: only JARVIS.exe and python.exe run' (($names -join ',') -eq 'JARVIS.exe,python.exe') ($names -join ',')
StopSandbox
$before = Records
$r = Step 'rerun after the update: nothing to do' $auth
Check 'rerun changes nothing' ($r.exit -eq 0 -and $r.text -like '*complete and recorded*' -and ((Records) -join ',') -eq ($before -join ',')) "exit $($r.exit)"

# 5. Rollback, only with its approval file.
[IO.File]::WriteAllText((Join-Path $root 'evidence\rollback-approved.json'), '{"note": "rehearsal"}', (New-Object Text.UTF8Encoding $false))
$r = Step 'rollback (approved)' $auth
$current = Get-Content -LiteralPath (Join-Path $sandboxHome 'current.json') -Raw | ConvertFrom-Json
Check 'rollback to 1.0.16' ($r.exit -eq 0 -and ((Records) -contains 'rollback.json') -and $current.release -eq $PreviousId) "$($current.release)"
Check 'rollback: the entry still says 1.0.17 (as the plan says)' ((Entry).present -and (Entry).version -eq $setupRecord.version) "$((Entry).version)"
$link = StartSandbox
$state = StateOf $link
Check 'sandbox: 1.0.16 running again on the same data' ($state.updates.installed_release -eq $PreviousId) $state.updates.installed_release
StopSandbox
$r = Step 'rerun after the rollback: nothing to do' $auth
Check 'rerun after rollback changes nothing' ($r.exit -eq 0 -and $r.text -like '*complete and recorded*') "exit $($r.exit)"

# 6. Cleanup through the sandbox's own entry (both releases removed, data kept, the entry and the staging gone).
$uninstaller = Join-Path $staging 'unins000.exe'
if (Test-Path -LiteralPath $uninstaller) {
    $u = Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART') -PassThru -Wait
    $null = $u.Handle
    $deadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $deadline -and ((Test-Path -LiteralPath $staging) -or (Test-Path -LiteralPath $key))) { Start-Sleep -Milliseconds 500 }
    Check 'cleanup: the sandbox uninstalled through its own entry' ($u.ExitCode -eq 0 -and -not (Test-Path -LiteralPath $key) -and -not (Test-Path -LiteralPath $staging) -and (Test-Path -LiteralPath (Join-Path $sandboxHome 'data\jarvis.sqlite3')) -and -not (Test-Path -LiteralPath (Join-Path $sandboxHome 'releases'))) "exit $($u.ExitCode)"
} else {
    # The Setup never ran (an earlier step stopped): no entry to clean up; the sandbox JARVIS is ended all the same.
    Check 'cleanup: the sandbox uninstalled through its own entry' $false 'no uninstaller: the update step never ran'
    StopSandbox
}
Check 'the owner real shortcuts unchanged throughout' (ShortcutsUnchanged) "$((RealShortcuts).desktop) $((RealShortcuts).startup)"

$liveAfter = LiveCount
Note "live JARVIS processes at the end: $liveAfter (start: $liveBefore); sandbox processes at the end: $((SandboxProcesses).Count)"
$failed = @($results | Where-Object { -not $_.passed }).Count
$summary = [ordered]@{ base = $Base; launcher_sha256 = (Get-FileHash -LiteralPath $Launcher -Algorithm SHA256).Hash.ToLower(); setup_sha256 = $authorization.final_setup_sha256; checks = @($results); failed = $failed
    real_shortcuts_before = $shortcutsBefore; real_shortcuts_after = (RealShortcuts); live_processes_before = $liveBefore; live_processes_after = $liveAfter; sandbox_processes_after = (SandboxProcesses).Count }
[IO.File]::WriteAllText((Join-Path $Base 'rehearsal-summary.json'), (ConvertTo-Json -InputObject $summary -Depth 5), (New-Object Text.UTF8Encoding $false))
Note ("{0} checks, {1} failed" -f $results.Count, $failed)
exit $(if ($failed) { 1 } else { 0 })
