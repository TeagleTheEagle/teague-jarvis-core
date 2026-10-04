<#
.SYNOPSIS
The one "next step" launcher for Stage 6 Gates 17 and 19 on the host (simplified acceptance, approved 2026-10-02).
Started by next-step.cmd in either account. It reads the evidence folder, works out what is next and, when that
step belongs to the account it was started from, runs it. Otherwise it says where the next step is. It never
skips ahead and never repeats a step that failed.

  owner account (jonny)      : build the two package discs
  validation (jarvis-s6-val) : attach the discs and start the VM; after the gates, take snapshot GATE17-19-PASS
  inside the VM              : gate.cmd on the package disc (this launcher only points there)
  Claude                     : checks the records; P3 runs only on the owner's "run P3"

VirtualBox is only ever called in the jarvis-s6-val session; under any other account this script never touches it.
#>
param(
    [string] $Root = 'D:\JARVIS-S6-FRESHVM',
    [string] $Plan = (Join-Path $PSScriptRoot 'gate17-plan.json'),
    # Testing only: print the decision without running anything; pretend to be an account / a VM state.
    [switch] $WhatIf, [string] $Account = $env:USERNAME, [string] $AssumeVmState
)
$ErrorActionPreference = 'Stop'
function Say($text) { Write-Host $text }
function Done($text) { Say ''; Say $text; exit 0 }
function Halt($text) { Say ''; Say "STOPPED: $text"; Say 'Photograph this window for Claude and wait.'; exit 2 }
function Run($description, $script, [hashtable] $arguments) {
    Say ''; Say "NEXT STEP: $description"
    if ($WhatIf) { Say ("  (test mode) would run {0} {1}" -f (Split-Path -Leaf $script), (($arguments.GetEnumerator() | Sort-Object Key | ForEach-Object { "-$($_.Key) $($_.Value)" }) -join ' ')); exit 0 }
    & $script @arguments
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    exit 0
}
if (-not (Test-Path -LiteralPath $Plan)) { Halt "the plan file $Plan is missing (Claude writes it after the FINAL selection)." }
$p = Get-Content -LiteralPath $Plan -Raw | ConvertFrom-Json
$owner = ($Account -eq 'jonny'); $validation = ($Account -eq 'jarvis-s6-val')
if (-not $owner -and -not $validation) { Halt "this launcher runs in the jonny or the jarvis-s6-val account, not $Account." }
$evidence = Join-Path $Root 'evidence\gate17'; $egress = Join-Path $Root 'evidence\guest-egress-01'

# 1. Package discs (owner account): both are built in one go.
$missing = @(@(@('Final', $p.final), @('Previous', $p.previous)) | Where-Object {
    -not ((Test-Path -LiteralPath (Join-Path $Root "media\JARVIS-PACKAGE-$($_[1]).iso")) -and (Test-Path -LiteralPath (Join-Path $evidence "package-disc-$($_[1]).json"))) })
if ($missing) {
    if (-not $owner) { Done 'The next step is in your own account (jonny): the package discs are not built yet. Switch to jonny and double-click next-step there.' }
    foreach ($disc in $missing) {
        Say ''; Say "NEXT STEP: build the package disc for $($disc[1]) ($($disc[0]))"
        if ($WhatIf) { Say "  (test mode) would run New-Gate17PackageDisc.ps1 -ReleaseId $($disc[1]) -Role $($disc[0])"; continue }
        & (Join-Path $PSScriptRoot 'New-Gate17PackageDisc.ps1') -ReleaseId $disc[1] -Role $disc[0]
    }
    Done 'Both package discs are built. The next step is in the jarvis-s6-val account: switch to it and double-click next-step there.'
}

# 2. Where the gates inside the VM stand (records in the egress folder, written by gate.cmd).
$marker = Join-Path $egress 'gate17-cycle.json'
$guestDone = $false; $guestFailed = $null
if (Test-Path -LiteralPath $marker) {
    $cycle = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
    if ($cycle.release -ne $p.final) { Halt "the gate inside the VM was started with $($cycle.release), the plan says $($p.final)." }
    $start = [datetime]::Parse($cycle.started_utc).ToUniversalTime()
    $runs = @(Get-ChildItem -LiteralPath $egress -Directory | Where-Object { $_.Name -match '^gate1[79]-\d{8}-\d{6}$' } | ForEach-Object {
        $s = Join-Path $_.FullName 'SUMMARY.json'
        if (Test-Path -LiteralPath $s) { $j = Get-Content -LiteralPath $s -Raw | ConvertFrom-Json; [pscustomobject]@{ folder = $_.Name; phase = $j.phase; overall = $j.overall; started = [datetime]::Parse($j.started_utc).ToUniversalTime() } }
    } | Where-Object { $_.started -ge $start.AddSeconds(-1) })
    $guestFailed = $runs | Where-Object { $_.overall -ne 'PASS' } | Select-Object -First 1
    $guestDone = [bool]($runs | Where-Object { $_.phase -eq 'Update' -and $_.overall -eq 'PASS' })
}
if ($guestFailed) { Halt "a step inside the VM did not pass ($($guestFailed.phase), $($guestFailed.folder)). Nothing is repeated without a decision." }

# 3. Everything else is in the validation account.
$snapshot = @(Get-ChildItem -LiteralPath (Join-Path $evidence 'vm') -Filter 'snapshot-GATE17-19-PASS-*.json' -ErrorAction SilentlyContinue)
if ($snapshot) { Done 'Gates 17 and 19 are recorded and the snapshot GATE17-19-PASS is taken. Tell Claude: gate 17 done. (Next: Claude checks the records, then "run P3".)' }
if (-not $validation) {
    if ($guestDone) { Done 'The next step is in the jarvis-s6-val account: the snapshot. Switch to jarvis-s6-val and double-click next-step there.' }
    Done 'The discs are built. The next step is in the jarvis-s6-val account: switch to it and double-click next-step there.'
}
if ($env:USERNAME -eq 'jarvis-s6-val' -and -not $AssumeVmState) {
    if ($env:VBOX_USER_HOME -ne "$Root\vbox-home") { Halt 'VBOX_USER_HOME is not set in this window. Close it, open a NEW File Explorer window and try again.' }
    $state = ((& 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe' showvminfo 'JARVIS-S6-FRESH' --machinereadable | Where-Object { $_ -like 'VMState=*' } | Select-Object -First 1) -replace '^VMState="?(.*?)"?$', '$1')
} else { $state = $AssumeVmState }
if (-not $state) { Halt 'the state of the VM could not be read.' }
if ($guestDone) {
    if ($state -ne 'poweroff') { Done 'All steps inside the VM passed, but the VM is still on. Inside the VM: Start > Power > Shut down. When the VM window has closed, double-click next-step again.' }
    Run 'take the snapshot GATE17-19-PASS' (Join-Path $PSScriptRoot 'Take-FreshVmSnapshot.ps1') @{ Snapshot = 'GATE17-19-PASS'; Evidence = (Join-Path $evidence 'vm'); Description = "Gates 17 and 19 passed inside the VM with $($p.final); taken after a clean shutdown, before P3" }
}
if ($state -eq 'poweroff') {
    Run 'attach the two package discs and start the VM' (Join-Path $PSScriptRoot 'Start-Gate17Vm.ps1') @{ FinalId = $p.final; PreviousId = $p.previous }
}
Done 'The VM is running. The next step is inside the VM: sign in, open the JARVIS_PKG disc in File Explorer and double-click gate.'
