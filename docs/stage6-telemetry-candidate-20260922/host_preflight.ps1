param([Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{32}$')][string]$RunId)
$ErrorActionPreference = 'Stop'
# The only selectable destination is a precreated run below this NEW tool directory.
# Historical script/evidence paths are not accepted as arguments.
$root = Join-Path $PSScriptRoot 'final'
$run = Join-Path $root $RunId
foreach ($p in @($PSScriptRoot,$root,$run)) {
    $item = Get-Item -LiteralPath $p -ErrorAction Stop
    if (!$item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Invalid evidence directory' }
}
$output = Join-Path $run 'final-host-state.json'
$stream = $null
try {
    # Atomic reservation occurs BEFORE any process/trace query. No check-then-write race.
    try { $stream = [IO.FileStream]::new($output,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read) }
    catch { throw "FINAL_EVIDENCE_CREATE_REJECTED: $output : $($_.Exception.Message)" }
    $all = @(Get-CimInstance Win32_Process)
    $matching = @($all | Where-Object { $_.ProcessId -ne $PID -and ($_.Name -match '^(VBox|VirtualBox|J6)' -or ($_.Name -match '^(python|pwsh|powershell)' -and $_.CommandLine -like '*D:\JARVIS-STAGE6-LIVE*')) } | Select-Object ProcessId,Name,CreationDate,ExecutablePath)
    $traceOutput = @(& logman query -ets 2>&1 | ForEach-Object { "$_" })
    if ($LASTEXITCODE -ne 0) { throw 'Trace session enumeration failed' }
    $traces = @($traceOutput | Where-Object { $_ -match '(?i)J6|JARVIS|Stage6' })
    $result = [ordered]@{utc=[DateTime]::UtcNow.ToString('o');runId=$RunId;matchingProcessCount=$matching.Count;matchingProcesses=$matching;diagnosticTraceCount=$traces.Count;diagnosticTraces=$traces;traceEnumeration=$traceOutput;protectedFilesAccessed=$false;productionChanged=$false;status=$(if($matching.Count -eq 0 -and $traces.Count -eq 0){'PASS'}else{'BLOCKED'})}
    $bytes = [Text.Encoding]::UTF8.GetBytes(($result | ConvertTo-Json -Depth 8))
    $stream.Write($bytes,0,$bytes.Length); $stream.Flush($true)
    $result | ConvertTo-Json -Depth 8
    if ($result.status -ne 'PASS') { throw 'Host preflight blocked' }
} finally { if ($null -ne $stream) { $stream.Dispose() } }
