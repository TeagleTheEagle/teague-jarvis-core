<#
.SYNOPSIS
One command for Gates 17 and 19 inside the acceptance VM. Started by gate.cmd at the root of the package disc.
It reads the records already in the evidence folder, works out which phase is next and runs it with
Invoke-Gate17.ps1:

  Install -> (owner: quit JARVIS from the tray, restart Windows, sign in) -> AfterRestart -> Cleanliness
          -> Uninstall -> Update (Gate 19: needs the disc with the previous build)

Rules (no silent retry): a phase that FAILED is never run again by this script; the gate stops for the owner's
decision. A run that never finished (Windows was reset under the 15-minute hang rule) is run again only when
gate.cmd is started with the word rerun, and the rerun is recorded as such. Every start of this script adds a
line to gate-driver-log.jsonl in the evidence folder.
#>
param(
    [string] $Mode = '',                                   # 'rerun' = repeat a phase whose last run never finished
    [string] $Evidence = 'Z:\',
    [string] $Share = '\\VBOXSVR\guest-egress-01',
    [string] $Package = (Split-Path -Parent $PSScriptRoot),
    [string] $PreviousPackage,
    # Local rehearsal only (never on the VM):
    [string] $InstallHome, [string] $Staging, [switch] $NoShortcuts, [switch] $NoRestartCheck, [string[]] $SkipPhases = @()
)
$ErrorActionPreference = 'Stop'
$Utf8 = New-Object Text.UTF8Encoding $false
$Rerun = ($Mode -eq 'rerun')
function Now { (Get-Date).ToUniversalTime().ToString('o') }
function Say($text) { Write-Host $text }
function Stop-Here($code, $text) { Say ''; Say "STOPPED: $text"; Say 'Photograph this window for Claude and wait.'; Log @{ outcome = 'stopped'; reason = $text }; exit $code }
function Log($entry) {
    if (-not (Test-Path -LiteralPath $Evidence)) { return }
    $line = [ordered]@{ utc = (Now); mode = $Mode; package = $Package }
    foreach ($key in $entry.Keys) { $line[$key] = $entry[$key] }
    [IO.File]::AppendAllText((Join-Path $Evidence 'gate-driver-log.jsonl'), ((ConvertTo-Json -InputObject $line -Depth 4 -Compress) + "`n"), $Utf8)
}

# 1. The evidence folder (the VM's single egress), mounted by hand and never remembered by Windows.
if (-not (Test-Path -LiteralPath $Evidence)) {
    if ($Evidence -like 'Z:*') { cmd /c "net use Z: $Share /persistent:no >nul 2>&1" }
    if (-not (Test-Path -LiteralPath $Evidence)) { Say ''; Say "STOPPED: the evidence folder $Evidence cannot be reached. Photograph this window for Claude and wait."; exit 3 }
}

# 2. The build on this disc, and the disc with the previous build (any other disc drive holding a release record).
$record = Get-ChildItem -LiteralPath $Package -Filter 'JARVIS-*.release.json' -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $record) { Stop-Here 3 "no JARVIS release record in $Package" }
$release = (Get-Content -LiteralPath $record.FullName -Raw | ConvertFrom-Json).release_id
if (-not $PreviousPackage) {
    foreach ($drive in [IO.DriveInfo]::GetDrives() | Where-Object { $_.DriveType -eq 'CDRom' -and $_.IsReady }) {
        $other = Get-ChildItem -LiteralPath $drive.RootDirectory.FullName -Filter 'JARVIS-*.release.json' -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($other -and (Get-Content -LiteralPath $other.FullName -Raw | ConvertFrom-Json).release_id -ne $release) { $PreviousPackage = $drive.RootDirectory.FullName }
    }
}

# 3. One cycle per build: only runs made after the cycle marker count, so the Gate 16R baseline runs are ignored.
$marker = Join-Path $Evidence 'gate17-cycle.json'
if (-not (Test-Path -LiteralPath $marker)) {
    [IO.File]::WriteAllText($marker, (ConvertTo-Json -InputObject ([ordered]@{ schema = 'jarvis-gate-cycle-v1'; release = $release; started_utc = (Now); account = "$env:USERDOMAIN\$env:USERNAME" })), $Utf8)
}
$cycle = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
if ($cycle.release -ne $release) { Stop-Here 3 "this disc holds $release but the gate was started with $($cycle.release)" }
$cycleStart = [datetime]::Parse($cycle.started_utc).ToUniversalTime()
function Runs {
    @(Get-ChildItem -LiteralPath $Evidence -Directory | Where-Object { $_.Name -match '^gate1[79]-\d{8}-\d{6}$' } | ForEach-Object {
        $stamp = [datetime]::ParseExact($_.Name.Substring(7), 'yyyyMMdd-HHmmss', [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]'AssumeUniversal, AdjustToUniversal')
        $summary = Join-Path $_.FullName 'SUMMARY.json'
        if (Test-Path -LiteralPath $summary) { $s = Get-Content -LiteralPath $summary -Raw | ConvertFrom-Json; [pscustomobject]@{ folder = $_.Name; started = $stamp; phase = $s.phase; overall = $s.overall; finished_utc = $s.finished_utc } }
        else { [pscustomobject]@{ folder = $_.Name; started = $stamp; phase = $null; overall = 'UNFINISHED'; finished_utc = $null } }
    } | Where-Object { $_.started -ge $cycleStart.AddSeconds(-1) } | Sort-Object started)
}

