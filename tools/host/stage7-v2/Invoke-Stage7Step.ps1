<#
.SYNOPSIS
Stage 7 check of a release (version 2): the one launcher on the PC (stage7-step.cmd in this folder). Run BY THE
OWNER, in whichever account is right for the next step; it reads the records, works out what is next and, when that
step belongs to the account it was started from, runs it; otherwise it says where the next step is. It refuses
everything until Claude has recorded the owner's approval of this check (stage7-authorized.json beside this
script, schema jarvis-stage7-authorized-v2: final, previous, label, expected_current_snapshot).

A copy of tools\host\Invoke-Stage7Step.ps1 (used for 1.0.11; unchanged, evidence) with every name taken from the
check's label, so each check has its own records and the 1.0.11 records are never read as this check's:
  disc            D:\JARVIS-S6-FRESHVM\media\JARVIS-STAGE7-<label>.iso
  host records    <Stage7>\<label>\evidence (default D:\JARVIS-stage7\<label>\evidence), VM records in ...\vm
  guest records   D:\JARVIS-S6-FRESHVM\evidence\guest-egress-01\stage7-<label> (created by Claude on approval)
  snapshot        STAGE7-PASS-<label>

  owner account (jonny)      : build the Stage 7 disc
  validation (jarvis-s6-val) : restore FRESH-PREREQ, attach the discs, start the VM;
                               after the pass inside the VM and a shutdown: snapshot STAGE7-PASS-<label>

A step that failed inside the VM stops everything; nothing is repeated without a decision.
#>
param(
    [string] $Root = 'D:\JARVIS-S6-FRESHVM',
    [string] $Stage7 = 'D:\JARVIS-stage7',
    [string] $Authorized = '',
    [string] $Repo = 'C:\Users\jonny\JARVIS-claude-workspace\repo',
    # Testing only: print the decision without running anything; pretend to be an account / a VM state.
    [switch] $WhatIf, [string] $Account = $env:USERNAME, [string] $AssumeVmState
)
$ErrorActionPreference = 'Stop'
# Set here, not as the parameter default: PowerShell 5.1 can leave $PSScriptRoot empty in a parameter default.
if (-not $Authorized) { $Authorized = Join-Path $PSScriptRoot 'stage7-authorized.json' }
function Say($text) { Write-Host $text }
function Done($text) { Say ''; Say $text; exit 0 }
function Halt($text) { Say ''; Say "STOPPED: $text"; Say 'Photograph this window for Claude and wait.'; exit 2 }
function Run($description, $script, [hashtable] $arguments) {
    Say ''; Say "NEXT STEP: $description"
    if ($WhatIf) { Say ("  (test mode) would run {0} {1}" -f (Split-Path -Leaf $script), (($arguments.GetEnumerator() | Sort-Object Key | ForEach-Object { "-$($_.Key) $($_.Value -join ',')" }) -join ' ')); exit 0 }
    & $script @arguments
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    exit 0
}
if (-not (Test-Path -LiteralPath $Authorized)) { Halt 'this Stage 7 check has not been approved yet (Claude records your approval first).' }
$p = Get-Content -LiteralPath $Authorized -Raw | ConvertFrom-Json
if ($p.schema -ne 'jarvis-stage7-authorized-v2') { Halt 'the approval file is not a version 2 approval (it belongs to another launcher).' }
if (-not $p.final -or -not $p.previous -or -not $p.label -or -not $p.expected_current_snapshot) { Halt 'the approval file does not name the two builds, the label and the expected current snapshot.' }
if ($p.label -notmatch '^[A-Za-z0-9._-]+$') { Halt "the label '$($p.label)' is not valid." }
$owner = ($Account -eq 'jonny'); $validation = ($Account -eq 'jarvis-s6-val')
if (-not $owner -and -not $validation) { Halt "this launcher runs in the jonny or the jarvis-s6-val account, not $Account." }
$evidence = Join-Path $Stage7 "$($p.label)\evidence"; $egress = Join-Path $Root "evidence\guest-egress-01\stage7-$($p.label)"
$passSnapshot = "STAGE7-PASS-$($p.label)"

# 1. The Stage 7 disc (owner account). The previous build's package disc exists already.
$disc = Join-Path $Root "media\JARVIS-STAGE7-$($p.label).iso"
if (-not ((Test-Path -LiteralPath $disc) -and (Test-Path -LiteralPath (Join-Path $evidence "stage7-disc-$($p.label).json")))) {
    if (-not $owner) { Done 'The next step is in your own account (jonny): the Stage 7 disc is not built yet. Switch to jonny and double-click stage7-step there.' }
    Say ''; Say "NEXT STEP: build the Stage 7 disc for $($p.final)"
    if ($WhatIf) { Say "  (test mode) would run New-Stage7Disc.ps1 -Evidence $evidence -Label $($p.label) -ReleaseId $($p.final) -Repo $Repo"; exit 0 }
    & (Join-Path $PSScriptRoot 'New-Stage7Disc.ps1') -ReleaseId $p.final -Label $p.label -Evidence $evidence -Repo $Repo
    Done 'The Stage 7 disc is built. Tell Claude "disc built". The next step is in the jarvis-s6-val account.'
}
if (-not (Test-Path -LiteralPath $egress)) { Halt "the evidence folder for this check ($egress) is missing; Claude creates it when you approve the check." }

# 2. Where the pass inside the VM stands (records in this check's egress folder, written by stage7.cmd).
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
$snapshot = @(Get-ChildItem -LiteralPath $vmEvidence -Filter "snapshot-$passSnapshot-*.json" -ErrorAction SilentlyContinue)
if ($snapshot) { Done "This Stage 7 check is recorded and the snapshot $passSnapshot is taken. Tell Claude: stage 7 done." }
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
    Run "take the snapshot $passSnapshot" (Join-Path $PSScriptRoot 'Take-FreshVmSnapshot.ps1') @{ Snapshot = $passSnapshot; Evidence = $vmEvidence; Description = "Stage 7 check $($p.label) passed inside the VM with $($p.final) (update from $($p.previous), interrupted update, rollback, uninstall, reinstall); taken after a clean shutdown" }
}
if ($state -eq 'poweroff') {
    if ($started) { Halt 'the VM was already started for this check and is now off, but the pass inside it did not finish. Nothing is repeated without a decision.' }
    Run 'restore the clean snapshot, attach the two discs and start the VM' (Join-Path $PSScriptRoot 'Start-Stage7Vm.ps1') @{ FinalId = $p.final; PreviousId = $p.previous; Label = $p.label; AllowedCurrent = @($p.expected_current_snapshot); Evidence = $vmEvidence }
}
if ($guestStarted) { Done 'The pass is running inside the VM. Follow what its window says (quit JARVIS, restart Windows, double-click stage7 again) until it says ALL STAGE 7 STEPS PASSED.' }
Done 'The VM is running. The next step is inside the VM: sign in, open the JARVIS_S7 disc in File Explorer and double-click stage7.'
