# Decision tests for the version 3 guest driver (tools\guest\stage7-v3\Invoke-Stage7Pass.ps1): how it finds its
# evidence folder from the disc, stops on anything wrong, reaches a folder on a drive that is not connected yet
# (incident 01 of the 1.0.14 check) and tells a restart of Windows from no restart (incident 02).
# Fake disc and egress folders in a scratch folder. No phase ever runs: every phase is skipped, or the driver is
# asked what it would run next (-WhatNext) and stops there; the previous package, install home and staging are
# scratch paths and shortcuts are off. Nothing is installed and no drive is scanned. Not run on the VM.
# Reads (only reads) this PC's count of Windows starts and its System log, for the two cases marked "real".
# Only ever for the version 3 driver: an older driver does not know -WhatNext, ignores it and would start the phase.
param([string] $Scratch = 'D:\JARVIS-release-work\scratch\stage7-v3-pass-test', [string] $Output = '')
$ErrorActionPreference = 'Stop'
$driver = Join-Path $PSScriptRoot '..\..\guest\stage7-v3\Invoke-Stage7Pass.ps1'
if ((Get-Content -LiteralPath $driver -Raw) -notmatch '\[switch\] \$WhatNext') { throw 'this driver has no -WhatNext switch; these tests would start a phase with it. STOP' }
$final = '1.0.15-0123456789ab'; $label = $final
$allSkipped = 'Install,AfterRestart,Uninstall,Update,Interrupt'; $restartNext = 'Install,Uninstall,Update,Interrupt'
$results = @()
function Write-Json($path, $data) { New-Item -ItemType Directory -Force -Path (Split-Path -Parent $path) | Out-Null; [IO.File]::WriteAllText($path, (ConvertTo-Json -InputObject $data -Depth 4)) }
function Fresh([bool] $record = $true, $target = @{ schema = 'jarvis-stage7-target-v1'; release_id = $final; label = $label; egress_folder = "stage7-$label" }, [bool] $egressFolder = $true) {
    if (Test-Path -LiteralPath $Scratch) { Remove-Item -LiteralPath $Scratch -Recurse -Force }
    $script:disc = Join-Path $Scratch 'disc'; $script:egress = Join-Path $Scratch 'egress'; $script:prev = Join-Path $Scratch 'prev'
    New-Item -ItemType Directory -Force -Path $disc, $egress, $prev | Out-Null
    if ($record) { Write-Json (Join-Path $disc "JARVIS-$final.release.json") @{ release_id = $final } }
    if ($target) { Write-Json (Join-Path $disc 'stage7-target.json') $target }
    Write-Json (Join-Path $prev 'JARVIS-1.0.14-e03872680e1d.release.json') @{ release_id = '1.0.14-e03872680e1d' }
    if ($egressFolder) { New-Item -ItemType Directory -Force -Path (Join-Path $egress "stage7-$label") | Out-Null }
}
function Check($name, [int] $exitExpected, [string[]] $expect, [scriptblock] $after, [switch] $FromDisc, [string] $Skip = $allSkipped, [string] $Extra = '', [string[]] $Never = @(), [string] $EgressRoot = '') {
    # -Command, not -File: only -Command passes -SkipPhases as a list (with -File it arrives as one string and no
    # phase would be skipped). Every path is a scratch path without spaces or quotes.
    # -FromDisc: the copy of the driver on the fake disc (disc\guest), started without -Package, as stage7.cmd starts it.
    $packageArgument = "-Package '$disc'"; $script = $driver
    if ($FromDisc) { New-Item -ItemType Directory -Force -Path (Join-Path $disc 'guest') | Out-Null; Copy-Item -LiteralPath $driver -Destination (Join-Path $disc 'guest'); $script = Join-Path $disc 'guest\Invoke-Stage7Pass.ps1'; $packageArgument = '' }
    if (-not $EgressRoot) { $EgressRoot = $egress }
    $command = "& '$script' $packageArgument -EgressRoot '$EgressRoot' -PreviousPackage '$prev' -InstallHome '$(Join-Path $Scratch 'home')' " +
               "-Staging '$(Join-Path $Scratch 'staging')' -NoShortcuts -SkipPhases $Skip $Extra; exit `$LASTEXITCODE"
    # 'Continue' for this one call: a driver that fails with an error message is a FAIL line here, not the end of the tests.
    $ErrorActionPreference = 'Continue'
    $out = (& powershell -NoProfile -ExecutionPolicy Bypass -Command $command 2>&1 | Out-String).Trim(); $code = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($out -match '=== (Install|AfterRestart|Uninstall|Update|Interrupt) ') { throw "a phase started in the test: $out" }
    $ok = ($code -eq $exitExpected) -and -not ($expect | Where-Object { $out -notlike "*$_*" }) -and -not ($Never | Where-Object { $out -like "*$_*" }) -and (& $after)
    $script:results += [ordered]@{ case = $name; passed = [bool]$ok; exit = $code; output = ($out -split "`r?`n" | Select-Object -Last 2) -join ' | ' }
    Write-Host ("{0}  {1}" -f $(if ($ok) { 'PASS' } else { 'FAIL' }), $name)
    if (-not $ok) { Write-Host "      exit $code; got: $out" }
}
$folder = { Join-Path $egress "stage7-$label" }
function LogLines { @(Get-Content -LiteralPath (Join-Path (& $folder) 'stage7-driver-log.jsonl') -ErrorAction SilentlyContinue | ForEach-Object { $_ | ConvertFrom-Json }) }
# One restart decision: the record made when the install step passed ($then; $null = no record), what Windows says
# now ($now; $null = ask this PC's real Windows), and what the driver must do.
function Restart-Case($name, $then, $now, [int] $exitExpected, [string[]] $expect, [string[]] $Never = @(), [scriptblock] $after = { $true }) {
    Fresh
    if ($null -ne $then) { Write-Json (Join-Path (& $folder) 'stage7-install-boot.json') $then }
    $extra = '-WhatNext'
    if ($null -ne $now) { $file = Join-Path $Scratch 'boot-now.json'; Write-Json $file $now; $extra += " -BootIdentityFile '$file'" }
    Check $name $exitExpected $expect $after -Skip $restartNext -Extra $extra -Never $Never
}

