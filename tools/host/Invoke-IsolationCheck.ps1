<#
.SYNOPSIS
AMENDMENT-v2 section 7(e) ACL-boundary test, run BY THE OWNER inside the jarvis-s6-val
session, non-elevated, against the synthetic fixtures only. Every operation on the
restricted fixture must be denied without mutation; the scratch positive control must
succeed; enumerating the two protected paths must be denied (nothing is read; if access
were granted, only a count is recorded and the run stops). Short names are recorded, never
enabled (v3 A2). Results go to <Evidence>\validation-results.jsonl; the owner's postflight
then proves the fixtures are unchanged.
#>
param(
    [Parameter(Mandatory)] [string] $Evidence,
    [string] $Root = 'D:\JARVIS-S6-FRESHVM\synthetic\isolation-01'
)
$ErrorActionPreference = 'Continue'
if ($env:USERNAME -ne 'jarvis-s6-val') { throw "Run this in the jarvis-s6-val session, not as $env:USERNAME" }
if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Elevated session: STOP' }
$out = Join-Path $Evidence 'validation-results.jsonl'
$results = New-Object Collections.ArrayList
function Rec($case, $target, $expect, $outcome, $detail) {
    $r = [ordered]@{ utc = (Get-Date).ToUniversalTime().ToString('o'); case = $case; target = $target; expected = $expect; outcome = $outcome; detail = $detail; pass = ($expect -eq $outcome) }
    $results.Add($r) | Out-Null
    Add-Content -LiteralPath $out -Value ($r | ConvertTo-Json -Compress) -Encoding UTF8
    Write-Host ("{0,-6} {1,-22} {2}" -f $(if ($r.pass) { 'ok' } else { 'FAIL' }), $case, $target)
}
function Attempt($case, $target, [scriptblock] $action, $expect = 'denied') {
    try { $null = & $action; Rec $case $target $expect 'succeeded' $null }
    catch {
        $e = $_.Exception; while ($e.InnerException) { $e = $e.InnerException }
        $kind = if ($e -is [UnauthorizedAccessException] -or $e.Message -match 'denied|Access to the path') { 'denied' } else { 'error' }
        Rec $case $target $expect $kind $e.GetType().Name
    }
}

$restricted = Join-Path $Root 'restricted'; $sentinel = Join-Path $restricted 'sentinel.bin'
$targets = [ordered]@{
    'direct'            = $sentinel
    'nested'            = Join-Path $restricted 'nested\sentinel.bin'
    'hardlink'          = Join-Path $Root 'aliases\hardlink.bin'
    'junction'          = Join-Path $Root 'aliases\junction\sentinel.bin'
    'extended-path'     = '\\?\' + $sentinel
    'dot-dot-path'      = Join-Path $Root 'scratch\..\restricted\sentinel.bin'
}
# Short names: recorded only. If the restricted folder has one, it becomes a further alias target; nothing is enabled.
$dirx = (cmd /c "dir /x `"$(Split-Path $restricted)`"" 2>&1 | Out-String)
$short = [regex]::Match($dirx, '\s(RESTRI~\d)\s+restricted')
if ($short.Success) { $targets['short-name'] = Join-Path (Split-Path $restricted) ($short.Groups[1].Value + '\sentinel.bin') } else { Rec 'short-name' $restricted 'not-exercised' 'not-exercised' 'no 8.3 name present (v3 A2: NOT_APPLICABLE_WITH_EVIDENCE)' }

foreach ($name in $targets.Keys) {
    $t = $targets[$name]
    Attempt "read ($name)" $t { [IO.File]::ReadAllBytes($t) }
    Attempt "open-write ($name)" $t { $s = [IO.File]::Open($t, 'Open', 'Write'); $s.Close() }
    Attempt "delete ($name)" $t { [IO.File]::Delete($t) }
    Attempt "rename ($name)" $t { [IO.File]::Move($t, "$t.renamed") }
}
Attempt 'enumerate' $restricted { [IO.Directory]::GetFileSystemEntries($restricted) }
Attempt 'enumerate (junction)' (Join-Path $Root 'aliases\junction') { [IO.Directory]::GetFileSystemEntries((Join-Path $Root 'aliases\junction')) }
Attempt 'create' (Join-Path $restricted 'new.bin') { [IO.File]::WriteAllText((Join-Path $restricted 'new.bin'), 'x') }
Attempt 'create (nested)' (Join-Path $restricted 'nested\new.bin') { [IO.File]::WriteAllText((Join-Path $restricted 'nested\new.bin'), 'x') }
Attempt 'permission-change' $sentinel { $acl = Get-Acl -LiteralPath $sentinel -ErrorAction Stop; $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($env:USERNAME, 'FullControl', 'Allow'))); Set-Acl -LiteralPath $sentinel -AclObject $acl -ErrorAction Stop }
Attempt 'ownership-change' $sentinel { $acl = New-Object Security.AccessControl.FileSecurity; $acl.SetOwner([Security.Principal.NTAccount]$env:USERNAME); [IO.File]::SetAccessControl($sentinel, $acl) }
Attempt 'delete-from-writable-parent' $restricted { [IO.Directory]::Delete($restricted, $true) }

# Positive control: the scratch folder must work, or a blanket failure would masquerade as isolation.
$scratch = Join-Path $Root 'scratch\positive-control.bin'
Attempt 'positive-control write' $scratch { [IO.File]::WriteAllText($scratch, 'positive control') } 'succeeded'
Attempt 'positive-control read' $scratch { if ([IO.File]::ReadAllText($scratch) -ne 'positive control') { throw 'content mismatch' } } 'succeeded'
Attempt 'positive-control delete' $scratch { [IO.File]::Delete($scratch) } 'succeeded'

# Protected paths: expected denial. Nothing is read; on unexpected access only a count is recorded, and the run stops.
foreach ($p in 'C:\Users\jonny\VirtualBox VMs\JARVIS-CLEAN-WIN11', 'C:\Users\jonny\.VirtualBox') {
    try { $n = @([IO.Directory]::GetFileSystemEntries($p)).Count; Rec 'protected-path enumerate' $p 'denied' 'succeeded' "ACCESS GRANTED to $n entries: STOP" }
    catch { $e = $_.Exception; while ($e.InnerException) { $e = $e.InnerException }; Rec 'protected-path enumerate' $p 'denied' $(if ($e -is [UnauthorizedAccessException]) { 'denied' } else { 'error' }) $e.GetType().Name }
}

$failed = @($results | Where-Object { -not $_.pass })
$summary = [ordered]@{ schema = 'stage6-isolation-check-v1'; utc = (Get-Date).ToUniversalTime().ToString('o'); account = $env:USERNAME; cases = $results.Count; failed = $failed.Count
                       status = $(if ($failed.Count -eq 0) { 'PASS_PENDING_OWNER_POSTFLIGHT' } else { 'FIRST_FAIL_STOP' }); short_name_listing = $dirx }
[IO.File]::WriteAllText((Join-Path $Evidence 'validation-summary.json'), ($summary | ConvertTo-Json -Depth 3), (New-Object Text.UTF8Encoding $false))
"$($summary.status): $($results.Count) cases, $($failed.Count) failed. Next: owner runs New-IsolationFixtures.ps1 -Phase Postflight."
if ($failed.Count) { exit 2 }
