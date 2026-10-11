<#
.SYNOPSIS
One command for Stage 7 (packaged-application acceptance; also the standard check of a release before it is
offered to the everyday JARVIS) inside the acceptance VM. Started by stage7.cmd at the root of the package disc.
A copy of the Gates 17/19 driver Invoke-Gate.ps1 (evidence, unchanged) with the Interrupt phase added and the
restart check done by uptime instead of wall-clock time. It reads the records already in the evidence folder,
works out which phase is next and runs it with Invoke-Stage7.ps1:

  Install -> (owner: quit JARVIS from the tray, restart Windows, sign in) -> AfterRestart -> Uninstall
          -> Update (previous build, update, rollback, update again) -> Interrupt (update killed mid-copy, rerun)

Rules (no silent retry): a phase that FAILED is never run again by this script; the pass stops for the owner's
decision. A run that never finished (Windows was reset under the 15-minute hang rule) is run again only when
stage7.cmd is started with the word rerun, and the rerun is recorded as such. Every start of this script adds a
line to stage7-driver-log.jsonl in the evidence folder.

Version 2 (tools\guest\stage7-v2, for every check after 1.0.11; the 1.0.11 scripts in tools\guest stay unchanged
as evidence): the disc carries stage7-target.json naming this check's own folder in the egress share
(stage7-<label>, created on the PC by Claude when the owner approves the check, never here), so each check keeps
its own records; and the E0 record also notes the Windows build.
#>
param(
    [string] $Mode = '',                                   # 'rerun' = repeat a phase whose last run never finished
    [string] $Evidence = '',
    [string] $Share = '\\VBOXSVR\guest-egress-01',
    [string] $Package = '',
    [string] $PreviousPackage,
    # Local rehearsal only (never on the VM):
    [string] $InstallHome, [string] $Staging, [switch] $NoShortcuts, [switch] $NoRestartCheck, [string[]] $SkipPhases = @(),
    [string] $EgressRoot = 'Z:\'
)
$ErrorActionPreference = 'Stop'
# Set here, not as the parameter default: PowerShell 5.1 can leave $PSScriptRoot empty in a parameter default.
if (-not $Package) { $Package = Split-Path -Parent $PSScriptRoot }
$Utf8 = New-Object Text.UTF8Encoding $false
$Rerun = ($Mode -eq 'rerun')
function Now { (Get-Date).ToUniversalTime().ToString('o') }
function Say($text) { Write-Host $text }
function Stop-Here($code, $text) { Say ''; Say "STOPPED: $text"; Say 'Photograph this window for Claude and wait.'; Log @{ outcome = 'stopped'; reason = $text }; exit $code }
function Log($entry) {
    if (-not $Evidence -or -not (Test-Path -LiteralPath $Evidence)) { return }
    $line = [ordered]@{ utc = (Now); mode = $Mode; package = $Package }
    foreach ($key in $entry.Keys) { $line[$key] = $entry[$key] }
    [IO.File]::AppendAllText((Join-Path $Evidence 'stage7-driver-log.jsonl'), ((ConvertTo-Json -InputObject $line -Depth 4 -Compress) + "`n"), $Utf8)
}

# 1. The build on this disc, and the evidence folder its check writes to (named on the disc).
$record = Get-ChildItem -LiteralPath $Package -Filter 'JARVIS-*.release.json' -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $record) { Stop-Here 3 "no JARVIS release record in $Package" }
$release = (Get-Content -LiteralPath $record.FullName -Raw | ConvertFrom-Json).release_id
if (-not $Evidence) {
    $targetFile = Join-Path $Package 'stage7-target.json'
    if (-not (Test-Path -LiteralPath $targetFile)) { Stop-Here 3 "this disc has no stage7-target.json; it was not built for a version 2 check." }
    $target = Get-Content -LiteralPath $targetFile -Raw | ConvertFrom-Json
    if ($target.release_id -ne $release) { Stop-Here 3 "this disc's target names $($target.release_id) but the disc holds $release." }
    if ($target.egress_folder -notmatch '^stage7-[A-Za-z0-9._-]+$') { Stop-Here 3 "this disc's target folder name is not valid: $($target.egress_folder)" }
    $Evidence = Join-Path $EgressRoot $target.egress_folder
}

# 2. The evidence folder (the VM's single egress), mounted by hand and never remembered by Windows. This check's
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

# 5. Run what is next.
$order = @('Install', 'AfterRestart', 'Uninstall', 'Update', 'Interrupt') | Where-Object { $_ -notin $SkipPhases }
function UptimeSeconds { [Math]::Round(((Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime).TotalSeconds, 0) }
$uptimeFile = Join-Path $Evidence 'stage7-install-uptime.json'
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
        # Restarted = Windows has been up for a shorter time now than when the install step finished. Both values are
        # "now minus boot time" read from the guest's own clock at that moment, so a slow guest clock cannot mislead.
        $then = $null; try { $then = (Get-Content -LiteralPath $uptimeFile -Raw | ConvertFrom-Json).uptime_seconds } catch {}
        if ($null -ne $then -and (UptimeSeconds) -ge $then) {
            Say ''; Say 'Windows has not been restarted since the install step. Do this now:'
            Say '  1. Near the clock, right-click the JARVIS icon (click the ^ arrow if it is hidden) and choose "Quit JARVIS completely".'
            Say '  2. Start > Power > Restart.'
            Say '  3. Sign in again, wait one minute, then open this disc and double-click stage7 again.'
            Log @{ outcome = 'waiting for the Windows restart' }; exit 0
        }
    }
    if ($phase -in 'Update', 'Interrupt' -and -not $PreviousPackage) { Stop-Here 3 'the disc with the previous build is not attached, so the update tests cannot run.' }
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
        [IO.File]::WriteAllText($uptimeFile, (ConvertTo-Json -InputObject ([ordered]@{ utc = (Now); uptime_seconds = (UptimeSeconds) })), $Utf8)
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
