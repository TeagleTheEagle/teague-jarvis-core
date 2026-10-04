# Local rehearsal of the Stage 7 driver (tools\guest\Invoke-Stage7Pass.ps1 + Invoke-Stage7.ps1) in a sandbox on
# D: (2026-10-04). Sandbox install home and staging, no shortcuts; the packages are the real 1.0.11 and 1.0.10
# zips with their release records. Sandbox JARVIS windows open on this PC while it runs; the owner's installed
# JARVIS (%LOCALAPPDATA%\JARVIS) is not touched: every check and every stop is limited to the sandbox home.
param([string] $Base = 'D:\JARVIS-release-work\stage7-local')
$ErrorActionPreference = 'Stop'
$driver = 'C:\Users\jonny\JARVIS-claude-workspace\repo\tools\guest\Invoke-Stage7Pass.ps1'
if (Test-Path -LiteralPath $Base) { throw "$Base exists" }
$evidence = Join-Path $Base 'evidence'; New-Item -ItemType Directory -Path $evidence | Out-Null
$common = @('-Evidence', $evidence, '-Package', 'D:\JARVIS-release-work\pkg-1.0.11', '-PreviousPackage', 'D:\JARVIS-release-work\pkg-1.0.10',
            '-InstallHome', (Join-Path $Base 'home'), '-Staging', (Join-Path $Base 'staging'), '-NoShortcuts')
$log = Join-Path $Base 'rehearsal.output.txt'
function Run([string] $title, [string[]] $extra) {
    Add-Content -LiteralPath $log -Value "===== $title  $(Get-Date -Format 'HH:mm:ss')"
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $driver @common @extra 2>&1 | Out-String
    Add-Content -LiteralPath $log -Value $out
    Add-Content -LiteralPath $log -Value "exit=$LASTEXITCODE  $(Get-Date -Format 'HH:mm:ss')"
}
Run 'first start: Install, then the driver asks for the Windows restart' @()
Run 'second start without a restart: the uptime check must refuse' @()
Run 'second start with -NoRestartCheck: AfterRestart, Uninstall, Update, Interrupt' @('-NoRestartCheck')
Run 'third start: nothing left to do' @('-NoRestartCheck')
$live = @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like "$env:LOCALAPPDATA\JARVIS\releases\*" }).Count
$sandbox = @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like (Join-Path $Base '*') }).Count
Add-Content -LiteralPath $log -Value "live JARVIS processes at the end: $live; sandbox processes at the end: $sandbox"
