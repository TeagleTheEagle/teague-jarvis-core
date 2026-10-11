<#
.SYNOPSIS
One command for Stage 7 (packaged-application acceptance; also the standard check of a release before it is
offered to the everyday JARVIS) inside the acceptance VM. Started by stage7.cmd at the root of the package disc.
A copy of the Gates 17/19 driver Invoke-Gate.ps1 (evidence, unchanged) with the Interrupt phase added. It reads the
records already in the evidence folder, works out which phase is next and runs it with Invoke-Stage7.ps1:

  Install -> (owner: quit JARVIS from the tray, restart Windows, sign in) -> AfterRestart -> Uninstall
          -> Update (previous build, update, rollback, update again) -> Interrupt (update killed mid-copy, rerun)

Rules (no silent retry): a phase that FAILED is never run again by this script; the pass stops for the owner's
decision. A run that never finished (Windows was reset under the 15-minute hang rule) is run again only when
stage7.cmd is started with the word rerun, and the rerun is recorded as such. Every start of this script adds a
line to stage7-driver-log.jsonl in the evidence folder.

Version 2 (tools\guest\stage7-v2, used for 1.0.12 to 1.0.14; unchanged, evidence): the disc carries
stage7-target.json naming this check's own folder in the egress share (stage7-<label>, created on the PC by Claude
when the owner approves the check, never here), so each check keeps its own records.

