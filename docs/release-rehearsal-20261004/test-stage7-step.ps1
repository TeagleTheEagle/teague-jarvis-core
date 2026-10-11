# Decision-table test of tools\host\Invoke-Stage7Step.ps1 against a fake tree (test mode: nothing is run, no
# VirtualBox, no disc build). Run by Claude, owner account. Each case prints the launcher's last line.
param([string] $Base = (Join-Path $env:TEMP ('stage7-step-test-' + [guid]::NewGuid().ToString('N').Substring(0, 8))))
$ErrorActionPreference = 'Stop'
$script = 'C:\Users\jonny\JARVIS-claude-workspace\repo\tools\host\Invoke-Stage7Step.ps1'
$root = Join-Path $Base 'vmroot'; $s7 = Join-Path $Base 'stage7'; $auth = Join-Path $Base 'stage7-authorized.json'
$egress = Join-Path $root 'evidence\guest-egress-01\stage7'; $ev = Join-Path $s7 'evidence'
New-Item -ItemType Directory -Path (Join-Path $root 'media'), $egress, (Join-Path $ev 'vm') -Force | Out-Null
$final = '1.0.11-60d406fb6398'
function Case([string] $title, [string] $account, [string] $state) {
    $arguments = @('-Root', $root, '-Stage7', $s7, '-Authorized', $auth, '-WhatIf', '-Account', $account)
    if ($state) { $arguments += @('-AssumeVmState', $state) }
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $script @arguments | Out-String
    $line = ($out.Trim() -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -Last 1)
    '{0,-52} [{1}] exit={2}  {3}' -f $title, $account, $LASTEXITCODE, $line.Trim()
}
function Run([string] $phase, [string] $overall, [string] $stamp) {
    $d = Join-Path $egress "stage7-$stamp"; New-Item -ItemType Directory -Path $d | Out-Null
    [IO.File]::WriteAllText((Join-Path $d 'SUMMARY.json'), (ConvertTo-Json -InputObject @{ phase = $phase; overall = $overall }))
}
Case 'not approved' 'jonny' ''
[IO.File]::WriteAllText($auth, '{"final":"1.0.11-60d406fb6398","previous":"1.0.10-915e906516dc"}')
Case 'wrong account' 'someone' ''
Case 'no disc, validation account' 'jarvis-s6-val' 'poweroff'
Case 'no disc, owner account' 'jonny' ''
[IO.File]::WriteAllText((Join-Path $root "media\JARVIS-STAGE7-$final.iso"), 'x'); [IO.File]::WriteAllText((Join-Path $ev "stage7-disc-$final.json"), '{}')
Case 'disc built, owner account' 'jonny' ''
Case 'disc built, validation, VM off' 'jarvis-s6-val' 'poweroff'
[IO.File]::WriteAllText((Join-Path $ev 'vm\stage7-start-20261004-000000.json'), '{}')
Case 'started, VM running, guest not started' 'jarvis-s6-val' 'running'
Case 'started, VM off, guest not started' 'jarvis-s6-val' 'poweroff'
[IO.File]::WriteAllText((Join-Path $egress 'stage7-cycle.json'), (ConvertTo-Json -InputObject @{ release = $final; started_utc = '2026-10-04T00:00:00Z' }))
Run 'Install' 'PASS' '20261004-000100'
Case 'guest running (Install passed), VM running' 'jarvis-s6-val' 'running'
Case 'guest unfinished, VM off' 'jarvis-s6-val' 'poweroff'
Run 'Update' 'FAIL' '20261004-000200'
Case 'a guest phase failed' 'jarvis-s6-val' 'running'
Remove-Item -LiteralPath (Join-Path $egress 'stage7-20261004-000200') -Recurse
Run 'Update' 'PASS' '20261004-000300'; Run 'Interrupt' 'PASS' '20261004-000400'
Case 'all passed, VM still on' 'jarvis-s6-val' 'running'
Case 'all passed, VM off' 'jarvis-s6-val' 'poweroff'
Case 'all passed, owner account' 'jonny' ''
[IO.File]::WriteAllText((Join-Path $ev 'vm\snapshot-STAGE7-PASS-20261004-000500.json'), '{}')
Case 'snapshot taken' 'jarvis-s6-val' 'poweroff'
[IO.File]::WriteAllText((Join-Path $egress 'stage7-cycle.json'), (ConvertTo-Json -InputObject @{ release = '9.9.9-x'; started_utc = '2026-10-04T00:00:00Z' }))
Case 'guest started with another build' 'jarvis-s6-val' 'running'
