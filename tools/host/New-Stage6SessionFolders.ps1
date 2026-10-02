<#
.SYNOPSIS
Run BY THE OWNER (own account, non-elevated) before Gate 16R step 2. Creates, as NEW objects
only, the folders the jarvis-s6-val session needs and grants that account access to them:
  D:\JARVIS-S6-FRESHVM\tools\                                   read + execute (the scripts it runs)
  D:\JARVIS-S6-FRESHVM\evidence\gate16r-<date>\account\         modify (its 7(b) results)
  D:\JARVIS-S6-FRESHVM\evidence\gate16r-<date>\isolation\       modify (its 7(e) results; the owner's pre/postflight go here too)
No existing folder's permissions are changed. ACL changes are an owner act (CLAUDE.md), which
is why Claude Code does not run this. Prints the resulting ACLs and the scripts' hashes.
#>
param(
    [string] $Root = 'D:\JARVIS-S6-FRESHVM',
    [string] $EvidenceRun = 'gate16r-20261002',
    [string] $Repo = 'C:\Users\jonny\JARVIS-claude-workspace\repo',
    [string] $ValidationAccount = 'jarvis-s6-val'
)
$ErrorActionPreference = 'Stop'
if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Elevated session: STOP (nothing on this route runs elevated)' }
$validation = (New-Object Security.Principal.NTAccount($ValidationAccount)).Translate([Security.Principal.SecurityIdentifier])
$inherit = [Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit'
function Grant($path, $rights) {
    $acl = Get-Acl -LiteralPath $path
    $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($validation, $rights, $inherit, [Security.AccessControl.PropagationFlags]::None, 'Allow')))
    Set-Acl -LiteralPath $path -AclObject $acl
}
$tools = Join-Path $Root 'tools'
$account = Join-Path $Root "evidence\$EvidenceRun\account"
$isolation = Join-Path $Root "evidence\$EvidenceRun\isolation"
foreach ($p in $tools, $account, $isolation) { if (Test-Path -LiteralPath $p) { throw "already exists, not touched: $p" } }
New-Item -ItemType Directory -Path $tools, $account, $isolation | Out-Null
foreach ($s in 'Invoke-ValidationAccountCheck.ps1', 'Invoke-IsolationCheck.ps1', 'New-FreshVm.ps1', 'New-IsolationFixtures.ps1', 'Invoke-PreservationCheckpoint.ps1') { Copy-Item -LiteralPath (Join-Path $Repo "tools\host\$s") -Destination $tools }
Grant $tools 'ReadAndExecute'
Grant $account 'Modify'
Grant $isolation 'Modify'
$record = [ordered]@{
    utc = (Get-Date).ToUniversalTime().ToString('o'); created_by = [Security.Principal.WindowsIdentity]::GetCurrent().Name; validation_sid = $validation.Value
    folders = @(foreach ($p in $tools, $account, $isolation) { [ordered]@{ path = $p; acl = @((Get-Acl -LiteralPath $p).Access | ForEach-Object { "$($_.AccessControlType) $($_.IdentityReference) $($_.FileSystemRights)" }) } })
    scripts = @(Get-ChildItem -LiteralPath $tools -File | ForEach-Object { [ordered]@{ name = $_.Name; sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower() } })
}
[IO.File]::WriteAllText((Join-Path $Root "evidence\$EvidenceRun\step2-folders.json"), (ConvertTo-Json -InputObject $record -Depth 5), (New-Object Text.UTF8Encoding $false))
ConvertTo-Json -InputObject $record -Depth 5