Version 3 (tools\guest\stage7-v3, for every check after 1.0.14) fixes the two incidents of the 1.0.14 check
(docs\stage7-1.0.14-evidence\incident-01-z-drive.json and incident-02-restart-check.json):
  1. The evidence path is put together as text, so the egress drive Z: need not exist yet; it is connected below.
     (Version 2 used Join-Path first, which refuses a drive that is not there, and ended before connecting it.)
  2. The restart check asks Windows which start this is (its own count of starts, and the newest "operating system
     started" entry of the System log) and compares that with the record made when the install step passed. However
     long the owner waits after the restart, a restart is seen; and without a restart none is seen, whatever the
     clock or the running time say. (Versions 1 and 2 compared running times, and refused a real restart when
     stage7 was started later after it than Windows had been running at the install step.)
     Without that record, or when Windows offers nothing to compare, the pass stops for a decision; the restarted
     phase is never run unchecked.
#>
param(
    [string] $Mode = '',                                   # 'rerun' = repeat a phase whose last run never finished
    [string] $Evidence = '',
    [string] $Share = '\\VBOXSVR\guest-egress-01',
    [string] $Package = '',
    [string] $PreviousPackage,
    # Local rehearsal and decision tests only (never on the VM; each one used is named in every driver-log line):
    [string] $InstallHome, [string] $Staging, [switch] $NoShortcuts, [switch] $NoRestartCheck, [string[]] $SkipPhases = @(),
    [string] $EgressRoot = 'Z:\',
    [string] $BootIdentityFile,                            # read "which start of Windows is this" from a file instead of Windows
    [switch] $WhatNext                                     # say which phase would run next, and stop before running it
)
$ErrorActionPreference = 'Stop'
# Set here, not as the parameter default: PowerShell 5.1 can leave $PSScriptRoot empty in a parameter default.
if (-not $Package) { $Package = Split-Path -Parent $PSScriptRoot }
$Utf8 = New-Object Text.UTF8Encoding $false
$Rerun = ($Mode -eq 'rerun')
$rehearsal = @(@('InstallHome', $InstallHome), @('Staging', $Staging), @('NoShortcuts', $NoShortcuts), @('NoRestartCheck', $NoRestartCheck), @('SkipPhases', $SkipPhases),
               @('BootIdentityFile', $BootIdentityFile), @('WhatNext', $WhatNext) | Where-Object { $_[1] } | ForEach-Object { $_[0] })
function Now { (Get-Date).ToUniversalTime().ToString('o') }
function Say($text) { Write-Host $text }
function Stop-Here($code, $text) { Say ''; Say "STOPPED: $text"; Say 'Photograph this window for Claude and wait.'; Log @{ outcome = 'stopped'; reason = $text }; exit $code }
function Log($entry) {
    if (-not $Evidence -or -not (Test-Path -LiteralPath $Evidence)) { return }
    $line = [ordered]@{ utc = (Now); mode = $Mode; package = $Package; driver = 3 }
    if ($rehearsal) { $line['rehearsal_only'] = ($rehearsal -join ',') }
    foreach ($key in $entry.Keys) { $line[$key] = $entry[$key] }
    [IO.File]::AppendAllText(($Evidence.TrimEnd('\') + '\stage7-driver-log.jsonl'), ((ConvertTo-Json -InputObject $line -Depth 4 -Compress) + "`n"), $Utf8)
}

# 1. The build on this disc, and the evidence folder its check writes to (named on the disc).
$record = Get-ChildItem -LiteralPath $Package -Filter 'JARVIS-*.release.json' -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $record) { Stop-Here 3 "no JARVIS release record in $Package" }
$release = (Get-Content -LiteralPath $record.FullName -Raw | ConvertFrom-Json).release_id
if (-not $Evidence) {
    $targetFile = Join-Path $Package 'stage7-target.json'
    if (-not (Test-Path -LiteralPath $targetFile)) { Stop-Here 3 "this disc has no stage7-target.json; it was not built for a version 2 or 3 check." }
    $target = Get-Content -LiteralPath $targetFile -Raw | ConvertFrom-Json
    if ($target.release_id -ne $release) { Stop-Here 3 "this disc's target names $($target.release_id) but the disc holds $release." }
    if ($target.egress_folder -notmatch '^stage7-[A-Za-z0-9._-]+$') { Stop-Here 3 "this disc's target folder name is not valid: $($target.egress_folder)" }
    # Put together as text, not with Join-Path: the drive is connected in step 2, and in PowerShell 5.1 Join-Path
    # refuses a drive that does not exist yet (incident 01 of the 1.0.14 check).
    $Evidence = $EgressRoot.TrimEnd('\') + '\' + $target.egress_folder
}

# 2. The evidence folder (the VM's single egress), connected here and never remembered by Windows. This check's
#    folder is created on the PC when the owner approves the check; it is never created here.
if (-not (Test-Path -LiteralPath $Evidence)) {
    if ($Evidence -like 'Z:*') { cmd /c "net use Z: $Share /persistent:no >nul 2>&1" }
    if (-not (Test-Path -LiteralPath $Evidence)) { Say ''; Say "STOPPED: the evidence folder $Evidence cannot be reached. Photograph this window for Claude and wait."; exit 3 }
}

# 3. The disc with the previous build (any other disc drive holding a release record).
if (-not $PreviousPackage) {
    foreach ($drive in [IO.DriveInfo]::GetDrives() | Where-Object { $_.DriveType -eq 'CDRom' -and $_.IsReady }) {
        $other = Get-ChildItem -LiteralPath $drive.RootDirectory.FullName -Filter 'JARVIS-*.release.json' -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($other -and (Get-Content -LiteralPath $other.FullName -Raw | ConvertFrom-Json).release_id -ne $release) { $PreviousPackage = $drive.RootDirectory.FullName }
    }
}

# 4. One cycle per build: only runs made after the cycle marker count, so the Gate 16R baseline runs are ignored.
$marker = Join-Path $Evidence 'stage7-cycle.json'
if (-not (Test-Path -LiteralPath $marker)) {
    [IO.File]::WriteAllText($marker, (ConvertTo-Json -InputObject ([ordered]@{ schema = 'jarvis-gate-cycle-v1'; release = $release; started_utc = (Now); account = "$env:USERDOMAIN\$env:USERNAME" })), $Utf8)
}
$cycle = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
if ($cycle.release -ne $release) { Stop-Here 3 "this disc holds $release but the pass was started with $($cycle.release)" }
$cycleStart = [datetime]::Parse($cycle.started_utc).ToUniversalTime()
function Runs {
    @(Get-ChildItem -LiteralPath $Evidence -Directory | Where-Object { $_.Name -match '^stage7-\d{8}-\d{6}$' } | ForEach-Object {
        $stamp = [datetime]::ParseExact($_.Name.Substring(7), 'yyyyMMdd-HHmmss', [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]'AssumeUniversal, AdjustToUniversal')
        $summary = Join-Path $_.FullName 'SUMMARY.json'
        if (Test-Path -LiteralPath $summary) { $s = Get-Content -LiteralPath $summary -Raw | ConvertFrom-Json; [pscustomobject]@{ folder = $_.Name; started = $stamp; phase = $s.phase; overall = $s.overall; finished_utc = $s.finished_utc } }
        else { [pscustomobject]@{ folder = $_.Name; started = $stamp; phase = $null; overall = 'UNFINISHED'; finished_utc = $null } }
    } | Where-Object { $_.started -ge $cycleStart.AddSeconds(-1) } | Sort-Object started)
}

# Which start of Windows this is. boot_id: Windows' own count of its starts. os_start_record: the number of the newest
# "The operating system started" entry in the System log (numbers only go up). Neither changes while Windows runs,
# however long, and neither depends on the clock. The running time is kept for the record and as the last resort.
function BootIdentity {
    if ($BootIdentityFile) { return (Get-Content -LiteralPath $BootIdentityFile -Raw | ConvertFrom-Json) }
    $bootId = $null; $startRecord = $null; $uptime = $null; $lastBoot = $null
    try { $bootId = (Get-ItemProperty -LiteralPath 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters' -Name BootId -ErrorAction Stop).BootId } catch {}
    try { $startRecord = (Get-WinEvent -FilterHashtable @{ LogName = 'System'; ProviderName = 'Microsoft-Windows-Kernel-General'; Id = 12 } -MaxEvents 1 -ErrorAction Stop).RecordId } catch {}
    try { $boot = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime; $uptime = [Math]::Round(((Get-Date) - $boot).TotalSeconds, 0); $lastBoot = $boot.ToUniversalTime().ToString('o') } catch {}
    [pscustomobject][ordered]@{ boot_id = $bootId; os_start_record = $startRecord; uptime_seconds = $uptime; last_boot_utc = $lastBoot }
}
# Was Windows restarted between the record $then and $now? Answers 'yes', 'no' or 'unknown', and what it went by.
# A count or a log number that moved is a restart (neither moves without one). Both there and neither moved: no
# restart. Only when Windows offered neither does the running time decide, and then only a shorter one proves anything.
function RestartSeen($then, $now) {
    $same = @()
    if ($null -ne $then.boot_id -and $null -ne $now.boot_id) { if ("$($now.boot_id)" -ne "$($then.boot_id)") { return @('yes', 'boot_id') }; $same += 'boot_id' }
    if ($null -ne $then.os_start_record -and $null -ne $now.os_start_record) { if ([long]$now.os_start_record -gt [long]$then.os_start_record) { return @('yes', 'os_start_record') }; $same += 'os_start_record' }
    if ($same) { return @('no', ($same -join '+')) }
    if ($null -ne $then.uptime_seconds -and $null -ne $now.uptime_seconds) { if ([double]$now.uptime_seconds -lt [double]$then.uptime_seconds) { return @('yes', 'uptime') }; return @('unknown', 'uptime') }
    return @('unknown', 'nothing')
}

# 5. Run what is next.
$order = @('Install', 'AfterRestart', 'Uninstall', 'Update', 'Interrupt') | Where-Object { $_ -notin $SkipPhases }
$bootFile = Join-Path $Evidence 'stage7-install-boot.json'
$ranNow = @()
foreach ($phase in $order) {
    $runs = Runs
    $unfinished = @($runs | Where-Object { $_.overall -eq 'UNFINISHED' })
    $handled = @((Get-Content -LiteralPath (Join-Path $Evidence 'stage7-driver-log.jsonl') -ErrorAction SilentlyContinue | ForEach-Object { ($_ | ConvertFrom-Json).rerun_of }) | Where-Object { $_ })
    $openUnfinished = @($unfinished | Where-Object { $_.folder -notin $handled })
    $last = $runs | Where-Object { $_.phase -eq $phase } | Select-Object -Last 1
    if ($last -and $last.overall -eq 'PASS') { continue }
    if ($last -and $last.overall -ne 'PASS') { Stop-Here 2 "the $phase phase failed earlier ($($last.folder)). It is not run again without a decision." }
    if ($openUnfinished) {
        if (-not $Rerun) { Stop-Here 2 "an earlier run did not finish ($($openUnfinished[-1].folder)). If Windows was reset after 15 minutes without progress, start stage7.cmd again with the word rerun." }
        Log @{ outcome = 'rerun'; phase = $phase; rerun_of = $openUnfinished[-1].folder }
        Say "Rerun of the $phase phase recorded (earlier unfinished run: $($openUnfinished[-1].folder))."
    }
    if ($phase -eq 'AfterRestart' -and -not $NoRestartCheck) {
        $then = $null; try { $then = Get-Content -LiteralPath $bootFile -Raw | ConvertFrom-Json } catch {}
        if ($null -eq $then) { Stop-Here 2 "the record of the Windows start the install step ran in (stage7-install-boot.json) is missing or cannot be read, so the restart cannot be checked." }
        $now = BootIdentity
        $seen = RestartSeen $then $now
        Log @{ outcome = 'restart check'; restarted = $seen[0]; by = $seen[1]; then = $then; now = $now }
        if ($seen[1] -eq 'nothing') { Stop-Here 2 'Windows offers nothing here that tells one start from the next, so the restart cannot be checked.' }
        if ($seen[0] -ne 'yes') {
            Say ''; Say 'Windows has not been restarted since the install step. Do this now:'
            Say '  1. Near the clock, right-click the JARVIS icon (click the ^ arrow if it is hidden) and choose "Quit JARVIS completely".'
            Say '  2. Start > Power > Restart.'
            Say '  3. Sign in again, wait one minute, then open this disc and double-click stage7 again.'
            if ($seen[0] -eq 'unknown') { Say "  (This Windows keeps no count of its starts, so the check goes by running time: start stage7 within $([Math]::Max(1, [Math]::Floor([double]$then.uptime_seconds / 60))) minutes of the restart.)" }
            Log @{ outcome = 'waiting for the Windows restart' }; exit 0
        }
    }
    if ($phase -in 'Update', 'Interrupt' -and -not $PreviousPackage) { Stop-Here 3 'the disc with the previous build is not attached, so the update tests cannot run.' }
    if ($WhatNext) { Say "NEXT: $phase"; Log @{ outcome = 'what next'; phase = $phase }; exit 0 }
    $arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $PSScriptRoot 'Invoke-Stage7.ps1'), '-Phase', $phase, '-Package', $Package, '-Evidence', $Evidence)
    if ($phase -in 'Update', 'Interrupt') { $arguments += @('-PreviousPackage', $PreviousPackage) }
    if ($InstallHome) { $arguments += @('-InstallHome', $InstallHome) }
    if ($Staging) { $arguments += @('-Staging', $Staging) }
    if ($NoShortcuts) { $arguments += '-NoShortcuts' }
    Say ''; Say "=== $phase ($release) started $(Get-Date -Format 'HH:mm:ss'); each line below is one finished check ==="
    & powershell @arguments
    $code = $LASTEXITCODE; $ranNow += $phase
    Log @{ outcome = $(if ($code -eq 0) { 'phase passed' } else { 'phase did not pass' }); phase = $phase; exit_code = $code }
    if ($code -ne 0) { Stop-Here 2 "the $phase phase did not pass." }
    if ($phase -eq 'Install') {
        $identity = BootIdentity
        [IO.File]::WriteAllText($bootFile, (ConvertTo-Json -InputObject ([ordered]@{ schema = 'jarvis-stage7-install-boot-v1'; utc = (Now); boot_id = $identity.boot_id; os_start_record = $identity.os_start_record
                                                                                    uptime_seconds = $identity.uptime_seconds; last_boot_utc = $identity.last_boot_utc })), $Utf8)
        Say ''; Say 'The install step PASSED. JARVIS is running. Now do this:'
        Say '  1. Near the clock, right-click the JARVIS icon (click the ^ arrow if it is hidden) and choose "Quit JARVIS completely".'
        Say '  2. Start > Power > Restart.'
        Say '  3. Sign in again, wait one minute, then open this disc and double-click stage7 again.'
        exit 0
    }
}
Say ''; Say "ALL STAGE 7 STEPS PASSED for $release."
Say 'Now shut Windows down: Start > Power > Shut down. Wait until the VM window closes.'
Say 'Then, on the PC in the jarvis-s6-val account, double-click stage7-step again (it takes the snapshot) and tell Claude: stage 7 done'
Log @{ outcome = 'all phases passed'; ran_now = $ranNow }
exit 0