# 4. Run what is next.
$order = @('Install', 'AfterRestart', 'Cleanliness', 'Uninstall', 'Update') | Where-Object { $_ -notin $SkipPhases }
$ranNow = @()
foreach ($phase in $order) {
    $runs = Runs
    $unfinished = @($runs | Where-Object { $_.overall -eq 'UNFINISHED' })
    $handled = @((Get-Content -LiteralPath (Join-Path $Evidence 'gate-driver-log.jsonl') -ErrorAction SilentlyContinue | ForEach-Object { ($_ | ConvertFrom-Json).rerun_of }) | Where-Object { $_ })
    $openUnfinished = @($unfinished | Where-Object { $_.folder -notin $handled })
    $last = $runs | Where-Object { $_.phase -eq $phase } | Select-Object -Last 1
    if ($last -and $last.overall -eq 'PASS') { continue }
    if ($last -and $last.overall -ne 'PASS') { Stop-Here 2 "the $phase phase failed earlier ($($last.folder)). It is not run again without a decision." }
    if ($openUnfinished) {
        if (-not $Rerun) { Stop-Here 2 "an earlier run did not finish ($($openUnfinished[-1].folder)). If Windows was reset after 15 minutes without progress, start gate.cmd again with the word rerun." }
        Log @{ outcome = 'rerun'; phase = $phase; rerun_of = $openUnfinished[-1].folder }
        Say "Rerun of the $phase phase recorded (earlier unfinished run: $($openUnfinished[-1].folder))."
    }
    if ($phase -eq 'AfterRestart' -and -not $NoRestartCheck) {
        $installed = $runs | Where-Object { $_.phase -eq 'Install' -and $_.overall -eq 'PASS' } | Select-Object -Last 1
        $boot = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToUniversalTime()
        if ($installed -and $boot -lt [datetime]::Parse($installed.finished_utc).ToUniversalTime()) {
            Say ''; Say 'Windows has not been restarted since the install step. Do this now:'
            Say '  1. Near the clock, right-click the JARVIS icon (click the ^ arrow if it is hidden) and choose "Quit JARVIS completely".'
            Say '  2. Start > Power > Restart.'
            Say '  3. Sign in again, wait one minute, then open this disc and double-click gate again.'
            Log @{ outcome = 'waiting for the Windows restart' }; exit 0
        }
    }
    if ($phase -eq 'Update' -and -not $PreviousPackage) { Stop-Here 3 'the disc with the previous build is not attached, so the update test (Gate 19) cannot run.' }
    $arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $PSScriptRoot 'Invoke-Gate17.ps1'), '-Phase', $phase, '-Package', $Package, '-Evidence', $Evidence)
    if ($phase -eq 'Update') { $arguments += @('-PreviousPackage', $PreviousPackage) }
    if ($InstallHome) { $arguments += @('-InstallHome', $InstallHome) }
    if ($Staging) { $arguments += @('-Staging', $Staging) }
    if ($NoShortcuts) { $arguments += '-NoShortcuts' }
    Say ''; Say "=== $phase ($release) started $(Get-Date -Format 'HH:mm:ss'); each line below is one finished check ==="
    & powershell @arguments
    $code = $LASTEXITCODE; $ranNow += $phase
    Log @{ outcome = $(if ($code -eq 0) { 'phase passed' } else { 'phase did not pass' }); phase = $phase; exit_code = $code }
    if ($code -ne 0) { Stop-Here 2 "the $phase phase did not pass." }
    if ($phase -eq 'Install') {
        Say ''; Say 'The install step PASSED. JARVIS is running. Now do this:'
        Say '  1. Near the clock, right-click the JARVIS icon (click the ^ arrow if it is hidden) and choose "Quit JARVIS completely".'
        Say '  2. Start > Power > Restart.'
        Say '  3. Sign in again, wait one minute, then open this disc and double-click gate again.'
        exit 0
    }
}
Say ''; Say "ALL STEPS PASSED for $release (Gate 17 and Gate 19)."
Say 'Now shut Windows down: Start > Power > Shut down. Wait until the VM window closes, then tell Claude: gate 17 done'
Log @{ outcome = 'all phases passed'; ran_now = $ranNow }
exit 0
