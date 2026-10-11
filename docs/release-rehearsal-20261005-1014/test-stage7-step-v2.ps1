# Decision table of the version 2 Stage 7 launcher (tools\host\stage7-v2\Invoke-Stage7Step.ps1), in test mode only
# (-WhatIf, -Account, -AssumeVmState) against a fake tree in a scratch folder: nothing is built, no VM is touched.
# Each case sets up the tree, runs the launcher and checks the last lines it prints.
param([string] $Scratch = 'D:\JARVIS-release-work\scratch\stage7-v2-step-test')
$ErrorActionPreference = 'Stop'
$launcher = Join-Path $PSScriptRoot '..\..\tools\host\stage7-v2\Invoke-Stage7Step.ps1'
$final = '1.0.14-e03872680e1d'; $previous = '1.0.11-60d406fb6398'; $label = $final
$results = @()
function Write-Json($path, $data) { New-Item -ItemType Directory -Force -Path (Split-Path -Parent $path) | Out-Null; [IO.File]::WriteAllText($path, (ConvertTo-Json -InputObject $data -Depth 4)) }
function Fresh {
    if (Test-Path -LiteralPath $Scratch) { Remove-Item -LiteralPath $Scratch -Recurse -Force }
    $script:root = Join-Path $Scratch 'S6'; $script:stage7 = Join-Path $Scratch 'stage7'; $script:auth = Join-Path $Scratch 'tools\stage7-authorized.json'
    New-Item -ItemType Directory -Force -Path (Join-Path $root 'media'), (Join-Path $root 'evidence\guest-egress-01'), $stage7 | Out-Null
    # The 1.0.11 check's records at the version 1 places: they must never count for this check.
    Write-Json (Join-Path $root 'evidence\guest-egress-01\stage7\stage7-cycle.json') @{ release = $previous }
    Write-Json (Join-Path $stage7 'evidence\vm\snapshot-STAGE7-PASS-20261004-105804.json') @{ snapshot_name = 'STAGE7-PASS' }
    Write-Json (Join-Path $stage7 'evidence\vm\stage7-start-20261004-092000.json') @{ restored_snapshot = 'FRESH-PREREQ' }
}
function Approve($data) { Write-Json $auth $data }
function V2 { Approve ([ordered]@{ schema = 'jarvis-stage7-authorized-v2'; final = $final; previous = $previous; label = $label; expected_current_snapshot = 'STAGE7-PASS' }) }
function DiscBuilt { Set-Content -LiteralPath (Join-Path $root "media\JARVIS-STAGE7-$label.iso") -Value 'fake'; Write-Json (Join-Path $stage7 "$label\evidence\stage7-disc-$label.json") @{ release_id = $final } }
function Egress { $e = Join-Path $root "evidence\guest-egress-01\stage7-$label"; New-Item -ItemType Directory -Force -Path $e | Out-Null; $e }
function GuestRun($egress, $name, $phase, $overall) { Write-Json (Join-Path $egress "$name\SUMMARY.json") @{ phase = $phase; overall = $overall } }
function Check($name, $account, $vmState, [string[]] $expect) {
    $arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $launcher, '-Root', $root, '-Stage7', $stage7, '-Authorized', $auth, '-WhatIf', '-Account', $account)
    if ($vmState) { $arguments += @('-AssumeVmState', $vmState) }
    $out = (& powershell @arguments 2>&1 | Out-String).Trim()
    $ok = -not ($expect | Where-Object { $out -notlike "*$_*" })
    $script:results += [ordered]@{ case = $name; passed = $ok; output = ($out -split "`r?`n" | Select-Object -Last 3) -join ' | ' }
    Write-Host ("{0}  {1}" -f $(if ($ok) { 'PASS' } else { 'FAIL' }), $name)
    if (-not $ok) { Write-Host "      got: $out" }
}

