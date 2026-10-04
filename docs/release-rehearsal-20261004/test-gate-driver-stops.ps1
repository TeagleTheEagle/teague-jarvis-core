# Stop and rerun behaviour of tools\guest\Invoke-Gate.ps1 with made-up records (no phase is really run: every case
# must stop, or wait for the restart, before it would start one).
$ErrorActionPreference = 'Stop'
$driver = 'C:\Users\jonny\JARVIS-claude-workspace\repo\tools\guest\Invoke-Gate.ps1'
$root = Join-Path $PSScriptRoot 'gate-driver-fake'
function Fresh { if (Test-Path -LiteralPath $root) { Remove-Item -LiteralPath $root -Recurse -Force }; New-Item -ItemType Directory -Path $root | Out-Null
    (@{ release = '1.0.11-60d406fb6398'; started_utc = (Get-Date).ToUniversalTime().AddMinutes(-5).ToString('o') } | ConvertTo-Json) | Set-Content -LiteralPath (Join-Path $root 'gate17-cycle.json') -Encoding ascii }
function Run-Record($offsetSeconds, $gate, $phase, $overall, $finishedOffsetMinutes) {
    $dir = Join-Path $root ("$gate-" + (Get-Date).ToUniversalTime().AddSeconds($offsetSeconds).ToString('yyyyMMdd-HHmmss')); New-Item -ItemType Directory -Path $dir | Out-Null
    if ($phase) { (@{ phase = $phase; overall = $overall; finished_utc = (Get-Date).ToUniversalTime().AddMinutes($finishedOffsetMinutes).ToString('o') } | ConvertTo-Json) | Set-Content -LiteralPath (Join-Path $dir 'SUMMARY.json') -Encoding ascii }
}
function Try-It($label, $mode) {
    $extra = @(if ($mode) { $mode })
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $driver @extra -Evidence $root -Package 'D:\JARVIS-release-work\pkg-1.0.11' -PreviousPackage 'D:\JARVIS-release-work\pkg-1.0.10' -InstallHome (Join-Path $root 'home') -Staging (Join-Path $root 'staging') -NoShortcuts | Out-String
    "--- $label (exit $LASTEXITCODE)`n" + $out.Trim()
}
Fresh; Run-Record -240 'gate17' 'Install' 'FAIL' 0
Try-It 'A: Install failed earlier -> must stop, not run again' ''
Try-It 'A2: same with the word rerun -> must still stop (a failure is never rerun)' 'rerun'
Fresh; Run-Record -240 'gate17' 'Install' 'PASS' 600
Try-It 'B: Install passed, Windows not restarted since -> must ask for the restart' ''
Fresh; Run-Record -240 'gate17' 'Install' 'PASS' -100000; Run-Record -180 'gate17' 'AfterRestart' 'PASS' 0; Run-Record -120 'gate17' $null $null 0
Try-It 'C: a run never finished -> must stop and mention rerun' ''
Fresh; '{ "release": "9.9.9-other", "started_utc": "2026-01-01T00:00:00Z" }' | Set-Content -LiteralPath (Join-Path $root 'gate17-cycle.json') -Encoding ascii
Try-It 'D: the gate was started with a different build -> must stop' ''
'--- driver log of case D folder:'; Get-Content -LiteralPath (Join-Path $root 'gate-driver-log.jsonl')
