$ErrorActionPreference = 'Stop'
$outputPath = Join-Path $PSScriptRoot $args[0]
if (Test-Path -LiteralPath $outputPath) { throw 'Census output already exists' }
$result = [ordered]@{utc=(Get-Date).ToUniversalTime().ToString('o'); currentCensusPid=$PID; readOnly=$true; status='BLOCKED'}
try {
    $processes = @(Get-CimInstance Win32_Process -ErrorAction Stop)
    $matches = @($processes | Where-Object {
        $_.ProcessId -ne $PID -and (
            $_.Name -match '^J6.*\.exe$' -or
            $_.ExecutablePath -match '^D:\\JARVIS-STAGE6-LIVE\\' -or
            $_.CommandLine -match 'D:\\JARVIS-STAGE6-LIVE\\|timed_monitor\.ps1|protected_baseline_worker|kernel_trace\.exe'
        )
    } | Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CreationDate)
    $vbox = @($processes | Where-Object { $_.Name -match '^(VirtualBox|VirtualBoxVM|VBoxHeadless|VBoxManage|VBoxSVC|VBoxSDS|VBoxNetDHCP|VBoxNetNAT)\.exe$' } | Select-Object ProcessId,Name,CreationDate)
    $traces = @(& "$env:SystemRoot\System32\logman.exe" query -ets 2>&1 | ForEach-Object { "$_" })
    $traceExit = $LASTEXITCODE
    $traceMatches = @($traces | Where-Object { $_ -match '(?i)J6|JARVIS|STAGE[-_ ]?6' })
    $result.processMatches=$matches
    $result.virtualBoxProcesses=$vbox
    $result.traceQueryExitCode=$traceExit
    $result.traceQuery=$traces
    $result.traceMatches=$traceMatches
    if ($traceExit -ne 0) { throw 'Read-only trace enumeration failed' }
    if ($matches.Count -or $traceMatches.Count -or $vbox.Count) { throw 'Unexpected diagnostic process, trace, or VirtualBox process' }
    $result.status='PASS'
    $result.matchingDiagnosticProcesses=0
    $result.matchingDiagnosticTraces=0
} catch {
    $result.error=$_.Exception.Message
}
$result | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $outputPath -Encoding UTF8
$result | ConvertTo-Json -Depth 7
if ($result.status -ne 'PASS') { exit 2 }
