# Local rehearsal of the version 4 Stage 7 scripts (tools\guest\stage7-v4\Invoke-Stage7Pass.ps1 + Invoke-Stage7.ps1)
# for a release that is its own app (1.0.17 and later), in a sandbox on D:: the method of
# docs\release-rehearsal-20261006-1015\rehearse-stage7-release-v3.ps1 with what version 4 adds.
# The package folder must hold the release zip, its record, JARVIS-Setup-<id>.exe and its .setup.json (as the disc
# root does); the previous package the zip and record of the build before it. Sandbox install home and staging, no
# shortcuts: the Setup is run with /DIR, /HOME and /NOSHORTCUTS, and the installer itself withholds the real shortcuts
# from any home that is not the PC's own install home. Sandbox JARVIS windows open on this PC while it runs; the
# owner's installed JARVIS (%LOCALAPPDATA%\JARVIS) is never addressed: every check and every stop is limited to the
# sandbox home. Recorded and required unchanged: the owner's real Desktop and Startup JARVIS.lnk (SHA-256 or ABSENT)
# before, after every start of the driver and at the end (any change stops the rehearsal at once); the number of
# live JARVIS processes before and after. The Installed-apps entry must be absent before (this PC has no real 1.0.17);
# the pass leaves the sandbox installed with its entry, so the rehearsal ends by running the sandbox's own uninstaller
# (program removed, data kept, package folder and entry gone), as the plan allows for a sandbox test that cleans up
# after itself.
# The restart check is exercised as in version 3: after the install step the driver is started again on the same
# start of Windows (it must ask for the restart), and then with a file that says "one start later" in place of
# Windows (the driver's rehearsal switch -BootIdentityFile). -NoRestartCheck is not used at all.
param(
    [Parameter(Mandatory)] [string] $Package,          # folder with JARVIS-<final>.zip, .release.json, JARVIS-Setup-<final>.exe, .setup.json
    [Parameter(Mandatory)] [string] $PreviousPackage,  # folder with the previous build's zip and .release.json
    [Parameter(Mandatory)] [string] $Base,
    [string] $Driver = ''
)
$ErrorActionPreference = 'Stop'
# Set here, not as the parameter default: PowerShell 5.1 can leave $PSScriptRoot empty in a parameter default.
if (-not $Driver) { $Driver = Join-Path $PSScriptRoot '..\..\tools\guest\stage7-v4\Invoke-Stage7Pass.ps1' }
$driverText = Get-Content -LiteralPath $Driver -Raw
if ($driverText -notmatch '\[string\] \$BootIdentityFile' -or $driverText -notmatch 'driver = 4') { throw 'this is not a version 4 driver. STOP' }
$setupRecordFile = Get-ChildItem -LiteralPath $Package -Filter 'JARVIS-Setup-*.setup.json' -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not (Get-ChildItem -LiteralPath $Package -Filter 'JARVIS-Setup-*.exe' -ErrorAction SilentlyContinue) -or -not $setupRecordFile) { throw "no JARVIS-Setup-<id>.exe with its .setup.json in $Package. STOP" }
# The sandbox pass gives the Setup /HOME, so it registers as "JARVIS (sandbox)" under the sandbox application id
# named in the Setup's record, never under the real JARVIS's (review finding M6 of 2026-10-07).
$setupRecord = Get-Content -LiteralPath $setupRecordFile.FullName -Raw | ConvertFrom-Json
if (-not $setupRecord.sandbox_app_id) { throw 'the Setup record names no sandbox_app_id; this harness is for a Setup built with the sandbox id. STOP' }
if (Test-Path -LiteralPath $Base) { throw "$Base exists" }
$evidence = Join-Path $Base 'evidence'; New-Item -ItemType Directory -Path $evidence | Out-Null
$home_ = Join-Path $Base 'home'; $staging = Join-Path $Base 'staging'
$common = @('-Evidence', $evidence, '-Package', $Package, '-PreviousPackage', $PreviousPackage,
            '-InstallHome', $home_, '-Staging', $staging, '-NoShortcuts')
