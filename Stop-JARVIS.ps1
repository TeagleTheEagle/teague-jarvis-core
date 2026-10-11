$ErrorActionPreference = 'Stop'
$jarvisPort = 8765
$jarvisConfig = Join-Path $PSScriptRoot '.env'
if (Test-Path -LiteralPath $jarvisConfig) {
    foreach ($jarvisLine in [IO.File]::ReadAllLines($jarvisConfig)) {
        if ($jarvisLine -match '^JARVIS_PORT=(\d+)$') { $jarvisPort = [int]$Matches[1] }
    }
}
$jarvisUrl = "http://127.0.0.1:$jarvisPort"
try {
    $jarvisResponse = Invoke-WebRequest -Uri $jarvisUrl -UseBasicParsing -SessionVariable jarvisSession -TimeoutSec 3
    if ($jarvisResponse.Content -notlike '*JARVIS*') { throw 'This address is not serving JARVIS.' }
    $null = Invoke-WebRequest -Uri "$jarvisUrl/api/shutdown" -WebSession $jarvisSession -Method POST -ContentType 'application/json' -Body '{}' -UseBasicParsing -TimeoutSec 3
    Write-Host 'JARVIS stopped.'
} catch { Write-Host 'JARVIS is not running, or could not be reached.' }
