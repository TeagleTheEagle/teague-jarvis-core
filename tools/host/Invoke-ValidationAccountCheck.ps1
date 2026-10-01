<#
.SYNOPSIS
AMENDMENT-v2 section 7(b) checks, run BY THE OWNER inside the jarvis-s6-val session,
non-elevated. Records identity, groups, privileges, saved-credential entries, profile age
and the VirtualBox home setting; never asks for, reads or records any password. Writes one
JSON file to the evidence folder and prints PASS/FAIL. Claude Code reviews the file.

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File Invoke-ValidationAccountCheck.ps1 -Evidence D:\JARVIS-S6-FRESHVM\evidence\gate16r-20261002\account
#>
param([Parameter(Mandatory)] [string] $Evidence)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Path $Evidence -Force | Out-Null
$id = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal] $id
$groups = @($id.Groups | ForEach-Object { try { $_.Translate([Security.Principal.NTAccount]).Value } catch { $_.Value } })
$privText = (whoami /priv 2>$null | Out-String)
$privileges = @([regex]::Matches($privText, 'Se\w+Privilege') | ForEach-Object { $_.Value } | Sort-Object -Unique)
$credText = (cmdkey /list 2>$null | Out-String)
$credTargets = @([regex]::Matches($credText, 'Target:\s*(.+)') | ForEach-Object { $_.Groups[1].Value.Trim() })
$vbox = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -in 'VirtualBox.exe', 'VBoxManage.exe', 'VBoxSVC.exe', 'VBoxSDS.exe', 'VirtualBoxVM.exe', 'VBoxHeadless.exe' } | ForEach-Object { $o = Invoke-CimMethod -InputObject $_ -MethodName GetOwner; "$($_.Name) [$($o.Domain)\$($o.User)]" })

$forbiddenGroups = @('Administrators', 'Backup Operators', 'Hyper-V Administrators', 'Power Users', 'Remote Desktop Users', 'Network Configuration Operators')
$forbiddenPrivileges = @('SeBackupPrivilege', 'SeRestorePrivilege', 'SeTakeOwnershipPrivilege', 'SeDebugPrivilege', 'SeImpersonatePrivilege', 'SeLoadDriverPrivilege')
$findings = @()
if ($env:USERNAME -ne 'jarvis-s6-val') { $findings += "running as $env:USERNAME, not jarvis-s6-val" }
if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { $findings += 'token is elevated / administrator' }
foreach ($g in $groups) { foreach ($f in $forbiddenGroups) { if ($g -like "*\$f") { $findings += "member of $g" } } }
foreach ($p in $privileges) { if ($p -in $forbiddenPrivileges) { $findings += "privilege present: $p" } }
foreach ($t in $credTargets) { if ($t -match 'jonny|admin|THEGRIZZLYBEAR\\(?!jarvis-s6-val)') { $findings += "saved credential entry that may reference the owner or an administrator: $t" } }
if ($env:VBOX_USER_HOME -ne 'D:\JARVIS-S6-FRESHVM\vbox-home') { $findings += "VBOX_USER_HOME is '$env:VBOX_USER_HOME' (expected D:\JARVIS-S6-FRESHVM\vbox-home; set it before VM creation)" }

$record = [ordered]@{
    schema = 'stage6-validation-account-check-v1'; utc = (Get-Date).ToUniversalTime().ToString('o')
    account = $id.Name; sid = $id.User.Value; elevated = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    groups = $groups; privileges = $privileges
    saved_credential_entries = $credTargets.Count; saved_credential_targets = $credTargets
    profile = $env:USERPROFILE; profile_created_utc = (Get-Item -LiteralPath $env:USERPROFILE).CreationTimeUtc.ToString('o')
    vbox_user_home = $env:VBOX_USER_HOME; virtualbox_processes = $vbox
    unresolved_by_owner_decision_20260930 = 'the two credential entries of the 2026-09-30 bounded decision remain UNRESOLVED (AMENDMENT-v3 A3)'
    findings = $findings; status = $(if ($findings.Count -eq 0) { 'PASS' } else { 'FAIL' })
}
[IO.File]::WriteAllText((Join-Path $Evidence 'validation-account-check.json'), ($record | ConvertTo-Json -Depth 4), (New-Object Text.UTF8Encoding $false))
"$($record.status)  ($($findings -join '; '))"
if ($findings.Count) { exit 2 }
