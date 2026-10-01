$ErrorActionPreference = 'Stop'
$jarvisRoot = $PSScriptRoot
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
$jarvisEdge = Join-Path ${env:ProgramFiles(x86)} 'Microsoft/Edge/Application/msedge.exe'
if (Test-Path -LiteralPath $jarvisEdge) {
    Start-Process -FilePath $jarvisEdge -ArgumentList @("--app=$jarvisUrl")
} else { Start-Process $jarvisUrl }
