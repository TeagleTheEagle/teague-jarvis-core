# Decision table of the version 3 Stage 7 launcher (Invoke-Stage7Step.ps1 in this folder), in test mode only
# (-WhatIf, -Account, -AssumeVmState) against a fake tree in a scratch folder: nothing is built, no VM is touched.
# The cases of the version 2 tests (docs\release-rehearsal-20261005-1014\test-stage7-step-v2.ps1), with the version 3
# approval file, the 1.0.15 names, and the records of the 1.0.14 check (a version 2 check, its own label) in the tree,
# which must never count for this check.
param([string] $Scratch = 'D:\JARVIS-release-work\scratch\stage7-v3-step-test', [string] $Output = '')
$ErrorActionPreference = 'Stop'
$launcher = Join-Path $PSScriptRoot 'Invoke-Stage7Step.ps1'
if ((Get-Content -LiteralPath $launcher -Raw) -notmatch 'jarvis-stage7-authorized-v3') { throw 'this is not the version 3 launcher. STOP' }
$final = '1.0.15-63362929d7ad'; $previous = '1.0.14-e03872680e1d'; $label = $final
$results = @()
function Write-Json($path, $data) { New-Item -ItemType Directory -Force -Path (Split-Path -Parent $path) | Out-Null; [IO.File]::WriteAllText($path, (ConvertTo-Json -InputObject $data -Depth 4)) }
function Fresh {
    if (Test-Path -LiteralPath $Scratch) { Remove-Item -LiteralPath $Scratch -Recurse -Force }
    $script:root = Join-Path $Scratch 'S6'; $script:stage7 = Join-Path $Scratch 'stage7'; $script:auth = Join-Path $Scratch 'tools\stage7-authorized.json'
    New-Item -ItemType Directory -Force -Path (Join-Path $root 'media'), (Join-Path $root 'evidence\guest-egress-01'), $stage7 | Out-Null
    # The 1.0.11 check's records at the version 1 places, and the 1.0.14 check's records at the version 2 places
    # (its own label): none of them may count for this check.
    Write-Json (Join-Path $root 'evidence\guest-egress-01\stage7\stage7-cycle.json') @{ release = '1.0.11-60d406fb6398' }
    Write-Json (Join-Path $stage7 'evidence\vm\snapshot-STAGE7-PASS-20261004-105804.json') @{ snapshot_name = 'STAGE7-PASS' }
    Write-Json (Join-Path $stage7 'evidence\vm\stage7-start-20261004-092000.json') @{ restored_snapshot = 'FRESH-PREREQ' }
    Write-Json (Join-Path $root "evidence\guest-egress-01\stage7-$previous\stage7-cycle.json") @{ release = $previous }
    Write-Json (Join-Path $root "evidence\guest-egress-01\stage7-$previous\stage7-20261005-020000\SUMMARY.json") @{ phase = 'Interrupt'; overall = 'PASS' }
    Write-Json (Join-Path $stage7 "$previous\evidence\vm\snapshot-STAGE7-PASS-$previous-20261005-030000.json") @{ snapshot_name = "STAGE7-PASS-$previous" }
    Write-Json (Join-Path $stage7 "$previous\evidence\stage7-disc-$previous.json") @{ release_id = $previous }
    Set-Content -LiteralPath (Join-Path $root "media\JARVIS-STAGE7-$previous.iso") -Value 'fake'
}
function Approve($data) { Write-Json $auth $data }
function V3 { Approve ([ordered]@{ schema = 'jarvis-stage7-authorized-v3'; final = $final; previous = $previous; label = $label; expected_current_snapshot = "STAGE7-PASS-$previous" }) }
function DiscBuilt { Set-Content -LiteralPath (Join-Path $root "media\JARVIS-STAGE7-$label.iso") -Value 'fake'; Write-Json (Join-Path $stage7 "$label\evidence\stage7-disc-$label.json") @{ release_id = $final } }
function Egress { $e = Join-Path $root "evidence\guest-egress-01\stage7-$label"; New-Item -ItemType Directory -Force -Path $e | Out-Null; $e }
function GuestRun($egress, $name, $phase, $overall) { Write-Json (Join-Path $egress "$name\SUMMARY.json") @{ phase = $phase; overall = $overall } }
function Check($name, $account, $vmState, [string[]] $expect) {
    $arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $launcher, '-Root', $root, '-Stage7', $stage7, '-Authorized', $auth, '-WhatIf', '-Account', $account)
    if ($vmState) { $arguments += @('-AssumeVmState', $vmState) }
    $ErrorActionPreference = 'Continue'
    $out = (& powershell @arguments 2>&1 | Out-String).Trim()
    $ErrorActionPreference = 'Stop'
    $ok = -not ($expect | Where-Object { $out -notlike "*$_*" })
    $script:results += [ordered]@{ case = $name; passed = $ok; output = ($out -split "`r?`n" | Select-Object -Last 3) -join ' | ' }
    Write-Host ("{0}  {1}" -f $(if ($ok) { 'PASS' } else { 'FAIL' }), $name)
    if (-not $ok) { Write-Host "      got: $out" }
}