# --- the cases of version 2, unchanged in what they ask ---
Fresh; Check 'target names this check: its own folder gets the cycle marker' 0 @("ALL STAGE 7 STEPS PASSED for $final") { (Get-Content -LiteralPath (Join-Path (& $folder) 'stage7-cycle.json') -Raw | ConvertFrom-Json).release -eq $final -and (Test-Path -LiteralPath (Join-Path (& $folder) 'stage7-driver-log.jsonl')) }
Fresh -egressFolder $false; Check 'folder not created on the PC: stops, creates nothing' 3 @('STOPPED', 'cannot be reached') { -not (Test-Path -LiteralPath (& $folder)) -and @(Get-ChildItem -LiteralPath $egress).Count -eq 0 }
Fresh -target @{ release_id = '1.0.99-x'; egress_folder = "stage7-$label" }; Check 'target for another build: stops' 3 @('STOPPED', 'target names 1.0.99-x') { -not (Test-Path -LiteralPath (Join-Path (& $folder) 'stage7-cycle.json')) }
Fresh -target $null; Check 'disc without a target file: stops' 3 @('STOPPED', 'no stage7-target.json') { $true }
Fresh -target @{ release_id = $final; egress_folder = '..\outside' }; Check 'unsafe folder name: stops' 3 @('STOPPED', 'not valid') { -not (Test-Path -LiteralPath (Join-Path $Scratch 'outside')) }
Fresh -record $false; Check 'no release record on the disc: stops cleanly' 3 @('STOPPED', 'no JARVIS release record') { $true }
Fresh; Write-Json (Join-Path (& $folder) 'stage7-cycle.json') @{ release = '1.0.14-e03872680e1d'; started_utc = '2026-10-04T09:00:00Z' }; Check 'cycle of another build in this folder: stops' 3 @('STOPPED', 'started with 1.0.14-e03872680e1d') { $true }
Fresh; Check 'started from the disc without -Package (as stage7.cmd does): finds the disc and its folder' 0 @("ALL STAGE 7 STEPS PASSED for $final") { (Get-Content -LiteralPath (Join-Path (& $folder) 'stage7-cycle.json') -Raw | ConvertFrom-Json).release -eq $final } -FromDisc

