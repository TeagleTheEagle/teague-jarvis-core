$ErrorActionPreference = 'Stop'
$r = $PSScriptRoot
$all = @(Get-CimInstance Win32_Process)
$matching = @($all | Where-Object { $_.ProcessId -ne $PID -and ($_.Name -match '^(VBox|VirtualBox|J6)' -or ($_.Name -match '^(python|pwsh|powershell)' -and $_.CommandLine -like '*D:\JARVIS-STAGE6-LIVE*')) } | Select-Object ProcessId,Name,CreationDate,ExecutablePath)
$traceOutput = @(& logman query -ets 2>&1 | ForEach-Object { "$_" })
if ($LASTEXITCODE -ne 0) { throw 'Trace session enumeration failed' }
$diagnosticTraces = @($traceOutput | Where-Object { $_ -match '(?i)J6|JARVIS|Stage6' })
$result = [ordered]@{ utc = [DateTime]::UtcNow.ToString('o'); matchingProcessCount = $matching.Count; matchingProcesses = $matching; diagnosticTraceCount = $diagnosticTraces.Count; diagnosticTraces = $diagnosticTraces; traceEnumeration = $traceOutput; protectedFilesAccessed = $false; productionChanged = $false }
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $r 'final-host-state.json') -Encoding UTF8
$result | ConvertTo-Json -Depth 8
if ($matching.Count -ne 0 -or $diagnosticTraces.Count -ne 0) { throw 'Cleanup is not closed' }