Fresh; Check 'no approval: refuses' 'jonny' '' @('STOPPED', 'not been approved')
Fresh; Approve @{ final = $final; previous = $previous }; Check 'version 1 approval file: refuses' 'jonny' '' @('STOPPED', 'not a version 3 approval')
Fresh; Approve ([ordered]@{ schema = 'jarvis-stage7-authorized-v2'; final = $final; previous = $previous; label = $label; expected_current_snapshot = "STAGE7-PASS-$previous" }); Check 'version 2 approval file: refuses' 'jonny' '' @('STOPPED', 'not a version 3 approval')
Fresh; Approve @{ schema = 'jarvis-stage7-authorized-v3'; final = $final; previous = $previous; label = $label }; Check 'approval without the expected snapshot: refuses' 'jonny' '' @('STOPPED', 'expected current snapshot')
Fresh; Approve @{ schema = 'jarvis-stage7-authorized-v3'; final = $final; previous = $previous; label = '..\x'; expected_current_snapshot = "STAGE7-PASS-$previous" }; Check 'unsafe label: refuses' 'jonny' '' @('STOPPED', 'not valid')
Fresh; V3; Check 'other account: refuses' 'someone' '' @('STOPPED', 'not someone')
Fresh; V3; Check 'owner, no disc: builds the disc for this label (the 1.0.14 disc does not count)' 'jonny' '' @("would run New-Stage7Disc.ps1 -Evidence $stage7\$label\evidence -Label $label -ReleaseId $final")
Fresh; V3; Check 'validation account, no disc: points to jonny' 'jarvis-s6-val' 'poweroff' @('in your own account (jonny)')
Fresh; V3; DiscBuilt; Check 'disc built, egress folder missing: refuses' 'jarvis-s6-val' 'poweroff' @('STOPPED', 'evidence folder for this check')
Fresh; V3; DiscBuilt; $null = Egress; Check 'disc built, VM off: restores from the approved snapshot (1.0.11 and 1.0.14 records ignored)' 'jarvis-s6-val' 'poweroff' @('would run Start-Stage7Vm.ps1', "-AllowedCurrent STAGE7-PASS-$previous", "-Label $label", "-Evidence $stage7\$label\evidence\vm")
Fresh; V3; DiscBuilt; $null = Egress; Check 'disc built, owner account: points to jarvis-s6-val' 'jonny' '' @('jarvis-s6-val account')
Fresh; V3; DiscBuilt; $e = Egress; Write-Json (Join-Path $e 'stage7-cycle.json') @{ release = $previous }; Check 'guest cycle of another build: refuses' 'jarvis-s6-val' 'running' @('STOPPED', "started with $previous")
Fresh; V3; DiscBuilt; $e = Egress; Write-Json (Join-Path $e 'stage7-cycle.json') @{ release = $final }; GuestRun $e 'stage7-20261007-010000' 'Install' 'FAIL'; Check 'failed guest run: stops' 'jarvis-s6-val' 'running' @('STOPPED', 'did not pass (Install')
Fresh; V3; DiscBuilt; $e = Egress; Write-Json (Join-Path $e 'stage7-cycle.json') @{ release = $final }; GuestRun $e 'stage7-20261007-010000' 'Install' 'PASS'; Check 'pass running in the VM' 'jarvis-s6-val' 'running' @('pass is running inside the VM')
Fresh; V3; DiscBuilt; $e = Egress; Write-Json (Join-Path $e 'stage7-cycle.json') @{ release = $final }; GuestRun $e 'stage7-20261007-010000' 'Install' 'PASS'; Write-Json (Join-Path $stage7 "$label\evidence\vm\stage7-start-20261007-005900.json") @{ restored_snapshot = 'FRESH-PREREQ' }; Check 'started, VM off, pass unfinished: refuses' 'jarvis-s6-val' 'poweroff' @('STOPPED', 'did not finish')
Fresh; V3; DiscBuilt; $e = Egress; Write-Json (Join-Path $e 'stage7-cycle.json') @{ release = $final }; GuestRun $e 'stage7-20261007-020000' 'Interrupt' 'PASS'; Check 'all passed, VM still on' 'jarvis-s6-val' 'running' @('still on')
Fresh; V3; DiscBuilt; $e = Egress; Write-Json (Join-Path $e 'stage7-cycle.json') @{ release = $final }; GuestRun $e 'stage7-20261007-020000' 'Interrupt' 'PASS'; Check 'all passed, VM off: snapshot for this label' 'jarvis-s6-val' 'poweroff' @('would run Take-FreshVmSnapshot.ps1', "-Snapshot STAGE7-PASS-$label")
Fresh; V3; DiscBuilt; $e = Egress; Write-Json (Join-Path $e 'stage7-cycle.json') @{ release = $final }; GuestRun $e 'stage7-20261007-020000' 'Interrupt' 'PASS'; Write-Json (Join-Path $stage7 "$label\evidence\vm\snapshot-STAGE7-PASS-$label-20261007-030000.json") @{ snapshot_name = "STAGE7-PASS-$label" }; Check 'snapshot recorded: done' 'jarvis-s6-val' 'poweroff' @('stage 7 done')

if (Test-Path -LiteralPath $Scratch) { Remove-Item -LiteralPath $Scratch -Recurse -Force }
$failed = @($results | Where-Object { -not $_.passed }).Count
Write-Host ''; Write-Host ("{0} cases, {1} failed" -f $results.Count, $failed)
if ($Output) { [IO.File]::WriteAllText($Output, (ConvertTo-Json -InputObject $results -Depth 3), (New-Object Text.UTF8Encoding $false)) }
exit $(if ($failed) { 1 } else { 0 })
