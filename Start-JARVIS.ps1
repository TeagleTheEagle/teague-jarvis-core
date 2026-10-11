$ErrorActionPreference = 'Stop'
$jarvisRoot = $PSScriptRoot
# ONE CORE, MANY CLIENTS: where the desktop app is installed, every launcher opens it and
# it joins (or starts) the shared background Core. The browser-only Core below remains
# only as a fallback for machines without the desktop app.
$jarvisDesktopLauncher = Join-Path $jarvisRoot 'Start-Desktop.ps1'
if ((Test-Path -LiteralPath (Join-Path $jarvisRoot 'desktop/node_modules/electron/dist/electron.exe')) -and (Test-Path -LiteralPath $jarvisDesktopLauncher)) {
    & $jarvisDesktopLauncher
    exit 0
}
$jarvisPython = Join-Path $jarvisRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $jarvisPython)) {
    $jarvisBundledPython = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
    if (Test-Path -LiteralPath $jarvisBundledPython) { $jarvisPython = $jarvisBundledPython }
    else {
        $jarvisCommand = Get-Command python -ErrorAction SilentlyContinue
        if (-not $jarvisCommand) { throw 'Python 3.11+ is required. Install Python, then run this launcher again.' }
        $jarvisPython = $jarvisCommand.Source
    }
}
$jarvisPort = 8765
$jarvisConfig = Join-Path $jarvisRoot '.env'
if (Test-Path -LiteralPath $jarvisConfig) {
    foreach ($jarvisLine in [IO.File]::ReadAllLines($jarvisConfig)) {
        if ($jarvisLine -match '^JARVIS_PORT=(\d+)$') { $jarvisPort = [int]$Matches[1] }
    }
}
$jarvisUrl = "http://127.0.0.1:$jarvisPort"
# One Core per data folder: if another launcher (normally the desktop app) already owns
# the Core on a different port, do not start a second JARVIS that shares its memory.
$jarvisOwnerFile = Join-Path $jarvisRoot 'data/core-owner.json'
if (Test-Path -LiteralPath $jarvisOwnerFile) {
    try {
        $jarvisOwner = Get-Content -LiteralPath $jarvisOwnerFile -Raw | ConvertFrom-Json
        if ($jarvisOwner.port -ne $jarvisPort -and (Get-Process -Id $jarvisOwner.pid -ErrorAction SilentlyContinue)) {
            Add-Type -AssemblyName PresentationFramework
            [void][System.Windows.MessageBox]::Show('JARVIS is already running in the desktop app. Use that window (or quit it first): only one JARVIS Core may own its memory.', 'JARVIS')
            exit 0
        }
    } catch {}
}
$jarvisAlreadyRunning = $false
try {
    $jarvisResponse = Invoke-WebRequest -Uri $jarvisUrl -UseBasicParsing -TimeoutSec 2
    $jarvisAlreadyRunning = $jarvisResponse.Content -like '*JARVIS*'
} catch {}
if (-not $jarvisAlreadyRunning) {
    $jarvisServerPath = Join-Path $jarvisRoot 'server.py'
    $jarvisProcess = Start-Process -FilePath $jarvisPython -ArgumentList @(('"' + $jarvisServerPath + '"')) -WorkingDirectory $jarvisRoot -WindowStyle Hidden -PassThru
    $jarvisReady = $false
    for ($jarvisTry = 0; $jarvisTry -lt 30; $jarvisTry++) {
        Start-Sleep -Milliseconds 200
        try { $null = Invoke-WebRequest -Uri $jarvisUrl -UseBasicParsing -TimeoutSec 1; $jarvisReady = $true; break } catch {}
    }
    if (-not $jarvisReady) { throw 'JARVIS could not start. Run python server.py from this folder to see the error.' }
}
# Open the Core in a desktop-style window. Edge's --app= on its own is not enough: when Edge has
# only background (startup-boost) processes and no window to hand off to, it exits showing nothing
# and the owner is left thinking JARVIS failed to start even though the Core is serving fine. So a
# window is verified to have really appeared, then --new-window is tried, then the default browser.
$jarvisEdge = @(
    (Join-Path ${env:ProgramFiles(x86)} 'Microsoft/Edge/Application/msedge.exe'),
    (Join-Path $env:ProgramFiles 'Microsoft/Edge/Application/msedge.exe'),
    (Join-Path $env:LOCALAPPDATA 'Microsoft/Edge/Application/msedge.exe')
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

# Every Edge window title visible right now. Wrapped in @() at each use: a scriptblock that returns
# an empty array hands back $null, which under $ErrorActionPreference = 'Stop' would abort this script.
$jarvisEdgeTitles = {
    @(Get-Process msedge -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowTitle } |
        ForEach-Object { $_.MainWindowTitle })
}
# A new window is one whose title was not there before the launch, so an Edge window the owner
# already had open is not mistaken for the window this launcher asked for.
$jarvisWindowAppeared = {
    param($jarvisKnown)
    $jarvisKnown = @($jarvisKnown)
    for ($jarvisTry = 0; $jarvisTry -lt 25; $jarvisTry++) {
        Start-Sleep -Milliseconds 200
        foreach ($jarvisTitle in @(& $jarvisEdgeTitles)) {
            if ($jarvisKnown -notcontains $jarvisTitle) { return $true }
        }
    }
    return $false
}

$jarvisBefore = @(& $jarvisEdgeTitles)
$jarvisWindowShown = $false
if ($jarvisEdge) {
    Start-Process -FilePath $jarvisEdge -ArgumentList @("--app=$jarvisUrl")
    $jarvisWindowShown = [bool](& $jarvisWindowAppeared $jarvisBefore)
    if (-not $jarvisWindowShown) {
        # --app= handed off to a windowless background instance and showed nothing.
        Start-Process -FilePath $jarvisEdge -ArgumentList @('--new-window', $jarvisUrl)
        $jarvisWindowShown = [bool](& $jarvisWindowAppeared $jarvisBefore)
    }
}
if (-not $jarvisWindowShown) { Start-Process $jarvisUrl }
