<#
.SYNOPSIS
The "next step" launcher for Stage 6 Gate 18 on the host. Started by gate18-step.cmd in either account. It reads
the evidence folder, works out what is next and, when that step belongs to the account it was started from, runs
it; otherwise it says where the next step is. It refuses everything until Claude has recorded the owner's
RESUME_STAGE6_RECOVERY (gate18-authorized.json beside this script).

  owner account (jonny)      : (by the owner's own command) copy the backup from the backup drive; then this
                               launcher builds the recovery disc
  validation (jarvis-s6-val) : attach the recovery disc and start the VM; afterwards take snapshot GATE18-PASS
  inside the VM              : gate18.cmd on the recovery disc (this launcher only points there)
  Claude                     : checks the records; P4 runs only on the owner's "run P4"

This launcher never reads or writes the backup drive, and VirtualBox is only ever called in the jarvis-s6-val session.
#>
param(
    [string] $Root = 'D:\JARVIS-S6-FRESHVM',
    [string] $Authorized = (Join-Path $PSScriptRoot 'gate18-authorized.json'),
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
if (-not (Test-Path -LiteralPath $Authorized)) { Halt 'Gate 18 has not been authorised yet (it needs your RESUME_STAGE6_RECOVERY, recorded by Claude).' }
$owner = ($Account -eq 'jonny'); $validation = ($Account -eq 'jarvis-s6-val')
if (-not $owner -and -not $validation) { Halt "this launcher runs in the jonny or the jarvis-s6-val account, not $Account." }
$evidence = Join-Path $Root 'evidence\gate18'; $egress = Join-Path $Root 'evidence\guest-egress-01'

# 1. The backup copy (the owner's own command) and the recovery disc (owner account).
if (-not (Test-Path -LiteralPath (Join-Path $evidence 'backup-copy.json'))) {
    Done 'The next step is yours, in the jonny account: copy your backup from the backup drive with the command Claude gave you (Copy-BackupForGate18.ps1). This launcher does not touch the backup drive.'
}
if (-not ((Test-Path -LiteralPath (Join-Path $Root 'media\JARVIS-RECOVERY.iso')) -and (Test-Path -LiteralPath (Join-Path $evidence 'recovery-disc.json')))) {
    if (-not $owner) { Done 'The next step is in your own account (jonny): the recovery disc is not built yet. Switch to jonny and double-click gate18-step there.' }
    Say ''; Say 'NEXT STEP: build the recovery disc from the backup copy'
    if ($WhatIf) { Say '  (test mode) would run New-Gate18RecoveryDisc.ps1'; exit 0 }
    & (Join-Path $PSScriptRoot 'New-Gate18RecoveryDisc.ps1')
    Done 'The recovery disc is built. The next step is in the jarvis-s6-val account: switch to it and double-click gate18-step there.'
}

# 2. Where the restore inside the VM stands.
$runs = @(Get-ChildItem -LiteralPath $egress -Directory -Filter 'gate18-*' | Sort-Object Name)
$guestDone = $false; $guestStarted = [bool]$runs
if ($runs) {
    $summary = Join-Path $runs[-1].FullName 'SUMMARY.json'
    if (Test-Path -LiteralPath $summary) {
        $overall = (Get-Content -LiteralPath $summary -Raw | ConvertFrom-Json).overall
        if ($overall -ne 'PASS') { Halt "the restore inside the VM did not pass ($($runs[-1].Name)). Nothing is repeated without a decision." }
        $guestDone = $true
    }
}

# 3. Everything else is in the validation account.
$snapshot = @(Get-ChildItem -LiteralPath (Join-Path $evidence 'vm') -Filter 'snapshot-GATE18-PASS-*.json' -ErrorAction SilentlyContinue)
if ($snapshot) { Done 'Gate 18 is recorded and the snapshot GATE18-PASS is taken. Tell Claude: gate 18 done. (Next: Claude checks the records, then "run P4".)' }
if (-not $validation) {
    if ($guestDone) { Done 'The next step is in the jarvis-s6-val account: the snapshot. Switch to jarvis-s6-val and double-click gate18-step there.' }
    Done 'The recovery disc is built. The next step is in the jarvis-s6-val account: switch to it and double-click gate18-step there.'
}
if ($env:USERNAME -eq 'jarvis-s6-val' -and -not $AssumeVmState) {
    if ($env:VBOX_USER_HOME -ne "$Root\vbox-home") { Halt 'VBOX_USER_HOME is not set in this window. Close it, open a NEW File Explorer window and try again.' }
    $state = ((& 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe' showvminfo 'JARVIS-S6-FRESH' --machinereadable | Where-Object { $_ -like 'VMState=*' } | Select-Object -First 1) -replace '^VMState="?(.*?)"?$', '$1')
} else { $state = $AssumeVmState }
if (-not $state) { Halt 'the state of the VM could not be read.' }
if ($guestDone) {
    if ($state -ne 'poweroff') { Done 'The restore passed, but the VM is still on. Inside the VM: Start > Power > Shut down. When the VM window has closed, double-click gate18-step again.' }
    Run 'take the snapshot GATE18-PASS' (Join-Path $PSScriptRoot 'Take-FreshVmSnapshot.ps1') @{ Snapshot = 'GATE18-PASS'; Evidence = (Join-Path $evidence 'vm'); Description = 'Gate 18 passed inside the VM: the owner''s backup restored into a second install; the VM now holds personal data; taken after a clean shutdown, before P4' }
}
if ($state -eq 'poweroff') {
    if ($guestStarted) { Halt "the restore inside the VM was started ($($runs[-1].Name)) but did not finish, and the VM is off. Nothing is repeated without a decision." }
    Run 'attach the recovery disc and start the VM' (Join-Path $PSScriptRoot 'Start-Gate18Vm.ps1') @{}
}
if ($guestStarted) { Done 'The restore is running inside the VM. Wait for it to finish there.' }
Done 'The VM is running. The next step is inside the VM: sign in, open the JARVIS_RECOVERY disc in File Explorer and double-click gate18.'