# --- incident 01: the egress drive is not connected when the driver starts ---
$free = [char[]](68..89) | Where-Object { -not (Test-Path -LiteralPath "$($_):\") } | Select-Object -First 1   # a drive letter this PC does not have (never Z:)
if ($free) {
    Fresh; Check "egress drive not there ($($free):): stops with the plain message, not with a Join-Path error" 3 @('STOPPED', "the evidence folder $($free):\stage7-$label cannot be reached") { -not (Test-Path -LiteralPath (Join-Path (& $folder) 'stage7-cycle.json')) } -FromDisc -EgressRoot "$($free):\" -Never @('Join-Path', 'Cannot find drive', 'does not exist')
} else { Write-Host 'SKIP  egress drive not there: this PC has no free drive letter between D and Y' }

# --- incident 02: was Windows restarted since the install step? ---
$install = @{ schema = 'jarvis-stage7-install-boot-v1'; utc = '2026-10-04T16:20:52Z'; boot_id = 7; os_start_record = 100; uptime_seconds = 2284; last_boot_utc = '2026-10-04T15:42:48Z' }
Restart-Case 'restarted, and stage7 started 77 minutes later (incident 02): the restart is seen' $install @{ boot_id = 8; os_start_record = 140; uptime_seconds = 4600 } 0 @('NEXT: AfterRestart') @('has not been restarted') {
    $check = LogLines | Where-Object { $_.outcome -eq 'restart check' } | Select-Object -Last 1
    $check.restarted -eq 'yes' -and $check.by -eq 'boot_id' -and $check.driver -eq 3 -and $check.then.boot_id -eq 7 -and $check.now.boot_id -eq 8 -and
        $check.rehearsal_only -like '*BootIdentityFile*' -and $check.rehearsal_only -like '*WhatNext*' -and @(LogLines | Where-Object { $_.outcome -eq 'what next' -and $_.phase -eq 'AfterRestart' }).Count -eq 1 }
Restart-Case 'not restarted, however long Windows has been running: asks for the restart' $install @{ boot_id = 7; os_start_record = 100; uptime_seconds = 90000 } 0 @('Windows has not been restarted since the install step', 'Start > Power > Restart') @('NEXT:', 'within') {
    @(LogLines | Where-Object { $_.outcome -eq 'restart check' -and $_.restarted -eq 'no' -and $_.by -eq 'boot_id+os_start_record' }).Count -eq 1 -and @(LogLines | Where-Object { $_.outcome -eq 'waiting for the Windows restart' }).Count -eq 1 }
Restart-Case 'not restarted, but the running time looks shorter (a clock jump): still asks for the restart' $install @{ boot_id = 7; os_start_record = 100; uptime_seconds = 100 } 0 @('Windows has not been restarted since the install step') @('NEXT:')
Restart-Case 'no count of starts, the System log has a newer start: the restart is seen' @{ boot_id = $null; os_start_record = 100; uptime_seconds = 2284 } @{ boot_id = $null; os_start_record = 140; uptime_seconds = 4600 } 0 @('NEXT: AfterRestart') @('has not been restarted')
Restart-Case 'count unchanged but the System log has a newer start: the restart is seen' $install @{ boot_id = 7; os_start_record = 101; uptime_seconds = 50 } 0 @('NEXT: AfterRestart') @('has not been restarted')
Restart-Case 'neither count nor log, shorter running time: the restart is seen (the rule of versions 1 and 2)' @{ uptime_seconds = 2284 } @{ uptime_seconds = 300 } 0 @('NEXT: AfterRestart') @('has not been restarted')
Restart-Case 'neither count nor log, longer running time: asks for the restart and says within how many minutes' @{ uptime_seconds = 2284 } @{ uptime_seconds = 5000 } 0 @('Windows has not been restarted since the install step', 'within 38 minutes of the restart') @('NEXT:')
Restart-Case 'no record of the install step''s start of Windows: stops, the restarted phase is not run unchecked' $null @{ boot_id = 8; os_start_record = 140; uptime_seconds = 60 } 2 @('STOPPED', 'the restart cannot be checked') @('NEXT:')
Restart-Case 'nothing to compare at all: stops' @{ utc = '2026-10-04T16:20:52Z' } @{ last_boot_utc = '2026-10-05T01:15:30Z' } 2 @('STOPPED', 'tells one start from the next') @('NEXT:')
$realBoot = $null; $realStart = $null
try { $realBoot = (Get-ItemProperty -LiteralPath 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters' -Name BootId -ErrorAction Stop).BootId } catch {}
try { $realStart = (Get-WinEvent -FilterHashtable @{ LogName = 'System'; ProviderName = 'Microsoft-Windows-Kernel-General'; Id = 12 } -MaxEvents 1 -ErrorAction Stop).RecordId } catch {}
if ($null -ne $realBoot -or $null -ne $realStart) {
    Restart-Case 'real: the record is of this very start of this PC: asks for the restart' @{ boot_id = $realBoot; os_start_record = $realStart; uptime_seconds = 1 } $null 0 @('Windows has not been restarted since the install step') @('NEXT:', 'within')
    Restart-Case 'real: the record is of an earlier start of this PC: the restart is seen' @{ boot_id = $(if ($null -ne $realBoot) { $realBoot - 1 }); os_start_record = $(if ($null -ne $realStart) { $realStart - 1 }); uptime_seconds = 1 } $null 0 @('NEXT: AfterRestart') @('has not been restarted')
} else { Write-Host 'SKIP  real: this PC offers neither a count of starts nor a readable System log' }
Fresh; Check 'the rehearsal switch that skips the restart check is named in the log' 0 @('NEXT: AfterRestart') { (LogLines | Select-Object -Last 1).rehearsal_only -like '*NoRestartCheck*' } -Skip $restartNext -Extra '-WhatNext -NoRestartCheck'

if (Test-Path -LiteralPath $Scratch) { Remove-Item -LiteralPath $Scratch -Recurse -Force }
$failed = @($results | Where-Object { -not $_.passed }).Count
Write-Host ''; Write-Host ("{0} cases, {1} failed (this PC: count of starts {2}, newest start entry {3})" -f $results.Count, $failed, $realBoot, $realStart)
if ($Output) { [IO.File]::WriteAllText($Output, (ConvertTo-Json -InputObject $results -Depth 3), (New-Object Text.UTF8Encoding $false)) }
exit $(if ($failed) { 1 } else { 0 })
