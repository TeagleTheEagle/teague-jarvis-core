# Local rehearsal of the Stage 7 driver (tools\guest\Invoke-Stage7Pass.ps1 + Invoke-Stage7.ps1) for a new release,
# in a sandbox on D: (same method as docs\release-rehearsal-20261004\rehearse-stage7.ps1, with the two packages as
# parameters). Sandbox install home and staging, no shortcuts. Sandbox JARVIS windows open on this PC while it runs;
# the owner's installed JARVIS (%LOCALAPPDATA%\JARVIS) is never addressed: every check and every stop is limited to
# the sandbox home. The number of live JARVIS processes is recorded before and after and must not change.
param(
    [Parameter(Mandatory)] [string] $Package,          # folder with JARVIS-<final>.zip and its .release.json
    [Parameter(Mandatory)] [string] $PreviousPackage,  # same for the previous build
    [Parameter(Mandatory)] [string] $Base,
    # The version 2 guest scripts (tools\guest\stage7-v2), as the check of every release after 1.0.11 uses them.
    [string] $Driver = ''
)
$ErrorActionPreference = 'Stop'
# Set here, not as the parameter default: PowerShell 5.1 can leave $PSScriptRoot empty in a parameter default.
if (-not $Driver) { $Driver = Join-Path $PSScriptRoot '..\..\tools\guest\stage7-v2\Invoke-Stage7Pass.ps1' }
if (Test-Path -LiteralPath $Base) { throw "$Base exists" }
$evidence = Join-Path $Base 'evidence'; New-Item -ItemType Directory -Path $evidence | Out-Null
$common = @('-Evidence', $evidence, '-Package', $Package, '-PreviousPackage', $PreviousPackage,
            '-InstallHome', (Join-Path $Base 'home'), '-Staging', (Join-Path $Base 'staging'), '-NoShortcuts')
$log = Join-Path $Base 'rehearsal.output.txt'
function LiveCount { @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like "$env:LOCALAPPDATA\JARVIS\releases\*" }).Count }
$liveBefore = LiveCount
Add-Content -LiteralPath $log -Value "live JARVIS processes at the start: $liveBefore"
$exits = @()
function Run([string] $title, [string[]] $extra) {
    # 'Continue' here: under 'Stop', PowerShell 5.1 turns a line the driver writes to its error output into a fatal
    # error and this harness would end mid-pass (first 1.0.12 attempt); the line belongs in the log instead.
    $ErrorActionPreference = 'Continue'
    Add-Content -LiteralPath $log -Value "===== $title  $(Get-Date -Format 'HH:mm:ss')"
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $driver @common @extra 2>&1 | Out-String
    Add-Content -LiteralPath $log -Value $out
    Add-Content -LiteralPath $log -Value "exit=$LASTEXITCODE  $(Get-Date -Format 'HH:mm:ss')"
    $script:exits += [ordered]@{ step = $title; exit = $LASTEXITCODE }
}
Run 'first start: Install, then the driver asks for the Windows restart' @()
Run 'second start without a restart: the uptime check must refuse' @()
Run 'second start with -NoRestartCheck: AfterRestart, Uninstall, Update, Interrupt' @('-NoRestartCheck')
Run 'third start: nothing left to do' @('-NoRestartCheck')
$liveAfter = LiveCount
$sandbox = @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like (Join-Path $Base '*') }).Count
Add-Content -LiteralPath $log -Value "live JARVIS processes at the end: $liveAfter (start: $liveBefore); sandbox processes at the end: $sandbox"
$summary = [ordered]@{ package = $Package; previous_package = $PreviousPackage; base = $Base; steps = $exits
                       live_processes_before = $liveBefore; live_processes_after = $liveAfter; sandbox_processes_after = $sandbox }
[IO.File]::WriteAllText((Join-Path $Base 'rehearsal-summary.json'), (ConvertTo-Json -InputObject $summary -Depth 4), (New-Object Text.UTF8Encoding $false))