$log = Join-Path $Base 'rehearsal.output.txt'
$summaryFile = Join-Path $Base 'rehearsal-summary.json'
$key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\' + $setupRecord.sandbox_app_id + '_is1'
function Entry { if (Test-Path -LiteralPath $key) { $e = Get-ItemProperty -LiteralPath $key; [ordered]@{ present = $true; name = $e.DisplayName; version = $e.DisplayVersion; location = $e.InstallLocation } } else { @{ present = $false } } }
function LiveCount { @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like "$env:LOCALAPPDATA\JARVIS\releases\*" }).Count }
function SandboxProcesses { @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like (Join-Path $Base '*') }) }
function RealShortcuts {
    $r = [ordered]@{}
    foreach ($pair in @(@('desktop', [Environment]::GetFolderPath('Desktop')), @('startup', [Environment]::GetFolderPath('Startup')))) {
        $p = Join-Path $pair[1] 'JARVIS.lnk'
        $r[$pair[0]] = $(if (Test-Path -LiteralPath $p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() } else { 'ABSENT' })
    }
    $r
}
$shortcutsBefore = RealShortcuts
$exits = @()
function Summary($state) {
    $summary = [ordered]@{ package = $Package; previous_package = $PreviousPackage; base = $Base; driver = 4; state = $state; steps = $exits
                           real_shortcuts_before = $shortcutsBefore; real_shortcuts_now = (RealShortcuts); live_processes_before = $liveBefore; live_processes_now = (LiveCount)
                           entry_before = $entryBefore; entry_now = (Entry); sandbox_processes_now = (SandboxProcesses).Count }
    $summary.real_shortcuts_unchanged = ($summary.real_shortcuts_now.desktop -eq $shortcutsBefore.desktop) -and ($summary.real_shortcuts_now.startup -eq $shortcutsBefore.startup)
    [IO.File]::WriteAllText($summaryFile, (ConvertTo-Json -InputObject $summary -Depth 5), (New-Object Text.UTF8Encoding $false))
    $summary
}
function WatchShortcuts($title) {
    $now = RealShortcuts
    if ($now.desktop -ne $shortcutsBefore.desktop -or $now.startup -ne $shortcutsBefore.startup) {
        Add-Content -LiteralPath $log -Value "THE OWNER'S REAL SHORTCUTS CHANGED during '$title': before $($shortcutsBefore | ConvertTo-Json -Compress), now $($now | ConvertTo-Json -Compress)"
        foreach ($p in SandboxProcesses) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
        $null = Summary 'STOPPED: the real shortcuts changed'
        throw "STOP: the owner's real shortcuts changed during '$title'"
    }
}
$liveBefore = LiveCount
$entryBefore = Entry
Add-Content -LiteralPath $log -Value "live JARVIS processes at the start: $liveBefore; real shortcuts: $($shortcutsBefore | ConvertTo-Json -Compress); Installed-apps entry before: $($entryBefore | ConvertTo-Json -Compress)"
if ($entryBefore.present) { $null = Summary 'STOPPED: an Installed-apps entry for JARVIS exists already'; throw 'an Installed-apps entry for JARVIS exists on this PC already; this rehearsal would overwrite and then remove it. STOP' }
function Run([string] $title, [string[]] $extra, [string] $mustSay = '') {
    # 'Continue' here: under 'Stop', PowerShell 5.1 turns a line the driver writes to its error output into a fatal
    # error and this harness would end mid-pass; the line belongs in the log instead.
    $ErrorActionPreference = 'Continue'
    Add-Content -LiteralPath $log -Value "===== $title  $(Get-Date -Format 'HH:mm:ss')"
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $Driver @common @extra 2>&1 | Out-String
    $code = $LASTEXITCODE
    Add-Content -LiteralPath $log -Value $out
    Add-Content -LiteralPath $log -Value "exit=$code  $(Get-Date -Format 'HH:mm:ss')"
    $entry = [ordered]@{ step = $title; exit = $code }
    if ($mustSay) { $entry.must_say = $mustSay; $entry.said = [bool]($out -like "*$mustSay*") }
    $entry.entry_after = (Entry).present
    $script:exits += $entry
    $ErrorActionPreference = 'Stop'
    WatchShortcuts $title
}
Run 'first start: Install, then the driver asks for the Windows restart' @() 'The install step PASSED'
Run 'second start on the same start of Windows: the restart check must ask for the restart' @() 'Windows has not been restarted since the install step'
# What Windows would say after a restart: the record of the install step, one start later.
$bootFile = Join-Path $evidence 'stage7-install-boot.json'
$later = Join-Path $Base 'boot-after-restart.json'
if (Test-Path -LiteralPath $bootFile) {
    $then = Get-Content -LiteralPath $bootFile -Raw | ConvertFrom-Json
    $now = [ordered]@{ boot_id = $(if ($null -ne $then.boot_id) { [long]$then.boot_id + 1 }); os_start_record = $(if ($null -ne $then.os_start_record) { [long]$then.os_start_record + 1 })
                       uptime_seconds = 60; last_boot_utc = (Get-Date).ToUniversalTime().ToString('o'); note = 'rehearsal: stands in for a restart of Windows' }
    [IO.File]::WriteAllText($later, (ConvertTo-Json -InputObject $now), (New-Object Text.UTF8Encoding $false))
    Run 'third start as after a restart (-BootIdentityFile): AfterRestart, Uninstall, Update, Interrupt' @('-BootIdentityFile', $later) 'ALL STAGE 7 STEPS PASSED'
    Run 'fourth start: nothing left to do' @('-BootIdentityFile', $later) 'ALL STAGE 7 STEPS PASSED'
} else {
    Add-Content -LiteralPath $log -Value 'The install step left no stage7-install-boot.json: the pass ends here.'
    $exits += [ordered]@{ step = 'install record'; exit = 1; must_say = 'stage7-install-boot.json exists'; said = $false }
}
# The pass leaves the sandbox installed with its Installed-apps entry: clean up through the sandbox's own uninstaller
# (the one in the sandbox staging folder; it runs the sandbox's installer with uninstall --home <sandbox>).
$uninstaller = Join-Path $staging 'unins000.exe'
$cleanup = [ordered]@{ uninstaller = $uninstaller; present = (Test-Path -LiteralPath $uninstaller); entry_before_cleanup = (Entry) }
if ($cleanup.present) {
    $ulog = Join-Path $Base 'cleanup-uninstall.log'
    $t = [Diagnostics.Stopwatch]::StartNew()
    $u = Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', "/LOG=`"$ulog`"") -PassThru -Wait
    $null = $u.Handle
    $deadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $deadline -and ((Test-Path -LiteralPath $staging) -or (Test-Path -LiteralPath $key))) { Start-Sleep -Milliseconds 500 }
    $ur = $null; try { $ur = Get-Content -LiteralPath ($staging.TrimEnd('\') + '-uninstall-result.json') -Raw | ConvertFrom-Json } catch {}
    $cleanup.uninstaller_exit = $u.ExitCode; $cleanup.seconds = [Math]::Round($t.Elapsed.TotalSeconds, 1); $cleanup.installer_status = $ur.status; $cleanup.installer_shortcuts = $ur.shortcuts
    $cleanup.program_files_removed = $ur.program_files_removed; $cleanup.kept = $ur.kept
}
$cleanup.entry_after_cleanup = (Entry); $cleanup.package_folder_left = (Test-Path -LiteralPath $staging); $cleanup.data_kept = (Test-Path -LiteralPath (Join-Path $home_ 'data\jarvis.sqlite3'))
$cleanup.clean = [bool]($cleanup.present -and $cleanup.uninstaller_exit -eq 0 -and $cleanup.installer_status -eq 'uninstalled' -and "$($cleanup.installer_shortcuts)" -like 'withheld*' -and -not $cleanup.entry_after_cleanup.present -and -not $cleanup.package_folder_left)
$exits += [ordered]@{ step = 'cleanup: the sandbox uninstalled through its own entry'; cleanup = $cleanup }
Add-Content -LiteralPath $log -Value ("cleanup: " + (ConvertTo-Json -InputObject $cleanup -Compress -Depth 4))
WatchShortcuts 'cleanup'
if (-not $cleanup.clean) {
    # The sandbox's entry or package folder is still there: the rehearsal did not clean up after itself, which the
    # plan requires of a sandbox test; said plainly and the run marked STOPPED.
    Add-Content -LiteralPath $log -Value 'FAIL: the cleanup did not remove the sandbox install, its entry and its package folder (or the installer did not withhold the real shortcuts).'
    $null = Summary 'STOPPED: the cleanup left the sandbox entry or package folder'
    exit 2
}
$summary = Summary 'finished'
Add-Content -LiteralPath $log -Value "live JARVIS processes at the end: $($summary.live_processes_now) (start: $liveBefore); sandbox processes at the end: $($summary.sandbox_processes_now); real shortcuts unchanged: $($summary.real_shortcuts_unchanged); entry now: $($summary.entry_now.present)"
