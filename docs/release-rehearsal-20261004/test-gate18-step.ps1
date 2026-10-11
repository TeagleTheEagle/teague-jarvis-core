# Decision-table test of tools\host\Invoke-Gate18Step.ps1 against a fake tree (test mode: nothing is run,
# VirtualBox and the backup drive are never touched). Run from any folder; it builds its tree beside itself.
$ErrorActionPreference = 'Stop'
$script = 'C:\Users\jonny\JARVIS-claude-workspace\repo\tools\host\Invoke-Gate18Step.ps1'
$root = Join-Path $env:TEMP 'gate18-step-fake-root'
if (Test-Path -LiteralPath $root) { Remove-Item -LiteralPath $root -Recurse -Force }
foreach ($d in 'media', 'evidence\gate18\vm', 'evidence\guest-egress-01') { New-Item -ItemType Directory -Path (Join-Path $root $d) -Force | Out-Null }
$auth = Join-Path $root 'gate18-authorized.json'
function Try-It($label, $account, $state) {
    $extra = @(if ($state) { '-AssumeVmState', $state })
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $script -Root $root -Authorized $auth -WhatIf -Account $account @extra | Out-String
    "--- $label [$account, vm=$state] exit $LASTEXITCODE`n" + $out.Trim()
}
function Guest-Run($name, $overall) {
    $dir = Join-Path $root "evidence\guest-egress-01\$name"; New-Item -ItemType Directory -Path $dir -Force | Out-Null
    if ($overall) { (@{ overall = $overall } | ConvertTo-Json) | Set-Content -LiteralPath (Join-Path $dir 'SUMMARY.json') -Encoding ascii }
}
Try-It '0 not authorised' 'jonny' ''
'{}' | Set-Content -LiteralPath $auth
Try-It '1 no backup copy yet' 'jonny' ''
Try-It '1 no backup copy yet' 'jarvis-s6-val' 'poweroff'
'{}' | Set-Content -LiteralPath (Join-Path $root 'evidence\gate18\backup-copy.json')
Try-It '2 backup copied, no disc' 'jarvis-s6-val' 'poweroff'
Try-It '2 backup copied, no disc' 'jonny' ''
'x' | Set-Content -LiteralPath (Join-Path $root 'media\JARVIS-RECOVERY.iso'); '{}' | Set-Content -LiteralPath (Join-Path $root 'evidence\gate18\recovery-disc.json')
Try-It '3 disc built' 'jonny' ''
Try-It '3 disc built, VM off' 'jarvis-s6-val' 'poweroff'
Try-It '3 disc built, VM running' 'jarvis-s6-val' 'running'
Guest-Run 'gate18-20260101-000001' $null
Try-It '4 restore running' 'jarvis-s6-val' 'running'
Try-It '4 restore unfinished, VM off' 'jarvis-s6-val' 'poweroff'
Guest-Run 'gate18-20260101-000001' 'PASS'
Try-It '5 restore passed, VM on' 'jarvis-s6-val' 'running'
Try-It '5 restore passed, VM off' 'jarvis-s6-val' 'poweroff'
Try-It '5 restore passed' 'jonny' ''
'{}' | Set-Content -LiteralPath (Join-Path $root 'evidence\gate18\vm\snapshot-GATE18-PASS-20260101-000002.json')
Try-It '6 snapshot taken' 'jarvis-s6-val' 'poweroff'
Remove-Item -LiteralPath (Join-Path $root 'evidence\gate18\vm\snapshot-GATE18-PASS-20260101-000002.json')
Guest-Run 'gate18-20260101-000001' 'FAIL'
Try-It '7 restore failed' 'jarvis-s6-val' 'running'
Remove-Item -LiteralPath $root -Recurse -Force
