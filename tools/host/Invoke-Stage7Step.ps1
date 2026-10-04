<#
.SYNOPSIS
Stage 7: the one launcher on the PC (stage7-step.cmd). Run BY THE OWNER, in whichever account is right for the
next step; it reads the records, works out what is next and, when that step belongs to the account it was
started from, runs it; otherwise it says where the next step is. It refuses everything until Claude has recorded
the owner's approval of the Stage 7 plan (stage7-authorized.json beside this script, naming the two builds).

  owner account (jonny)      : build the Stage 7 disc
  validation (jarvis-s6-val) : restore the clean snapshot, attach the discs, start the VM;
                               after the pass inside the VM and a shutdown: snapshot STAGE7-PASS

A step that failed inside the VM stops everything; nothing is repeated without a decision.
#>
param(
    [string] $Root = 'D:\JARVIS-S6-FRESHVM',
    [string] $Stage7 = 'D:\JARVIS-stage7',
    [string] $Authorized = (Join-Path $PSScriptRoot 'stage7-authorized.json'),
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
if (-not (Test-Path -LiteralPath $Authorized)) { Halt 'Stage 7 has not been approved yet (Claude records your approval of the plan first).' }
$p = Get-Content -LiteralPath $Authorized -Raw | ConvertFrom-Json
if (-not $p.final -or -not $p.previous) { Halt 'the approval file does not name the two builds.' }
$owner = ($Account -eq 'jonny'); $validation = ($Account -eq 'jarvis-s6-val')
if (-not $owner -and -not $validation) { Halt "this launcher runs in the jonny or the jarvis-s6-val account, not $Account." }
$evidence = Join-Path $Stage7 'evidence'; $egress = Join-Path $Root 'evidence\guest-egress-01\stage7'

# 1. The Stage 7 disc (owner account). The previous build's package disc exists from Stage 6.
$disc = Join-Path $Root "media\JARVIS-STAGE7-$($p.final).iso"
if (-not ((Test-Path -LiteralPath $disc) -and (Test-Path -LiteralPath (Join-Path $evidence "stage7-disc-$($p.final).json")))) {
    if (-not $owner) { Done 'The next step is in your own account (jonny): the Stage 7 disc is not built yet. Switch to jonny and double-click stage7-step there.' }
    Say ''; Say "NEXT STEP: build the Stage 7 disc for $($p.final)"
    if ($WhatIf) { Say "  (test mode) would run New-Stage7Disc.ps1 -ReleaseId $($p.final)"; exit 0 }
    & (Join-Path $PSScriptRoot 'New-Stage7Disc.ps1') -ReleaseId $p.final
    Done 'The Stage 7 disc is built. Tell Claude "disc built". The next step is in the jarvis-s6-val account.'
}

# 2. Where the pass inside the VM stands (records in the egress folder, written by stage7.cmd).
$marker = Join-Path $egress 'stage7-cycle.json'
$guestDone = $false; $guestFailed = $null; $guestStarted = (Test-Path -LiteralPath $marker)
if ($guestStarted) {
    $cycle = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
    if ($cycle.release -ne $p.final) { Halt "the pass inside the VM was started with $($cycle.release), the plan says $($p.final)." }
    $runs = @(Get-ChildItem -LiteralPath $egress -Directory | Where-Object { $_.Name -match '^stage7-\d{8}-\d{6}$' } | ForEach-Object {
        $s = Join-Path $_.FullName 'SUMMARY.json'
        if (Test-Path -LiteralPath $s) { $j = Get-Content -LiteralPath $s -Raw | ConvertFrom-Json; [pscustomobject]@{ folder = $_.Name; phase = $j.phase; overall = $j.overall } }
    })
    $guestFailed = $runs | Where-Object { $_.overall -ne 'PASS' } | Select-Object -First 1
    $guestDone = [bool]($runs | Where-Object { $_.phase -eq 'Interrupt' -and $_.overall -eq 'PASS' })
}
if ($guestFailed) { Halt "a step inside the VM did not pass ($($guestFailed.phase), $($guestFailed.folder)). Nothing is repeated without a decision." }

# 3. Everything else is in the validation account.
$vmEvidence = Join-Path $evidence 'vm'
$snapshot = @(Get-ChildItem -LiteralPath $vmEvidence -Filter 'snapshot-STAGE7-PASS-*.json' -ErrorAction SilentlyContinue)
if ($snapshot) { Done 'Stage 7 is recorded and the snapshot STAGE7-PASS is taken. Tell Claude: stage 7 done.' }
if (-not $validation) {
    if ($guestDone) { Done 'The next step is in the jarvis-s6-val account: the snapshot. Switch to jarvis-s6-val and double-click stage7-step there.' }
    Done 'The disc is built. The next step is in the jarvis-s6-val account: switch to it and double-click stage7-step there.'
}
if ($env:USERNAME -eq 'jarvis-s6-val' -and -not $AssumeVmState) {
    if ($env:VBOX_USER_HOME -ne "$Root\vbox-home") { Halt 'VBOX_USER_HOME is not set in this window. Close it, open a NEW File Explorer window and try again.' }
    $state = ((& 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe' showvminfo 'JARVIS-S6-FRESH' --machinereadable | Where-Object { $_ -like 'VMState=*' } | Select-Object -First 1) -replace '^VMState="?(.*?)"?$', '$1')
} else { $state = $AssumeVmState }
if (-not $state) { Halt 'the state of the VM could not be read.' }
$started = @(Get-ChildItem -LiteralPath $vmEvidence -Filter 'stage7-start-*.json' -ErrorAction SilentlyContinue)
if ($guestDone) {
    if ($state -ne 'poweroff') { Done 'All steps inside the VM passed, but the VM is still on. Inside the VM: Start > Power > Shut down. When the VM window has closed, double-click stage7-step again.' }
    Run 'take the snapshot STAGE7-PASS' (Join-Path $PSScriptRoot 'Take-FreshVmSnapshot.ps1') @{ Snapshot = 'STAGE7-PASS'; Evidence = $vmEvidence; Description = "Stage 7 passed inside the VM with $($p.final) (update from $($p.previous), interrupted update, rollback, uninstall, reinstall); taken after a clean shutdown" }
}
if ($state -eq 'poweroff') {
    if ($started) { Halt 'the VM was already started for Stage 7 and is now off, but the pass inside it did not finish. Nothing is repeated without a decision.' }
    Run 'restore the clean snapshot, attach the two discs and start the VM' (Join-Path $PSScriptRoot 'Start-Stage7Vm.ps1') @{ FinalId = $p.final; PreviousId = $p.previous; Evidence = $vmEvidence }
}
if ($guestStarted) { Done 'The pass is running inside the VM. Follow what its window says (quit JARVIS, restart Windows, double-click stage7 again) until it says ALL STAGE 7 STEPS PASSED.' }
Done 'The VM is running. The next step is inside the VM: sign in, open the JARVIS_S7 disc in File Explorer and double-click stage7.'
