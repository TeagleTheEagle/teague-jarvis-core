# Decision-table test of tools\host\Invoke-NextStep.ps1 against a fake tree (test mode: nothing is run, VirtualBox is never called).
$ErrorActionPreference = 'Stop'
$script = 'C:\Users\jonny\JARVIS-claude-workspace\repo\tools\host\Invoke-NextStep.ps1'
$root = Join-Path $PSScriptRoot 'next-step-fake-root'
if (Test-Path -LiteralPath $root) { Remove-Item -LiteralPath $root -Recurse -Force }
foreach ($d in 'media', 'evidence\gate17\vm', 'evidence\guest-egress-01') { New-Item -ItemType Directory -Path (Join-Path $root $d) -Force | Out-Null }
$plan = Join-Path $root 'gate17-plan.json'
'{ "final": "1.0.11-aaa", "previous": "1.0.10-bbb" }' | Set-Content -LiteralPath $plan -Encoding ascii
function Try-It($label, $account, $state) {
    $extra = @(if ($state) { '-AssumeVmState', $state })
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $script -Root $root -Plan $plan -WhatIf -Account $account @extra | Out-String
    "--- $label [$account, vm=$state] exit $LASTEXITCODE`n" + $out.Trim()
}
function Guest-Run($name, $phase, $overall) {
    $dir = Join-Path $root "evidence\guest-egress-01\$name"; New-Item -ItemType Directory -Path $dir -Force | Out-Null
    (@{ phase = $phase; overall = $overall; started_utc = (Get-Date).ToUniversalTime().ToString('o') } | ConvertTo-Json) | Set-Content -LiteralPath (Join-Path $dir 'SUMMARY.json') -Encoding ascii
}
Try-It '1 nothing built' 'jarvis-s6-val' 'poweroff'
Try-It '1 nothing built' 'jonny' ''
foreach ($id in '1.0.11-aaa', '1.0.10-bbb') { 'x' | Set-Content -LiteralPath (Join-Path $root "media\JARVIS-PACKAGE-$id.iso"); '{}' | Set-Content -LiteralPath (Join-Path $root "evidence\gate17\package-disc-$id.json") }
Try-It '2 discs built' 'jonny' ''
Try-It '2 discs built, VM off' 'jarvis-s6-val' 'poweroff'
Try-It '2 discs built, VM running' 'jarvis-s6-val' 'running'
Try-It '2 state unreadable' 'jarvis-s6-val' ''
(@{ release = '1.0.11-aaa'; started_utc = (Get-Date).ToUniversalTime().AddMinutes(-1).ToString('o') } | ConvertTo-Json) | Set-Content -LiteralPath (Join-Path $root 'evidence\guest-egress-01\gate17-cycle.json') -Encoding ascii
Guest-Run 'gate17-20260101-000001' 'Install' 'PASS'
Try-It '3 install passed, VM running' 'jarvis-s6-val' 'running'
Guest-Run 'gate19-20260101-000002' 'Update' 'PASS'
Try-It '4 all passed, VM still on' 'jarvis-s6-val' 'running'
Try-It '4 all passed, VM off' 'jarvis-s6-val' 'poweroff'
Try-It '4 all passed' 'jonny' ''
'{}' | Set-Content -LiteralPath (Join-Path $root 'evidence\gate17\vm\snapshot-GATE17-19-PASS-20260101-000003.json')
Try-It '5 snapshot taken' 'jarvis-s6-val' 'poweroff'
Guest-Run 'gate17-20260101-000004' 'Cleanliness' 'FAIL'
Try-It '6 a guest step failed' 'jarvis-s6-val' 'running'
Try-It '7 wrong account' 'someone' 'poweroff'
