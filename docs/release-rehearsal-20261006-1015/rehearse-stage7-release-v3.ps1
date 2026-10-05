# Local rehearsal of the version 3 Stage 7 driver (tools\guest\stage7-v3\Invoke-Stage7Pass.ps1 + Invoke-Stage7.ps1)
# for a new release, in a sandbox on D: (the method of docs\release-rehearsal-20261004-1012\rehearse-stage7-release.ps1).
# Sandbox install home and staging, no shortcuts. Sandbox JARVIS windows open on this PC while it runs; the owner's
# installed JARVIS (%LOCALAPPDATA%\JARVIS) is never addressed: every check and every stop is limited to the sandbox
# home. The number of live JARVIS processes is recorded before and after and must not change.
#
# New with version 3: the restart check is exercised with what Windows really says. After the install step the
# driver is started again on the same start of Windows (it must ask for the restart), and then with a file that
# says "one start later" in place of Windows (the driver's rehearsal switch -BootIdentityFile), which stands in for
# the restart nobody performs here. -NoRestartCheck is not used at all.
param(
    [Parameter(Mandatory)] [string] $Package,          # folder with JARVIS-<final>.zip and its .release.json
    [Parameter(Mandatory)] [string] $PreviousPackage,  # same for the previous build
    [Parameter(Mandatory)] [string] $Base,
    [string] $Driver = ''
)
$ErrorActionPreference = 'Stop'
# Set here, not as the parameter default: PowerShell 5.1 can leave $PSScriptRoot empty in a parameter default.
if (-not $Driver) { $Driver = Join-Path $PSScriptRoot '..\..\tools\guest\stage7-v3\Invoke-Stage7Pass.ps1' }
if ((Get-Content -LiteralPath $Driver -Raw) -notmatch '\[string\] \$BootIdentityFile') { throw 'this is not a version 3 driver. STOP' }
if (Test-Path -LiteralPath $Base) { throw "$Base exists" }
$evidence = Join-Path $Base 'evidence'; New-Item -ItemType Directory -Path $evidence | Out-Null
$common = @('-Evidence', $evidence, '-Package', $Package, '-PreviousPackage', $PreviousPackage,
            '-InstallHome', (Join-Path $Base 'home'), '-Staging', (Join-Path $Base 'staging'), '-NoShortcuts')
$log = Join-Path $Base 'rehearsal.output.txt'
function LiveCount { @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like "$env:LOCALAPPDATA\JARVIS\releases\*" }).Count }
$liveBefore = LiveCount
Add-Content -LiteralPath $log -Value "live JARVIS processes at the start: $liveBefore"
$exits = @()
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
    $script:exits += $entry
    $ErrorActionPreference = 'Stop'
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
$liveAfter = LiveCount
$sandbox = @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like (Join-Path $Base '*') }).Count
Add-Content -LiteralPath $log -Value "live JARVIS processes at the end: $liveAfter (start: $liveBefore); sandbox processes at the end: $sandbox"
$summary = [ordered]@{ package = $Package; previous_package = $PreviousPackage; base = $Base; driver = 3; steps = $exits
                       live_processes_before = $liveBefore; live_processes_after = $liveAfter; sandbox_processes_after = $sandbox }
[IO.File]::WriteAllText((Join-Path $Base 'rehearsal-summary.json'), (ConvertTo-Json -InputObject $summary -Depth 4), (New-Object Text.UTF8Encoding $false))
