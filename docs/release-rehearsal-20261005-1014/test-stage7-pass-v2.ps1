# How the version 2 guest driver (tools\guest\stage7-v2\Invoke-Stage7Pass.ps1) finds its evidence folder from the disc
# and stops on anything wrong. Fake disc and egress folders in a scratch folder; every phase is skipped, the previous
# package, install home and staging are scratch paths and shortcuts are off, so nothing is installed and no drive is
# scanned. Not run on the VM.
param([string] $Scratch = 'D:\JARVIS-release-work\scratch\stage7-v2-pass-test')
$ErrorActionPreference = 'Stop'
$driver = Join-Path $PSScriptRoot '..\..\tools\guest\stage7-v2\Invoke-Stage7Pass.ps1'
$final = '1.0.14-e03872680e1d'; $label = $final
$results = @()
function Write-Json($path, $data) { New-Item -ItemType Directory -Force -Path (Split-Path -Parent $path) | Out-Null; [IO.File]::WriteAllText($path, (ConvertTo-Json -InputObject $data -Depth 4)) }
function Fresh([bool] $record = $true, $target = @{ schema = 'jarvis-stage7-target-v1'; release_id = $final; label = $label; egress_folder = "stage7-$label" }, [bool] $egressFolder = $true) {
    if (Test-Path -LiteralPath $Scratch) { Remove-Item -LiteralPath $Scratch -Recurse -Force }
    $script:disc = Join-Path $Scratch 'disc'; $script:egress = Join-Path $Scratch 'egress'; $script:prev = Join-Path $Scratch 'prev'
    New-Item -ItemType Directory -Force -Path $disc, $egress, $prev | Out-Null
    if ($record) { Write-Json (Join-Path $disc "JARVIS-$final.release.json") @{ release_id = $final } }
    if ($target) { Write-Json (Join-Path $disc 'stage7-target.json') $target }
    Write-Json (Join-Path $prev 'JARVIS-1.0.11-60d406fb6398.release.json') @{ release_id = '1.0.11-60d406fb6398' }
    if ($egressFolder) { New-Item -ItemType Directory -Force -Path (Join-Path $egress "stage7-$label") | Out-Null }
}
function Check($name, [int] $exitExpected, [string[]] $expect, [scriptblock] $after, [switch] $FromDisc) {
    # -Command, not -File: only -Command passes -SkipPhases as a list (with -File it arrives as one string and no
    # phase would be skipped). Every path is a scratch path without spaces or quotes.
    # -FromDisc: the copy of the driver on the fake disc (disc\guest), started without -Package, as stage7.cmd starts it.
    $packageArgument = "-Package '$disc'"; $script = $driver
    if ($FromDisc) { New-Item -ItemType Directory -Force -Path (Join-Path $disc 'guest') | Out-Null; Copy-Item -LiteralPath $driver -Destination (Join-Path $disc 'guest'); $script = Join-Path $disc 'guest\Invoke-Stage7Pass.ps1'; $packageArgument = '' }
    $command = "& '$script' $packageArgument -EgressRoot '$egress' -PreviousPackage '$prev' -InstallHome '$(Join-Path $Scratch 'home')' " +
               "-Staging '$(Join-Path $Scratch 'staging')' -NoShortcuts -SkipPhases Install,AfterRestart,Uninstall,Update,Interrupt; exit `$LASTEXITCODE"
    $out = (& powershell -NoProfile -ExecutionPolicy Bypass -Command $command 2>&1 | Out-String).Trim(); $code = $LASTEXITCODE
    if ($out -match '=== (Install|AfterRestart|Uninstall|Update|Interrupt) ') { throw "a phase started in the test: $out" }
    $ok = ($code -eq $exitExpected) -and -not ($expect | Where-Object { $out -notlike "*$_*" }) -and (& $after)
    $script:results += [ordered]@{ case = $name; passed = [bool]$ok; exit = $code; output = ($out -split "`r?`n" | Select-Object -Last 2) -join ' | ' }
    Write-Host ("{0}  {1}" -f $(if ($ok) { 'PASS' } else { 'FAIL' }), $name)
    if (-not $ok) { Write-Host "      exit $code; got: $out" }
}
$folder = { Join-Path $egress "stage7-$label" }

Fresh; Check 'target names this check: its own folder gets the cycle marker' 0 @("ALL STAGE 7 STEPS PASSED for $final") { (Get-Content -LiteralPath (Join-Path (& $folder) 'stage7-cycle.json') -Raw | ConvertFrom-Json).release -eq $final -and (Test-Path -LiteralPath (Join-Path (& $folder) 'stage7-driver-log.jsonl')) }
Fresh -egressFolder $false; Check 'folder not created on the PC: stops, creates nothing' 3 @('STOPPED', 'cannot be reached') { -not (Test-Path -LiteralPath (& $folder)) -and @(Get-ChildItem -LiteralPath $egress).Count -eq 0 }
Fresh -target @{ release_id = '1.0.99-x'; egress_folder = "stage7-$label" }; Check 'target for another build: stops' 3 @('STOPPED', 'target names 1.0.99-x') { -not (Test-Path -LiteralPath (Join-Path (& $folder) 'stage7-cycle.json')) }
Fresh -target $null; Check 'disc without a target file: stops' 3 @('STOPPED', 'no stage7-target.json') { $true }
Fresh -target @{ release_id = $final; egress_folder = '..\outside' }; Check 'unsafe folder name: stops' 3 @('STOPPED', 'not valid') { -not (Test-Path -LiteralPath (Join-Path $Scratch 'outside')) }
Fresh -record $false; Check 'no release record on the disc: stops cleanly' 3 @('STOPPED', 'no JARVIS release record') { $true }
Fresh; Write-Json (Join-Path (& $folder) 'stage7-cycle.json') @{ release = '1.0.11-60d406fb6398'; started_utc = '2026-10-04T09:00:00Z' }; Check 'cycle of another build in this folder: stops' 3 @('STOPPED', 'started with 1.0.11-60d406fb6398') { $true }
Fresh; Check 'started from the disc without -Package (as stage7.cmd does): finds the disc and its folder' 0 @("ALL STAGE 7 STEPS PASSED for $final") { (Get-Content -LiteralPath (Join-Path (& $folder) 'stage7-cycle.json') -Raw | ConvertFrom-Json).release -eq $final } -FromDisc

if (Test-Path -LiteralPath $Scratch) { Remove-Item -LiteralPath $Scratch -Recurse -Force }
$failed = @($results | Where-Object { -not $_.passed }).Count
Write-Host ''; Write-Host ("{0} cases, {1} failed" -f $results.Count, $failed)
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'test-stage7-pass-v2.output.json'), (ConvertTo-Json -InputObject $results -Depth 3), (New-Object Text.UTF8Encoding $false))
exit $(if ($failed) { 1 } else { 0 })