Fresh; Check 'no approval: refuses' 'jonny' '' @('STOPPED', 'not been approved')
Fresh; Approve @{ final = $final; previous = $previous }; Check 'version 1 approval file: refuses' 'jonny' '' @('STOPPED', 'not a version 2 approval')
Fresh; Approve @{ schema = 'jarvis-stage7-authorized-v2'; final = $final; previous = $previous; label = $label }; Check 'approval without the expected snapshot: refuses' 'jonny' '' @('STOPPED', 'expected current snapshot')
Fresh; Approve @{ schema = 'jarvis-stage7-authorized-v2'; final = $final; previous = $previous; label = '..\x'; expected_current_snapshot = 'STAGE7-PASS' }; Check 'unsafe label: refuses' 'jonny' '' @('STOPPED', 'not valid')
Fresh; V2; Check 'other account: refuses' 'someone' '' @('STOPPED', 'not someone')
Fresh; V2; Check 'owner, no disc: builds the disc for this label' 'jonny' '' @("would run New-Stage7Disc.ps1 -Evidence $stage7\$label\evidence -Label $label -ReleaseId $final")
Fresh; V2; Check 'validation account, no disc: points to jonny' 'jarvis-s6-val' 'poweroff' @('in your own account (jonny)')
Fresh; V2; DiscBuilt; Check 'disc built, egress folder missing: refuses' 'jarvis-s6-val' 'poweroff' @('STOPPED', 'evidence folder for this check')
Fresh; V2; DiscBuilt; $null = Egress; Check 'disc built, VM off: restores from the approved snapshot (1.0.11 records ignored)' 'jarvis-s6-val' 'poweroff' @('would run Start-Stage7Vm.ps1', '-AllowedCurrent STAGE7-PASS', "-Label $label", "-Evidence $stage7\$label\evidence\vm")
Fresh; V2; DiscBuilt; $null = Egress; Check 'disc built, owner account: points to jarvis-s6-val' 'jonny' '' @('jarvis-s6-val account')
Fresh; V2; DiscBuilt; $e = Egress; Write-Json (Join-Path $e 'stage7-cycle.json') @{ release = $previous }; Check 'guest cycle of another build: refuses' 'jarvis-s6-val' 'running' @('STOPPED', "started with $previous")
Fresh; V2; DiscBuilt; $e = Egress; Write-Json (Join-Path $e 'stage7-cycle.json') @{ release = $final }; GuestRun $e 'stage7-20261005-010000' 'Install' 'FAIL'; Check 'failed guest run: stops' 'jarvis-s6-val' 'running' @('STOPPED', 'did not pass (Install')
Fresh; V2; DiscBuilt; $e = Egress; Write-Json (Join-Path $e 'stage7-cycle.json') @{ release = $final }; GuestRun $e 'stage7-20261005-010000' 'Install' 'PASS'; Check 'pass running in the VM' 'jarvis-s6-val' 'running' @('pass is running inside the VM')
Fresh; V2; DiscBuilt; $e = Egress; Write-Json (Join-Path $e 'stage7-cycle.json') @{ release = $final }; GuestRun $e 'stage7-20261005-010000' 'Install' 'PASS'; Write-Json (Join-Path $stage7 "$label\evidence\vm\stage7-start-20261005-005900.json") @{ restored_snapshot = 'FRESH-PREREQ' }; Check 'started, VM off, pass unfinished: refuses' 'jarvis-s6-val' 'poweroff' @('STOPPED', 'already started for this check')
Fresh; V2; DiscBuilt; $e = Egress; Write-Json (Join-Path $e 'stage7-cycle.json') @{ release = $final }; GuestRun $e 'stage7-20261005-020000' 'Interrupt' 'PASS'; Check 'all passed, VM still on' 'jarvis-s6-val' 'running' @('still on')
Fresh; V2; DiscBuilt; $e = Egress; Write-Json (Join-Path $e 'stage7-cycle.json') @{ release = $final }; GuestRun $e 'stage7-20261005-020000' 'Interrupt' 'PASS'; Check 'all passed, VM off: snapshot for this label' 'jarvis-s6-val' 'poweroff' @("would run Take-FreshVmSnapshot.ps1", "-Snapshot STAGE7-PASS-$label")
Fresh; V2; DiscBuilt; $e = Egress; Write-Json (Join-Path $e 'stage7-cycle.json') @{ release = $final }; GuestRun $e 'stage7-20261005-020000' 'Interrupt' 'PASS'; Write-Json (Join-Path $stage7 "$label\evidence\vm\snapshot-STAGE7-PASS-$label-20261005-030000.json") @{ snapshot_name = "STAGE7-PASS-$label" }; Check 'snapshot recorded: done' 'jarvis-s6-val' 'poweroff' @('check is recorded', "STAGE7-PASS-$label")

if (Test-Path -LiteralPath $Scratch) { Remove-Item -LiteralPath $Scratch -Recurse -Force }
$failed = @($results | Where-Object { -not $_.passed }).Count
Write-Host ''; Write-Host ("{0} cases, {1} failed" -f $results.Count, $failed)
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'test-stage7-step-v2.output.json'), (ConvertTo-Json -InputObject $results -Depth 3), (New-Object Text.UTF8Encoding $false))
exit $(if ($failed) { 1 } else { 0 })
